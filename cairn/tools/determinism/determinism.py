"""determinism — WHERE THE LLM IS, and therefore whether a component replays.

AKIEN, 2026-08-13, correcting this module's first cut, and the correction is the whole
definition:

  "i assume shell means requires running a script. DETERMINISTIC code can call other
   scripts. But Pure DETERMINISTIC means no LLM calls. So whatever shell scripts it calls
   can't make LLM calls. MOSTLY means the LLM does not run in the operational loop. But an
   LLM is called periodically, such as during "SLEEP" (we do have that idea) to review the
   feedback and update the deterministic components if needed."

THE AXIS IS THE LLM. The first cut graded on "does it leave the process", which put `git`
in the same bucket as an oracle and reported 17 components as reaching one when not one of
them could reach the inference host. Shelling out is ORDINARY: a component may run all the
scripts it likes and stay pure, so long as nothing down that path calls an LLM. What makes
a verdict unreplayable is an oracle in the loop, not a fork.

THE THREE VERDICTS:

  PURE DETERMINISTIC     no LLM anywhere — not at fire time, not at SLEEP. Same input,
                         same verdict, forever. This is what a GATE must be, because Law 7
                         makes a gate's verdict permanent in a record of truth, and a
                         verdict you cannot replay is not a record, it is a memory.

  MOSTLY DETERMINISTIC   no LLM in the OPERATIONAL LOOP, but the component has a seam the
                         LLM runs through periodically — at SLEEP — to review feedback and
                         update the deterministic parts. The fire path still replays; the
                         thing that CHANGES the fire path does not, and it runs out of band
                         where its output can be inspected before it lands.

  REACHES AN ORACLE      the LLM is in the operational loop. Correct and necessary for the
                         librarian, for chat, for /chart. A defect exactly when the thing
                         is a gate.

A GATE MAY NEVER REACH AN ORACLE, AND THAT IS NOW A WALK RATHER THAN A SENTENCE. Akien,
2026-08-13: "NO GATES MAY CONSULT ORACLES EVER PERIOD. A GATE ONLY OPENS WHEN A FINDINGS
REPORT MATCHES WHAT IT ALLOWS. ITS AN == compare. Must be identical. NO ORACLE." Gate-ness
used to live in prose in a charter, where nothing could check it; it is now DERIVED from
the same import graph as everything else — a gate is a component whose fire path reaches
``cairn.tools.gate``, the primitive that holds the == compare. Two import facts, one walk,
and the rule is physics: a gate that grows a path to the inference host is a VIOLATION here
and reds this tool's proof, which the corpus runs.

WHAT COUNTS AS THE LLM, and it is one name because a ruling made it one: everything routes
through ``cairn.devices.inference_domain``, the sole path to the inference host. So this
does not keep a list of hosts, ports or providers — it walks to the door. A second door
would be a defect that sieve catches at its own address, not a hole here.

THE SEAMS ARE NAMED BY THE CORPUS, NOT COINED HERE. ``live.py`` is the stated convention
for the thin edge where the LLM doors compose (librarian/live.py: "trees.py stays
import-pure; this thin edge is where the doors compose (the same shape as
intention_extractor/live.py)"), and ``nexus.py`` is the question-nexus, where a component's
learning happens. Both are SLEEP-time by design. A component is walked from its NON-seam
modules: if a seam is reachable from the fire path anyway, it counts against the verdict,
because then the LLM really is in the loop no matter what the file is called.

OFF-BOX IS REPORTED, NOT GRADED. 5432, the trees and the network are not oracles in Akien's
sense — psycopg2 is not an LLM. They matter to replayability (a row can change under you)
and they are shown, but they do not set the verdict, because the verdict answers his
question and not a different one.

SHELLING IS THE DIRECTION OF TRAVEL, NOT A HOLE (Akien, 2026-08-13: "i don't care about
the argv. if it's working, it's working. I never dispermitted shelling. since we're trying
to push compilation downward, the hope is more and more things become individually
callable."). This module's second cut chased every computed argv and flagged five
components ``*UNPROVEN`` for it, which dressed the system's own goal up as a debt. Shell
targets are still REPORTED — they are the visible evidence of that compilation pushing
downward — and they are not graded, not flagged, and not chased.

WHAT THIS CANNOT SEE, stated so no green reads wider than the walk:
  - a dynamic import with a computed name (inherited from import_sieve, not weakened).
"""

from __future__ import annotations

import ast
import json
import os
from pathlib import Path

from cairn.tools.import_sieve import sieve as import_sieve

CHARTER = "intention+why.json"

# THE ORACLE IS ONE NAME because ruling 2026-08-08 made inference_domain the sole path to
# the inference host. Walking to the door beats keeping a list of what is behind it.
LLM = ("cairn.devices.inference_domain",)

# Off-box but NOT an oracle: state that can change under a re-run. Reported beside the
# verdict, never folded into it — grading these as oracles is the error this module's
# first cut shipped with.
OFF_BOX = tuple(m for m in import_sieve.DEFAULT_LADDER[3]["modules"]
                if not m.startswith("cairn.devices.inference_domain"))

# THE GATE PRIMITIVE. A gate is a component that reaches this — the module holding the ==
# compare Akien specified. Derived, never declared: a charter field saying "I am a gate"
# is a value stranded in a human's head, and it goes stale in the direction that looks safe.
GATE = ("cairn.tools.gate",)
GATE_TOOL_PATH = os.path.join("cairn", "tools", "gate")

SKIP_PARTS = {"__pycache__", ".git", "node_modules", ".venv", "venv", "proofs",
              "validations", "probes"}

# The SLEEP seams — the corpus's own filenames, not a coinage minted here. `live.py` is the
# stated LLM edge; `nexus.py` is the question-nexus where learning lands. Excluded as
# ENTRY POINTS only: if the fire path imports one anyway, the walk still arrives and the
# component is graded on it, because a seam reachable from the loop IS in the loop.
SEAMS = ("live.py", "nexus.py")

PURE = "PURE DETERMINISTIC"
MOSTLY = "MOSTLY DETERMINISTIC"
ORACLE = "REACHES AN ORACLE"


def _own_modules(comp_dir: Path, root: Path) -> list[str]:
    """The component's OWN importable surface — its top-level .py files.

    Proofs, probes and validations are excluded: a proof may reach anything it needs to
    stand up a fixture, and judging a gate by what its test imports would red the gate for
    being well tested. The question is what the SHIPPED path reaches.
    """
    out = []
    for p in sorted(comp_dir.glob("*.py")):
        if p.name.startswith("_") and p.name != "__init__.py":
            continue
        out.append(os.path.relpath(p, root))
    return out


def shell_targets(path: Path) -> set[str]:
    """The binaries this file shells to, read off the literal argv head.

    REPORTED, NEVER GRADED, AND A COMPUTED ARGV IS NOT CHASED. Akien, 2026-08-13: "i don't
    care about the argv. if it's working, it's working. I never dispermitted shelling."
    Shelling out to an individually callable thing is compilation pushing DOWNWARD, which
    is the direction the whole system is trying to move — so what this collects is evidence
    of that, not a debt register.
    """
    try:
        tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, SyntaxError):
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", "")
        if name not in {"run", "Popen", "check_output", "call", "check_call"}:
            continue
        root = fn.value if isinstance(fn, ast.Attribute) else None
        rootname = getattr(root, "id", "")
        if rootname and rootname not in {"subprocess"}:
            continue
        if not node.args:
            continue
        first = node.args[0]
        if isinstance(first, ast.List) and first.elts:
            head = first.elts[0]
            if isinstance(head, ast.Constant) and isinstance(head.value, str):
                found.add(os.path.basename(head.value))
        elif isinstance(first, ast.Constant) and isinstance(first.value, str):
            found.add(os.path.basename(first.value.split()[0]))
    return found


def _refusals(path: Path) -> list[str]:
    """Refusal classes declared in a file — ONE signature of a thing that can say no.

    THE COLUMN SAYS `REFUSES`, NOT `GATES`, AND THE NARROWING IS THE POINT. Raising is not
    the only way to gate: build_inspector is THE post-build gate and declares no refusal
    class in its fire path — it returns findings and exits 1, and the emit chokepoint
    refuses on them. A blank here means "declares no refusal class", never "does not gate".
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
    """Every component on disk that holds a charter and ships code. Sorted, derived.

    THE ROSTER IS DISK. A hand-kept list of "the gates" would go stale the first time one
    moved, and silently — the failure ground_loop's discovery was ruled into existence to
    kill (Akien, 2026-08-11: "THE PROBLEM WITH SUBSCRIBE IS NOW YOU HAVE A LIST THAT YOU
    HAVE TO MAINTAIN AND CAN BECOME STALE"). A component without an intention does not run,
    so the charter IS the membership test.
    """
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
    """The whole report: every component, where its LLM is, and the verdict that follows.

    Raises on an empty corpus rather than returning a clean-looking nothing — the hollow
    floor import_sieve builds into ``catches`` for the same reason (Law 8: a green over
    zero files is not a green).
    """
    root = Path(root).resolve()
    graph = import_sieve.import_graph(str(root))
    if not graph:
        raise import_sieve.HollowScan(
            f"determinism: no .py files under {root} — a report over an unread tree would "
            "show every component pure, which is the shape of a green that means nothing")

    def walk(mods: list[str]) -> dict:
        llm: dict[str, str] = {}
        offbox: dict[str, str] = {}
        gate: dict[str, str] = {}
        shells: set[str] = set()
        reached: set[str] = set()
        for mod in mods:
            if mod not in graph:
                continue
            closure = dict(import_sieve.reaches(graph, mod))
            closure[mod] = [mod]
            reached |= set(closure)
            for path in closure:
                shells |= shell_targets(root / path)
                for imported in graph.get(path, ()):
                    for t in LLM:
                        if import_sieve._matches(imported, t):
                            llm.setdefault(t, " -> ".join(closure[path]))
                    # A GATE IS WHAT DOES THE COMPARE, NOT WHAT CALLS ONE. Direct import
                    # only, and only from the component's OWN modules — measured, first
                    # run: the transitive reading made skills/chart a gate because it can
                    # reach build_inspector, and then red it for the SLEEP seam it is
                    # entitled to. Under a transitive rule gate-ness spreads up every
                    # caller until everything is a gate, and a rule that reds everything
                    # gets ignored.
                    if path in mods:
                        for t in GATE:
                            if import_sieve._matches(imported, t):
                                gate.setdefault(t, path)
                    for t in OFF_BOX:
                        if import_sieve._matches(imported, t):
                            offbox.setdefault(t, " -> ".join(closure[path]))
        return {"llm": llm, "offbox": offbox, "gate": gate, "shells": sorted(shells),
                "reach": len(reached)}

    empty = {"llm": {}, "offbox": {}, "gate": {}, "shells": [], "reach": 0}
    rows = []
    for comp in components(root):
        fire_mods = [m for m in comp["modules"] if os.path.basename(m) not in SEAMS]
        seam_mods = [m for m in comp["modules"] if os.path.basename(m) in SEAMS]
        fire = walk(fire_mods)
        seam = walk(seam_mods) if seam_mods else dict(empty)
        if fire["llm"]:
            verdict = ORACLE
        elif seam["llm"]:
            verdict = MOSTLY
        else:
            verdict = PURE
        # A GATE IS THE COMPONENT THAT REACHES THE == COMPARE, and the gate tool itself is
        # not one — it IS the compare, the way a lock is not a door. Excluding it by
        # address keeps the roster honest: otherwise every gate count starts at one for
        # free, which is a green earned by counting the ruler among the things measured.
        gate_via = {**seam["gate"], **fire["gate"]}
        is_gate = bool(gate_via) and comp["path"] != GATE_TOOL_PATH
        rows.append({**comp,
                     "rung": _rung(comp["path"]),
                     "verdict": verdict,
                     "is_gate": is_gate,
                     "gate_via": gate_via.get(GATE[0], ""),
                     # THE ONE RULE THAT IS NOT A REPORT. Akien: "NO GATES MAY CONSULT
                     # ORACLES EVER PERIOD." A gate whose fire path OR whose SLEEP seam
                     # reaches the LLM is in violation — a gate has no legitimate SLEEP
                     # seam either, because a gate that gets rewritten by an oracle
                     # between runs does not replay, and Law 7 makes its verdict permanent.
                     "gate_violation": is_gate and bool(fire["llm"] or seam["llm"]),
                     "refuses": bool({r for m in fire_mods for r in _refusals(root / m)}),
                     "llm": fire["llm"],
                     "offbox": fire["offbox"],
                     "shells": fire["shells"],
                     "seams": seam_mods,
                     "seam_llm": seam["llm"],
                     "reach": fire["reach"]})
    order = {PURE: 0, MOSTLY: 1, ORACLE: 2}
    rows.sort(key=lambda r: (order[r["verdict"]], r["path"]))
    gates = [r for r in rows if r["is_gate"]]
    return {"root": str(root), "components": len(rows), "rows": rows,
            "gates": len(gates),
            "gate_violations": [r["path"] for r in gates if r["gate_violation"]],
            "counts": {v: sum(1 for r in rows if r["verdict"] == v)
                       for v in (PURE, MOSTLY, ORACLE)}}


def render(report: dict) -> str:
    """The surface Akien reads. One line per component, evidence indented under it."""
    L = []
    c = report["counts"]
    L.append("=" * 78)
    L.append("DETERMINISM — where the LLM is, per component")
    L.append("=" * 78)
    L.append(f"{report['components']} components  ·  {c[PURE]} pure  ·  "
             f"{c[MOSTLY]} mostly (LLM at SLEEP only)  ·  {c[ORACLE]} LLM in the loop")
    L.append("")

    # THE GATES FIRST, because they are the thing being inspected and the rule over them is
    # absolute. A gate list that could be empty and still print a header would be a green
    # earned by having nothing to check, so zero gates says so in those words.
    gates = [r for r in report["rows"] if r["is_gate"]]
    L.append("--- GATES " + "-" * 54)
    L.append("    NO GATE MAY CONSULT AN ORACLE. A gate opens only on an == compare against")
    L.append("    what it allows — identical, or it stays shut. (Akien, 2026-08-13)")
    if not gates:
        L.append("")
        L.append("    NONE — no component reaches cairn.tools.gate. Nothing here is gated,")
        L.append("    and a rule over an empty set is not a green.")
    for r in gates:
        bad = r["gate_violation"]
        L.append("")
        L.append(f"  {'VIOLATION' if bad else 'clean    '}  {r['path']:44s} {r['verdict']}")
        L.append(f"      gate via {r['gate_via']}")
        if bad:
            for t, chain in sorted({**r["llm"], **r["seam_llm"]}.items()):
                L.append(f"      REACHES AN ORACLE: {t}   via {chain}")
    L.append("")
    mark = {PURE: "  ", MOSTLY: "~ ", ORACLE: "! "}
    last = None
    for r in report["rows"]:
        if r["verdict"] != last:
            L.append("")
            L.append(f"--- {r['verdict']} " + "-" * (58 - len(r["verdict"])))
            last = r["verdict"]
        flag = "  GATE" if r["is_gate"] else ""
        refuses = "REFUSES" if r["refuses"] else "       "
        L.append(f"{mark[r['verdict']]}{r['path']:44s} {r['rung']:14s} {refuses}{flag}")
        for t, chain in sorted(r["llm"].items()):
            L.append(f"      LLM IN THE LOOP: {t}   via {chain}")
        if r["seam_llm"]:
            L.append(f"      SLEEP seam ({', '.join(os.path.basename(s) for s in r['seams'])})"
                     f" reaches the LLM   [out of band, by design]")
        if r["shells"]:
            L.append(f"      shells to: {', '.join(r['shells'])}")
        if r["offbox"]:
            L.append(f"      off-box (not an oracle): {', '.join(sorted(r['offbox']))}")
    return "\n".join(L)


def main(argv: list[str] | None = None) -> int:
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    as_json = "--json" in argv
    argv = [a for a in argv if a != "--json"]
    root = argv[0] if argv else str(Path(__file__).resolve().parents[3])
    report = measure(root)
    print(json.dumps(report, indent=2) if as_json else render(report))
    # EXIT 1 ON A GATE VIOLATION, so the one absolute rule is readable by anything that can
    # read an exit code. Everything else in this report is a measurement Akien dispositions;
    # "no gate consults an oracle" is not a measurement, it is the rule.
    return 1 if report["gate_violations"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
