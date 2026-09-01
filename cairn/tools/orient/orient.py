"""orient — the prebuild orientation instrument. Deterministic scans first; Hex on the miss.

Born 2026-07-27 from a morning in which CC, working from the same data, reached three
different conclusions about the same system (the logging floor: "0 of 13", then "one
floor missing", then "floor built since 07-22, 7 call sites, zero in bus"). Every wrong
conclusion had the same root: A PROXY WAS READ INSTEAD OF THE THING — the word `logging`
instead of the capability ``emit()``, the map instead of the tree, CC's own narration
instead of the remote. Akien's framing, verbatim: "we build a script for this function
that can _fail over to_ hex for any additional help ... because we'd build from the
start as a learning device."

THE CONTRACT
  - A SCAN is deterministic, inference-free, and answers by MEASURING the territory
    (AST call sites, file presence, git plumbing) — never by grepping for a word or
    reading a record about the world. Its result is a measurement (Law 3).
  - Every scan carries PROVENANCE: the correction that seeded it. That is the learning
    device (learns-its-gates): when Akien catches CC wrong, the check that would have
    caught it becomes a scan here, and the class of error stops recurring (Law 1).
  - ``deepen()`` is the failover seam — for the question no scan answers. It goes
    through ``inference_domain.resolve`` and NOWHERE else (the sole path to the host;
    its cost lands in yield_report's meter). Its answer is a LABELED READ, never a
    measurement — a scan's number outranks Hex's prose, always.

CLI (inference-free unless you ask to deepen):
  python3 -m cairn.tools.orient.orient census            # every component, measured
  python3 -m cairn.tools.orient.orient calls <name>      # call sites of a capability
  python3 -m cairn.tools.orient.orient git               # HEAD vs @{u}, both repos
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

# The ONE owner of class-space addressing (rung names, component roster). Admitted by name
# here on 2026-08-13, the way librarian/library.py and chart/orient.py already admit it: the
# leaf imports nothing but pathlib, and cairn/tools/base/__init__.py is empty by the
# boot-order law written into it, so this pulls in no component.
from cairn.tools.base import address

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_COMMONS = _REPO_ROOT.parent / "CairnCommons"

# Each scan's floor: refuse to report on a tree it barely saw. A scan that silently
# saw 3 files and said "zero call sites" is the proxy error wearing a lab coat.
_MIN_MODULES_SCANNED = 20


class ScanRefused(RuntimeError):
    """A scan that cannot honestly measure refuses loudly (Law 7) — it never guesses."""


def _py_files(root: Path):
    return [p for p in root.rglob("*.py") if "__pycache__" not in p.parts]


# ── scan: call sites, capability not mention ─────────────────────────────────


def call_sites(name: str, *, root: Path | None = None) -> dict:
    """Where is ``name`` actually CALLED — not mentioned, called.

    Provenance: 2026-07-27 — CC grepped for the word `logging`, found stdlib-shaped
    strings, and reported "0 of 13 components have logging" of a tree with a composed
    emission base and 7 live ``emit()`` call sites. Prose about a capability cannot
    fire it; only a call site can. Same fix as the sole-path tooth (mention → capability).
    """
    root = root or (_REPO_ROOT / "cairn")
    sites, scanned = [], 0
    for p in _py_files(root):
        scanned += 1
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except SyntaxError as e:
            raise ScanRefused(
                f"call_sites({name!r}): {p} does not parse ({e}) — a scan that skips the "
                "unparseable file reports a smaller world than exists; fix the file or "
                "exclude it explicitly."
            ) from None
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                called = (
                    f.attr if isinstance(f, ast.Attribute)
                    else f.id if isinstance(f, ast.Name)
                    else None
                )
                if called == name:
                    sites.append({
                        "file": str(p.relative_to(root.parent) if root.parent in p.parents else p),
                        "line": node.lineno,
                        "in_proofs": "proofs" in p.parts,
                    })
    if scanned < _MIN_MODULES_SCANNED and root == _REPO_ROOT / "cairn":
        raise ScanRefused(
            f"call_sites({name!r}) saw only {scanned} modules under {root} — floor is "
            f"{_MIN_MODULES_SCANNED}; this is not a scan of the tree."
        )
    return {
        "scan": "call_sites",
        "question": f"where is {name}() actually called?",
        "measured": {"sites": sites, "modules_scanned": scanned,
                     "call_sites_outside_proofs": sum(1 for s in sites if not s["in_proofs"])},
        "provenance": "2026-07-27: 'logging' word-grep reported 0 of 13; emit() had 7 call "
                      "sites. Capability, not mention.",
    }


# ── scan: device census, world not record ────────────────────────────────────


def device_census(*, root: Path | None = None) -> dict:
    """Every component directory, measured: does it subclass BaseDevice, does its
    charter exist ON DISK, how many proofs, what do its validations' verdicts SAY,
    and how many non-proof ``self.emit(...)`` call sites — the DiagnosticBase
    surface, receiver checked — does it carry.

    Provenance: 2026-07-26/27 — three answers about system state were read from
    records (a filed edge, the map, a docstring) and were wrong about the world.
    A census row is built only from things a filesystem call returned. Sharpened
    2026-07-27 (same day): the generic emit-by-name count admitted two homonyms
    (an audit function, the workflow chokepoint) — the emission measure now checks
    the receiver is ``self``, not just the word.
    """
    root = root or (_REPO_ROOT / "cairn")
    if not root.is_dir():
        raise ScanRefused(
            f"device_census: {root} is not a directory — a census of nowhere must refuse, "
            "not report zero components (a clean-looking empty world is the proxy error)."
        )
    # WHAT MAKES A DIRECTORY A COMPONENT — widened 2026-08-01, at the first skill to
    # cross PROVEME through the build gate. The old test was "top-level *.py", which is
    # a test for PYTHON, not for a component: skills/intent/ carries a charter, a
    # history, a state, proofs/ and probes/ — everything CLAUDE.md names — and its only
    # .py files live one level down, so the census reported skills/ as EMPTY and the
    # build gate refused the crossing rather than pass an address it could not measure.
    # The disposition the gate itself named was "grow the census", and CLAUDE.md already
    # says what a component is: "A component without an intention doesn't run." So the
    # charter is the other admission door. Measured before widening: under cairn/ the
    # two tests select the SAME 23 directories (no row added, none dropped), and under
    # skills/ the charter test finds the 9 that were invisible. Kept as a UNION, not a
    # swap — a directory with .py and no charter must stay visible, because
    # charter_on_disk=False on a real row is exactly the finding cairnmap --gate reads.
    # AN UNREADABLE DIRECTORY IS MEASURED, NOT FATAL — and never silently skipped.
    # Measured 2026-08-03: ``Path.is_file()`` PROPAGATES PermissionError here, so a single
    # unreadable sibling (systemd's per-service private dirs under /tmp) crashed the whole
    # census with a bare traceback. A scan that dies on one entry reports nothing about the
    # other twenty-two, and a raw traceback is not a diagnostic (Law 7: loud at diagnostic
    # surfaces means legible, not merely noisy). Both alternatives were worse: crashing loses
    # the census, and skipping quietly is the "gate that inspects nothing passes everything"
    # fault the inspector's own refusal already names. So it RIDES THE RETURN as its own
    # roster, and a caller that cares (build_inspector) can red on it.
    # Shape borrowed, not invented: the validations walk below already reports "UNREADABLE: e".
    # THE WALK IS TWO LEVELS SINCE 2026-08-13 and it is not spelled here. A component sits at
    # cairn/<rung>/<name>/, and the rung names have exactly one owner (base.address.CLASS_RUNGS)
    # — spelling them a second time here is the drift this census exists to catch in others.
    components, unreadable = address.component_dirs(root)
    if not components:
        raise ScanRefused(
            f"device_census: no component directories under {root} — wrong root?"
            + (f" ({len(unreadable)} entr{'y' if len(unreadable) == 1 else 'ies'} could not "
               f"be read: {[u['path'] for u in unreadable]})" if unreadable else ""))
    rows = []
    for d in components:
        subclasses = []
        # THE DEVICE SURFACE IS ``self.emit(...)``, NOT ANY FUNCTION NAMED ``emit``.
        # Measured 2026-07-27, the homonym discovery: of 4 generic emit() call sites, only
        # 2 were DiagnosticBase's surface — sudo_relay's is a module-level audit function
        # and harbor_master's is transitions.emit, the workflow chokepoint. Counting by the
        # word let two components pass the silent_device sieve on a homonym — the exact
        # words-kept-meanings-replaced failure, in code. So the census counts the RECEIVER
        # too: a Call on an Attribute named emit whose value is the name ``self``.
        self_emit_sites = 0
        for p in _py_files(d):
            if "proofs" in p.parts:
                continue
            try:
                tree = ast.parse(p.read_text(encoding="utf-8"))
            except SyntaxError:
                continue  # call_sites is the scan that refuses on this; the census marks it
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef) and any(
                    (isinstance(b, ast.Name) and b.id == "BaseDevice")
                    or (isinstance(b, ast.Attribute) and b.attr == "BaseDevice")
                    for b in node.bases
                ):
                    subclasses.append(f"{p.name}:{node.name}")
                elif (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "emit"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "self"
                ):
                    self_emit_sites += 1
        verdicts = []
        for v in sorted(d.glob("validations/*.json")):
            # Measured shape (this scan's own census, 2026-07-27): every validation file in
            # the tree is a LIST of eight-field records — append-only, so the LATEST record
            # is the standing verdict and the count is how many times it was sealed.
            try:
                recs = json.loads(v.read_text())
                latest = recs[-1] if isinstance(recs, list) and recs else recs
                verdict = latest.get("verdict") if isinstance(latest, dict) else (
                    f"UNEXPECTED SHAPE: {type(recs).__name__} of {type(latest).__name__}"
                )
                verdicts.append({"file": v.name, "verdict": verdict,
                                 "records": len(recs) if isinstance(recs, list) else 1})
            except (json.JSONDecodeError, OSError) as e:
                verdicts.append({"file": v.name, "verdict": f"UNREADABLE: {e}", "records": 0})
        charter_path = d / "intention+why.json"
        runtime_role = ""
        if charter_path.is_file():
            try:
                runtime_role = json.loads(charter_path.read_text()).get("runtime_role", "")
            except (json.JSONDecodeError, OSError):
                pass
        rows.append({
            "component": d.name,
            # THE NAME IS NOT THE ADDRESS (base.address.AmbiguousComponent, 2026-08-13).
            # ``orient`` is both a tool and a machine held by the builder device; a consumer
            # keyed on d.name alone collapses the two and inspects one of them twice while
            # the other is never inspected at all — silently, which is the failure this
            # census exists to prevent. The row therefore carries WHERE it was measured,
            # relative to the pkg root it was measured under, and a consumer that needs a
            # unique subject key uses this.
            "dir": str(d.relative_to(root)),
            "charter_on_disk": charter_path.exists(),
            "runtime_role": runtime_role,
            "device_subclasses": subclasses,
            "proofs": len(list(d.glob("proofs/test_*.py"))),
            "validations": verdicts,
            "self_emit_call_sites_outside_proofs": self_emit_sites,
        })
    return {
        "scan": "device_census",
        "question": "what does each component MEASURABLY have?",
        "measured": {"components": rows, "count": len(rows), "unreadable": unreadable},
        "provenance": "2026-07-26/27: system state was reported from records three times and "
                      "was wrong about the world each time. Census rows come from the "
                      "filesystem only.",
    }


# ── scan: repo truth, thing not narration ────────────────────────────────────


def repo_truth(*, repos: list[Path] | None = None) -> dict:
    """HEAD vs upstream and working-tree dirt, from git plumbing — never from a label.

    Provenance: 2026-07-26 — an ``echo "cairn pushed"`` welded to ``&&`` attested a
    push that never happened; ``git status`` clean confirmed the wrong thing. Only a
    command that reads the THING (rev-parse, rev-list, porcelain) counts.
    """
    repos = repos or [_REPO_ROOT, _COMMONS]
    out = []
    for r in repos:
        def _git(*args):
            p = subprocess.run(["git", "-C", str(r), *args], capture_output=True, text=True)
            return p.returncode, p.stdout.strip(), p.stderr.strip()
        rc, head, err = _git("rev-parse", "HEAD")
        if rc != 0:
            raise ScanRefused(f"repo_truth: {r} is not a readable git repo ({err})")
        rc, upstream, _ = _git("rev-parse", "@{u}")
        ahead = behind = None
        if rc == 0:
            rc2, counts, _ = _git("rev-list", "--left-right", "--count", "HEAD...@{u}")
            if rc2 == 0:
                ahead, behind = (int(x) for x in counts.split())
        _, porcelain, _ = _git("status", "--porcelain")
        out.append({
            "repo": r.name, "head": head,
            "upstream": upstream if upstream and not upstream.startswith("@") else None,
            "ahead_of_upstream": ahead, "behind_upstream": behind,
            "dirty_paths": len(porcelain.splitlines()),
        })
    return {
        "scan": "repo_truth",
        "question": "is what I said committed/pushed ACTUALLY committed/pushed?",
        "measured": {"repos": out},
        "provenance": "2026-07-26: an echo label attested a push that had not happened. "
                      "Read the thing, never the narration.",
    }


def import_map(path, *, root: Path | None = None) -> dict:
    """Which modules ACTUALLY ENTER a file — imports measured as capability, with
    the loose package form resolved to the module it binds.

    Provenance: 2026-07-28 — the same red twice in one day: import-allowlist teeth
    recorded ``ast.ImportFrom.module`` verbatim, so ``from cairn.machines.chart import
    constrain`` recorded as the prefix ``cairn.machines.chart`` and was refused, though the
    module entering is exactly ``cairn.devices.builder.machines.constrain.constrain`` — the identical module the
    precise spelling admits. The teeth measured the SPELLING, not the capability;
    the fix applied twice was a respelling, treating the symptom. The corpus walk
    placed this beside the echo-label and emit-homonym scars: one family,
    word-not-capability, third member. Measured before the fix: 70 loose-form
    cairn-internal imports repo-wide — the form is the house idiom, so the
    measurement RESOLVES it rather than banning it. First correction to ride
    orient's own brick loop end to end (node cd9e57c05b35661b -> propose_scan ->
    this installation); ratified by Akien 2026-07-28 ('i like it').
    """
    root = root or _REPO_ROOT
    p = Path(path)
    if not p.is_file():
        raise ScanRefused(
            f"import_map({str(path)!r}): no such file — a scan of nothing must "
            "refuse, not report an empty import list.")
    try:
        tree = ast.parse(p.read_text(encoding="utf-8"))
    except SyntaxError as e:
        raise ScanRefused(
            f"import_map({str(path)!r}): does not parse ({e}) — an unparseable file "
            "has an unknowable import list; refusing beats narrating a smaller one."
        ) from None
    entering = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            entering.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            recorded = ("." * node.level) + (node.module or "")
            base = (Path(root, *node.module.split("."))
                    if node.module and not node.level else None)
            for a in node.names:
                if base is not None and ((base / (a.name + ".py")).is_file()
                                         or (base / a.name).is_dir()):
                    entering.add(node.module + "." + a.name)  # the loose form, resolved
                else:
                    entering.add(recorded)
    return {
        "scan": "import_map",
        "question": f"which modules actually enter {p.name}?",
        "measured": {"path": str(p), "imports": sorted(entering)},
        "provenance": "2026-07-28: allowlist teeth read the import's SPELLING, so the "
                      "loose form 'from cairn.devices.builder.machines.constrain import constrain' recorded as its "
                      "prefix and refused — twice in one day — though the module "
                      "entering is exactly the one the precise spelling admits. Third "
                      "member of the word-not-capability family (echo-label, "
                      "emit-homonym). 70 loose-form imports measured repo-wide: the "
                      "form is the house idiom, so the measurement resolves it rather "
                      "than banning it. First correction through orient's own brick "
                      "loop; ratified by Akien 2026-07-28.",
    }


SCANS = {"call_sites": call_sites, "device_census": device_census,
         "repo_truth": repo_truth, "import_map": import_map}


# ── the failover seam: Hex, on the miss, through the one door ────────────────


def deepen(question: str, *, resolve) -> dict:
    """The question no scan answers goes to Hex — through inference_domain's
    ``resolve`` (the sole path; metered, cached — and for ORIENT traffic a cache hit
    is a genuine saving, unlike librarian backfill). The caller injects ``resolve``
    (the CLI wires the real one); this module never opens the host itself.

    The answer is a LABELED READ. It is returned under ``read``, never ``measured`` —
    a scan's number outranks Hex's prose by construction, not by discipline.
    """
    if not callable(resolve):
        raise ScanRefused(
            "deepen: no resolve seam injected — the failover goes through "
            "inference_domain.resolve or not at all (sole path). Refusing to answer "
            "from nothing; a fabricated deepening is the exact failure orient exists "
            "to end."
        )
    result = resolve({"kind": "generate", "prompt": question})
    return {
        "scan": "deepen",
        "question": question,
        "read": result,   # deliberately NOT "measured" — this is inference, labeled as such
        "provenance": "2026-07-27, Akien: 'fail over to hex for any additional help' — "
                      "the failover half of the learning device; deterministic scans are "
                      "always consulted first.",
    }


def _main(argv: list[str]) -> int:
    if not argv or argv[0] not in {"census", "calls", "git", "imports"}:
        print(__doc__)
        return 2
    if argv[0] == "census":
        print(json.dumps(device_census(), indent=2))
    elif argv[0] == "calls":
        if len(argv) < 2:
            print("calls <name> — which capability?", file=sys.stderr)
            return 2
        print(json.dumps(call_sites(argv[1]), indent=2))
    elif argv[0] == "git":
        print(json.dumps(repo_truth(), indent=2))
    elif argv[0] == "imports":
        if len(argv) < 2:
            print("imports <file> — which file?", file=sys.stderr)
            return 2
        print(json.dumps(import_map(argv[1]), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
