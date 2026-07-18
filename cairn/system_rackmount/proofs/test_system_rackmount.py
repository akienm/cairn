"""Proof for system_rackmount — the device abstracting host system services device-independently.

Exercises the WHOLE spine composed as a system: the tester (proven-space), db_domain (the owned
target), ground_loop (runs one fired pass), and the system rackmount surfacing the scheduler as
its first system service. The scheduler is reached the way a device would reach it — by name,
through the rackmount (``service('scheduler')``) — never by importing the OS or the service
class. The firing physics is proven WITHOUT a clock: ``tick`` takes its moment (and any observed
context) explicitly, so a trigger's decision is a table, not a race.

Teeth a hollow build could not pass:
  - THE RACKMOUNT HANDS OUT ITS SERVICE BY NAME, and refuses a missing one LOUDLY (CP1 / Law 7).
    A rackmount that returned None for an unmounted service, or hid the scheduler, trips this.
  - A TRIGGER FIRES EXACTLY WHEN ITS CONDITION IS MET — interval (first tick + every N seconds),
    date (once, at/after), quantity (count ≥ threshold), state (the reactive summons).
  - A ONE-SHOT FIRES ONCE. INTERVAL RESPECTS THE CADENCE.
  - A FIRED DRIVER ACTUALLY RUNS — through ground_loop, end to end: the row lands in the owned
    target and the run-record rides in the tick-record. The service adds no execution of its own.
  - A REFUSED DRIVER IS LOUD AND DOES NOT ABORT THE BATCH (Law 7, CP2).
  - REACTIVE FIRES ONLY THE MATCH.
  - THE RACKMOUNT IS A DEVICE (Law 2 / Form v0 #2) and reports its services + their state.

Requires Postgres (db_domain) and runs the tester (subprocess proofs, to admit the method).
Each writing test mints its OWN owned target; all are dropped on the way out.

    python3 cairn/system_rackmount/proofs/test_system_rackmount.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.core_values import CoreValuesMixin
from cairn.db_domain import store
from cairn.ground_loop.loop import GroundLoopDevice
from cairn.ground_loop.registry import MethodRegistry
from cairn.ground_loop.proofs.fixtures.collect import collect
from cairn.system_rackmount.rackmount import SystemRackmountDevice
from cairn.system_rackmount.services.scheduler import SchedulerService, _trigger_fires

_FIXTURES = _REPO_ROOT / "cairn" / "ground_loop" / "proofs" / "fixtures"
_PROOF_COLLECT = _FIXTURES / "proof_collect.py"

_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_OWNER = "sensor"
_CREATED: list[str] = []  # every target this proof mints — all dropped in _cleanup

_NOW = datetime(2026, 7, 18, 12, 0, 0)


def _fresh_rackmount() -> SystemRackmountDevice:
    """A rackmount whose scheduler fires onto a ground_loop that admits `collect` (proof passed)."""
    reg = MethodRegistry()
    reg.register("collect", collect, _PROOF_COLLECT)
    return SystemRackmountDevice(GroundLoopDevice(registry=reg))


def _scheduler() -> SchedulerService:
    """Reach the scheduler the device-independent way — by name, through the rackmount."""
    return _fresh_rackmount().service("scheduler")


def _new_target() -> str:
    """Mint a fresh owned target so each test's landed rows are its own (no cross-test bleed)."""
    name = f"_srm_target_{_NONCE}_{len(_CREATED)}"
    store.create_owned_table(name, _OWNER, {"value": "text"})
    _CREATED.append(name)
    return name


def _driver(table: str, name="collect-driver", method="collect", owner=_OWNER):
    return {
        "name": name,
        "method": method,
        "why": "collect the reading into the owned target on the scheduler's cadence",
        "target": {"table": table, "owner": owner},
    }


# --- the rackmount hands out its service by name, loudly ---------------------

def test_the_rackmount_hands_out_its_service_and_refuses_a_missing_one():
    rm = _fresh_rackmount()
    assert rm.services() == ["scheduler"], "the scheduler is the first mounted system service"
    assert isinstance(rm.service("scheduler"), SchedulerService), "reachable by name, device-independently"
    assert rm.scheduler is rm.service("scheduler"), "the convenience is the same object"
    try:
        rm.service("nope")
        raise AssertionError("a missing system service must be refused loudly, not returned as None")
    except KeyError:
        pass


# --- the firing physics, as a pure table (no clock, no stack) ---------------

def test_a_trigger_fires_exactly_when_its_condition_is_met():
    assert _trigger_fires({"kind": "interval", "seconds": 300}, _NOW, None, 0, {}) is True
    assert _trigger_fires({"kind": "interval", "seconds": 300}, _NOW, _NOW - timedelta(seconds=299), 1, {}) is False
    assert _trigger_fires({"kind": "interval", "seconds": 300}, _NOW, _NOW - timedelta(seconds=300), 1, {}) is True

    at = {"kind": "date", "at": _NOW}
    assert _trigger_fires(at, _NOW - timedelta(seconds=1), None, 0, {}) is False
    assert _trigger_fires(at, _NOW, None, 0, {}) is True
    assert _trigger_fires(at, _NOW + timedelta(hours=1), None, 1, {}) is False  # already fired

    q = {"kind": "quantity", "source": "queue_depth", "at_least": 10}
    assert _trigger_fires(q, _NOW, None, 0, {"queue_depth": 9}) is False
    assert _trigger_fires(q, _NOW, None, 0, {"queue_depth": 10}) is True

    s = {"kind": "state", "on": "PROVEME"}
    assert _trigger_fires(s, _NOW, None, 0, {"state": "BUILDME"}) is False
    assert _trigger_fires(s, _NOW, None, 0, {"state": "PROVEME"}) is True


def test_a_one_shot_fires_once_not_every_tick():
    sched = _scheduler()
    sched.mount(_driver(_new_target()), {"kind": "date", "at": _NOW})
    first = sched.tick(_NOW + timedelta(seconds=1))
    second = sched.tick(_NOW + timedelta(hours=2))
    assert first["fired_count"] == 1, "a date trigger must fire once it is due"
    assert second["fired_count"] == 0, "a one-shot must not re-fire on later pulses"


def test_interval_respects_the_cadence():
    sched = _scheduler()
    sched.mount(_driver(_new_target()), {"kind": "interval", "seconds": 300})
    a = sched.tick(_NOW)
    b = sched.tick(_NOW + timedelta(seconds=120))
    c = sched.tick(_NOW + timedelta(seconds=360))
    assert (a["fired_count"], b["fired_count"], c["fired_count"]) == (1, 0, 1), \
        "interval must fire, hold within the window, then fire again — cadence is physics"


def test_a_fired_driver_actually_runs_through_ground_loop():
    sched = _scheduler()
    target = _new_target()
    sched.mount(_driver(target), {"kind": "interval", "seconds": 60})
    record = sched.tick(_NOW)
    assert record["fired_count"] == 1
    entry = record["fired"][0]
    assert entry["outcome"] == "ok" and entry["run"]["wrote"] == {"value": "42"}, \
        "a fired driver's run-record must ride in the tick-record"
    rows = store.read(target, where="value = %s", params=("42",))
    assert len(rows) == 1 and rows[0]["value"] == "42", "the scheduler must run, not merely schedule"


def test_a_refused_driver_is_loud_and_does_not_abort_the_batch():
    sched = _scheduler()
    target = _new_target()
    sched.mount(_driver(target, name="good"), {"kind": "interval", "seconds": 60})
    sched.mount(_driver(target, name="bad", method="never-registered"), {"kind": "interval", "seconds": 60})
    record = sched.tick(_NOW)
    assert record["fired_count"] == 2, "both triggers fired — firing is separate from run outcome"
    by_name = {e["driver"]: e for e in record["fired"]}
    assert by_name["good"]["outcome"] == "ok", "the good driver still runs despite its neighbour"
    assert by_name["bad"]["outcome"] == "refused", "the unproven driver is refused, not run"
    assert "UnprovenMethod" in by_name["bad"]["error"], "the kick-back is loud and permanent (Law 7)"
    rows = store.read(target, where="value = %s", params=("42",))
    assert len(rows) == 1, "a refused driver must not abort the drain of the rest"


def test_reactive_fires_only_the_match():
    sched = _scheduler()
    target = _new_target()
    sched.mount(_driver(target, name="on-proveme"), {"kind": "state", "on": "PROVEME"})
    sched.mount(_driver(target, name="on-interval"), {"kind": "interval", "seconds": 999999})
    sched.tick(_NOW)  # interval fires once here (first eval); now on a long cadence
    record = sched.tick(_NOW + timedelta(seconds=1), context={"state": "PROVEME"})
    fired_names = {e["driver"] for e in record["fired"]}
    assert fired_names == {"on-proveme"}, "a state pulse fires only the mount waiting on that state"


def test_the_rackmount_is_a_device():
    rm = _fresh_rackmount()
    assert isinstance(rm, CoreValuesMixin), "a device must compose the core values (Law 2)"
    assert [v.id for v in rm.CORE_VALUES] == ["CP1", "CP2", "CP3", "CP4", "CP5", "CP6"]
    surface = rm.introspect()
    assert list(surface) == ["intention", "state", "settings", "other"], "Form v0 #2 order"
    assert surface["state"]["services"] == ["scheduler"], "state surfaces the abstracted services"
    assert surface["settings"]["scheduler"]["trigger_kinds"] == ["date", "interval", "quantity", "state"]


def _cleanup():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            for table in _CREATED:
                cur.execute(f'DROP TABLE IF EXISTS "{table}"')
                cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (table,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_the_rackmount_hands_out_its_service_and_refuses_a_missing_one,
        test_a_trigger_fires_exactly_when_its_condition_is_met,
        test_a_one_shot_fires_once_not_every_tick,
        test_interval_respects_the_cadence,
        test_a_fired_driver_actually_runs_through_ground_loop,
        test_a_refused_driver_is_loud_and_does_not_abort_the_batch,
        test_reactive_fires_only_the_match,
        test_the_rackmount_is_a_device,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — system_rackmount: hands out the scheduler by name (device-independent); the "
          "scheduler fires exactly when met, runs through ground_loop, a refused driver is loud")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
