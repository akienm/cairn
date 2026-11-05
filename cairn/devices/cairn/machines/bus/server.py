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
import sys
import threading
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from cairn.devices.cairn.machines.bus.bus import BusDevice

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


class BusProcess:
    """The ring, the held shims, and the per-shim locks — everything one request touches."""

    def __init__(self, bus: BusDevice) -> None:
        from cairn.tools.bus_client.roster import DeviceRoster

        self.bus = bus
        self.roster = DeviceRoster(bus)
        self.stamp = code_stamp()
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
        bus.set_while_waiting(self._serve_held)

    # --- holding ----------------------------------------------------------------------

    def _wire(self, shim) -> None:
        """Wire a held shim's delivery onto the ring — ``_wire_delivery``, the one step of a
        first pulse that is about mail — once, then wrap the poke it registered in that
        shim's own lock. Not a pulse (decision 12): a pulse fires probes and stamps snapshots."""
        if self._is_wired(shim.device_id):
            return
        with self._holding(shim.device_id):
            # Re-read under the shim's own lock: two wakes can both pass the check above, and
            # only the first may wire (ticket 445e66f32ba0).
            if self._is_wired(shim.device_id):
                return
            shim._wire_delivery()
            self._wired.add(shim.device_id)
            hook = self.bus._delivery_hooks.get(shim.device_id)
            if hook is not None and not getattr(hook, "_bus_locked", False):
                self._hooks[shim.device_id] = hook

                def locked(envelope, _id=shim.device_id):
                    self._queues[_id].append(envelope)
                    self._drain(_id)
                locked._bus_locked = True
                self.bus._delivery_hooks[shim.device_id] = locked

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
        again: the bus raises the addressee's mail trouble itself and receipts the bounce."""
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
            self._raise_undeliverable_bounce(envelope, reason)
        else:
            self._return_to_sender(envelope, reason)

    def _return_to_sender(self, envelope: dict, reason: str) -> None:
        to = envelope.get("addressee") or ""
        sender = envelope.get("sender") or ""
        self.bus.post(
            sender="bus", to=sender, channel="personal", why=f"bounced: {reason}",
            body={"is_bounce": True, "reason": reason,
                  "original_verb": envelope.get("verb", ""), "original_addressee": to,
                  "original_sender": sender, "trouble": f"mail-{to}-has-no-receiver"},
            reply_to=envelope["id"])
        self.bus.record_delivery(envelope["id"], to=to, by="bus-bounced-no-receiver")

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

    def report_stood(self, now: datetime | None = None) -> int:
        """Raise one trouble for each personal envelope standing undelivered STOOD_S or more,
        once per envelope. Rides the flush because the flush is the one op the beat sends the
        bus process. It REPORTS and nothing else: no wake or delivery is retried here, so no
        message ever waits on a tick to be delivered (bus clause 5). Identity is per
        addressee — many stuck letters to one name are one trouble with a count. An envelope
        whose date cannot be read is raised too, with its age unknown, never skipped (Law 7)."""
        now = now or datetime.now()
        raised = 0
        for envelope in self.bus.undelivered(limit=1_000_000):
            if envelope["id"] in self._stood_reported:
                continue
            age = _age_s(envelope.get("date"), now)
            if age is not None and age < STOOD_S:
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
        local = not in_process and not remote
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


class _Handler(socketserver.StreamRequestHandler):
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
            reply = final_flush(self.server.process.bus, self.server.home)
            self._send(reply)
            threading.Thread(target=self.server.shutdown, daemon=True).start()
            return
        self._send(self.reply_to(req))

    def admit(self, req: dict) -> dict | None:
        return None

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


class _HomeWatch:
    daemon_threads = True
    home: Path | None = None

    def service_actions(self) -> None:
        """A bus whose home folder is gone has no address left to answer at — a proof's
        scratch HOME was removed under it — so it ends itself rather than run on as a leak."""
        if self.home is not None and not self.home.exists():
            print(f"bus: {self.home} is gone — exiting", file=sys.stderr, flush=True)
            threading.Thread(target=self.shutdown, daemon=True).start()
            self.home = None


if hasattr(socketserver, "ThreadingUnixStreamServer"):   # absent on Windows
    class _Server(_HomeWatch, socketserver.ThreadingUnixStreamServer):
        pass


class _LoopServer(_HomeWatch, socketserver.ThreadingTCPServer):
    allow_reuse_address = False   # port 0: the kernel picks, so there is nothing to reuse
    key = ""


class _LanServer(socketserver.ThreadingTCPServer):
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

    threading.Thread(target=_backlog, name="bus-backlog", daemon=True).start()
    if lan_server is not None:
        threading.Thread(target=lan_server.serve_forever, name="bus-lan", daemon=True).start()
    try:
        server.serve_forever()
    finally:
        if lan_server is not None:
            lan_server.shutdown()
            lan_server.server_close()
        server.server_close()
        final_flush(bus, home)
        if unix:
            sock.unlink(missing_ok=True)
        (home / PORT_FILE).unlink(missing_ok=True)
        held.close()
    return 0
