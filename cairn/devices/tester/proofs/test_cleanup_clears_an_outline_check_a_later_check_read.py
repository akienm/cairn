"""Proof for ticket 244b2e6c411f — cairn cleanup clears an outline-check trouble once a later check read
the ticket.

Measured 2026-11-19: red-tickets-outline-check-b7987e439273 stands live although the newest
record for that ticket, CairnCommons/outline_checks/b7987e439273-20261119T093117.json, reads
``ran: True`` (the 20261118T204848 one that raised it reads False). ``red_tickets._outline_check``
raises the trouble and nothing clears it; the tester's recheck (ticket 17b087f2483f) knew only the
seal kinds. The tester now rechecks its outline-check kind too and emits the clear; the trouble
device's drain folds it (Law 6), which tooth 3 reads through ``cairn trouble live``.

1. the newest record reads ran True (an older one False): recheck clears the trouble;
2. the newest reads ran False (an older one True), or no record exists: the trouble stands;
3. in a scratch HOME, with CAIRN_OUTLINE_CHECKS_DIR at a scratch records dir, the trouble is
   raised and drained OPEN, ``bin/cairn cleanup``'s seals line reports it cleared, and
   ``cairn trouble live`` no longer lists it.

Teeth 1-2 run recheck in-process over a scratch records dir and read the clears it emits to a
recording raiser (ticket 0dbb6b5e940a: no trouble-device internals); tooth 3 runs the
wiring as subprocesses under the scratch HOME and its own CAIRN_BUS_UNIT, stopped and reset in
finally (the ea354f41ec67 world). recheck is bound at call time. Nothing is written outside the
scratch dirs.

    bin/cairn test cairn/devices/tester/proofs/test_cleanup_clears_an_outline_check_a_later_check_read.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"244b2e6c411f": {
    "1": "an_outline_check_trouble_clears_when_the_newest_record_ran",
    "2": "an_outline_check_trouble_stands_when_the_newest_did_not_run_or_none_exists",
    "3": "cleanup_clears_an_outline_check_trouble_through_the_cli",
}}
READ, UNREAD, NONE = "0c1ead000001", "0c1ead000002", "0c1ead000003"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:600]}")
    if not ok:
        FAILURES.append(name)


def _records(root: Path) -> None:
    root.mkdir(parents=True, exist_ok=True)
    for tid, old, new in ((READ, False, True), (UNREAD, True, False)):
        for stamp, ran in (("20261118T000000", old), ("20261119T000000", new)):
            (root / f"{tid}-{stamp}.json").write_text(json.dumps({"ticket": tid, "ran": ran}),
                                                      encoding="utf-8")


class _Recorder:
    """Records each clear the recheck emits. The fold of a clear into the store is the trouble
    device's own write (Law 6), proved at its own address; a tester proof that built a
    TroubleDevice to read the fold reached past the store tool (ticket 0dbb6b5e940a), so these
    teeth read what the tester EMITS, as test_reseal_door.py's _FakeRaiser does."""

    def __init__(self):
        self.cleared: list[str] = []

    def clear_trouble(self, identity, *, by, what_changed):
        self.cleared.append(identity)


def _in_process(tmp: Path) -> None:
    from cairn.devices.tester.recheck import _slug, recheck

    records = tmp / "outline_checks"
    _records(records)
    ids = {tid: _slug(f"red_tickets:outline_check:{tid}") for tid in (READ, UNREAD, NONE)}
    rec = _Recorder()
    got = recheck([f"red_tickets:outline_check:{tid}" for tid in ids], proof_roots=[tmp],
                  raiser=rec, outline_root=records)
    show = json.dumps({"recheck": got, "cleared": rec.cleared})
    check(PROVES["244b2e6c411f"]["1"], ids[READ] in got["cleared"] and rec.cleared == [ids[READ]], show)
    check(PROVES["244b2e6c411f"]["2"],
          all(ids[t] in got["standing"] and ids[t] not in rec.cleared for t in (UNREAD, NONE)), show)


def _run(env: dict, *argv: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(list(argv), cwd=REPO, env=env, capture_output=True, text=True,
                          timeout=timeout)


def _through_cli(home: Path) -> None:
    records = home / "outline_checks"
    _records(records)
    unit = f"cairn-proof-outlinerecheck-{os.getpid()}"
    env = dict(os.environ, HOME=str(home), CAIRN_BUS_UNIT=unit, GIT_TERMINAL_PROMPT="0",
               PYTHONPATH=str(REPO), CAIRN_OUTLINE_CHECKS_DIR=str(records))
    cairn = str(REPO / "bin" / "cairn")
    try:
        r = _run(env, sys.executable, "-c",
                 "from cairn.tools.base.diagnostic import ModuleRaiser\n"
                 f"ModuleRaiser('tester').raise_trouble('red_tickets:outline_check:{READ}', "
                 "why='a check that did not read it')\n")
        drained = _run(env, cairn, "trouble", "drain")
        ident = f"red-tickets-outline-check-{READ}"

        def live() -> list[str]:
            out = _run(env, cairn, "trouble", "live", "--json")
            try:
                return [t["id"] for t in json.loads(out.stdout)]
            except Exception:  # noqa: BLE001 — an unreadable list reds the tooth with its text
                return [f"unreadable: {out.stdout[-200:]} {out.stderr[-200:]}"]

        before = live()
        cleanup = _run(env, cairn, "cleanup")
        seals = next((ln for ln in cleanup.stdout.splitlines() if ln.startswith("seals ")), "")
        after = live()
        check(PROVES["244b2e6c411f"]["3"],
              ident in before and ident not in after and " ok " in seals and ident in seals,
              f"raise_rc={r.returncode} {r.stderr[-200:]!r} drain_rc={drained.returncode} "
              f"open_before={ident in before} seals_line={seals!r} cleanup_rc={cleanup.returncode} "
              f"live_after={after}")
    finally:
        for verb in ("stop", "reset-failed"):
            subprocess.run(["systemctl", "--user", verb, f"{unit}.service"],
                           capture_output=True, text=True)


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir
    for fn, prefix, teeth in ((_in_process, "oclrin", ("1", "2")), (_through_cli, "oclrcli", ("3",))):
        try:
            fn(Path(scratch_dir(prefix)))
        except Exception as exc:  # noqa: BLE001 — a raising setup reds its teeth by name, loud
            for n in teeth:
                if PROVES["244b2e6c411f"][n] not in FAILURES:
                    check(PROVES["244b2e6c411f"][n], False, f"{fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}" if FAILURES else "\nall teeth green")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
