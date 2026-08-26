"""ticket_inspector.inspector — check every ticket for structural completeness.

Two check families, one roster:
  FIELD_PRESENCE  — fields required past a cursor threshold
  CURSOR_GATED    — requirements that activate at specific cursors

Every check returns a list of findings. A finding carries:
  ticket   — the ticket id
  check    — the check name (from the roster)
  finding  — what is wrong, human-readable
  evidence — the raw data
"""

from __future__ import annotations

import json
import os
import re
from pathlib import Path

TICKETS_DIR = Path(os.path.expanduser("~/dev/src/CairnCommons/tickets/"))
CAIRN_ROOT = Path(os.path.expanduser("~/dev/src/cairn"))
COMMONS_ROOT = Path(os.path.expanduser("~/dev/src/CairnCommons"))

CURSOR_ORDER = ("THINKME", "TICKETME", "BUILDME", "PROVEME", "WATCHME", "PROVED")

ROSTER = (
    "required_fields",
    "parseable_state",
    "sorted_berth_present",
    "intent_berth_present",
    "chart_claim_present",
    "gates_defined",
    "node_class_resolves",
    "traces_present",
    "watchme_present",
    "buildme_has_how",
    "children_are_ticket_ids",
    "child_tickets_exist",
    "owning_intention_resolves",
    "state_matches_node_class",
)


def _cursor(state: str) -> str | None:
    m = re.search(r"\[(\w+)\]", state)
    return m.group(1) if m else None


def _past(cursor: str | None, threshold: str) -> bool:
    if cursor is None:
        return False
    try:
        return CURSOR_ORDER.index(cursor) >= CURSOR_ORDER.index(threshold)
    except ValueError:
        return False


def _has_because(val) -> bool:
    return (isinstance(val, str)
            and val.lower().startswith("none")
            and "because" in val.lower())


def inspect_ticket(t: dict) -> list[dict]:
    """Check one ticket dict. Returns findings list (empty = clean)."""
    tid = t.get("id", "?")
    state = t.get("state", "")
    cursor = _cursor(state)
    findings = []

    def finding(check: str, text: str, evidence: dict | None = None):
        findings.append({
            "ticket": tid,
            "check": check,
            "finding": text,
            "evidence": evidence or {},
        })

    # --- REQUIRED FIELDS ---
    for field in ("id", "state", "intention", "why", "falsifier"):
        val = t.get(field)
        if not val or (isinstance(val, str) and not val.strip()):
            finding("required_fields", f"{field} is empty or missing",
                    {"field": field})

    # --- PARSEABLE STATE ---
    if not re.search(r"\w+@v\d+:", state):
        finding("parseable_state",
                f"state does not match <class>@v<N>: pattern",
                {"state": state[:120]})

    # --- SORTED_BERTH (past THINKME) ---
    if _past(cursor, "TICKETME"):
        sb = t.get("sorted_berth", "")
        if not sb:
            finding("sorted_berth_present",
                    "past THINKME but no sorted_berth",
                    {"cursor": cursor})
        elif isinstance(sb, str) and sb.startswith("none") and not _has_because(sb):
            finding("sorted_berth_present",
                    "'none' without a 'because' reason",
                    {"sorted_berth": sb[:120]})

    # --- INTENT_BERTH (past THINKME) ---
    if _past(cursor, "TICKETME"):
        ib = t.get("intent_berth", "")
        if not ib:
            finding("intent_berth_present",
                    "past THINKME but no intent_berth",
                    {"cursor": cursor})
        elif isinstance(ib, str) and ib.startswith("none") and not _has_because(ib):
            finding("intent_berth_present",
                    "'none' without a 'because' reason",
                    {"intent_berth": ib[:120]})

    # --- CHART_CLAIM (past TICKETME) ---
    if _past(cursor, "BUILDME"):
        cc = t.get("chart_claim", "")
        if not cc:
            finding("chart_claim_present",
                    "past TICKETME but no chart_claim",
                    {"cursor": cursor})

    # --- GATES ---
    if not t.get("gates"):
        finding("gates_defined", "no gates defined")

    # --- NODE_CLASS ---
    nc = t.get("node_class", "")
    if not nc:
        finding("node_class_resolves", "no node_class")
    elif isinstance(nc, str):
        nc_clean = nc.split("(")[0].split(" ")[0].strip()
        nc_path = COMMONS_ROOT / "node_classes" / f"{nc_clean}.json"
        if not nc_path.exists():
            finding("node_class_resolves",
                    f"node_class '{nc_clean}' has no file in node_classes/",
                    {"node_class": nc, "tried": str(nc_path)})

    # --- TRACES_TO ---
    if not t.get("traces_to"):
        finding("traces_present", "no traces_to")

    # --- WATCHME ---
    if "WATCHME" in state:
        wm = t.get("watchme")
        if not wm:
            finding("watchme_present",
                    "state string mentions WATCHME but no watchme field")
        elif isinstance(wm, dict):
            for wf in ("object", "trigger", "enough", "carrier", "probe"):
                if not wm.get(wf):
                    finding("watchme_present",
                            f"watchme missing {wf}",
                            {"field": wf})
        elif isinstance(wm, list):
            for i, w in enumerate(wm):
                if isinstance(w, dict):
                    for wf in ("object", "trigger", "enough", "carrier", "probe"):
                        if not w.get(wf):
                            finding("watchme_present",
                                    f"watchme[{i}] missing {wf}",
                                    {"index": i, "field": wf})
        elif isinstance(wm, str) and wm.startswith("none") and not _has_because(wm):
            finding("watchme_present",
                    "'none' without a 'because' reason",
                    {"watchme": str(wm)[:120]})

    # --- BUILDME HAS HOW ---
    if cursor == "BUILDME":
        how = t.get("how", "")
        if not how:
            finding("buildme_has_how",
                    "at BUILDME with no how field",
                    {"cursor": cursor})

    # --- CHILDREN ARE TICKET IDS ---
    children = t.get("children", [])
    if isinstance(children, str) and children.strip() and "none" not in children.lower():
        finding("children_are_ticket_ids",
                "children is prose, not a list",
                {"children": children[:120]})
    elif isinstance(children, list):
        for i, c in enumerate(children):
            if isinstance(c, str) and (len(c) >= 120 or " " in c):
                finding("children_are_ticket_ids",
                        f"child[{i}] is prose, not a ticket id",
                        {"index": i, "child": c[:120]})

    # --- CHILD TICKETS EXIST ---
    if isinstance(children, list):
        for c in children:
            if isinstance(c, str) and len(c) < 120 and " " not in c:
                cpath = TICKETS_DIR / f"{c}.json"
                if not cpath.exists():
                    finding("child_tickets_exist",
                            f"child ticket '{c}' has no file",
                            {"child": c})

    # --- OWNING INTENTION RESOLVES ---
    oi = t.get("owning_intention", "")
    if oi and isinstance(oi, str):
        if oi.startswith("none"):
            pass
        else:
            candidates = [
                CAIRN_ROOT / oi,
                Path(os.path.expanduser("~/dev/src")) / oi,
                COMMONS_ROOT / oi,
            ]
            if not any(p.exists() for p in candidates):
                finding("owning_intention_resolves",
                        f"owning intention path does not resolve: {oi}",
                        {"owning_intention": oi})

    # --- STATE MATCHES NODE_CLASS ---
    if nc and isinstance(nc, str) and re.search(r"\w+@v\d+:", state):
        state_class = state.split("@")[0].strip() if "@" in state else ""
        nc_clean = nc.split("(")[0].split(" ")[0].strip()
        if state_class and nc_clean and state_class != nc_clean:
            finding("state_matches_node_class",
                    f"state class '{state_class}' != node_class '{nc_clean}'",
                    {"state_class": state_class, "node_class": nc_clean})

    return findings


def inspect_corpus(tickets_dir: Path | None = None) -> dict:
    """Inspect all tickets. Returns {tickets_checked, clean, with_findings,
    total_findings, by_check, findings}."""
    tdir = tickets_dir or TICKETS_DIR
    all_findings = []
    checked = 0
    clean = 0

    for f in sorted(tdir.glob("*.json")):
        try:
            t = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        cursor = _cursor(t.get("state", ""))
        if cursor == "PROVED":
            continue
        checked += 1
        ff = inspect_ticket(t)
        if ff:
            all_findings.extend(ff)
        else:
            clean += 1

    by_check = {}
    for f in all_findings:
        by_check.setdefault(f["check"], []).append(f)

    return {
        "tickets_checked": checked,
        "clean": clean,
        "with_findings": checked - clean,
        "total_findings": len(all_findings),
        "by_check": {k: len(v) for k, v in sorted(by_check.items())},
        "findings": all_findings,
    }


if __name__ == "__main__":
    import sys
    result = inspect_corpus()
    print(f"Checked: {result['tickets_checked']}  "
          f"Clean: {result['clean']}  "
          f"Findings: {result['total_findings']}")
    print()
    for check, count in sorted(result["by_check"].items(),
                                key=lambda x: -x[1]):
        print(f"  {check}: {count}")

    if "--detail" in sys.argv:
        print()
        for f in result["findings"]:
            print(f"  [{f['ticket']}] {f['check']}: {f['finding']}")
