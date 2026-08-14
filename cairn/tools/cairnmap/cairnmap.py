"""cairn/tools/cairnmap/cairnmap.py — the help surface, compiled from charters. Zero inference.

THE THREE RULINGS THAT FIX WHAT THIS IS (Akien, 2026-07-15, MAP.md "cairnmap"):
a VIEW, not a device — it owns no truth, only the render; CONTEXTUAL — v0 scopes by
WHERE (stand in a component's directory and you are briefed on that component, the
runtime twin of Cairn's founding move); REFERENCE ONLY — it describes commands, it
never runs them.

COMPILED, NOT AUTHORED. ``render(charters, context) -> surface`` with no model in the
loop. Law 5 already makes every component co-locate its ``intention+why.json``; this
module projects those files and nothing else. It cannot drift, because it is derived:
regenerate -> current. A hand-written help page is the schema-apart-from-data rot the
design names as the thing that killed the quarry's docs.

ITS PROOF IS THE DERIVATION GATE — completeness both ways. Every charter'd command and
skill appears; nothing without a charter appears. An uncharted command does not get a
help line, it gets a RED — so the map is not a doc you trust but a live check that the
command-set and the help-set are the same set.

AND THAT GATE HOLDS A PROOF RECORD, NOT A COMPLAINT LIST (Akien, 2026-08-13: "EVERYTHING
ALWAYS PROVED AND LISTING WHAT IT PROVED ... SAME PATTERN EVERYWHERE"). ``inspect`` names
every lane that RAN with its EXPECTED beside its ACTUAL, passes included; ``check`` is a
VIEW over the mismatches, derived and never parallel. What that retires: `green` used to
be printed on an EMPTY list, which is the same bytes whether every lane agreed, the
roster was never read, or the walk found no charters at all — green on silence. The skill lane checks three records that
must agree (charter beside the code, roster in node_classes/skill.json, symlink in the
install dir) because the measured 2026-07-31 defect was exactly their disagreement:
/chart, /moreabout and /sail carried charters and symlinks but were absent from the
roster, and nothing red'd.

THE CHARTER IS THE HELP. Zero inference means this can only show what a charter already
says plainly — so a confusing entry here is a bug in the charter, fixed at source.

HOW A COMMAND IS OWNED (the v0 convention, filed as an edge in the charter): a charter
— or a top-level facility block inside one carrying its own ``what`` + ``invoke`` (the
``flight_recorder`` shape in bin's charter) — owns ``cairn <name>`` iff its ``invoke``
mentions it. A convention the gate enforces, not yet a schema field.
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

from cairn.tools.base import address
from cairn.tools.gate import gate

CHARTER = "intention+why.json"
WIDTH = 78


# ── the world ────────────────────────────────────────────────────────────────
# The same seam ruling.py and CAIRN_CMD_DIR give their proofs: override the parent of
# the two roots and the whole module runs against a temp world, never the live tree.

def roots_parent() -> Path:
    override = os.environ.get("CAIRN_ROOTS_PARENT")
    if override:
        return Path(override)
    return Path(__file__).resolve().parents[4]        # cairn/tools/cairnmap/ -> cairn/ -> repo -> parent


def repo_root() -> Path:
    return roots_parent() / "cairn"


def commons_root() -> Path:
    return roots_parent() / "CairnCommons"


def skills_install_dir() -> Path:
    override = os.environ.get("CAIRN_SKILLS_INSTALL_DIR")
    if override:
        return Path(override)
    return Path.home() / ".claude" / "skills"


# ── gather: read every charter, loudly ───────────────────────────────────────

def gather(repo: Path | None = None) -> tuple[list[dict], list[str]]:
    """Every ``intention+why.json`` under the repo, sorted by path.

    Returns ``(charters, reds)``. A charter that fails to parse is a RED, never a
    skip (Law 7): a silently absent component is exactly the invisible failure a
    completeness surface exists to kill. It still gets a stub entry so the map shows
    the address of the wreck.
    """
    repo = repo or repo_root()
    charters, reds = [], []
    for path in sorted(repo.rglob(CHARTER)):
        if any(part.startswith(".") or part == "__pycache__" for part in path.parts):
            continue
        rel = path.relative_to(repo)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            reds.append(f"unreadable charter: {rel} — {type(exc).__name__}: {exc}")
            data = {}
        charters.append({"path": path, "rel": str(rel), "dir": str(rel.parent), "data": data})
    return charters, reds


def units(charter: dict) -> list[dict]:
    """The invocable units a charter carries: the charter itself, plus any top-level
    facility block (a dict value with its own ``what`` + ``invoke`` strings — the
    ``flight_recorder`` precedent in bin's charter, generalized)."""
    data = charter["data"]
    out = [{"charter": charter, "what": data.get("what", ""), "invoke": data.get("invoke", "")}]
    for value in data.values():
        if (isinstance(value, dict)
                and isinstance(value.get("what"), str) and isinstance(value.get("invoke"), str)):
            out.append({"charter": charter, "what": value["what"], "invoke": value["invoke"]})
    return out


# ── the three record sets the gate compares ──────────────────────────────────

def commands(repo: Path | None = None) -> list[str]:
    cmd_dir = (repo or repo_root()) / "bin" / "cmd"
    if not cmd_dir.is_dir():
        return []
    return sorted(p.name for p in cmd_dir.iterdir()
                  if p.is_file() and os.access(p, os.X_OK))


def skill_roster(commons: Path | None = None) -> tuple[list[str], str | None]:
    """``members_so_far`` from the skill node-class, names without the slash.
    A missing or unreadable roster is a red, not an empty list — the roster is a
    record of truth, and this gate is the physics its roster_note asked for."""
    path = (commons or commons_root()) / "node_classes" / "skill.json"
    try:
        members = json.loads(path.read_text(encoding="utf-8")).get("members_so_far", [])
        return sorted(m.lstrip("/") for m in members), None
    except Exception as exc:
        return [], f"skill roster unreadable: {path} — {type(exc).__name__}: {exc}"


def installed_skills(install: Path | None = None) -> dict[str, Path | None]:
    """Name -> resolved target for every entry in the install dir (None = dangling)."""
    install = install or skills_install_dir()
    if not install.is_dir():
        return {}
    out: dict[str, Path | None] = {}
    for entry in sorted(install.iterdir()):
        try:
            out[entry.name] = entry.resolve(strict=True)
        except OSError:
            out[entry.name] = None
    return out


# ── the derivation gate: completeness both ways ──────────────────────────────

def _entry_of(identity: str, *, expected, actual, location: str, reds: list[str],
              **values) -> dict:
    """One entry of this gate's proof record, in the seed's shape.

    ``reds`` rides as a LIST and the refusal sentence is joined from it, never split
    back out of one: a red may legitimately contain the separator (an exception's own
    message does), and re-splitting a joined string is a parser guessing at what it
    just built. The list is the record; the sentence is the render.
    """
    return gate.proved(identity=identity, expected=expected, actual=actual,
                       location=location, code="cairnmap.py:%s" % identity,
                       source="cairnmap.inspect", reds=list(reds),
                       lack="; ".join(reds), **values)


def inspect(repo: Path | None = None, commons: Path | None = None,
            install: Path | None = None) -> list[dict]:
    """THE PROOF RECORD this gate opens on: one entry per check that RAN, EXPECTED
    beside ACTUAL, passes included (Akien, 2026-08-13: "EVERYTHING ALWAYS PROVED AND
    LISTING WHAT IT PROVED ... SAME PATTERN EVERYWHERE").

    What it replaces, and why the replacement is not cosmetic: ``check`` returned only
    the reds, so `derivation gate: green` was printed on an EMPTY list — the same bytes
    whether every lane agreed, the roster was never read, or the walk found no charters
    at all. Green on silence. Each lane now says what it EXPECTED and what it ACTUALLY
    found, so a lane that stops running makes this record SHORTER rather than cleaner.

    A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED: the three per-skill lanes append
    nothing when the roster itself is unreadable, because the entry above them has
    already closed the gate and comparing against an empty roster would manufacture
    findings that are really one finding.
    """
    repo = repo or repo_root()
    charters, unreadable = gather(repo)
    record: list[dict] = []

    record.append(_entry_of(
        "every_charter_parses",
        expected=[], actual=unreadable,
        location="cairn/tools/cairnmap",
        reds=unreadable,
        charters_found=len(charters)))

    # A component without an intention doesn't run (CLAUDE.md) — code with no charter.
    # WHICH DIRECTORIES ARE COMPONENTS IS NOT THIS FILE'S QUESTION (address.component_dirs,
    # 2026-08-13). It used to be a one-level iterdir, and after the rung move that walk
    # accused `devices/`, `machines/` and `tools/` of being chartless components — three
    # reds naming containers instead of the code inside them, which is a gate lying about
    # where to look. The rungs carry a package __init__ and no charter, so a shallower
    # test cannot tell them from a real component; only the roster can.
    pkg = repo / "cairn"
    chartered_dirs = {c["dir"] for c in charters}
    chartless = []
    if pkg.is_dir():
        for d in address.component_dirs(pkg)[0]:
            if any(d.glob("*.py")) and str(d.relative_to(repo)) not in chartered_dirs:
                chartless.append(str(d.relative_to(repo)))
    record.append(_entry_of(
        "every_component_carries_a_charter",
        expected=[], actual=sorted(chartless),
        location="cairn/",
        reds=["component without a charter: %s/ (code that, by CLAUDE.md, "
              "doesn't run)" % d for d in sorted(chartless)],
        components_walked=len(address.component_dirs(pkg)[0]) if pkg.is_dir() else 0))

    # Skill lane: charter <-> roster <-> installed symlink must be the same set.
    chartered = {Path(c["dir"]).name for c in charters if c["dir"].startswith("skills/")}
    roster, roster_err = skill_roster(commons)
    record.append(_entry_of(
        "the_skill_roster_is_readable",
        expected=[], actual=[roster_err] if roster_err else [],
        location="CairnCommons/node_classes/skill.json",
        reds=[roster_err] if roster_err else [],
        roster_size=len(roster)))

    installed = installed_skills(install)
    # GUARDED: an unreadable roster is ONE finding. Comparing a charter set against the
    # empty list it degrades to would append a second entry per skill, all of them
    # derived from the failure above — the gate is already closed, and a record that
    # multiplies one fault into fifteen is a diagnostic surface lying about how many
    # things are wrong. Absent, not passed.
    if not roster_err:
        record.append(_entry_of(
            "every_chartered_skill_is_on_the_roster",
            expected=sorted(chartered), actual=sorted(chartered & set(roster)),
            location="CairnCommons/node_classes/skill.json",
            reds=["skill missing from the roster: /%s carries a charter but "
                  "node_classes/skill.json members_so_far omits it (the measured "
                  "2026-07-31 defect)" % n for n in sorted(chartered - set(roster))]))
        record.append(_entry_of(
            "every_roster_entry_carries_a_charter",
            expected=sorted(roster), actual=sorted(set(roster) & chartered),
            location="skills/",
            reds=["roster entry with no charter: /%s is in members_so_far but "
                  "skills/%s/%s does not exist" % (n, n, CHARTER)
                  for n in sorted(set(roster) - chartered)]))

    where = skills_install_dir() if install is None else install
    record.append(_entry_of(
        "every_chartered_skill_is_installed",
        expected=sorted(chartered), actual=sorted(chartered & set(installed)),
        location=str(where),
        reds=["skill not installed: /%s carries a charter but has no entry in %s"
              % (n, where) for n in sorted(chartered - set(installed))]))

    strays, misaimed = [], []
    for name, target in sorted(installed.items()):
        if name not in chartered:
            strays.append("installed skill with no charter: %s -> %s" % (name, target))
        elif target is None or target != (repo / "skills" / name).resolve():
            misaimed.append("installed skill points away from its charter'd source: "
                            "%s -> %s" % (name, target))
    record.append(_entry_of(
        "every_installed_skill_points_at_its_charter",
        expected=[], actual=strays + misaimed,
        location=str(where),
        reds=strays + misaimed,
        installed_count=len(installed)))

    # Command lane: every bin/cmd/<name> is owned by some charter'd unit's invoke.
    all_units = [u for c in charters for u in units(c)]
    cmds = commands(repo)
    owned = []
    for name in cmds:
        pat = re.compile(rf"\bcairn\s+{re.escape(name)}\b")
        if any(pat.search(u["invoke"]) for u in all_units):
            owned.append(name)
    record.append(_entry_of(
        "every_command_is_named_by_a_charter",
        expected=sorted(cmds), actual=sorted(owned),
        location="bin/cmd/",
        reds=["command without a charter: bin/cmd/%s — no charter's invoke mentions "
              "`cairn %s`, so it cannot render (an undocumented command is impossible, "
              "by design)" % (n, n) for n in sorted(set(cmds) - set(owned))],
        units_searched=len(all_units)))

    return record


def check(repo: Path | None = None, commons: Path | None = None,
          install: Path | None = None) -> list[str]:
    """Every red the compiled surface can see, in one pass (complete diagnostic on the
    first pass — never make the reader re-run to learn the next one).

    A VIEW OVER ``inspect``, DERIVED AND NEVER PARALLEL. Two mouths for one question is
    how a gate and the sentence it prints come to disagree about what failed, so the
    reds are read back out of the record's own mismatches rather than accumulated
    beside it. Each entry carries its reds as a LIST, so this reads them straight back
    out and stays byte-identical to what callers already read.
    """
    reds: list[str] = []
    for e in inspect(repo, commons, install):
        if gate.passed(e):
            continue
        reds.extend(e.get("values", {}).get("reds") or [])
    return reds


# ── render: the map, and the standing-in-a-directory brief ───────────────────

def _wrap(text: str, indent: str = "  ") -> str:
    out, line = [], indent
    for word in str(text).split():
        if len(line) + len(word) + 1 > WIDTH and line.strip():
            out.append(line.rstrip())
            line = indent + word + " "
        else:
            line += word + " "
    if line.strip():
        out.append(line.rstrip())
    return "\n".join(out)


def first_sentence(text: str) -> str:
    """Deterministic one-liner: up to the first sentence break. Truncation, never
    summary — a mechanical cut is projection, a paraphrase would be inference."""
    text = " ".join(str(text).split())
    m = re.search(r"\.(\s|$)", text)
    return text[:m.end()].rstrip() if m else text


def _entry(name: str, what: str, pad: int) -> str:
    body = _wrap(first_sentence(what) or "(charter has no `what`)",
                 " " * (pad + 5)).lstrip()
    return f"  {name.ljust(pad)} — {body}"


def render_map(repo: Path | None = None, commons: Path | None = None,
               install: Path | None = None) -> str:
    repo = repo or repo_root()
    charters, _ = gather(repo)
    reds = check(repo, commons, install)
    by_dir = {c["dir"]: c for c in charters}
    lines = ["═" * WIDTH,
             "CAIRNMAP — compiled from charters, zero inference".center(WIDTH),
             "a view: it describes what you can do here; invocation stays with the commands".center(WIDTH),
             "═" * WIDTH, ""]

    skills = sorted(c for c in by_dir if c.startswith("skills/") and c != "skills")
    if skills:
        pad = max(len(Path(d).name) + 1 for d in skills)
        lines.append("SKILLS — the work loop (type /name in a session)")
        for d in skills:
            lines.append(_entry("/" + Path(d).name, by_dir[d]["data"].get("what", ""), pad))
        lines.append("")

    cmds = commands(repo)
    all_units = [u for c in charters for u in units(c)]
    owned = []
    for name in cmds:
        pat = re.compile(rf"\bcairn\s+{re.escape(name)}\b")
        unit = next((u for u in all_units if pat.search(u["invoke"])), None)
        if unit:                                 # the uncharted render only as reds
            owned.append((name, unit))
    if owned:
        pad = max(len(n) for n, _ in owned)
        lines.append("COMMANDS — cairn <name>")
        for name, unit in owned:
            lines.append(_entry(name, unit["what"], pad))
        lines.append("")

    comps = sorted(d for d in by_dir if not d.startswith("skills/"))
    if comps:
        pad = max(len(d) for d in comps)
        lines.append("COMPONENTS — stand in the directory (or `cairn cairnmap <dir>`) "
                     "for the full charter")
        for d in comps:
            lines.append(_entry(d if d != "." else "(repo root)",
                                by_dir[d]["data"].get("what", ""), pad))
        lines.append("")

    lines.append("COMPLETENESS — the derivation gate, both ways")
    if reds:
        for red in reds:
            lines.append(_wrap("RED: " + red, "  "))
    else:
        lines.append("  green — every command, skill and component traces to a charter,")
        lines.append("  and nothing renders without one.")
    lines.append("")
    lines.append("─" * WIDTH)
    lines.append(_wrap(f"Compiled from {len(charters)} charters. The charter is the "
                       "help: a wrong or confusing entry above is a bug in its "
                       "charter, fixed at source — never here.", ""))
    lines.append("═" * WIDTH)
    return "\n".join(lines)


def _render_value(value, indent: str = "  ") -> str:
    if isinstance(value, str):
        return _wrap(value, indent)
    if isinstance(value, list):
        return "\n".join(indent + "· " + _wrap(v, indent + "  ").lstrip()
                         if isinstance(v, str)
                         else indent + "· " + json.dumps(v, ensure_ascii=False)
                         for v in value)
    if isinstance(value, dict):
        parts = []
        for k, v in value.items():
            parts.append(f"{indent}{k}:")
            parts.append(_render_value(v, indent + "  "))
        return "\n".join(parts)
    return _wrap(json.dumps(value), indent)


def render_detail(charter_path: Path) -> str:
    """The standing-in-a-directory brief: the whole charter, every field, in the
    file's own order. No whitelist — a field the author wrote is a field the
    reader gets, or the charter and the help have two owners."""
    data = json.loads(charter_path.read_text(encoding="utf-8"))
    lines = ["═" * WIDTH,
             f"{data.get('component', charter_path.parent.name)} — {charter_path}".center(WIDTH),
             "═" * WIDTH]
    for key, value in data.items():
        lines.append("")
        lines.append(key.upper())
        lines.append(_render_value(value))
    lines.append("═" * WIDTH)
    return "\n".join(lines)


def context_charter(cwd: Path, repo: Path | None = None) -> Path | None:
    """WHERE the caller stands: the nearest charter at or above cwd, inside the repo.
    The v0 context key — the next axis (WHO) is designed-in and not yet built."""
    repo = (repo or repo_root()).resolve()
    cur = cwd.resolve()
    while True:
        if cur == repo or repo not in cur.parents:
            return None                    # at the root (or outside): the whole map
        if (cur / CHARTER).is_file():
            return cur / CHARTER
        cur = cur.parent
