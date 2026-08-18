"""IS THIS PROCESS OLDER THAN THE CODE IT IS JUDGING?

One predicate, asked only on the failure path, so a healthy heartbeat pays nothing for it.

WHY IT EXISTS. On 2026-08-13 the resident loop started at 15:35:43; that evening a commit
moved ``cairn/base/probe.py`` to ``cairn/tools/base/probe.py``. ``discovery.load_module``
execs each probe file off its path, so every probe bound the NEW ``Probe`` class while the
daemon's own frame still held the OLD one — two distinct class objects wearing one name.
``isinstance`` is an identity test, so it returned False, and the loop reported ``PROBE is
Probe, not a Probe`` thirteen times and benched thirteen devices. Two more failed with
``ImportError`` for symbols added to a module after the process started. ONE ROOT CAUSE,
TWO ERROR CLASSES, AND NEITHER OF THEM NAMES THE LOOP. Fifteen devices carrying twenty-two
probes went dark for 29 hours, so every watch armed since the move had never once fired.

WHAT THIS MEASURES, AND IT IS NOT THE TREE. The question is not "has any code changed" — an
ordinary edit changes code every few minutes and means nothing. It is "has a module THIS
PROCESS ALREADY HOLDS stopped matching its file on disk", which is a fact about ``sys.modules``
and disk, and about nothing else. The cheap predicate (newest mtime in the tree > process
start) was FALSIFIED against the live healthy loop during this ticket's survey: the loop
started 15:17:36 and an ordinary edit landed at 15:30. It rides in ``diagnostics()`` as
payload, under a key that says it is not the test.

TWO EVIDENCES ASSERT DRIFT, NAMING NO SYMBOL (the ticket's falsifier clause 3 — special-casing
today's two faces means the next rename produces a third face and the loop blames a device
again):

  VANISHED   the loaded module's file is no longer at that address. Needs no clock at all:
             a module whose source moved away cannot match it. This is the identity face.
  REWRITTEN  what this process HOLDS is not what the file on disk would produce now: a name
             the disk source defines unconditionally that the held module does not carry, or
             a held function whose bytecode differs from a fresh compile of the same source.

WHY THE EVIDENCE MUST CONTAIN THE ASKER, AND WHY THE BYTECODE HEADER DID NOT — the correction
this module was rebuilt for (2026-08-18). The first build compared the source's mtime to the
mtime embedded in that module's ``.pyc`` header, and both of those numbers are ON DISK. The
``.pyc`` is a SHARED artifact: any second interpreter that imports the module rewrites the
header, and the evidence is repaired while the asker is not. Measured, and the second process
was an ordinary proof run in the same tree — the loop then benched an innocent device at
03:44Z for an ``ImportError`` a fresh interpreter did not reproduce. A predicate whose two
terms are both on disk cannot in principle tell two processes of different ages apart, so no
amount of care at that comparison would have held.

The comparison here has the asker in it: one term is the code objects THIS PROCESS holds, the
other is a fresh compile of the source. It needs no clock and no bytecode file, so clause (5)
of ground_loop's falsifier — no runtime state beyond the ruled liveness record — is untouched
for the same reason it was before, by a mechanism that does not depend on who else has run.
It is also STRICTLY LESS SENSITIVE than the mtime comparison it replaces: a file rewritten
with identical content reads fresh, because content is what was ever meant.

AND IT ENUMERATES NO FACE. The loud face (a symbol added after boot — ``ImportError``) is a
name on disk the held module lacks; the quiet face (a probe body exec'd fresh off its path
whose ``from cairn... import`` dependencies still resolve through the boot-time
``sys.modules``) is a held function whose bytecode differs. Neither is detected by its error
text or its symbol name, which is what the charter reds.

WHERE IT IS BLIND, SAID OUT LOUD (Law 9 — absence of evidence is not evidence of freshness).
A held object that cannot be matched to a code object reads UNDECIDABLE and never CURRENT:
a decorated function with no ``__wrapped__``, a C extension attribute, a name bound at import
time by something other than its own ``def``. A module in which NOTHING was comparable reads
UNDECIDABLE whole. Names defined inside ``if``/``try`` at module level are not compared at
all — their absence is legitimate — and that is a deliberate blindness, recorded rather than
papered over. ``diagnostics()`` reports the undecidable counts, modules and objects apart, so
a reader can tell "nothing drifted" from "I could not look".

Proofs: ``proofs/test_staleness.py`` (this module) and ``proofs/test_discovery.py`` (the
benching decision it feeds), both written before this file existed.
"""

from __future__ import annotations

import ast
import os
import struct
import sys
from pathlib import Path
from types import CodeType

# The evidences. Two assert drift; one asserts only that the question could not be answered,
# and a caller that treats it as either green or red is reading the predicate wrong.
VANISHED = "VANISHED"
REWRITTEN = "REWRITTEN"
UNDECIDABLE = "UNDECIDABLE"
DRIFTED = (VANISHED, REWRITTEN)

# Probe modules are exec'd off their path under a synthetic name and RE-EXECUTED by design
# whenever their file changes (discovery.ProbeCache's mtime gate). Their freshness is not
# drift, and counting it would make every ordinary probe edit read as a stale process.
SYNTHETIC_PREFIX = "cairn._probes."

_PYC_HEADER = 16          # magic(4) flags(4) source-mtime(4) source-size(4)
_HASH_BASED = 0b1         # PEP 552: bit 0 of the flags word


def class_space_root() -> Path:
    """The root of the code this process judges — measured from where ``cairn`` was imported
    from, never spelled as a literal, so a checkout at a second address judges itself."""
    import cairn
    return Path(cairn.__file__).resolve().parents[1]


def process_started() -> float:
    """This process's start time as a POSIX timestamp.

    ``/proc/self`` is created when the process is, so its ctime IS the start time — no
    clock-tick arithmetic, no ``psutil``. Falls back to the interpreter's own boot moment
    where ``/proc`` is absent; the value is PAYLOAD only (see ``diagnostics``), so a coarse
    answer costs a reader nothing and the predicate nothing at all.
    """
    try:
        return os.stat("/proc/self").st_ctime
    except OSError:
        import time
        return time.time() - (time.monotonic() if hasattr(time, "monotonic") else 0.0)


def _is_pseudo_path(source: str) -> bool:
    """``<stdin>``, ``<string>``, ``<frozen importlib._bootstrap>`` — Python's own convention
    for a module that never came from a file at all.

    FOUND BY AIMING THIS PREDICATE AT THE REAL WORLD, not by reasoning about it. Under
    ``python3 - <<EOF`` the ``__main__`` module carries ``__file__ == "<stdin>"``, which
    resolves to a path under the class-space root that does not exist — so the predicate
    reported VANISHED and called a perfectly healthy interpreter stale. The proofs missed it
    because a proof run as a script has a real ``__main__``. A module with no file behind it
    cannot have drifted from one, and saying so is not an exemption: it is the measurement.
    """
    name = source.rsplit("/", 1)[-1]
    return name.startswith("<") and name.endswith(">")


def _bytecode_source_mtime(module) -> int | None:
    """The source mtime the loaded bytecode was compiled against, or ``None`` when there is
    no timestamp to compare — absent pyc, unreadable pyc, or hash-based bytecode.

    PAYLOAD ONLY SINCE 2026-08-18, and kept rather than deleted for the same reason
    ``tree_newer_than_process`` is kept: it was the predicate, it was measured wrong, and a
    reader standing over a misattributed bench still wants to see what it says. It decides
    nothing now — see ``diagnostics``' ``not_the_predicate`` list, where it is named.
    """
    cached = getattr(module, "__cached__", None)
    if not cached:
        return None
    try:
        with open(cached, "rb") as fh:
            head = fh.read(_PYC_HEADER)
    except OSError:
        return None
    if len(head) < _PYC_HEADER:
        return None
    if struct.unpack("<I", head[4:8])[0] & _HASH_BASED:
        return None
    return struct.unpack("<I", head[8:12])[0]


def _unconditional_definitions(tree: ast.Module) -> list[str]:
    """Names the disk source binds at module level UNCONDITIONALLY — direct children of the
    module body only.

    The bound is the point. A ``STORE_NAME`` scan of the compiled module would be one line
    shorter and would also collect every name bound inside ``if sys.version_info ...`` or
    ``try: import x except ImportError:``, where NOT carrying the name is the correct state
    for a live process. Those branches are how a module legitimately holds fewer names than
    its source mentions, so comparing them would manufacture drift out of a working import.
    """
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            names += [t.id for t in node.targets if isinstance(t, ast.Name)]
    return names


def _index_code(code: CodeType, prefix: str = "") -> dict[str, CodeType]:
    """Every function body a fresh compile produced, keyed by dotted name.

    One level of nesting is followed — a class body is itself a code object, and its methods
    are code objects inside it — because that is where the held side can be reached from
    (``getattr(cls, method)``). A closure nested inside a function is NOT indexed: there is no
    attribute path to it, so indexing it would only manufacture keys the held view must then
    report undecidable.
    """
    out: dict[str, CodeType] = {}
    for const in code.co_consts:
        if not isinstance(const, CodeType):
            continue
        name = prefix + const.co_name
        out[name] = const
        if not prefix and const.co_name not in ("<lambda>", "<listcomp>", "<dictcomp>",
                                                "<setcomp>", "<genexpr>"):
            for inner in const.co_consts:
                if isinstance(inner, CodeType):
                    out[name + "." + inner.co_name] = inner
    return out


def _held_code(module, dotted: str) -> CodeType | None:
    """The code object THIS PROCESS holds for ``dotted``, or ``None`` when it cannot be
    reached — which is a reading of UNDECIDABLE, never of freshness."""
    obj = module
    for part in dotted.split("."):
        obj = getattr(obj, part, None)
        if obj is None:
            return None
    for _ in range(8):                    # decorator chains, bounded so a cycle cannot hang
        wrapped = getattr(obj, "__wrapped__", None)
        if wrapped is None:
            break
        obj = wrapped
    obj = getattr(obj, "__func__", obj)   # classmethod / staticmethod / bound method
    code = getattr(obj, "__code__", None)
    return code if isinstance(code, CodeType) else None


def _same_code(a: CodeType, b: CodeType) -> bool:
    """Do these two code objects execute the same thing?

    Compared on instructions, names and constants — NOT on line numbers. A comment added
    above a function shifts every ``co_firstlineno`` below it while changing nothing this
    process would execute, and the caller's response to drift is to STOP BENCHING ANYBODY:
    over-detection hides real device defects just as surely as under-detection blames
    innocent ones. Nested code objects recurse, so a changed closure body still counts.
    """
    if a.co_code != b.co_code or a.co_names != b.co_names \
            or a.co_varnames != b.co_varnames or len(a.co_consts) != len(b.co_consts):
        return False
    for x, y in zip(a.co_consts, b.co_consts):
        if isinstance(x, CodeType) or isinstance(y, CodeType):
            if not (isinstance(x, CodeType) and isinstance(y, CodeType) and _same_code(x, y)):
                return False
        elif type(x) is not type(y) or x != y:
            return False
    return True


def held_vs_disk(module, path: Path) -> dict:
    """The one comparison: what this process holds for this module against what its file
    would produce now. Returns ``{verdict, detail, comparable, undecidable_objects}`` with
    verdict in ``REWRITTEN`` | ``UNDECIDABLE`` | ``None`` (nothing found to disagree).

    Never raises. A source that no longer parses reads UNDECIDABLE — the file is mid-write or
    broken, and calling that freshness would be the same failure one layer over.
    """
    try:
        src = path.read_bytes()
        tree = ast.parse(src, filename=str(path))
        fresh = compile(tree, str(path), "exec")
    except (OSError, SyntaxError, ValueError):
        return {"verdict": UNDECIDABLE, "comparable": 0, "undecidable_objects": 0,
                "detail": "the source on disk could not be read or compiled, so what this "
                          "process holds cannot be compared against it — this is not a "
                          "report that the two agree"}

    for name in _unconditional_definitions(tree):
        if not hasattr(module, name):
            return {"verdict": REWRITTEN, "comparable": 0, "undecidable_objects": 0,
                    "detail": f"the file defines {name!r} at module level and the module "
                              "this process holds does not carry it, so the process is "
                              "older than the file — this is the face that raises "
                              "ImportError at the importer, named here as a difference "
                              "rather than as an error string"}

    comparable = undecidable = 0
    for dotted, code in _index_code(fresh).items():
        held = _held_code(module, dotted)
        if held is None:
            undecidable += 1
            continue
        comparable += 1
        if not _same_code(held, code):
            return {"verdict": REWRITTEN, "comparable": comparable,
                    "undecidable_objects": undecidable,
                    "detail": f"the bytecode this process holds for {dotted!r} differs from "
                              "a fresh compile of the file, so it has been executing the old "
                              "body ever since the file changed — the quiet face, which "
                              "reports healthy at every surface"}
    if comparable == 0 and undecidable:
        return {"verdict": UNDECIDABLE, "comparable": 0, "undecidable_objects": undecidable,
                "detail": "nothing this module holds could be matched to a code object "
                          "(decorated without __wrapped__, C extension, or bound by "
                          "something other than its own def), so the question could not be "
                          "answered here"}
    return {"verdict": None, "comparable": comparable, "undecidable_objects": undecidable,
            "detail": ""}


def read_all(root: Path | None = None,
             modules: dict | None = None) -> tuple[list[dict], dict]:
    """The findings AND the coverage tally, from one pass.

    THE TALLY IS NOT BOOKKEEPING — it is the only thing that separates "I compared 485
    objects and none of them disagreed" from "I could compare nothing, so of course nothing
    disagreed". Findings alone cannot say it, because a clean process produces an EMPTY list
    either way; the first build's ``undecidable`` count had the same hole one level up and
    read 0 on a process where 181 objects were unreachable. Law 9 on the reader's side of the
    predicate: absence of evidence is not evidence of freshness, and a reader has to be able
    to tell the two apart without leaving.
    """
    findings = _drift(root, modules, tally := {"modules_read": 0, "comparable_objects": 0,
                                               "undecidable_objects": 0})
    return findings, tally


def module_drift(root: Path | None = None, modules: dict | None = None) -> list[dict]:
    """Every module THIS PROCESS holds, under ``root``, that no longer matches its file.

    Returns a list of ``{module, evidence, file, detail}`` — complete enough to resolve from
    the first report (I-complete-diagnostic-on-first-pass), because the caller turns these
    straight into a trouble's detail without going back to disk.

    Scoped by FILE PATH rather than by module name: ``skills.chart.live`` is this system's
    code just as much as ``cairn.tools.base.probe`` is, and a name-prefix scope would have
    silently excluded it. Never raises — a predicate that can take the heartbeat down is
    worse than the defect it reports.

    The findings alone; ``read_all`` returns the same pass's coverage tally beside them.
    """
    return _drift(root, modules, None)


def _drift(root: Path | None, modules: dict | None, tally: dict | None) -> list[dict]:
    root = Path(root) if root is not None else class_space_root()
    findings: list[dict] = []
    for name, module in list((modules if modules is not None else sys.modules).items()):
        if name.startswith(SYNTHETIC_PREFIX):
            continue
        source = getattr(module, "__file__", None)
        if not source:
            continue                      # builtins, namespace packages: nothing to compare
        if _is_pseudo_path(source):
            continue                      # never came from a file, so it cannot have left one
        try:
            path = Path(source).resolve()
            path.relative_to(root)
        except (ValueError, OSError):
            continue                      # outside the code we judge (stdlib, site-packages)
        if not path.exists():
            findings.append({
                "module": name, "evidence": VANISHED, "file": str(path),
                "detail": "this process holds a module whose file is no longer at that "
                          "address — anything it defines is a second object wearing the "
                          "same name as whatever now lives there",
            })
            continue
        read = held_vs_disk(module, path)
        if tally is not None:
            tally["modules_read"] += 1
            tally["comparable_objects"] += read["comparable"]
            tally["undecidable_objects"] += read["undecidable_objects"]
        if read["verdict"] is not None:
            findings.append({
                "module": name, "evidence": read["verdict"], "file": str(path),
                "detail": read["detail"],
                "comparable": read["comparable"],
                "undecidable_objects": read["undecidable_objects"],
            })
    return findings


def is_stale(findings: list[dict] | None = None) -> bool:
    """Does the drift actually ASSERT staleness? UNDECIDABLE does not — it says the question
    was unanswerable, and answering it 'yes' would make a tree with no bytecode permanently
    stale while answering 'no' would make it permanently, silently green."""
    if findings is None:
        findings = module_drift()
    return any(f["evidence"] in DRIFTED for f in findings)


def _bytecode_header_disagreements(root: Path) -> list[str]:
    """What the RETIRED comparison would say right now — payload for a reader, never a test.

    Cheap (one header read per held module, no compile), and it stays out of ``module_drift``
    so there is exactly one place drift is decided.
    """
    out = []
    for name, module in list(sys.modules.items()):
        if name.startswith(SYNTHETIC_PREFIX):
            continue
        source = getattr(module, "__file__", None)
        if not source or _is_pseudo_path(source):
            continue
        try:
            path = Path(source).resolve()
            path.relative_to(root)
            if not path.exists():
                continue
            embedded = _bytecode_source_mtime(module)
            if embedded is not None and (int(path.stat().st_mtime) & 0xFFFFFFFF) != embedded:
                out.append(name)
        except (ValueError, OSError):
            continue
    return out


def diagnostics(root: Path | None = None, findings: list[dict] | None = None,
                tree: bool = True) -> dict:
    """EVERYTHING A READER NEEDS TO TELL 'THE LOOP IS OLD' FROM 'THE DEVICE IS BROKEN'
    WITHOUT GOING BACK TO DISK — and NONE of it is the predicate.

    ``tree_newer_than_process`` is here on purpose and is labelled on purpose. It is the
    comparison this ticket's survey FALSIFIED against the live healthy loop, and it is still
    the first thing a human wants to know. Carrying it under ``not_the_predicate`` is the
    difference between a useful fact and a test that reds on every ordinary edit; the tooth
    ``test_the_diagnostic_payload_carries_the_falsified_comparison_labelled`` holds that line.
    """
    root = Path(root) if root is not None else class_space_root()
    coverage: dict | None = None
    if findings is None:
        findings, coverage = read_all(root)
    started = process_started()

    # The tree walk is the only expensive thing here — an rglob over the whole class space —
    # and the caller that runs on EVERY BEAT while a staleness lasts turns it off. A reader
    # asking once gets it; a heartbeat asking 86,400 times a day does not.
    newest_path, newest_mtime = None, 0.0
    if tree:
        try:
            for path in root.rglob("*.py"):
                if "__pycache__" in path.parts:
                    continue
                mtime = path.stat().st_mtime
                if mtime > newest_mtime:
                    newest_path, newest_mtime = str(path), mtime
        except OSError:
            pass

    return {
        "pid": os.getpid(),
        "process_started": float(started),
        "python": sys.executable,
        "root": str(root),
        "modules_held_under_root": sum(
            1 for m in list(sys.modules.values())
            if getattr(m, "__file__", None) and str(root) in str(getattr(m, "__file__", ""))),
        "drifted": [f for f in findings if f["evidence"] in DRIFTED],
        "undecidable": sum(1 for f in findings if f["evidence"] == UNDECIDABLE),
        # MODULES and OBJECTS counted apart, because they answer different questions: the
        # first is "how many modules could I not look at", the second is "inside the modules
        # I did look at, how much did I have to skip". A build that reported only the first
        # could go blind one object at a time without the number ever moving.
        #
        # AND THE NAME SAYS *IN FINDINGS*, because this sums over the FINDINGS and a clean
        # pass has none — it read 0 over a process where 181 objects were in fact
        # unreachable. That is the reading that sent this build back for the coverage tally
        # below, and leaving both keys spelled the same would have re-laid the same trap one
        # line apart: same word, two populations (Law 7 — a diagnostic surface may not be
        # ambiguous about what it counted).
        "undecidable_objects_in_findings": sum(f.get("undecidable_objects", 0)
                                               for f in findings),
        # THE COVERAGE OF THE PASS, not of the findings. ``None`` when the caller supplied
        # findings — the tally belongs to a pass, and inventing one for a list handed in from
        # elsewhere would be a number about nothing.
        "coverage": coverage,
        "bytecode_header_disagrees": _bytecode_header_disagreements(root),
        "bytecode_writing": not sys.dont_write_bytecode,
        "tree_walked": tree,
        "tree_newest_file": newest_path,
        "tree_newest_mtime": newest_mtime if tree else None,
        "tree_newer_than_process": (newest_mtime > started) if tree else None,
        "not_the_predicate": ["tree_newer_than_process", "bytecode_header_disagrees"],
        "why_not_the_predicate": "MEASURED FALSE on the live healthy loop during this "
                                 "ticket's survey: the loop started 15:17:36 and an ordinary "
                                 "edit landed at 15:30, so this comparison calls every "
                                 "working loop stale. It is here because a reader wants it, "
                                 "and it decides nothing.",
        "why_the_bytecode_header_is_not_the_predicate": "IT WAS the predicate until "
                                 "2026-08-18, and it is here so a reader can see what the "
                                 "old comparison would have said. Both of its terms are on "
                                 "disk, so any second interpreter importing the module "
                                 "repairs the evidence without repairing this process — "
                                 "measured, by an ordinary proof run in the same tree, and "
                                 "the loop benched an innocent device on the strength of it.",
    }
