"""PROOF for ticket cff5a197b3c4, clause 4: folder mail lands late, and cairn owns press_office.

A non-device addressee is delivered by its folder's instanceizer (BusDevice._try_folder_delivery).
Measured 2026-10-02: two envelopes still stood undelivered from 2026-09-30, both addressed to
folders that resolve today. One was the press_office WATCHME (c9e5226f); the other was to
charter (ab8ce962). The bus cached a failed resolution as None for its whole life, and no
code re-offered an envelope once it was stored.

  4. A folder addressee with no instanceizer at the first post gains one. The second post
     then lands both envelopes in the folder's recorder, and undelivered(to=it) reads 0.
     That includes an envelope like the press_office WATCHME (personal, kind 'record',
     sender == addressee). The cairn device's charter also names
     ~/.cairn/folders/press_office in its owns[].

The fixture folder is live instance-space, marked as testing, and removed at close.

    python3 cairn/devices/cairn/machines/bus/proofs/test_folder_mail_lands_late.py
"""

from __future__ import annotations

import contextlib
import json
import shutil
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.cairn.machines.bus.bus import BusDevice  # noqa: E402
from cairn.tools.base import address  # noqa: E402
from cairn.tools.instanceizer.instanceizer import ensure  # noqa: E402

PROVES = {"cff5a197b3c4": {"4": "folder_mail_lands_late_and_cairn_owns_press_office"}}

_FOLDER = "testing-cff5a197b3c4-late-folder"
_CHARTER = _REPO_ROOT / "cairn" / "devices" / "cairn" / "intention+why.json"
PASS = 0
FAIL = 0


def _records(fp: Path) -> list[dict]:
    out = []
    for p in fp.rglob("records.jsonl"):
        out += [json.loads(line) for line in p.read_text().splitlines() if line.strip()]
    return out


def folder_mail_lands_late_and_cairn_owns_press_office():
    fp = address.folder_path(_FOLDER)
    shutil.rmtree(fp, ignore_errors=True)
    try:
        with BusDevice.scratch("bus_fml") as bus:
            early = bus.post(sender=_FOLDER, to=_FOLDER, channel="personal",
                             why="testing-cff5a197b3c4 posted before the folder existed")
            bus.flush()
            assert [e["id"] for e in bus.undelivered(to=_FOLDER)] == [early["id"]], (
                "the early envelope should stand undelivered while nothing answers")
            ensure(fp, tool_class="cairn.tools.data_recorder.data_recorder.DataRecorder")
            late = bus.post(sender=_FOLDER, to=_FOLDER, channel="personal",
                            why="testing-cff5a197b3c4 posted after the folder gained an instanceizer")
            bus.flush()
            left = bus.undelivered(to=_FOLDER)
            assert not left, f"{len(left)} envelope(s) still stand undelivered: {left}"
            landed = {r.get("envelope_id") for r in _records(fp)}
            assert {early["id"], late["id"]} <= landed, (
                f"the folder recorder holds {landed}, not both envelopes")
    finally:
        shutil.rmtree(fp, ignore_errors=True)
    owns = json.loads(_CHARTER.read_text()).get("owns") or []
    assert "~/.cairn/folders/press_office" in owns, (
        f"the cairn device's charter owns {owns!r}, not ~/.cairn/folders/press_office")


TEETH = [folder_mail_lands_late_and_cairn_owns_press_office]


def _tooth(fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {fn.__name__}")


if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
