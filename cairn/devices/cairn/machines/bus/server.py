"""The bus process — one per cairn instance, hosting every shim (ticket 48519f4789b1).

Until this file, every command built its own ``BusDevice`` and its own shims in its own
process: two device commands were two rings, so mail posted by one was a db round-trip away
from the other, and ``cairn librarian show status`` paid a private beat to wire a roster that
died with it (89.3s, measured 2026-09-06). Now one process holds the ring and the shims, and
every caller speaks to it over a unix socket through ``cairn.tools.bus_client.remote``.

THE ADDRESS. ``<home>/bus.sock`` (mode 0600 — one box, one user, the file mode is the gate)
and ``<home>/bus.lock``, where home is ``CAIRN_BUS_HOME`` else the bus's instance folder
``~/.cairn/devices/cairn/machines/bus/0`` (the instance segment is never optional).

THE CLAIM. ``fcntl.flock(LOCK_EX|LOCK_NB)`` on the lock file — the shape of
``ground_loop/guard.py claim_singleton``, written again here and cited, never imported (RULE 1:
guard is the ground loop's internal). A refused claim exits 3, the unit's SuccessExitStatus.
A stale socket from a dead process is unlinked only AFTER the claim is won.

THE WIRE. One JSON object per line each way. Every request carries ``op`` and ``root`` (the
caller's class root). Ops: ``call``, ``hold``, ``verbs``, ``flush``, ``stats``, ``shutdown``.
Any exception answers ``{ok: false, error}`` — loud, never empty (Law 7).

THE BUS SERVES THE CODE THAT ASKS (decision 4). A request from a different class root, or one
arriving after any ``*.py`` under this root changed, is answered ``{ok: false, stale: true}``
and nothing else; the client shuts this process down and starts one from its own root.
"""
from __future__ import annotations

import faulthandler
import fcntl
import importlib
import json
import os
import signal
import socketserver
import sys
import threading
from collections import deque
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from cairn.devices.cairn.machines.bus.bus import BusDevice

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
        if shim.device_id in self._wired and shim.device_id in self.bus._delivery_hooks:
            return
        with self._holding(shim.device_id):
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

    def answer(self, req: dict, *, in_process: bool = False) -> dict:
        # A request from code this process hosts runs this process's code by definition, so
        # it is never stale against it; only a caller across the socket can be.
        root = req.get("root")
        if not in_process and root is not None and str(root) != str(ROOT):
            return {"ok": False, "stale": True, "root": str(ROOT)}
        if (not in_process and req.get("op") not in ("shutdown", "flush")
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
    def handle(self) -> None:
        line = self.rfile.readline()
        if not line:
            return
        try:
            req = json.loads(line)
        except ValueError as exc:
            reply = {"ok": False, "error": f"not one JSON line: {exc}"}
            req = {}
        else:
            if req.get("op") == "shutdown":
                # A shutdown ENDS the process whatever the flush does: a bus that cannot stop
                # is a stale bus nothing can replace (measured 2026-10-03 — one Decimal in the
                # ring failed every flush, so every shutdown, so every caller after it).
                reply = final_flush(self.server.process.bus, self.server.home)
                self._send(reply)
                threading.Thread(target=self.server.shutdown, daemon=True).start()
                return
            reply = self.server.process.answer(req)
        self._send(reply)

    def _send(self, reply: dict) -> None:
        self.wfile.write((json.dumps(reply, default=str) + "\n").encode())
        self.wfile.flush()


class _Server(socketserver.ThreadingUnixStreamServer):
    daemon_threads = True
    home: Path | None = None

    def service_actions(self) -> None:
        """A bus whose home folder is gone has no address left to answer at — a proof's
        scratch HOME was removed under it — so it ends itself rather than run on as a leak."""
        if self.home is not None and not self.home.exists():
            print(f"bus: {self.home} is gone — exiting", file=sys.stderr, flush=True)
            threading.Thread(target=self.shutdown, daemon=True).start()
            self.home = None


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


def claim(home: Path):
    """Take ``<home>/bus.lock`` or return None — the singleton claim (cited from
    ground_loop/guard.py claim_singleton). The open file IS the claim; keep it."""
    home.mkdir(parents=True, exist_ok=True)
    fh = open(home / "bus.lock", "a+")
    try:
        fcntl.flock(fh, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        fh.close()
        return None
    fh.seek(0)
    fh.truncate()
    fh.write(f"{os.getpid()}\n")
    fh.flush()
    return fh


def serve(home: Path, bus: BusDevice) -> int:
    # A wedged bus is a diagnostic surface (Law 7): ``kill -USR1 <pid>`` writes every
    # thread's stack to the bus log without stopping the process or needing ptrace rights.
    faulthandler.register(signal.SIGUSR1, all_threads=True)
    held = claim(home)
    if held is None:
        print(f"bus: {home}/bus.lock is held — one bus per instance; exiting {EXIT_HELD}",
              file=sys.stderr)
        return EXIT_HELD
    sock = home / "bus.sock"
    sock.unlink(missing_ok=True)   # only now: the claim is ours, so any socket here is dead
    old = os.umask(0o177)
    try:
        server = _Server(str(sock), _Handler)
    finally:
        os.umask(old)
    os.chmod(sock, 0o600)
    server.process = BusProcess(bus)
    server.home = home
    # A hosted shim that reaches the bus is answered on its own thread (see remote.py), and
    # reaches THIS bus: a shim hosted at a scratch home must never dial the live instance.
    from cairn.tools.bus_client import remote
    os.environ["CAIRN_BUS_HOME"] = str(home)
    process = server.process
    remote.answer_in_process(home, lambda req: process.answer(req, in_process=True))
    try:
        land_spill(bus, home)
    except Exception as exc:  # noqa: BLE001 — the spill stays on disk for the next start
        print(f"bus: spill did not land: {type(exc).__name__}: {exc}", file=sys.stderr, flush=True)
    print(f"bus: serving {sock} pid {os.getpid()} root {ROOT}", file=sys.stderr, flush=True)

    def _backlog() -> None:
        # After the bind (ticket 7cb1989e7825): a woken shim may dial this bus back, so the
        # socket must already answer. The pass is the start event's, never a beat's.
        try:
            print(f"bus: backlog {process.return_the_backlog()}", file=sys.stderr, flush=True)
        except Exception as exc:  # noqa: BLE001 — the backlog waits for the next start, loud
            print(f"bus: backlog pass failed: {type(exc).__name__}: {exc}",
                  file=sys.stderr, flush=True)

    threading.Thread(target=_backlog, name="bus-backlog", daemon=True).start()
    try:
        server.serve_forever()
    finally:
        server.server_close()
        final_flush(bus, home)
        sock.unlink(missing_ok=True)
        held.close()
    return 0
