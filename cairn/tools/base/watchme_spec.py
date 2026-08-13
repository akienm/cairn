"""base/watchme_spec.py — the WATCHME spec, made machine-readable.

Ticket ``watchme-emits-a-probe`` piece (c-ii), 2026-07-30. Being in the workflow is what
OBLIGES the ticket to specify, at ticketing, everything needed to emit the probe: how it
accumulates (``trigger``), when it clears (``enough``), what rides back (``carrier``), where
that lands (``nexus``), and who consumes it. Akien's rule, in one line:

    OPTIONAL TO CARRY, MANDATORY TO SATISFY ONCE CARRIED.
    "none, because X" is the only other legal answer; silence is not.

THE MEASURED VOID THIS FILLS. Before this module the ONLY ticket check in the system was
``cairn.machines.chart.orient.ticket_claim_error``, and it never opens the ticket — it asks whether a
file of that name exists. So no rule about a ticket's CONTENTS had anywhere to run. The
five fields would have been prose on a ticket schema, which is exactly the shape the whole
node is paying off: a falsifier field written on every ticket since the beginning, never
fired, never measured.

WHY THE OBJECT IS THE JOIN KEY. A free summons may repeat, so ``WATCHME(a) -> WATCHME(b)``
is two obligations and needs two specs. They are matched by the object named IN THE WORKFLOW
STRING — the record of truth — so a spec cannot drift onto a watch the node does not carry,
and a watch cannot be carried with no spec behind it. Both directions are checked; one
direction would let the pair rot in the unchecked half.

WHY SOME TICKETS ARE EXEMPT BY A STATED RULE, not by luck. There are two exemptions and
they are ONE rule: the obligation attaches at TICKETING, to a version the ticketer composed
whose vocabulary contains WATCHME.
  - ``@v1`` — the registered vocabulary contains no WATCHME at all, so the obligation cannot
    attach. A consequence of the version the string claims, not a grandfather list.
  - ``migrated_from`` present — the version claim was applied TO the ticket by a sweep, not
    composed by its ticketer, so nobody was ever asked the question. Akien's ruling of
    2026-08-03 is the authority: "a workflow is composed at ticketing time by the ticketer
    based on the needs of the ticket."
Both exist for the same reason, and it is the promotion-filter jurisdiction failure the
entry-gate stone already paid for once: A CHECK THAT RETRO-REDS EVERY OPEN BOAT IS A CHECK
THAT GETS DISABLED. Measured twice now — the second time on 2026-08-03, when the scrub sweep
retagged 50 cast tickets to v2 in one act and this rule redded all 50.

STILL AN IOU AT ONE END, and it is named rather than papered over: CASTING HAS NO
CHOKEPOINT. ``/sorted`` files a ticket by writing a file; nothing refuses the write. So this
module is the RULE in machine-readable form plus a runnable sweep, and it becomes physics
where a door already opens the ticket — the WATCHME emission gate (piece c-i). Until casting
itself rides a door, "the spec is required AT TICKETING" is enforced one step late, and Law
4 says that makes it a tracked debt, not a resting state.

    python3 cairn/tools/base/proofs/test_watchme_spec.py          # exit 0 = green
    python3 -m cairn.tools.base.watchme_spec                      # sweep every filed ticket
"""

from __future__ import annotations

import json
import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
_TICKETS = _REPO_ROOT.parent / "CairnCommons" / "tickets"

# Akien's five, in his order. ``enough`` is spelled as the Probe field is spelled
# (cairn/tools/base/probe.py) on purpose: know the primitive, know the spec — nobody should have to
# memorise a mapping between the thing and its description.
REQUIRED_FIELDS = ("trigger", "enough", "carrier", "nexus", "consumer")

# The berth of the probe this spec compiles to. Not one of Akien's five — it is what makes
# the emission gate answerable from a PATH rather than from a live device registry, which is
# the load-bearing bound of the whole split (a registry is out of this ticket's constrain).
BERTH_FIELD = "probe"

_NONE_RE = re.compile(r"^none,\s*because\s+\S+", re.IGNORECASE)


class WatchmeSpecRed(ValueError):
    """A ticket's WATCHME spec is missing, incomplete, or does not match the watches its
    workflow string actually carries. Loud and complete on the first pass (Law 7): the
    message names every fault, so no one has to re-run the check to find the next one."""


def workflow_objects(workflow_str: str) -> list[str | None]:
    """The objects of every WATCHME the string carries, in order. Parses through the
    chokepoint's own parser so this module cannot develop a second opinion about what a
    workflow string says (Law 1 — one implementation of a settled question)."""
    from cairn.tools.base.transitions import parse_workflow
    wf = parse_workflow(workflow_str)
    return [wf.objects[i] if i < len(wf.objects) else None
            for i, s in enumerate(wf.path) if s == "WATCHME"]


def _version_of(workflow_str: str) -> str:
    from cairn.tools.base.transitions import parse_workflow
    return parse_workflow(workflow_str).version


def watchme_spec_error(ticket: dict) -> str | None:
    """The rule. Returns the refusal text, or None when the ticket satisfies it.

    THREE OUTCOMES, and the middle one is the whole point:
      - the string carries no WATCHME and the class version cannot carry one (v1) -> exempt,
        by the stated version rule.
      - the string carries no WATCHME and its version COULD -> the ticket must record
        ``"watchme": "none, because X"``. Silence is refused; that is the difference between
        an author who considered efficacy and one who skipped the question.
      - the string carries watches -> one complete spec per watch, joined by object.
    """
    state = ticket.get("state")
    if not isinstance(state, str) or not state.strip():
        return None                       # see below — no string, no claimed version, no obligation
    try:
        objects = workflow_objects(state)
        version = _version_of(state)
    except Exception:  # noqa: BLE001
        # NOT THIS MODULE'S VERDICT TO GIVE (Law 6 — the parser owns parse). Measured on the
        # first sweep: three v0 tickets from 2026-07-15/16 (cc-learning-store,
        # learning-as-a-pattern, default-superclaude-to-200k) carry a bare word — 'building',
        # 'validated' — because they predate workflow strings entirely. Redding them here is
        # exactly the retro-red this piece's falsifier names, and it would be a SECOND opinion
        # about malformedness besides: the chokepoint already refuses an unparseable string
        # loudly at every crossing, so nothing hides. The stated rule, one rung below the v1
        # rule: THE OBLIGATION ATTACHES TO A CLAIMED VERSION WHOSE VOCABULARY CONTAINS WATCHME.
        # A state that names no version claims none, so nothing attaches.
        return None

    declared = ticket.get("watchme")

    if not objects:
        if version == "v1":
            return None          # the vocabulary has no WATCHME — the obligation cannot attach
        if ticket.get("migrated_from"):
            # A SWEPT VERSION CLAIM IS NOT AN AUTHORED ONE — the second stated rule, added
            # 2026-08-03 with Akien's scrub sweep, and it is the same rule as the v1 one, not
            # a second mechanism. The obligation attaches AT TICKETING, where an author is
            # present to answer "does this intention need a watch?". A ticket carrying
            # `migrated_from` had its version claim applied TO it by a sweep; nobody was asked.
            # Akien's own ruling the same day settles which it is: "a workflow is composed at
            # ticketing time by the ticketer based on the needs of the ticket" — so a string
            # the ticketer did not compose carries no ticketing-time obligation.
            #
            # THIS LOSES NO ENFORCEMENT. It is the static corpus scan that stands down, not a
            # gate: a swept ticket carries no WATCHME (that is what the sweep did), and the
            # crossing-time gate (transitions._emission_gate) only fires on a string that DOES
            # carry one. The moment an author edits this string to carry a watch, the watch is
            # authored and every check below applies in full.
            #
            # Without this rule the 2026-08-03 sweep retro-redded 50 cast tickets at once —
            # exactly "a check that retro-reds every open boat is a check that gets disabled",
            # which this module's own header names as the failure it was built to avoid.
            return None
        if isinstance(declared, str) and _NONE_RE.match(declared.strip()):
            return None
        return ("workflow claims %s and carries no WATCHME, so the ticket must record "
                "watchme: \"none, because <reason>\" — silence is not one of the two legal "
                "answers (found: %r)" % (version, declared))

    specs = declared if isinstance(declared, list) else ([declared] if declared else [])
    faults: list[str] = []

    by_object: dict[str, dict] = {}
    for i, spec in enumerate(specs):
        if not isinstance(spec, dict):
            faults.append("watchme[%d] is %s, not a spec object" % (i, type(spec).__name__))
            continue
        obj = spec.get("object")
        if not isinstance(obj, str) or not obj.strip():
            faults.append("watchme[%d] names no object — the object is the join key to the "
                          "watch it describes, so a spec without one describes nothing" % i)
            continue
        if obj in by_object:
            faults.append("two specs claim object %r — a watch has exactly one spec" % obj)
            continue
        by_object[obj] = spec

    for obj in objects:
        spec = by_object.pop(obj, None)
        if spec is None:
            faults.append("WATCHME(%s) is carried by the workflow with NO spec — mandatory to "
                          "satisfy once carried" % obj)
            continue
        missing = [f for f in REQUIRED_FIELDS
                   if not (isinstance(spec.get(f), str) and spec[f].strip())]
        if missing:
            faults.append("WATCHME(%s) spec is missing %s (the five are %s)"
                          % (obj, ", ".join(missing), ", ".join(REQUIRED_FIELDS)))
        berth = spec.get(BERTH_FIELD)
        if not (isinstance(berth, str) and berth.strip()):
            faults.append("WATCHME(%s) spec names no %r — the emission gate resolves ARMED "
                          "from a path, so a spec with no berth cannot be gated"
                          % (obj, BERTH_FIELD))

    for orphan in by_object:
        faults.append("a spec claims object %r, which no WATCHME in the workflow carries — a "
                      "spec cannot drift onto a watch the node does not have" % orphan)

    if faults:
        return "; ".join(faults)
    return None


def spec_for(ticket: dict, obj: str) -> dict | None:
    """The one spec on this ticket that describes the watch named ``obj``, or None."""
    declared = ticket.get("watchme")
    specs = declared if isinstance(declared, list) else ([declared] if declared else [])
    for spec in specs:
        if isinstance(spec, dict) and spec.get("object") == obj:
            return spec
    return None


def armed_error(spec: dict, *, root: Path | str = _REPO_ROOT) -> str | None:
    """IS THE PROBE THIS SPEC PROMISED ACTUALLY ARMED? Returns the refusal text, or None.

    ARMED IS MEASURED, NOT ASSERTED (Law 3). A path that exists is not a probe; a module that
    imports is not an emitter. So all three are checked and every fault is reported together
    (Law 7 — complete on the first pass, never re-run the gate to find the next fault):

      1. the berth is on disk and imports,
      2. it declares module-level ``PROBE``, a real ``cairn.tools.base.probe.Probe``,
      3. that Probe can EMIT and can STOP — it carries a ``carry`` and an ``enough``.

    WHY (3) IS PART OF ARMED, and not a nicety. "Emission, not accumulation" is the ticket's
    own phrase for the failure this gate exists to stop. A probe with no carrier pokes to say
    only THAT a line was crossed — nothing is gathered, so the efficacy question the WATCHME
    was carried for cannot be answered by it. A probe with no ``enough`` can never clear,
    which is the standing pulse-cost the shrinking-footprint discipline refuses. The spec
    PROMISED both fields at ticketing; this is where the promise is measured against the code.

    WHY A PATH AND NOT A REGISTRY. Deliberate and bounded: asking a live device roster "is
    this probe armed?" would make the chokepoint reach outward at a crossing, and a registry
    is explicitly OUT of this ticket's constrain. A berth is a file in class-space, so ARMED
    answers from the same repo the crossing is journaled in — no device, no bus, no network.
    Importing a declaration module IS the measurement, and a probe berth is a declaration by
    construction (see probe.py's header).
    """
    import importlib.util

    from cairn.tools.base.probe import Probe

    berth = spec.get(BERTH_FIELD)
    if not (isinstance(berth, str) and berth.strip()):
        return "the spec names no %r berth, so ARMED cannot be measured at all" % BERTH_FIELD
    p = Path(berth)
    if not p.is_absolute():
        p = Path(root) / berth
    if not p.is_file():
        return ("no probe is berthed at %s — the ticket promised one at %r and the world does "
                "not hold it (done is verified in the world, never in the record)" % (p, berth))

    try:
        mod_spec = importlib.util.spec_from_file_location(f"_probe_berth_{p.stem}", p)
        module = importlib.util.module_from_spec(mod_spec)
        mod_spec.loader.exec_module(module)
    except Exception as exc:  # noqa: BLE001 — a berth that cannot load is not armed
        return "the berth at %s does not load (%s: %s)" % (p, type(exc).__name__, exc)

    probe = getattr(module, "PROBE", None)
    if probe is None:
        return ("the berth at %s declares no module-level PROBE — a probe berth is a "
                "DECLARATION module, and the gate reads the declaration rather than running "
                "construction logic it cannot predict" % p)
    if not isinstance(probe, Probe):
        return ("the berth at %s declares PROBE as %s, not a cairn.tools.base.probe.Probe"
                % (p, type(probe).__name__))

    faults = []
    if probe.carry is None:
        faults.append("it carries no `carry`, so its poke says only THAT a line was crossed — "
                      "nothing is gathered, which is exactly the accumulation-without-emission "
                      "shape this gate refuses")
    if probe.enough is None:
        faults.append("it declares no `enough`, so the watch can never clear — the spec "
                      "promised an enough-condition at ticketing")
    if faults:
        return "the probe at %s is berthed but not armed: %s" % (p, "; and ".join(faults))
    return None


def require_watchme_spec(ticket: dict) -> None:
    """The refusing face, for a caller that wants the raise rather than the text."""
    err = watchme_spec_error(ticket)
    if err:
        raise WatchmeSpecRed(err)


def sweep(tickets_dir: Path | str = _TICKETS) -> list[dict]:
    """Run the rule across every filed ticket. The instrument the ticketing rule is measured
    by — and the row that answers the falsifier this piece was most likely to fail: a check
    that RETRO-REDS pre-existing cast tickets is a check that gets turned off."""
    out = []
    for p in sorted(Path(tickets_dir).glob("*.json")):
        if p.name.startswith("_"):
            continue                      # the schema charter, not a ticket
        try:
            t = json.loads(p.read_text(encoding="utf-8"))
        except Exception as exc:  # noqa: BLE001
            out.append({"ticket": p.stem, "error": f"unreadable: {exc}"})
            continue
        out.append({"ticket": p.stem, "error": watchme_spec_error(t)})
    return out


if __name__ == "__main__":
    rows = sweep()
    red = [r for r in rows if r["error"]]
    for r in red:
        print(f"  RED  {r['ticket']}: {r['error']}")
    print(f"\n{len(rows) - len(red)}/{len(rows)} filed tickets satisfy the WATCHME rule")
