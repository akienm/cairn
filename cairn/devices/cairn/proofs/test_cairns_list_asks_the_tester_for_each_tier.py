"""Teeth for ticket c811a8b1b8c7 — Cairn's scheduled list asks the tester for the hourly, daily
and weekly runs.

Outline 9.4.2.3.7.2-.4 and 5.3.3.1 (Akien, 2026-11-13): the hourly reseal-yellow, the daily
run-every-proof (in sleep) and the weekly weekly-run are the tester's tiers, and Cairn asks for
each over the bus. Measured 2026-11-13 before the build: cairn/devices/cairn/0/ held only bin/,
so no list existed, and nothing in Cairn's sleep asked the tester for anything.

WHY THE TEETH ARE THESE. One per falsifier clause; a hollow build fails at least one:
  (1) Cairn's shim, pulsed over the schedule.json this ticket writes, sends reseal-yellow to
      the tester once at an hourly slot (and not again in that slot). At the weekly slot it
      sends weekly-run once (and not again in that slot);
  (2) Cairn's own sleep step (its ``sleep-cycle`` mint) sends run-every-proof to the tester
      once, and that ask stands on the bus BEFORE the hand to the first sleeper. The token
      moves on while the tester is still running: an ask, not a wait;
  (3) with nobody answering as the tester, whether none is wired on the bus or no bus reaches
      it at all, each of the three asks raises its trouble and reads ``refused``. None reads
      ``answered``.

THE WORLD. A scratch bus (the cairn device's published scratch_bus, a real store under it), on
which a STUB TESTER is wired under the name ``tester``. It records each envelope it is handed
and answers it as the tester's shim does, a reply carrying ``reply_to``. Cairn is its REAL shim
and device, with only the edges stood in: no probes on the pulse (the tooth is the list, not
the probes), ``last_fired`` in a scratch file, and the device's roots under scratch.
``raise_trouble`` and ``clear_trouble`` are spies, so a proof's trouble never reaches the live
lane, and the ask's timeout is shortened.

    bin/cairn test cairn/devices/cairn/proofs/test_cairns_list_asks_the_tester_for_each_tier.py
"""
from __future__ import annotations

import json
import sys
import threading
import time
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "c811a8b1b8c7": {
        "1": "test_the_hourly_and_weekly_slots_each_ask_their_tier_once",
        "2": "test_cairns_sleep_asks_run_every_proof_before_the_token_moves_on",
        "3": "test_with_no_tester_answering_each_ask_is_raised_and_none_reads_answered",
    },
}

SCHEDULE = _REPO_ROOT / "cairn" / "devices" / "cairn" / "0" / "schedule.json"
SLEEPER = "fx_sleeper_c811"


class _StubTester:
    """Wired on the bus as ``tester``: records each ask and answers it as a shim does. A verb in
    ``hold`` waits for ``release`` before it answers (a tier that is still running)."""

    def __init__(self, bus, *, hold=()) -> None:
        self.bus, self.hold, self.got = bus, set(hold), []
        self.release = threading.Event()

    def __call__(self, envelope: dict) -> None:
        if envelope.get("reply_to") or (envelope.get("body") or {}).get("is_bounce"):
            return
        self.got.append(envelope)
        if envelope.get("verb") in self.hold:
            self.release.wait(10)
        self.bus.post(sender="tester", to=envelope["sender"], channel="personal",
                      why=f"{envelope.get('verb')} reply", reply_to=envelope["id"],
                      body={"tier": envelope.get("verb"), "proofs": [], "ticketed": [],
                            "refusals": []})

    def asked(self, verb: str) -> list[dict]:
        return [e for e in self.got if e.get("verb") == verb]


def _troubles(monkeypatch) -> list[dict]:
    from cairn.devices.cairn.device import CairnDevice
    raised: list[dict] = []
    monkeypatch.setattr(CairnDevice, "raise_trouble",
                        lambda self, identity, *, why, detail=None, now=None:
                        raised.append({"identity": identity, "why": why}) or {})
    monkeypatch.setattr(CairnDevice, "clear_trouble",
                        lambda self, identity, *, by, what_changed, now=None: {})
    return raised


def _roots():
    tmp = Path(scratch_dir("cairn-c811-"))
    roots = {"repo": tmp / "repo", "commons": tmp / "commons", "instance": tmp / "instance"}
    roster_root = tmp / "roster"
    (roster_root / "cairn" / "devices" / SLEEPER).mkdir(parents=True)
    return tmp, roots, roster_root


def _shim(bus, tmp: Path, roots: dict, last_fired: dict, roster_root: Path | None = None):
    """Cairn's REAL shim over ``bus``, reading the real schedule.json, with last_fired scratch."""
    from cairn.devices.cairn.device import CairnDevice
    from cairn.devices.cairn.shim import CairnShim
    fired = tmp / "scheduler" / "last_fired.json"
    fired.parent.mkdir(parents=True, exist_ok=True)
    fired.write_text(json.dumps(last_fired), encoding="utf-8")

    class _Cairn(CairnShim):
        def probes(self):
            return []

        def _schedule_path(self):
            return SCHEDULE

        def _last_fired_path(self):
            return fired

        def _start_device(self):
            dev = CairnDevice(bus=self._bus, roots=roots, roster_root=roster_root)
            dev.set_diagnostic_receiver(None)
            return dev

    shim = _Cairn(bus)
    shim.set_diagnostic_receiver(None)
    return shim


def _until(pred, within: float = 5.0) -> bool:
    end = time.monotonic() + within
    while time.monotonic() < end:
        if pred():
            return True
        time.sleep(0.02)
    return pred()


def _asks(dev) -> list[dict]:
    return dev.declared_verbs()["tester-asks"]({"verb": "tester-asks", "body": {}})["asks"]


def test_the_hourly_and_weekly_slots_each_ask_their_tier_once(monkeypatch):
    from cairn.devices.cairn.tools.scratch_bus import scratch_bus
    entries = {e["name"]: e for e in json.loads(SCHEDULE.read_text(encoding="utf-8"))}
    assert entries.get("test-tier-hourly", {}).get("cadence") == "hourly" and \
        entries["test-tier-hourly"].get("verb") == "ask-tester-reseal-yellow", entries
    assert entries.get("test-tier-weekly", {}).get("cadence") == "weekly@Sun 02:00" and \
        entries["test-tier-weekly"].get("verb") == "ask-tester-weekly-run", entries
    assert all("9.4.2.3.7" in e.get("why", "") for e in entries.values()), entries
    _troubles(monkeypatch)
    tmp, roots, _ = _roots()
    with scratch_bus.scratch_bus("c811_slots") as bus:
        tester = _StubTester(bus)
        bus.wire_delivery("tester", tester)
        shim = _shim(bus, tmp, roots, {"test-tier-hourly": "2026-11-16T09:00:00",
                                       "test-tier-weekly": "2026-11-15T02:00:00"})
        shim.on_pulse(datetime(2026, 11, 16, 10, 5))          # Mon: an hourly slot only
        assert _until(lambda: len(tester.asked("reseal-yellow")) == 1), tester.got
        shim.on_pulse(datetime(2026, 11, 16, 10, 40))         # the same slot
        time.sleep(0.3)
        assert len(tester.asked("reseal-yellow")) == 1, \
            f"the same hourly slot asked again: {tester.got}"
        assert tester.asked("weekly-run") == [], f"Monday asked the weekly tier: {tester.got}"
        shim.on_pulse(datetime(2026, 11, 22, 2, 10))          # Sun 02:00: the weekly slot
        assert _until(lambda: len(tester.asked("weekly-run")) == 1), tester.got
        shim.on_pulse(datetime(2026, 11, 22, 2, 50))          # the same slot
        time.sleep(0.3)
        assert len(tester.asked("weekly-run")) == 1, \
            f"the same weekly slot asked again: {tester.got}"
        assert all(e.get("sender") == "cairn" for e in tester.got), tester.got
        assert _until(lambda: {a["state"] for a in _asks(shim._device)} == {"answered"}), \
            _asks(shim._device)


def test_cairns_sleep_asks_run_every_proof_before_the_token_moves_on(monkeypatch):
    from cairn.devices.cairn.device import CairnDevice
    from cairn.devices.cairn.tools.scratch_bus import scratch_bus
    _troubles(monkeypatch)
    tmp, roots, roster_root = _roots()
    with scratch_bus.scratch_bus("c811_sleep") as bus:
        tester = _StubTester(bus, hold={"run-every-proof"})
        bus.wire_delivery("tester", tester)
        bus.post(sender=SLEEPER, to=SLEEPER, channel="announce", why="a sleeper's menu",
                 body={"verbs": ["sleep"]})
        dev = CairnDevice(bus=bus, roots=roots, roster_root=roster_root)
        dev.set_diagnostic_receiver(None)
        got = dev.declared_verbs()["sleep-cycle"]({"verb": "sleep-cycle", "body": {"act": "mint"}})
        try:
            cycle = got["cycle"]
            assert cycle["roster"] == [SLEEPER], got
            assert not tester.release.is_set() and len(tester.asked("run-every-proof")) == 1, \
                f"the sleep step did not ask run-every-proof once: {tester.got}"
            assert (cycle.get("asked") or {}).get("verb") == "run-every-proof", cycle
            mail = bus.read(channel="personal")
            ask = [i for i, e in enumerate(mail)
                   if e.get("addressee") == "tester" and e.get("verb") == "run-every-proof"]
            hand = [i for i, e in enumerate(mail)
                    if e.get("addressee") == SLEEPER and "sleep_token" in (e.get("body") or {})]
            assert len(ask) == 1 and len(hand) == 1 and ask[0] < hand[0], \
                f"the ask must stand on the bus before the token moves on: ask {ask}, hand {hand}"
        finally:
            tester.release.set()
        assert _until(lambda: [a["state"] for a in _asks(dev)] == ["answered"]), _asks(dev)
        assert len(tester.asked("run-every-proof")) == 1, tester.got


def test_with_no_tester_answering_each_ask_is_raised_and_none_reads_answered(monkeypatch):
    import cairn.devices.cairn.device as cairn_device
    import cairn.tools.bus_client.bus_client as bus_client
    from cairn.devices.cairn.device import CairnDevice
    from cairn.devices.cairn.tools.scratch_bus import scratch_bus
    raised = _troubles(monkeypatch)
    monkeypatch.setattr(cairn_device, "ASK_TIMEOUT_S",
                        {"reseal-yellow": 0.5, "weekly-run": 0.5, "run-every-proof": 0.5})
    tiers = ("reseal-yellow", "weekly-run", "run-every-proof")
    tmp, roots, roster_root = _roots()
    with scratch_bus.scratch_bus("c811_silent") as bus:        # nobody wired as the tester
        bus.post(sender=SLEEPER, to=SLEEPER, channel="announce", why="a sleeper's menu",
                 body={"verbs": ["sleep"]})
        shim = _shim(bus, tmp, roots, {}, roster_root)
        shim.on_pulse(datetime(2026, 11, 22, 2, 10))           # both slots due
        dev = shim._device
        got = dev.declared_verbs()["sleep-cycle"]({"verb": "sleep-cycle", "body": {"act": "mint"}})
        assert (got["cycle"].get("asked") or {}).get("state") != "answered", got
        assert _until(lambda: sorted(a["verb"] for a in _asks(dev)) == sorted(tiers)
                      and {a["state"] for a in _asks(dev)} == {"refused"}), _asks(dev)
        for verb in tiers:
            assert any(r["identity"] == f"cairn-tester-ask-{verb}-unanswered" for r in raised), \
                f"the unanswered {verb} ask was not raised: {raised}"
    raised.clear()
    def no_tester(*names, **kw):
        raise LookupError("no shim answers to 'tester'")
    monkeypatch.setattr(bus_client, "reach", no_tester)
    lone = CairnDevice(bus=None, roots=roots)
    lone.set_diagnostic_receiver(None)
    for verb in ("ask-tester-reseal-yellow", "ask-tester-weekly-run"):
        answer = lone.declared_verbs()[verb]({"verb": verb, "body": {}})
        assert answer.get("state") == "refused" and "tester" in answer.get("reason", ""), answer
    assert sorted(r["identity"] for r in raised) == [
        "cairn-tester-ask-reseal-yellow-unanswered", "cairn-tester-ask-weekly-run-unanswered"], raised
    assert not [a for a in _asks(lone) if a["state"] == "answered"], _asks(lone)


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
