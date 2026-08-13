"""determinism — what each component can REACH, and therefore whether it is replayable.

AKIEN, 2026-08-13, and this module exists to answer him with an instrument rather than a
sentence: "we're sprinting toward akien can inspect the gates and inspectors and find them
deterministic and mostly deterministic respectively. I want to SEE that before anything
else. That's our base level thing above skills. but it has to be the thing those skills
can depend on."

THE CLAIM THIS MEASURES. build_inspector's charter has said since 2026-07-27 that a gate is
"inference-free by construction ... a gate that consults an oracle is not a gate", and the
verdict is "always HARDWARE". That is a claim about a FIRE PATH, and until now it was
prose: readable, plausible, and unfalsifiable at a glance. Law 3 — nothing is known until
measured. This walks the path.

THE DEFINITION, and it is deliberately narrow enough to be wrong:

  DETERMINISTIC          the component's transitive import closure reaches no oracle and
                         shells out to nothing. Same input, same registry revision, same
                         verdict, forever. This is what a GATE must be, because Law 7 makes
                         its verdict permanent in a record of truth, and a verdict you
                         cannot replay is not a record, it is a memory.

  MOSTLY DETERMINISTIC   no oracle, but it shells out. `git` over a committed tree replays;
                         a proof subprocess replays unless the world moved under it. This
                         is what an INSPECTOR is allowed to be: it measures a real machine,
                         and a real machine has weather.

  REACHES AN ORACLE      the closure arrives at inference, 5432, the trees, or the network.
                         Not a defect by itself — inference_domain REACHING inference is
                         the point. It is a defect exactly when the thing is a gate.

WHY THE ROSTER IS NOT A LIST IN THIS FILE. A hand-kept list of "the gates" would go stale
the first time one moved, and it would go stale SILENTLY — the same failure ground_loop's
discovery was ruled into existence to kill (Akien, 2026-08-11: "THE PROBLEM WITH SUBSCRIBE
IS NOW YOU HAVE A LIST THAT YOU HAVE TO MAINTAIN AND CAN BECOME STALE"). So the roster is
DISK: a component is a directory holding an ``intention+why.json``, because a component
without an intention does not run. Nothing declares itself onto this report and nothing can
fall off it except by ceasing to exist.

WHAT IT INHERITS AND DOES NOT RE-DERIVE. The reach walk, the band ladder and the
mention-vs-capability lesson all live in ``cairn.tools.import_sieve`` and are composed here,
not copied (Law 1). That module's header records the two failures that taught the mesh —
a docstring's honest mention of inference_domain firing a grep, and a port number in an
error string doing the same. Re-deriving reach here would re-earn both.

WHAT THIS CANNOT SEE, stated so no green reads wider than it is — inherited whole from
import_sieve and NOT weakened:
  - a subprocess that dials. ``subprocess.run(["curl", ...])`` imports nothing, and this
    module reports the shell-out without knowing where it went.
  - a dynamic import with a computed name.
  - anything a shelled binary does. `git` is judged replayable by REPUTATION here, which is
    a claim about git, not a measurement of it.
A component that comes back DETERMINISTIC has been measured deterministic ON ITS IMPORTS.
That is a real floor and it is not the whole ceiling.
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

from cairn.tools.import_sieve import sieve as import_sieve

CHARTER = "intention+why.json"

# The oracles, taken from import_sieve's own band-3 rung rather than re-listed, so a door
# added to the ladder is a door this report starts seeing on the same day (Law 1). The
# ladder is the corpus's one answer to "what counts as off-box".
ORACLES = tuple(import_sieve.DEFAULT_LADDER[3]["modules"])

# Band 2 holds `ast` and the directory walks too, which are pure computation over disk and
# replay fine. The only band-2 entry that leaves the process is the shell.
SHELL = ("subprocess",)

SKIP_PARTS = {"__pycache__", ".git", "node_modules", ".venv", "venv", "proofs",
              "validations", "probes"}

# THE FIRE PATH AND THE LEARNING SEAM ARE TWO PATHS, and collapsing them was this module's
# first measured defect (2026-08-13, caught on its own first run). build_inspector came back
# REACHES AN ORACLE — true of the component, and false about the gate. The reach was
# `nexus.py`, the question-nexus graft, which its charter has always kept separate:
# "no deepen seam exists at fire-time ... Inference may serve the LEARNING of sieves, but a
# learning lands here only by installation — evidence-provenanced, ratified, versioned —
# never mid-fire". A report that reds the gate for the seam its design deliberately isolates
# is measuring the component when the FIRE PATH was meant.
#
# `nexus.py` is the corpus's existing name for that seam, not a coinage minted here: orient
# and build_inspector each carry one, and I-nexi-everywhere is the standing pattern
# ("every learning component is a question nexus; fire-paths are HARDWARE"). So the split is
# derived from a convention already on disk. If a learning seam is ever spelled some other
# way, this under-reaches, and that is a real limit rather than a hidden one.
LEARNING_SEAM = ("nexus.py",)

DETERMINISTIC = "DETERMINISTIC"
MOSTLY = "MOSTLY DETERMINISTIC"
ORACLE = "REACHES AN ORACLE"


def _own_modules(comp_dir: Path, root: Path) -> list[str]:
    """The component's OWN importable surface — its top-level .py files.

    Proofs, probes and validations are excluded on purpose: a proof may reach anything it
    needs to stand up a fixture, and judging a gate by what its test imports would red the
    gate for being well tested. The question is what the SHIPPED path reaches.
    """
    out = []
    for p in sorted(comp_dir.glob("*.py")):
        if p.name.startswith("_") and p.name != "__init__.py":
            continue
        out.append(os.path.relpath(p, root))
    return out


def _refusals(path: Path) -> list[str]:
    """Refusal classes declared in a file — ONE signature of a thing that can say no.

    Deriving this from the AST rather than from a charter's prose means a component cannot
    quietly stop refusing while its charter still says it does.

    THE COLUMN SAYS `REFUSES`, NOT `GATES`, AND THE NARROWING IS THE POINT. Raising is not
    the only way to gate: build_inspector is THE post-build gate and declares no refusal
    class at all in its fire path — it returns findings and exits 1, and the emit
    chokepoint is what refuses on them. So a blank here means "declares no refusal class",
    never "does not gate". Naming the column for the wider claim would be a green read
    wider than what was measured (Law 3), and gate-ness is a question this instrument has
    not earned an answer to.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return []
    names = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        for base in node.bases:
            b = base.id if isinstance(base, ast.Name) else getattr(base, "attr", "")
            if b.endswith(("Error", "Exception", "Refused", "Red")):
                names.append(node.name)
                break
    return names


def components(root: str | Path = ".") -> list[dict]:
    """Every component on disk that holds a charter and ships code. Sorted, derived."""
    root = Path(root).resolve()
    out = []
    for charter in sorted(root.rglob(CHARTER)):
        rel_parts = charter.relative_to(root).parts
        if any(p in SKIP_PARTS or p.startswith(".") for p in rel_parts):
            continue
        comp = charter.parent
        mods = _own_modules(comp, root)
        if not mods:
            continue                      # prose-as-implementation: nothing to walk
        out.append({"component": comp.name,
                    "path": str(comp.relative_to(root)),
                    "modules": mods})
    return out


def _rung(rel: str) -> str:
    """Which rung of the complexity axis this address sits on — read off the path, because
    the path IS the declaration (CLAUDE.md: one address written in two roots)."""
    parts = rel.split(os.sep)
    if parts[0] == "skills":
        return "skill"
    if "devices" in parts:
        return "machine (held)" if "machines" in parts else "device"
    if "machines" in parts:
        return "machine"
    if "tools" in parts:
        return "tool"
    return "?"


def measure(root: str | Path = ".") -> dict:
    """The whole report: every component, what it reaches, and the verdict that follows.

    Raises on an empty corpus rather than returning a clean-looking nothing — the hollow
    floor import_sieve builds into ``catches`` for the same reason (Law 8: a green over
    zero files is not a green).
    """
    root = Path(root).resolve()
    graph = import_sieve.import_graph(str(root))
    if not graph:
        raise import_sieve.HollowScan(
            f"determinism: no .py files under {root} — a report over an unread tree would "
            "show every component deterministic, which is the shape of a green that means "
            "nothing")
    def walk(mods: list[str]) -> tuple[dict[str, str], dict[str, str], int]:
        """Oracle hits, shell hits and closure size for one set of entry modules."""
        reached: set[str] = set()
        oracle_hits: dict[str, str] = {}
        shell_hits: dict[str, str] = {}
        for mod in mods:
            if mod not in graph:
                continue
            closure = dict(import_sieve.reaches(graph, mod))
            closure[mod] = [mod]
            reached |= set(closure)
            for path in closure:
                for imported in graph.get(path, ()):
                    for t in ORACLES:
                        if import_sieve._matches(imported, t):
                            oracle_hits.setdefault(t, " -> ".join(closure[path]))
                    for t in SHELL:
                        if import_sieve._matches(imported, t):
                            shell_hits.setdefault(path, t)
        return oracle_hits, shell_hits, len(reached)

    rows = []
    for comp in components(root):
        fire = [m for m in comp["modules"]
                if os.path.basename(m) not in LEARNING_SEAM]
        seam = [m for m in comp["modules"]
                if os.path.basename(m) in LEARNING_SEAM]
        oracle_hits, shell_hits, reach = walk(fire)
        seam_oracles, _, _ = walk(seam) if seam else ({}, {}, 0)
        verdict = ORACLE if oracle_hits else (MOSTLY if shell_hits else DETERMINISTIC)
        refusals = sorted({r for m in fire for r in _refusals(root / m)})
        rows.append({**comp,
                     "rung": _rung(comp["path"]),
                     "verdict": verdict,
                     "refuses": bool(refusals),
                     "refusals": refusals,
                     "oracles": oracle_hits,
                     "shells": sorted(shell_hits),
                     "learning_seam": seam,
                     "seam_oracles": seam_oracles,
                     "reach": reach})
    rows.sort(key=lambda r: (r["verdict"] != DETERMINISTIC,
                             r["verdict"] != MOSTLY, r["path"]))
    return {"root": str(root), "components": len(rows), "rows": rows,
            "counts": {v: sum(1 for r in rows if r["verdict"] == v)
                       for v in (DETERMINISTIC, MOSTLY, ORACLE)}}


def render(report: dict) -> str:
    """The surface Akien reads. One line per component, evidence indented under it."""
    L = []
    c = report["counts"]
    L.append("=" * 78)
    L.append("DETERMINISM — what each component's shipped import path can reach")
    L.append("=" * 78)
    L.append(f"{report['components']} components  ·  {c[DETERMINISTIC]} deterministic  ·  "
             f"{c[MOSTLY]} mostly  ·  {c[ORACLE]} reach an oracle")
    L.append("")
    mark = {DETERMINISTIC: "  ", MOSTLY: "~ ", ORACLE: "! "}
    last = None
    for r in report["rows"]:
        if r["verdict"] != last:
            L.append("")
            L.append(f"--- {r['verdict']} " + "-" * (60 - len(r["verdict"])))
            last = r["verdict"]
        gate = "REFUSES" if r["refuses"] else "       "
        L.append(f"{mark[r['verdict']]}{r['path']:47s} {r['rung']:14s} {gate}")
        for t, chain in sorted(r["oracles"].items()):
            L.append(f"      oracle: {t}   via {chain}")
        for p in r["shells"]:
            L.append(f"      shell:  {p}")
        if r["seam_oracles"]:
            # Reported, never counted against the verdict: the seam is where learning is
            # SUPPOSED to reach an oracle. Silence here would hide a real reach; counting it
            # would red a gate for having a learning path (Law 7 — loud, and correctly aimed).
            L.append(f"      learning seam ({', '.join(r['learning_seam'])}) reaches: "
                     f"{', '.join(sorted(r['seam_oracles']))}   [by design — not fire-time]")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    root = argv[0] if argv else str(Path(__file__).resolve().parents[3])
    report = measure(root)
    print(json.dumps(report, indent=2) if as_json else render(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
