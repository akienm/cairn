#!/usr/bin/env python3
"""Teeth for the database proxy v0 — one per falsifier clause of ticket a22eb3c25ccd.

The relay runs over ephemeral loopback ports against a fake upstream (an echo server that
tags each reply), never 5432. The process and the device face run in children under a scratch
HOME (scratch.home_env), so the record lands in a scratch ~/.cairn and the bus address is
scrubbed. The subject is bound at call time: with dbproxy taken away every tooth reds by name.
"""

from __future__ import annotations

import json
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

TICKET = "a22eb3c25ccd"
PROVES = {"a22eb3c25ccd": {
    "1": "test_two_concurrent_connections_round_trip_through_the_relay_kept_apart",
    "2": "test_the_listener_is_bound_to_loopback_only",
    "3": "test_a_held_listen_port_exits_zero_records_held_and_forwards_nothing",
    "4": "test_a_refused_upstream_closes_the_client_and_is_counted",
    "5": "test_a_wake_spawns_its_own_process_once_and_windowless_on_windows",
    "6": "test_the_device_answers_as_database",
}}
T = PROVES[TICKET]
FAILURES: list[str] = []
PASSED: set[str] = set()


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)
    else:
        PASSED.add(name)


def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    p = s.getsockname()[1]
    s.close()
    return p


def echo_upstream() -> tuple[socket.socket, int]:
    srv = socket.socket()
    srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    srv.bind(("127.0.0.1", 0))
    srv.listen(8)

    def serve(c):
        with c:
            while True:
                d = c.recv(4096)
                if not d:
                    return
                c.sendall(b"pg:" + d)

    def loop():
        while True:
            try:
                c, _ = srv.accept()
            except OSError:
                return
            threading.Thread(target=serve, args=(c,), daemon=True).start()

    threading.Thread(target=loop, daemon=True).start()
    return srv, srv.getsockname()[1]


def recv_exact(s: socket.socket, n: int) -> bytes:
    buf = b""
    while len(buf) < n:
        d = s.recv(n - len(buf))
        if not d:
            break
        buf += d
    return buf


def teeth_relay(Relay) -> None:
    srv, up = echo_upstream()
    relay = Relay(0, up).start()
    try:
        # 1. two concurrent connections, each sees only its own reply
        a = socket.create_connection(("127.0.0.1", relay.listen_port), timeout=5)
        b = socket.create_connection(("127.0.0.1", relay.listen_port), timeout=5)
        a.sendall(b"alpha-1"); b.sendall(b"bravo-2")
        ra = recv_exact(a, 10); rb = recv_exact(b, 10)
        a.sendall(b"alpha-3"); ra2 = recv_exact(a, 10)
        a.close(); b.close()
        check(T["1"], ra == b"pg:alpha-1" and rb == b"pg:bravo-2" and ra2 == b"pg:alpha-3",
              f"a={ra!r} b={rb!r} a2={ra2!r}")
        # 2. loopback only
        host = relay.bound_address[0]
        check(T["2"], host == "127.0.0.1", f"bound {relay.bound_address}")
    finally:
        relay.stop(); srv.close()
    # 4. refused upstream: client closed, refusal counted
    dead = free_port()
    relay = Relay(0, dead).start()
    try:
        c = socket.create_connection(("127.0.0.1", relay.listen_port), timeout=5)
        c.settimeout(5)
        try:
            got = c.recv(10)
        except OSError:
            got = b""
        c.close()
        deadline = time.time() + 3
        while relay.refused < 1 and time.time() < deadline:
            time.sleep(0.05)
        check(T["4"], got == b"" and relay.refused == 1 and relay.connections == 0,
              f"recv={got!r} refused={relay.refused} connections={relay.connections}")
    finally:
        relay.stop()


def env_for(home: Path, **extra: str) -> dict:
    from cairn.tools.scratch.scratch import home_env
    return home_env(home, PYTHONPATH=str(REPO), **extra)


def record_at(home: Path) -> dict:
    p = home / ".cairn" / "devices" / "dbproxy" / "0" / "relay.json"
    try:
        return json.loads(p.read_text())
    except (OSError, ValueError):
        return {}


def tooth_held() -> None:
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("dbproxy-held-")
    holder = socket.socket()
    holder.bind(("127.0.0.1", 0))
    holder.listen(1)
    port = holder.getsockname()[1]
    try:
        r = subprocess.run([sys.executable, "-m", "cairn.devices.dbproxy"], cwd=str(REPO),
                           env=env_for(home, CAIRN_DBPROXY_LISTEN_PORT=str(port),
                                       CAIRN_DBPROXY_POSTGRES_PORT=str(free_port())),
                           capture_output=True, text=True, timeout=20)
        rec = record_at(home)
        check(T["3"], r.returncode == 0 and rec.get("state") == "held" and rec.get("connections") == 0,
              f"rc={r.returncode} record={rec} err={r.stderr[-200:]!r}")
    finally:
        holder.close()


WAKE_CHILD = r"""
import json, os, sys
from cairn.devices.dbproxy.device import DatabaseProxyDevice, spawn_argv_and_kwargs
from cairn.tools.windowless_spawn.windowless_spawn import background_pythonw, detached_kwargs
first = DatabaseProxyDevice()
import time
from cairn.devices.dbproxy.__main__ import record_path
deadline = time.time() + 15
rec = {}
while time.time() < deadline:
    try:
        rec = json.loads(record_path().read_text())
        if rec.get("state") == "listening":
            break
    except Exception:
        pass
    time.sleep(0.1)
second = DatabaseProxyDevice()
argv, kw = spawn_argv_and_kwargs("nt")
calls = []
class FakeProc: pid = 4242
def fake_popen(a, **k):
    calls.append((a, sorted(k)))
    return FakeProc()
nt_ok = argv[0] == background_pythonw(os_name="nt") and argv[1:] == ["-m", "cairn.devices.dbproxy"] \
        and kw == detached_kwargs(os_name="nt") and bool(kw)
print(json.dumps({"waker": os.getpid(), "spawned": first.spawned_pid, "second": second.spawned_pid,
                  "rec": rec, "nt_ok": nt_ok, "state": second.state()}))
"""


def tooth_own_process() -> None:
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("dbproxy-wake-")
    port = free_port()
    out, pid = {}, None
    try:
        r = subprocess.run([sys.executable, "-c", WAKE_CHILD], cwd=str(REPO),
                           env=env_for(home, CAIRN_DBPROXY_LISTEN_PORT=str(port),
                                       CAIRN_DBPROXY_POSTGRES_PORT=str(free_port())),
                           capture_output=True, text=True, timeout=40)
        try:
            out = json.loads(r.stdout.strip().splitlines()[-1])
        except (ValueError, IndexError):
            out = {"stderr": r.stderr[-300:]}
        pid = out.get("spawned")
        listening = False
        try:
            socket.create_connection(("127.0.0.1", port), timeout=3).close()
            listening = True
        except OSError:
            pass
        rec = out.get("rec", {})
        ok = (isinstance(pid, int) and pid != out.get("waker") and rec.get("pid") == pid
              and rec.get("state") == "listening" and rec.get("listen_port") == port
              and listening and out.get("second") is None and out.get("nt_ok") is True)
        check(T["5"], ok, json.dumps(out)[:300] + f" listening={listening}")
    finally:
        if isinstance(pid, int):
            try:
                os.kill(pid, 15)
            except OSError:
                pass


def tooth_answers_as() -> None:
    from cairn.devices.dbproxy.shim import DatabaseProxyShim
    charter = json.loads((REPO / "cairn/devices/dbproxy/intention+why.json").read_text())
    did = DatabaseProxyShim().device_id
    check(T["6"], did == "database" and charter.get("answers_as") == "database",
          f"device_id={did!r} answers_as={charter.get('answers_as')!r}")


def main() -> int:
    try:
        from cairn.devices.dbproxy.forward import Relay
    except Exception as exc:  # noqa: BLE001 — the hollow reading
        for n in T.values():
            check(n, False, f"subject absent: {exc!r}"[:120])
        print(f"\nRED — {len(FAILURES)} failure(s)")
        return 1
    for step in (lambda: teeth_relay(Relay), tooth_held, tooth_own_process, tooth_answers_as):
        try:
            step()
        except Exception as exc:  # noqa: BLE001 — one tooth's crash reds its own name only
            print(f"  aborted: {exc!r}")
    for n in T.values():
        if n not in FAILURES and n not in PASSED:
            check(n, False, "unran: its step aborted before the check")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
