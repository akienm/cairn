"""THE SEAM THAT LETS A MARKDOWN-EXECUTED SKILL RIDE THE LEARNING BLOCK ANATOMY.

A skill's executor is an LLM reading markdown, so a door the markdown *asks* to be
called is policy, not physics — the exact skate ticket ``skills-migrate-one-blow``
exists to close. Cairn already solved this for LLM-executed steps, and not by trust:
the chart bricks gate the packet, berth it, and let a downstream consumer refuse to
proceed without the artifact. This module applies that proven shape to a skill.

WHAT IT IS NOT: a second learning primitive. Every organ here is
``cairn.learning_block``'s — the door, the trace, the finding. This seam owns exactly
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

from cairn.base.address import instance_path
from cairn.learning_block.learning_block import (
    DoorRefused,
    declare_contract,
    emit_finding,
    fire_door,
)

_REPO = Path(__file__).resolve().parents[2]
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
    cairn.skill_block fire <skill>`` ran the flat contract alone — two entrances with
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


def _write_berth(skill: str, payload: dict, door_rec: dict, finding_rec: dict,
                 when: datetime, *, root: Path | None = None) -> Path:
    base = berth_root(root) / skill
    base.mkdir(parents=True, exist_ok=True)
    stamp = when.strftime("%Y%m%dT%H%M%S")
    path = base / f"{skill}-{stamp}-{uuid.uuid4().hex[:12]}.json"
    path.write_text(json.dumps({
        "skill": skill,
        "block": block_name(skill),
        "when": when.isoformat(),
        "exit": payload.get("exit"),
        "answers": {k: v for k, v in payload.items() if k != "bullets"},
        "bullets": finding_rec["data"]["bullets"],
        "trace_id": door_rec["id"],
        "finding_id": finding_rec["id"],
    }, indent=2, sort_keys=True) + "\n")
    return path


def fire(skill: str, payload: dict, *, now: datetime | None = None,
         skills_root: Path | str | None = None,
         berths: Path | str | None = None,
         trace_root: Path | None = None,
         judge_kwargs: dict | None = None) -> dict:
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
    if exit_value is not None and exit_value not in EXITS:
        semantic.append({
            "field": "exit",
            "why": f"exit {exit_value!r} is not one of {EXITS}. The two exits are not "
                   "decoration — routed_out is the kill, and it is counted separately "
                   "because it is the exit the whole trace organ was built to stop losing.",
        })

    door_rec = fire_door(contract, payload, now=when, root=trace_root,
                         extra_lacks=semantic, judge=judge_name)

    finding_rec = emit_finding(block, list(payload.get("bullets") or []),
                               now=when, root=trace_root)
    path = _write_berth(skill, payload, door_rec, finding_rec, when, root=berths)
    return {
        "berth": str(path),
        "block": block,
        "exit": exit_value,
        "trace_id": door_rec["id"],
        "finding_id": finding_rec["id"],
    }


def read_berth(path: Path | str) -> dict | None:
    """Read a berthed firing. ``None`` when it is missing or unreadable — the caller
    (a gate) turns that into a finding with the address in it, rather than an exception
    that says nothing about which berth failed."""
    try:
        doc = json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return None
    return doc if isinstance(doc, dict) else None


__all__ = [
    "EXITS", "SkillBlockRefused", "DoorRefused",
    "block_name", "load_contract", "judge_for", "berth_root", "fire", "read_berth",
]
