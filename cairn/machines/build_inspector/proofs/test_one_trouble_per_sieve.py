"""Proof for ticket cd27b72ba964 — a build inspector finding is ONE trouble per sieve, its count
rising each run it stands, never one trouble per component the sieve flags.

Akien, 2026-10-18: *"A trouble is ONLY EVER ONE. All those other things are broke. They should be
incrementing a counter, not adding another trouble."* The raise contract already said it
(cairn/tools/base/diagnostic.py: ``identity`` names the DEFECT, not the occurrence); the inspector
named each trouble ``inspector-new-finding-<method>-<at>``, so one sieve finding stood as one
trouble per component — 45 ``encapsulation_holds`` troubles and 3 ``device_isolation_holds``,
counted in ~/.cairn/logs/cairn/0/troubletickets/cleared that day.

The teeth, every one against scratch roots (the raiser and the store both live under them, so
HOME is never written):

  1. ONE RAISE PER SIEVE. Three above-baseline findings of one sieve at three components plus one
     of a second sieve raise exactly twice, under identities that name the sieve alone, and the
     first raise's detail names all three components.
  2. THE COUNT RISES. The same findings raised on a second run, folded by trouble's own drain,
     leave ONE live file for the sieve, at count 2.
  3. THE STANDING SET IS PER SIEVE. ``_standing_finding_ids`` returns sieve identities only.
  4. THE OLD FAN-OUT CLEARS. A reconcile over a store holding an old per-component trouble and the
     new per-sieve one clears the old and keeps the new.
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


class _Scratch:
    """Scratch roots, the inspector's raiser pointed under them, and trouble's drain over them."""

    def __enter__(self):
        from cairn.tools.base.address import log_path
        self._tmp = tempfile.TemporaryDirectory(prefix="cairn-proof-one-trouble-per-sieve-")
        self.roots = {k: Path(self._tmp.name) for k in ("repo", "commons", "instance")}
        self.store = log_path("cairn", 0, self.roots) / "troubletickets"
        self.store.mkdir(parents=True)
        self._mod = __import__("importlib").import_module("cairn.machines.build_inspector.inspector")
        self._real = self._mod._raiser
        from cairn.tools.base.diagnostic import ModuleRaiser
        roots = self.roots
        self._mod._raiser = lambda: ModuleRaiser("build_inspector", roots=roots)
        return self

    def drain(self):
        from cairn.devices.trouble.shim import TroubleShim
        TroubleShim(roots=self.roots).drain()

    def live(self):
        return sorted(p.stem for p in self.store.glob("*.json"))

    def __exit__(self, *exc):
        self._mod._raiser = self._real
        self._tmp.cleanup()


class _Recorder:
    def __init__(self):
        self.raised = []

    def raise_trouble(self, identity, *, why, detail=None, **kw):
        self.raised.append({"identity": identity, "why": why, "detail": detail})


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


def the_count_rises():
    with _Scratch() as s:
        _inspector._file_troubles_for_new_findings(_FINDINGS)
        s.drain()
        _inspector._file_troubles_for_new_findings(_FINDINGS)
        s.drain()
        alpha = _inspector._finding_trouble_id(_A)
        mine = [n for n in s.live() if n.startswith("inspector-new-finding-proof-sieve")]
        assert mine == sorted([alpha, _inspector._finding_trouble_id(_B)]), \
            f"live after two runs: {mine!r}"
        ticket = json.loads((s.store / f"{alpha}.json").read_text(encoding="utf-8"))
        assert ticket.get("count") == 2, f"count after two runs: {ticket.get('count')!r}"


def the_standing_set_is_per_sieve():
    d = Path(tempfile.mkdtemp(prefix="cairn-proof-one-trouble-baseline-"))
    bp = d / "finding_baseline.json"
    bp.write_text(json.dumps({"known": [], "updated": "2026-10-18"}), encoding="utf-8")
    still = _inspector._standing_finding_ids(_FINDINGS, baseline_path=bp)
    want = sorted([_inspector._finding_trouble_id(_A), _inspector._finding_trouble_id(_B)])
    assert still == want, f"standing {still!r}, want {want!r}"


def the_old_fan_out_clears():
    with _Scratch() as s:
        old = "inspector-new-finding-proof-sieve-alpha-devices-one"
        from cairn.tools.base.diagnostic import ModuleRaiser
        ModuleRaiser("build_inspector", roots=s.roots).raise_trouble(
            old, why="the per-component identity this ticket retires", detail={"at": "devices/one"})
        _inspector._file_troubles_for_new_findings(_FINDINGS[:3])
        s.drain()
        assert old in s.live(), f"fixture did not land: {s.live()!r}"
        mod = __import__("importlib").import_module("cairn.machines.build_inspector.inspector")
        real_bp = mod._BASELINE_PATH
        mod._BASELINE_PATH = Path(tempfile.mkdtemp(prefix="cairn-proof-one-trouble-bp-")) / "none.json"
        try:
            mod._reconcile_cleared_findings(_FINDINGS[:3])
        finally:
            mod._BASELINE_PATH = real_bp
        s.drain()
        live = s.live()
        assert old not in live, f"the old per-component trouble still stands: {live!r}"
        assert _inspector._finding_trouble_id(_A) in live, f"the sieve's trouble was cleared: {live!r}"


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


_PARTS = [one_raise_per_sieve, the_count_rises, the_standing_set_is_per_sieve,
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
