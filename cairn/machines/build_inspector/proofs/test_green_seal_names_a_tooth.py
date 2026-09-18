"""Proofs for the green_seal_names_a_tooth sieve — and the corpus invariant it guards.

Ticket 77f15efd5a96. Four fixture teeth a hollow sieve could not pass (empty teeth fires,
absent teeth fires, a named tooth is quiet, a red seal is quiet), one tooth that the seat
is in the nest, and the live-corpus invariant: over every standing seal in this repo,
green seals naming no tooth number ZERO — asserted as an invariant, never a snapshot, so
it stays red the day a hollow green comes back.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.build_inspector.inspector import (  # noqa: E402
    SIEVES, green_seal_names_a_tooth,
)
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "77f15efd5a96": {
        "2": ["test_a_green_seal_with_empty_teeth_fires",
              "test_a_green_seal_with_no_teeth_key_fires",
              "test_a_green_seal_naming_a_tooth_is_quiet",
              "test_a_red_seal_is_quiet",
              "test_an_orphan_seal_is_caught",
              "test_the_seat_is_in_the_nest"],
        "4": ["test_the_live_corpus_has_no_green_seal_naming_no_tooth"],
    },
}

# Seals Akien decided to KEEP standing without a tooth, by the answer that kept them —
# empty until an answer says otherwise (open-6b86f1467e6d, open-d415cbb00c56).
KEPT_BY_ANSWER: dict[str, str] = {}


def _row(name):
    return {"component": name, "dir": name, "charter_on_disk": True, "proofs": 1,
            "validations": [], "device_subclasses": [],
            "self_emit_call_sites_outside_proofs": 0}


def _component(root: Path, name: str, *, verdict="green", teeth=None, proof=True):
    comp = root / name
    (comp / "proofs").mkdir(parents=True)
    if proof:
        (comp / "proofs" / "test_thing.py").write_text("assert True\n", encoding="utf-8")
    evidence = {"source_fingerprint": "fixture"}
    if teeth is not None:
        evidence["teeth_green"] = teeth
    (comp / "validations").mkdir()
    (comp / "validations" / "test_thing.json").write_text(json.dumps([{
        "claim": "fixture", "caller": "test", "date": "2026-09-15T00:00:00",
        "method": "fixture", "verdict": verdict, "evidence": evidence,
        "falsifier": "test", "horizon": "test"}]), encoding="utf-8")
    return comp


def test_a_green_seal_with_empty_teeth_fires():
    root = scratch_dir("green-seal-empty-teeth-")
    f = green_seal_names_a_tooth(_row("empty"), _component(root, "empty", teeth=[]))
    assert len(f) == 1 and f[0]["method"] == "green_seal_names_a_tooth", f
    assert f[0]["values"]["teeth_green"] == "empty", f[0]


def test_a_green_seal_with_no_teeth_key_fires():
    """Absent and empty are different claims (Law 7) — both fire, each named as itself."""
    root = scratch_dir("green-seal-absent-teeth-")
    f = green_seal_names_a_tooth(_row("absent"), _component(root, "absent", teeth=None))
    assert len(f) == 1, f
    assert f[0]["values"]["teeth_green"] == "absent", f[0]


def test_a_green_seal_naming_a_tooth_is_quiet():
    root = scratch_dir("green-seal-named-")
    f = green_seal_names_a_tooth(_row("named"), _component(root, "named", teeth=["test_x"]))
    assert f == [], f


def test_a_red_seal_is_quiet():
    """A red seal is already distrusted; this sieve has nothing to add to it."""
    root = scratch_dir("green-seal-red-")
    f = green_seal_names_a_tooth(_row("red"), _component(root, "red", verdict="red", teeth=[]))
    assert f == [], f


def test_an_orphan_seal_is_caught():
    """The seal stands, the proof is gone — component_color starts from proofs/ and cannot
    see this; five of the 31 measured offenders were exactly this shape."""
    root = scratch_dir("green-seal-orphan-")
    f = green_seal_names_a_tooth(_row("orphan"), _component(root, "orphan", teeth=[], proof=False))
    assert len(f) == 1 and f[0]["values"]["seal"] == "test_thing.json", f


def test_the_seat_is_in_the_nest():
    """A sieve that exists and is not registered judges nothing."""
    assert SIEVES.get("green_seal_names_a_tooth") is green_seal_names_a_tooth, sorted(SIEVES)


def test_the_live_corpus_has_no_green_seal_naming_no_tooth():
    """THE DONE-MEASURE, AS AN INVARIANT. Every standing seal under cairn/ is walked; the
    denominator is asserted non-zero so a walk that found nothing cannot pass; the
    offenders must equal the set Akien decided to keep (today: none)."""
    walked = offenders = 0
    named = []
    for vals_dir in sorted((_REPO_ROOT / "cairn").rglob("validations")):
        if not vals_dir.is_dir():
            continue
        comp_dir = vals_dir.parent
        seals = [p for p in vals_dir.glob("*.json")]
        walked += len(seals)
        for f in green_seal_names_a_tooth(_row(comp_dir.name), comp_dir):
            offenders += 1
            named.append(str((comp_dir / "validations" / f["values"]["seal"]).relative_to(_REPO_ROOT)))
    print(f"  live corpus: {offenders} green seal(s) naming no tooth over {walked} standing seals")
    # The floor is a bound, not a snapshot: 193 seal files stood on 2026-09-16 (the 224 of the
    # 2026-09-15 census counted seal RECORDS; six orphan/probe seals were removed by answer).
    assert walked > 100, f"the walk found only {walked} seals — it did not see the corpus"
    assert sorted(named) == sorted(KEPT_BY_ANSWER), (
        f"{offenders} green seal(s) name no tooth: {named}")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
