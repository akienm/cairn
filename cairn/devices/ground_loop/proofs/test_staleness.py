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
    diagnostics, is_stale, module_drift, read_all,
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
    """LAW 9 ON THE PREDICATE ITSELF. Unanswerable must not read as fresh — a predicate that
    silently degrades to green is how a watch layer goes dark quietly, which is the entire
    outage this ticket is about.

    THE FIXTURE MOVED WITH THE MECHANISM (2026-08-18). It used to remove the ``.pyc``, because
    the predicate read its evidence out of the bytecode header; that comparison is retired,
    and the case it called unanswerable — a module whose file gained a symbol — is now
    ANSWERED, which is the improvement. What remains genuinely unanswerable is a held object
    that cannot be matched to a code object at all, so that is what the fixture builds now.
    Two shapes, because they fail differently: an object the process holds that has no
    ``__code__`` (here a C builtin, standing for every decorated-without-``__wrapped__``,
    extension-backed or dynamically-bound attribute), and a source that no longer parses.
    """
    w = _world()
    try:
        w.write("held.py", "def f():\n    return 1\n")
        mod = w.load("held.py")
        mod.f = len                             # a C builtin: no code object to compare
        findings = w.drift()
        blind = [f for f in findings if f["module"] == f"{w.name}.held"]
        assert blind and blind[0]["evidence"] == UNDECIDABLE, findings
        assert blind[0]["undecidable_objects"] == 1, blind
    finally:
        w.close()

    w = _world()
    try:
        w.write("broken.py", "def f():\n    return 1\n")
        w.load("broken.py")
        w.write("broken.py", "def f(:\n")       # mid-write, or simply broken
        findings = w.drift()
        blind = [f for f in findings if f["module"] == f"{w.name}.broken"]
        assert blind and blind[0]["evidence"] == UNDECIDABLE, findings
    finally:
        w.close()


def test_a_second_interpreter_cannot_repair_the_evidence_for_this_one():
    """THE TOOTH THE FIRST BUILD COULD NOT HAVE PASSED, and it is the reason there was a
    second build. Written 2026-08-18, ticket staleness-is-about-this-process-not-about-disk.

    The retired predicate compared the source's mtime to the mtime embedded in that module's
    ``.pyc`` header. BOTH TERMS ARE ON DISK, and a ``.pyc`` is a SHARED artifact — so any
    second process that imports the module rewrites the header, and the evidence is repaired
    while this process is not. That is not a bug in the comparison; it is the comparison
    being unable, in principle, to tell two processes of different ages apart over one tree.

    THE SECOND INTERPRETER IS THE ENTIRE FIXTURE. Without it, the header still names the
    pre-edit mtime and the old predicate answers correctly — which is exactly how eleven
    green teeth stood over a live misattribution, and why this one runs a real subprocess
    rather than simulating one. Verified to fail by name against HEAD's staleness.py before
    the fix landed; it must fail, not error, or it is reproducing nothing.

    Both faces are asserted here, because the repaired header hides both: the LOUD one (a
    name the file gained, which raises ImportError at the importer) and the QUIET one (a body
    that changed with its name unchanged, which reports healthy at every surface).
    """
    import subprocess

    for body, expect_in_detail in (
            ("def f():\n    return 2\nARRIVED_LATER = 3\n", "'ARRIVED_LATER'"),
            ("def f():\n    return 2\n", "'f'")):
        w = _world()
        try:
            path = w.write("held.py", "def f():\n    return 1\n")
            mod = w.load("held.py")
            assert getattr(mod, "__cached__", None) and os.path.exists(mod.__cached__), \
                "fixture needs real bytecode for a second interpreter to repair"

            w.write("held.py", body)
            w.age_the_source(path)

            # The second interpreter. It re-imports the module in a process of its own,
            # which rewrites the shared .pyc header to the CURRENT source mtime.
            before = os.stat(mod.__cached__).st_mtime
            subprocess.run([sys.executable, "-c", f"import {w.name}.held"],
                           cwd=str(w.root), check=True,
                           env={"PYTHONPATH": str(w.root), "PATH": "/usr/bin:/bin"})
            assert os.stat(mod.__cached__).st_mtime != before, \
                "the second interpreter did not rewrite the bytecode — fixture never took"

            # The retired comparison now reads CLEAN. Asserted, not assumed: if it did not,
            # this tooth would be green for a reason unrelated to the property. Read INLINE
            # from the header rather than through the module's helper, so this tooth runs
            # unchanged against the build that predates the helper — which is the only way
            # "it reds against HEAD" is a claim anyone can re-check later.
            import struct
            with open(mod.__cached__, "rb") as fh:
                head = fh.read(16)
            embedded = struct.unpack("<I", head[8:12])[0]
            assert embedded == (int(os.stat(path).st_mtime) & 0xFFFFFFFF), \
                "the fixture failed to repair the header, so it reproduces nothing"

            findings = [f for f in w.drift() if f["module"] == f"{w.name}.held"]
            assert findings and findings[0]["evidence"] == REWRITTEN, findings
            assert expect_in_detail in findings[0]["detail"], findings[0]["detail"]
        finally:
            w.close()


def test_the_predicate_names_no_symbol_and_reads_no_clock():
    """THE CHARTER'S BAN, READ AS A CHECK RATHER THAN AS CARE. ground_loop's falsifier reds
    'the predicate special-casing the two faces seen in 2026-08 by symbol name or error
    text', and clause (5) forbids the heartbeat holding runtime state of its own.

    A SPECIAL CASE IS A COMPARISON OR AN ATTRIBUTE REACH — never a sentence. The first draft
    of this tooth grepped the source text and bit on the word ``ImportError`` inside a
    ``detail`` string, which is the module EXPLAINING which face a difference corresponds to.
    Explaining a face is the opposite of enumerating one, so the scan reads the deciding
    functions' syntax instead: every identifier they touch, and every string constant that
    takes part in a comparison. The prose is left alone deliberately, and that IS the bound —
    this shows the banned spellings decide nothing, and cannot show that no other
    face-specific shortcut hides under a name nobody thought to list.
    """
    import ast as _ast
    import inspect
    import textwrap
    from cairn.devices.ground_loop import staleness as st

    touched: set[str] = set()
    for fn in (st.module_drift, st.held_vs_disk, st._same_code, st._index_code,
               st._held_code, st._unconditional_definitions):
        tree = _ast.parse(textwrap.dedent(inspect.getsource(fn)))
        for node in _ast.walk(tree):
            if isinstance(node, _ast.Name):
                touched.add(node.id)
            elif isinstance(node, _ast.Attribute):
                touched.add(node.attr)
            elif isinstance(node, _ast.Compare):
                for part in [node.left, *node.comparators]:
                    if isinstance(part, _ast.Constant) and isinstance(part.value, str):
                        touched.add(part.value)

    for banned in ("Probe", "common_shape_record", "ImportError", "cannot import name",
                   "st_mtime", "__cached__", "time", "utime", "_bytecode_source_mtime"):
        assert banned not in touched, (banned, sorted(touched))


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
    # CLOSED ON PURPOSE, and it grew by one on 2026-08-18: the bytecode-header comparison was
    # the predicate until it was measured wrong, and it now rides beside the other retired
    # one. Equality rather than containment, so a THIRD thing cannot join the payload without
    # a hand deciding it belongs there.
    assert d["not_the_predicate"] == ["tree_newer_than_process",
                                      "bytecode_header_disagrees"], d.get("not_the_predicate")
    for key in d["not_the_predicate"]:
        assert key in d, (key, sorted(d))
    assert isinstance(d["process_started"], float)
    assert d["pid"] == os.getpid()


def test_the_coverage_tally_separates_nothing_drifted_from_i_could_not_look():
    """LAW 9 ON THE READER'S SIDE, and it was found by aiming the finished build at the real
    world rather than by reasoning: over 77 held modules the payload reported
    ``undecidable_objects: 0`` while 181 objects were in fact unreachable. Both numbers were
    honest and the pair was misleading, because the count was summed over FINDINGS and a
    clean process has none — so "compared everything, all fresh" and "compared nothing"
    printed identically.

    The tally belongs to the PASS. It is ``None`` when the caller supplies findings, because
    a coverage number invented for a list handed in from elsewhere is a number about nothing.
    """
    findings, tally = read_all()
    assert tally["modules_read"] > 0, tally
    assert tally["comparable_objects"] > tally["modules_read"], tally
    assert tally["undecidable_objects"] >= 0, tally
    assert diagnostics(findings=findings, tree=False)["coverage"] is None

    # AND THE TWO COUNTS MAY NOT SHARE A NAME. The payload carries an unreachable-object
    # count summed over the FINDINGS and another summed over the PASS; spelling both
    # "undecidable_objects" would re-lay the exact trap this tooth exists for, one line
    # apart, in the surface a reader consults precisely when something is wrong.
    d = diagnostics()
    assert "undecidable_objects" not in d, sorted(d)
    # An INVARIANT, not a snapshot: the findings-derived count sums over every finding, and
    # ``drifted`` is a subset of those, so it can only be greater or equal — on this healthy
    # process both are 0, which is exactly the reading that must not be mistaken for coverage.
    assert d["undecidable_objects_in_findings"] >= sum(
        f.get("undecidable_objects", 0) for f in d["drifted"]), d
    assert d["coverage"]["undecidable_objects"] >= d["undecidable_objects_in_findings"], d

    w = _world()
    try:
        w.write("held.py", "def f():\n    return 1\n")
        mod = w.load("held.py")
        mod.f = len                                  # unreachable: no code object
        _, t = read_all(root=w.root)
        assert t["comparable_objects"] == 0 and t["undecidable_objects"] == 1, t
    finally:
        w.close()


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
