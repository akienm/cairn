#!/usr/bin/env python3
"""Proof for ticket 229ee25ff6f0 — the heartbeat's page is the cairn device's.

Outline 5.6.3: the ground loop must never grow back "a bus, a shim, probes, ...", and 5.6.5
gives it no verbs. Outline 2.3.8.5: a machine may have a panel of its own, reached through its
host device's public interface. So the Heartbeat pane and the ``beat`` verb, which a shim of the
ground loop's own served until this ticket, are the cairn device's (5.3.2: the cairn device owns
the ground loop). They read the ground loop's public faces only: ``guard.held`` and
``heartbeat.read_record``.

One tooth per falsifier clause this file owns (1-3 berth in bin/proofs/test_retired_components_are_gone.py):

  4. the cairn device's beat pane data is the ground loop's lock (``up``) plus its beat record as
     ``heartbeat.read_record`` returns it, and an absent record is the named lack;
  5. the cairn device answers verb ``beat`` with that data;
  6. the cairn device's page, assembled by the standard ``BaseShim.active_page``, carries the
     Heartbeat pane after the trouble pane, answered rather than absent;
  7. the cairn device's charter says it carries the heartbeat's page.

Every subject is imported inside a guard, so a reverted world reds teeth instead of crashing.

    python3 cairn/devices/cairn/proofs/test_the_cairn_page_carries_the_heartbeat.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"229ee25ff6f0": {
    "4": "the_pane_renders_what_the_record_and_the_lock_say",
    "5": "the_beat_verb_answers_the_same_data",
    "6": "the_cairn_page_carries_the_heartbeat",
    "7": "the_charter_says_it_carries_the_heartbeat",
}}

CHARTER = _REPO / "cairn" / "devices" / "cairn" / "intention+why.json"
_T0 = datetime(2026, 8, 9, 12, 0, 0, tzinfo=timezone.utc)


def _faces():
    from cairn.devices.cairn import device
    from cairn.devices.cairn.machines.ground_loop import guard, heartbeat
    return device, guard, heartbeat


def the_pane_renders_what_the_record_and_the_lock_say():
    device, guard, heartbeat = _faces()
    with tempfile.TemporaryDirectory() as td:
        home = Path(td) / "0"
        absent = device.beat_pane_data(home=home)
        assert absent["up"] is False and absent["record"] is None, absent
        assert "no record at" in absent["lack"], "an absent record is a NAMED lack, never blank"
        heartbeat.write_record(_T0, {"beats": 1}, os.getpid(), home)
        claim = guard.claim_singleton(home)
        try:
            pane = device.beat_pane_data(home=home)
            assert pane["up"] is True and pane["record"]["state"] == {"beats": 1}, pane
            assert {k: v for k, v in pane.items() if k not in ("reports", "up", "age_s")} == \
                {k: v for k, v in heartbeat.read_record(home).items() if k != "age_s"}, \
                "the pane's record IS the read face's own output: render, never derive"
            assert "resident singleton" in pane["reports"]
        finally:
            claim.release()
        assert device.beat_pane_data(home=home)["up"] is False, "released: the pane says down"


def the_beat_verb_answers_the_same_data():
    device, _guard, _hb = _faces()
    verbs = device.CairnDevice().declared_verbs()
    assert "beat" in verbs, f"the cairn device has no beat verb: {sorted(verbs)}"
    data = verbs["beat"]({"id": "proof-beat"})
    assert data["up"] in (True, False), data
    assert data["record"] is not None or "no record at" in data["lack"], data
    assert "resident singleton" in data["reports"]


def the_cairn_page_carries_the_heartbeat():
    from cairn.devices.cairn.shim import CairnShim
    page = CairnShim().active_page()
    assert page["device"] == "cairn", page.get("device")
    kinds = [p["kind"] for p in page["panes"]]
    assert "trouble" in kinds and "beat" in kinds and kinds.index("beat") > kinds.index("trouble"), kinds
    pane = next(p for p in page["panes"] if p["kind"] == "beat")
    assert pane["label"] == "Heartbeat" and "absent" not in pane, pane
    assert pane["data"]["up"] in (True, False)


def the_charter_says_it_carries_the_heartbeat():
    what = json.loads(CHARTER.read_text(encoding="utf-8"))["what"]
    assert "Heartbeat pane" in what, "the cairn charter's what does not say it carries the Heartbeat pane"


TEETH = [the_pane_renders_what_the_record_and_the_lock_say,
         the_beat_verb_answers_the_same_data,
         the_cairn_page_carries_the_heartbeat,
         the_charter_says_it_carries_the_heartbeat]


def main() -> int:
    failed = 0
    for fn in TEETH:
        try:
            fn()
        except Exception as exc:  # noqa: BLE001 — the house runner: every tooth runs and reads
            failed += 1
            print(f"  FAIL  {fn.__name__}: {type(exc).__name__}: {exc}", flush=True)
        else:
            print(f"  PASS  {fn.__name__}", flush=True)
    print(f"{len(TEETH) - failed} passed, {failed} failed out of {len(TEETH)}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
