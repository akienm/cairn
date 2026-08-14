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
  REWRITTEN  the source mtime no longer matches the mtime recorded IN THE BYTECODE Python
             wrote when it imported the module. This is the ImportError face.

WHY THE BYTECODE AND NOT A CLOCK. The honest comparison is "was this file written after this
MODULE was loaded", and per-module load times are exactly the runtime state ground_loop's
falsifier clause (5) forbids the heartbeat from holding — it may keep no state of its own
except the ruled liveness record. The ``.pyc`` header already carries the answer for free:
it embeds the source mtime its bytecode was compiled from, and nobody rewrites it unless the
module is imported again. A module loaded LATE from a freshly written file therefore reads
CURRENT (Python just wrote that header), while a module loaded EARLY whose source changed
since reads REWRITTEN (the header still names the old mtime). MEASURED on both cases before
this module was written. So the predicate is stateless, computed from ``sys.modules`` and
disk on the failure path, and clause (5) is not brushed.

WHERE IT IS BLIND, SAID OUT LOUD (Law 9 — absence of evidence is not evidence of freshness).
With ``-B``/``PYTHONDONTWRITEBYTECODE``, a read-only tree, or PEP 552 hash-based bytecode,
there is no timestamp to compare and the module reads UNDECIDABLE — never CURRENT. The
header's mtime field is also one-second granular, so a rewrite landing inside the same second
as the original is invisible; that bound is real and is orders of magnitude below the 29-hour
staleness this exists to catch. ``diagnostics()`` reports the undecidable count so a reader
can tell "nothing drifted" from "I could not look".

Proofs: ``proofs/test_staleness.py`` (this module) and ``proofs/test_discovery.py`` (the
benching decision it feeds), both written before this file existed.
"""

from __future__ import annotations

import os
import struct
import sys
from pathlib import Path

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
    no timestamp to compare — absent pyc, unreadable pyc, or hash-based bytecode."""
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


def module_drift(root: Path | None = None, modules: dict | None = None) -> list[dict]:
    """Every module THIS PROCESS holds, under ``root``, that no longer matches its file.

    Returns a list of ``{module, evidence, file, detail}`` — complete enough to resolve from
    the first report (I-complete-diagnostic-on-first-pass), because the caller turns these
    straight into a trouble's detail without going back to disk.

    Scoped by FILE PATH rather than by module name: ``skills.chart.live`` is this system's
    code just as much as ``cairn.tools.base.probe`` is, and a name-prefix scope would have
    silently excluded it. Never raises — a predicate that can take the heartbeat down is
    worse than the defect it reports.
    """
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
        embedded = _bytecode_source_mtime(module)
        if embedded is None:
            findings.append({
                "module": name, "evidence": UNDECIDABLE, "file": str(path),
                "detail": "no timestamped bytecode for this module, so whether its source "
                          "changed since it was loaded cannot be answered here — this is "
                          "not a report that it is current",
            })
            continue
        current = int(path.stat().st_mtime) & 0xFFFFFFFF
        if current != embedded:
            findings.append({
                "module": name, "evidence": REWRITTEN, "file": str(path),
                "detail": f"source mtime {current} does not match the {embedded} recorded in "
                          "the bytecode this process loaded, so the file was written after "
                          "this module was imported and the two have disagreed ever since",
            })
    return findings


def is_stale(findings: list[dict] | None = None) -> bool:
    """Does the drift actually ASSERT staleness? UNDECIDABLE does not — it says the question
    was unanswerable, and answering it 'yes' would make a tree with no bytecode permanently
    stale while answering 'no' would make it permanently, silently green."""
    if findings is None:
        findings = module_drift()
    return any(f["evidence"] in DRIFTED for f in findings)


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
    if findings is None:
        findings = module_drift(root)
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
        "bytecode_writing": not sys.dont_write_bytecode,
        "tree_walked": tree,
        "tree_newest_file": newest_path,
        "tree_newest_mtime": newest_mtime if tree else None,
        "tree_newer_than_process": (newest_mtime > started) if tree else None,
        "not_the_predicate": ["tree_newer_than_process"],
        "why_not_the_predicate": "MEASURED FALSE on the live healthy loop during this "
                                 "ticket's survey: the loop started 15:17:36 and an ordinary "
                                 "edit landed at 15:30, so this comparison calls every "
                                 "working loop stale. It is here because a reader wants it, "
                                 "and it decides nothing.",
    }
