"""Proof: validation_store digests a component's current seals into one comparable string.

Ticket f43b5705ea03, child of 50e0581737e8 (a seal that reached another component turns yellow
when that component's seals move). The yellow sieve needs one token for a component's seal
state, recorded at seal time and recomputed later; ``seal_digest(component_dir)`` is it — a
sha256 over the sorted rows [stem, verdict, evidence.source_fingerprint] of each validations
file's CURRENT (last) record.

Five teeth, one per falsifier clause, each over a fresh scratch fixture component:

  1. Two calls over an unchanged fixture component return the same 64-hex string.
  2. Changing a current record's evidence.source_fingerprint changes the digest.
  3. Changing its verdict changes the digest.
  4. Inserting an older entry before the last, or changing only a timestamp field, leaves the
     digest unchanged.
  5. A component with no validations dir returns the sha256 of the canonical empty list.

seal_digest is resolved inside each tooth, so a hollow build reds every tooth instead of
crashing the import. This proof measures only cairn/tools/validation_store (RULE 1).

    python3 cairn/tools/validation_store/proofs/test_seal_digest.py
"""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "f43b5705ea03": {
        "1": "test_an_unchanged_component_digests_the_same",
        "2": "test_a_moved_fingerprint_moves_the_digest",
        "3": "test_a_changed_verdict_moves_the_digest",
        "4": "test_history_and_timestamps_do_not_move_the_digest",
        "5": "test_no_validations_digests_the_empty_list",
    },
}


def _record(verdict: str, fp: str, at: str = "2026-11-02T00:00:00+00:00") -> dict:
    return {"verdict": verdict, "at": at, "evidence": {"source_fingerprint": fp}}


def _component(trails: dict[str, list[dict]] | None) -> Path:
    """A scratch component; ``trails`` maps stem -> trail (None: no validations dir at all)."""
    comp = scratch_dir("seal_digest_fixture_component_") / "comp"
    comp.mkdir()
    if trails is not None:
        vdir = comp / "validations"
        vdir.mkdir()
        for stem, trail in trails.items():
            (vdir / f"{stem}.json").write_text(json.dumps(trail, indent=2), encoding="utf-8")
    return comp


def _write(comp: Path, stem: str, trail: list[dict]) -> None:
    (comp / "validations" / f"{stem}.json").write_text(json.dumps(trail, indent=2), encoding="utf-8")


def _base() -> dict[str, list[dict]]:
    return {"test_alpha": [_record("green", "aaa")],
            "test_beta": [_record("red", "bbb0"), _record("green", "bbb")]}


def _digest(comp: Path) -> str:
    from cairn.tools.validation_store.validation_store import seal_digest
    return seal_digest(str(comp))


def test_an_unchanged_component_digests_the_same():
    comp = _component(_base())
    first, second = _digest(comp), _digest(comp)
    assert first == second, (first, second)
    assert re.fullmatch(r"[0-9a-f]{64}", first), first


def test_a_moved_fingerprint_moves_the_digest():
    comp = _component(_base())
    before = _digest(comp)
    _write(comp, "test_beta", [_record("red", "bbb0"), _record("green", "bbb-moved")])
    assert _digest(comp) != before


def test_a_changed_verdict_moves_the_digest():
    comp = _component(_base())
    before = _digest(comp)
    _write(comp, "test_alpha", [_record("red", "aaa")])
    assert _digest(comp) != before


def test_history_and_timestamps_do_not_move_the_digest():
    comp = _component(_base())
    before = _digest(comp)
    _write(comp, "test_beta", [_record("red", "bbb0"), _record("open", "older"),
                               _record("green", "bbb")])
    assert _digest(comp) == before, "an older entry before the last moved the digest"
    _write(comp, "test_alpha", [_record("green", "aaa", at="2027-01-01T00:00:00+00:00")])
    assert _digest(comp) == before, "a timestamp-only change moved the digest"


def test_no_validations_digests_the_empty_list():
    comp = _component(None)
    empty = hashlib.sha256(json.dumps([], sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    assert _digest(comp) == empty, _digest(comp)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
