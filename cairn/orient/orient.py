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
  python3 -m cairn.orient.orient census            # every component, measured
  python3 -m cairn.orient.orient calls <name>      # call sites of a capability
  python3 -m cairn.orient.orient git               # HEAD vs @{u}, both repos
"""

from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
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
    and how many non-proof emit() call sites does it carry.

    Provenance: 2026-07-26/27 — three answers about system state were read from
    records (a filed edge, the map, a docstring) and were wrong about the world.
    A census row is built only from things a filesystem call returned.
    """
    root = root or (_REPO_ROOT / "cairn")
    if not root.is_dir():
        raise ScanRefused(
            f"device_census: {root} is not a directory — a census of nowhere must refuse, "
            "not report zero components (a clean-looking empty world is the proxy error)."
        )
    components = sorted(
        d for d in root.iterdir()
        if d.is_dir() and d.name != "__pycache__" and list(d.glob("*.py"))
    )
    if not components:
        raise ScanRefused(f"device_census: no component directories under {root} — wrong root?")
    rows = []
    for d in components:
        subclasses = []
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
        emit_sites = call_sites("emit", root=d)["measured"]["sites"] if _py_files(d) else []
        rows.append({
            "component": d.name,
            "charter_on_disk": (d / "intention+why.json").exists(),
            "device_subclasses": subclasses,
            "proofs": len(list(d.glob("proofs/test_*.py"))),
            "validations": verdicts,
            "emit_call_sites_outside_proofs": sum(1 for s in emit_sites if not s["in_proofs"]),
        })
    return {
        "scan": "device_census",
        "question": "what does each component MEASURABLY have?",
        "measured": {"components": rows, "count": len(rows)},
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


SCANS = {"call_sites": call_sites, "device_census": device_census, "repo_truth": repo_truth}


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
    if not argv or argv[0] not in {"census", "calls", "git"}:
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
    return 0


if __name__ == "__main__":
    raise SystemExit(_main(sys.argv[1:]))
