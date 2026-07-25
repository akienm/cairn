"""Proof: the TRAFFIC IMAGE (harbor_master child c) — the harbour master's state-right-now
view, composed as DATA from the real fleet. The rung the parent PROVES on.

Four claims, each a tooth a hollow view could not pass:

  1. THE EMERGENT GATE. Gates are the in-flight boats grouped by their transition-class —
     emergent, shared by many workflows. Non-hollow floor (Law 8): over the real fleet at
     least one gate must hold MORE THAN ONE occupant (a gate that never shares proves nothing
     about 'the sum of what's on tickets in flight'). Every occupant's gate is exactly its
     own standing (the grouping is honest, not relabelled).

  2. THE JOURNEY STITCH. A boat at sea AND docked joins under one canonical voyage across the
     hyphen/underscore id-spelling (``harbor-master`` == ``harbor_master``). Non-hollow: such
     a mid-journey boat must actually appear AND be flagged — the broad view earning its keep
     by surfacing a boat whose migration is unreconciled (the silently-stuck boon).

  3. OWNS NOTHING (Law 7). Every occupant field is byte-equal to its register entry (standing,
     source) — a projection over an index, inventing nothing. The gates' occupants are exactly
     the open set, none lost or duplicated.

  4. CALM WHEN HEALTHY. Per gate, underway (a COUNT) + flagged (a LIST) partition the occupants
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


def test_the_journey_stitches_across_id_spelling():
    reg = register.register()
    # the reflexive stitch: harbor-master (open ticket) joins harbor_master (berthed history).
    mine = journey.journey_of(reg, "harbor-master")
    assert mine["voyage"] == "harbor_master", "the canonical voyage did not normalise the hyphen"
    assert mine["mid_journey"], (
        "the harbor's own two vantages did not stitch — the open ticket (harbor-master) and the "
        "berthed history (harbor_master) must join under one voyage (register filed-edge e)")
    berths = {v["berth"] for v in mine["vantages"]}
    assert berths == {"open", "in_port"}, f"expected both vantages, got {berths}"
    # non-hollow: a mid-journey boat must actually surface AS A FLAG in the image — the boon.
    img = journey.traffic_image(reg)
    flagged = [o for g in img["gates"] for o in g["flagged"]]
    assert flagged, ("no boat flagged — a green here is hollow: the broad view exists to surface "
                     "the silently-stuck (a boat arrived yet still at sea), and the real fleet has them")
    for o in flagged:
        assert o["condition"] == "mid-journey" and o["marker"] == "[~]", (
            f"{o['id']}: flagged but not the mid-journey condition — the only flag built today")
        assert any(v["berth"] == "in_port" for v in o["vantages"]), (
            f"{o['id']}: flagged mid-journey but carries no in-port vantage — a false flag")
    print(f"    (flagged mid-journey: {', '.join(o['id'] for o in flagged)})")


def test_the_image_owns_nothing():
    reg = register.register()
    img = journey.traffic_image(reg)
    open_by_id = {b["id"]: b for b in reg["open"]}
    occupants = [o for g in img["gates"] for o in g["occupants"]]
    # every occupant field that the register authored is byte-equal to the register's own entry.
    for o in occupants:
        src = open_by_id[o["id"]]
        assert o["standing"] == src["standing"] and o["source"] == src["source"], (
            f"{o['id']}: the image's standing/source diverged from the register — a rival record, "
            f"not a projection (Law 7)")
    # the gates are exactly the open set — none lost, none invented, none duplicated.
    assert sorted(o["id"] for o in occupants) == sorted(b["id"] for b in reg["open"]), (
        "the gates' occupants are not exactly the in-flight (open) boats — a boat was lost or invented")
    # docked = in-port boats with no open vantage; every one is real and off the gates.
    gated_canons = {journey._canon(o["id"]) for o in occupants}
    for d in img["docked"]:
        assert journey._canon(d["id"]) not in gated_canons, (
            f"{d['id']}: listed docked yet also at a gate — a boat double-counted")


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
        test_the_journey_stitches_across_id_spelling,
        test_the_image_owns_nothing,
        test_calm_when_healthy_partition,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the traffic image composes the real fleet into emergent gates (shared, "
          "non-hollow), stitches a boat's two vantages across id-spelling and flags the "
          "silently-stuck (the boon), owns nothing (a projection over the register, Law 7), and "
          "keeps each gate's calm/flagged partition exact — harbor_master child c")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
