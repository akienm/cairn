"""Proof for ticket e8fb6bcd23c5 — a chart berth that claims a ticket is readable from every box.

Measured 2026-11-12: a chart chain berths in instance-space (``~/.cairn/devices/chart/0/packets``),
so a hollow, verdict or chain read on a box other than the one that charted the ticket found
every stage None. The /intent and /sorted berths already travel through the commons
(``<commons>/berths/<skill>/``, ticket d692ef650534); the chart's did not.

1. clause_1_a_claiming_berth_is_carried_byte_identical: each of the eight stage writers, given a
   packet that names a ticket, leaves ``<commons>/berths/chart/<name>`` byte-identical to the
   berth it wrote;
2. clause_2_an_unclaimed_berth_is_not_carried: a packet naming no ticket is not carried, while a
   claiming one written by the same writer in the same run is;
3. clause_3_chain_for_ticket_reads_the_mirror: chain_for_ticket over a default store that lacks
   the berth finds it at its commons address;
4. clause_4_a_berth_in_both_places_is_indexed_once_locally: a berth present in the local store
   and the mirror is indexed once, at the local path.

The writers' own judges are stubbed for the run (they gate packet SHAPE, which this ticket does
not touch; their proofs stand beside them); the default store is repointed by
``chain.BERTHS_ROOT`` and the commons by ``artifact.set_diagnostic_roots``, both restored in
``finally``. Every subject is bound at tooth time.

Run bare:  PYTHONPATH=. python3 cairn/tools/chain/proofs/test_a_claiming_chart_berth_is_read_from_every_box.py
"""
from __future__ import annotations

import importlib
import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "e8fb6bcd23c5": {
        "1": "clause_1_a_claiming_berth_is_carried_byte_identical",
        "2": "clause_2_an_unclaimed_berth_is_not_carried",
        "3": "clause_3_chain_for_ticket_reads_the_mirror",
        "4": "clause_4_a_berth_in_both_places_is_indexed_once_locally",
    },
}

FAILURES: list[str] = []
TICKET = "e8fb0000a001"
# stage -> (module, writer, the judges the writer calls before it lands the file)
WRITERS = {
    "orient": ("orient", "write_packet", ("validate_orient",)),
    "constrain": ("constrain", "write_constrain", ("validate_constrain",)),
    "survey": ("survey", "write_survey", ("validate_survey",)),
    "decompose": ("decompose", "write_decompose", ("validate_decompose",)),
    "triage": ("triage", "write_triage", ("validate_triage",)),
    "hypothesize": ("hypothesize", "write_hypothesize", ("validate_hypothesize",)),
    "validate": ("validate", "write_validate", ("validate_validate",)),
    "verdict": ("verdict", "write_verdict", ("validate_verdict", "observe_instruments")),
}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:800]}")
    if not ok:
        FAILURES.append(name)


def _stub(value):
    return lambda *a, **k: value


def _write(stage: str, packet: dict, packets: Path) -> str:
    mod_name, writer, judges = WRITERS[stage]
    mod = importlib.import_module(f"cairn.devices.codemother.machines.{mod_name}.{mod_name}")
    saved = {j: getattr(mod, j) for j in judges}
    try:
        for j in judges:
            setattr(mod, j, _stub([] if j == "observe_instruments" else {}))
        return getattr(mod, writer)(packet, instance_dir=str(packets), root=str(REPO))
    finally:
        for j, fn in saved.items():
            setattr(mod, j, fn)


def tooth_1(packets: Path, mirror: Path) -> None:
    name = PROVES["e8fb6bcd23c5"]["1"]
    try:
        wrong = []
        for stage in WRITERS:
            p = Path(_write(stage, {"ticket": TICKET, "fixture": f"tooth 1 {stage}"}, packets))
            m = mirror / p.name
            if not m.is_file() or m.read_bytes() != p.read_bytes():
                wrong.append(f"{stage}: wrote {p.name}, mirror has it={m.is_file()}")
        check(name, not wrong, "; ".join(wrong) or "all eight writers carried their berth")
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2(packets: Path, mirror: Path) -> None:
    name = PROVES["e8fb6bcd23c5"]["2"]
    try:
        claimed = Path(_write("orient", {"ticket": TICKET, "fixture": "tooth 2 claimed"}, packets))
        unclaimed = Path(_write("orient", {"fixture": "tooth 2 unclaimed"}, packets))
        ok = (mirror / claimed.name).is_file() and not (mirror / unclaimed.name).exists()
        check(name, ok, f"claimed carried={(mirror / claimed.name).is_file()} "
                        f"unclaimed carried={(mirror / unclaimed.name).exists()}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_3(mirror: Path) -> None:
    name = PROVES["e8fb6bcd23c5"]["3"]
    try:
        from cairn.tools.chain import chain
        only = mirror / "survey-20261112T000003-e8fb00000003.json"
        only.write_text(json.dumps({"ticket": "e8fb0000c003"}), encoding="utf-8")
        got = chain.chain_for_ticket("e8fb0000c003")
        check(name, got.get("survey") == str(only), f"chain={got}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_4(packets: Path, mirror: Path) -> None:
    name = PROVES["e8fb6bcd23c5"]["4"]
    try:
        from cairn.tools.chain import chain
        base = "triage-20261112T000004-e8fb00000004.json"
        body = json.dumps({"ticket": "e8fb0000d004"})
        (packets / base).write_text(body, encoding="utf-8")
        (mirror / base).write_text(body, encoding="utf-8")
        got = chain.claiming_packet_paths("e8fb0000d004", "triage")
        check(name, got == [str(packets / base)], f"indexed={got}")
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    from cairn.tools.artifact import artifact as A
    from cairn.tools.chain import chain
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-e8fb6bcd23c5-chart-mirror-")
    store = tmp / "chart"
    packets = store / "0" / "packets"
    packets.mkdir(parents=True)
    commons = tmp / "CairnCommons"
    mirror = commons / "berths" / "chart"
    mirror.mkdir(parents=True)
    saved_root = chain.BERTHS_ROOT
    chain.BERTHS_ROOT = os.path.realpath(str(store))
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
    try:
        tooth_1(packets, mirror)
        tooth_2(packets, mirror)
        tooth_3(mirror)
        tooth_4(packets, mirror)
    finally:
        A.set_diagnostic_roots(None)
        chain.BERTHS_ROOT = saved_root
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
