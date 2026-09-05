"""THE SORTED DOOR — the cast stops being a paragraph and becomes a refusable packet.

/sorted is tenant #2 of the ``cairn.machines.skill_block`` seam (ticket
``sorted-becomes-a-learning-block``, opus-pass rank 3 ruled spec 2026-08-03). The flat
contract in ``skills/sorted/intention+why.json`` is the seam's half; this module is the
other half: the SEMANTIC judges the flat {field: why} shape cannot express —

- the node class must RESOLVE in ``CairnCommons/node_classes/`` (the same
  ``load_class_def`` the emit chokepoint runs — one implementation, two mouths);
- the workflow string must PARSE and CONFORM to the class's registered version, with
  its cursor still at the cast (a drifted string refused here costs one fix; the same
  string refused at its first crossing costs a dead voyage);
- the watchme spec is judged by THE EMISSION GATE'S OWN RULE
  (``cairn.tools.base.watchme_spec.watchme_spec_error`` — the five fields plus the probe
  berth, joined to the workflow's own ``WATCHME(<object>)``), or takes the named
  exemption with a JUDGEABLE reason — one carrying at least one resolvable referent
  (a path on disk, a cast ticket id, a roster command). 'none, because <one plausible
  sentence>' is the measured hollow pass this door exists to stop;
- ``exit`` and ``disposition`` must cohere, so the seam's two-exit vocabulary never
  flattens /sorted's three real outcomes.

ONE PASS, BY CONSTRUCTION: the flat lacks (the primitive's own ``check_input``) and the
semantic lacks are collected together and refused in a SINGLE ``DoorRefused`` whose
send_back is traced under ``skill:sorted`` — so a refusal is a datum the
``sorted-door-refusals`` probe can count, never a lost moment. A clean packet rides
``skill_block.fire`` unchanged: the seam berths, traces and emits the finding exactly as
it does for /intent. ZERO seam change is this build's own falsifier (the template claim).

Fire from bash (the door skills actually use):

    PYTHONPATH=$HOME/dev/src/cairn python3 skills/sorted/door.py <packet.json>

exit 0 recorded (berth printed), 2 refused (every lack named), and an unwritable
recording root follows the seam's convention: the recording never wedges the work.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:                       # script-invoked beside the skill
    sys.path.insert(0, str(_REPO))

from cairn.tools.base.transitions import (                  # noqa: E402
    IllegalTransition,
    MalformedWorkflow,
    _conform,
    load_class_def,
    parse_workflow,
)
from cairn.tools.base.watchme_spec import (                 # noqa: E402
    BERTH_FIELD,
    REQUIRED_FIELDS,
    watchme_spec_error,
)
from cairn.machines.build_inspector.inspector import reason_has_referent  # noqa: E402
from cairn.machines.learning_block.learning_block import (     # noqa: E402
    DoorRefused,
    check_input,
    write_trace,
)
from cairn.machines.skill_block import skill_block as sb       # noqa: E402

_COMMONS = _REPO.parent / "CairnCommons"
_EXEMPT_RE = re.compile(r"^none,\s*because\s+", re.IGNORECASE)

# The cast fires at the resolution pivot, so the cursor is at or before the crossing
# casting performs. A string arriving with its cursor already downstream is a record
# of a voyage that never sailed — fiction the chokepoint would trust.
_CAST_CURSORS = ("THINKME", "TICKETME")


def judge_packet(payload: dict, *, node_class_root: Path | str | None = None,
                 repo: Path | None = None, commons: Path | None = None) -> list[dict]:
    """Every SEMANTIC lack, one pass — {field, why} dicts, the door's own vocabulary.

    Judges only fields that are PRESENT; absence is the flat contract's finding, and
    reporting it twice would be two doors disagreeing about one lack.
    """
    lacks: list[dict] = []
    kw = {"root": node_class_root} if node_class_root is not None else {}

    node_class = payload.get("node_class")
    class_def = None
    if isinstance(node_class, str) and node_class.strip():
        try:
            class_def = load_class_def(node_class.strip(), **kw)
        except (IllegalTransition, OSError, json.JSONDecodeError) as exc:
            lacks.append({"field": "node_class",
                          "why": f"does not resolve: {exc} — an unknown class is a demand "
                                 "to write one FIRST, not a value to improvise"})

    workflow = payload.get("workflow")
    wf = None
    if isinstance(workflow, str) and workflow.strip():
        try:
            wf = parse_workflow(workflow)
        except MalformedWorkflow as exc:
            lacks.append({"field": "workflow", "why": f"does not parse: {exc}"})
        if wf is not None:
            if class_def is not None:
                if wf.node_class != node_class.strip():
                    lacks.append({"field": "workflow",
                                  "why": f"names class {wf.node_class!r} while the packet casts "
                                         f"{node_class!r} — one node, one class"})
                else:
                    try:
                        _conform(wf, class_def)
                    except (IllegalTransition, MalformedWorkflow) as exc:
                        lacks.append({"field": "workflow",
                                      "why": f"does not conform to the registered "
                                             f"{wf.node_class}@{wf.version}: {exc}"})
            if wf.here not in _CAST_CURSORS:
                lacks.append({"field": "workflow",
                              "why": f"cursor stands at {wf.here!r} — a cast fires at the pivot "
                                     f"({' or '.join(_CAST_CURSORS)}); a cursor already "
                                     "downstream records a voyage that never sailed"})

    watchme = payload.get("watchme")
    empty_watchme = (watchme is None or watchme == {} or
                     (isinstance(watchme, str) and not watchme.strip()))
    if empty_watchme:
        pass  # absence is the flat contract's lack; a second report would be a second door
    elif not isinstance(watchme, (dict, list, str)):
        lacks.append({"field": "watchme",
                      "why": f"carries a {type(watchme).__name__} — the legal shapes are the "
                             "spec object (or a list of them, one per watch) or the "
                             "exemption string 'none, because <X>'"})
    else:
        # THE GATE'S OWN RULE, NOT A COPY OF IT. Measured 2026-08-05, n=2 in one
        # session: this door held a private five-field list, passed two casts clean,
        # and the emission gate's corpus proof redded both minutes later for the probe
        # berth the door never asked for. A check weaker than the claim it certifies
        # prints a seal on packets the gate will refuse — so the judgment here IS
        # watchme_spec_error, the code the gate runs, and the two cannot disagree
        # again. The join, the field floor, the berth, orphan specs and the
        # exemption-under-summons case all live in that one implementation.
        err = None
        if wf is not None:
            err = watchme_spec_error({"workflow_and_state": workflow, "watchme": watchme})
            if err:
                lacks.append({"field": "watchme", "why": err})
        else:
            # No parseable workflow to join against, so the gate rule cannot attach;
            # the workflow's own lack is already named above. What CAN still be said
            # in the same pass is the field floor, from the gate's own constants.
            specs = watchme if isinstance(watchme, list) else [watchme]
            for spec in (s for s in specs if isinstance(s, dict)):
                missing = [f for f in ("object", *REQUIRED_FIELDS, BERTH_FIELD)
                           if not (isinstance(spec.get(f), str) and spec[f].strip())]
                if missing:
                    lacks.append({"field": "watchme",
                                  "why": "spec is missing " + ", ".join(missing) +
                                         " — the gate reads five fields plus the probe "
                                         "berth; a partial spec is a watch nobody can arm"})
        # The shape and referent judgments below are the door's own floor on an
        # exemption; when the gate rule already faulted the field, its refusal names
        # the fix and a second entry would be two doors disagreeing about one lack.
        if isinstance(watchme, str) and not err:
            m = _EXEMPT_RE.match(watchme.strip())
            if not m:
                lacks.append({"field": "watchme",
                              "why": "a string watchme must be the named exemption "
                                     "'none, because <X>' — anything else is silence with "
                                     "extra words"})
            else:
                reason = watchme.strip()[m.end():].strip()
                if not reason:
                    lacks.append({"field": "watchme",
                                  "why": "exemption with no reason after 'none, because' — "
                                         "silence with a prefix on it"})
                elif not reason_has_referent(reason, repo=repo or _REPO,
                                             commons=commons or _COMMONS):
                    lacks.append({"field": "watchme",
                                  "why": "exemption reason points at nothing checkable — it "
                                         "must carry at least one resolvable referent: a path "
                                         "on disk, a cast ticket id, or a roster command "
                                         "(bin/cmd/<name>). A plausible sentence a later "
                                         "reader cannot go verify is the hollow pass this "
                                         "door was built against"})

    tot = payload.get("task_or_ticket")
    if isinstance(tot, str) and tot.strip():
        if tot.strip().lower() not in ("ticket", "task"):
            lacks.append({"field": "task_or_ticket",
                          "why": f"{tot!r} is not 'ticket' or 'task' — carried through from "
                                 "/intent; the seed test has exactly two answers"})

    exit_value = payload.get("exit")
    disposition = payload.get("disposition")
    # EXIT MEMBERSHIP IS THE SEAM'S LACK, NOT THIS DOOR'S — since 2026-08-05 skill_block
    # names an unknown exit as a lack riding the same refusal, so restating it here would
    # send the caller two entries for one field (Law 1: settled once, not per tenant).
    # What this door owns is the coherence of the DISPOSITION with a legal exit.
    if isinstance(exit_value, str) and exit_value in sb.EXITS:
        if isinstance(disposition, str) and disposition.strip():
            d = disposition.strip()
            if exit_value == "routed_forward" and d != "cast":
                lacks.append({"field": "disposition",
                              "why": f"routed_forward carries disposition {d!r} — a forward "
                                     "routing IS the cast; anything else is a route wearing "
                                     "the wrong exit"})
            if exit_value == "routed_out" and not (d == "not-ready" or
                                                   d.startswith("escalated:")):
                lacks.append({"field": "disposition",
                              "why": f"routed_out carries disposition {d!r} — the real route is "
                                     "'not-ready' or 'escalated:<rung>', so the two-exit "
                                     "vocabulary never flattens the three real outcomes"})

    return lacks


def fire(payload: dict, *, now=None, skills_root=None, berths=None, trace_root=None,
         node_class_root=None, repo=None, commons=None) -> dict:
    """Ride the seam — which resolves ``judge_packet`` from this file's address and
    raises flat AND semantic lacks in ONE refusal, traced once under the same block.

    A passthrough, not a second door. The composition used to live here, and that is
    what let the generic entrance skip every semantic judge in the system.
    """
    return sb.fire("sorted", payload, now=now, skills_root=skills_root,
                   berths=berths, trace_root=trace_root,
                   judge_kwargs={"node_class_root": node_class_root,
                                 "repo": repo, "commons": commons})


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print("usage: python3 skills/sorted/door.py <packet.json>\n"
              "The packet carries /sorted's input_contract fields — see\n"
              "  python3 -m cairn.machines.skill_block contract sorted", file=sys.stderr)
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
        # The seam's convention, inherited on purpose: the recording never wedges the
        # work — exit 0, no berth printed, the loss loud and surfacing later at the
        # BUILDME gate for a ticket that cannot name a berth.
        print(f"/sorted: the firing could not be RECORDED — {exc}\n"
              "  no berth exists for this cast; the ticket's sorted_berth cannot be\n"
              "  filled and buildme_rides_the_sorted will refuse its BUILDME until\n"
              "  this is fixed or the named exemption is recorded.", file=sys.stderr)
        print(json.dumps({"berth": None, "recorded": False, "reason": str(exc)},
                         indent=2, sort_keys=True))
        return 0
    except DoorRefused as exc:
        lacks = getattr(exc, "lacks", None) or []
        lines = [f"  - {l['field']}: {l['why']}" for l in lacks] or [f"  - {exc}"]
        print("/sorted cast refused — every lack named on this one pass:\n"
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
