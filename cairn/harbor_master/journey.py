"""harbor_master/journey.py — the JOURNEY VIEW: the TRAFFIC IMAGE, state-right-now.

harbor_master child c — the last rung; the parent PROVES when this lands. It is the
harbour master's main view (the VTS *traffic image* — state as it is this instant, not
motion) rendered as DATA for the web_server's journey pane (web-server child d). Design
consolidated in CairnCommons/notes/held-traffic-image.json; this file builds the honest,
non-hollow SLICE of that design whose facts exist on disk TODAY, and files the rest as
grow-against-need (below) rather than emitting a marker no boat can yet wear (Law 8).

It composes the fleet REGISTER (child a) into two derived, computed-on-read structures:

  1. THE EMERGENT GATE. A gate is not infrastructure — its occupancy is the SUM of the
     IN-FLIGHT boats (open tickets) sitting at one transition-class. Many workflows share
     one gate at once (BUILDME holds every boat mid-build). So the gates are just the open
     boats GROUPED BY STANDING — emergent, not declared (held-traffic-image: the_gate).

  2. THE JOURNEY STITCH. An open ticket and its berthed history are TWO VANTAGES of one
     voyage. They differ only by id-spelling — a ticket is hyphenated (``harbor-master``),
     its berth is underscored (``harbor_master``) — so the register's ``find`` misses the
     join (register filed-edge e). This module NORMALISES that (``_canon``) and stitches the
     vantages under one voyage, which is what lets the view show a boat that is at sea AND
     already docked: MID-JOURNEY, its migration unreconciled (register filed-edge c).

THE ONE HONEST FLAG (today). The design's marker vocabulary ([R] requested, [W] waiting,
[F] failed, [X] refused, [S] stalled) mostly needs an OWNED FACT that does not exist yet —
the gate's queue (requests/refusals/dwell), a subscription registry (staff/starvation), a
'waiting_on' record. Emitting those markers now would be hollow (Law 8: a marker no boat can
wear). The single condition that is STRUCTURAL and computed-on-read TODAY is MID-JOURNEY: a
boat showing in BOTH lanes (open + in-port). It is the honest instance of the design's
"silently stuck" — a boat that has arrived but never left the sea (its ticket outlived its
berth) — the very thing the broad view earns its keep by surfacing. So the view carries
exactly two conditions now: ``underway`` (the calm default) and ``mid-journey`` (the flag).
The rest are FILED, each with the owned fact it waits on (see ``GROW_AGAINST_NEED`` below).

OWNS NOTHING (Law 7). Like ``render`` and like ``state.json`` to ``history``, the traffic
image is a PRESENTATION-grade projection: every field it carries is READ from the register
(itself an index over the boats' own records), never invented. Computed on read, never
stored — it cannot drift from the fleet it shows. The proof pins this: each occupant's
standing/source is byte-equal to its register entry.

CALM WHEN HEALTHY (held-traffic-image: markers_are_primitive_sublists_are_rendering). A gate
reports its ``underway`` as a COUNT and its ``flagged`` as a LIST — healthy is a number, a
boat needing an eye is a line you can read. The grouping is derived, not stored (Law 1).

Deliberately dependency-light: the register + pure grouping. Runs bare.

    python3 -m cairn.harbor_master.journey        # prints the traffic image as a human summary
"""

from __future__ import annotations

from cairn.harbor_master import register


# What the traffic image will grow to carry, each gated on an OWNED FACT that does not
# exist yet — filed here (not emitted) so the view never wears a marker no boat can (Law 8).
# When the fact acquires an owner, the marker grafts into ``_condition`` below, one at a time.
GROW_AGAINST_NEED = {
    "[R] requested": "the clearance REQUEST must leave a trace owned by the gate's queue "
                     "(clearance today writes nothing until it grants) — held-traffic-image IOU",
    "[X] refused": "a REFUSAL must be journaled by the gate's queue, distinct from the boat's "
                   "successful-crossing history (an illegal move must never look like it happened)",
    "[W] waiting-on": "needs a 'waiting_on' owned fact (a question record / pending decision); "
                      "the ticket's prose waits_on is narrative, not a clean party to render",
    "[F] failed": "needs a boat to carry a red/failed standing; no in-flight boat wears one today",
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


def _condition(open_boat: dict, vantages: list[dict]) -> tuple[str, str]:
    """The boat's condition + its marker, computed on read (no store). Today: MID-JOURNEY
    (the boat also has an in-port vantage — arrived yet still at sea, the honest silently-stuck)
    or UNDERWAY (the calm default). The rest of the vocabulary is FILED (``GROW_AGAINST_NEED``)
    until its owned fact exists — a marker no boat can wear would be hollow (Law 8)."""
    if any(v["berth"] == "in_port" for v in vantages):
        return "mid-journey", "[~]"     # at sea AND docked — migration unreconciled (the flag)
    return "underway", ""               # cleared and moving — the happy path


def traffic_image(reg: dict | None = None) -> dict:
    """Compile the TRAFFIC IMAGE — state-right-now, as DATA. A pure projection over the
    register (child a); computed on read, never stored, so it cannot drift (Law 7).

    Returns ``{gates, docked, counts}``:
      - ``gates``   — the IN-FLIGHT (open) boats grouped by standing (the emergent gate). Each
                      ``{gate, occupants, underway, flagged}``: ``underway`` a COUNT (calm),
                      ``flagged`` the LIST of boats needing an eye (calm-when-healthy).
      - ``docked``  — boats berthed with NO open vantage (arrived, off the gates); the quiet
                      background of the harbour, carried as a list.
      - ``counts``  — in_flight / gates / flagged / docked / fleet.
    Each occupant is the register's own open-boat entry, plus the derived ``gate`` (its
    standing), ``condition`` + ``marker``, and its stitched ``vantages`` — nothing invented.
    """
    reg = reg or register.register()
    voyages = _vantages_by_voyage(reg)

    # docked = a voyage whose ONLY vantage is in-port (arrived, no open ticket at a gate).
    open_canons = {_canon(b["id"]) for b in reg["open"]}
    docked = [b for b in reg["in_port"] if _canon(b["id"]) not in open_canons]

    # the emergent gates: open boats grouped by standing (the transition-class they share).
    gates: dict[str, list[dict]] = {}
    for b in reg["open"]:
        vantages = voyages[_canon(b["id"])]
        condition, marker = _condition(b, vantages)
        occupant = dict(b)                       # the register's own entry, read (Law 7) ...
        occupant["gate"] = b["standing"]         # ... plus the derived gate (its standing) ...
        occupant["condition"] = condition        # ... its condition + marker ...
        occupant["marker"] = marker
        occupant["vantages"] = vantages          # ... and its stitched two-vantage voyage.
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
    return {
        "gates": gate_list,
        "docked": sorted(docked, key=lambda o: o["id"]),
        "counts": {
            "in_flight": len(reg["open"]),
            "gates": len(gate_list),
            "flagged": flagged_total,
            "docked": len(docked),
            "fleet": reg["counts"]["fleet"],
        },
    }


def journey_of(reg: dict, boat_id: str) -> dict:
    """One boat's whole voyage, vantages STITCHED — the single-boat view under the traffic
    image. Normalises the id (``harbor-master`` joins ``harbor_master``) so a boat mid-journey
    returns BOTH its open ticket and its berthed history under one voyage (the join the
    register's literal ``find`` leaves open, register filed-edge e). ``mid_journey`` is True
    when both vantages are present."""
    canon = _canon(boat_id)
    vantages = _vantages_by_voyage(reg).get(canon, [])
    berths = {v["berth"] for v in vantages}
    return {
        "voyage": canon,
        "vantages": vantages,
        "mid_journey": "open" in berths and "in_port" in berths,
    }


def _main() -> int:
    img = traffic_image()
    c = img["counts"]
    print(f"TRAFFIC IMAGE — {c['in_flight']} in flight across {c['gates']} gates "
          f"({c['flagged']} flagged), {c['docked']} docked\n")
    for g in img["gates"]:
        flags = "".join(f" {o['marker']}{o['id']}" for o in g["flagged"])
        tail = f"  ⚑{flags}" if g["flagged"] else ""
        print(f"  {g['gate']:12} {g['underway']} underway, {len(g['flagged'])} flagged{tail}")
    print(f"\n  docked (arrived, off the gates): {c['docked']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
