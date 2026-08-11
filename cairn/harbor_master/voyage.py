"""harbor_master/voyage.py — the VOYAGE VIEW: the TRAFFIC IMAGE, state-right-now.

harbor_master child c — the last rung; the parent PROVES when this lands. It is the
harbour master's main view (the VTS *traffic image* — state as it is this instant, not
motion) rendered as DATA for the web_server's voyage pane (web-server child d). Design
consolidated in CairnCommons/notes/held-traffic-image.json; this file builds the honest,
non-hollow SLICE of that design whose facts exist on disk TODAY, and files the rest as
grow-against-need (below) rather than emitting a marker no boat can yet wear (Law 8).

It composes the fleet REGISTER (child a) into two derived, computed-on-read structures:

  1. THE EMERGENT GATE. A gate is not infrastructure — its occupancy is the SUM of the
     AT-SEA boats (open tickets) sitting at one transition-class. Many workflows share
     one gate at once (BUILDME holds every boat mid-build). So the gates are just the open
     boats GROUPED BY STANDING — emergent, not declared (held-traffic-image: the_gate).

  2. THE VOYAGE STITCH. An open ticket and its berthed history are TWO VANTAGES of one
     voyage. They differ only by id-spelling — a ticket is hyphenated (``harbor-master``),
     its berth is underscored (``harbor_master``) — so the register's ``find`` misses the
     join (register filed-edge e). This module NORMALISES that (``_canon``) and stitches the
     vantages under one voyage, which is what lets the view show a boat that is at sea AND
     already berthed: MID-VOYAGE, its migration unreconciled (register filed-edge c).

THE HONEST CONDITIONS (today), each computed-on-read from a fact on disk. The design's marker
vocabulary ([R] requested, [W] waiting, [F] failed, [X] refused, [S] stalled) mostly needs an
OWNED FACT that does not exist yet — a subscription registry (staff/starvation), a 'waiting_on'
record — so emitting it now would be hollow (Law 8: a marker no boat can wear). THE GATE'S QUEUE
IS NO LONGER ONE OF THE MISSING FACTS: it was built 2026-08-10 (ticket clearance-leaves-a-trace)
and every clearance attempt, granted or refused, is on disk with its actor, its boat, its target
and its reason. What each of the two queue-gated markers still needs is stated at its own entry
below rather than here, because the two turned out to need different things. Two conditions ARE
structural today:

  • AT-ANCHOR ([✓]). A boat sitting in the open lane whose cursor is at a REST stage
    (PROVED) is not at sea — it is DONE, awaiting its berth: the physical migration beside
    code that the auto-berther (register filed-edge c) will do. Read straight off the cursor the
    register already parses (Law 1 — the done-ness is IN the cursor; the image compiles it, it is
    not re-derived). These boats leave the at-sea count and the gates entirely: PROVED is a
    rest, not a gate where work waits. This is the interim honest count until the auto-berther
    physically berths them (which must first de-brittle the proofs that pin the live fleet).

  • MID-VOYAGE ([~]). A boat in BOTH lanes (open + in-port) while STILL IN WORKFLOW (cursor not
    yet at rest) — arrived yet unreconciled, the honest "silently stuck" the broad view earns its
    keep by surfacing. Reading the cursor SHARPENS this: a both-lanes boat at PROVED is berth-
    pending (done, park it), NOT stuck; the [~] alarm is reserved for one that has NOT finished.

So three conditions in all — ``at-anchor`` (done), ``mid-voyage`` (stuck), ``underway``
(the calm default). The rest are FILED, each with the owned fact it waits on (``GROW_AGAINST_NEED``).

OWNS NOTHING (Law 7). Like ``render`` and like ``state.json`` to ``history``, the traffic
image is a PRESENTATION-grade projection: every field it carries is READ from the register
(itself an index over the boats' own records), never invented. Computed on read, never
stored — it cannot drift from the fleet it shows. The proof pins this: each occupant's
standing/source is byte-equal to its register entry.

CALM WHEN HEALTHY (held-traffic-image: markers_are_primitive_sublists_are_rendering). A gate
reports its ``underway`` as a COUNT and its ``flagged`` as a LIST — healthy is a number, a
boat needing an eye is a line you can read. The grouping is derived, not stored (Law 1).

Deliberately dependency-light: the register + pure grouping. Runs bare.

    python3 -m cairn.harbor_master.voyage        # prints the traffic image as a human summary
"""

from __future__ import annotations

from cairn.harbor_master import register


# What the traffic image will grow to carry, each gated on an OWNED FACT that does not
# exist yet — filed here (not emitted) so the view never wears a marker no boat can (Law 8).
# When the fact acquires an owner, the marker grafts into ``_condition`` below, one at a time.
GROW_AGAINST_NEED = {
    # THE QUEUE EXISTS NOW (cairn/harbor_master/clearance.py, ticket clearance-leaves-a-trace,
    # 2026-08-10): both of these were filed as waiting on it, and neither still is. What each
    # waits on now is a DIFFERENT thing, and saying "the queue" for both would go on hiding that.
    "[R] requested": "NOT the queue any more — the queue records attempts, and this marker "
                     "presumes DWELL: a request that is outstanding, sitting somewhere between "
                     "asking and being answered. The gate is synchronous (clear() decides and "
                     "returns or raises), so there is no pending state for a boat to be IN and "
                     "nothing to render. This marker needs an asynchronous clearance — or it "
                     "should be retired. It is not waiting on data; it is waiting on a design "
                     "question nobody has asked yet",
    "[X] refused": "the fact is THERE (clearance.read_attempts() carries every refusal with its "
                   "boat, actor, target and reason); what is missing is STILL-refused. A boat "
                   "whose attempt was refused once and then cleared is not flagged, it is moving "
                   "— so the predicate is 'refused since its last journaled crossing', and a "
                   "marker without it would pin itself on the first refusal and never clear, "
                   "which is the flag that fires on normal motion. Grow it against a real "
                   "refusal: the live queue holds none yet, and the shape of the first one is "
                   "what should decide whether the flag belongs on the boat or on the actor",
    "[W] waiting-on": "needs a 'waiting_on' owned fact (a question record / pending decision); "
                      "the ticket's prose waits_on is narrative, not a clean party to render",
    "[F] failed": "needs a boat to carry a red/failed standing; no at-sea boat wears one today",
    "[S] starvation": "the GATE-level stall — a gate with boats and no qualified subscriber — "
                      "needs the subscription registry (staff) + the latching-alarm primitive",
}


def _canon(boat_id: str) -> str:
    """The canonical voyage key: a ticket's hyphenated id and its berth's underscored dir name
    are one voyage (``harbor-master`` == ``harbor_master``). Normalise to join them — the
    stitch the register's literal ``find`` leaves open (register filed-edge e)."""
    return boat_id.replace("-", "_")


def _vantages_by_voyage(reg: dict) -> dict:
    """Map each canonical voyage -> the list of its vantages (open ticket, berthed history,
    or both), each a thin READ of the register's own boat entry (owns nothing, Law 7)."""
    voyages: dict[str, list[dict]] = {}
    for b in reg["fleet"]:
        voyages.setdefault(_canon(b["id"]), []).append(
            {"berth": b["berth"], "standing": b["standing"], "source": b["source"], "id": b["id"]}
        )
    return voyages


# The formal REST stages — a cursor here means the workflow is DONE, not voyaging. ``PROVED``
# is the code-seam rest and the concept-piece rest both; other classes' rests graft here as a
# fleet grows to hold them (grow-against-need — not guessed ahead of a boat that wears one).
REST_STANDINGS = {"PROVED"}


def _condition(open_boat: dict, vantages: list[dict]) -> tuple[str, str]:
    """The boat's condition + its marker, computed on read (no store). Three conditions today:
    AT-ANCHOR (the cursor is at a REST stage — done, awaiting its berth), MID-VOYAGE (still
    in workflow yet also holding an in-port vantage — arrived-but-unreconciled, the silently-stuck),
    or UNDERWAY (the calm default). At-anchor is read FIRST: a done boat that also has a berth
    is 'park it', not 'stuck' — the cursor sharpens the flag. The rest of the vocabulary is FILED
    (``GROW_AGAINST_NEED``) until its owned fact exists — a marker no boat can wear is hollow (Law 8)."""
    if open_boat["standing"] in REST_STANDINGS:
        return "at-anchor", "[✓]"   # done at a rest cursor, still in the open lane — awaiting berth
    if any(v["berth"] == "in_port" for v in vantages):
        return "mid-voyage", "[~]"     # at sea AND berthed while STILL in workflow — the silently-stuck
    return "underway", ""               # cleared and moving — the happy path


def traffic_image(reg: dict | None = None) -> dict:
    """Compile the TRAFFIC IMAGE — state-right-now, as DATA. A pure projection over the
    register (child a); computed on read, never stored, so it cannot drift (Law 7).

    Returns ``{gates, at_anchor, berthed, counts}``:
      - ``gates``        — the truly AT-SEA open boats grouped by standing (the emergent gate).
                           Each ``{gate, occupants, underway, flagged}``: ``underway`` a COUNT
                           (calm), ``flagged`` the LIST needing an eye (calm-when-healthy).
      - ``at_anchor``— open boats at a REST cursor (PROVED): DONE, awaiting berth. Off the
                           gates and out of the at-sea count — PROVED is a rest, not a gate.
      - ``berthed``       — boats berthed with NO open vantage (arrived, off the gates); the quiet
                           background of the harbour.
      - ``counts``       — at_sea / at_anchor / gates / flagged / berthed / fleet.
    Each occupant/entry is the register's own open-boat entry, plus the derived ``gate`` (its
    standing), ``condition`` + ``marker``, and its stitched ``vantages`` — nothing invented.
    """
    reg = reg or register.register()
    voyages = _vantages_by_voyage(reg)

    # berthed = a voyage whose ONLY vantage is in-port (arrived, no open ticket at a gate).
    open_canons = {_canon(b["id"]) for b in reg["open"]}
    berthed = [b for b in reg["in_port"] if _canon(b["id"]) not in open_canons]

    # classify every open boat, then split: at-anchor (done) leaves the gates; the rest are
    # the emergent gates — the at-sea boats grouped by the standing (transition-class) they share.
    at_anchor: list[dict] = []
    gates: dict[str, list[dict]] = {}
    for b in reg["open"]:
        vantages = voyages[_canon(b["id"])]
        condition, marker = _condition(b, vantages)
        occupant = dict(b)                       # the register's own entry, read (Law 7) ...
        occupant["gate"] = b["standing"]         # ... plus the derived gate (its standing) ...
        occupant["condition"] = condition        # ... its condition + marker ...
        occupant["marker"] = marker
        occupant["vantages"] = vantages          # ... and its stitched two-vantage voyage.
        if condition == "at-anchor":
            at_anchor.append(occupant)       # done — off the gates, awaiting berth
        else:
            gates.setdefault(b["standing"], []).append(occupant)

    gate_list = []
    for gate in sorted(gates):
        occupants = sorted(gates[gate], key=lambda o: o["id"])
        flagged = [o for o in occupants if o["marker"]]
        gate_list.append({
            "gate": gate,
            "occupants": occupants,
            "underway": sum(1 for o in occupants if not o["marker"]),  # the calm COUNT
            "flagged": flagged,                                         # the LIST that needs an eye
        })

    flagged_total = sum(len(g["flagged"]) for g in gate_list)
    at_sea = sum(len(g["occupants"]) for g in gate_list)
    return {
        "gates": gate_list,
        "at_anchor": sorted(at_anchor, key=lambda o: o["id"]),
        "berthed": sorted(berthed, key=lambda o: o["id"]),
        "counts": {
            "at_sea": at_sea,                   # voyaging boats only (at-anchor excluded)
            "at_anchor": len(at_anchor),
            "gates": len(gate_list),
            "flagged": flagged_total,
            "berthed": len(berthed),
            "fleet": reg["counts"]["fleet"],
        },
    }


def voyage_of(reg: dict, boat_id: str) -> dict:
    """One boat's whole voyage, vantages STITCHED — the single-boat view under the traffic
    image. Normalises the id (``harbor-master`` joins ``harbor_master``) so a boat mid-voyage
    returns BOTH its open ticket and its berthed history under one voyage (the join the
    register's literal ``find`` leaves open, register filed-edge e). ``mid_voyage`` is True
    when both vantages are present; ``at_anchor`` is True when the open vantage's cursor is
    at a REST stage (done, awaiting berth) — the same cursor read the traffic image classifies by."""
    canon = _canon(boat_id)
    vantages = _vantages_by_voyage(reg).get(canon, [])
    berths = {v["berth"] for v in vantages}
    open_v = next((v for v in vantages if v["berth"] == "open"), None)
    return {
        "voyage": canon,
        "vantages": vantages,
        "mid_voyage": "open" in berths and "in_port" in berths,
        "at_anchor": bool(open_v and open_v["standing"] in REST_STANDINGS),
    }


def _main() -> int:
    img = traffic_image()
    c = img["counts"]
    print(f"TRAFFIC IMAGE — {c['at_sea']} at sea across {c['gates']} gates "
          f"({c['flagged']} flagged), {c['at_anchor']} at-anchor, {c['berthed']} berthed\n")
    for g in img["gates"]:
        flags = "".join(f" {o['marker']}{o['id']}" for o in g["flagged"])
        tail = f"  ⚑{flags}" if g["flagged"] else ""
        print(f"  {g['gate']:12} {g['underway']} underway, {len(g['flagged'])} flagged{tail}")
    if img["at_anchor"]:
        names = ", ".join(o["id"] for o in img["at_anchor"])
        print(f"\n  at-anchor (done, awaiting berth): {c['at_anchor']}  ✓ {names}")
    print(f"  berthed (arrived, off the gates): {c['berthed']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
