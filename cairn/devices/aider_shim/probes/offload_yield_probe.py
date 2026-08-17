"""aider_shim_offload_yield — does handing a build to the apprentice actually YIELD?

THE TICKET'S WATCHME, COMPILED. The spec (CairnCommons/tickets/aider-shim.json) names this
exact path, and the emission gate resolves ARMED from it, so this module is what stands
between the WATCHME crossing and a refusal. Its fields are that spec's, kept in the spec's
own words where they are the answer:

  trigger  — "each ticket built through the shim reaches its verdict artifact — the exit
             gate's deposit is the event that already fires; no poll"
  enough   — "five shimmed tickets with green-rate and CC-tool-call comparison recorded"
  carrier  — "a verdict artifact against THIS ticket's falsifier: per shimmed ticket, did
             it pass unchanged physics, and what was the CC call count vs the direct-build
             baseline"
  nexus    — the hypothesize tree
  consumer — Akien at triage (offload-more vs pull-back is his call)

WHAT THE POPULATION IS, AND WHY IT COULD NOT BE INFERRED. "Built through the shim" is not
readable from a verdict artifact: an artifact records that a ticket reached a verdict, never
who moved the code. So the shim STAMPS it — every recorded ask carries the ticket it was
made for (fence.SeenLog.record's `ticket`, added in the same voyage as this probe, for this
reason) — and a shimmed ticket is one that appears in the ask log AND has a standing verdict
artifact. The alternative was inferring shimmed-ness from timestamps, which is a proxy that
goes wrong the first time two voyages overlap, and goes wrong SILENTLY.

THE HOLE IS CARRIED VISIBLY, NOT OMITTED. The carrier asks for two numbers per ticket and
only one of them has an instrument today. "Did it pass unchanged physics" is read straight
off the verdict artifact's criteria. "CC call count vs the direct-build baseline" is not
counted by anything — /sail step 9 says so in as many words ("nothing counts the calls,
nothing observes them"), and the observer is ticket
`the-builds-tool-calls-are-evidence-about-the-chart`. So the carrier renders that column as
an explicit hole per ticket, following `probe.as_a_path`'s precedent of rendering a missing
link visibly rather than dropping the key: a receiver that gets a row with one column
missing knows what it is missing; a receiver that gets a row with one column absent thinks
the row is complete.

AND THAT HOLE IS WHY `enough` DEMANDS BOTH. A stopping condition that could be satisfied by
the half we can already measure would retire this watch at the exact moment it had learned
the less interesting half — the apprentice's builds pass, but nobody knows whether they
COST less, which is the whole question the offload was made to answer. So `enough` waits for
the column, and `horizon` is what makes the waiting loud instead of patient: a probe armed
and never firing is this design's own named failure mode, and the honest place for "the
instrument does not exist yet" is a horizon that runs out, not an `enough` that quietly
lowers the bar.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

from cairn.tools.base.probe import Probe

TICKET = "aider-shim"

#: Instance-space, and the same path fence.DEFAULT_RECORD writes. Imported rather than
#: re-spelled would be better, and is not possible without dragging the fence's whole
#: import into a module the emission gate loads to READ — so it is asserted against the
#: fence by this device's proof instead, which is where a two-spellings drift gets caught.
ASK_LOG = Path.home() / ".cairn" / "devices" / "aider_shim" / "0" / "asks.jsonl"

#: Where verdict artifacts berth. The resolver below is composed, never re-derived.
_VERDICT_STAGE = "verdict"


def shimmed_tickets(*, ask_log: Path | None = None) -> list[str]:
    """Tickets this device actually built for, oldest first, deduplicated.

    Reads only ALLOWED asks: a ticket whose every ask was refused was never built through
    the shim — the fence stopped it — and counting it would inflate the population with
    exactly the runs that produced no work.
    """
    path = Path(ask_log) if ask_log is not None else ASK_LOG
    if not path.exists():
        return []
    seen: list[str] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError:
            continue  # a torn line names no ticket; the log's own owner carries that finding
        t = row.get("ticket") or ""
        if t and row.get("verdict") == "allowed" and t not in seen:
            seen.append(t)
    return seen


def _artifact_for(ticket: str, *, berths_root=None):
    from cairn.devices.builder.machines.verdict.verdict import (  # noqa: PLC0415
        latest_claiming_artifact,
    )
    return latest_claiming_artifact(ticket, berths_root=berths_root)


def yields_so_far(*, ask_log: Path | None = None, berths_root=None) -> list[dict]:
    """One row per shimmed ticket that has reached a standing verdict artifact.

    THE TWO COLUMNS THE CARRIER ASKS FOR, and the second one is a declared hole. `passed`
    is measured — every criterion's outcome, read off the artifact. `cc_calls` is
    `None` with `cc_calls_hole` naming why, per the header.
    """
    rows = []
    for ticket in shimmed_tickets(ask_log=ask_log):
        found = _artifact_for(ticket, berths_root=berths_root)
        if not found:
            continue
        path, artifact = found
        criteria = artifact.get("criteria") or []
        outcomes = [c.get("outcome") for c in criteria]
        rows.append({
            "ticket": ticket,
            "verdict_berth": path,
            "criteria": len(criteria),
            "passed": bool(criteria) and all(o == "passed" for o in outcomes),
            "outcomes": outcomes,
            "cc_calls": None,
            "cc_calls_hole": "no instrument counts CC's tool calls yet (/sail step 9 is a "
                             "hand's act); ticket "
                             "the-builds-tool-calls-are-evidence-about-the-chart owns it",
        })
    return rows


def _trigger(now=None, context=None) -> bool:
    """True when a shimmed ticket has reached a verdict artifact it had not reached before.

    NOT A POLL, and the distinction survives the fact that this reads the disk: the probe is
    evaluated on the beat that was already going to happen, and what it asks is whether the
    exit gate's deposit — an event that fires whether or not anyone is watching — has left a
    new artifact behind. The count rides `context` so the shim's own memory holds the state
    (a Probe is frozen and holds none), and the anti-bounce default means a standing
    population pokes once, at the crossing.
    """
    context = context or {}
    rows = yields_so_far(ask_log=context.get("ask_log"),
                         berths_root=context.get("berths_root"))
    return len(rows) > int(context.get("seen", 0))


def _carry(context=None) -> dict:
    context = context or {}
    rows = yields_so_far(ask_log=context.get("ask_log"),
                         berths_root=context.get("berths_root"))
    return {
        "ticket": TICKET,
        "shimmed": len(rows),
        "green": sum(1 for r in rows if r["passed"]),
        "rows": rows,
        "asks": str(ASK_LOG),
        "reads": "green-rate is measured; the CC-call comparison is a declared hole per row",
    }


def _enough(context=None) -> bool:
    """Five shimmed tickets with BOTH columns recorded — the spec's words, unlowered.

    The `cc_calls is not None` clause is the one that will hold this open, and that is
    deliberate: see the header. When the counter ships, this condition starts being
    satisfiable without a line changing here.
    """
    context = context or {}
    rows = yields_so_far(ask_log=context.get("ask_log"),
                         berths_root=context.get("berths_root"))
    complete = [r for r in rows if r["cc_calls"] is not None]
    return len(complete) >= 5


#: Honest as a placeholder, dishonest as a measurement — the same tracked debt every
#: sibling probe carries: nothing pulses this shim yet, so loudness rides
#: BaseShim.overdue() alone. Re-tune when the beat becomes a real number.
_HORIZON = 1000

PROBE = Probe(
    why="does offloading a build to the apprentice actually yield? The shim can be built, "
        "proved and sealed and still be a net loss — if every shimmed ticket costs CC as "
        "many calls to supervise as it would have cost to build, the offload bought "
        "nothing, and nothing in the system would say so. This watch counts the tickets "
        "that went through the shim, reads whether each passed the UNCHANGED physics, and "
        "carries the cost column as a visible hole until something counts it.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "offload-yield", "ticket": TICKET,
          "consumer": "Akien at triage — offload-more vs pull-back is his call"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)
