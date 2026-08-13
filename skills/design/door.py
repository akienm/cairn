"""THE DESIGN DOOR — the step between birth and cast stops being unrecorded conversation.

/design is tenant #5 of the ``cairn.machines.skill_block`` seam. It fires at the OPENING of the
design step, which makes it the odd one: /intent and /sorted gate a finished packet,
this one gates an entry. What it refuses is therefore entry-shaped —

- ``intent_berth`` must RESOLVE to a readable berth for skill ``intent``, and that
  berth's exit must be ``routed_forward``. Designing on a berth that does not exist is
  designing on nothing; designing on a berth the trace question KILLED is spending the
  resolver on a node the cheapest gate in the system already turned away. The one other
  legal value is the named exemption, judged by the same ``reason_has_referent`` the
  sorted door and ``buildme_rides_the_sorted`` use — one implementation, three mouths;
- ``entering_from`` must be ``intent`` (first pass) or ``sorted:<berth path>`` (routed
  back on a completeness red), and a sorted return must name a berth that resolves.
  This is the field that turns the back-edge /intent's charter names as ABSENT into a
  countable arrival;
- ``open_questions`` must be a LIST. A paragraph is one question wearing a plural, and
  a work list whose items cannot be struck one at a time is not a work list.

ONE PASS, BY CONSTRUCTION: flat lacks (the primitive's ``check_input``) and semantic
lacks are collected together and raised in a SINGLE ``DoorRefused`` whose send_back is
traced under ``skill:design`` — a refusal is a datum, never a lost moment. A clean
packet rides ``skill_block.fire`` unchanged.

NO ``exit`` FIELD, ON PURPOSE. This records an opening; the step's exits are /sorted's
to record at the close. Two components recording one outcome is how they come to
disagree about it.

Fire from bash (what the skill actually uses):

    PYTHONPATH=$HOME/dev/src/cairn python3 skills/design/door.py <packet.json>

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
_SORTED_ENTRY_RE = re.compile(r"^sorted:\s*(\S.*)$")


def _judge_berth(value: str, field: str, want_skill: str, *,
                 require_forward: bool) -> list[dict]:
    """Shared by both berth-bearing fields, because they fail the same four ways and a
    reader comparing two differently-worded refusals for one shape learns nothing."""
    berth = sb.read_berth(value)
    if berth is None:
        return [{"field": field,
                 "why": f"berth {value!r} does not read — the path is missing, unreadable, "
                        "or not a berth. A design session opened on a berth that does not "
                        "resolve is a design session on nothing"}]
    got = berth.get("skill")
    if got != want_skill:
        return [{"field": field,
                 "why": f"berth {value!r} was fired by skill {got!r}, not {want_skill!r} — "
                        "one field, one door; a berth from the wrong door records a "
                        "different act than the one this field claims"}]
    if require_forward and berth.get("exit") != "routed_forward":
        return [{"field": field,
                 "why": f"berth {value!r} exited {berth.get('exit')!r} — the trace question "
                        "already turned this node away, and designing on it spends the "
                        "resolver on work the cheapest gate in the system killed. If the kill "
                        "was wrong, that is a new birth at /intent, not a design session"}]
    return []


def judge_packet(payload: dict, *, repo: Path | None = None,
                 commons: Path | None = None) -> list[dict]:
    """Every SEMANTIC lack, one pass — {field, why} dicts, the door's own vocabulary.

    Judges only fields that are PRESENT; absence is the flat contract's finding, and
    reporting it twice would be two doors disagreeing about one lack.
    """
    lacks: list[dict] = []

    berth_value = payload.get("intent_berth")
    if isinstance(berth_value, str) and berth_value.strip():
        raw = berth_value.strip()
        m = _EXEMPT_RE.match(raw)
        if m:
            reason = raw[m.end():].strip()
            if not reason_has_referent(reason, repo=repo or _REPO,
                                       commons=commons or _COMMONS):
                lacks.append({"field": "intent_berth",
                              "why": "exemption reason points at nothing checkable — it must "
                                     "carry at least one resolvable referent: a path on disk, "
                                     "a cast ticket id, or a roster command (bin/cmd/<name>). "
                                     "A plausible sentence a later reader cannot go verify is "
                                     "the hollow pass this door was built against"})
        elif raw.lower().startswith("none"):
            lacks.append({"field": "intent_berth",
                          "why": f"{raw!r} is neither a berth path nor the named exemption — "
                                 "the exemption form is 'none, because <X>'; anything else "
                                 "beginning with 'none' is silence with extra words"})
        else:
            lacks += _judge_berth(raw, "intent_berth", "intent", require_forward=True)

    entering = payload.get("entering_from")
    if isinstance(entering, str) and entering.strip():
        raw = entering.strip()
        m = _SORTED_ENTRY_RE.match(raw)
        if m:
            lacks += _judge_berth(m.group(1).strip(), "entering_from", "sorted",
                                  require_forward=False)
        elif raw.lower() != "intent":
            lacks.append({"field": "entering_from",
                          "why": f"{raw!r} is not a legal entry — the two are 'intent' (a "
                                 "first pass) and 'sorted:<berth path>' (routed back on a "
                                 "completeness red). Free prose here would leave the return "
                                 "trip uncountable, which is the whole reason the field exists"})
    elif entering is not None and not isinstance(entering, str):
        lacks.append({"field": "entering_from",
                      "why": f"carries a {type(entering).__name__} — the legal values are the "
                             "string 'intent' or 'sorted:<berth path>'"})

    questions = payload.get("open_questions")
    if isinstance(questions, str) and questions.strip():
        lacks.append({"field": "open_questions",
                      "why": "is a string — the work list is a LIST. One blob is one question "
                             "wearing a plural, and a list whose items cannot be struck one at "
                             "a time cannot be worked down"})
    elif isinstance(questions, (list, tuple)) and questions:
        blank = [i for i, q in enumerate(questions) if not str(q or "").strip()]
        if blank:
            lacks.append({"field": "open_questions",
                          "why": f"entries {blank} are blank — an empty slot in a work list "
                                 "reads as a question nobody wrote down"})

    return lacks


def fire(payload: dict, *, now=None, skills_root=None, berths=None, trace_root=None,
         repo=None, commons=None) -> dict:
    """Ride the seam — which resolves ``judge_packet`` from this file's address and
    raises flat AND semantic lacks in ONE refusal. A passthrough, not a second door."""
    return sb.fire("design", payload, now=now, skills_root=skills_root,
                   berths=berths, trace_root=trace_root,
                   judge_kwargs={"repo": repo, "commons": commons})


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print("usage: python3 skills/design/door.py <packet.json>\n"
              "The packet carries /design's input_contract fields — see\n"
              "  python3 -m cairn.machines.skill_block contract design", file=sys.stderr)
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
        # The seam's convention, inherited: the recording never wedges the work. Unlike
        # /idea — where the record IS the work — the artifact of the design step is the
        # cast /sorted writes, so a lost berth costs the return-trip count, not the work.
        print(f"/design: the opening could not be RECORDED — {exc}\n"
              "  the design work can proceed; what is lost is the arrival record, so this\n"
              "  pass will not be countable as a return trip.", file=sys.stderr)
        print(json.dumps({"berth": None, "recorded": False, "reason": str(exc)},
                         indent=2, sort_keys=True))
        return 0
    except DoorRefused as exc:
        lacks = getattr(exc, "lacks", None) or []
        lines = [f"  - {l['field']}: {l['why']}" for l in lacks] or [f"  - {exc}"]
        print("/design opening refused — every lack named on this one pass:\n"
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
