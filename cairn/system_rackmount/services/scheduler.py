"""scheduler — a system service: the physics of WHEN a driver fires.

This is ONE service the system rackmount abstracts (see ../rackmount.py). It is not a device
and does not mount in the rack itself — the *system rackmount* is the rack-mount device; the
scheduler is a system service it surfaces device-independently, alongside others to come. A
device that needs to fire drivers on a cadence asks the rackmount for the ``scheduler`` service
and uses this interface — it never touches the host's clock/cron/timer directly. That is the
device-independence: the OS-specific backing (what pulses a real clock) is swappable behind this
same interface, and no device is coupled to it.

THE SEAM it closes (the spine's ground_loop → its scheduler): ``ground_loop`` runs ONE fired
pass of a driver — resolve to proven-space, write through the owner's gate, emit a run-record.
It deliberately does not schedule. This service is the other half: it decides WHEN, and hands
each fired driver to ground_loop. It introduces no execution authority of its own.

WHAT IT DOES: a driver is MOUNTED with a declarative trigger — one of the four (``interval`` /
``date`` / ``quantity`` / ``state``). A ``tick(now, context)`` is ONE waking pulse: evaluate
every mount's trigger against the moment (and any observed ``context``), collect the ones that
fire into a queue, DRAIN the queue through ``ground_loop.run_driver``, and return a TICK-RECORD
— what fired, what each run did, what held. The tick-record is the legibility surface: a pulse
is itself evidence (LEARNING, not silent RUNNING).

THE TWO WAKING MODES are just what PULSES the tick — the evaluation is one and the same:
  - **scheduled / batched** — a wall-clock cadence pulses ``tick(now)``; interval/date/quantity
    triggers fire and the queue drains (the harvester, the sleep-consolidation graze).
  - **reactive** — a state-entry event pulses ``tick(now, {"state": "PROVEME"})``; a ``state``
    trigger fires the peer waiting on that summons (builder ⟵ BUILDME, tester ⟵ PROVEME).
``tick`` takes ``now`` and ``context`` explicitly, so the firing physics is PROVABLE without a
clock or a live state feed (mirrors ``should_expire``/``run_driver`` taking their moment in).

A FIRED DRIVER THAT CANNOT RUN IS LOUD, NOT SWALLOWED (Law 7, CP2): ground_loop refuses an
unproven method (``UnprovenMethod``) or a non-owner write (``OwnershipError``) by raising. This
service, draining a BATCH, catches each kick-back into a permanent ``refused`` entry in the
tick-record — carrying the error — and keeps draining the rest. One misconfigured driver never
aborts a waking pulse, and never disappears into silence. The trigger still counts as FIRED (it
met its condition); the run outcome is a separate axis — so a broken interval driver fires on
its cadence and records each failure, rather than hot-looping.

FILED EDGES (children of this stone):
  - NO wall-clock loop lives here. ``tick`` is one pulse; the timer/daemon that calls it on a
    cadence (the OS-specific backing the rackmount hides) is a thin wrapper, like sudo_relay's
    ``daemon.py``. Everything UNDER the pulse is proven.
  - Mounts are IN-MEMORY (like ground_loop's registry). A restart-surviving mount-table waits on
    a durable consumer; the scheduler's own drivers are self-hosting once the emit-chokepoint
    gives them an owned target.
  - No priority/fairness across a large fired batch, no retry/backoff on a refused run — v0
    drains in mount order and records each outcome.
"""

from __future__ import annotations

from datetime import datetime

from cairn.ground_loop.loop import GroundLoopDevice

# The four trigger kinds, each with the field(s) it needs to answer "fire now?". interval: every
# N seconds · date: once at/after a moment · quantity: an observed count crossed a threshold ·
# state: a named state was entered (the reactive summons). Behavior as declarative data — a
# trigger is a dict, not code (the operational-driver primitive; MAP.md).
TRIGGER_KINDS = {
    "interval": ("seconds",),
    "date": ("at",),
    "quantity": ("source", "at_least"),
    "state": ("on",),
}


def _validate_trigger(trigger: dict) -> dict:
    """A trigger is refused loudly (CP1) before a driver is mounted — a mount you cannot fire is
    a defect, not a resting state. Returns a normalized copy (a ``date`` iso string → datetime)."""
    if not isinstance(trigger, dict) or "kind" not in trigger:
        raise ValueError("a trigger must be a dict carrying a 'kind' — one of "
                         f"{sorted(TRIGGER_KINDS)} (interval/date/quantity/state)")
    kind = trigger["kind"]
    if kind not in TRIGGER_KINDS:
        raise ValueError(f"unknown trigger kind {kind!r}; the four are {sorted(TRIGGER_KINDS)}")
    missing = [f for f in TRIGGER_KINDS[kind] if f not in trigger]
    if missing:
        raise ValueError(f"a {kind} trigger is missing {missing} — it needs {TRIGGER_KINDS[kind]}")

    normalized = dict(trigger)
    if kind == "date" and isinstance(normalized["at"], str):
        # A JSON-declarative driver carries an iso string; the physics wants a datetime.
        normalized["at"] = datetime.fromisoformat(normalized["at"])
    return normalized


def _trigger_fires(trigger: dict, now: datetime, last_fired: datetime | None,
                   fired_count: int, context: dict) -> bool:
    """The physics of WHEN — a pure decision over (the moment, this mount's history, the observed
    context). No side effects, so it is provable as a table: below the condition → hold; at or
    past it → fire. This is the whole of the 'scheduling'; everything else is plumbing."""
    kind = trigger["kind"]
    if kind == "interval":
        # Fire immediately on first evaluation, then every ``seconds`` thereafter.
        if last_fired is None:
            return True
        return (now - last_fired).total_seconds() >= trigger["seconds"]
    if kind == "date":
        # A one-shot: fire the first tick at or after the moment, and never again.
        return fired_count == 0 and now >= trigger["at"]
    if kind == "quantity":
        # Fire while an observed count is at/over the threshold (drain-a-queue: depth ≥ N).
        return context.get(trigger["source"], 0) >= trigger["at_least"]
    if kind == "state":
        # Reactive: fire when the pulse carries the state this mount waits on (the summons).
        return context.get("state") == trigger["on"]
    raise ValueError(f"unknown trigger kind {kind!r}")  # unreachable — mount validated it


class _Mount:
    """A driver on the scheduler: the ground_loop driver + its trigger + its fire-history. The
    history (last_fired, fired_count) is what makes interval cadence and date one-shot PHYSICS."""

    __slots__ = ("driver", "trigger", "last_fired", "fired_count")

    def __init__(self, driver: dict, trigger: dict) -> None:
        self.driver = driver
        self.trigger = trigger
        self.last_fired: datetime | None = None
        self.fired_count = 0


class SchedulerService:
    """The trigger-firing scheduler as a system service (NOT a device — the system rackmount is
    the device that surfaces this). Its interface is ``mount`` (wire a trigger to a driver) and
    ``tick`` (one waking pulse). It reaches execution ONLY through a ``GroundLoopDevice`` — the
    scheduler decides WHEN, ground_loop runs, db_domain owns."""

    name = "scheduler"

    def __init__(self, ground_loop: GroundLoopDevice) -> None:
        if not isinstance(ground_loop, GroundLoopDevice):
            raise ValueError("the scheduler fires onto a GroundLoopDevice — it runs no driver itself")
        self._loop = ground_loop
        self._mounts: list[_Mount] = []
        self._ticks = 0
        self._last_tick: dict | None = None

    # --- wire a driver under a trigger --------------------------------------

    def mount(self, driver: dict, trigger: dict) -> None:
        """Wire ``trigger`` to ``driver``. The trigger is validated here (loud, CP1); the driver's
        deep validation stays ground_loop's gate — the scheduler requires only that it is a dict
        with a 'name', so the tick-record can name it. Separation of concerns: the scheduler owns
        WHEN, ground_loop owns WHETHER-IT-CAN-RUN."""
        if not isinstance(driver, dict) or "name" not in driver:
            raise ValueError("a mounted driver must be a dict carrying at least a 'name' — "
                             "the scheduler names it in the tick-record; ground_loop gates the rest")
        self._mounts.append(_Mount(driver, _validate_trigger(trigger)))

    # --- one waking pulse ---------------------------------------------------

    def tick(self, now: datetime, context: dict | None = None) -> dict:
        """One waking pulse. Evaluate every mount's trigger against ``now`` and the observed
        ``context``; drain the fired ones through ground_loop; return the tick-record. A mount
        fires when its condition is met — marked FIRED whether the run then succeeds or is kicked
        back, so cadence stays honest and a broken driver can't hot-loop."""
        context = context or {}
        fired: list[dict] = []
        held: list[dict] = []
        for m in self._mounts:
            if _trigger_fires(m.trigger, now, m.last_fired, m.fired_count, context):
                m.last_fired = now
                m.fired_count += 1
                fired.append(self._drain_one(m))
            else:
                held.append({"driver": m.driver["name"], "trigger_kind": m.trigger["kind"]})

        record = {
            "date": now.isoformat(timespec="seconds"),
            "fired": fired,
            "fired_count": len(fired),
            "held": held,  # what was evaluated and did NOT fire — a pulse is evidence, in full
        }
        self._ticks += 1
        self._last_tick = record
        return record

    def _drain_one(self, mount: _Mount) -> dict:
        """Hand one fired driver to ground_loop. A kick-back (unproven method / non-owner write /
        malformed driver) is caught into a permanent ``refused`` entry — loud at this diagnostic
        surface and permanent in the record (Law 7) — never swallowed, and it does not abort the
        rest of the drain (CP2: a failure is a further advance in learning, recorded as one)."""
        try:
            run_record = self._loop.run_driver(mount.driver)
            return {"driver": mount.driver["name"], "trigger_kind": mount.trigger["kind"],
                    "outcome": "ok", "run": run_record}
        except Exception as exc:  # noqa: BLE001 — a batch drainer must record every kick-back, not die on one
            return {"driver": mount.driver["name"], "trigger_kind": mount.trigger["kind"],
                    "outcome": "refused", "error": f"{type(exc).__name__}: {exc}"}

    # --- what the rackmount folds into its state ----------------------------

    def state(self) -> dict:
        """The service's condition — the system rackmount surfaces this in its own state()."""
        return {
            "mounted": len(self._mounts),
            "ticks": self._ticks,
            "last_fired_count": (self._last_tick or {}).get("fired_count"),
            "drivers": [
                {
                    "name": m.driver["name"],
                    "trigger_kind": m.trigger["kind"],
                    "fired_count": m.fired_count,
                    "last_fired": m.last_fired.isoformat(timespec="seconds") if m.last_fired else None,
                }
                for m in self._mounts
            ],
        }

    def settings(self) -> dict:
        """The service's configuration — the system rackmount surfaces this too."""
        return {
            "trigger_kinds": sorted(TRIGGER_KINDS),  # interval / date / quantity / state
            "waking": "two modes, one evaluation — scheduled (a cadence pulses tick(now)) and "
            "reactive (a state-entry event pulses tick(now, {'state': ...})). The pulse source is "
            "the caller's; the trigger kind decides what fires.",
            "wall_clock": "none here — tick is ONE pulse; the OS-specific timer/daemon that calls "
            "it on a cadence is the backing the system rackmount hides (a filed edge), so the "
            "firing physics is proven without a clock.",
            "execution": "ground_loop — the scheduler runs no driver itself; every fired driver "
            "drains through ground_loop.run_driver (which gates proven-space + the owner's write).",
        }
