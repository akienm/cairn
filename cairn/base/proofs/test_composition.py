"""Composition teeth — every device and shim structurally carries CP1-CP6.

This is the tooth the last session filed as an OPEN EDGE and could not close:
it is not enough to *place* the values in a mixin, the proof must fail if any
device or shim could exist without them. That claim is a property of
``BaseDevice``/``BaseShim`` — unprovable until those bases exist. They exist now
(device.py, shim.py), so this closes the edge.

Two teeth, and they bite differently:
  - ``test_bases_compose_the_mixin`` is LIVE now: it asserts, directly, that
    ``BaseDevice`` and ``BaseShim`` compose ``CoreValuesMixin`` and carry the six
    in order. Drop the mixin from either base and this goes red.
  - ``test_no_subclass_lacks_the_values`` sweeps every imported subclass of the
    two bases. Today that set is empty (the tester isn't built), so it passes
    with zero offenders — an armed trap, not a vacuous claim: the first device or
    shim that overrides ``CORE_VALUES`` to something divergent, or regresses the
    mixin away, trips it. We say so out loud rather than let a green look like
    more coverage than it is (CP1 — name what wasn't measured).

Grafted-in-spirit from the quarry's CP1 boundary proof
(``UnseenUniversity/tests/test_core_values.py``), re-authored for Cairn's base.

Runnable bare (no test framework — the tester device will own how proofs run):
    python3 cairn/base/proofs/test_composition.py     # exit 0 = green
    pytest cairn/base/proofs/test_composition.py       # discovered as test_* fns
"""

from __future__ import annotations

import sys
from pathlib import Path

# Run bare without an editable install: put the repo root on the path so `cairn`
# imports. parents[3] is the repo root (proofs -> base -> cairn pkg -> repo).
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.core_values import CoreValuesMixin
from cairn.base.device import BaseDevice
from cairn.base.shim import BaseShim

EXPECTED_IDS = ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]
_BASES = (BaseDevice, BaseShim)


def _all_subclasses(cls: type) -> set[type]:
    """Every transitive subclass of `cls` currently imported into the interpreter."""
    seen: set[type] = set()
    stack = list(cls.__subclasses__())
    while stack:
        sub = stack.pop()
        if sub in seen:
            continue
        seen.add(sub)
        stack.extend(sub.__subclasses__())
    return seen


def test_bases_compose_the_mixin():
    # The structural guarantee: because both bases compose CoreValuesMixin, every
    # device and every shim inherits all six by Python's own semantics.
    for base in _BASES:
        assert issubclass(base, CoreValuesMixin), (
            f"{base.__name__} must compose CoreValuesMixin — without it, a device "
            f"or shim can exist that is not driven by the core values (Law 2)"
        )
        assert [v.id for v in base.CORE_VALUES] == EXPECTED_IDS, (
            f"{base.__name__}.CORE_VALUES drifted from the canonical six-in-order"
        )


def test_no_subclass_lacks_the_values():
    # Catches a future device/shim that overrides CORE_VALUES to something
    # divergent, or a regression that drops the mixin. Empty offender set today
    # (no devices yet) — an armed trap, not proven coverage.
    offenders = []
    for base in _BASES:
        for cls in _all_subclasses(base):
            ids = [getattr(v, "id", None) for v in getattr(cls, "CORE_VALUES", [])]
            if ids != EXPECTED_IDS:
                offenders.append(f"{cls.__module__}.{cls.__name__} -> {ids}")
    assert not offenders, "device/shim classes lacking core values: " + "; ".join(offenders)


def _swept_subclass_count() -> int:
    return sum(len(_all_subclasses(base)) for base in _BASES)


def _main() -> int:
    for check in (test_bases_compose_the_mixin, test_no_subclass_lacks_the_values):
        check()
        print(f"  PASS  {check.__name__}")
    swept = _swept_subclass_count()
    armed = (
        f"armed over {swept} imported subclass(es)"
        if swept
        else "armed, 0 subclasses yet (no devices built — trap set, not exercised)"
    )
    print(f"green — BaseDevice/BaseShim carry CP1-CP6; subclass sweep {armed}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
