"""ground_loop — the generic driver-executor. The spine's parts, first working as a system.

THE HYPOTHESIS (Law 3, stated so it can be refuted): most of what a device DOES — collect a
metric, watch a threshold, alarm, fold artifacts into the trees — is not bespoke per-device
code but the SAME loop with different (trigger, method, target). If that is true, ONE generic
executor can run all of them from declarative data. This module is that executor at its
minimal provable size; building it either confirms the hypothesis for the simple case or
shows where it breaks (operational-driver.json; MAP.md 'the operational-driver primitive').

WHAT IT DOES: given a driver — ``{name, method, why, target:{table, owner}}`` — it
  1. resolves ``method`` against the method-registry, and REFUSES if it is not in
     proven-space (Law 8 — a driver introduces no new code; registry.py holds the gate),
  2. runs the proven method to produce a row,
  3. writes that row to the driver's OWNED target through db_domain, whose owner-gate refuses
     any write that is not the target's owner's (Law 6 — physics, not the caller's goodwill),
  4. returns a RUN-RECORD — so the run is legible. This is what makes a driver LEARNING and
     not silent RUNNING (MAP: 'anything running is emitting evidence, so anything running is
     learning'; there is no uninstrumented execution in Cairn — the UU silent-failure disease).

It is the first device that COMPOSES the ones before it: the tester defines proven-space, and
db_domain is the owned target. The ground_loop introduces no third authority — it only wires
those two under a driver's declared why.

WHAT IT IS NOT (deliberate, matches the spine order ground_loop → rack): it does not SCHEDULE.
A driver's trigger (interval / date / quantity / a-state) is fired by the ``host``/rack device
(the next spine step); ``run_driver`` runs ONE fired pass. Reactive/scheduled waking, queue
draining, and back-edge (kick-back) routing are the rack's and the emit-chokepoint's to add.

OPEN EDGES (filed, not faked — children of this stone):
  - RUN-RECORDS are produced, not yet journaled/persisted — a durable journey is a later
    stone (the rack consumes run-records; journeys land with the emit-chokepoint). Mirrors the
    tester's produced-not-persisted discipline; the target WRITE is durable, the run-record is
    the legibility surface.
  - The registry is in-memory (registry.py edge); a durable method-registry waits on a real
    restart-surviving consumer.
  - v0 methods take no arguments and return a row; a driver's ``sources`` (inputs to the
    method) firm up when a transform-driver (not just a sensor) pulls them.
"""

from __future__ import annotations

from datetime import datetime

from cairn.base.device import BaseDevice
from cairn.db_domain import store
from cairn.ground_loop.registry import MethodRegistry

REQUIRED_DRIVER_FIELDS = ("name", "method", "why", "target")


def _validate_driver(driver: dict) -> None:
    """A malformed driver is refused before anything runs (CP1: say what's wrong, loudly)."""
    if not isinstance(driver, dict):
        raise ValueError(f"a driver must be a dict of {REQUIRED_DRIVER_FIELDS}, got {type(driver).__name__}")
    missing = [f for f in REQUIRED_DRIVER_FIELDS if f not in driver]
    if missing:
        raise ValueError(f"driver is missing required field(s) {missing} — every driver carries {REQUIRED_DRIVER_FIELDS}")
    target = driver["target"]
    if not isinstance(target, dict) or "table" not in target or "owner" not in target:
        raise ValueError("driver.target must be {'table': ..., 'owner': ...} — the owned target a write routes through (Law 6)")


class GroundLoopDevice(BaseDevice):
    """The generic driver-executor as a device (carries CP1-CP6; reports intention/state/settings).

    Its one capability is ``run_driver``. It holds a ``MethodRegistry`` (proven-space) and
    reaches durable state only through db_domain — it opens no connection of its own and
    introduces no method of its own.
    """

    def __init__(self, registry: MethodRegistry | None = None, device_id: str = "ground_loop") -> None:
        super().__init__()
        self._registry = registry or MethodRegistry()
        self._device_id = device_id
        self._drivers_run = 0
        self._last_record: dict | None = None

    @property
    def device_id(self) -> str:
        return self._device_id

    @property
    def registry(self) -> MethodRegistry:
        return self._registry

    # --- the one capability: run a fired driver -----------------------------

    def run_driver(self, driver: dict) -> dict:
        """Run one fired pass of ``driver``: resolve (Law 8) → run → owner-gated write (Law 6) →
        run-record. Both guards are PROPAGATED, not swallowed: an unproven method raises
        ``UnprovenMethod`` and a non-owner target raises ``OwnershipError`` — a refused driver
        run is a loud kick-back (CP2), never a success-shaped silence (Law 7)."""
        _validate_driver(driver)

        # G1 (Law 8): the method must resolve to proven-space, else the driver does not run.
        method = self._registry.resolve(driver["method"])  # raises UnprovenMethod if not proven

        # Run the proven method to produce the row it collects/transforms.
        row = method()

        # G2 (Law 6): the write routes through the target owner's gate — db_domain refuses
        # any write that is not the declared owner's, and any table it did not create.
        target = driver["target"]
        store.write(target["table"], target["owner"], row)

        # G3 (LEARNING, not RUNNING): the run leaves a legible record — evidence, not silence.
        record = self._run_record(driver, row, outcome="ok")
        self._drivers_run += 1
        self._last_record = record
        return record

    def _run_record(self, driver: dict, row: dict, *, outcome: str) -> dict:
        """The evidence a driver run emits — what ran, why, what it wrote, when."""
        return {
            "driver": driver["name"],
            "method": driver["method"],
            "why": driver["why"],
            "target": driver["target"],
            "wrote": row,
            "outcome": outcome,
            "date": datetime.now().isoformat(timespec="seconds"),
        }

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "Run a declarative driver — wire a PROVEN method to an OWNED target — as one "
            "generic executor: resolve to proven-space (Law 8), write through the owner's gate "
            "(Law 6), leave a legible run-record (LEARNING, not silent RUNNING).",
            "why": "Most of what a device does is the same loop with different fields; making it "
            "data run by one executor means no uninstrumented daemon is left to rot silently — the "
            "hypothesis (Law 3) that the ground_loop IS that executor.",
        }

    def state(self) -> dict:
        return {
            "drivers_run": self._drivers_run,
            "last_outcome": (self._last_record or {}).get("outcome"),
            "proven_methods": self._registry.names(),  # what is currently wireable
        }

    def settings(self) -> dict:
        return {
            "method_registry": "in-memory; a method is wireable only after its proof passes under "
            "the tester (proven-space, Law 8). Durable registry is a filed edge.",
            "target_gate": "db_domain — writes route through the target owner's gate (Law 6); the "
            "ground_loop opens no connection of its own.",
            "scheduling": "none — run_driver runs one FIRED pass; triggers (interval/date/quantity/"
            "a-state) belong to the host/rack device (the next spine step).",
        }
