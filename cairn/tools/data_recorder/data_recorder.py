"""data_recorder — a mailbox that holds structured feedback until an LLM reads it.

A TOOL (Law 6): users, not an owner. Probes write to it; scheduled-llm-gate-inspection
reads from it. The tool gates no writes at its own address — gating is the holder's act.

Three operations, one JSONL file per inspector:
  write(record)       — append one structured JSON record
  read()              — return all accumulated records
  clear(ids)          — remove consumed records by id

Storage: JSONL under the holder's instance-space path, at
``~/.cairn/devices/<device>/<instance>/tools/data_recorder/<inspector_name>/records.jsonl``
per ruling 2026-08-14-tools-and-machines-remember-under-their-holder.

JSONL so appending is atomic and reading is streaming. No database — this is a flat-file
tool, not relational state.
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path


RECORDS_FILE = "records.jsonl"

REQUIRED_KEYS = ("finding", "inspector_target", "probe_source", "timestamp")


class DataRecorder:
    """Accumulate-and-clear mailbox for structured feedback records.

    Construction touches no disk — the directory is made at the first write.
    """

    def __init__(self, base_dir: str | Path) -> None:
        self._dir = Path(base_dir)
        self._path = self._dir / RECORDS_FILE

    @property
    def path(self) -> Path:
        return self._path

    def write(self, record: dict) -> str:
        """Append one record. Returns the assigned id.

        The record must carry at least the REQUIRED_KEYS. A ``timestamp`` field
        is added if missing; an ``id`` is always assigned (uuid4).
        """
        if not isinstance(record, dict):
            raise TypeError("record must be a dict, got %s" % type(record).__name__)
        missing = [k for k in REQUIRED_KEYS if k not in record or k == "timestamp"]
        non_ts_missing = [k for k in REQUIRED_KEYS if k != "timestamp" and k not in record]
        if non_ts_missing:
            raise ValueError("record missing required keys: %s" % ", ".join(non_ts_missing))

        entry = dict(record)
        entry["id"] = str(uuid.uuid4())
        if "timestamp" not in entry or not entry["timestamp"]:
            entry["timestamp"] = datetime.now(timezone.utc).isoformat()

        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")

        return entry["id"]

    def read(self) -> list[dict]:
        """Return all accumulated records, in write order.

        An absent file is an empty list, not an error — nothing has been written yet.
        """
        if not self._path.is_file():
            return []
        out = []
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            out.append(json.loads(line))
        return out

    def clear(self, ids: list[str]) -> int:
        """Remove records by id. Returns the count of records removed.

        Rewrites the file without the named ids. If all records are cleared,
        the file is removed.
        """
        if not isinstance(ids, list) or not ids:
            return 0
        if not self._path.is_file():
            return 0

        id_set = set(ids)
        kept = []
        removed = 0
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("id") in id_set:
                removed += 1
            else:
                kept.append(line)

        if not kept:
            self._path.unlink(missing_ok=True)
        else:
            self._path.write_text("\n".join(kept) + "\n", encoding="utf-8")

        return removed
