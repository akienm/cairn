"""Proof: the bus speaks TCP — on a box with no AF_UNIX, and box to box over pinned TLS
(ticket 5183005fa134, falsifier clauses a, b and c).

Windows is not here, so its two differences are made here: AF_UNIX is deleted from ``socket``
in a fresh courier before the client loads (the path akiendell takes), and ``fcntl`` is hidden
from the server with a stand-in ``msvcrt`` that records the lock it is asked for. Teeth, all
printed, none stopping at the first red:

  (a1) with no AF_UNIX a fresh courier's ``RemoteBus().list()`` answers from a bus it lazily
       started; the bus serves loopback TCP (``<home>/bus.port``), and no ``bus.sock`` exists;
       a request with the wrong key is refused.
  (a2) the server module imports with no ``fcntl``, and its claim takes msvcrt's byte lock —
       once, and not twice.
  (a3) the Windows spawn: this venv's python, ``--tcp``, DETACHED_PROCESS|CREATE_NO_WINDOW|
       CREATE_NEW_PROCESS_GROUP.
  (b)  the LAN door: plain TCP gets no answer; a pinned box is answered and is never stale
       (its root is another checkout's); an unpinned box is refused; a box with no
       certificate may only ask, and its ask is held, not pinned; shutdown is refused.
  (c)  the Unix-socket p50 round trip stays within 10% of the baseline measured before the
       build (``BASELINE_UNIX_P50_US``, recorded on the ticket); TCP loopback is measured and
       printed beside it.

Run:  python3 cairn/devices/cairn/machines/bus/proofs/test_the_bus_speaks_tcp.py
"""
from __future__ import annotations

import json
import os
import socket
import statistics
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {
    "5183005fa134": {
        "a": "with no AF_UNIX a fresh RemoteBus().list() answers from a bus it lazily started over TCP 127.0.0.1",
        "b": "the LAN port answers only a pinned box and refuses plain TCP",
        "c": "the Unix-socket p50 stays within 10% of its pre-build baseline; TCP loopback is measured",
    },
}

# Measured 2026-11-04 on akiendelllinux before the build, through exchange({"op": "stats"})
# against a scratch bus (filled in from the pre-build bench; see the ticket's decisions).
# Measured 2026-11-04 on akiendelllinux BEFORE the build (tree at 9b327b6a, this file's own _bench,
# 400 exchanges after 50 warm-up, three scratch buses): p50 6893.0 / 6953.6 / 6810.8 us; the
# median is the baseline. The ticket's 50 us was a bare-broker bench; the live exchange carries
# the code-stamp staleness check on every call, which is why the measured floor is ~7 ms.
BASELINE_UNIX_P50_US = 6893.0

FAILURES: list[str] = []
_MODULE = "cairn.devices.cairn.machines.bus"
_UNIT = f"cairn-bus-proof-tcp-{os.getpid()}"
_FREE_PORT_TRIES = 20


def ok(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if cond else 'RED '} {name}")
    if detail:
        print(f"         -> {detail}")
    if not cond:
        FAILURES.append(f"{name}: {detail}")


def _env(home: Path, **extra) -> dict:
    env = dict(os.environ)
    env.update({"CAIRN_BUS_HOME": str(home), "CAIRN_BUS_UNIT": _UNIT,
                "PYTHONPATH": str(_REPO) + os.pathsep + env.get("PYTHONPATH", ""),
                "PYTHONDONTWRITEBYTECODE": "1"})
    env.update({k: str(v) for k, v in extra.items()})
    return env


def _py(home: Path, code: str, timeout: float = 90, **extra) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-c", code], env=_env(home, **extra), cwd=str(_REPO),
                          capture_output=True, text=True, timeout=timeout)


_NO_UNIX = "import socket\ndel socket.AF_UNIX\n"


def _bus_pids(home: Path) -> list[int]:
    r = subprocess.run(["pgrep", "-f", f"{_MODULE} serve --home {home}"],
                       capture_output=True, text=True)
    return sorted(int(p) for p in r.stdout.split() if p.strip() and int(p) != os.getpid())


def _stop(home: Path, no_unix: bool = False) -> None:
    _py(home, (_NO_UNIX if no_unix else "") +
        "from cairn.tools.bus_client.remote import exchange\n"
        "try:\n    exchange({'op': 'shutdown'}, timeout=30)\nexcept Exception:\n    pass\n",
        timeout=60)
    subprocess.run(["systemctl", "--user", "stop", f"{_UNIT}.service"], capture_output=True)
    subprocess.run(["systemctl", "--user", "reset-failed", f"{_UNIT}.service"],
                   capture_output=True)
    for pid in _bus_pids(home):
        try:
            os.kill(pid, 15)
        except OSError:
            pass


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait_for(path: Path, s: float = 20) -> bool:
    deadline = time.monotonic() + s
    while time.monotonic() < deadline:
        if path.exists():
            return True
        time.sleep(0.05)
    return False


# --- (a) ---------------------------------------------------------------------------------

def tooth_a1_no_af_unix_lazy_starts_over_tcp(home: Path) -> None:
    name = PROVES["5183005fa134"]["a"]
    r = _py(home, _NO_UNIX +
            "import json\nfrom cairn.tools.bus_client.remote import RemoteBus\n"
            "print(json.dumps(RemoteBus(scratch=True).list()))\n")
    port_rec = home / "bus.port"
    rec = json.loads(port_rec.read_text()) if port_rec.exists() else {}
    ok(name, r.returncode == 0 and rec.get("port") and not (home / "bus.sock").exists(),
       f"rc={r.returncode} bus.port={rec and {k: rec[k] for k in ('port', 'pid', 'lan')}} "
       f"bus.sock={(home / 'bus.sock').exists()} out={r.stdout.strip()[-200:]} "
       f"err={r.stderr.strip()[-400:]}")
    if rec.get("port"):
        with socket.create_connection(("127.0.0.1", int(rec["port"])), timeout=10) as c:
            c.sendall(b'{"op": "stats", "key": "not-the-key"}\n')
            reply = json.loads(c.makefile("r").readline() or "{}")
        ok("a request with the wrong loopback key is refused",
           reply.get("ok") is False and "key" in str(reply.get("error")), f"reply={reply}")


def tooth_a2_server_claims_without_fcntl(home: Path) -> None:
    code = (
        "import sys, types, json\n"
        "sys.modules['fcntl'] = None\n"
        "calls = []\n"
        "held = set()\n"
        "def locking(fd, mode, n):\n"
        "    calls.append((mode, n))\n"
        "    if 'one' in held:\n"
        "        raise OSError(36, 'Resource deadlock avoided')\n"
        "    held.add('one')\n"
        "sys.modules['msvcrt'] = types.SimpleNamespace(locking=locking, LK_NBLCK=2)\n"
        "from pathlib import Path\n"
        "from cairn.devices.cairn.machines.bus import server\n"
        f"h = Path({str(home / 'claim')!r})\n"
        "first = server.claim(h)\n"
        "second = server.claim(h)\n"
        "print(json.dumps({'fcntl': server.fcntl, 'first': first is not None,\n"
        "                  'second': second is not None, 'calls': calls}))\n")
    r = _py(home, code)
    try:
        got = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        got = {"rc": r.returncode, "err": r.stderr.strip()[-400:]}
    ok("the server claims its lock through msvcrt when there is no fcntl",
       got.get("fcntl") is None and got.get("first") is True and got.get("second") is False
       and got.get("calls") == [[2, 1], [2, 1]], f"{got}")


def tooth_a3_windows_spawn_flags(home: Path) -> None:
    from unittest import mock
    from cairn.tools.bus_client import remote
    seen = {}

    def popen(cmd, **kw):
        seen["cmd"], seen["flags"] = cmd, kw.get("creationflags")
        return mock.Mock()

    with mock.patch.object(remote.subprocess, "Popen", popen), \
            mock.patch.object(remote.os, "name", "nt"):
        how = remote._spawn(home, True)
    want = 0x00000008 | 0x08000000 | 0x00000200
    cmd = seen.get("cmd") or []
    ok("the Windows spawn is detached, windowless, this python, over --tcp",
       how == "detached" and seen.get("flags") == want and cmd[:1] == [sys.executable]
       and "--tcp" in cmd and "--scratch" in cmd, f"how={how} seen={seen}")


# --- (b) ---------------------------------------------------------------------------------

def tooth_b_the_lan_door(base: Path) -> None:
    from cairn.tools.bus_client import tls
    home, mine, stranger, asker = base / "lanhome", base / "boxb", base / "boxc", base / "boxd"
    srv_tls = home / "tls"
    tls.make_identity(srv_tls, "boxa")
    for d, n in ((mine, "boxb"), (stranger, "boxc"), (asker, "boxd")):
        tls.make_identity(d, n)
        tls.trust(d, "boxa", (srv_tls / "box.crt").read_text())
    tls.trust(srv_tls, "boxb", (mine / "box.crt").read_text())
    lan = _free_port()
    log = open(base / "lan-bus.log", "w")
    proc = subprocess.Popen([sys.executable, "-m", _MODULE, "serve", "--home", str(home),
                             "--scratch", "--lan", str(lan)], env=_env(home), cwd=str(_REPO),
                            stdout=log, stderr=log)
    try:
        if not _wait_for(home / "bus.port"):
            ok(PROVES["5183005fa134"]["b"], False,
               f"no bus.port within 20s; log: {(base / 'lan-bus.log').read_text()[-600:]}")
            return
        far = f"127.0.0.1:{lan}"
        # plain TCP: the TLS server reads a ClientHello, gets JSON, and answers no JSON
        try:
            with socket.create_connection(("127.0.0.1", lan), timeout=10) as c:
                c.sendall(b'{"op": "stats"}\n')
                raw = c.recv(4096)
        except OSError as exc:
            raw = f"closed: {exc}".encode()
        plain_answered = raw.strip().startswith(b"{")
        ok("the LAN port refuses plain TCP", not plain_answered, f"got {raw[:120]!r}")

        def courier(tls_dir: Path, code: str) -> dict:
            r = _py(home, "import json\nfrom cairn.tools.bus_client.remote import exchange\n"
                    + code, CAIRN_BUS_TLS_DIR=tls_dir, CAIRN_BUS_HOME=far)
            try:
                return json.loads(r.stdout.strip().splitlines()[-1])
            except Exception:  # noqa: BLE001
                return {"courier_rc": r.returncode, "err": r.stderr.strip()[-300:]}

        pinned = courier(mine, "print(json.dumps(exchange({'op': 'stats', 'root': '/another/box'})))\n")
        ok("a pinned box is answered, and its other root is not stale",
           pinned.get("ok") is True and not pinned.get("stale"), f"{pinned}")
        listed = courier(mine, "from cairn.tools.bus_client.remote import RemoteBus\n"
                               "print(json.dumps({'ok': True, 'list': RemoteBus().list()}))\n")
        ok("RemoteBus at host:port speaks the BusDevice face across TLS",
           listed.get("ok") is True and "list" in listed, f"{str(listed)[:300]}")
        down = courier(mine, "print(json.dumps(exchange({'op': 'shutdown'})))\n")
        ok("a pinned box may not shut this box's bus down",
           down.get("ok") is False and "LAN" in str(down.get("error")), f"{down}")
        strange = courier(stranger, "try:\n    print(json.dumps(exchange({'op': 'stats'})))\n"
                                    "except Exception as e:\n"
                                    "    print(json.dumps({'refused': type(e).__name__ + ': ' + str(e)}))\n")
        ok("an unpinned box is refused at the handshake", "refused" in strange, f"{strange}")
        first = courier(asker, "from cairn.tools.bus_client import tls\nimport os\n"
                               f"print(json.dumps(tls.first_contact(os.environ['CAIRN_BUS_TLS_DIR'], '127.0.0.1', {lan})))\n")
        held = tls.asks(srv_tls)
        ok("a box with no certificate may only ask, and the ask is held, not pinned",
           first.get("home") == "boxa" and (first.get("reply") or {}).get("held") is True
           and held.get("boxd") == tls.identity(asker)["fingerprint"]
           and "boxd" not in tls.known(srv_tls), f"first={first} asks={held}")
    finally:
        _stop(home)
        try:
            proc.wait(20)
        except subprocess.TimeoutExpired:
            proc.kill()
        log.close()


# --- (c) ---------------------------------------------------------------------------------

def _bench(home: Path, no_unix: bool, n: int = 400) -> float:
    r = _py(home, (_NO_UNIX if no_unix else "") +
            "import json, time, statistics\n"
            "from cairn.tools.bus_client.remote import exchange, ensure_bus\n"
            "ensure_bus(scratch=True)\n"
            "for _ in range(50):\n    exchange({'op': 'stats'})\n"
            "ts = []\n"
            f"for _ in range({n}):\n"
            "    t = time.perf_counter(); exchange({'op': 'stats'}); ts.append(time.perf_counter() - t)\n"
            "print(statistics.median(ts) * 1e6)\n", timeout=180)
    return float(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 else float("nan")


def tooth_c_latency(base: Path) -> None:
    uhome, thome = base / "unix", base / "tcp"
    try:
        unix = _bench(uhome, False)
    finally:
        _stop(uhome)
    try:
        tcp = _bench(thome, True)
    finally:
        _stop(thome, no_unix=True)
    print(f"         unix p50 {unix:.0f} us; tcp loopback p50 {tcp:.0f} us; "
          f"baseline unix {BASELINE_UNIX_P50_US} us")
    ok(PROVES["5183005fa134"]["c"],
       BASELINE_UNIX_P50_US is not None and unix <= BASELINE_UNIX_P50_US * 1.10 and tcp == tcp,
       f"unix={unix:.0f}us tcp={tcp:.0f}us baseline={BASELINE_UNIX_P50_US}")


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir
    base = Path(scratch_dir("bus-tcp"))
    a_home = base / "a1"
    try:
        tooth_a1_no_af_unix_lazy_starts_over_tcp(a_home)
    except Exception as exc:  # noqa: BLE001
        ok("tooth_a1_no_af_unix_lazy_starts_over_tcp", False, f"raised {type(exc).__name__}: {exc}")
    finally:
        _stop(a_home, no_unix=True)
    for tooth, arg in ((tooth_a2_server_claims_without_fcntl, base),
                       (tooth_a3_windows_spawn_flags, base / "a3"),
                       (tooth_b_the_lan_door, base),
                       (tooth_c_latency, base)):
        try:
            tooth(arg)
        except Exception as exc:  # noqa: BLE001 — every tooth prints; none stops the rest
            ok(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    if FAILURES:
        print(f"RED — {len(FAILURES)} failed")
        return 1
    print("GREEN — the bus speaks TCP on a box with no AF_UNIX, and only to pinned boxes")
    return 0


def test_the_bus_speaks_tcp():
    assert main() == 0, FAILURES


if __name__ == "__main__":
    sys.exit(main())
