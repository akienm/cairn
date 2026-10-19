"""Proof for ticket 63e6eb836769 — an operator's clear from the command line carries the
operator's measured hand.

Measured 2026-10-12: Akien ran his clear script from his own terminal and all 9
who-writes-what clears landed with by 'akien' and NO 'hand', so every one stayed OPEN.
`cairn trouble clear` asked over the bus (verb 'clear'), and TroubleDevice._handle_clear
called clear() with no hand; c2172127d7a4 measured the hand only on the emission path.
Since ticket ee04bb869795 (2026-10-18) the CLI asks nothing over the bus: it emits
clear_trouble, which measures the hand in the CLI's own process, and folds it there.

1. clear() handed hand {'class': 'akien'} closes an open trouble notified ['cc'] (standing
   CLEARED), and its cleared_by entry carries that hand;
2. the CLI clear (cairn/devices/trouble/0/bin/trouble), run over a scratch HOME, lands a
   cleared_by entry whose hand class is the one artifact.caller() measures in this process
   tree — read off the ticket file the clear moved into cleared/.

Scratch stores. The device and the CLI are reached at call time, so a reverted build reds a
tooth rather than crashing the import.

Run bare:  PYTHONPATH=. python3 cairn/devices/trouble/proofs/test_a_cli_clear_carries_the_hand.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "63e6eb836769": {
        "1": "a_clear_verb_carrying_an_akien_hand_closes_the_trouble",
        "2": "the_cli_clear_branch_sends_the_measured_hand",
    },
}

AKIEN = {"class": "akien", "unit": "a-scope", "ancestry": ["101:a-scope"]}
CLI = REPO / "cairn/devices/trouble/0/bin/trouble"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:300]}")
    if not ok:
        FAILURES.append(name)


def tooth_1(store: Path) -> None:
    name = PROVES["63e6eb836769"]["1"]
    try:
        from cairn.devices.trouble.trouble import TroubleDevice, CLEARED
        dev = TroubleDevice(root=str(store))
        dev.set_diagnostic_receiver(None)
        dev.raise_trouble("a-cli-clear-proof-trouble", why="a proof's trouble", detail={"n": 1},
                          recipients=["cc"])
        reply = dev.clear("a-cli-clear-proof-trouble", by="akien",
                          what_changed="the proof cleared it", hand=AKIEN)
        t = dev._read("a-cli-clear-proof-trouble") or {}
        last = (t.get("cleared_by") or [{}])[-1]
        check(name, t.get("standing") == CLEARED and last.get("hand") == AKIEN,
              json.dumps({"standing": t.get("standing"), "hand": last.get("hand"),
                          "reply": reply.get("outcome")}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2() -> None:
    name = PROVES["63e6eb836769"]["2"]
    try:
        import os
        import subprocess
        import tempfile
        from cairn.tools.artifact import artifact
        from cairn.tools.base.address import log_path
        measured = artifact.caller()
        with tempfile.TemporaryDirectory(prefix="cairn-proof-cli-hand-") as d:
            home = Path(d) / "home"
            roots = {"repo": REPO, "commons": REPO.parent / "CairnCommons",
                     "instance": home / ".cairn"}
            store = log_path("cairn", 0, roots) / "troubletickets"
            store.mkdir(parents=True)
            (store / "a-cli-clear-proof-trouble.json").write_text(json.dumps({
                "id": "a-cli-clear-proof-trouble", "standing": "OPEN", "why": "a proof's trouble",
                "count": 1, "first_seen": "2026-10-18T00:00:00+00:00",
                "last_seen": "2026-10-18T00:00:00+00:00", "occurrences": [], "notified": ["cc"],
                "cleared_by": [], "recurred_after_clear": None, "prior_attempts": 0}),
                encoding="utf-8")
            # THE CALLER'S ENVIRONMENT, HOME and PYTHONPATH replaced: the CLI's TroubleShim lazy-inits the
            # ground loop, and a stripped env left systemd-run --user without its manager, so the start
            # fell through to a setsid loop under the scratch HOME that outlived the run (measured
            # 2026-10-18, three of them). Inherited, the held unit name refuses the start, and a loop a
            # run does start carries CAIRN_TESTER_TEST_ID, which the tester stops.
            out = subprocess.run(
                ["bash", str(CLI), "clear", "a-cli-clear-proof-trouble", "--by", "akien",
                 "--what-changed", "the proof cleared it"],
                capture_output=True, text=True, timeout=120,
                env={**os.environ, "HOME": str(home), "PYTHONPATH": str(REPO)})
            # Wherever the owner's clear left it: cleared/ when the hand closes it, the top when
            # it is recorded and still awaiting another recipient.
            found = [q for q in (store / "cleared" / "a-cli-clear-proof-trouble.json",
                                 store / "a-cli-clear-proof-trouble.json") if q.is_file()]
            last = ((json.loads(found[0].read_text(encoding="utf-8")).get("cleared_by") or [{}])[-1]
                    if found else {})
        hand = last.get("hand")
        check(name, out.returncode == 0 and isinstance(hand, dict)
              and hand.get("class") == measured.get("class") and last.get("by") == "akien",
              json.dumps({"rc": out.returncode, "hand": hand, "measured": measured.get("class"),
                          "out": (out.stdout + out.stderr)[-200:]}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir
    tooth_1(scratch_dir("cairn-proof-cli-clear-hand-") / "store")
    tooth_2()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
