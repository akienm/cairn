"""Proof of the finding baseline's two sides (commit d26147f, 2026-09-03): a finding above the
baseline raises a trouble, a finding covered by a ticket in the baseline does not — and the
RECONCILE reads the same set, so covering a standing finding by ticket retires its trouble at
the next run instead of sustaining it forever.

Measured 2026-09-13: `inspector-new-finding-machine-imports-no-device-machines-build-inspector`
was raised on the sieve's first live run (09-12), the covering ticket 135a905eac3c was cast the
same day, and adding it to finding_baseline.json changed nothing — `_reconcile_cleared_findings`
was handed EVERY finding, so trouble was told the covered identity still stood. Two hands, one
set: that is what this proof pins.
"""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))


class _Late:
    """Resolved at call time so a hollowed subject reds a tooth instead of killing the import."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_inspector = _Late("cairn.machines.build_inspector.inspector")

PASS = 0
FAIL = 0

_COVERED = {"method": "machine_imports_no_device", "at": "machines/build_inspector"}
_BARE = {"method": "component_color", "at": "tools/tree"}


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _baseline_covering(finding) -> Path:
    d = Path(tempfile.mkdtemp(prefix="inspector-proof-baseline-"))
    bp = d / "finding_baseline.json"
    bp.write_text(json.dumps({"known": [{**finding, "ticket": "135a905eac3c"}],
                              "updated": "2026-09-13"}))
    return bp


def a_covered_finding_is_below_the_baseline_and_a_bare_one_above():
    bp = _baseline_covering(_COVERED)
    above = _inspector.check_baseline([_COVERED, _BARE], baseline_path=bp)
    assert above == [_BARE], f"above baseline: {above!r}"


def the_standing_set_is_the_above_baseline_set():
    bp = _baseline_covering(_COVERED)
    still = _inspector._standing_finding_ids([_COVERED, _BARE], baseline_path=bp)
    bare_id = _inspector._finding_trouble_id(_BARE["method"], _BARE["at"])
    covered_id = _inspector._finding_trouble_id(_COVERED["method"], _COVERED["at"])
    assert still == [bare_id], f"standing: {still!r}"
    assert covered_id not in still


def the_reconcile_hands_trouble_only_what_still_stands_above_baseline():
    """The wiring tooth: `_reconcile_cleared_findings` is fed the whole finding list (as
    `_main` feeds it) and must pass trouble the above-baseline identities alone."""
    import importlib
    mod = importlib.import_module("cairn.machines.build_inspector.inspector")
    seen = {}

    class _Stub:
        def reconcile_troubles(self, prefix, still, **kw):
            seen["prefix"], seen["still"] = prefix, list(still)

    real_raiser, real_path = mod._raiser, mod._BASELINE_PATH
    mod._raiser = lambda: _Stub()
    mod._BASELINE_PATH = _baseline_covering(_COVERED)
    try:
        n = mod._reconcile_cleared_findings([_COVERED, _BARE])
    finally:
        mod._raiser, mod._BASELINE_PATH = real_raiser, real_path
    bare_id = mod._finding_trouble_id(_BARE["method"], _BARE["at"])
    assert seen.get("prefix") == "inspector-new-finding-", seen
    assert seen.get("still") == [bare_id], f"trouble was told these stand: {seen.get('still')!r}"
    assert n == 1, n


TEETH = [
    a_covered_finding_is_below_the_baseline_and_a_bare_one_above,
    the_standing_set_is_the_above_baseline_set,
    the_reconcile_hands_trouble_only_what_still_stands_above_baseline,
]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
