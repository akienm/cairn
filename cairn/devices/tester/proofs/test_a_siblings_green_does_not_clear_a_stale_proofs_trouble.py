"""Proof: a sibling's green does not clear the trouble a still-stale proof raised (ticket 86b6bf19ed2a).

MEASURED 2026-10-06, the reason this file exists. ``cairn/tools/base/proofs/test_transitions.py``
runs ~182s and declares no PROOF_TIMEOUT_S, so the commit-time reseal (budget 120s) times it
out on every commit touching its closure. The door DID raise: ``~/.cairn/logs/tester/0/
20261006.083253.205466.tester.raise_trouble.json`` carries ``seal-red-cairn-tools-base`` with
the timeout why. 1.8 seconds later ``20261006.083254.995762.tester.clear_trouble.json`` cleared
the SAME identity because a sibling, ``test_watchme_spec.py``, resealed green. The identity is
one per component on purpose (``trouble_identity``'s docstring: per-proof would file eleven
troubles for one broken import). The clear has no such reason. A green from one proof says
nothing about another proof in the component, so the trouble vanished while the stale seal
stood. The next PROVED was refused by ``component_color``, and nothing on any record said why.

The rule a hollow build cannot pass: the component's seal-red trouble stays raised while ANY
sealed proof in that component does not reproduce, and clears on the green that leaves none.

Teeth:
  1. a proof times out; a sibling in the same component then reseals green. No clear is
     sent, and the green's result names the sibling still standing unreproduced.
  2. when that last unreproduced proof reseals green, exactly one clear is sent.
  3. a rung-3 red sibling holds the trouble the same way a timeout does, and a sibling that
     was NEVER sealed does not hold it (it is not a seal that stopped reproducing; holding on
     it would pin every component that adds a proof red until the proof's first seal).

    python3 cairn/devices/tester/proofs/test_a_siblings_green_does_not_clear_a_stale_proofs_trouble.py
"""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.device import GREEN, RED  # noqa: E402
from cairn.devices.tester.reseal import reseal, trouble_identity  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.validation_store.validation_store import (  # noqa: E402
    persist_validation, source_fingerprint,
)

PROVES = {"86b6bf19ed2a": {
    "1": "test_a_siblings_green_leaves_a_timed_out_proofs_trouble_RAISED",
    "2": "test_the_green_that_leaves_no_stale_sibling_CLEARS",
    "3": "test_a_red_sibling_holds_and_a_never_sealed_one_does_NOT",
}}


def _component(prefix: str = "sibling-green-fixture-") -> tuple[Path, Path, Path]:
    """A scratch component with two proofs: ``proofs/test_fast.py`` and ``proofs/test_slow.py``."""
    root = scratch_dir(prefix) / "widget"
    (root / "proofs").mkdir(parents=True)
    (root / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    fast = root / "proofs" / "test_fast.py"
    slow = root / "proofs" / "test_slow.py"
    fast.write_text("assert 2 == 2\n", encoding="utf-8")
    slow.write_text("assert 3 == 3\n", encoding="utf-8")
    return root, fast, slow


def _record(proof: Path, verdict: str, *, evidence=None) -> dict:
    ev = {"source_fingerprint": source_fingerprint(str(proof)),
          "returncode": 0 if verdict == GREEN else 1}
    ev.update(evidence or {})
    return {
        "claim": f"{proof.name} passes",
        "caller": "sibling-green fixture",
        "date": datetime.now().isoformat(timespec="seconds"),
        "method": "ran the proof as a subprocess and read its exit code",
        "verdict": verdict,
        "evidence": ev,
        "falsifier": "the proof exits non-zero, or the fingerprint of the code it proves moves",
        "horizon": "valid until the proof file or the code it proves changes",
    }


class _Tester:
    def __init__(self, verdict: str, *, timed_out: bool = False):
        self.verdict, self.timed_out = verdict, timed_out

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        if self.timed_out:   # the runner's own shape for a killed subject (test_reseal_door)
            return _record(Path(proof_path), RED, evidence={
                "returncode": None, "stdout_tail": "",
                "stderr_tail": f"timed out after {timeout}s"})
        return _record(Path(proof_path), self.verdict,
                       evidence=None if self.verdict == GREEN else
                       {"stderr_tail": "AssertionError: fixture"})


class _Raiser:
    def __init__(self):
        self.raised, self.cleared = [], []

    def raise_trouble(self, identity, *, why, detail=None):
        self.raised.append(identity)

    def clear_trouble(self, identity, *, by, what_changed):
        self.cleared.append(identity)


def _both_sealed_then_code_moves() -> tuple[Path, Path, Path]:
    root, fast, slow = _component()
    persist_validation(_record(fast, GREEN), proof_path=str(fast))
    persist_validation(_record(slow, GREEN), proof_path=str(slow))
    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")
    return root, fast, slow


def test_a_siblings_green_leaves_a_timed_out_proofs_trouble_RAISED():
    _, fast, slow = _both_sealed_then_code_moves()
    raiser = _Raiser()
    timed = reseal(slow, tester=_Tester(RED, timed_out=True), raiser=raiser)
    assert timed["outcome"] == "timeout", timed
    assert raiser.raised == [trouble_identity(slow)], raiser.raised

    green = reseal(fast, tester=_Tester(GREEN), raiser=raiser)
    assert green["outcome"] in ("resealed", "sealed"), green
    assert raiser.cleared == [], (
        f"a sibling's green cleared {raiser.cleared} while test_slow.py still does not "
        "reproduce. The trouble vanished and the stale seal stayed")
    standing = green.get("still_unreproduced")
    assert standing and any(s.endswith("proofs/test_slow.py") for s in standing), (
        f"the green's result does not name the sibling still standing unreproduced: {green}")


def test_the_green_that_leaves_no_stale_sibling_CLEARS():
    _, fast, slow = _both_sealed_then_code_moves()
    raiser = _Raiser()
    reseal(slow, tester=_Tester(RED, timed_out=True), raiser=raiser)
    reseal(fast, tester=_Tester(GREEN), raiser=raiser)
    last = reseal(slow, tester=_Tester(GREEN), raiser=raiser)
    assert last["outcome"] in ("resealed", "sealed"), last
    assert raiser.cleared == [trouble_identity(slow)], (
        f"the green that left no stale sibling did not clear exactly once: {raiser.cleared}")
    assert not last.get("still_unreproduced"), last


def test_a_red_sibling_holds_and_a_never_sealed_one_does_NOT():
    _, fast, slow = _both_sealed_then_code_moves()
    raiser = _Raiser()
    red = reseal(slow, tester=_Tester(RED), raiser=raiser)
    assert red["outcome"] == "red", red
    reseal(fast, tester=_Tester(GREEN), raiser=raiser)
    assert raiser.cleared == [], f"a sibling's green cleared a standing rung-3 red: {raiser.cleared}"

    root, fast2, slow2 = _component()
    persist_validation(_record(fast2, GREEN), proof_path=str(fast2))   # slow2: never sealed
    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")
    raiser2 = _Raiser()
    out = reseal(fast2, tester=_Tester(GREEN), raiser=raiser2)
    assert raiser2.cleared == [trouble_identity(fast2)], (
        f"a never-sealed sibling held the clear. It is not a seal that stopped reproducing: "
        f"{raiser2.cleared}, {out}")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
