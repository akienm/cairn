"""PROBE — does a ticket wear ONE status everywhere it appears?

Berth for the WATCHME(one-status-everywhere) that ticket 3feb201c84ea
a-ticket-has-one-status-and-one-reader carries. Berthed beside
cairn/tools/operator_inbox because that is WHAT IT WATCHES: the one reader's label,
as printed by the three reports `akienupdate` shows Akien — the operator inbox, the
codemother dashboard, the harbor map.

THE MEASUREMENT. Re-render the three reports through their own modules, read every
ticket atom (date, label, id, title) off the printed text, and diff the label per
ticket id across the reports it appears on. A divergence is one id with two labels
— the defect Akien named 2026-09-06 ("for a given ticket that appers in all the
places, i should see the same status. it has one status.").

TRIGGER: every tester seal of operator_inbox, codemother or harbor_master after the
crossing, and every `akienupdate` run — measured here as: the reports, re-rendered
now, disagree about any id.

ENOUGH: fourteen days after PROVED with zero divergent ids across every run, or the
first run with one — which names the ticket and the two labels and stops.

CARRIER: a verdict artifact against the ticket's falsifier tooth (1): ids seen,
reports each appeared in, tokens per report, divergences.

AUTHORITY: none. This probe deposits and pokes; codemother, as owner of the care of
the code, reads it (Law 6).
"""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "3feb201c84ea"
_ROW = re.compile(r"^\s*(\d{4}-\d{2}-\d{2})\s+(\S+)\s+([0-9a-f]{12})\s+(.*)$")
_HDR = re.compile(r"([A-Z]+(?::[a-z]+)?) \((\d+)\)")
_ENOUGH_DAYS = 14

_first_clean_run: datetime | None = None
_divergence_seen: dict | None = None


def _rows(text: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for line in text.splitlines():
        m = _ROW.match(line)
        if m:
            out[m.group(3)] = m.group(2)
    return out


def _render_three() -> dict[str, str]:
    from cairn.tools.operator_inbox.inbox import build_inbox
    from cairn.devices.codemother.dashboard import format_dashboard
    from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice
    dev = HarborMasterDevice()
    hmap = dev._handle_show({"id": "probe", "sender": "probe", "to": "harbor_master",
                             "verb": "show", "body": {"what": "map", "args": ["open"]}})
    return {"inbox": build_inbox(), "dashboard": format_dashboard(), "map": hmap["text"]}


def _header_counts(inbox_text: str) -> dict[str, int]:
    """The inbox prints its tickets as ONE header line — `LABEL (n) | LABEL (n)` — not
    rows. Its lane in the venn is therefore the per-label count, diffed against the rows
    the other two reports print."""
    for line in inbox_text.splitlines():
        if line.strip().startswith("TICKETS ("):
            return {m.group(1): int(m.group(2)) for m in _HDR.finditer(line)}
    return {}


def _measure() -> dict:
    reports = _render_three()
    per_report = {name: _rows(text) for name, text in reports.items() if name != "inbox"}
    seen: dict[str, dict[str, str]] = {}
    for name, rows in per_report.items():
        for tid, label in rows.items():
            seen.setdefault(tid, {})[name] = label
    divergences = {tid: labels for tid, labels in seen.items() if len(set(labels.values())) != 1}
    header = _header_counts(reports["inbox"])
    counted: dict[str, int] = {}
    for label in per_report["dashboard"].values():
        counted[label] = counted.get(label, 0) + 1
    if header != counted:
        divergences["<inbox header vs dashboard rows>"] = {"inbox": str(header), "dashboard": str(counted)}
    return {
        "ids_seen": len(seen),
        "on_two_or_more": sum(1 for v in seen.values() if len(v) >= 2),
        "per_report_counts": {**{k: len(v) for k, v in per_report.items()}, "inbox_header": header},
        "divergences": divergences,
    }


def _trigger(now, context: dict) -> bool:
    global _divergence_seen
    result = _measure()
    if result["divergences"]:
        _divergence_seen = result["divergences"]
        return True
    return False


def _enough(context: dict) -> bool:
    global _first_clean_run
    if _divergence_seen:
        return True                      # the first divergence names itself and stops
    result = _measure()
    if result["divergences"]:
        return True
    now = datetime.now(timezone.utc)
    if _first_clean_run is None:
        _first_clean_run = now
    return (now - _first_clean_run).days >= _ENOUGH_DAYS


def _carry(context: dict) -> dict:
    result = _measure()
    if result["divergences"]:
        first = next(iter(result["divergences"].items()))
        finding = (f"one ticket, two statuses: {first[0]} wears "
                   + " / ".join(f"{k}={v}" for k, v in first[1].items()))
    else:
        finding = (f"{result['ids_seen']} ids, {result['on_two_or_more']} on two or more "
                   f"reports, every label identical")
    return {
        "finding": finding,
        "measurement": result,
        "ticket": owning_ticket(_OWNING_TICKET),
    }


PROBE = Probe(
    why="a ticket has one status; the three reports are venn diagrams of one reader, "
        "and an id wearing two labels across them is the bug Akien named 2026-09-06",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "codemother", "kind": "efficacy",
          "falsifier_tooth": "3feb201c84ea (1): one id, two labels across the three reports"},
    carry=_carry,
    enough=_enough,
    horizon=500,
)


if __name__ == "__main__":
    print(json.dumps({**_measure(), "would_trigger": bool(_measure()["divergences"])},
                     indent=2, default=str))
