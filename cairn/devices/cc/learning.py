"""cc/learning.py — instance-local learning store for CC gate-preference records.

Write/read primitives at ~/.cairn/devices/cc/0/learning/. Each record ties to a
gate and carries decision, signal, evidence, confidence_move — the v0 fields from
CairnCommons/learning/README.md. One file per record, named by id.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_ROOT = Path.home() / ".cairn" / "devices" / "cc" / "0" / "learning"

SIGNALS = {
    "confirmation": ("confirmation", "+ slow (confirmed prediction; the denominator grows)"),
    "correction": ("correction", "- fast (counter-evidence; asymmetric by design)"),
    "weak": ("weak", "~ negligible (silence is not approval)"),
}


def write_record(
    *,
    gate: str,
    decision: str,
    signal: str,
    verbatim: str,
    session: str = "",
    note: str = "",
    ceiling: bool = False,
    root: Path | str | None = None,
) -> dict:
    """Write one gate-record to the instance store. Returns the record."""
    if not gate or not isinstance(gate, str):
        raise ValueError("gate must be a non-empty string")
    if signal not in SIGNALS:
        raise ValueError(f"signal {signal!r} not in {tuple(SIGNALS)}")

    now = datetime.now(timezone.utc)
    evidence, confidence_move = SIGNALS[signal]
    record = {
        "id": f"cc-{now.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
        "date": now.date().isoformat(),
        "session": session,
        "gate": gate,
        "decision": decision,
        "signal": {"kind": signal, "verbatim": verbatim},
        "evidence": evidence,
        "ceiling": ceiling,
        "confidence_move": confidence_move,
        "note": note or f"cc learning record for gate {gate}",
        "provenance": "cairn.devices.cc.learning.write_record",
    }

    store = Path(root) if root else _DEFAULT_ROOT
    store.mkdir(parents=True, exist_ok=True)
    path = store / f"{record['id']}.json"
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    return record


def read_records(
    *,
    gate: str | None = None,
    root: Path | str | None = None,
) -> list[dict]:
    """Read records from the instance store, optionally filtered by gate."""
    store = Path(root) if root else _DEFAULT_ROOT
    if not store.is_dir():
        return []
    records = []
    for p in sorted(store.glob("cc-*.json")):
        try:
            rec = json.loads(p.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        if gate is None or rec.get("gate") == gate:
            records.append(rec)
    return records
