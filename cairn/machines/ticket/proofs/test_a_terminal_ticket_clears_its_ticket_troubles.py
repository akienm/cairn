"""Proof for ticket c1664a4eb3ad — a terminal ticket's own unqueued/refused troubles clear at cleanup.

A ticket's ``ticket-unqueued-*`` and ``ticket-refused-*`` troubles clear when a later ask at the
same gate is taken or passed (41a5bae3d01b, 794835a34ec9). Measured 2026-11-19: 8c5fdb750b75's
clearance asks timed out while the gate still carried it to PROVED, and a terminal ticket asks no
gate again, so its unqueued trouble stood with nothing left to clear it. Now ``cairn cleanup``
hands the live ticket troubles to ``python3 -m cairn.machines.ticket.ticket --recheck``, and each
whose ticket stands terminal, with the raise standing on its trail, is cleared by the ticket.

1. A ticket at PROVED whose unqueued trouble stands raised: recheck clears it, and the newest
   record naming it on the ticket's trail is the clear.
2. A ticket still under way (FIXME) keeps its raised trouble, and a terminal ticket with nothing
   raised is sent no clear: both read standing.
3. Through the wiring a hand runs: in a scratch HOME, the raise is drained OPEN, ``bin/cairn
   cleanup`` reports it cleared on its tickets line, and ``cairn trouble live`` no longer lists it.

Every tooth runs in a scratch world: a scratch ticket store (the live store charter copied in,
fixture plans and states), the tickets' diagnostic roots under the same scratch dir, and for
tooth 3 a scratch HOME with CAIRN_TICKETS_DIR at the store and the drain's bus under this proof's
own CAIRN_BUS_UNIT, stopped and reset at the end. Nothing is written outside the scratch world.

    bin/cairn test cairn/machines/ticket/proofs/test_a_terminal_ticket_clears_its_ticket_troubles.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"c1664a4eb3ad": {
    "1": "a_proved_tickets_raised_trouble_is_cleared",
    "2": "an_under_way_or_unraised_ticket_reads_standing_and_sends_no_clear",
    "3": "cleanup_clears_a_proved_tickets_trouble_through_the_cli",
}}
_COMMONS = REPO.parent / "CairnCommons"
if not (_COMMONS / "tickets" / "_charter+why.json").is_file():
    _COMMONS = Path.home() / "dev" / "src" / "CairnCommons"
_CHARTER = _COMMONS / "tickets" / "_charter+why.json"
_WF = {"PROVED": "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]",
       "FIXME": "code-seam@v2: THINKME -> TICKETME -> [FIXME:waiting] -> BUILDME -> PROVEME -> PROVED"}
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:1500]}")
    if not ok:
        FAILURES.append(name)


def _store(tmp: Path) -> Path:
    store = tmp / "tickets"
    store.mkdir()
    shutil.copy(_CHARTER, store / "_charter+why.json")
    for tid, at in (("fixtureprovedraised", "PROVED"), ("fixturefixmeraised", "FIXME"),
                    ("fixtureprovedunraised", "PROVED")):
        plan = store / f"{tid}-a-fixture-ticket.json"
        plan.write_text(json.dumps({"id": tid, "title": "a fixture ticket",
                                    "owning_intention": "cairn/machines/ticket/intention+why.json"},
                                   indent=2) + "\n")
        (store / f"{tid}-a-fixture-ticket.state.json").write_text(json.dumps(
            {"workflow_and_state": _WF[at], "node_class": "code-seam"}, indent=2) + "\n")
    return store


def _records(t, ident: str) -> list[str]:
    """``raise``/``clear`` for each trail record naming ``ident``, newest first."""
    trail = Path(t.diagnostic_trail())
    out = []
    for p in sorted(trail.glob("*_trouble.json"), key=lambda p: p.name, reverse=True) \
            if trail.is_dir() else []:
        if json.loads(p.read_text(encoding="utf-8")).get("pointer") == ident:
            out.append("raise" if p.name.endswith(".raise_trouble.json") else "clear")
    return out


def _in_process(tmp: Path) -> None:
    from cairn.machines.ticket.ticket import Ticket, recheck
    store = _store(tmp)
    roots = {k: tmp / k for k in ("repo", "commons", "instance")}
    for p in roots.values():
        p.mkdir()
    ident = {tid: f"ticket-unqueued-{tid}-at-clearance"
             for tid in ("fixtureprovedraised", "fixturefixmeraised", "fixtureprovedunraised")}
    tk = {tid: Ticket.at(tid, tickets_dir=store, roots=roots) for tid in ident}
    for tid in ("fixtureprovedraised", "fixturefixmeraised"):
        tk[tid].raise_trouble(ident[tid], why="a fixture ask nobody took")
    got = recheck(list(ident.values()), tickets_dir=store, roots=roots)
    a = ident["fixtureprovedraised"]
    check(PROVES["c1664a4eb3ad"]["1"],
          a in got["cleared"] and _records(tk["fixtureprovedraised"], a)[:1] == ["clear"],
          f"recheck={got} trail={_records(tk['fixtureprovedraised'], a)}")
    b, c = ident["fixturefixmeraised"], ident["fixtureprovedunraised"]
    check(PROVES["c1664a4eb3ad"]["2"],
          b in got["standing"] and c in got["standing"]
          and _records(tk["fixturefixmeraised"], b) == ["raise"]
          and _records(tk["fixtureprovedunraised"], c) == [],
          f"recheck={got} fixme_trail={_records(tk['fixturefixmeraised'], b)} "
          f"unraised_trail={_records(tk['fixtureprovedunraised'], c)}")


def _run(env: dict, *argv: str, timeout: int = 600) -> subprocess.CompletedProcess:
    return subprocess.run(list(argv), cwd=REPO, env=env, capture_output=True, text=True,
                          timeout=timeout)


def _through_cleanup(home: Path) -> None:
    store = _store(home)
    unit = f"cairn-proof-tickettroubles-{os.getpid()}"
    env = dict(os.environ, HOME=str(home), CAIRN_BUS_UNIT=unit, CAIRN_TICKETS_DIR=str(store),
               GIT_TERMINAL_PROMPT="0", PYTHONPATH=str(REPO))
    cairn = str(REPO / "bin" / "cairn")
    ident = "ticket-unqueued-fixtureprovedraised-at-clearance"
    try:
        r = _run(env, sys.executable, "-c",
                 "import os\nfrom cairn.machines.ticket.ticket import Ticket\n"
                 "t = Ticket.at('fixtureprovedraised', tickets_dir=os.environ['CAIRN_TICKETS_DIR'])\n"
                 f"t.raise_trouble({ident!r}, why='a fixture ask nobody took')\n")
        def trail() -> list[str]:
            return sorted(str(q.relative_to(home)) for q in home.rglob("*_trouble.json"))
        t_raised = trail()
        drained = _run(env, cairn, "trouble", "drain")
        t_drained = trail()

        def live() -> list[str]:
            out = _run(env, cairn, "trouble", "live", "--json")
            try:
                return [t["id"] for t in json.loads(out.stdout)]
            except Exception:
                return [f"unreadable: {out.stdout[-200:]} {out.stderr[-200:]}"]

        before = live()
        cleanup = _run(env, cairn, "cleanup")
        line = next((ln for ln in cleanup.stdout.splitlines() if ln.startswith("tickets ")), "")
        after = live()
        # the clear names the notified recipient, so it closes whatever hand runs cleanup
        # (a gate's re-run is not an operator's hand)
        bys = [json.loads(q.read_text()).get("values", {}).get("by")
               for q in home.rglob("*.Ticket.clear_trouble.json")]
        check(PROVES["c1664a4eb3ad"]["3"],
              ident in before and ident not in after and " ok " in line and ident in line
              and bys == ["cc"],
              f"raise_rc={r.returncode} {r.stderr[-200:]!r} drain_rc={drained.returncode} "
              f"open_before={ident in before} tickets_line={line!r} "
              f"cleanup_rc={cleanup.returncode} live_after={after} clear_by={bys} "
              f"trail_raised={t_raised} trail_drained={t_drained} cleanup_out={cleanup.stdout[-300:]!r}")
    finally:
        for verb in ("stop", "reset-failed"):
            subprocess.run(["systemctl", "--user", verb, f"{unit}.service"],
                           capture_output=True, text=True)


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir
    for fn, prefix in ((_in_process, "tktrbl"), (_through_cleanup, "tktclean")):
        try:
            fn(scratch_dir(prefix))
        except Exception as exc:  # noqa: BLE001 — a raising setup reds its teeth, loud
            FAILURES.append(fn.__name__)
            print(f"  FAIL  {fn.__name__}: {type(exc).__name__}: {exc}")
    print(f"\n{len(FAILURES)} failure(s): {FAILURES}" if FAILURES else "\nall teeth green")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
