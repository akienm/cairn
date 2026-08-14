"""PROOF — the loop can tell ITS OWN AGE from a device's defect, and does not cry wolf.

Ticket the-loop-names-its-own-staleness-instead-of-benching-a-device. For 29 hours a
daemon that outlived a file move reported ``PROBE is Probe, not a Probe`` and benched
fifteen devices. The message was self-refuting and pointed at the wrong party, and being
pointed at the wrong party is what made it quiet.

THESE TEETH WERE WRITTEN BEFORE THE PREDICATE THEY JUDGE — the corpus's judges-before-the-
judged order, and here it is not a preference. The appealing implementation compares the
process start time to the newest mtime in the tree, and every test one would then think to
write goes green. THE SURVEY ALREADY FALSIFIED THAT PREDICATE against the live process:
the loop started 15:17:36 and an ordinary edit landed at 15:30, so the healthy running loop
read STALE. Any predicate that trips on an ordinary edit is worse than none, because a
staleness alarm that is always on is a bench that never lifts.

WHAT A HOLLOW BUILD PASSES AND THIS MUST NOT (Law 8):

  * Tree-newest-mtime > process-start. Dies at ``test_an_edit_to_a_file_this_process_never
    _imported_stays_green`` and at ``..._loaded_late_from_a_newly_written_file_stays_green``.
  * Special-casing today's two faces by symbol name or error text (``Probe``,
    ``common_shape_record``). The ticket's falsifier clause (3) refuses it and every tooth
    here names a symbol that never moved in this corpus.
  * Reporting green when it cannot see. A module with no timestamped bytecode is
    UNDECIDABLE, not fresh — absence of evidence is not evidence of freshness (Law 9), and
    ``test_a_module_it_cannot_judge_reads_undecidable_not_green`` bites exactly there.

AND THE CLAUSE MY OWN REPRODUCTION EARNED: the green cases are measured on a package with
NO staleness present. My first experiment checked for false positives on an already-stale
process, so its green proved nothing at all.

    python3 cairn/devices/ground_loop/proofs/test_staleness.py     # exit 0 = green
"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.tester.scratch import scratch_dir  # noqa: E402
from cairn.devices.ground_loop.staleness import (  # noqa: E402
    DRIFTED, UNDECIDABLE, VANISHED, REWRITTEN,
    diagnostics, is_stale, module_drift,
)

_PKG_SERIAL = [0]


class _World:
    """A temp package this process really imports — the only way to construct staleness
    honestly, because staleness is a property of a LOADED module and nothing else.

    Each world gets a unique package name so worlds cannot contaminate one another: the
    'green measured on an already-stale process' mistake is structurally impossible here,
    not merely avoided by care.
    """

    def __init__(self) -> None:
        _PKG_SERIAL[0] += 1
        self.name = f"stale_fixture_{_PKG_SERIAL[0]}"
        # Through the tester's own door, not tempfile: a proof that reaches the system
        # temp directly leaves what it makes behind, which is how 3581 of them piled up.
        self.root = scratch_dir(f"{self.name}-")
        (self.root / self.name).mkdir()
        (self.root / self.name / "__init__.py").write_text("", encoding="utf-8")
        sys.path.insert(0, str(self.root))

    def write(self, rel: str, body: str) -> Path:
        path = self.root / self.name / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def load(self, rel: str):
        return importlib.import_module(f"{self.name}.{rel[:-3].replace('/', '.')}")

    def age_the_source(self, path: Path, seconds: int = 3600) -> None:
        """Rewrite-in-place, with the mtime moved by hand.

        Sleeping past the bytecode header's one-second resolution would work and would cost
        a second per tooth; ``utime`` states the same fact in one call. What matters is that
        the SOURCE mtime changes while the bytecode Python already wrote does not — which is
        exactly what happens when a file is edited under a running process.
        """
        st = os.stat(path)
        os.utime(path, (st.st_atime + seconds, st.st_mtime + seconds))

    def drift(self) -> list[dict]:
        return module_drift(root=self.root)

    def close(self) -> None:
        for name in [n for n in sys.modules if n.split(".")[0] == self.name]:
            del sys.modules[name]
        if str(self.root) in sys.path:
            sys.path.remove(str(self.root))
        shutil.rmtree(self.root, ignore_errors=True)


def _world():
    return _World()


# --- the anti-false-positive tooth: three greens that must stay green -------

def test_an_edit_to_a_file_this_process_never_imported_stays_green():
    """THE TOOTH THAT KILLS THE CHEAP PREDICATE. The tree's newest mtime moves forward and
    this process is not one bit staler for it, because it never loaded the file. A predicate
    that watches the TREE instead of what it HOLDS calls every ordinary edit staleness — and
    that is not a hypothetical, it is what the survey measured against the live loop."""
    w = _world()
    try:
        w.write("held.py", "VALUE = 1\n")
        w.load("held.py")
        assert not is_stale(w.drift()), w.drift()

        w.write("never_imported.py", "VALUE = 2\n")            # the tree just got newer
        untouched = w.write("also_never_imported.py", "VALUE = 3\n")
        w.age_the_source(untouched)                            # and newer still

        findings = w.drift()
        assert not is_stale(findings), findings
    finally:
        w.close()


def test_a_module_loaded_late_from_a_newly_written_file_stays_green():
    """THE SUBTLE FALSE POSITIVE, found by reproduction rather than reasoning. A module
    imported AFTER the process started, from a file written after the process started, is
    NEWER than the process on every clock — and is perfectly fresh, because the process
    loaded it from that very file. Process start is a lower bound on nothing useful."""
    w = _world()
    try:
        w.write("early.py", "VALUE = 1\n")
        w.load("early.py")

        w.write("late.py", "VALUE = 2\n")   # written now, well after this process began
        w.load("late.py")                   # ...and loaded now, so it matches its file

        findings = w.drift()
        assert not is_stale(findings), findings
    finally:
        w.close()


def test_a_genuinely_drifted_module_goes_red():
    """The red the greens above must not cost. Loaded, then the source changed underneath —
    the ImportError face of this outage (a symbol added to a module the process already
    held). Named generically: nothing here is called Probe or common_shape_record."""
    w = _world()
    try:
        path = w.write("held.py", "VALUE = 1\n")
        w.load("held.py")
        assert not is_stale(w.drift())

        w.write("held.py", "VALUE = 1\nARRIVED_LATER = 2\n")
        w.age_the_source(path)

        findings = w.drift()
        assert is_stale(findings), findings
        drifted = [f for f in findings if f["evidence"] in DRIFTED]
        assert [f["module"] for f in drifted] == [f"{w.name}.held"], drifted
        assert drifted[0]["evidence"] == REWRITTEN, drifted[0]
    finally:
        w.close()


def test_a_module_whose_file_moved_away_goes_red():
    """The IDENTITY face — the one that said 'PROBE is Probe, not a Probe' thirteen times.
    A module this process holds whose file is no longer at that address needs no clock at
    all to judge: the evidence is that the file is gone."""
    w = _world()
    try:
        path = w.write("relocated.py", "class Marker:\n    pass\n")
        w.load("relocated.py")
        assert not is_stale(w.drift())

        moved = w.root / w.name / "elsewhere" / "relocated.py"
        moved.parent.mkdir(parents=True, exist_ok=True)
        (moved.parent / "__init__.py").write_text("", encoding="utf-8")
        shutil.move(str(path), str(moved))

        findings = w.drift()
        assert is_stale(findings), findings
        gone = [f for f in findings if f["evidence"] == VANISHED]
        assert [f["module"] for f in gone] == [f"{w.name}.relocated"], gone
    finally:
        w.close()


def test_a_module_it_cannot_judge_reads_undecidable_not_green():
    """LAW 9 ON THE PREDICATE ITSELF. The REWRITTEN evidence is read out of the bytecode
    Python wrote at import; with no such bytecode (``-B``, a read-only tree, a hash-based
    pyc) the question is unanswerable. Unanswerable must not read as fresh — a predicate
    that silently degrades to green is how a watch layer goes dark quietly, which is the
    entire outage this ticket is about."""
    w = _world()
    try:
        path = w.write("held.py", "VALUE = 1\n")
        mod = w.load("held.py")
        cached = getattr(mod, "__cached__", None)
        assert cached and os.path.exists(cached), "fixture needs real bytecode to remove"

        w.write("held.py", "VALUE = 1\nARRIVED_LATER = 2\n")
        w.age_the_source(path)
        os.remove(cached)                       # the evidence is now unavailable

        findings = w.drift()
        blind = [f for f in findings if f["module"] == f"{w.name}.held"]
        assert blind and blind[0]["evidence"] == UNDECIDABLE, findings
    finally:
        w.close()


def test_a_module_that_never_came_from_a_file_is_not_drift():
    """THE FALSE POSITIVE THE PROOFS ABOVE COULD NOT SEE, found by aiming the finished
    predicate at the real world instead of at a fixture.

    Under ``python3 - <<EOF`` the ``__main__`` module's ``__file__`` is the literal string
    ``<stdin>``. That resolves to a path under the class-space root, the path does not exist,
    and the predicate read VANISHED — calling a healthy interpreter stale, which under the
    loop's new branch means no device is ever benched again. Every tooth above missed it
    because a proof run as a script has a real ``__main__`` with a real file. So the fixture
    is the shape itself, not the shell that produced it."""
    import types
    for pseudo in ("<stdin>", "<string>", "<frozen importlib._bootstrap>"):
        module = types.ModuleType("__main__")
        module.__file__ = pseudo
        findings = module_drift(modules={"__main__": module})
        assert findings == [], (pseudo, findings)


def test_the_real_outage_is_caught_by_this_predicate():
    """n=1 AGAINST THE THING THAT ACTUALLY HAPPENED. Commit ba50814 deleted
    ``cairn/base/probe.py``; the daemon went on holding a module bound to that address for 29
    hours. The frame below is that state — the path is what git says the process imported
    from, not a shape invented to be catchable."""
    import types
    frame = types.ModuleType("cairn.base.probe")
    frame.__file__ = str(Path(__file__).resolve().parents[3] / "cairn" / "base" / "probe.py")
    findings = module_drift(modules={"cairn.base.probe": frame})
    assert is_stale(findings), findings
    assert findings[0]["evidence"] == VANISHED, findings


# --- the payload is NOT the predicate ---------------------------------------

def test_the_diagnostic_payload_carries_the_falsified_comparison_labelled():
    """The tree's newest mtime against the process start is exactly the comparison that was
    falsified, and it is genuinely useful to a reader. It rides as PAYLOAD, under a key that
    says so, and nothing in the predicate reads it. A build that quietly promoted it back to
    the test would pass every tooth above only until an ordinary edit landed."""
    d = diagnostics()
    assert "tree_newer_than_process" in d, sorted(d)
    assert d["not_the_predicate"] == ["tree_newer_than_process"], d.get("not_the_predicate")
    assert isinstance(d["process_started"], float)
    assert d["pid"] == os.getpid()


def test_the_payload_says_when_the_predicate_is_blind():
    """A reader must be able to tell 'nothing has drifted' from 'I could not look'."""
    d = diagnostics()
    assert "undecidable" in d and isinstance(d["undecidable"], int), sorted(d)
    assert "bytecode_writing" in d, sorted(d)


def test_stripping_the_payload_changes_no_verdict():
    """THE VERDICT IS COMPUTED TWICE, WITH THE PAYLOAD POPULATED AND WITHOUT, AND THE TWO
    MUST BE IDENTICAL — the validate berth's fifth criterion, and the reason it exists is
    that the payload field IS the falsified comparison. Carrying a killed test next to a
    live one is only safe while nothing downstream can reach for it, so this asserts the
    reach rather than trusting the layout: same findings, ``tree=True`` and ``tree=False``,
    and every judgement-bearing key agrees while only the tree keys differ.

    ``is_stale`` taking findings and ``diagnostics`` taking the same findings is what makes
    this measurable at all — if the verdict were recomputed inside the reporter, 'with and
    without the payload' would not be two runs of one thing."""
    w = _world()
    try:
        path = w.write("held.py", "VALUE = 1\n")
        w.load("held.py")
        w.write("held.py", "VALUE = 1\nARRIVED_LATER = 2\n")
        w.age_the_source(path)
        findings = w.drift()

        loud = diagnostics(root=w.root, findings=findings, tree=True)
        quiet = diagnostics(root=w.root, findings=findings, tree=False)

        assert is_stale(findings) is True, findings
        assert loud["drifted"] == quiet["drifted"], (loud["drifted"], quiet["drifted"])
        assert loud["undecidable"] == quiet["undecidable"]
        # and the ONLY keys that moved are the payload half, which decides nothing
        differing = {k for k in loud if loud[k] != quiet.get(k)}
        assert differing <= {"tree_walked", "tree_newest_file", "tree_newest_mtime",
                             "tree_newer_than_process"}, differing
        assert quiet["tree_newer_than_process"] is None, quiet["tree_newer_than_process"]

        # the same identity on the GREEN side: a payload cannot manufacture a verdict either
        clean = module_drift(root=w.root, modules={})
        assert is_stale(clean) is False, clean
        assert diagnostics(root=w.root, findings=clean, tree=True)["drifted"] == \
            diagnostics(root=w.root, findings=clean, tree=False)["drifted"] == []
    finally:
        w.close()


def test_this_healthy_process_reads_not_stale_over_the_real_tree():
    """Measured on a process with NO staleness present — the clause my own reproduction
    earned by getting it wrong. This test process imported cairn seconds ago, so every
    module it holds matches its file, and the predicate must be silent over the real root.
    A predicate that reds here would red the healthy loop, which is the failure mode."""
    findings = module_drift()
    drifted = [f for f in findings if f["evidence"] in DRIFTED]
    assert not drifted, drifted


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — the proof reports, it does not raise
            failures += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — the loop knows its own age, and an ordinary edit is not staleness")
