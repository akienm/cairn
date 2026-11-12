"""The bus process — one per cairn instance, hosting every shim (ticket 48519f4789b1).

Until this file, every command built its own ``BusDevice`` and its own shims in its own
process: two device commands were two rings, so mail posted by one was a db round-trip away
from the other, and ``cairn librarian show status`` paid a private beat to wire a roster that
died with it (89.3s, measured 2026-09-06). Now one process holds the ring and the shims, and
every caller speaks to it over a unix socket through ``cairn.tools.bus_client.remote``.

THE ADDRESS. ``<home>/bus.sock`` (mode 0600 — one box, one user, the file mode is the gate)
and ``<home>/bus.lock``, where home is ``CAIRN_BUS_HOME`` else the bus's instance folder
``~/.cairn/devices/cairn/machines/bus/0`` (the instance segment is never optional).
Where Python has no AF_UNIX (Windows, measured 2026-11-04 on akiendell) or with ``serve
--tcp``, the local door is a loopback port the kernel picks, written with a per-start key to
``<home>/bus.port`` (the key is the gate a file mode cannot be on a port). The box-to-box door
is TLS on the LAN port, both ends pinned (``cairn.tools.bus_client.tls``), open by default
only on a home with a box identity, and answering only ``LAN_OPS``. Ticket 5183005fa134.

THE CLAIM. ``fcntl.flock(LOCK_EX|LOCK_NB)`` on the lock file — the shape of
``ground_loop/guard.py claim_singleton``, written again here and cited, never imported (RULE 1:
guard is the ground loop's internal); on Windows, msvcrt's non-blocking lock on its first byte.
A refused claim exits 3, the unit's SuccessExitStatus. A stale socket (or ``bus.port``) from a
dead process is removed only AFTER the claim is won.

THE WIRE. One JSON object per line each way. Every request carries ``op`` and ``root`` (the
caller's class root). Ops: ``call``, ``hold``, ``verbs``, ``flush``, ``stats``, ``shutdown``.
Any exception answers ``{ok: false, error}`` — loud, never empty (Law 7).

THE BUS SERVES THE CODE THAT ASKS (decision 4). A request from a different class root, or one
arriving after any ``*.py`` under this root changed, is answered ``{ok: false, stale: true}``
and nothing else; the client shuts this process down and starts one from its own root.
"""
from __future__ import annotations

import faulthandler
import hmac
import importlib
import json
import os
import platform
import secrets
import signal
import socketserver
import struct
import sys
import threading
import time
import traceback
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

try:
    import resource
except ImportError:   # Windows: no getrusage, so a stop line's maxrss is null
    resource = None

from cairn.devices.cairn.machines.bus.bus import BusDevice
from cairn.tools.base.diagnostic import DiagnosticBase
from cairn.tools.base import testing_mark

try:                      # the claim's two spellings: flock on Linux, a byte lock on Windows
    import fcntl
except ImportError:       # pragma: no cover — Windows
    fcntl = None

# cairn/devices/cairn/machines/bus/server.py → five parents up is the class root.
ROOT = Path(__file__).resolve().parents[5]
EXIT_HELD = 3
DEFAULT_HOME = Path("~/.cairn/devices/cairn/machines/bus/0")
# Akien 2026-10-18: "the bus unable to wake a shim for 600 seconds sends trouble ticket."
STOOD_S = 600

# The bus methods a caller may reach through ``call``. Named, not getattr-anything: the
# socket is the bus's public interface, and a private method is not on it (RULE 1).
CALLABLE = ("post", "read", "count", "request", "undelivered", "record_delivery",
            "digest", "list", "toggle")


def bus_home(home: str | Path | None = None) -> Path:
    if home is not None:
        return Path(home).expanduser()
    env = os.environ.get("CAIRN_BUS_HOME")
    return Path(env).expanduser() if env else DEFAULT_HOME.expanduser()


def _age_s(date, now: datetime) -> float | None:
    """Seconds since an envelope's ``date`` (naive local isoformat at post; the store may hand
    back a datetime), or None when it cannot be read."""
    try:
        posted = date if isinstance(date, datetime) else datetime.fromisoformat(str(date))
    except (TypeError, ValueError):
        return None
    if posted.tzinfo is not None:
        posted = posted.astimezone().replace(tzinfo=None)
    return (now - posted).total_seconds()


def code_stamp(root: Path = ROOT) -> float:
    """The newest mtime over every ``*.py`` under ``<root>/cairn`` and ``<root>/bin``
    (measured 2026-10-02: 373 files, 3ms). ``bin`` holds extensionless python scripts too,
    so every regular file there counts."""
    newest = 0.0
    for top in (root / "cairn", root / "bin"):
        for dirpath, dirnames, filenames in os.walk(top):
            dirnames[:] = [d for d in dirnames if d != "__pycache__"]
            for name in filenames:
                if top.name == "cairn" and not name.endswith(".py"):
                    continue
                try:
                    newest = max(newest, os.stat(os.path.join(dirpath, name)).st_mtime)
                except OSError:
                    continue
    return newest


class _InFlight(DiagnosticBase):
    """The requests this process is answering (ticket 1029d5146152). A shutdown that arrives
    while any are held DRAINS: it answers at once, keeps serving (stale refusal suspended, so a
    newer caller is served rather than sent to spawn a bus that cannot claim the lock), and
    exits at the first moment none is held, or at the cap. Measured 2026-11-12: a replace
    killed a 14-minute constrain ask because the daemon handler threads died with the process."""

    def __init__(self) -> None:
        super().__init__()
        self._cv = threading.Condition()
        self._held: dict[int, str] = {}
        self._next = 0
        self.deadline: float | None = None

    def enter(self, op: str) -> int:
        with self._cv:
            self._next += 1
            self._held[self._next] = op
            return self._next

    def leave(self, ticket: int) -> None:
        with self._cv:
            self._held.pop(ticket, None)
            self._cv.notify_all()

    @property
    def count(self) -> int:
        with self._cv:
            return len(self._held)

    @property
    def draining(self) -> bool:
        return self.deadline is not None

    def begin(self, cap: float) -> bool:
        """Start the drain; True only for the call that started it (a second shutdown joins)."""
        with self._cv:
            if self.deadline is not None:
                return False
            self.deadline = time.monotonic() + cap
            return True

    def wait(self) -> list[str]:
        """Block until nothing is held or the cap passes; the ops still held when it returns."""
        with self._cv:
            while self._held:
                left = self.deadline - time.monotonic()
                if left <= 0:
                    break
                self._cv.wait(left)
            return list(self._held.values())


def _drain_cap() -> float:
    """CAIRN_BUS_DRAIN_S, default 600: the inference-call limit (outline 5.5.3.9)."""
    try:
        return float(os.environ.get("CAIRN_BUS_DRAIN_S", "600"))
    except ValueError:
        return 600.0


class BusProcess(DiagnosticBase):
    """The ring, the held shims, and the per-shim locks — everything one request touches."""

    def __init__(self, bus: BusDevice) -> None:
        from cairn.tools.bus_client.roster import DeviceRoster

        super().__init__()
        self.bus = bus
        self.roster = DeviceRoster(bus)
        self.stamp = code_stamp()
        self.in_flight = _InFlight()
        # Guards the roster lookup and shim construction only, never _wire: holding it while
        # _wire waits on a busy shim's lock deadlocked that shim's own handler and stalled
        # every other wake on the bus (ticket 445e66f32ba0, measured 2026-10-18).
        self._hold_lock = threading.RLock()
        # One RLock per held shim (decision 8): a slow answer blocks only its own device's
        # traffic, and a handler that posts to itself re-enters on the same thread.
        self._shim_locks: dict[str, threading.RLock] = {}
        # A POKE NEVER WAITS ON ANOTHER SHIM'S LOCK (ticket c2036433beaf). Measured 2026-10-17
        # by py-spy: a handler holding codemother's lock posted to inference_domain while a
        # handler holding inference_domain's posted a reply to codemother — each blocked on the
        # other's lock, and the asker hung the 900s client timeout. Now a poke that finds its
        # shim's lock held leaves the envelope in that shim's queue and returns; whoever holds
        # the lock drains the queue before letting go, and a request() made under a held lock
        # drains its own thread's queues while it waits for the reply.
        self._queues: dict[str, deque] = {}
        self._hooks: dict[str, object] = {}
        self._local = threading.local()
        self._by_spec: dict[str, object] = {}
        self._wired: set[str] = set()
        # Envelopes already raised as standing past STOOD_S (ticket b30069239480), so each
        # is reported once per bus life; a restart re-raises the backlog once, and the trouble
        # device folds that into the same identity's count.
        self._stood_reported: set[str] = set()
        # MAIL ARRIVES, AND WHAT CANNOT MARKS ITSELF (ticket 7cb1989e7825): a personal post
        # nobody is wired to take wakes its addressee's shim here, in the same call, or comes
        # back to its sender. Installed at construction so no post can slip past it.
        bus.set_no_receiver(self.no_receiver)
        bus.set_delivery_wrapper(self._locked_hook)
        bus.set_while_waiting(self._serve_held)

    # --- holding ----------------------------------------------------------------------

    def _wire(self, shim) -> None:
        """Wire a held shim's delivery onto the ring — ``_wire_delivery``, the one step of a
        first pulse that is about mail — once; the poke it registers is wrapped in that
        shim's own lock at registration (``_locked_hook``). Not a pulse (decision 12): a pulse fires probes and stamps snapshots."""
        if self._is_wired(shim.device_id):
            return
        with self._holding(shim.device_id):
            # Re-read under the shim's own lock: two wakes can both pass the check above, and
            # only the first may wire (ticket 445e66f32ba0).
            if self._is_wired(shim.device_id):
                return
            shim._wire_delivery()
            self._wired.add(shim.device_id)

    def _locked_hook(self, device_id: str, hook):
        """The bus's delivery wrapper: a shim's poke runs under its own lock, from the moment
        the shim registers it — never raw, not even while its wiring is still starting the
        device (ticket 7778e24dd82e)."""
        if getattr(hook, "_bus_locked", False):
            return hook
        self._lock_for(device_id)
        self._hooks[device_id] = hook

        def locked(envelope, _id=device_id):
            self._queues[_id].append(envelope)
            self._drain(_id)
        locked._bus_locked = True
        return locked

    def _is_wired(self, device_id: str) -> bool:
        return device_id in self._wired and device_id in self.bus._delivery_hooks

    # --- one shim, one thread at a time ---------------------------------------------------

    def _held(self) -> list:
        """The device ids whose locks this thread holds, innermost last."""
        stack = getattr(self._local, "held", None)
        if stack is None:
            stack = self._local.held = []
        return stack

    def _lock_for(self, device_id: str) -> threading.RLock:
        self._queues.setdefault(device_id, deque())
        return self._shim_locks.setdefault(device_id, threading.RLock())

    @contextmanager
    def _holding(self, device_id: str):
        """Hold ``device_id``'s lock, blocking — but while waiting, keep serving the queues of
        the shims this thread already holds, so the holder it waits on can be answered."""
        lock = self._lock_for(device_id)
        while not lock.acquire(timeout=0.05):
            self._serve_held()
        held = self._held()
        held.append(device_id)
        try:
            yield
        finally:
            held.pop()
            lock.release()
        self._drain(device_id)

    def _drain(self, device_id: str) -> None:
        """Run the queued pokes for ``device_id`` if its lock is free to this thread; if another
        thread holds it, return — that holder drains before it lets go. The outer loop re-reads
        the queue after release, so a poke queued between the last pop and the release is
        never stranded."""
        lock = self._lock_for(device_id)
        queue = self._queues[device_id]
        while queue:
            if not lock.acquire(blocking=False):
                return
            held = self._held()
            held.append(device_id)
            try:
                while queue:
                    try:
                        envelope = queue.popleft()
                    except IndexError:
                        break
                    hook = self._hooks.get(device_id)
                    if hook is None:
                        continue
                    try:
                        hook(envelope)
                    except Exception as exc:  # noqa: BLE001 — as post() reports a failed hook
                        self.bus.emit("delivery_failed", pointer=envelope.get("id"), values={
                            "addressee": device_id, "error": f"{type(exc).__name__}: {exc}",
                        })
            finally:
                held.pop()
                lock.release()

    def _serve_held(self) -> None:
        """Drain every queue whose lock this thread holds — the bus calls this from inside
        request() while it waits for a reply (``set_while_waiting``)."""
        for device_id in list(dict.fromkeys(self._held())):
            self._drain(device_id)

    def hold_name(self, name: str, *, wire: bool = True):
        """The shim that answers to ``name``, held here. ``wire`` holds it for MAIL (its
        delivery wired); a shim held only to answer a verb line is held cold — wiring
        announces its menu, which wakes the device, and a cold ``list`` wakes nothing (decision 12)."""
        with self._hold_lock:
            shim = self.roster.shim_for(name)
        if shim is None:
            raise LookupError(
                f"no shim answers to {name!r} — a device's bus presence IS "
                f"cairn/devices/{name}/shim.py on disk, and nothing was discovered there")
        if wire:
            self._wire(shim)
        return shim

    def hold_class(self, spec: str, *, wire: bool = True):
        """``module:Class`` — a shim class named by its address, constructed here, never in the
        caller. The device id it answers to is the class's own; one shim per id."""
        with self._hold_lock:
            shim = self._by_spec.get(spec)
            if shim is None:
                module, _, cls_name = spec.partition(":")
                cls = getattr(importlib.import_module(module), cls_name)
                shim = cls(bus=self.bus)
                if shim.device_id in self.roster.held:
                    shim = self.roster.shim_for(shim.device_id)
                else:
                    self.roster.hold(shim)
                self._by_spec[spec] = shim
        if wire:
            self._wire(shim)
        return shim

    # --- mail nobody was wired to take (ticket 7cb1989e7825) ---------------------------

    def _still_waiting(self, envelope: dict) -> bool:
        return envelope["id"] in self.bus._pending

    def no_receiver(self, envelope: dict) -> None:
        """Wake the addressee's shim for ``envelope``, or return the letter to its sender.

        Waking is ``hold_name(wire=True)``: wiring drains the shim's mailbox, this envelope
        included, through ``_check_mail`` — the same take every wired post gets. Mail is the
        ONLY thing that wakes a device here; nobody mailed is never held. If no shim answers,
        or the shim could not take it (a shim that cannot wake a device), the bus bounces once
        and the envelope leaves transit. A returned letter that cannot land is never bounced
        again: the bus raises the addressee's mail trouble itself and receipts the bounce. A
        testing-marked bounce that cannot land is test debris and is disposed of, never raised
        (ticket b3386f431ae3; 71d1bbfa98b0 D2)."""
        if not self._still_waiting(envelope):
            return
        to = envelope.get("addressee") or ""
        body = envelope.get("body") or {}
        reason = None
        try:
            self.hold_name(to, wire=True)
        except LookupError as exc:
            reason = str(exc)
        if not self._still_waiting(envelope):
            return
        if reason is None:
            reason = f"{to}'s shim could not take the envelope — it cannot wake a device to receive it"
        if body.get("is_bounce"):
            if testing_mark.mark_of(body) is not None:
                self._dispose_test_bounce(envelope, reason)
            else:
                self._raise_undeliverable_bounce(envelope, reason)
        else:
            self._return_to_sender(envelope, reason)

    def _return_to_sender(self, envelope: dict, reason: str) -> None:
        to = envelope.get("addressee") or ""
        sender = envelope.get("sender") or ""
        body = {"is_bounce": True, "reason": reason,
                "original_verb": envelope.get("verb", ""), "original_addressee": to,
                "original_sender": sender, "trouble": f"mail-{to}-has-no-receiver"}
        # CONTAGION (ticket b3386f431ae3; 71d1bbfa98b0): a bounce born of a test's letter
        # carries the test's mark, so wherever it lands it reads as test debris.
        mark = testing_mark.mark_of(envelope.get("body") or {})
        if mark is not None:
            body[testing_mark.FIELD] = mark
        self.bus.post(
            sender="bus", to=sender, channel="personal", why=f"bounced: {reason}",
            body=body, reply_to=envelope["id"])
        self.bus.record_delivery(envelope["id"], to=to, by="bus-bounced-no-receiver")

    def _dispose_test_bounce(self, bounce: dict, reason: str) -> None:
        """A testing-marked bounce nobody can take is test debris (ticket b3386f431ae3;
        71d1bbfa98b0 D2): logged and receipted, never raised into the live trouble lane."""
        body = bounce.get("body") or {}
        mark = testing_mark.mark_of(body) or {}
        sender = bounce.get("addressee") or ""
        emit = getattr(self.bus, "emit", None)
        if callable(emit):
            emit("test_bounce_disposed", pointer=bounce["id"], values={
                "bounce_envelope": bounce["id"], "sender": sender,
                "receiver": body.get("original_addressee") or "",
                "test": mark.get("test", ""), "reason": reason})
        self.bus.record_delivery(bounce["id"], to=sender, by="bus-test-bounce-disposed")

    def _raise_undeliverable_bounce(self, bounce: dict, reason: str) -> None:
        body = bounce.get("body") or {}
        sender = bounce.get("addressee") or ""
        receiver = body.get("original_addressee") or ""
        identity = body.get("trouble") or f"mail-{receiver}-bounced"
        self.bus.raise_trouble(
            identity,
            why=f"bounced: {body.get('reason', '?')} — and the sender {sender} could not take "
                f"the returned letter ({reason})",
            detail={"sender": sender, "receiver": receiver, "bounce": True,
                    "envelope": bounce.get("reply_to"), "bounce_envelope": bounce["id"]})
        self.bus.record_delivery(bounce["id"], to=sender, by="bus-bounce-undeliverable")

    def return_the_backlog(self) -> dict:
        """One pass, at start, over the envelopes standing undelivered when this process came
        up: each takes the path a fresh post takes. An event (the start), never a beat."""
        seen = woken = 0
        for envelope in self.bus.undelivered(limit=1_000_000):
            if envelope.get("reply_to") and not (envelope.get("body") or {}).get("is_bounce"):
                continue
            seen += 1
            try:
                self.no_receiver(envelope)
            except Exception as exc:  # noqa: BLE001 — one envelope cannot stop the pass
                self.bus.emit("no_receiver_failed", pointer=envelope.get("id"),
                              values={"error": f"{type(exc).__name__}: {exc}"})
            else:
                woken += 1
        return {"seen": seen, "passed": woken}

    # --- ops --------------------------------------------------------------------------

    def op_call(self, req: dict):
        method = req.get("method")
        if method not in CALLABLE:
            raise ValueError(f"{method!r} is not on the bus's interface — one of {CALLABLE}")
        return {"ok": True, "json": getattr(self.bus, method)(**(req.get("kwargs") or {}))}

    def op_hold(self, req: dict):
        if req.get("shim"):
            self.hold_class(req["shim"])
        for name in req.get("devices") or []:
            self.hold_name(name)
        return {"ok": True, "held": self.roster.held}

    def op_verbs(self, req: dict):
        shim = (self.hold_class(req["shim"], wire=False) if req.get("shim")
                else self.hold_name(req["device"], wire=False))
        with self._holding(shim.device_id):
            result = shim.resolve(list(req.get("verbs") or []))
        return {"ok": True, "exit": int(result.get("exit", 1)), "text": result.get("text", ""),
                "json": result.get("data")}

    def op_flush(self, _req: dict):
        flushed = self.bus.flush()
        flushed["stood"] = self.report_stood()
        return {"ok": True, "json": flushed}

    # --- mail that stands (ticket b30069239480) ----------------------------------------

    def _dispose_test_mail(self, envelope: dict, age: float | None) -> None:
        """Testing-marked mail standing STOOD_S is test debris (ticket 6357c2eeff7c; 71d1bbfa98b0
        D2): logged and receipted, never raised into the live trouble lane."""
        mark = testing_mark.mark_of(envelope.get("body") or {}) or {}
        to = envelope.get("addressee") or ""
        emit = getattr(self.bus, "emit", None)
        if callable(emit):
            emit("test_mail_disposed", pointer=envelope["id"], values={
                "envelope": envelope["id"], "sender": envelope.get("sender") or "",
                "addressee": to, "test": mark.get("test", ""),
                "age_s": None if age is None else int(age)})
        self.bus.record_delivery(envelope["id"], to=to, by="bus-test-mail-disposed")

    def report_stood(self, now: datetime | None = None) -> int:
        """Raise one trouble for each personal envelope standing undelivered STOOD_S or more,
        once per envelope. Rides the flush because the flush is the one op the beat sends the
        bus process. It REPORTS and nothing else: no wake or delivery is retried here, so no
        message ever waits on a tick to be delivered (bus clause 5). Identity is per
        addressee — many stuck letters to one name are one trouble with a count. An envelope
        whose date cannot be read is raised too, with its age unknown, never skipped (Law 7).
        Testing-marked mail that stands is test debris: disposed of, never raised (6357c2eeff7c)."""
        now = now or datetime.now()
        raised = 0
        for envelope in self.bus.undelivered(limit=1_000_000):
            if envelope["id"] in self._stood_reported:
                continue
            age = _age_s(envelope.get("date"), now)
            if age is not None and age < STOOD_S:
                continue
            if testing_mark.mark_of(envelope.get("body") or {}):
                self._dispose_test_mail(envelope, age)
                self._stood_reported.add(envelope["id"])
                continue
            to = envelope.get("addressee") or ""
            sender = envelope.get("sender") or ""
            held = to in self.roster.held
            self.bus.raise_trouble(
                f"mail-{to}-stood-{STOOD_S}s",
                why=f"mail to {to} from {sender} has stood undelivered "
                    f"{'an unknown time' if age is None else f'{int(age)}s'} (over {STOOD_S}s): "
                    f"{envelope.get('why', '')!r}"
                    f"{'' if held else f' — no shim for {to} is held'}",
                detail={"envelope": envelope["id"], "sender": sender, "addressee": to,
                        "why": envelope.get("why", ""), "verb": envelope.get("verb", ""),
                        "reply_to": envelope.get("reply_to"), "date": str(envelope.get("date")),
                        "age_s": None if age is None else int(age), "held": held})
            self._stood_reported.add(envelope["id"])
            raised += 1
        return raised

    def op_stats(self, _req: dict):
        bus = self.bus
        return {"ok": True, "json": {
            "pid": os.getpid(), "root": str(ROOT), "table": bus._table,
            "posted": bus._posted, "delivered": bus._delivered, "db_reads": bus.db_reads,
            "ring_depth": bus.ring_depth,
            "receipts": [r["envelope"] for r in list(bus._ring_receipts)],
            "held": self.roster.held,
            # Where each held shim's class was loaded from — the one fact about a hosted
            # object a caller across the socket can check (the shim.py on disk IS the device's
            # bus presence; the three-faces proof reads it here).
            "shims": {name: getattr(sys.modules.get(type(self.roster.shim_for(name)).__module__),
                                    "__file__", None)
                      for name in self.roster.held}}}

    def answer(self, req: dict, *, in_process: bool = False, remote: bool = False) -> dict:
        # A request from code this process hosts runs this process's code by definition, so
        # it is never stale against it; only a caller across the socket can be. A caller on
        # ANOTHER BOX (``remote``) runs its own box's code: its root names a different
        # checkout by construction, and its replace-on-stale cannot reach this process, so
        # the stale answer would be a refusal nobody can act on (ticket 5183005fa134).
        root = req.get("root")
        # A DRAINING bus serves everyone: refusing stale would send the caller to replace a
        # bus that is already going, and its spawn would lose the lock (ticket 1029d5146152).
        local = not in_process and not remote and not self.in_flight.draining
        if local and root is not None and str(root) != str(ROOT):
            return {"ok": False, "stale": True, "root": str(ROOT)}
        if (local and req.get("op") not in ("shutdown", "flush")
                and code_stamp() > self.stamp):
            return {"ok": False, "stale": True, "root": str(ROOT)}
        handler = getattr(self, f"op_{req.get('op')}", None)
        if handler is None:
            return {"ok": False, "error": f"no op {req.get('op')!r} on the bus process"}
        try:
            return handler(req)
        except Exception as exc:  # noqa: BLE001 — every failure is an answer, never a hang
            return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


class _Handler(DiagnosticBase, socketserver.StreamRequestHandler):
    """One JSON line in, one out. ``admit`` may refuse a request before it is answered;
    ``reply_to`` answers an admitted one — the two seams the loopback and LAN doors fill."""

    def handle(self) -> None:
        line = self.rfile.readline()
        if not line:
            return
        try:
            req = json.loads(line)
        except ValueError as exc:
            self._send({"ok": False, "error": f"not one JSON line: {exc}"})
            return
        if not isinstance(req, dict):
            self._send({"ok": False, "error": "a request is one JSON object"})
            return
        refused = self.admit(req)
        if refused is not None:
            self._send(refused)
            return
        if req.get("op") == "shutdown":
            # A shutdown ENDS the process whatever the flush does: a bus that cannot stop
            # is a stale bus nothing can replace (measured 2026-10-03 — one Decimal in the
            # ring failed every flush, so every shutdown, so every caller after it).
            stop = getattr(self.server, "stop", None)
            if stop is not None:
                stop.set("verb", {"op": "shutdown", **self.caller()})
            held = self.server.process.in_flight
            if held.count or held.draining:
                # Requests are in flight: answer now, serve on, exit when they are answered
                # or at the cap (ticket 1029d5146152).
                cap = _drain_cap()
                if held.begin(cap):
                    threading.Thread(target=self._drain_then_stop, daemon=True).start()
                self._send({"ok": True, "draining": held.count, "drain_s": cap})
                return
            reply = final_flush(self.server.process.bus, self.server.home)
            self._send(reply)
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        if req.get("op") == "stats":
            self._send(self.reply_to(req))
            return
        held = self.server.process.in_flight
        ticket = held.enter(str(req.get("op")))
        try:
            reply = self.reply_to(req)
        finally:
            held.leave(ticket)
        self._send(reply)

    def _drain_then_stop(self) -> None:
        cut = self.server.process.in_flight.wait()
        if cut:
            print(f"bus: drain cut {len(cut)} request(s): {', '.join(cut)}", flush=True)
        try:
            final_flush(self.server.process.bus, self.server.home)
        finally:
            self.server.shutdown()

    def admit(self, req: dict) -> dict | None:
        return None

    def caller(self) -> dict:
        """Who is asking (ticket 73c58a1dcad7, D5). On the unix door the kernel's peer
        credentials (SO_PEERCRED on Linux) name the asking process and its command line; a TCP
        door names the peer address. Read through the request this handler already holds, so
        the server never imports socket."""
        if isinstance(self.client_address, tuple):
            return {"peer": f"{self.client_address[0]}:{self.client_address[1]}"}
        if not sys.platform.startswith("linux"):
            return {"caller_pid": None}
        try:   # SOL_SOCKET 1, SO_PEERCRED 17: struct ucred {pid, uid, gid}
            pid, _uid, _gid = struct.unpack("3i", self.request.getsockopt(1, 17, 12))
        except OSError as exc:
            return {"caller_pid": None, "caller_error": f"{type(exc).__name__}: {exc}"}
        try:
            cmd = Path(f"/proc/{pid}/cmdline").read_bytes().replace(b"\0", b" ").decode(
                errors="replace").strip()
        except OSError:
            cmd = None
        return {"caller_pid": pid, "caller_cmd": cmd}

    def reply_to(self, req: dict) -> dict:
        return self.server.process.answer(req)

    def _send(self, reply: dict) -> None:
        self.wfile.write((json.dumps(reply, default=str) + "\n").encode())
        self.wfile.flush()


class _LoopHandler(_Handler):
    """The loopback door (no AF_UNIX, or ``serve --tcp``). A loopback port has no file mode to
    gate it — any local account can dial 127.0.0.1 — so the gate moves to a key: random per
    start, written beside the port in ``<home>/bus.port``, which carries the home folder's
    own permissions. A request without it is refused before it is read further."""

    def admit(self, req: dict) -> dict | None:
        key = req.pop("key", None)
        if not isinstance(key, str) or not hmac.compare_digest(key, self.server.key):
            return {"ok": False, "error": "the bus key is wrong or missing — read it from "
                                          f"{self.server.home}/bus.port"}
        return None


# What a pinned box across the LAN may ask. Not shutdown, hold or flush: those govern THIS
# box's process and its ring, and the box that runs it is the one that owns them (Law 6).
LAN_OPS = ("call", "stats", "verbs")


class _LanHandler(_Handler):
    """The box-to-box door: TLS on the bus's own TCP port, both ends pinned (``tls``). The
    handshake runs here, per connection, so an ask accepted a moment ago counts at once."""

    timeout = 900.0  # the socket waits as long as the slowest local caller already waits

    def setup(self) -> None:
        from cairn.tools.bus_client import tls
        raw = self.request
        raw.settimeout(30)           # a handshake that stalls is a dead peer, not a slow verb
        self.request = tls.server_context(self.server.tls_dir).wrap_socket(raw, server_side=True)
        self.peer = tls.peer_box(self.server.tls_dir, self.request)
        super().setup()

    def admit(self, req: dict) -> dict | None:
        op = req.get("op")
        if self.peer is None:
            if op == "ask":
                return None
            return {"ok": False, "error": "this box is not pinned here — it may only ask "
                                          "(cairn install on the asking box)"}
        if op not in LAN_OPS:
            return {"ok": False, "error": f"{op!r} is not open across the LAN — one of {LAN_OPS}"}
        return None

    def reply_to(self, req: dict) -> dict:
        from cairn.tools.bus_client import tls
        d = self.server.tls_dir
        if req.get("op") == "ask":
            try:
                fp = tls.hold_ask(d, tls.check_name(str(req.get("box"))), str(req.get("cert")))
            except (ValueError, OSError) as exc:
                return {"ok": False, "error": f"the ask was not held: {exc}"}
            me = tls.identity(d)
            print(f"bus: held an ask from {req.get('box')} ({fp}) at {d}/asks",
                  file=sys.stderr, flush=True)
            return {"ok": True, "held": True, "box": me["name"], "fingerprint": me["fingerprint"]}
        return self.server.process.answer(req, remote=True)


class _HomeWatch(DiagnosticBase):
    daemon_threads = True
    home: Path | None = None

    def service_actions(self) -> None:
        """A bus whose home folder is gone has no address left to answer at — a proof's
        scratch HOME was removed under it — so it ends itself rather than run on as a leak."""
        if self.home is not None and not self.home.exists():
            print(f"bus: {self.home} is gone — exiting", file=sys.stderr, flush=True)
            stop = getattr(self, "stop", None)
            if stop is not None:
                stop.set("home-gone", {"home": str(self.home)})
            threading.Thread(target=self.shutdown, daemon=True).start()
            self.home = None


if hasattr(socketserver, "ThreadingUnixStreamServer"):   # absent on Windows
    class _Server(_HomeWatch, socketserver.ThreadingUnixStreamServer):
        pass


class _LoopServer(_HomeWatch, socketserver.ThreadingTCPServer):
    allow_reuse_address = False   # port 0: the kernel picks, so there is nothing to reuse
    key = ""


class _LanServer(DiagnosticBase, socketserver.ThreadingTCPServer):
    daemon_threads = True
    # On Windows SO_REUSEADDR lets a second process steal a bound port; off there.
    allow_reuse_address = os.name != "nt"
    tls_dir: Path | None = None

    def handle_error(self, request, client_address) -> None:
        # A refused handshake is the door working; one line, not a traceback per stranger.
        exc = sys.exc_info()[1]
        print(f"bus: lan {client_address[0]} refused: {type(exc).__name__}: {exc}",
              file=sys.stderr, flush=True)


SPILL = "bus.unflushed.jsonl"


def final_flush(bus: BusDevice, home: Path | None) -> dict:
    """Flush the ring; if the store refuses, spill it to ``<home>/bus.unflushed.jsonl`` so the
    next bus at this home lands it (``land_spill``). Loud either way (Law 7): the error is in
    the reply and the log, and nothing the ring held is dropped."""
    try:
        return {"ok": True, "json": bus.flush()}
    except Exception as exc:  # noqa: BLE001 — reported and spilled, never swallowed
        error = f"{type(exc).__name__}: {exc}"
        spilled = bus.spill(home / SPILL) if home is not None else None
        print(f"bus: flush failed ({error}); spilled {spilled} to {home}/{SPILL}",
              file=sys.stderr, flush=True)
        return {"ok": False, "error": f"flush failed: {error}", "spilled": spilled}


def land_spill(bus: BusDevice, home: Path) -> dict | None:
    """A spill left by the bus before this one goes back in the ring and is flushed now; the
    file is renamed ``.landed-<stamp>`` only after that flush commits."""
    spill = home / SPILL
    if not spill.exists():
        return None
    restored = bus.restore(spill)
    flushed = bus.flush()
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    spill.rename(home / f"{SPILL}.landed-{stamp}")
    print(f"bus: landed spill {restored} → {flushed}", file=sys.stderr, flush=True)
    return {"restored": restored, "flushed": flushed}


def _lock(fh) -> bool:
    if fcntl is not None:
        try:
            fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            return False
        return True
    import msvcrt   # Windows: a non-blocking lock on the first byte, held while fh is open
    fh.seek(0)
    try:
        msvcrt.locking(fh.fileno(), msvcrt.LK_NBLCK, 1)
    except OSError:
        return False
    return True


def claim(home: Path):
    """Take ``<home>/bus.lock`` or return None — the singleton claim (cited from
    ground_loop/guard.py claim_singleton). The open file IS the claim; keep it."""
    home.mkdir(parents=True, exist_ok=True)
    fh = open(home / "bus.lock", "a+")
    if not _lock(fh):
        fh.close()
        return None
    fh.seek(0)
    fh.truncate()
    fh.write(f"{os.getpid()}\n")
    fh.flush()
    return fh


PORT_FILE = "bus.port"


def _is_the_home() -> bool:
    """This box is a cairn home: CAIRN_HOME_HOST unset (the installer's answer for a home, as
    before it was asked), or naming this box."""
    host = os.environ.get("CAIRN_HOME_HOST", "").strip()
    return not host or host.split(".")[0].lower() == platform.node().split(".")[0].lower()


def _lan_default(home: Path, scratch: bool) -> int | None:
    """The LAN door opens by default only on a home that has a box identity — never on a
    scratch bus, never on an attaching box (federation is not this ticket's)."""
    from cairn.tools.bus_client import tls
    if scratch or not _is_the_home() or not tls.has_identity(home / "tls"):
        return None
    return tls.lan_port()


def _write_port(home: Path, record: dict) -> None:
    tmp = home / f"{PORT_FILE}.{os.getpid()}.tmp"
    tmp.write_text(json.dumps(record) + "\n")
    if os.name != "nt":
        os.chmod(tmp, 0o600)
    os.replace(tmp, home / PORT_FILE)


STOPS_FILE = "stops.jsonl"
# The requests still unanswered when this bus stopped, for the next bus to hold as given up
# (ticket 054a03f974f6): written last at every stop serve() returns from, retired at the next start.
ASKS_FILE = "asks_in_flight.json"
_BACKLOG_JOIN_S = 30.0  # the pass is one read of undelivered; a minute would be wedged
_STOP_SIGNALS = tuple(getattr(signal, n) for n in ("SIGTERM", "SIGINT", "SIGHUP")
                      if hasattr(signal, n))


class _Stop(DiagnosticBase):
    """Why this bus process stopped (ticket 73c58a1dcad7). The first cause recorded wins (D4):
    the shutdown a signal starts does not overwrite the signal. Unset at the end means clean."""

    def __init__(self) -> None:
        super().__init__()
        self._lock = threading.Lock()
        self.cause: str | None = None
        self.detail: dict = {}

    def set(self, cause: str, detail: dict) -> bool:
        with self._lock:
            if self.cause is not None:
                return False
            self.cause, self.detail = cause, detail
            return True


def _signal_stops(server, stop: _Stop):
    """Catch SIGTERM, SIGINT and SIGHUP as a recorded stop (D3). The signals are blocked in
    this thread before any thread serve() starts, so they wait for one daemon waiter whose
    sigwaitinfo names the sender's pid; a Python handler stays installed for a thread that
    predates the mask (sender_pid null). Returns the undo, run when serve() ends."""
    if not _STOP_SIGNALS or threading.current_thread() is not threading.main_thread():
        return lambda: None

    def _stopped_by(signum: int, sender: int | None) -> None:
        if stop.set("signal", {"signal": signal.Signals(signum).name, "sender_pid": sender}):
            threading.Thread(target=server.shutdown, daemon=True).start()

    old_handlers = {s: signal.signal(s, lambda n, _f: _stopped_by(n, None))
                    for s in _STOP_SIGNALS}
    old_mask = None
    if hasattr(signal, "sigwaitinfo") and hasattr(signal, "pthread_sigmask"):
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, _STOP_SIGNALS)

        def _wait() -> None:
            while True:
                info = signal.sigwaitinfo(_STOP_SIGNALS)
                _stopped_by(info.si_signo, info.si_pid)

        threading.Thread(target=_wait, name="bus-stop-signals", daemon=True).start()

    def _undo() -> None:
        if old_mask is not None:
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
        for s, h in old_handlers.items():
            signal.signal(s, h)
    return _undo


def _record_stop(home: Path, stop: _Stop) -> None:
    """One line per stop at ``<home>/stops.jsonl`` and on stderr (D2, D7): stderr is the bus
    log, so a home-gone stop, whose home cannot hold the file, is still recorded."""
    line = json.dumps({
        "at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "pid": os.getpid(), "cause": stop.cause or "clean", "detail": stop.detail,
        "maxrss": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss if resource else None,
    }, default=str)
    print(f"bus: stop {line}", file=sys.stderr, flush=True)
    if home.is_dir():
        try:
            with open(home / STOPS_FILE, "a", encoding="utf-8") as fh:
                fh.write(line + "\n")
        except OSError as exc:
            print(f"bus: stop line not written to {home / STOPS_FILE}: "
                  f"{type(exc).__name__}: {exc}", file=sys.stderr, flush=True)


def serve(home: Path, bus: BusDevice, *, tcp: bool = False, lan: int | None = None,
          scratch: bool = False) -> int:
    """Serve the bus at ``home``. The local door is ``<home>/bus.sock`` where the platform has
    AF_UNIX, else (or with ``tcp``) a loopback port named in ``<home>/bus.port`` with its key.
    ``lan`` opens the box-to-box TLS door on that port; None means the default rule
    (``_lan_default``), 0 means closed."""
    # A wedged bus is a diagnostic surface (Law 7): ``kill -USR1 <pid>`` writes every
    # thread's stack to the bus log without stopping the process or needing ptrace rights.
    if hasattr(signal, "SIGUSR1"):
        faulthandler.register(signal.SIGUSR1, all_threads=True)
    stop = _Stop()
    held = claim(home)
    if held is None:
        print(f"bus: {home}/bus.lock is held — one bus per instance; exiting {EXIT_HELD}",
              file=sys.stderr)
        return EXIT_HELD
    process = BusProcess(bus)
    # No AF_UNIX (Windows) shows as no unix server class; the server never imports socket
    # (the sole-path mesh, inspector.py _SOLE_PATH: a module that can dial is a door).
    unix = hasattr(socketserver, "ThreadingUnixStreamServer") and not tcp
    sock = home / "bus.sock"
    (home / PORT_FILE).unlink(missing_ok=True)   # the claim is ours: any record here is dead
    if unix:
        sock.unlink(missing_ok=True)   # only now: the claim is ours, so any socket here is dead
        old = os.umask(0o177)
        try:
            server = _Server(str(sock), _Handler)
        finally:
            os.umask(old)
        os.chmod(sock, 0o600)
        where = str(sock)
    else:
        server = _LoopServer(("127.0.0.1", 0), _LoopHandler)
        server.key = secrets.token_hex(16)
        where = f"127.0.0.1:{server.server_address[1]}"
    server.process = process
    server.home = home
    server.stop = stop
    # Before any thread this function starts, so each inherits the blocked mask (D3).
    undo_signals = _signal_stops(server, stop)
    lan_port_open = _lan_default(home, scratch) if lan is None else (lan or None)
    lan_server = None
    if lan_port_open:
        lan_server = _LanServer(("0.0.0.0", lan_port_open), _LanHandler)
        lan_server.process, lan_server.home, lan_server.tls_dir = process, home, home / "tls"
    if not unix or lan_server is not None:
        _write_port(home, {"port": server.server_address[1] if not unix else None,
                           "key": server.key if not unix else None,
                           "pid": os.getpid(),
                           "lan": lan_server.server_address[1] if lan_server else None})
    # A hosted shim that reaches the bus is answered on its own thread (see remote.py), and
    # reaches THIS bus: a shim hosted at a scratch home must never dial the live instance.
    from cairn.tools.bus_client import remote
    os.environ["CAIRN_BUS_HOME"] = str(home)
    remote.answer_in_process(home, lambda req: process.answer(req, in_process=True))
    try:
        land_spill(bus, home)
    except Exception as exc:  # noqa: BLE001 — the spill stays on disk for the next start
        print(f"bus: spill did not land: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    try:
        taken = bus.take_over_asks(home / ASKS_FILE)
        if taken["taken_over"]:
            print(f"bus: took over {taken['taken_over']} unanswered ask(s) as given up",
                  file=sys.stderr, flush=True)
    except Exception as exc:  # noqa: BLE001 — their late replies stand and report_stood says so
        print(f"bus: asks not taken over: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    lan_note = f" lan 0.0.0.0:{lan_server.server_address[1]}" if lan_server else ""
    print(f"bus: serving {where}{lan_note} pid {os.getpid()} root {ROOT}",
          file=sys.stderr, flush=True)

    def _backlog() -> None:
        # After the bind (ticket 7cb1989e7825): a woken shim may dial this bus back, so the
        # socket must already answer. The pass is the start event's, never a beat's.
        try:
            print(f"bus: backlog {process.return_the_backlog()}", file=sys.stderr, flush=True)
        except Exception as exc:  # noqa: BLE001 — the backlog waits for the next start, loud
            print(f"bus: backlog pass failed: {type(exc).__name__}: {exc}",
                  file=sys.stderr, flush=True)

    backlog = threading.Thread(target=_backlog, name="bus-backlog", daemon=True)
    backlog.start()
    if lan_server is not None:
        threading.Thread(target=lan_server.serve_forever, name="bus-lan", daemon=True).start()
    try:
        server.serve_forever()
    except BaseException as exc:
        stop.set("exception", {"type": type(exc).__name__, "message": str(exc),
                               "traceback": traceback.format_exc()})
        raise
    finally:
        try:
            if lan_server is not None:
                lan_server.shutdown()
                lan_server.server_close()
            server.server_close()
            # The backlog pass reaches the bus's tables (undelivered -> _ensure). A serve that
            # returned under it let a scratch bus's exit drop the tables while the pass was
            # re-creating them: measured 2026-11-08, two orphan tables (no registry row) per
            # run of test_every_stop_records_its_cause.py, 50 standing. Nothing this function
            # started touches the bus after it returns.
            backlog.join(timeout=_BACKLOG_JOIN_S)
            final_flush(bus, home)
            if home.is_dir():
                try:
                    bus.hand_over_asks(home / ASKS_FILE)
                except Exception as exc:  # noqa: BLE001 — loud; their replies will stand
                    print(f"bus: asks not handed over: {type(exc).__name__}: {exc}",
                          file=sys.stderr, flush=True)
            if unix:
                sock.unlink(missing_ok=True)
            (home / PORT_FILE).unlink(missing_ok=True)
        finally:
            _record_stop(home, stop)
            undo_signals()
            held.close()
    return 0
