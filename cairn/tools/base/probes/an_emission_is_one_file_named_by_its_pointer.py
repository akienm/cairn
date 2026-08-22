"""PROBE — does every emission file hold exactly one record, and is every pointer thin?

Berth for the WATCHME that ticket ``an-emission-is-one-file-named-by-its-pointer`` carries.
Berthed beside ``cairn/tools/base`` because that is WHAT IT WATCHES: ``breadcrumb_log.py``
is the writer, and the one way this design fails silently is a new emit site passing a fat
payload where the pointer should be, or a writer that appends to a file instead of creating
one — the grain the ticket exists to hold.

THE EFFICACY QUESTION: does the grain hold across writers who never read this ticket? The
proof beside the code settles that the shipped writer produces one-file-per-emission on the
day it ships. Whether the NEXT writer carries the grain is a fact about the next writer,
and the ticket's own ``enough`` names that explicitly: "held across at least TWO emitting
components that landed AFTER this ticket."

THREE INVARIANTS MEASURED TOGETHER, because they are one grain seen from three angles:

  (a) ONE FILE, ONE RECORD. The count of ``.json`` trail files in a device's log directory
      equals the count of records those files hold. A file holding two records NAMES that
      file, because "the count is off" is a finding nobody can act on.

  (b) THE POINTER IS THIN. Every emitted pointer is an address (a path, a digest, a short
      id), not a payload smuggled as a pointer. The threshold is 256 chars — well above
      any file path or digest, well below the 1,171-char median canonical text that was
      inference_domain's legacy (now a 64-char digest). An out-of-band pointer NAMES the
      device and the length, because "the median rose" is a finding nobody can act on.

  (c) THE OLD SHAPE IS RECEDING. The count of surviving ``diagnostics.jsonl`` files should
      fall to zero within one retention window; failure to fall is itself a finding, because
      a device still appending to the old shape is a device the new code has not reached.

FILES ONLY, by construction: the probe walks ``~/.cairn/logs/`` — no device, no bus, no
network — so it stays cheap enough to sit on a pulse.

AUTHORITY: none. This probe deposits and pokes; fixing a stopped writer or a fat pointer is
the owner's act at the floor (Law 6).
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base.address import resolve
from cairn.tools.base.breadcrumb_log import RECORD_NAME
from cairn.tools.base.probe import Probe, owning_ticket

_OWNING_TICKET = "an-emission-is-one-file-named-by-its-pointer"

_POINTER_BAND_HIGH = 256
_POINTER_BAND_INFERENCE_LEGACY = 1171


def survey_the_logs_tree(*, roots: dict[str, Path] | None = None) -> dict:
    """Walk every device's log directory and measure the three invariants.

    Returns a dict carrying per-device figures and corpus-level summaries.
    """
    logs_root = resolve("instance/logs", roots)
    if not logs_root.exists():
        return {"devices": {}, "total_files": 0, "total_records": 0,
                "multi_record_files": [], "pointer_distribution": {},
                "surviving_jsonl": 0, "surviving_jsonl_devices": [],
                "hollow": "the logs root does not exist"}

    devices: dict[str, dict] = {}
    total_files = 0
    total_records = 0
    multi_record_files: list[dict] = []
    pointer_distribution: dict[str, dict] = {}
    surviving_jsonl = 0
    surviving_jsonl_devices: list[str] = []

    for device_dir in sorted(logs_root.iterdir()):
        if not device_dir.is_dir():
            continue
        for instance_dir in sorted(device_dir.iterdir()):
            if not instance_dir.is_dir():
                continue
            device_key = f"{device_dir.name}/{instance_dir.name}"

            json_files = sorted(instance_dir.glob("*.json"))
            file_count = len(json_files)
            record_count = 0
            pointer_lengths: list[int] = []

            for jf in json_files:
                try:
                    text = jf.read_text(encoding="utf-8").strip()
                    if not text:
                        continue
                    lines = [ln for ln in text.splitlines() if ln.strip()]
                    n_records = len(lines)
                    record_count += n_records
                    if n_records != 1:
                        multi_record_files.append({
                            "file": str(jf), "records_in_file": n_records,
                            "device": device_key})
                    for ln in lines:
                        rec = json.loads(ln)
                        ptr = rec.get("pointer", "")
                        if ptr:
                            pointer_lengths.append(len(str(ptr)))
                except (ValueError, OSError):
                    multi_record_files.append({
                        "file": str(jf), "records_in_file": "unreadable",
                        "device": device_key})

            has_jsonl = (instance_dir / RECORD_NAME).is_file()
            if has_jsonl:
                surviving_jsonl += 1
                surviving_jsonl_devices.append(device_key)

            total_files += file_count
            total_records += record_count

            ptr_summary = {}
            if pointer_lengths:
                ptr_summary = {
                    "count": len(pointer_lengths),
                    "min": min(pointer_lengths),
                    "max": max(pointer_lengths),
                    "median": sorted(pointer_lengths)[len(pointer_lengths) // 2],
                    "out_of_band": [l for l in pointer_lengths if l > _POINTER_BAND_HIGH],
                }
            pointer_distribution[device_key] = ptr_summary

            devices[device_key] = {
                "files": file_count, "records": record_count,
                "has_jsonl": has_jsonl, "pointer_lengths": ptr_summary}

    return {"devices": devices, "total_files": total_files,
            "total_records": total_records,
            "multi_record_files": multi_record_files,
            "pointer_distribution": pointer_distribution,
            "surviving_jsonl": surviving_jsonl,
            "surviving_jsonl_devices": surviving_jsonl_devices,
            "hollow": None}


def _corpus(context: dict) -> dict:
    return context.get("corpus") or survey_the_logs_tree()


def _trigger(now, context: dict) -> bool:
    """TRUE when any file holds more than one record, or any pointer is out of band.

    These are the two ways the grain breaks: a writer that appends instead of creating,
    and a caller that passes the payload where the pointer should be.
    """
    s = _corpus(context)
    if s.get("hollow"):
        return True
    if s["multi_record_files"]:
        return True
    for dev, ptr in s["pointer_distribution"].items():
        if ptr and ptr.get("out_of_band"):
            return True
    return False


def _enough(context: dict) -> bool:
    """CLEARED when the invariant has held across 2+ emitting components that landed AFTER
    this ticket. The ticket's own ``enough`` names it explicitly: the thing being watched is
    whether the grain is carried by the floor or by the discipline of whoever writes the
    next emit site.

    COUNTED BY DEVICES WITH PER-FILE EMISSIONS (not by devices with diagnostics.jsonl only,
    since those predate this ticket). Two or more devices with .json files, all clean.
    """
    s = _corpus(context)
    if s.get("hollow"):
        return False
    if s["multi_record_files"]:
        return False
    for dev, ptr in s["pointer_distribution"].items():
        if ptr and ptr.get("out_of_band"):
            return False
    emitting_devices = sum(
        1 for d in s["devices"].values() if d["files"] > 0)
    return emitting_devices >= 2


def _carry(context: dict) -> dict:
    s = _corpus(context)
    parts = []
    if s.get("hollow"):
        parts.append(f"the logs tree is HOLLOW — {s['hollow']}")
    if s["multi_record_files"]:
        parts.append(f"{len(s['multi_record_files'])} file(s) hold more than one record: "
                     + ", ".join(f["file"] for f in s["multi_record_files"]))
    out_of_band_devices = []
    for dev, ptr in s["pointer_distribution"].items():
        if ptr and ptr.get("out_of_band"):
            out_of_band_devices.append(
                f"{dev} has {len(ptr['out_of_band'])} pointer(s) over {_POINTER_BAND_HIGH} "
                f"chars (max {ptr['max']})")
    if out_of_band_devices:
        parts.append("fat pointer(s): " + "; ".join(out_of_band_devices))

    return {
        "finding": "; ".join(parts) or "the grain holds — one file, one record, all pointers in band",
        "counts": {
            "total_files": s["total_files"],
            "total_records": s["total_records"],
            "files_eq_records": s["total_files"] == s["total_records"],
        },
        "multi_record_files": s["multi_record_files"],
        "pointer_distribution": s["pointer_distribution"],
        "pointer_band": f"0-{_POINTER_BAND_HIGH} chars (a thin pointer is an address — a path, "
                        f"a digest, a short id — not a payload; inference_domain's legacy was "
                        f"{_POINTER_BAND_INFERENCE_LEGACY}-char median canonical text, now a "
                        f"64-char digest)",
        "surviving_jsonl": {
            "count": s["surviving_jsonl"],
            "devices": s["surviving_jsonl_devices"],
        },
        "emitting_devices": sum(1 for d in s["devices"].values() if d["files"] > 0),
        "ticket": owning_ticket(_OWNING_TICKET),
        "against_falsifier": "the ticket's clause (1) is one emission one file; clause (3) is "
                             "the pointer inside the corpus band; the surviving diagnostics.jsonl "
                             "count tracks the old shape receding within one retention window",
        "suggests": ("repair the probe — the logs tree does not exist" if s.get("hollow") else
                     "read the named file(s) and device(s): a multi-record file is a writer that "
                     "appended instead of creating, and a fat pointer is a caller that passed "
                     "the payload where the pointer should be — different failures with "
                     "different first moves"),
    }


_HORIZON = 1000

PROBE = Probe(
    why="does every emission file hold exactly one record, and is every pointer thin? — "
        "the proof settles it on the day it ships, and whether the NEXT writer carries "
        "the grain is a fact about the next writer",
    trigger=_trigger,
    to="harbor_master",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=_carry,
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    print(json.dumps(_carry({}), indent=2, default=str))
