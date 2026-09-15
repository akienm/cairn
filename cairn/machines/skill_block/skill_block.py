"""THE SEAM THAT LETS A MARKDOWN-EXECUTED SKILL RIDE THE LEARNING BLOCK ANATOMY.

A skill's executor is an LLM reading markdown, so a door the markdown *asks* to be
called is policy, not physics — the exact skate ticket ``skills-migrate-one-blow``
exists to close. Cairn already solved this for LLM-executed steps, and not by trust:
the chart bricks gate the packet, berth it, and let a downstream consumer refuse to
proceed without the artifact. This module applies that proven shape to a skill.

WHAT IT IS NOT: a second learning primitive. Every organ here is
``cairn.machines.learning_block``'s — the door, the trace, the finding. This seam owns exactly
two things the primitive does not: reading a skill's declared contract from its
charter, and berthing the firing so a gate downstream can find it.

THE CONTRACT LIVES IN THE SKILL'S CHARTER, NOT HERE. ``skills/<name>/intention+why.json``
carries ``input_contract`` — ``{field: why}``. That is what makes "template brick" a claim
that can be cashed rather than asserted: migrating skill #2 adds a charter field and
changes no code in this file. It is also Law 5 — the skill's contract and the skill share
an address — and Law 4, because a contract that must say WHY each field matters cannot be
filled in by a caller looking for the cheapest way past a gate.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path

from cairn.tools.base.address import instance_path
from cairn.tools.gate import gate
from cairn.machines.learning_block.learning_block import (
    DoorRefused,
    declare_contract,
    fire_door,
)

_REPO = Path(__file__).resolve().parents[3]
_SKILLS = _REPO / "skills"

EXITS = ("routed_forward", "routed_out")

# The berth root. ONE device for the seam, with the skill as a path level — not one
# device per skill, which would multiply devices by the roster for a single component.
# The component owns the root (Law 6); the skill is a tenant inside it.
_BERTHS = Path(os.environ.get("CAIRN_SKILL_BERTHS",
                              instance_path("skill_block", 0) / "berths"))


class SkillBlockRefused(ValueError):
    """The seam's own refusal — a skill that cannot be read as a block at all.

    Distinct from ``DoorRefused``, which means the FIRING was insufficient. This one
    means the SKILL is not wired: no charter, no ``input_contract``, an unknown exit.
    A caller cannot fix it by filling in fields, so conflating the two would send a
    fixable refusal and an unfixable one back through the same channel.
    """


def block_name(skill: str) -> str:
    """The trace/gate key for a skill. Namespaced so a skill named ``intent`` and a
    component named ``intent`` cannot collide in the one trace directory."""
    return f"skill:{skill}"


def load_contract(skill: str, *, skills_root: Path | str | None = None) -> dict:
    """Read the skill's declared input contract out of its charter.

    Refuses loudly and specifically at every step — a skill with no charter, a charter
    with no ``input_contract``, a contract that is not a mapping, an empty one. Silence
    is never a legal answer: an unwired skill must not look like a skill with no
    requirements, because that door would pass everything.
    """
    root = Path(skills_root) if skills_root is not None else _SKILLS
    charter = root / skill / "intention+why.json"
    if not charter.is_file():
        raise SkillBlockRefused(
            f"skill {skill!r} cannot be fired as a block: no charter at {charter}. "
            "A component without an intention doesn't run (CLAUDE.md)."
        )
    try:
        doc = json.loads(charter.read_text())
    except (OSError, json.JSONDecodeError) as exc:
        raise SkillBlockRefused(f"skill {skill!r}: charter at {charter} is unreadable — {exc}")
    requires = doc.get("input_contract")
    if not isinstance(requires, dict) or not requires:
        raise SkillBlockRefused(
            f"skill {skill!r} declares no input_contract in {charter}. The contract lives "
            "in the charter so migrating a skill is a charter edit, not a code edit — add "
            "an 'input_contract' object of {field: why it is required}. An absent contract "
            "is NOT an empty one: a door with no requirements passes everything, which is "
            "the vacuous gate this build exists to avoid."
        )
    return declare_contract(block_name(skill), requires)


def _door_module(skill: str, skills_root: Path | str | None = None):
    """Import ``skills/<skill>/door.py``, or ``None`` when the skill has none.

    THE IMPORT IS LAZY ON PURPOSE. ``skills/<skill>/door.py`` imports this module at its
    top, so resolving it at import time here would close a cycle. Called from inside
    ``fire``, this module is already in ``sys.modules`` and the cycle never forms.
    """
    root = Path(skills_root) if skills_root is not None else _SKILLS
    path = root / skill / "door.py"
    if not path.is_file():
        return None
    import importlib.util
    spec = importlib.util.spec_from_file_location(f"cairn._skill_door_{skill}", path)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:                       # noqa: BLE001 — loud, never silent
        raise SkillBlockRefused(
            f"skill {skill!r}: its door at {path} would not import — {exc!r}. A judge that "
            "cannot load must not read as a skill with nothing to judge, because that is "
            "the vacuous pass this seam exists to stop (Law 8)."
        ) from exc
    return module


def judge_for(skill: str, *, skills_root: Path | str | None = None):
    """The skill's own SEMANTIC judge, resolved from the address the contract already
    came from: ``skills/<skill>/door.py::judge_packet``. ``None`` when the skill has no
    judge, which is a legitimate state (a flat contract with nothing to say about
    meaning) and not a lack.

    WHY THE SEAM RESOLVES IT INSTEAD OF THE CALLER CALLING IT. Before this, the judge
    lived only behind ``python3 skills/<skill>/door.py`` while ``python3 -m
    cairn.machines.skill_block fire <skill>`` ran the flat contract alone — two entrances with
    different strictness, and the generic one, reachable by anyone, skipped every
    semantic judge in the system. MEASURED 2026-08-05 with one packet carrying
    ``from_idea`` shaped like an id and resolving to nothing: the seam ACCEPTED it and
    the skill's door REFUSED it. Strictness must not depend on which command was typed
    (Law 4), so the address that yields the contract now yields the judge too.

    """
    module = _door_module(skill, skills_root)
    judge = getattr(module, "judge_packet", None) if module is not None else None
    return judge if callable(judge) else None


def berth_root(root: Path | str | None = None) -> Path:
    return Path(root) if root is not None else _BERTHS


def _write_berth(skill: str, payload: dict, door_rec: dict, berth_id: str,
                 when: datetime, *, root: Path | None = None,
                 from_finding: str | None = None) -> Path:
    base = berth_root(root) / skill
    base.mkdir(parents=True, exist_ok=True)
    stamp = when.strftime("%Y%m%dT%H%M%S")
    path = base / f"{skill}-{stamp}-{uuid.uuid4().hex[:12]}.json"
    title = (payload.get("title")
             or payload.get("slate_id")
             or payload.get("what", "")[:120]
             or "")
    doc = {
        "skill": skill,
        "block": block_name(skill),
        "title": str(title).strip(),
        "when": when.isoformat(),
        "exit": payload.get("exit"),
        "answers": {k: v for k, v in payload.items() if k != "bullets"},
        "bullets": [{"text": b} if isinstance(b, str) else b
                    for b in (payload.get("bullets") or [])],
        "trace_id": door_rec["id"],
        "finding_id": berth_id,
    }
    if from_finding:
        doc["from_finding"] = from_finding
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")
    return path


def inspect_firing(skill: str, payload: dict, semantic: list[dict],
                   *, judged: bool) -> list[dict]:
    """THE SKILL'S OWN TWO LANES, as a PROOF RECORD — one entry per check that RAN,
    EXPECTED beside ACTUAL, passes included (Akien, 2026-08-13: "EVERYTHING ALWAYS
    PROVED AND LISTING WHAT IT PROVED ... SAME PATTERN EVERYWHERE").

    They ride the primitive's record (``extra_record``) rather than raising separately,
    for the reason ``fire`` has always given: two doors about one firing is two doors.
    What is new is that they arrive as ENTRIES. Flattened into the door's one aggregate,
    a skill with no judge and a skill whose judge was satisfied read alike, and the exit
    lane — which is GUARDED, since a packet with no ``exit`` has no vocabulary to check
    — could not say it had been skipped.
    """
    record = [gate.proved(
        identity="the_skills_own_judge_finds_nothing",
        location="%s.judge_packet" % skill,
        code="skill_block.py:inspect_firing", source="skill_block.door",
        expected=[], actual=[l.get("field", "?") for l in semantic],
        lacks=list(semantic))] if judged else []

    exit_value = payload.get("exit")
    if exit_value is not None:
        # GUARDED: no exit declared means no vocabulary to check against, so this entry
        # is ABSENT — the contract's own required-field lane above has already spoken
        # about whether ``exit`` had to be there at all.
        record.append(gate.proved(
            identity="the_exit_is_one_of_the_two",
            location="%s.exit" % skill,
            code="skill_block.py:inspect_firing", source="skill_block.door",
            # BOTH SIDES READ THE SAME SENTENCE WHEN IT PASSES. A raw ``actual`` of
            # "routed_forward" against an ``expected`` of the whole vocabulary can never
            # be ==, so the lane would red on every healthy firing; the value itself
            # rides in ``exit`` where a reader can still see it.
            expected="one of %s" % ", ".join(sorted(EXITS)),
            actual=("one of %s" % ", ".join(sorted(EXITS)) if exit_value in EXITS
                    else "%r, which is neither" % exit_value),
            exit=exit_value, vocabulary=sorted(EXITS),
            lacks=[] if exit_value in EXITS else [{
                "field": "exit",
                "why": f"exit {exit_value!r} is not one of {EXITS}. The two exits are "
                       "not decoration — routed_out is the kill, and it is counted "
                       "separately because it is the exit the whole trace organ was "
                       "built to stop losing.",
            }]))
    return record


def fire(skill: str, payload: dict, *, now: datetime | None = None,
         skills_root: Path | str | None = None,
         berths: Path | str | None = None,
         trace_root: Path | None = None,
         judge_kwargs: dict | None = None,
         from_finding: str | None = None) -> dict:
    """ONE call: gate the firing, trace it, emit its finding, berth it.

    One call rather than three because the caller is an LLM reading markdown, and every
    step it must remember is a step it can skip. The skill's charter says /intent is
    "the cheapest gate in the system" — three calls would have made the cheapest gate
    the most ceremonious one.

    BOTH EXITS BERTH. ``routed_out`` — the node killed because nothing traced to the
    Telos — is the most valuable firing in the system and the only one with no
    downstream artifact to record it; today it vanishes into conversation. It berths
    here exactly like a forward routing, and its finding reaches the gate the same way.
    """
    when = now or datetime.now()
    contract = load_contract(skill, skills_root=skills_root)
    block = contract["block"]

    # The door is the primitive's, unbypassed: it traces a send_back WITH EVERY LACK and
    # then raises, so a refusal is a datum and not a lost moment. An empty `bullets` list
    # is caught here too, since check_input now reads an empty collection as a lack.
    # THE SKILL'S OWN JUDGE RIDES THE SAME REFUSAL — resolved from the same address the
    # contract came from, so no entrance is looser than any other (see `judge_for`).
    module = _door_module(skill, skills_root)
    judge = getattr(module, "judge_packet", None) if module is not None else None
    judge = judge if callable(judge) else None
    # The judge's NAME rides the refusal trace so a send_back says WHO refused. Default is
    # derived from the skill; a door whose name is not derivable (saveslate's judge is
    # "slate-door") declares JUDGE_NAME beside its judge, at its own address.
    judge_name = getattr(module, "JUDGE_NAME", f"{skill}-door") if module is not None else None
    semantic = list(judge(payload, **(judge_kwargs or {}))) if judge is not None else []

    # AN UNKNOWN EXIT IS A LACK, NOT A SEPARATE TRIP. It used to raise here, BEFORE the
    # door — so a packet that was both hollow and mis-exited came back naming only the
    # exit, and the caller fixed one thing to learn about the next. Every lack in one
    # pass is the door's whole contract; the exit rides it like any other field.
    exit_value = payload.get("exit")
    door_rec = fire_door(contract, payload, now=when, root=trace_root,
                         extra_record=inspect_firing(skill, payload, semantic,
                                                     judged=judge is not None),
                         judge=judge_name)

    berth_id = uuid.uuid4().hex[:12]
    path = _write_berth(skill, payload, door_rec, berth_id, when, root=berths,
                        from_finding=from_finding)
    return {
        "berth": str(path),
        "block": block,
        "exit": exit_value,
        "trace_id": door_rec["id"],
        "finding_id": berth_id,
    }


def reviewed_address(path: Path | str) -> Path | None:
    """Where ``sweep_reviewed`` puts a berth once the operator has reviewed it:
    ``<berths>/<skill>/<name>`` moves to ``<berths>/../logs/reviewed/<skill>/<name>``.
    ``None`` when the path is not shaped like a berth address."""
    p = Path(path)
    if p.parent.parent.name != "berths":
        return None
    return p.parent.parent.parent / "logs" / "reviewed" / p.parent.name / p.name


def read_berth(path: Path | str) -> dict | None:
    """Read a berthed firing. ``None`` when it is missing or unreadable — the caller
    (a gate) turns that into a finding with the address in it, rather than an exception
    that says nothing about which berth failed.

    A ticket carries the berth address it was cast with; a review then MOVES the berth
    (``sweep_reviewed``). The address on the ticket stays the address: a berth missing
    from ``berths/<skill>/`` is read from its reviewed home before it is called missing.
    Measured 2026-09-06: the first BUILDME crossing attempted after an operator review
    (ticket 3feb201c84ea) was refused as 'intent berth readable: False' by the very
    review that approved it."""
    for candidate in (Path(path), reviewed_address(path)):
        if candidate is None:
            continue
        try:
            doc = json.loads(candidate.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        return doc if isinstance(doc, dict) else None
    return None


_PAIR_WINDOW_SECONDS = 300


def find_paired_sorted(intent_finding_id: str, intent_when: str,
                       *, root: Path | None = None) -> dict | None:
    """Find the sorted berth that was cast from this intent.

    Structural match first (from_finding field), then timestamp proximity
    fallback for berths written before the field existed.
    """
    base = berth_root(root) / "sorted"
    if not base.is_dir():
        return None
    intent_dt = datetime.fromisoformat(intent_when)
    best_by_time: tuple[float, dict, Path] | None = None
    for berth_file in sorted(base.glob("*.json")):
        doc = read_berth(berth_file)
        if doc is None:
            continue
        if doc.get("from_finding") == intent_finding_id:
            return {"doc": doc, "path": berth_file}
        sorted_dt = datetime.fromisoformat(doc.get("when", "2000-01-01"))
        delta = (sorted_dt - intent_dt).total_seconds()
        if 0 < delta < _PAIR_WINDOW_SECONDS:
            if best_by_time is None or delta < best_by_time[0]:
                best_by_time = (delta, doc, berth_file)
    if best_by_time is not None:
        return {"doc": best_by_time[1], "path": best_by_time[2]}
    return None


_REVIEWED_LOG = Path(os.environ.get(
    "CAIRN_SKILL_REVIEWED_LOG",
    instance_path("skill_block", 0) / "reviewed.jsonl"))


def reviewed_berth_ids(*, path: Path | None = None) -> set[str]:
    p = path if path is not None else _REVIEWED_LOG
    if not p.exists():
        return set()
    ids: set[str] = set()
    for line in p.read_text().splitlines():
        if not line.strip():
            continue
        try:
            ids.add(json.loads(line)["berth_id"])
        except (json.JSONDecodeError, KeyError):
            continue
    return ids


def mark_reviewed(berth_id: str, words: str, *,
                  path: Path | None = None,
                  now: datetime | None = None) -> dict:
    when = now or datetime.now()
    p = path if path is not None else _REVIEWED_LOG
    p.parent.mkdir(parents=True, exist_ok=True)
    rec = {"berth_id": berth_id, "when": when.isoformat(), "words": words}
    with open(p, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    return rec


AUTO_DRAIN_SKILLS = {"saveslate"}


# ---------------------------------------------------------------------------
# MEASUREMENT DRAINS THE REVIEW LANE (ticket fb988505c5cb, 2026-09-15).
#
# A berth whose ticket has reached a terminal cursor is REFERENCE, not a decision
# Akien's head still has to settle — the ticket was built, proved and crossed, and
# every one of those crossings was measured. Leaving its /intent and /sorted berths
# in the review lane was costing him the one resource that funds the project (his
# review bandwidth), so the lane's membership is now measured from the ticket side:
# the ticket names its berths (``intent_berth`` / ``sorted_berth`` are berth paths;
# ``from_idea`` is an idea id whose FILE under ideas/ names the idea berth) and the
# cursor is read through the grammar (``transitions.parse_workflow``), never by
# string-matching a bracket. Nothing here writes: the reviewed log is his voice
# (Law 6) and stays byte-identical; the drain is a read-time filter.
# ---------------------------------------------------------------------------

def _commons_root() -> Path:
    """The commons the tickets and ideas are read from. ``CAIRN_ARTIFACT_ROOTS`` is the
    artifact door's own seam for a scratch world (so a proof isolates the same way the door
    does); ``CAIRN_COMMONS_ROOT`` is the inbox's; the live commons is the default."""
    env = os.environ.get("CAIRN_ARTIFACT_ROOTS")
    if env:
        try:
            named = json.loads(env)
            if isinstance(named, dict) and named.get("CairnCommons"):
                return Path(named["CairnCommons"])
        except json.JSONDecodeError:
            pass
    return Path(os.environ.get("CAIRN_COMMONS_ROOT",
                               Path.home() / "dev" / "src" / "CairnCommons"))


def tickets_root(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    env = os.environ.get("CAIRN_TICKETS_DIR")
    return Path(env) if env else _commons_root() / "tickets"


def ideas_root(root: Path | None = None) -> Path:
    if root is not None:
        return Path(root)
    env = os.environ.get("CAIRN_IDEAS_DIR")
    return Path(env) if env else _commons_root() / "ideas"


def _read_json_dict(path: Path) -> dict | None:
    """A record that cannot be read contributes NOTHING — it neither drains nor keeps.
    Law 7 for the lane: an unreadable ticket is never a reason to drop a decision."""
    try:
        doc = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError, UnicodeDecodeError):
        return None
    return doc if isinstance(doc, dict) else None


def _berth_key(value: object) -> str | None:
    """A ticket's berth pointer, normalised for the map — or None when the field carries
    ``none, because …``, an empty string, or anything that is not a path."""
    if not isinstance(value, str) or not value.startswith("/"):
        return None
    return str(Path(value).resolve())


def _idea_berth(from_idea: object, ideas: Path) -> str | None:
    """``from_idea`` is an idea id (or, on eight older tickets, a path to the idea file);
    the idea FILE carries the berth path. The berth doc itself does not record its idea
    id, which is why the join goes through the file and not the berth (D3, corrected)."""
    if not isinstance(from_idea, str) or not from_idea.strip() or from_idea.startswith("none"):
        return None
    p = Path(from_idea) if from_idea.startswith("/") else ideas / f"{from_idea}.json"
    if p.suffix != ".json":
        p = p.with_suffix(".json")
    doc = _read_json_dict(p)
    if doc is None:
        return None
    return _berth_key(doc.get("berth"))


def berth_ticket_cursors(*, tickets: Path | None = None,
                         ideas: Path | None = None) -> dict[str, list[str]]:
    """THE TICKET-SIDE MAP: berth path → the cursor STATE of every ticket naming it.

    Read from the tickets root, one pass; a ticket names up to three berths (its intent
    firing, its sorted door firing, and — through ``from_idea`` and the idea file — the
    idea that bore it). One idea bears several tickets, so a berth may collect several
    cursors; ``drains_by_measurement`` decides what the list means. A ticket whose cursor
    does not parse contributes nothing for its berths (it is UNPARSED, not terminal)."""
    from cairn.tools.base.transitions import MalformedWorkflow, parse_workflow
    tdir = tickets_root(tickets)
    idir = ideas_root(ideas)
    out: dict[str, list[str]] = {}
    if not tdir.is_dir():
        return out
    for tp in sorted(tdir.glob("*.json")):
        if tp.name.startswith("_"):
            continue
        doc = _read_json_dict(tp)
        if doc is None or not isinstance(doc.get("workflow_and_state"), str):
            continue
        try:
            state = parse_workflow(doc["workflow_and_state"]).here
        except MalformedWorkflow:
            continue
        keys = [_berth_key(doc.get("intent_berth")), _berth_key(doc.get("sorted_berth")),
                _idea_berth(doc.get("from_idea"), idir)]
        for k in keys:
            if k is not None:
                out.setdefault(k, []).append(state)
    return out


def drains_by_measurement(cursors: list[str]) -> bool:
    """The ANY-terminal rule (Akien's answer on open-d0a5003c404a, 2026-09-15): a berth
    drains when AT LEAST ONE ticket naming it rests at a terminal cursor. An empty list —
    no ticket names the berth, or every ticket naming it was unreadable — keeps it."""
    from cairn.tools.base.transitions import is_terminal
    return any(is_terminal(c) for c in cursors)


def pending_reviews(*, root: Path | None = None,
                    reviewed_path: Path | None = None,
                    drain: bool = True,
                    tickets: Path | None = None,
                    ideas: Path | None = None) -> list[dict]:
    """The review lane. ``drain=True`` (the lane Akien sees) drops every berth named by a
    terminal ticket; ``drain=False`` is the full census the deep view (``show artifact``)
    and the live-fire diff read, so a drained berth still resolves by id."""
    base = berth_root(root)
    if not base.is_dir():
        return []
    reviewed = reviewed_berth_ids(path=reviewed_path)
    cursors = berth_ticket_cursors(tickets=tickets, ideas=ideas) if drain else {}
    pending: list[dict] = []
    for skill_dir in sorted(base.iterdir()):
        if not skill_dir.is_dir():
            continue
        if skill_dir.name in AUTO_DRAIN_SKILLS:
            continue
        for berth_file in sorted(skill_dir.glob("*.json")):
            doc = read_berth(berth_file)
            if doc is None:
                continue
            if doc.get("finding_id") in reviewed:
                continue
            if drain and drains_by_measurement(cursors.get(str(berth_file.resolve()), [])):
                continue
            pending.append({
                "berth_id": doc.get("finding_id"),
                "skill": doc.get("skill", skill_dir.name),
                "title": doc.get("title", ""),
                "when": doc.get("when", ""),
                "exit": doc.get("exit"),
                "bullets": doc.get("bullets", []),
                "path": str(berth_file),
            })
    pending.sort(key=lambda r: r.get("when", ""))
    return pending


def sweep_reviewed(*, root: Path | None = None,
                   reviewed_path: Path | None = None) -> list[Path]:
    base = berth_root(root)
    reviewed = reviewed_berth_ids(path=reviewed_path)
    if not reviewed:
        return []
    dest = base.parent / "logs" / "reviewed"
    moved: list[Path] = []
    for skill_dir in sorted(base.iterdir()):
        if not skill_dir.is_dir():
            continue
        for berth_file in sorted(skill_dir.glob("*.json")):
            doc = read_berth(berth_file)
            if doc is None:
                continue
            if doc.get("finding_id") in reviewed:
                skill_dest = dest / skill_dir.name
                skill_dest.mkdir(parents=True, exist_ok=True)
                dst = skill_dest / berth_file.name
                import shutil
                shutil.move(str(berth_file), str(dst))
                moved.append(dst)
    return moved


__all__ = [
    "EXITS", "SkillBlockRefused", "DoorRefused",
    "block_name", "load_contract", "judge_for", "berth_root", "fire", "read_berth",
    "inspect_firing", "find_paired_sorted",
    "reviewed_berth_ids", "mark_reviewed", "pending_reviews", "sweep_reviewed",
    "tickets_root", "ideas_root", "berth_ticket_cursors", "drains_by_measurement",
]
