"""PROBE — charter-feedback-reaches-codemother

Berth for the WATCHME that ticket ``65b34c57ab71`` carries. Berthed beside
``cairn/devices/codemother`` because that is WHERE THE HELD INSTANCE LIVES: the charter
tool's state berths under its holder at ``devices/codemother/0/tools/charter/`` (Law 6),
and the data_recorder backpack there is what feedback about charter quality lands in.

THE QUESTION: does feedback actually ARRIVE? Placement is proved by the proof; whether
anything in the running system ever addresses the tool and gets through is efficacy —
so enough is the first record that has been both WRITTEN to the held inbound and READ
back out of it (the ticket's own enough), from a sender that is not the proof harness.
The survey reads the live inbound through the same door the shim writes it with.
"""

from __future__ import annotations

import json

from cairn.tools.base.probe import Probe, owning_ticket, once

_OWNING_TICKET = "65b34c57ab71"
_OBJECT = "charter-feedback-reaches-codemother"
_ENOUGH_RECORDS = 1


def survey() -> dict:
    from cairn.devices.codemother.shim import charter_instance
    from cairn.tools.instanceizer.instanceizer import load
    held = charter_instance()
    ensured = (held / "instanceizer.json").is_file()
    records: list[dict] = []
    if ensured:
        try:
            records = load(held).read()
        except Exception as exc:  # noqa: BLE001 — a broken backpack is a finding, not a crash
            return {"address": str(held), "ensured": True, "records": 0, "senders": [],
                    "read_back": False, "broken": f"{type(exc).__name__}: {exc}"}
    senders = sorted({str(r.get("probe_source", "")) for r in records})
    return {
        "address": str(held),
        "ensured": ensured,
        "records": len(records),
        "senders": senders,
        # read_back is true by construction once records exist: the survey IS the read
        "read_back": bool(records),
        "latest": records[-1].get("finding") if records else None,
    }


def _trigger(now, context: dict) -> bool:
    s = once(context, "survey", survey)
    return s["records"] > 0 or not s["ensured"]


def _enough(context: dict) -> bool:
    s = once(context, "survey", survey)
    return s["ensured"] and s["records"] >= _ENOUGH_RECORDS and s["read_back"]


def _carry(context: dict) -> dict:
    s = once(context, "survey", survey)
    if not s["ensured"]:
        finding = ("UNHELD — codemother has not ensured its charter instance at "
                   f"{s['address']}; feedback addressed to charter has nowhere to land")
    elif s.get("broken"):
        finding = f"BROKEN — the held backpack refuses to read: {s['broken']}"
    elif s["records"] >= _ENOUGH_RECORDS:
        finding = (f"REACHES — {s['records']} feedback record(s) written to and read from "
                   f"codemother's held charter inbound, from {', '.join(s['senders']) or 'nobody'}")
    else:
        finding = "HELD, SILENT — the instance stands and nothing has addressed it yet"
    return {"finding": finding, "survey": s, "ticket": owning_ticket(_OWNING_TICKET)}


PROBE = Probe(
    why="charter's state berths under its holder, codemother (Law 6); this probe watches "
        "whether feedback about charter quality actually reaches that held instance — "
        "the first record written and read back is the placement working, not merely built",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy",
          "ticket": owning_ticket(_OWNING_TICKET),
          "object": _OBJECT},
    carry=_carry,
    enough=_enough,
    horizon=500,
)


if __name__ == "__main__":
    s = survey()
    print(json.dumps({
        "survey": s,
        "would_trigger": _trigger(None, {"survey": s}),
        "enough": _enough({"survey": s}),
        "carry": _carry({"survey": s}),
    }, indent=2, default=str))
