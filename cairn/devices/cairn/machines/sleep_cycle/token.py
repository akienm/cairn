"""sleep_cycle/token.py — the sleep-cycle token, handed round the roster by the cairn device.

THE SHAPE IS A HUB, NOT A RELAY, and that is measured rather than chosen (ticket bf146e9e3967,
D2): a ``Probe.to`` is a static field, and a probe may not import the cairn device's roster
(no cross-device imports), so a device's three-line probe cannot address "the next device".
So the cairn device HANDS the token to one device at a time and every device answers back to
cairn, which hands onward. What the ticket asked for — a token posted, received by at least
one device, forwarded through the roster in alpha order, returned to cairn — is exactly what
happens; only the forwarding hop runs through cairn instead of device-to-device.

TWO CHANNELS, TWO JOBS. The HAND rides ``personal`` because that is the only channel the bus
delivers on (``bus.py``: ``announce`` is a record with no delivery); it is VERB-LESS because a
verbed envelope to a discovered device bounces (``shim.deliver`` — ``_FeedbackDevice`` declares
no verbs) while a verb-less one lands in the device's inbound ``DataRecorder`` through
``receive()``. The ANNOUNCE feed is the RECORD of the rotation: one record per hand, one at
the close, so a complete rotation over n devices leaves exactly n+1 records for its cycle_id,
and "did the rotation complete?" is a read of the feed, never a memory.

THE ROSTER IS OPT-IN BY FILE (D3). The ground loop's roster (``discovery.device_folders``)
held 43 probes folders on 2026-09-18 and none of them carried a sleep probe; a token handed
to a device with nothing to answer it would stall at position 0 forever. So the roster here is
that list FILTERED to folders holding ``SLEEP_PROBE`` — a device joins the rotation by
berthing that one file and leaves by deleting it, the same physics as the roster itself.

THE STANDING CYCLE IS INSTANCE STATE (D4): ``cycle.json`` under the cairn instance, rewritten
atomically on every change; a mint over an open cycle appends the old one to
``superseded.jsonl`` first (Law 7 — kept, corrected by a later line). Nothing here is a
poller: the hand is an event, the answer is a probe firing on the beat that already runs.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

from cairn.devices.cairn.machines.ground_loop.discovery import device_folders
from cairn.tools.base.address import instance_path

# The one file that puts a device on the sleep rotation — berthed in its probes/ folder,
# three lines long (cairn/tools/base/mail_probe.py). Named so a reader of the folder can
# tell what it does without opening it.
SLEEP_PROBE = "sleeps_when_the_token_arrives.py"

# The body key every hand carries and every answer echoes. The handler results below
# NEVER carry it: the shim posts a verb's result back to the sender as a reply, which lands
# in the same inbound recorder the device's probe reads, and the probe matches on this key.
TOKEN_KEY = "sleep_token"

DEVICE = "cairn"
WHY = "sleep token"


def _now(now=None) -> str:
    return (now or datetime.now(timezone.utc)).isoformat()


# ── the roster ──────────────────────────────────────────────────────────────

def roster(root: Path | None = None) -> list[str]:
    """Alpha-sorted device ids whose probes/ folder holds ``SLEEP_PROBE`` — read from disk
    every call, never cached, so the rotation can never hold a device that has left."""
    ids = {device_id for device_id, folder in device_folders(root)
           if (Path(folder) / SLEEP_PROBE).is_file()}
    return sorted(ids)


# ── the standing cycle ──────────────────────────────────────────────────────

def cycle_dir(roots: dict | None = None) -> Path:
    return instance_path(DEVICE, 0, roots) / "machines" / "sleep_cycle"


def standing(roots: dict | None = None) -> dict | None:
    """The standing cycle (open or closed) or None when none was ever minted here."""
    p = cycle_dir(roots) / "cycle.json"
    if not p.is_file():
        return None
    return json.loads(p.read_text())


def _write(cycle: dict, roots: dict | None) -> None:
    d = cycle_dir(roots)
    d.mkdir(parents=True, exist_ok=True)
    tmp = d / "cycle.json.tmp"
    tmp.write_text(json.dumps(cycle, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, d / "cycle.json")


def _announce(bus, cycle: dict, event: str, device: str | None) -> None:
    bus.post(sender=DEVICE, to=DEVICE, channel="announce", verb="", why=WHY,
             body={"cycle_id": cycle["cycle_id"], "event": event, "device": device,
                   "position": cycle["position"], "of": len(cycle["roster"])})


def _hand(bus, cycle: dict) -> None:
    """Hand the token to roster[position] — verb-less, on personal (see the module docstring)."""
    device = cycle["roster"][cycle["position"]]
    bus.post(sender=DEVICE, to=device, channel="personal", verb="", why=WHY,
             body={TOKEN_KEY: cycle["cycle_id"], "position": cycle["position"],
                   "of": len(cycle["roster"])})
    _announce(bus, cycle, "hand", device)


def _close(bus, cycle: dict, by: str, now=None) -> None:
    cycle["closed_at"] = _now(now)
    cycle["closed_by"] = by
    _announce(bus, cycle, "closed", None)


def mint(bus, *, roots: dict | None = None, roster_root: Path | None = None, now=None) -> dict:
    """Open a cycle and hand the token to the first device. An open cycle is superseded
    (kept in superseded.jsonl); an empty roster closes at once as "nothing to visit"."""
    old = standing(roots)
    if old is not None and old.get("closed_at") is None:
        d = cycle_dir(roots)
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "superseded.jsonl", "a", encoding="utf-8") as fh:
            fh.write(json.dumps({**old, "superseded_at": _now(now)}, sort_keys=True) + "\n")
    cycle = {"cycle_id": uuid.uuid4().hex, "roster": roster(roster_root), "position": 0,
             "visited": [], "opened_at": _now(now), "closed_at": None, "closed_by": None}
    if cycle["roster"]:
        _hand(bus, cycle)
    else:
        _close(bus, cycle, "nothing to visit", now)
    _write(cycle, roots)
    return cycle


def receive_answer(bus, body: dict, *, roots: dict | None = None, now=None) -> dict:
    """A device's answer to the hand. Refused loudly when it names a cycle that is not the
    standing open one, or comes from a device that is not the current holder (Law 7: the
    refusal is the record). Accepted: recorded under ``visited``, then the next hand or the
    close. The result never carries TOKEN_KEY (see its comment)."""
    body = body if isinstance(body, dict) else {}
    cycle = standing(roots)
    cycle_id, device = body.get(TOKEN_KEY), body.get("device")
    if cycle is None or cycle.get("closed_at") is not None:
        return {"accepted": False, "reason": "no open cycle", "cycle_id": cycle_id, "device": device}
    if cycle_id != cycle["cycle_id"]:
        return {"accepted": False, "reason": "stale cycle_id", "cycle_id": cycle_id,
                "standing": cycle["cycle_id"], "device": device}
    holder = cycle["roster"][cycle["position"]]
    if device != holder:
        return {"accepted": False, "reason": "out of turn", "cycle_id": cycle_id,
                "device": device, "holder": holder}
    cycle["visited"].append({"device": device, "answer": body.get("answer"), "at": _now(now)})
    cycle["position"] += 1
    closed = cycle["position"] >= len(cycle["roster"])
    if closed:
        _close(bus, cycle, "rotation complete", now)
    else:
        _hand(bus, cycle)
    _write(cycle, roots)
    return {"accepted": True, "cycle_id": cycle["cycle_id"], "position": cycle["position"],
            "closed": closed}
