"""At-rest probe: every held data_recorder declares a reader, and the reader is not late.

THE MEASUREMENT THAT BORE IT (ticket a4c2be029f49, 2026-09-18): ten recorders in
instance-space held 1,817 records and NOTHING had ever read one. The charter's clause 5
("nobody reads from it — a mailbox nobody opens is a black hole") was a sentence with no
number under it. The recorder now writes ``reading.json`` beside ``records.jsonl`` —
``started`` (first write), ``last_read``, ``expected_read_frequency_seconds`` and
``on_read`` — and this probe is what turns that declaration into a red on the beat.

Two identities, because "never declared a reader" and "declared one who is late" are
different defects with different fixes (Law 7 — one identity would fold them into a
count nobody can act on):

  recorder-declares-no-reader-<device>-<instance>-<name>   reading.json absent, or
                                                           expected_read_frequency_seconds null
  recorder-read-overdue-<device>-<instance>-<name>         now - (last_read or started)
                                                           > expected_read_frequency_seconds

UNDECLARED IS RED — there is no fallback frequency. The census walks
``address.held_tool_paths("data_recorder")`` (the held part's address IS the declaration;
no registry) one level down to each named recorder, so a holder nobody spelled into a
list is still counted.

The raise sits in the TRIGGER, memoized per beat through ``once``: it runs every beat
whether or not the line crosses, so a standing overdue raises each beat and the trouble
drain folds recurrences on identity (the counting_block pattern). The same pass emits
``reconcile_troubles("recorder-", still)`` so a recorder that gets read CLEARS — the
owner computes the difference; this module reads no store. The raiser is
``ModuleRaiser("data_recorder")``: emissions land under ``instance/logs/data_recorder/0/``
and the trouble shim drains that home like any device's (measured at the cast).

``roots=`` on every judge is the same isolation seam the rest of the base carries — the
proof hands a scratch roots table and never touches the live tree.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.address import held_tool_paths
from cairn.tools.base.diagnostic import ModuleRaiser
from cairn.tools.base.probe import Probe, once

TOOL = "data_recorder"
SCOPE = "recorder-"
NO_READER = "recorder-declares-no-reader"
OVERDUE = "recorder-read-overdue"
READING_FILE = "reading.json"
RECORDS_FILE = "records.jsonl"


def _parse(stamp: str | None) -> datetime | None:
    if not stamp:
        return None
    dt = datetime.fromisoformat(stamp)
    return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)


def _recorders(roots=None) -> list[dict]:
    """Every named recorder under every holder: ``{device, instance, name, dir, reading}``.
    A recorder is a child dir of a held ``tools/data_recorder`` that carries either file."""
    found = []
    for held in held_tool_paths(TOOL, roots):
        device = held.parent.parent.parent.name
        instance = held.parent.parent.name
        for child in sorted(p for p in held.iterdir() if p.is_dir()):
            reading_path = child / READING_FILE
            if not reading_path.is_file() and not (child / RECORDS_FILE).is_file():
                continue
            reading = None
            if reading_path.is_file():
                try:
                    reading = json.loads(reading_path.read_text(encoding="utf-8"))
                except (OSError, ValueError):
                    reading = None
            found.append({"device": device, "instance": instance, "name": child.name,
                          "dir": str(child), "reading": reading})
    return found


def census(now: datetime, *, roots=None) -> dict:
    """The judgement, pure: ``{"recorders": n, "troubles": {identity: detail}, "current": [...]}``.
    Reads reading.json against the clock handed in; raises nothing, writes nothing."""
    troubles: dict[str, dict] = {}
    current: list[str] = []
    recs = _recorders(roots)
    for r in recs:
        tail = "%s-%s-%s" % (r["device"], r["instance"], r["name"])
        reading = r["reading"]
        freq = (reading or {}).get("expected_read_frequency_seconds")
        if reading is None or freq is None:
            troubles["%s-%s" % (NO_READER, tail)] = {
                "dir": r["dir"], "reading": reading,
                "why": "no reading.json" if reading is None
                       else "expected_read_frequency_seconds is null",
            }
            continue
        since = _parse(reading.get("last_read")) or _parse(reading.get("started"))
        if since is None:
            troubles["%s-%s" % (NO_READER, tail)] = {
                "dir": r["dir"], "reading": reading,
                "why": "neither last_read nor started is stamped"}
            continue
        age = (now - since).total_seconds()
        if age > freq:
            troubles["%s-%s" % (OVERDUE, tail)] = {
                "dir": r["dir"], "reading": reading, "age_seconds": int(age),
                "expected_read_frequency_seconds": freq,
                "why": "last read %ds ago against a declared %ds" % (age, freq)}
        else:
            current.append(tail)
    return {"recorders": len(recs), "troubles": troubles, "current": current}


def report(now: datetime, *, roots=None, raiser=None) -> dict:
    """The beat's act: census, raise each trouble through the base, reconcile the scope so
    what is no longer observed clears. Returns the census with ``raised`` beside it."""
    c = census(now, roots=roots)
    raiser = raiser or ModuleRaiser(TOOL, roots=roots)
    for identity, detail in sorted(c["troubles"].items()):
        raiser.raise_trouble(identity, why=detail["why"], detail=detail, now=now)
    raiser.reconcile_troubles(
        SCOPE, sorted(c["troubles"]), by="cc",
        what_changed="the recorder's reading.json now reads current on the beat "
                     "(reading_is_declared_and_current)", now=now)
    c["raised"] = sorted(c["troubles"])
    return c


def _trigger(now, context: dict) -> bool:
    c = once(context, "recorder_reading", lambda: report(now))
    return bool(c["troubles"])


def _carry(context: dict) -> dict:
    c = once(context, "recorder_reading", lambda: report(datetime.now(timezone.utc)))
    return {
        "recorders": c["recorders"],
        "raised": c["raised"],
        "current": c["current"],
        "finding": (
            "%d of %d held data_recorder(s) red — %d declare no reader, %d overdue; each is "
            "a trouble under recorder-* raised from instance/logs/data_recorder/0"
            % (len(c["raised"]), c["recorders"],
               sum(1 for i in c["raised"] if i.startswith(NO_READER)),
               sum(1 for i in c["raised"] if i.startswith(OVERDUE)))
        ) if c["raised"] else (
            "every one of %d held data_recorder(s) declares a reader and was read inside "
            "its declared frequency" % c["recorders"]),
    }


PROBE = Probe(
    why="a recorder nobody reads is a black hole with a charter (clause 5); the declaration "
        "in reading.json is inert until something reads it against a clock on the beat and "
        "raises. Undeclared is red — no default frequency — and a declared reader who is "
        "late is the other red; both clear the beat the recorder is read.",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "at-rest", "scope": SCOPE},
    carry=_carry,
)
