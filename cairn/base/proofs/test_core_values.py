"""Pin test for CP1-CP6 — the teeth of the "values in the base" contract (Law 2).

It is not enough to *place* the values; this test fails if the enforced form drifts
from the canonical words, changes the set, or reorders them. Grafted with its subject
from the quarry and re-pointed at Cairn's commons record.

Runnable two ways, no test framework required today (the tester device will own how
proofs run when it lands):
    python3 cairn/base/proofs/test_core_values.py     # bare: exit 0 = green
    pytest cairn/base/proofs/test_core_values.py       # discovered as test_* functions

Kept import-light on purpose (no DB, no device boot).

Scope: this proof pins the *values* (set, order, immutability, commons agreement).
The composition teeth — "no BaseDevice/BaseShim subclass can lack the values" — live
in the sibling proofs/test_composition.py (they needed the bases to exist; they do
now). See base/intention+why.json.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# Run bare (`python3 cairn/base/proofs/test_core_values.py`) without an editable
# install: put the repo root on the path so the `cairn` package imports. parents[3]
# is the cairn repo root (proofs -> base -> cairn pkg -> repo). Harmless when the
# package is already installed.
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.core_values import CORE_VALUES, CoreValue, CoreValuesMixin

EXPECTED_IDS = ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]

# The canonical words live in the sibling commons repo (three-roots invariant:
# ~/dev/src/CairnCommons). The repo root's parent is src/.
_COMMONS_RECORD = _REPO_ROOT.parent / "CairnCommons" / "intentions" / "core-values.md"


def _norm(text: str) -> str:
    """Collapse all whitespace so line-wrapped narratives compare as substrings."""
    return re.sub(r"\s+", " ", text).strip()


def test_canonical_values_are_the_six_in_order():
    assert [v.id for v in CORE_VALUES] == EXPECTED_IDS
    for v in CORE_VALUES:
        assert isinstance(v, CoreValue)
        assert v.narrative.strip(), f"{v.id} missing narrative"
        assert v.why.strip(), f"{v.id} missing why (CP3: there's always a why)"


def test_core_value_record_is_frozen():
    # The contract must be immutable — a mutable CoreValue is a silent drift surface.
    try:
        CORE_VALUES[0].narrative = "tampered"  # type: ignore[misc]
    except AttributeError:  # dataclass(frozen=True) raises FrozenInstanceError (an AttributeError)
        pass
    else:  # pragma: no cover
        raise AssertionError("CoreValue must be frozen")


def test_core_value_lookup_helper():
    assert CoreValuesMixin.core_value("CP1").narrative == "I don't know"
    try:
        CoreValuesMixin.core_value("CP99")
    except KeyError:
        pass
    else:  # pragma: no cover
        raise AssertionError("core_value should raise KeyError for unknown id")


def test_code_matches_the_commons_record():
    # Falsifier from core-values.md itself: "Any drift between the code and this
    # record is a red — physics, not a keep-in-sync comment." Bites when the sibling
    # commons repo is present (Akien's env); loudly abstains if it is not, rather
    # than making green depend on an external checkout (CP1 — say what wasn't measured).
    if not _COMMONS_RECORD.exists():
        print(f"NOTE: commons record not found at {_COMMONS_RECORD} — drift gate ABSTAINED (not measured)")
        return False
    record = _norm(_COMMONS_RECORD.read_text())
    for v in CORE_VALUES:
        assert v.id in record, f"{v.id} absent from commons record"
        assert _norm(v.narrative) in record, f"{v.id} narrative drifted from commons record"
        assert _norm(v.why) in record, f"{v.id} why drifted from commons record"
    return True


def _main() -> int:
    checks = [
        test_canonical_values_are_the_six_in_order,
        test_core_value_record_is_frozen,
        test_core_value_lookup_helper,
        test_code_matches_the_commons_record,
    ]
    drift_ran = None
    for check in checks:
        result = check()
        if check is test_code_matches_the_commons_record:
            drift_ran = result
        print(f"  PASS  {check.__name__}")
    gate = "bit" if drift_ran else "ABSTAINED (commons record absent)"
    print(f"green — CP1-CP6 pinned; commons drift gate {gate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
