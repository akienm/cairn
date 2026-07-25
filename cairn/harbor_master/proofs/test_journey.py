"""Proof: the TRAFFIC IMAGE (harbor_master child c) — the harbour master's state-right-now
view, composed as DATA from the real fleet. The rung the parent PROVES on.

Five claims, each a tooth a hollow view could not pass:

  1. THE EMERGENT GATE. Gates are the in-flight boats grouped by their transition-class —
     emergent, shared by many workflows. Non-hollow floor (Law 8): over the real fleet at
     least one gate must hold MORE THAN ONE occupant (a gate that never shares proves nothing
     about 'the sum of what's on tickets in flight'). Every occupant's gate is exactly its
     own standing (the grouping is honest, not relabelled).

  2. THE JOURNEY STITCH + THE SHARPENED FLAG. A boat at sea AND docked joins under one canonical
     voyage across the hyphen/underscore id-spelling (a ticket ``x-y`` == its berth ``x_y``).
     Non-hollow: such boats must actually appear, and the ones STILL IN WORKFLOW must be flagged
     mid-journey [~] (the silently-stuck boon) — while ones at REST are NOT flagged (the cursor
     sharpens it: done-and-docked is berth-pending, not stuck). Picks its subjects from the live
     fleet, not a pinned id (a proof that names a boat reddens when that boat legitimately moves).

  3. BERTH-PENDING. A boat in the open lane at a REST cursor (PROVED) is DONE, awaiting its berth:
     it leaves the in-flight count and the gates entirely (PROVED is a rest, not a gate). Proven on a
     CONSTRUCTED fleet exercising every branch of the classifier — non-hollow by construction, NOT by
     live migration-debt: once the debt is physically berthed the live fleet holds zero berth-pending
     (the goal, reached 2026-07-24), so a proof that required one would red on a clean fleet. A second
     tooth checks the partition invariant on the real fleet with no such floor.

  4. OWNS NOTHING (Law 7). Every entry field is byte-equal to its register entry (standing, source)
     — a projection over an index, inventing nothing. Gates ∪ berth_pending == the open set exactly,
     disjoint — none lost, invented, or double-bucketed.

  5. CALM WHEN HEALTHY. Per gate, underway (a COUNT) + flagged (a LIST) partition the occupants
     exactly; a boat is flagged iff it wears a marker; a gate with no flagged boats reports an
     empty list, not a hidden one.

Dependency-light: the register + journey.py. Runs bare.

    python3 cairn/harbor_master/proofs/test_journey.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.harbor_master import journey, register


def test_gates_are_emergent_and_shared():
    reg = register.register()
    img = journey.traffic_image(reg)
    assert img["gates"], "no gates — the traffic image found no in-flight boats to compose"
    shared = [g for g in img["gates"] if len(g["occupants"]) > 1]
    assert shared, ("no gate holds more than one boat — a green here is hollow (Law 8): the "
                    "emergent gate is 'the sum of what's on tickets in flight', which a "
                    "one-boat-per-gate fleet never demonstrates")
    for g in img["gates"]:
        for o in g["occupants"]:
            assert o["gate"] == g["gate"] == o["standing"], (
                f"{o['id']}: grouped under gate {g['gate']!r} but its standing is {o['standing']!r} "
                f"— the grouping relabelled a boat (a gate that is not its occupants' transition-class)")
    print(f"    ({len(img['gates'])} gates; shared: "
          f"{', '.join(g['gate'] for g in shared)})")


def test_the_journey_stitches_across_id_spelling_and_the_flag_is_sharpened():
    reg = register.register()
    img = journey.traffic_image(reg)
    # pick the subjects from the LIVE fleet — every boat showing in BOTH lanes — rather than
    # pinning an id: a proof that names a boat reddens the moment that boat legitimately berths
    # (the brittleness we fixed once; see memory proof-over-live-data-assert-invariants).
    both = [b for b in reg["open"] if journey.journey_of(reg, b["id"])["mid_journey"]]
    assert both, ("no boat shows in both lanes — the stitch has nothing to demonstrate; the real "
                  "fleet has berthed boats whose tickets still voyage")
    for b in both:
        j = journey.journey_of(reg, b["id"])
        # the hyphenated ticket id and the underscored berth dir join under one canonical voyage.
        assert j["voyage"] == journey._canon(b["id"]), "the canonical voyage did not normalise the hyphen"
        assert {v["berth"] for v in j["vantages"]} == {"open", "in_port"}, "both vantages must be present"
    # THE SHARPENING (Law 1 — the cursor decides): a both-lanes boat STILL IN WORKFLOW is flagged
    # mid-journey [~] (the silently-stuck boon); one AT REST is berth-pending (done), never flagged.
    flagged = [o for g in img["gates"] for o in g["flagged"]]
    assert flagged, ("no boat flagged mid-journey — a green here is hollow: the broad view exists to "
                     "surface the silently-stuck (arrived yet still in workflow), and the fleet has them")
    for o in flagged:
        assert o["condition"] == "mid-journey" and o["marker"] == "[~]", (
            f"{o['id']}: flagged but not mid-journey — the flag is reserved for in-workflow both-lanes boats")
        assert any(v["berth"] == "in_port" for v in o["vantages"]), (
            f"{o['id']}: flagged mid-journey but carries no in-port vantage — a false flag")
        assert o["standing"] not in journey.REST_STANDINGS, (
            f"{o['id']}: flagged mid-journey but its cursor is at rest — a done boat is berth-pending, not stuck")
    print(f"    (mid-journey flagged: {', '.join(o['id'] for o in flagged)})")


def test_the_image_owns_nothing():
    reg = register.register()
    img = journey.traffic_image(reg)
    open_by_id = {b["id"]: b for b in reg["open"]}
    occupants = [o for g in img["gates"] for o in g["occupants"]]
    entries = occupants + img["berth_pending"]          # every open boat lands in exactly one bucket
    # every entry field that the register authored is byte-equal to the register's own entry.
    for o in entries:
        src = open_by_id[o["id"]]
        assert o["standing"] == src["standing"] and o["source"] == src["source"], (
            f"{o['id']}: the image's standing/source diverged from the register — a rival record, "
            f"not a projection (Law 7)")
    # gates ∪ berth_pending == the open set exactly — none lost, none invented, none duplicated.
    assert sorted(o["id"] for o in entries) == sorted(b["id"] for b in reg["open"]), (
        "gates + berth_pending are not exactly the open boats — a boat was lost or invented")
    assert not ({o["id"] for o in occupants} & {o["id"] for o in img["berth_pending"]}), (
        "a boat is both at a gate and berth-pending — the two buckets are not disjoint")
    # docked = in-port boats with no open vantage; every one is real and off both open buckets.
    open_canons = {journey._canon(o["id"]) for o in entries}
    for d in img["docked"]:
        assert journey._canon(d["id"]) not in open_canons, (
            f"{d['id']}: listed docked yet also in the open lane — a boat double-counted")


def _synthetic_reg() -> dict:
    """A fabricated fleet that exercises every branch of ``journey._condition`` — so berth-pending
    and the cursor-sharpening are proven NON-HOLLOW by construction, independent of what the live
    fleet happens to carry. Once the berth-pending debt is physically berthed the live fleet may hold
    ZERO (that is the goal), and a proof that REQUIRED a berth-pending boat would then red on a CLEAN
    fleet — backwards. The register's own entry shapes are mirrored here (register.py)."""
    open_ = [
        {"id": "syn-proved", "berth": "open", "standing": "PROVED", "node_class": "code-seam",
         "source": "CairnCommons/tickets/syn-proved.json"},
        {"id": "syn-proved-docked", "berth": "open", "standing": "PROVED", "node_class": "code-seam",
         "source": "CairnCommons/tickets/syn-proved-docked.json"},
        {"id": "syn-build", "berth": "open", "standing": "BUILDME", "node_class": "code-seam",
         "source": "CairnCommons/tickets/syn-build.json"},
        {"id": "syn-build-docked", "berth": "open", "standing": "BUILDME", "node_class": "code-seam",
         "source": "CairnCommons/tickets/syn-build-docked.json"},
    ]
    in_port = [  # the two *-docked boats also carry a berthed vantage (id underscored, per _canon)
        {"id": "syn_proved_docked", "berth": "in_port", "standing": "berthed", "gate": "berthed",
         "seq": 1, "source": "cairn/syn_proved_docked/history.json"},
        {"id": "syn_build_docked", "berth": "in_port", "standing": "built", "gate": "built",
         "seq": 1, "source": "cairn/syn_build_docked/history.json"},
    ]
    fleet = open_ + in_port
    return {"open": open_, "in_port": in_port, "fleet": fleet,
            "counts": {"open": len(open_), "in_port": len(in_port), "fleet": len(fleet)}}


def test_berth_pending_and_the_cursor_sharpening_on_a_constructed_fleet():
    """BERTH-PENDING (claim 3) + the cursor SHARPENING, proven on a fabricated fleet exercising every
    branch of the classifier — non-hollow by construction, not by live migration-debt. A PROVED open
    boat is berth-pending [✓] and OFF the gates whether or not it is also docked (the CURSOR decides,
    not the second lane); a BUILDME boat is a gate occupant; a BUILDME boat that is ALSO docked is the
    silently-stuck mid-journey [~]. in_flight counts only the gate occupants, and in_flight +
    berth_pending exhausts the open lane."""
    reg = _synthetic_reg()
    img = journey.traffic_image(reg)
    bp = {o["id"] for o in img["berth_pending"]}
    assert bp == {"syn-proved", "syn-proved-docked"}, (
        f"berth-pending is not exactly the PROVED open boats — the cursor must decide it whether one "
        f"lane or both (a hollow image that read PROVED as a gate would fail here): {bp}")
    for o in img["berth_pending"]:
        assert (o["standing"] in journey.REST_STANDINGS and o["condition"] == "berth-pending"
                and o["marker"] == "[✓]"), f"{o['id']}: wrong condition/marker for a done boat"
    gate_ids = {o["id"] for g in img["gates"] for o in g["occupants"]}
    assert gate_ids == {"syn-build", "syn-build-docked"}, (
        f"gate occupants are not exactly the in-flight boats — a PROVED boat leaked onto a gate: {gate_ids}")
    assert not (bp & gate_ids), "a boat is both berth-pending and at a gate — PROVED is a rest, not a gate"
    flagged = {o["id"] for g in img["gates"] for o in g["flagged"]}
    assert flagged == {"syn-build-docked"}, (
        f"mid-journey [~] is not reserved for the in-workflow both-lanes boat (the PROVED-and-docked "
        f"one must be berth-pending, NOT flagged): {flagged}")
    assert img["counts"]["in_flight"] == len(gate_ids)
    assert img["counts"]["in_flight"] + img["counts"]["berth_pending"] == len(reg["open"])


def test_the_live_fleet_partition_is_exact():
    """On the REAL fleet, with NO floor (the honest count legitimately holds zero berth-pending once
    the debt is physically berthed — 2026-07-24): whatever IS berth-pending is at a rest cursor and
    off the gates, and in_flight + berth_pending exhausts the open lane exactly."""
    reg = register.register()
    img = journey.traffic_image(reg)
    gate_ids = {o["id"] for g in img["gates"] for o in g["occupants"]}
    for o in img["berth_pending"]:
        assert o["standing"] in journey.REST_STANDINGS, (
            f"{o['id']}: berth-pending but its cursor {o['standing']!r} is not a rest")
        assert o["id"] not in gate_ids, f"{o['id']}: berth-pending yet still placed at a gate"
    assert img["counts"]["in_flight"] == len(gate_ids), "in_flight is not exactly the gate occupants"
    assert img["counts"]["in_flight"] + img["counts"]["berth_pending"] == len(reg["open"]), (
        "in_flight + berth_pending must exhaust the open lane — a boat fell out of the count")
    print(f"    (live: {img['counts']['in_flight']} in flight, {img['counts']['berth_pending']} berth-pending)")


def test_calm_when_healthy_partition():
    reg = register.register()
    img = journey.traffic_image(reg)
    for g in img["gates"]:
        marked = [o for o in g["occupants"] if o["marker"]]
        assert g["underway"] == len(g["occupants"]) - len(marked), (
            f"gate {g['gate']}: underway count does not equal occupants minus flagged — the "
            f"calm/flagged split does not partition")
        assert g["flagged"] == marked, (
            f"gate {g['gate']}: the flagged LIST is not exactly the marked boats (a hidden flag)")
        assert g["underway"] + len(g["flagged"]) == len(g["occupants"]), (
            f"gate {g['gate']}: underway + flagged != occupants — a boat fell out of the partition")


def _main() -> int:
    checks = [
        test_gates_are_emergent_and_shared,
        test_the_journey_stitches_across_id_spelling_and_the_flag_is_sharpened,
        test_berth_pending_and_the_cursor_sharpening_on_a_constructed_fleet,
        test_the_live_fleet_partition_is_exact,
        test_the_image_owns_nothing,
        test_calm_when_healthy_partition,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the traffic image composes the real fleet into emergent gates (shared, "
          "non-hollow), stitches a boat's two vantages across id-spelling and flags only the "
          "in-workflow silently-stuck (the cursor sharpens it), sets DONE-but-unberthed boats "
          "apart as berth-pending, owns nothing (a projection over the register, Law 7), and "
          "keeps each gate's calm/flagged partition exact — harbor_master child c")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
