"""Proof for ticket e2ed467ef1a5 — an operator's hand that came over ssh does not close a trouble by
operator power (outline 17.2.2, Q#115).

Measured 2026-11-18: an ssh login's shell sits in a session-<n>.scope, which the artifact door's
classify() reads as akien, and CC on another box logs in with the key Akien's own ssh uses. The
artifact door's caller() now carries ``ssh`` (the sshd pid) when the hand descends from an ssh
login (ticket a9cf64d1f92e), and clear_trouble sends that caller() as the clear's hand. Until CC
has its own key, the operator close refuses any such hand, Akien's included: the clear still
lands on the record (Law 7), and the trouble closes only by the notified rule.

1. a trouble notified ['cc'], cleared by 'akien' with hand {class akien, ssh} stays OPEN, and
   its cleared_by entry carries that hand;
2. the same clear with hand {class akien} and no ssh closes it (the operator close stands);
3. a hand {class cc, ssh} by 'akien' also stays OPEN: the refusal is by ssh, not by class.

Scratch world and store; the clear emissions are written with ``emit`` in the shape
clear_trouble writes, so this proof measures the holder alone (RULE 1). The device is
imported inside ``main``.

Run bare:  PYTHONPATH=. python3 cairn/devices/trouble/proofs/test_an_ssh_hand_does_not_operator_close.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "e2ed467ef1a5": {
        "1": "an_akien_hand_over_ssh_stays_open",
        "2": "an_akien_hand_at_the_box_closes",
        "3": "a_cc_hand_over_ssh_stays_open",
    },
}

SSH_AKIEN = {"class": "akien", "unit": "session-4397.scope", "ancestry": ["101:session-4397.scope"], "ssh": 99}
BOX_AKIEN = {"class": "akien", "unit": "session-4397.scope", "ancestry": ["101:session-4397.scope"]}
SSH_CC = {"class": "cc", "unit": "superclaude-1.scope", "ancestry": ["202:superclaude-1.scope"], "ssh": 98}
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:300]}")
    if not ok:
        FAILURES.append(name)


def _component(world: Path):
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Fixture(DiagnosticBase):
        @property
        def diagnostic_device(self) -> str:
            return "a_fixture_component"

    d = _Fixture()
    d.set_diagnostic_roots({k: world for k in ("repo", "commons", "instance")})
    return d


def main() -> int:
    from cairn.devices.trouble.shim import TroubleShim
    from cairn.devices.trouble.trouble import TroubleDevice, CLEARED

    with tempfile.TemporaryDirectory(prefix="cairn-ssh-clear-proof-") as tmp:
        world, store = Path(tmp) / "world", Path(tmp) / "store"
        c = _component(world)
        for ident in ("over-ssh-akien", "at-the-box-akien", "over-ssh-cc"):
            c.raise_trouble(ident, why="a proof's trouble", detail={"n": 1})
        shim = TroubleShim(roots={k: world for k in ("repo", "commons", "instance")}, root=str(store))
        shim.drain()
        for ident, hand in (("over-ssh-akien", SSH_AKIEN), ("at-the-box-akien", BOX_AKIEN),
                            ("over-ssh-cc", SSH_CC)):
            c.emit("clear_trouble", pointer=ident,
                   values={"by": "akien", "what_changed": "a proof's clear", "hand": hand})
        shim.drain()
        dev = TroubleDevice(root=str(store))
        dev.set_diagnostic_receiver(None)
        got = {i: (dev._read(i) or {}) for i in ("over-ssh-akien", "at-the-box-akien", "over-ssh-cc")}

        def show(t: dict) -> str:
            return json.dumps({"standing": t.get("standing"), "notified": t.get("notified"),
                               "hand": ((t.get("cleared_by") or [{}])[-1]).get("hand")})

        one, two, three = got["over-ssh-akien"], got["at-the-box-akien"], got["over-ssh-cc"]
        check(PROVES["e2ed467ef1a5"]["1"],
              one.get("notified") == ["cc"] and one.get("standing") != CLEARED
              and ((one.get("cleared_by") or [{}])[-1]).get("hand") == SSH_AKIEN, show(one))
        check(PROVES["e2ed467ef1a5"]["2"], two.get("standing") == CLEARED, show(two))
        check(PROVES["e2ed467ef1a5"]["3"],
              three.get("standing") != CLEARED and len(three.get("cleared_by") or []) == 1, show(three))

    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
