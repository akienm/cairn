"""Proof for ticket 87f0fc7b3514 — a red seal is one trouble, under one identity, from raise to clear.

MEASURED 2026-11-05 over ~/.cairn/logs/tester/0: the commit ladder (reseal.py) keyed seal
troubles per COMPONENT (seal-red-<component>) and the validation store keyed them per proof
stem (validation-verdict-changed-<stem>) — two spellings of one defect. seal-red-* stood at 755
raises against 5362 clears: 5054 clears had no standing raise, because every green reseal
cleared whether or not anything had been raised. Akien answered the grain per PROOF
(open-69cd989012c4).

Teeth (each builds a scratch component; fake raisers only, nothing reaches the live lane):
  1. the_store_and_the_ladder_spell_one_key — validation_store.seal_trouble_identity exists,
     equals reseal.trouble_identity for a proof, and announce_verdict_change raises that pointer;
  2. siblings_carry_their_own_keys — two proofs in one component, two identities;
  3. a_green_with_nothing_raised_clears_nothing — sealed green, code moved, reseal green: no clear;
  4. a_red_then_green_clears_once — rung-3 red then green: one clear, the raise's pointer;
  5. a_trail_says_whether_it_stands — a raiser whose diagnostic_trail() holds raise k then
     clear k gets no clear for k; holding only raise k, it gets one.

    python3 cairn/devices/tester/proofs/test_a_red_seal_is_one_trouble_from_raise_to_clear.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"87f0fc7b3514": {
    "1": "test_the_store_and_the_ladder_spell_one_key",
    "2": "test_siblings_carry_their_own_keys",
    "3": "test_a_green_with_nothing_raised_clears_nothing",
    "4": "test_a_red_then_green_clears_once",
    "5": "test_a_trail_says_whether_it_stands",
}}

GREEN, RED = "green", "red"


def _component(prefix: str = "testing-87f0fc7b3514-one-key-") -> tuple[Path, Path, Path]:
    """A scratch component: ``widget/{code.py, proofs/test_fast.py, proofs/test_slow.py}``."""
    from cairn.tools.scratch.scratch import scratch_dir
    root = scratch_dir(prefix) / "widget"
    (root / "proofs").mkdir(parents=True)
    (root / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    fast, slow = root / "proofs" / "test_fast.py", root / "proofs" / "test_slow.py"
    fast.write_text("assert 2 == 2\n", encoding="utf-8")
    slow.write_text("assert 3 == 3\n", encoding="utf-8")
    return root, fast, slow


def _record(proof: Path, verdict: str) -> dict:
    from cairn.tools.validation_store.validation_store import source_fingerprint
    ev = {"source_fingerprint": source_fingerprint(str(proof)),
          "returncode": 0 if verdict == GREEN else 1}
    if verdict != GREEN:
        ev["stderr_tail"] = "AssertionError: fixture"
    return {
        "claim": f"{proof.name} passes", "caller": "87f0fc7b3514 fixture",
        "date": datetime.now().isoformat(timespec="seconds"),
        "method": "ran the proof as a subprocess and read its exit code", "verdict": verdict,
        "evidence": ev,
        "falsifier": "the proof exits non-zero, or the fingerprint of the code it proves moves",
        "horizon": "valid until the proof file or the code it proves changes",
    }


class _Tester:
    def __init__(self, verdict: str):
        self.verdict = verdict

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        return _record(Path(proof_path), self.verdict)


class _Raiser:
    """Records raises and clears; carries no trail (the fixture-raiser case)."""

    def __init__(self):
        self.raised, self.cleared = [], []

    def raise_trouble(self, identity, *, why, detail=None):
        self.raised.append(identity)

    def clear_trouble(self, identity, *, by, what_changed):
        self.cleared.append(identity)


class _TrailRaiser(_Raiser):
    """A raiser whose diagnostic_trail() is a scratch directory the tooth writes into."""

    def __init__(self, trail: Path):
        super().__init__()
        self.trail = trail

    def diagnostic_trail(self):
        return self.trail


def _sealed_green_then_code_moves(proof: Path, root: Path) -> None:
    from cairn.tools.validation_store.validation_store import persist_validation
    persist_validation(_record(proof, GREEN), proof_path=str(proof))
    (root / "code.py").write_text("VALUE = 3\n", encoding="utf-8")


def test_the_store_and_the_ladder_spell_one_key():
    from cairn.devices.tester.reseal import trouble_identity
    from cairn.tools.validation_store import validation_store as vs
    _, fast, _ = _component()
    key = vs.seal_trouble_identity(str(fast))
    assert key == trouble_identity(fast), (key, trouble_identity(fast))
    assert key.startswith("seal-red-") and key.endswith("proofs-test-fast"), key
    device = _Raiser()
    vs.announce_verdict_change(vs.validations_path_for(str(fast)), {
        "from": GREEN, "to": RED, "was_sealed": "a", "now_sealed": "b",
        "was_caller": "x", "now_caller": "y", "claim": "c"}, device=device)
    assert device.raised == [key], f"the store announced {device.raised}, the ladder keys {key}"


def test_siblings_carry_their_own_keys():
    from cairn.devices.tester.reseal import trouble_identity
    _, fast, slow = _component()
    assert trouble_identity(fast) != trouble_identity(slow), (
        f"two proofs in one component share {trouble_identity(fast)!r}")


def test_a_green_with_nothing_raised_clears_nothing():
    from cairn.devices.tester.reseal import reseal
    root, fast, _ = _component()
    _sealed_green_then_code_moves(fast, root)
    raiser = _Raiser()
    out = reseal(fast, tester=_Tester(GREEN), raiser=raiser)
    assert out["outcome"] in ("resealed", "sealed"), out
    assert raiser.cleared == [], f"a green with nothing raised cleared {raiser.cleared}"


def test_a_red_then_green_clears_once():
    from cairn.devices.tester.reseal import reseal
    root, fast, _ = _component()
    _sealed_green_then_code_moves(fast, root)
    raiser = _Raiser()
    red = reseal(fast, tester=_Tester(RED), raiser=raiser)
    assert red["outcome"] == "red" and raiser.raised, (red, raiser.raised)
    (root / "code.py").write_text("VALUE = 2  # repaired\n", encoding="utf-8")
    green = reseal(fast, tester=_Tester(GREEN), raiser=raiser)
    assert green["outcome"] in ("resealed", "sealed"), green
    assert raiser.cleared == [raiser.raised[0]], (raiser.raised, raiser.cleared)


def _emit(trail: Path, stamp: str, gate: str, pointer: str) -> None:
    (trail / f"{stamp}.tester.{gate}.json").write_text(json.dumps({
        "gate": gate, "pointer": pointer, "source": "tester", "values": {"by": "cc"}}),
        encoding="utf-8")


def test_a_trail_says_whether_it_stands():
    from cairn.devices.tester.reseal import reseal, trouble_identity
    from cairn.tools.scratch.scratch import scratch_dir
    # cleared on the trail: the green emits nothing
    root, fast, _ = _component()
    _sealed_green_then_code_moves(fast, root)
    trail = scratch_dir("testing-87f0fc7b3514-trail-")
    _emit(trail, "20261105.090000.000001", "raise_trouble", trouble_identity(fast))
    _emit(trail, "20261105.090001.000001", "clear_trouble", trouble_identity(fast))
    done = _TrailRaiser(trail)
    reseal(fast, tester=_Tester(GREEN), raiser=done)
    assert done.cleared == [], f"the trail shows the key cleared; the green cleared it again"
    # raised on the trail: the green clears it once
    root2, fast2, _ = _component()
    _sealed_green_then_code_moves(fast2, root2)
    trail2 = scratch_dir("testing-87f0fc7b3514-trail-")
    _emit(trail2, "20261105.090000.000001", "raise_trouble", trouble_identity(fast2))
    open_ = _TrailRaiser(trail2)
    reseal(fast2, tester=_Tester(GREEN), raiser=open_)
    assert open_.cleared == [trouble_identity(fast2)], open_.cleared


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
