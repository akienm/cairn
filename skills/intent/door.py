"""THE INTENT DOOR — the fan-out edge, and the challenge floor the charter already declared.

/intent has ridden the ``cairn.machines.skill_block`` seam since 2026-08-01 with a flat contract
and no semantic judges. Two things that contract DECLARES were, until this module,
unenforced — declared rules with nothing behind them, which Law 4 calls a tracked debt
rather than a resting state:

- ``from_idea`` (new, 2026-08-04) — WHICH captured idea this intention came from. The
  measured red it closes: *the fan-out has no edge*. None of /intent's fields recorded
  where an intention came FROM; the trace pointed only UP, to a Law. The moment one idea
  bore three intentions, the three could not say they were siblings and none could point
  at the prose that bore them. The value must RESOLVE — an id in
  ``CairnCommons/ideas/``, a path to one, or the named exemption with a checkable
  referent. It cites the COMMONS record and never a berth path, because a berth is
  instance-space and means nothing on another machine.
- ``challenge`` — the charter says the five answers are required and that "the floor is
  presence". A one-key object satisfied ``check_input`` and therefore satisfied nothing.
  Enforcing a floor the charter already declared is not a new rule; it is the same rule,
  moved from prose into physics.

QUALITY STAYS THE MODEL'S. This door checks that a referent EXISTS and that the five
answers are PRESENT. Whether an answer is any good is Akien's gate's question — the
finding stands there either way.

ONE PASS: flat lacks and semantic lacks are raised in a SINGLE ``DoorRefused`` traced
under ``skill:intent``, so the ``intent-door-refusals`` denominator keeps counting both
kinds through one mouth.

Fire from bash (what the skill actually uses):

    PYTHONPATH=$HOME/dev/src/cairn python3 skills/intent/door.py <packet.json>

exit 0 recorded (berth printed), 2 refused (every lack named).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:                       # script-invoked beside the skill
    sys.path.insert(0, str(_REPO))

from cairn.machines.build_inspector.inspector import reason_has_referent   # noqa: E402
from cairn.machines.learning_block.learning_block import (                 # noqa: E402
    DoorRefused,
    check_input,
    write_trace,
)
from cairn.machines.skill_block import skill_block as sb                   # noqa: E402

_COMMONS = _REPO.parent / "CairnCommons"
_EXEMPT_RE = re.compile(r"^none,\s*because\s+", re.IGNORECASE)
_CHALLENGE_FIELDS = ("better_approach", "prior_art", "hidden_assumption",
                     "real_collision", "back_up")


def idea_exists(value: str, *, commons: Path | None = None) -> bool:
    """An idea id, or a path to one, resolving under ``CairnCommons/ideas/``.

    Both forms accepted because the id is what /idea prints and a path is what a reader
    copies out of a file listing; refusing one of them would teach nothing and cost a
    round trip.
    """
    base = (Path(commons) if commons is not None else _COMMONS) / "ideas"
    token = str(value).strip()
    if not token:
        return False
    if (base / f"{token}.json").is_file():
        return True
    p = Path(token).expanduser()
    if p.is_file() and p.suffix == ".json" and p.parent.name == "ideas":
        return True
    return (base / token).is_file()


def judge_packet(payload: dict, *, repo: Path | None = None,
                 commons: Path | None = None) -> list[dict]:
    """Every SEMANTIC lack, one pass. Judges only fields that are PRESENT; absence is
    the flat contract's finding, and reporting it twice would be two doors disagreeing
    about one lack."""
    lacks: list[dict] = []

    origin = payload.get("from_idea")
    if isinstance(origin, str) and origin.strip():
        raw = origin.strip()
        m = _EXEMPT_RE.match(raw)
        if m:
            reason = raw[m.end():].strip()
            if not reason_has_referent(reason, repo=repo or _REPO,
                                       commons=commons or _COMMONS):
                lacks.append({"field": "from_idea",
                              "why": "exemption reason points at nothing checkable — it must "
                                     "carry at least one resolvable referent: a path on disk, "
                                     "a cast ticket id, or a roster command (bin/cmd/<name>). "
                                     "'none, because it came up in conversation' is the "
                                     "hollow pass this judge exists to stop"})
        elif raw.lower().startswith("none"):
            lacks.append({"field": "from_idea",
                          "why": f"{raw!r} is neither an idea nor the named exemption — the "
                                 "exemption form is 'none, because <X>'; anything else "
                                 "beginning with 'none' is silence with extra words"})
        elif not idea_exists(raw, commons=commons or _COMMONS):
            lacks.append({"field": "from_idea",
                          "why": f"{raw!r} does not resolve under CairnCommons/ideas/ — an "
                                 "origin that cannot be opened is not an edge, and the whole "
                                 "point of the field is that siblings born of one idea can "
                                 "find each other and the prose that bore them. Capture it "
                                 "first with /idea, or take the named exemption"})
    elif origin is not None and not isinstance(origin, str):
        lacks.append({"field": "from_idea",
                      "why": f"carries a {type(origin).__name__} — the legal values are an "
                             "idea id, a path to one, or 'none, because <X>'"})

    tot = payload.get("task_or_ticket")
    if isinstance(tot, str) and tot.strip():
        if tot.strip().lower() not in ("ticket", "task"):
            lacks.append({"field": "task_or_ticket",
                          "why": f"{tot!r} is not 'ticket' or 'task' — the seed test has "
                                 "exactly two answers: does replaying this on a bare machine "
                                 "contribute to regrowing the system? ticket if yes, task if no"})

    challenge = payload.get("challenge")
    if isinstance(challenge, dict) and challenge:
        missing = [f for f in _CHALLENGE_FIELDS if not str(challenge.get(f) or "").strip()]
        if missing:
            lacks.append({"field": "challenge",
                          "why": "the adversarial pass is missing " + ", ".join(missing) +
                                 " — the charter declares all five required and the floor is "
                                 "PRESENCE. A partial pass is the pass not having run, and as "
                                 "an optional route it fired zero times while one measured "
                                 "session re-derived already-solved work three times"})
    elif challenge is not None and challenge != {} and not isinstance(challenge, dict):
        lacks.append({"field": "challenge",
                      "why": f"carries a {type(challenge).__name__} — the challenge is an "
                             f"object with the five answers {_CHALLENGE_FIELDS}"})

    return lacks


def fire(payload: dict, *, now=None, skills_root=None, berths=None, trace_root=None,
         repo=None, commons=None) -> dict:
    """Ride the seam. The seam resolves ``judge_packet`` from this file's address and
    raises flat AND semantic lacks in ONE refusal, so this is a passthrough and not a
    second entrance — the composition used to live here, which is exactly what made
    ``python3 -m cairn.machines.skill_block fire intent`` the looser of the two doors."""
    return sb.fire("intent", payload, now=now, skills_root=skills_root,
                   berths=berths, trace_root=trace_root,
                   judge_kwargs={"repo": repo, "commons": commons})


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print("usage: python3 skills/intent/door.py <packet.json>\n"
              "The packet carries /intent's input_contract fields — see\n"
              "  python3 -m cairn.machines.skill_block contract intent", file=sys.stderr)
        return 2
    try:
        payload = json.loads(Path(args[0]).read_text())
    except (OSError, json.JSONDecodeError) as exc:
        print(f"packet {args[0]!r} unreadable — {exc}", file=sys.stderr)
        return 2
    if not isinstance(payload, dict):
        print(f"packet {args[0]!r} must be a JSON object", file=sys.stderr)
        return 2
    try:
        result = fire(payload)
    except OSError as exc:
        # The seam's convention: the recording never wedges the work — exit 0, no berth,
        # the loss loud and surfacing later at the BUILDME gate for a ticket that cannot
        # name an intent berth.
        print(f"/intent: the firing could not be RECORDED — {exc}\n"
              "  no berth exists for this birth; the ticket's intent_berth cannot be\n"
              "  filled and buildme_rides_the_intent will refuse its BUILDME until this\n"
              "  is fixed or the named exemption is recorded.", file=sys.stderr)
        print(json.dumps({"berth": None, "recorded": False, "reason": str(exc)},
                         indent=2, sort_keys=True))
        return 0
    except DoorRefused as exc:
        lacks = getattr(exc, "lacks", None) or []
        lines = [f"  - {l['field']}: {l['why']}" for l in lacks] or [f"  - {exc}"]
        print("/intent birth refused — every lack named on this one pass:\n"
              + "\n".join(lines)
              + "\n(the refusal is recorded; fix the packet and fire again — the door "
              "re-judges the WHOLE packet, so one fix cannot earn a new first-pass "
              "refusal for something already named)", file=sys.stderr)
        return 2
    except sb.SkillBlockRefused as exc:
        print(str(exc), file=sys.stderr)
        return 2
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
