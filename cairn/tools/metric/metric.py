"""metric — records a measurement of anything (outline 17.27).

A TOOL (Law 6): users, not an owner. A metric is a primitive whose job is to measure whatever
it is, and like feedback (which a metric strictly is) it must have a consumer (17.27).

  record   — a Metric records into its HOLDER's data recorder (17.27.1): no bus, no database.
             A name the recording component's charter does not declare, with a consumer, is
             refused (17.27.4) and nothing is written.
  take     — hands what waits in a holder's recorder to a sink as rows in the table's shape
             (COLUMNS, 17.27.2), and clears them only once the sink has returned. The read is
             the event (17.27.3): nothing polls. A sink that raises leaves every record in place.

The charter declares each name as ``"metrics": {"<name>": {"consumer": "<who reads it>",
"unit": "<unit>"}}``. The table itself is its holder's to create and own (5.3.6); this tool
only says what a row is.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.diagnostic import DiagnosticBase
from cairn.tools.data_recorder.data_recorder import DataRecorder

RECORDER = "metrics"
# HYPOTHESIS: a day. Nothing has measured how often a metrics report is asked for; the
# first consumer (the yield report, 11.4.4.2) sets the real number. Declared, because an
# undeclared read frequency is red (cairn/tools/data_recorder).
READ_FREQUENCY_SECONDS = 86400

# The one table's row (17.27.2). Fields not relevant to a source stay blank (None).
COLUMNS = {
    "at": "timestamptz NOT NULL",
    "name": "text NOT NULL",
    "source": "text NOT NULL",
    "start": "timestamptz",
    "end": "timestamptz",
    "value": "double precision",
    "unit": "text",
    "subject": "text",
    "info": "jsonb",
}


class UndeclaredMetric(ValueError):
    """A metric name its recording component's charter does not declare with a consumer."""


def recorder(holder_dir: str | Path) -> DataRecorder:
    """The holder's metrics recorder: ``<holder>/tools/data_recorder/metrics/``."""
    return DataRecorder(Path(holder_dir) / "tools" / "data_recorder" / RECORDER,
                        expected_read_frequency_seconds=READ_FREQUENCY_SECONDS, on_read="drain")


def declared(charter_path: str | Path) -> dict:
    """The charter's ``metrics`` declaration: name -> {consumer, unit}. Absent is empty."""
    charter = json.loads(Path(charter_path).read_text(encoding="utf-8"))
    out = charter.get("metrics") or {}
    if not isinstance(out, dict):
        raise UndeclaredMetric(f"{charter_path}: 'metrics' is not a name -> {{consumer, unit}} map")
    return out


class Metric(DiagnosticBase):
    """Records measurements for one source into its holder's recorder."""

    def __init__(self, holder_dir: str | Path, charter_path: str | Path, *, source: str) -> None:
        super().__init__()
        if not source or not str(source).strip():
            raise ValueError("a metric needs a source: the device or tool that records it")
        self._recorder = recorder(holder_dir)
        self._charter = Path(charter_path)
        self._source = source

    def record(self, name: str, value: float | None = None, *, unit: str | None = None,
               subject: str | None = None, start: str | None = None, end: str | None = None,
               info: dict | None = None, at: str | None = None) -> str:
        """Record one measurement; returns the record id. Refuses an undeclared name."""
        spec = declared(self._charter).get(name)
        if not isinstance(spec, dict) or not str(spec.get("consumer") or "").strip():
            raise UndeclaredMetric(
                f"metric {name!r} is not declared with a consumer in {self._charter} "
                "(outline 17.27.4: a name with no consumer is a red)")
        if info is not None:
            json.dumps(info)  # an info that cannot be stored as json is refused here, loudly
        return self._recorder.write({
            "finding": name,
            "inspector_target": RECORDER,
            "probe_source": self._source,
            "at": at or datetime.now(timezone.utc).isoformat(),
            "start": start,
            "end": end,
            "value": value,
            "unit": unit if unit is not None else spec.get("unit"),
            "subject": subject,
            "info": info,
        })


def _row(record: dict) -> dict:
    return {
        "at": record.get("at") or record.get("timestamp"),
        "name": record["finding"],
        "source": record["probe_source"],
        "start": record.get("start"),
        "end": record.get("end"),
        "value": record.get("value"),
        "unit": record.get("unit"),
        "subject": record.get("subject"),
        "info": record.get("info"),
    }


def take(holder_dir: str | Path, sink) -> int:
    """Hand every waiting record to ``sink(rows)`` and clear them once it returns.

    Each row carries exactly the COLUMNS keys. If ``sink`` raises, nothing is cleared and the
    exception propagates (Law 7). Returns the count handed over."""
    rec = recorder(holder_dir)
    records = rec.read()
    if not records:
        rec.stamp_read([])
        return 0
    sink([_row(r) for r in records])
    rec.stamp_read([r["id"] for r in records])
    return len(records)
