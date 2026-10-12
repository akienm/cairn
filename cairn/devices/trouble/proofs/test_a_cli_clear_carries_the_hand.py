"""Proof for ticket 63e6eb836769 — an operator's clear from the command line carries the
operator's measured hand.

Measured 2026-10-12: Akien ran his clear script from his own terminal and all 9
who-writes-what clears landed with by 'akien' and NO 'hand', so every one stayed OPEN.
`cairn trouble clear` asks over the bus (verb 'clear'), and TroubleDevice._handle_clear
called clear() with no hand; c2172127d7a4 measured the hand only on the emission path.

1. _handle_clear on an envelope whose body carries hand {'class': 'akien'} closes an open
   trouble notified ['cc'] (standing CLEARED), and its cleared_by entry carries that hand;
2. the CLI clear branch (cairn/devices/trouble/0/bin/trouble) sends a body whose 'hand' is
   the dict artifact.caller() measures in the CLI's own process — read by running the
   branch's Python against a fake bus and reading the body it hands to request().

Scratch store. The device and the CLI's Python are reached at call time, so a reverted
build reds a tooth rather than crashing the import.

Run bare:  PYTHONPATH=. python3 cairn/devices/trouble/proofs/test_a_cli_clear_carries_the_hand.py
"""
from __future__ import annotations

import json
import sys
import types
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


def _clear_branch_source() -> str:
    """The Python the CLI's ``clear)`` branch hands to ``python3 -c``, as python3 receives it.

    The branch is a bash double-quoted string: bash turns ``\\"`` into ``"`` and expands
    ``$REPO_ROOT``. Those are the only two expansions the branch uses, so they are the only
    two applied here."""
    text = CLI.read_text(encoding="utf-8")
    start = text.index("  clear)\n")
    body = text[text.index('exec python3 -c "', start) + len('exec python3 -c "'):]
    body = body[:body.index('\n" "$@"')]
    return body.replace('\\"', '"').replace("$REPO_ROOT", str(REPO))


def tooth_1(store: Path) -> None:
    name = PROVES["63e6eb836769"]["1"]
    try:
        from cairn.devices.trouble.trouble import TroubleDevice, CLEARED
        dev = TroubleDevice(root=str(store))
        dev.set_diagnostic_receiver(None)
        dev.raise_trouble("a-cli-clear-proof-trouble", why="a proof's trouble", detail={"n": 1},
                          recipients=["cc"])
        reply = dev.declared_verbs()["clear"]({
            "sender": "cli",
            "body": {"identity": "a-cli-clear-proof-trouble", "by": "akien",
                     "what_changed": "the proof cleared it", "hand": AKIEN}})
        t = dev._read("a-cli-clear-proof-trouble") or {}
        last = (t.get("cleared_by") or [{}])[-1]
        check(name, t.get("standing") == CLEARED and last.get("hand") == AKIEN,
              json.dumps({"standing": t.get("standing"), "hand": last.get("hand"),
                          "reply": reply.get("outcome")}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2() -> None:
    name = PROVES["63e6eb836769"]["2"]
    sent: dict = {}

    class _FakeBus:
        def request(self, **kw):
            sent.update(kw)
            return {"body": {"outcome": "cleared", "standing": "CLEARED"}}

    fake = types.ModuleType("cairn.tools.bus_client")
    fake.reach = lambda device: _FakeBus()
    saved_mod, saved_argv = sys.modules.get("cairn.tools.bus_client"), sys.argv
    try:
        from cairn.tools.artifact import artifact
        measured = artifact.caller()
        src = _clear_branch_source()
        sys.modules["cairn.tools.bus_client"] = fake
        sys.argv = ["-c", "a-cli-clear-proof-trouble", "--by", "akien",
                    "--what-changed", "the proof cleared it"]
        exec(compile(src, str(CLI), "exec"), {"__name__": "__main__"})
        hand = (sent.get("body") or {}).get("hand")
        check(name, isinstance(hand, dict) and hand.get("class") == measured.get("class")
              and sent.get("verb") == "clear",
              json.dumps({"verb": sent.get("verb"), "hand": hand, "measured": measured.get("class")}))
    except SystemExit as exc:
        check(name, False, f"the clear branch exited {exc.code}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")
    finally:
        sys.argv = saved_argv
        if saved_mod is not None:
            sys.modules["cairn.tools.bus_client"] = saved_mod
        else:
            sys.modules.pop("cairn.tools.bus_client", None)


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
