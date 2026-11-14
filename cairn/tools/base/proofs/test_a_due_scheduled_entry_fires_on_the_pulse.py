"""A due scheduled entry fires on the pulse (ticket 185cee7cce24).

Outline 9.4.2.3.7 (test tiers): the hourly, daily and weekly runs are entries on a device
instance's own list. Measured 2026-11-13: the base shim's on_pulse evaluated probes and pulse
modules only, so no device could run a verb on a clock, and `cairn <device> scheduler` was an
unknown verb (exit 2).

Teeth a hollow base could not pass (a fixture shim declaring verb 'reseal-yellow', a spy bus,
a scratch schedule.json and last_fired.json; no live device, no live bus, no store):
  1. A pulse at a due time posts the entry's verb to the device itself once and records
     last_fired; a second pulse in the same slot posts nothing.
  2. After a gap spanning three slots, the next pulse posts the entry once.
  3. `scheduler set` refuses a verb the device does not declare and a cadence it cannot read,
     naming each, and writes nothing.
  4. `scheduler list`, `show` and `get` answer from schedule.json as written.

Run: bin/cairn test cairn/tools/base/proofs/test_a_due_scheduled_entry_fires_on_the_pulse.py
"""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir

PROVES = {
    "185cee7cce24": {
        "1": "test_a_due_entry_fires_once_and_the_same_slot_fires_nothing",
        "2": "test_a_gap_of_three_slots_fires_once",
        "3": "test_set_refuses_an_undeclared_verb_and_an_unreadable_cadence_and_writes_nothing",
        "4": "test_list_show_and_get_answer_from_the_schedule_as_written",
    },
}

_DEVICE = "scheduled_device_185c"
_ENTRY = {"name": "reseal", "cadence": "hourly", "verb": "reseal-yellow",
          "why": "the hourly tier reseals yellow components"}


class _SpyBus:
    def __init__(self) -> None:
        self.posted: list[dict] = []

    def post(self, **envelope) -> dict:
        envelope = {"id": f"posted{len(self.posted)}", **envelope}
        self.posted.append(envelope)
        return envelope

    def wire_delivery(self, device_id: str, deliver) -> None:
        pass

    def read(self, **kw) -> list[dict]:
        return []

    def undelivered(self, *, to: str, limit: int) -> list[dict]:
        return []

    def record_delivery(self, envelope_id: str, *, to: str, by: str) -> None:
        pass


def _fixture(entries=None):
    """A shim over a scratch schedule; built at call time so a reverted base reds the tooth."""
    from cairn.tools.base.shim import BaseShim

    d = scratch_dir("sched185c")
    sched, fired = d / "schedule.json", d / "scheduler" / "last_fired.json"
    if entries is not None:
        sched.write_text(json.dumps(entries, indent=2) + "\n", encoding="utf-8")

    class _Shim(BaseShim):
        def __init__(self, bus):
            super().__init__(bus=bus)
            self.set_diagnostic_receiver(None)

        @property
        def device_id(self):
            return _DEVICE

        def _start_device(self):
            raise AssertionError("a scheduled pulse must not need the device awake")

        def raise_trouble(self, *a, **kw):
            return None

        def declared_contract(self):
            return {"verbs": ["reseal-yellow", "show", "get"], "panes": []}

        def _schedule_path(self):
            return sched

        def _last_fired_path(self):
            return fired

    bus = _SpyBus()
    return _Shim(bus), bus, sched, fired


def _scheduled_posts(bus) -> list[dict]:
    return [e for e in bus.posted if e.get("to") == _DEVICE and e.get("verb") == "reseal-yellow"]


def test_a_due_entry_fires_once_and_the_same_slot_fires_nothing():
    shim, bus, _, fired = _fixture([_ENTRY])
    rec = shim.on_pulse(datetime(2026, 11, 13, 10, 5))
    posts = _scheduled_posts(bus)
    assert len(posts) == 1, f"expected one post of reseal-yellow to the device, posted: {bus.posted}"
    assert [s.get("name") for s in rec.get("scheduled") or []] == ["reseal"], f"record: {rec}"
    assert fired.exists(), "last_fired was not recorded"
    assert "reseal" in json.loads(fired.read_text(encoding="utf-8")), fired.read_text(encoding="utf-8")
    rec2 = shim.on_pulse(datetime(2026, 11, 13, 10, 55))
    assert len(_scheduled_posts(bus)) == 1, f"the same slot fired again: {bus.posted}"
    assert rec2.get("scheduled") == [], f"the second pulse's record: {rec2}"
    print("ok test_a_due_entry_fires_once_and_the_same_slot_fires_nothing")


def test_a_gap_of_three_slots_fires_once():
    shim, bus, _, fired = _fixture([_ENTRY])
    shim.on_pulse(datetime(2026, 11, 13, 10, 5))
    assert len(_scheduled_posts(bus)) == 1, f"first pulse: {bus.posted}"
    shim.on_pulse(datetime(2026, 11, 13, 13, 20))      # 11:00, 12:00 and 13:00 all passed
    assert len(_scheduled_posts(bus)) == 2, (
        f"a gap of three slots must fire exactly once more, posted: {_scheduled_posts(bus)}")
    shim.on_pulse(datetime(2026, 11, 13, 13, 40))
    assert len(_scheduled_posts(bus)) == 2, "the catch-up fired again within its slot"
    print("ok test_a_gap_of_three_slots_fires_once")


def test_set_refuses_an_undeclared_verb_and_an_unreadable_cadence_and_writes_nothing():
    shim, _, sched, fired = _fixture([_ENTRY])
    before = sched.read_bytes()
    r = shim.resolve(["scheduler", "set", "nightly", "--cadence", "nightly@25:99", "--verb", "no-such-verb"])
    assert r["exit"] == 2, f"set was not refused: {r}"
    assert "no-such-verb" in r["text"] and "nightly@25:99" in r["text"], (
        f"the refusal does not name both lacks: {r['text']!r}")
    assert sched.read_bytes() == before, "a refused set wrote the schedule"
    assert not fired.exists(), "a refused set wrote last_fired"
    ok = shim.resolve(["scheduler", "set", "nightly", "--cadence", "daily@02:30", "--verb", "reseal-yellow"])
    assert ok["exit"] == 0, f"a good set was refused: {ok}"
    names = [e["name"] for e in json.loads(sched.read_text(encoding="utf-8"))]
    assert names == ["reseal", "nightly"], f"the good set did not land as written: {names}"
    print("ok test_set_refuses_an_undeclared_verb_and_an_unreadable_cadence_and_writes_nothing")


def test_list_show_and_get_answer_from_the_schedule_as_written():
    weekly = {"name": "weekly", "cadence": "weekly@Sun 03:00", "verb": "reseal-yellow", "why": "the weekly tier"}
    shim, _, _, _ = _fixture([_ENTRY, weekly])
    lst = shim.resolve(["scheduler", "list"])
    assert lst["exit"] == 0 and lst["data"] == [_ENTRY, weekly], f"list: {lst}"
    assert "weekly@Sun 03:00" in lst["text"], lst["text"]
    show = shim.resolve(["scheduler", "show", "weekly"])
    assert show["exit"] == 0 and "the weekly tier" in show["text"] and "never" in show["text"], f"show: {show}"
    got = shim.resolve(["scheduler", "get", "reseal"])
    assert got["exit"] == 0, f"get: {got}"
    assert json.loads(got["text"]) == dict(_ENTRY, last_fired=None), f"get: {got['text']!r}"
    miss = shim.resolve(["scheduler", "show", "absent"])
    assert miss["exit"] == 1 and "absent" in miss["text"], f"show of an absent entry: {miss}"
    print("ok test_list_show_and_get_answer_from_the_schedule_as_written")


if __name__ == "__main__":
    test_a_due_entry_fires_once_and_the_same_slot_fires_nothing()
    test_a_gap_of_three_slots_fires_once()
    test_set_refuses_an_undeclared_verb_and_an_unreadable_cadence_and_writes_nothing()
    test_list_show_and_get_answer_from_the_schedule_as_written()
