"""ground_loop — THE HEARTBEAT. One daemon that provides a pulse, and nothing more.

THE MOST BASIC MECHANISM IN CAIRN (converged with Akien 2026-07-18;
``CairnCommons/intentions-not-beside-code/I-heartbeat-probes-and-bus.md``). The ground_loop does NOT
execute, resolve, schedule, route, or write. It BEATS. On each beat it pulses the shim of
every subscribed device; handling the pulse — evaluating probes, firing the due ones —
lives in the SHIM (``cairn/tools/base/shim.py``), never here.

THIS FILE CORRECTS A GOOF. The first ground_loop (584aa74) was a generic driver-EXECUTOR
(``run_driver``: resolve a method against a proven-space registry, run it, write through
db_domain). That collapsed three roles — heartbeat + firing + scheduling — into one device
and lost the property that made the design worth having: *a probe is the same unit no
matter what fires it.* The ground_loop is only the heartbeat; a single daemon structure
everyone else hangs their own handlers on. All state stays on disk (via db_domain), reached
by the devices the shim wakes — the heartbeat itself holds none.

WHY SO SMALL: because a rule enforced by a big mechanism is a big mechanism to get wrong.
The heartbeat's whole contract is "pulse the subscribed shims, in order, and leave a legible
beat-record." Everything a device DOES hangs off its own shim's response to the pulse, where
the device's own data and probes live (Law 6). The heartbeat carries no device's logic.

``beat`` takes ``now`` (and an optional shared ``context``) EXPLICITLY, so the pulse physics
is provable WITHOUT a wall clock — the same discipline as the tester taking its proof-path
and the shim taking its moment. The OS-specific timer/daemon that calls ``beat`` on a real
cadence is a thin wrapper (like sudo_relay's ``daemon.py``, the one part unprovable without
the OS) — a filed edge, not code here.

FILED EDGES (children of this stone, not faked):
  - SUBSCRIPTION by a file in the device's own folder tree: today a device subscribes its
    shim in-process via ``subscribe(shim)``; discovering subscribers by scanning device code
    trees for a probe-declaration file grows when devices are separate OS processes and the
    heartbeat cannot hold in-process references to them.
  - (retired 2026-08-09, ticket ground-loop-writes-its-own-liveness) The wall-clock DAEMON
    that pulses ``beat`` on a cadence now exists as ``__main__.py`` (python3 -m
    cairn.devices.ground_loop) — still the thin wrapper this file stays provable without.
"""

from __future__ import annotations

import os
from datetime import datetime, timezone

from cairn.tools.base.device import BaseDevice
from cairn.devices.ground_loop.discovered import DiscoveredShim
from cairn.devices.ground_loop.discovery import ProbeCache
from cairn.devices.ground_loop.liveness import read_liveness, write_liveness

# The trouble identity a benched device gets. One prefix, here, because two readers need it:
# ``_bench`` writes it and ``_refresh_bench`` parses the device back out of it. A device is
# on the bench exactly when a LIVE ticket by this name exists — there is no second record of
# benching, so the bench cannot disagree with the lane (Law 1).
TROUBLE_PREFIX = "ground-loop-device-"


def liveness_pane_data(now, home=None) -> dict:
    """The LIVENESS pane's DATA (ticket the-ground-loop-pane-shows-its-state) — the read
    face's own answer, untouched, plus the one presentation fact the page needs: WHICH
    loop this reports. The pane RENDERS what the loop wrote; it never derives or caches
    (the ticket's falsifier): verdict, record, age, and any named lack all come from
    ``read_liveness`` — the ruled 5s threshold's one address — so this pane cannot grow
    a second opinion about how stale is dead. Pure: ``now`` is injected, so the
    projection is provable without a clock; the wall-clock wrap happens at declaration
    (``declared_panes``), the last possible moment."""
    return {
        "reports": "the resident singleton's liveness record (instance 0), read from disk "
        "at request time — whatever process serves this page",
        **read_liveness(now, home),
    }


class GroundLoopDevice(BaseDevice):
    """The heartbeat as a device (carries CP1-CP6; reports intention/state/settings). Its one
    capability is ``beat`` — pulse every subscribed shim once. It holds no method registry, no
    DB connection, no execution: firing lives in the shims it pulses.

    ``liveness_home`` is construction-time IDENTITY, not a per-beat concern: the resident
    loop (instance 0) is constructed with its instance dir and every beat touches its
    liveness record there (ticket ground-loop-writes-its-own-liveness — the write is part
    of the pass). Constructed without one, the device is an anonymous in-process heartbeat
    — no device space, no record — which is what every pure-physics proof builds."""

    def __init__(self, device_id: str = "ground_loop", liveness_home=None,
                 discover=None, trouble=None, bus=None) -> None:
        super().__init__()
        self._device_id = device_id
        self._liveness_home = liveness_home
        self._shims: list = []          # the pulse roster: discovered from disk, plus hand-subscribed
        self._beats = 0
        self._last_beat: dict | None = None
        # THE DISK ROSTER (ruled 2026-08-11 — see discovery.py). Injected, so the pure-physics
        # proofs keep beating without a filesystem and a proof can hand a fake tree. ``None``
        # means the pre-ruling behaviour: pulse only what was hand-subscribed.
        self._discover = discover
        # THE BUS THE DISCOVERED SHIMS FIRE ONTO. Handed straight through to each
        # ``DiscoveredShim`` and never touched here: the heartbeat does not post, read, or
        # route — it only makes sure a shim it creates has somewhere to poke. Without it a
        # probe that fires records ``unwired`` (honest, and exactly what two live probes were
        # doing on 2026-08-11 — the trigger was true and there was nowhere to send it).
        self._bus = bus
        self._probe_cache = None        # built lazily; only the real discoverer needs one
        self._discovered: dict = {}     # device_id -> DiscoveredShim, this loop's own
        # THE BENCH — device_id -> the trouble id holding it out. A device that failed is not
        # retried until its ticket is CLEARED, and only the recipient may clear it
        # (trouble.py). The loop never un-benches on its own: that would be the loop deciding
        # a trouble went away, which is exactly what the trouble lane exists to forbid.
        self._trouble = trouble
        self._benched: dict[str, str] = {}
        self._bench_stamp = None        # the trouble store's fingerprint at the last refresh

    @property
    def device_id(self) -> str:
        return self._device_id

    # --- subscribe a device's shim to the beat ------------------------------

    def subscribe(self, shim) -> None:
        """Subscribe ``shim`` to the heartbeat. A shim must answer ``device_id`` and ``on_pulse``
        (the handling lives there — CP1: refuse loudly what cannot be pulsed). Idempotent by
        ``device_id`` — subscribing the same device twice does not double-pulse it."""
        if not hasattr(shim, "on_pulse") or not hasattr(shim, "device_id"):
            raise TypeError("only a shim (with device_id + on_pulse) can subscribe to the heartbeat — "
                            "the ground_loop pulses shims; the shim handles the pulse")
        if any(s.device_id == shim.device_id for s in self._shims):
            return
        self._shims.append(shim)
        # GATE CONTACT (DiagnosticBase): the roster CHANGED — a device joined the beat. Once
        # per device (the idempotent re-subscribe changes nothing and emits nothing). The
        # beat itself never emits: a breadcrumb per pulse is the exact firehose the shim
        # lesson forbids — the heartbeat's crossings are roster changes and pulse FAILURES.
        self.emit("subscribe", pointer=shim.device_id)

    @property
    def subscribers(self) -> list[str]:
        return [s.device_id for s in self._shims]

    # --- the live roster: the nav across the top (web-server child c) --------

    def roster(self) -> dict:
        """The live heartbeat ROSTER — the devices this heartbeat beats to — published at ALL
        times, as the authoritative nav for the web presentation surface (web-server child c).

        The heartbeat already KNOWS its subscribers: it owns the subscription list (Law 6). This
        is that knowledge published as DATA, no new owner and no new state — the roster IS the
        subscription list, plus each device's live wakefulness (its shim's ``running``) so the
        nav can show who is awake. Available before the first beat too (``beats`` 0, the current
        subscribers): you can navigate to a device the moment it subscribes, not only once it has
        been pulsed. A device ABSENT from the roster cannot appear in the nav — honest by
        construction: you navigate to what the heartbeat beats."""
        return {
            "beats": self._beats,
            "devices": [
                {"device": s.device_id, "awake": bool(getattr(s, "running", False))}
                for s in self._shims
            ],
        }

    def shim_for(self, device_id: str):
        """The subscribed shim for ``device_id``, or None. The heartbeat holds its subscribers'
        shims (in-process v0), so a presentation surface can reach a device's page THROUGH the
        heartbeat that beats it — you can only reach what is on the roster. A read accessor, no
        new ownership: the subscription list is already this device's (Law 6). When devices are
        separate OS processes this becomes 'address the shim over the bus', the filed edge."""
        for s in self._shims:
            if s.device_id == device_id:
                return s
        return None

    # --- the disk roster + the bench ----------------------------------------

    def _bench_store_stamp(self):
        """A cheap fingerprint of the trouble store: one ``scandir``, no file reads.

        THE FIRST VERSION OF THIS STATTED THE DIRECTORY, AND THE PROOF KILLED IT. A clear is
        an in-place rewrite of one ticket file (``trouble.py``'s ``_write`` — no temp, no
        rename), so the directory's own mtime does not move when a ticket is cleared. The
        gate was watching the single event it needed to catch and missing it: a device would
        have stayed benched forever after its ticket was cleared, and the beat would have
        looked perfectly healthy while doing it. The fingerprint therefore rides the ENTRIES
        — name, mtime, size — which moves for a raise, a clear, and a hand-edit alike.
        ``None`` means the store could not be read, which never equals a real fingerprint,
        so an unreadable store re-reads rather than freezing the bench."""
        root = getattr(self._trouble, "_root", None)
        if root is None or not root.exists():
            return ()
        try:
            with os.scandir(root) as entries:
                return tuple(sorted(
                    (e.name, e.stat().st_mtime, e.stat().st_size)
                    for e in entries if e.name.endswith(".json")))
        except OSError:
            return None

    def _refresh_bench(self) -> None:
        """Re-read which devices are held out by a LIVE trouble ticket.

        Gated on the store's fingerprint, so an unchanged store costs one ``scandir`` per
        beat rather than a directory of JSON reads per second. The loop reads this list; it
        never writes to it except by raising, and it never removes from it — a device leaves
        the bench when its ticket is CLEARED, which is the recipient's act alone."""
        if self._trouble is None:
            return
        stamp = self._bench_store_stamp()
        if stamp is not None and stamp == self._bench_stamp:
            return
        try:
            live = self._trouble.live()
        except Exception as exc:  # noqa: BLE001 — an unreadable lane must not stop the heartbeat
            self.emit("bench_unreadable", pointer="trouble",
                      values={"error": f"{type(exc).__name__}: {exc}"})
            return
        self._bench_stamp = stamp
        self._benched = {t["id"][len(TROUBLE_PREFIX):]: t["id"]
                         for t in live
                         if str(t.get("id", "")).startswith(TROUBLE_PREFIX)}

    def _bench(self, device_id: str, why: str, detail: dict) -> None:
        """A device failed: raise (or increment) its trouble ticket and hold it out.

        The identity names the DEFECT — *this device fails on the beat* — not the
        occurrence, so a device failing every second produces one ticket with a count,
        never a ticket per beat (trouble.py's damper). Benching in memory immediately means
        the very next beat already skips it, without waiting for the mtime gate."""
        ident = TROUBLE_PREFIX + device_id
        self._benched[device_id] = ident
        if self._trouble is None:
            return
        try:
            self._trouble.raise_trouble(ident, why=why, detail=detail)
        except Exception as exc:  # noqa: BLE001 — the lane failing cannot take the heartbeat with it
            self.emit("bench_unwritable", pointer=ident,
                      values={"error": f"{type(exc).__name__}: {exc}"})

    def _reconcile(self) -> None:
        """Rebuild the pulse roster from DISK — the whole point of the ruling.

        Hand-subscribed shims are left exactly as they are (the web server registers real
        device shims that carry pages), and a discovered device whose name a hand-subscribed
        shim already holds is NOT given a second shim — one device, one shim, or a probe
        fires twice per beat. Everything else on disk gets a ``DiscoveredShim``, refreshed
        with this pass's probes; a device whose folder has vanished leaves the roster."""
        if self._discover is None:
            return
        if self._probe_cache is None:
            self._probe_cache = ProbeCache()
        self._refresh_bench()
        try:
            found = self._discover(cache=self._probe_cache, skip=set(self._benched))
        except Exception as exc:  # noqa: BLE001 — discovery itself failing must not stop the beat
            self.emit("discovery_refused", pointer="disk",
                      values={"error": f"{type(exc).__name__}: {exc}"})
            return
        hand_held = {s.device_id for s in self._shims
                     if s.device_id not in self._discovered}
        for device_id, entry in found.items():
            if entry.get("benched"):
                continue
            if entry["failures"]:
                self._bench(device_id,
                            why=f"the {device_id} device's probe folder does not import, so its "
                                "watches cannot be fired; the heartbeat has held it out until "
                                "this is fixed and the ticket cleared",
                            detail={"folder": entry["folder"], "failures": entry["failures"]})
                continue
            if device_id in hand_held:
                continue      # a real shim already fronts this device — do not double-pulse it
            shim = self._discovered.get(device_id)
            if shim is None:
                shim = DiscoveredShim(device_id, entry["folder"], bus=self._bus)
                self._discovered[device_id] = shim
                self._shims.append(shim)
                self.emit("discovered", pointer=device_id,
                          values={"folder": entry["folder"], "probes": len(entry["probes"])})
            shim.set_probes(entry["probes"], entry["folder"])
        # A device that left disk, or that just got benched, leaves the roster. Its shim is
        # DROPPED rather than emptied so its crossing-memory dies with it: a probe re-armed
        # after a fix is a fresh watch, not one resuming a line it no longer remembers.
        gone = [d for d in self._discovered
                if d not in found or d in self._benched or found[d].get("benched")]
        for device_id in gone:
            shim = self._discovered.pop(device_id)
            self._shims = [s for s in self._shims if s is not shim]
            self.emit("undiscovered", pointer=device_id,
                      values={"reason": "benched" if device_id in self._benched
                              else "probes folder no longer on disk"})

    # --- the one capability: one beat ---------------------------------------

    def beat(self, now, context: dict | None = None) -> dict:
        """One beat: pulse every subscribed shim once, in order, and return a BEAT-RECORD — what
        was pulsed and what each pulse did. A shim that raises before its own batch-safe firing
        becomes a loud, permanent entry and does NOT stop the beat reaching the others (CP2,
        Law 7). The record is the legibility surface: a beat is evidence — a record, never a
        silent ``RUNNING`` — so the heartbeat is observable by construction. (This line used to name a
        node state as the alternative to silent RUNNING; that state was dissolved 2026-07-30
        by ticket watchme-emits-a-probe. EVIDENCE is what a beat actually yields, and was
        always the point.)"""
        context = context or {}
        # THE ROSTER IS READ BEFORE IT IS PULSED, every pass (ruled 2026-08-11). A probe file
        # written one second ago is fired by this beat; one deleted one second ago is not.
        self._reconcile()
        pulses: list[dict] = []
        for shim in list(self._shims):
            try:
                pulses.append(shim.on_pulse(now, context))
            except Exception as exc:  # noqa: BLE001 — one shim failing cannot stop the heartbeat
                error = f"{type(exc).__name__}: {exc}"
                pulses.append({"device": shim.device_id, "outcome": "refused", "error": error})
                # GATE CONTACT (DiagnosticBase): a pulse FAILED — per anomaly, never per
                # beat (a healthy beat is silent; its record already returns to the caller).
                # The error rides the values whole: complete on first pass, no re-run to
                # gather what already happened.
                self.emit("pulse_refused", pointer=shim.device_id,
                          values={"beat": self._beats + 1, "error": error})
                # AND THE DEVICE COMES OFF THE BEAT until someone clears its ticket. A shim
                # whose pulse raises is broken at the device level, and re-entering it once a
                # second buys nothing but a bigger count. (A shim that merely had a probe
                # raise never reaches here — BaseShim.on_pulse already isolates per probe, so
                # arriving in this branch means the shim itself failed.)
                self._bench(shim.device_id,
                            why=f"the {shim.device_id} device's shim raised on the heartbeat "
                                "pulse, so none of its watches can fire; the heartbeat has "
                                "held it out until this is fixed and the ticket cleared",
                            detail={"beat": self._beats + 1, "error": error})
        record = {
            "beat": self._beats + 1,
            "date": str(now),
            "pulsed": self.subscribers,
            "pulses": pulses,
        }
        self._beats += 1
        self._last_beat = record
        # THE LIVENESS TOUCH (ticket ground-loop-writes-its-own-liveness): a beat IS a
        # touch — last-run is THIS beat's injected now, state is the device's own state()
        # surface after the pass, pid is this process. Atomic, in the loop's own device
        # space, only when the device HAS one (see __init__). A failed write raises loudly:
        # a shim failing cannot stop the beat, but the loop failing to write its own record
        # is the loop's own fault, and swallowing it would leave a stale stamp lying about
        # a loop that thinks it is running (Law 7 at a record of truth).
        if self._liveness_home is not None:
            write_liveness(now, self.state(), os.getpid(), self._liveness_home)
        return record

    # --- the declared pane: the liveness record, rendered not derived --------

    def declared_panes(self) -> list[dict]:
        """The ground loop's one pane (ticket the-ground-loop-pane-shows-its-state): the
        LIVENESS record — last run, state, pid, LIVE/DEAD at the ruled 5s threshold — as
        every device gets a page: a declared pane the base shim carries, never a route or
        a port. The handler is ``liveness_pane_data`` wrapped with the wall clock here, at
        declaration — the projection itself stays pure and provable. The handler takes no
        ``home``: the pane reports the RESIDENT singleton's record (instance 0) wherever
        this device object lives, because liveness is the resident loop's owned fact and
        the page is a view of it, not of the process serving the page."""
        return [{
            "kind": "liveness",
            "label": "Liveness",
            "handler": lambda: liveness_pane_data(datetime.now(timezone.utc).astimezone()),
        }]

    # --- Form v0 #2 surface -------------------------------------------------

    def intention(self) -> dict:
        return {
            "what": "The heartbeat — one daemon that provides a pulse, and nothing more. On each "
            "beat it pulses the shim of every subscribed device; the handling (firing due "
            "probes) lives in the shim, not here.",
            "why": "A single daemon structure everyone else hangs their own handlers on. Keeping "
            "the heartbeat to ONLY a pulse means a probe is the same unit no matter what fires "
            "it, and no device's logic rots inside the beat — the goof (an executor here) collapsed "
            "three roles into one and lost that.",
        }

    def state(self) -> dict:
        return {
            "beats": self._beats,
            "subscribers": self.subscribers,
            "last_pulsed_count": len((self._last_beat or {}).get("pulsed", [])),
        }

    def settings(self) -> dict:
        return {
            "does": "pulse subscribed shims, in order; leave a beat-record",
            "does_not": "execute, resolve, schedule, route, or write — firing lives in the shim; "
            "durable state lives in db_domain, reached by the devices the shim wakes",
            "cadence": "none here — beat takes 'now' explicitly, so the pulse is provable without a "
            "clock; the wall-clock backing is __main__.py (python3 -m cairn.devices.ground_loop), the thin "
            "wrapper that beats once per second (ruled 2026-07-30)",
            "liveness": "constructed with its instance home (the runner does), every beat writes "
            "~/.cairn/devices/ground_loop/0/liveness.json atomically — last-run, state, pid; the "
            "read face liveness.read_liveness answers LIVE/DEAD at the ruled 5s threshold (Law 6: "
            "liveness is this device's owned fact, read, never scanned from the process table)",
            "subscription": "in-process via subscribe(shim); file-in-the-device's-tree discovery is "
            "a filed edge for when devices are separate OS processes",
            "roster": "publishes roster() at all times — the devices it beats to, each with live "
            "wakefulness — as the nav for the web presentation surface (web-server child c); no new "
            "owner, it IS the subscription list this device already owns (Law 6)",
        }
