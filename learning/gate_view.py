#!/usr/bin/env python3
"""gate_view — the compiled per-gate projection of the learning store.

Casts one rung of horizon-of-awareness into code: fold-the-settled (Law 1).
Reads the raw, append-only records (the cold / L3 layer) and folds them by GATE
into a compiled view (the warm / L2 layer) — so recall can surface one gate's
evidence on demand instead of the whole scroll (sparse-on-demand: the finite
context window is spent on the relevant gate, not the corpus).

Pure projection, zero-inference: the output is a deterministic fold of records/,
the same shape as cairnmap over charters. Provable by inspection — run it and the
view is exactly the records grouped by gate. No tester needed for that claim.

Usage:
    gate_view.py            # every gate, most-evidence-first
    gate_view.py <gate>     # one gate's compiled view (sparse recall)
"""
import json
import sys
from pathlib import Path

# cairn/learning/gate_view.py -> the repo root is three parents up; the store's
# raw records live under the sibling CairnCommons root (code reads knowledge).
ROOT = Path(__file__).resolve().parents[2]
RECORDS = ROOT / "CairnCommons" / "learning" / "records"


def load_records():
    out = []
    for path in sorted(RECORDS.glob("*.json")):
        doc = json.loads(path.read_text())
        out.extend(doc.get("records", []))
    return out


def has_ceiling(rec):
    # v0 heuristic: the ceiling guardrail is read from prose. RUNG 3 makes it a
    # structured field — a never-auto-open guardrail must be physics, not a
    # substring match (Law 4). Flagged here so recall can't misread it as open.
    return "ceiling" in rec.get("confidence_move", "").lower()


def fold(records):
    gates = {}
    for rec in records:
        gates.setdefault(rec["gate"], []).append(rec)
    for recs in gates.values():
        recs.sort(key=lambda r: r["id"], reverse=True)  # newest first
    return gates


def render(gates, only=None):
    # most-evidence-first: the gates CC has learned the most about lead.
    order = sorted(gates, key=lambda g: (-len(gates[g]), g))
    for gate in order:
        if only and gate != only:
            continue
        recs = gates[gate]
        flag = "  ⚠ never-auto-opens (ceiling)" if any(map(has_ceiling, recs)) else ""
        plural = "s" if len(recs) != 1 else ""
        print(f"gate: {gate}  [{len(recs)} record{plural}]{flag}")
        for r in recs:
            print(f"  {r['date']}  {r['evidence']:<12}  {r.get('note', '').strip()}")
        print()


if __name__ == "__main__":
    only = sys.argv[1] if len(sys.argv) > 1 else None
    gates = fold(load_records())
    if only and only not in gates:
        print(f"no records for gate: {only}", file=sys.stderr)
        print(f"known gates: {', '.join(sorted(gates))}", file=sys.stderr)
        sys.exit(1)
    render(gates, only)
