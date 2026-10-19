"""Proof for ticket cd27b72ba964 — a build inspector finding is ONE trouble per sieve, its count
rising each run it stands, never one trouble per component the sieve flags.

Akien, 2026-10-18: *"A trouble is ONLY EVER ONE. All those other things are broke. They should be
incrementing a counter, not adding another trouble."* The raise contract already said it
(cairn/tools/base/diagnostic.py: ``identity`` names the DEFECT, not the occurrence); the inspector
named each trouble ``inspector-new-finding-<method>-<at>``, so one sieve finding stood as one
trouble per component — 45 ``encapsulation_holds`` troubles and 3 ``device_isolation_holds``,
counted in ~/.cairn/logs/cairn/0/troubletickets/cleared that day.

The teeth read only what the inspector itself hands its raiser (RULE 1: a proof measures only its
own component). Trouble's fold, where a raise of a standing identity becomes a rising count and a
reconcile clears what its still-set omits, is trouble's to prove and is proven at its own address:

  1. ONE RAISE PER SIEVE. Three above-baseline findings of one sieve at three components plus one
     of a second sieve raise exactly twice, under identities that name the sieve alone, and the
     first raise's detail names all three components.
  2. EVERY RUN RAISES THE SAME IDENTITY. The same findings on a second run raise the very
     identities of the first, so trouble's fold counts one trouble up rather than filing another.
  3. THE STANDING SET IS PER SIEVE. ``_standing_finding_ids`` returns sieve identities only.
  4. THE OLD FAN-OUT CLEARS. The reconcile hands trouble a still-set under the
     ``inspector-new-finding-`` prefix that holds the sieve's identity and not the old
     per-component one, so trouble clears the old and keeps the new.
  5. THE DETAIL STAYS BOUNDED. A sieve flagging fifteen components carries ten findings whole,
     names all fifteen components, and counts the five it left out.

The subject is bound at call time, so ``cairn test --hollow`` reverting inspector.py reads as red
teeth rather than an import that never ran.

    bin/cairn test cairn/machines/build_inspector/proofs/test_one_trouble_per_sieve.py
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

# The falsifier is one unnumbered clause, so ONE composite tooth claims it; its five parts
# still print one by one.
PROVES = {"cd27b72ba964": {"all": "one_trouble_per_sieve"}}

PASS = 0
FAIL = 0


def _finding(method, at):
    return {"method": method, "at": at, "about": f"{method} fixture at {at}",
            "expected": True, "actual": False, "compare": "exact",
            "values": {"fixture": "cd27b72ba964"}}


_A = "proof_sieve_alpha"
_B = "proof_sieve_beta"
_FINDINGS = [_finding(_A, "devices/one"), _finding(_A, "devices/two"),
             _finding(_A, "machines/three"), _finding(_B, "tools/four")]


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        # The detail rides its own line: a hollow reading takes the whole PASS/FAIL line as the name.
        print(f"  FAIL  {name}")
        print(f"        {type(exc).__name__}: {exc}"[:400])
    else:
        PASS += 1
        print(f"  PASS  {name}")


class _Recorder:
    def __init__(self):
        self.raised = []

        self.reconciled = []

    def raise_trouble(self, identity, *, why, detail=None, **kw):
        self.raised.append({"identity": identity, "why": why, "detail": detail})

    def reconcile_troubles(self, scope, still, **kw):
        self.reconciled.append({"scope": scope, "still": list(still)})


def _recorded(fn):
    """Run ``fn(mod)`` with the inspector's raiser swapped for a recorder; return the recorder."""
    rec = _Recorder()
    mod = __import__("importlib").import_module("cairn.machines.build_inspector.inspector")
    real = mod._raiser
    mod._raiser = lambda: rec
    try:
        fn(mod)
    finally:
        mod._raiser = real
    return rec


def one_raise_per_sieve():
    rec = _Recorder()
    real = _inspector._raiser
    mod = __import__("importlib").import_module("cairn.machines.build_inspector.inspector")
    mod._raiser = lambda: rec
    try:
        mod._file_troubles_for_new_findings(_FINDINGS)
    finally:
        mod._raiser = real
    ids = [r["identity"] for r in rec.raised]
    want = [_inspector._finding_trouble_id(_A), _inspector._finding_trouble_id(_B)]
    assert ids == want, f"raised {ids!r}, want one per sieve {want!r}"
    for i in ids:
        for comp in ("one", "two", "three", "four"):
            assert comp not in i, f"the identity {i!r} names a component ({comp})"
    detail = rec.raised[0]["detail"] or {}
    assert detail.get("components") == ["devices/one", "devices/two", "machines/three"], detail


def every_run_raises_the_same_identity():
    def two_runs(mod):
        mod._file_troubles_for_new_findings(_FINDINGS)
        mod._file_troubles_for_new_findings(_FINDINGS)
    ids = [r["identity"] for r in _recorded(two_runs).raised]
    one = [_inspector._finding_trouble_id(_A), _inspector._finding_trouble_id(_B)]
    assert ids == one + one, f"two runs raised {ids!r}, want the same {one!r} twice"


def the_standing_set_is_per_sieve():
    d = Path(tempfile.mkdtemp(prefix="cairn-proof-one-trouble-baseline-"))
    bp = d / "finding_baseline.json"
    bp.write_text(json.dumps({"known": [], "updated": "2026-10-18"}), encoding="utf-8")
    still = _inspector._standing_finding_ids(_FINDINGS, baseline_path=bp)
    want = sorted([_inspector._finding_trouble_id(_A), _inspector._finding_trouble_id(_B)])
    assert still == want, f"standing {still!r}, want {want!r}"


def the_old_fan_out_clears():
    old = "inspector-new-finding-proof-sieve-alpha-devices-one"
    bp = Path(tempfile.mkdtemp(prefix="cairn-proof-one-trouble-bp-")) / "none.json"

    def reconcile(mod):
        real_bp = mod._BASELINE_PATH
        mod._BASELINE_PATH = bp
        try:
            mod._reconcile_cleared_findings(_FINDINGS[:3])
        finally:
            mod._BASELINE_PATH = real_bp
    calls = _recorded(reconcile).reconciled
    assert len(calls) == 1, f"{len(calls)} reconcile calls"
    assert calls[0]["scope"] == "inspector-new-finding-", calls[0]
    still = calls[0]["still"]
    assert old not in still, f"the old per-component identity still stands: {still!r}"
    assert _inspector._finding_trouble_id(_A) in still, f"the sieve's identity was dropped: {still!r}"


def the_detail_stays_bounded():
    rec = _Recorder()
    mod = __import__("importlib").import_module("cairn.machines.build_inspector.inspector")
    real = mod._raiser
    mod._raiser = lambda: rec
    many = [_finding(_A, f"devices/c{i:02d}") for i in range(15)]
    try:
        mod._file_troubles_for_new_findings(many)
    finally:
        mod._raiser = real
    assert len(rec.raised) == 1, f"{len(rec.raised)} raises for one sieve"
    detail = rec.raised[0]["detail"] or {}
    assert len(detail.get("components") or []) == 15, detail.get("components")
    assert len(detail.get("findings") or []) == 10, len(detail.get("findings") or [])
    assert detail.get("findings_omitted") == 5, detail.get("findings_omitted")


_PARTS = [one_raise_per_sieve, every_run_raises_the_same_identity, the_standing_set_is_per_sieve,
          the_old_fan_out_clears, the_detail_stays_bounded]


def one_trouble_per_sieve():
    """The composite the PROVES key names: every part green."""
    before = FAIL
    for fn in _PARTS:
        _tooth(fn.__name__, fn)
    assert FAIL == before, f"{FAIL - before} part(s) red"


if __name__ == "__main__":
    _tooth("one_trouble_per_sieve", one_trouble_per_sieve)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
