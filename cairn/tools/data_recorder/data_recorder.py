"""data_recorder — a mailbox that holds structured feedback until an LLM reads it.

A TOOL (Law 6): users, not an owner. Probes write to it; scheduled-llm-gate-inspection
reads from it. The tool gates no writes at its own address — gating is the holder's act.

Four operations, one JSONL file per inspector:
  write(record)       — append one structured JSON record
  read()              — return all accumulated records
  clear(ids)          — remove consumed records by id
  stamp_read(ids)     — say the mailbox was read; drain the ids or hold them, as declared

AND A SELF-DECLARATION (ticket a4c2be029f49, 2026-09-18). Beside ``records.jsonl`` sits
``reading.json`` — four fields: ``started`` (ISO, stamped on the FIRST write, never at
construction: a constructed-but-never-written recorder has no life to date), ``last_read``
(ISO or null), ``expected_read_frequency_seconds`` (int or null) and ``on_read``
(``drain`` | ``hold``). The two settings come from the HOLDER at construction — the tool
knows nothing about who reads it, and it invents no default: measured at the cast, ten
recorders held 1,817 records and NOTHING had ever read one. The charter's clause 5 ("nobody
reads from it — a mailbox nobody opens is a black hole") was a sentence; the declaration is
what makes it a number an at-rest probe can red on (``probes/reading_is_declared_and_current``).
UNDECLARED IS RED — there is no fallback frequency.

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
READING_FILE = "reading.json"

READING_FIELDS = ("started", "last_read", "expected_read_frequency_seconds", "on_read")
ON_READ = ("drain", "hold")

REQUIRED_KEYS = ("finding", "inspector_target", "probe_source", "timestamp")


class DataRecorder:
    """Accumulate-and-clear mailbox for structured feedback records.

    Construction touches no disk — the directory is made at the first write.
    """

    def __init__(self, base_dir: str | Path, *,
                 expected_read_frequency_seconds: int | None = None,
                 on_read: str | None = None) -> None:
        if on_read is not None and on_read not in ON_READ:
            raise ValueError("on_read is one of %s, got %r" % (ON_READ, on_read))
        if expected_read_frequency_seconds is not None and (
                not isinstance(expected_read_frequency_seconds, int)
                or isinstance(expected_read_frequency_seconds, bool)
                or expected_read_frequency_seconds <= 0):
            raise ValueError("expected_read_frequency_seconds is a positive int or None, got %r"
                             % (expected_read_frequency_seconds,))
        self._dir = Path(base_dir)
        self._path = self._dir / RECORDS_FILE
        self._reading_path = self._dir / READING_FILE
        self._expected_read_frequency_seconds = expected_read_frequency_seconds
        self._on_read = on_read

    @property
    def path(self) -> Path:
        return self._path

    @property
    def reading_path(self) -> Path:
        return self._reading_path

    # --- the self-declaration ------------------------------------------------

    def reading(self) -> dict | None:
        """The four declared fields as they stand on disk, or None before the first write
        or stamp. Reads only — asking a recorder how it is read must not create a
        declaration (the same bound ``address`` keeps)."""
        if not self._reading_path.is_file():
            return None
        return json.loads(self._reading_path.read_text(encoding="utf-8"))

    def _write_reading(self, *, now: datetime, first_write: bool = False,
                       read: bool = False) -> dict:
        """Merge the holder's CURRENT declaration over what stands: ``started`` is set once
        (on the first write) and never moved; ``last_read`` moves only on a stamp; the two
        settings are always the constructor's, so a holder that changes its declaration
        is read as it now declares, not as it once did."""
        standing = self.reading() or {}
        reading = {
            "started": standing.get("started"),
            "last_read": standing.get("last_read"),
            "expected_read_frequency_seconds": self._expected_read_frequency_seconds,
            "on_read": self._on_read,
        }
        if first_write and reading["started"] is None:
            reading["started"] = now.isoformat()
        if read:
            reading["last_read"] = now.isoformat()
        self._dir.mkdir(parents=True, exist_ok=True)
        self._reading_path.write_text(json.dumps(reading, sort_keys=True, indent=2) + "\n",
                                      encoding="utf-8")
        return reading

    def stamp_read(self, ids: list[str] | None = None, *, now: datetime | None = None) -> int:
        """Say the mailbox was read now. Under ``on_read == "drain"`` with ids given, the
        ids are cleared in the same act; under ``hold`` (or with no ids) the records stay
        and only ``last_read`` moves. Returns the count cleared (0 under hold).

        ``now`` is the clock a caller may freeze (the same seam ``emit`` and
        ``raise_trouble`` carry); the default is UTC now."""
        now = now or datetime.now(timezone.utc)
        cleared = 0
        if self._on_read == "drain" and ids:
            cleared = self.clear(list(ids))
        self._write_reading(now=now, read=True)
        return cleared

    def write(self, record: dict, *, now: datetime | None = None) -> str:
        """Append one record. Returns the assigned id.

        The record must carry at least the REQUIRED_KEYS. A ``timestamp`` field
        is added if missing; an ``id`` is always assigned (uuid4). The FIRST write
        also stamps ``started`` on the declaration (``reading.json``); later writes
        leave it where it is. ``now`` freezes the clock for both.
        """
        now = now or datetime.now(timezone.utc)
        if not isinstance(record, dict):
            raise TypeError("record must be a dict, got %s" % type(record).__name__)
        missing = [k for k in REQUIRED_KEYS if k not in record or k == "timestamp"]
        non_ts_missing = [k for k in REQUIRED_KEYS if k != "timestamp" and k not in record]
        if non_ts_missing:
            raise ValueError("record missing required keys: %s" % ", ".join(non_ts_missing))

        entry = dict(record)
        entry["id"] = str(uuid.uuid4())
        if "timestamp" not in entry or not entry["timestamp"]:
            entry["timestamp"] = now.isoformat()

        self._dir.mkdir(parents=True, exist_ok=True)
        with open(self._path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, sort_keys=True) + "\n")
        self._write_reading(now=now, first_write=True)

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
