"""ONE BUS PER INSTANCE HOSTS EVERY SHIM — ticket 48519f4789b1.

Today every caller of ``bus_client`` builds its own ``BusDevice`` in its own process: nine
private rings that never meet, and each ``cairn <device> show ...`` wakes a private shim. The
ticket collapses them onto one pipe: one resident bus process per instance, claimed by an
flock and listening on a unix socket under the bus's instance home, hosting every shim; a
client is a courier over that socket. This proof holds the four teeth of the falsifier:

  (1) two couriers started at once against one home leave exactly ONE bus process for it
      (``pgrep -f`` over the bus module and that home), and both name the same pid;
  (2) a message posted from process P1 is taken by a shim registered from process P2 with
      no db read — a ring hit, measured by the bus's own receipts and its db-read counter;
  (3) no code outside the bus package and its proofs calls ``BusDevice(`` (an ast walk over
      every python file and python script in class-space, so a docstring never counts);
  (4) ``cli_main`` — the mouth every launcher speaks through — answers ``get pid`` through the
      socket in under 1s, and the pid it reports is the bus process's: the shim lives there,
      and the caller built no shim and beat nothing of its own.

Beside the four, two decisions of the ticket are held here because they are the bus's own:

  (D1) ``python3 -m cairn.devices.cairn.machines.bus pulse`` sends ``flush`` and exits 0 —
       and exits 0 too, saying so, when no bus process is running (nothing in any ring);
  (stale) a request carrying a class root the bus process does not serve is refused as
       stale rather than answered by code the caller is not running.

Every bus this proof starts runs over a scratch table (``serve --scratch``) under a scratch
home, its systemd unit named ``cairn-bus-proof-<pid>`` so a leak explains itself; teardown
asks it to shut down and stops the unit regardless.

Run:  python3 cairn/devices/cairn/machines/bus/proofs/test_one_bus_process.py
"""
from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {
    "48519f4789b1": {
        "1": "two couriers leave one bus process for the instance",
        "2": "a post from one process is taken from the ring by a shim registered from another",
        "3": "nothing outside the bus package calls BusDevice",
        "4": "a launcher line round-trips through the bus process in under 1s",
    },
}

FAILURES: list[str] = []
_MODULE = "cairn.devices.cairn.machines.bus"
_FIXTURE = "cairn.devices.cairn.machines.bus.proofs.bus_proof_echo:BusProofEchoShim"
_UNIT = f"cairn-bus-proof-{os.getpid()}"


def ok(name: str, cond: bool, detail: str = "") -> None:
    print(f"  {'ok  ' if cond else 'RED '} {name}")
    if detail:
        print(f"         -> {detail}")
    if not cond:
        FAILURES.append(f"{name}: {detail}")


def _env(home: Path) -> dict:
    env = dict(os.environ)
    env["CAIRN_BUS_HOME"] = str(home)
    env["CAIRN_BUS_UNIT"] = _UNIT
    env["PYTHONPATH"] = str(_REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _py(home: Path, code: str, timeout: float = 60) -> subprocess.CompletedProcess:
    """One courier: a fresh python process that speaks only the client's public face."""
    return subprocess.run([sys.executable, "-c", code], env=_env(home), cwd=str(_REPO),
                          capture_output=True, text=True, timeout=timeout)


def _bus_pids(home: Path) -> list[int]:
    r = subprocess.run(["pgrep", "-f", f"{_MODULE} serve --home {home}"],
                       capture_output=True, text=True)
    me = os.getpid()
    return sorted(int(p) for p in r.stdout.split() if p.strip() and int(p) != me)


_ENSURE = (
    "import json, os\n"
    "from cairn.tools.bus_client.remote import ensure_bus, RemoteBus\n"
    "ensure_bus(scratch=True)\n"
    "print(json.dumps(RemoteBus().stats()))\n"
)


def _teardown(home: Path) -> None:
    _py(home, "from cairn.tools.bus_client.remote import RemoteBus\n"
              "try:\n    RemoteBus().shutdown()\nexcept Exception:\n    pass\n", timeout=30)
    subprocess.run(["systemctl", "--user", "stop", f"{_UNIT}.service"], capture_output=True)
    subprocess.run(["systemctl", "--user", "reset-failed", f"{_UNIT}.service"], capture_output=True)
    for pid in _bus_pids(home):
        try:
            os.kill(pid, 15)
        except OSError:
            pass


def tooth_1(home: Path) -> None:
    name = PROVES["48519f4789b1"]["1"]
    try:
        procs = [subprocess.Popen([sys.executable, "-c", _ENSURE], env=_env(home), cwd=str(_REPO),
                                  stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                 for _ in range(2)]
        outs = [p.communicate(timeout=60) for p in procs]
    except Exception as exc:  # noqa: BLE001
        ok(name, False, f"couriers raised {type(exc).__name__}: {exc}")
        return
    pids_seen = []
    for (out, err), p in zip(outs, procs):
        try:
            pids_seen.append(json.loads(out.strip().splitlines()[-1])["pid"])
        except Exception:  # noqa: BLE001
            pids_seen.append(f"rc={p.returncode} err={err.strip()[-300:]}")
    running = _bus_pids(home)
    ok(name, len(running) == 1 and len(set(map(str, pids_seen))) == 1 and pids_seen[0] in running,
       f"bus processes for the home={running} couriers named={pids_seen}")


def tooth_2(home: Path) -> None:
    name = PROVES["48519f4789b1"]["2"]
    p2 = _py(home, "import json\n"
                   "from cairn.tools.bus_client.remote import RemoteBus\n"
                   f"print(json.dumps(RemoteBus().hold_shim({_FIXTURE!r})))\n")
    p1 = _py(home, "import json\n"
                   "from cairn.tools.bus_client.remote import RemoteBus\n"
                   "bus = RemoteBus()\n"
                   "before = bus.stats()\n"
                   "env = bus.post(sender='bus_proof_courier', to='bus_proof_echo', verb='echo',\n"
                   "               channel='personal', why='one-bus proof, throwaway', body={'n': 48519})\n"
                   "after = bus.stats()\n"
                   "print(json.dumps({'id': env['id'], 'before': before, 'after': after,\n"
                   "                  'me': __import__('os').getpid()}))\n")
    try:
        held = json.loads(p2.stdout.strip().splitlines()[-1])
        got = json.loads(p1.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        ok(name, False, f"P2 rc={p2.returncode} {p2.stderr.strip()[-300:]} | "
                        f"P1 rc={p1.returncode} {p1.stderr.strip()[-300:]}")
        return
    receipted = got["id"] in (got["after"].get("receipts") or [])
    reads = got["after"].get("db_reads", -1) - got["before"].get("db_reads", -1)
    ok(name, "bus_proof_echo" in (held.get("held") or []) and receipted and reads == 0
       and got["after"]["pid"] != got["me"],
       f"held={held.get('held')} receipted={receipted} db_reads_during={reads} "
       f"bus_pid={got['after'].get('pid')} poster_pid={got['me']}")


def _python_files() -> list[Path]:
    out = []
    for top in ("cairn", "bin"):
        for p in (_REPO / top).rglob("*"):
            if not p.is_file() or "__pycache__" in p.parts or "validations" in p.parts:
                continue
            if p.suffix == ".py":
                out.append(p)
            elif p.suffix == "" and top == "bin":
                try:
                    head = p.open("rb").readline()
                except OSError:
                    continue
                if b"python" in head:
                    out.append(p)
    return out


def tooth_3() -> None:
    name = PROVES["48519f4789b1"]["3"]
    bus_pkg = _REPO / "cairn" / "devices" / "cairn" / "machines" / "bus"
    needle = "Bus" + "Device"
    hits = []
    for p in _python_files():
        if bus_pkg in p.parents:
            continue
        try:
            tree = ast.parse(p.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                f = node.func
                called = f.id if isinstance(f, ast.Name) else f.attr if isinstance(f, ast.Attribute) else None
                if called == needle:
                    hits.append(f"{p.relative_to(_REPO)}:{node.lineno}")
    ok(name, not hits, f"callers={hits}")


def tooth_4(home: Path) -> None:
    name = PROVES["48519f4789b1"]["4"]
    code = ("import json, os, sys, time\n"
            "from cairn.tools.base.shim import cli_main\n"
            "from cairn.devices.cairn.machines.bus.proofs.bus_proof_echo import BusProofEchoShim\n"
            "built = []\n"
            "orig = BusProofEchoShim.__init__\n"
            "def spy(self, *a, **k):\n"
            "    built.append(os.getpid()); orig(self, *a, **k)\n"
            "BusProofEchoShim.__init__ = spy\n"
            "cli_main(BusProofEchoShim, ['get', 'pid'])\n"     # first line may hold the shim
            "t = time.monotonic()\n"
            "rc = cli_main(BusProofEchoShim, ['get', 'pid'])\n"
            "dt = time.monotonic() - t\n"
            "print(json.dumps({'rc': rc, 'dt': dt, 'built_here': built, 'me': os.getpid()}))\n")
    r = _py(home, code)
    lines = r.stdout.strip().splitlines()
    try:
        meas = json.loads(lines[-1])
        answer = json.loads(lines[-2])
        bus_pid = (answer.get("data") or {}).get("pid")
    except Exception:  # noqa: BLE001
        ok(name, False, f"rc={r.returncode} out={r.stdout.strip()[-300:]} err={r.stderr.strip()[-300:]}")
        return
    running = _bus_pids(home)
    ok(name, meas["rc"] == 0 and meas["dt"] < 1.0 and not meas["built_here"]
       and bus_pid in running and bus_pid != meas["me"],
       f"rc={meas['rc']} round_trip={meas['dt']:.3f}s shims_built_in_caller={meas['built_here']} "
       f"answered_by_pid={bus_pid} bus_pids={running}")


def tooth_d1_flush(home: Path) -> None:
    name = "the spawned pulse flushes the ring through the bus process"
    _py(home, "from cairn.tools.bus_client.remote import RemoteBus\n"
              "RemoteBus().post(sender='bus_proof_courier', to='bus_proof_nobody', channel='personal',\n"
              "                 why='one-bus proof, throwaway', body={})\n")
    r = subprocess.run([sys.executable, "-m", _MODULE, "pulse", "--home", str(home)], env=_env(home),
                       cwd=str(_REPO), capture_output=True, text=True, timeout=60)
    depth = _py(home, "import json\nfrom cairn.tools.bus_client.remote import RemoteBus\n"
                      "print(json.dumps(RemoteBus().stats()))\n")
    try:
        st = json.loads(depth.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        st = {}
    ok(name, r.returncode == 0 and "flushed" in r.stdout and st.get("ring_depth") == 0,
       f"rc={r.returncode} out={r.stdout.strip()[-200:]} err={r.stderr.strip()[-200:]} ring_depth={st.get('ring_depth')}")


def tooth_d1_nobody(empty: Path) -> None:
    name = "the pulse exits 0 when no bus process is running"
    r = subprocess.run([sys.executable, "-m", _MODULE, "pulse", "--home", str(empty)], env=_env(empty),
                       cwd=str(_REPO), capture_output=True, text=True, timeout=60)
    ok(name, r.returncode == 0 and "no bus process" in (r.stdout + r.stderr) and not _bus_pids(empty),
       f"rc={r.returncode} out={(r.stdout + r.stderr).strip()[-200:]}")


def tooth_stale(home: Path) -> None:
    name = "a request from a class root the bus does not serve is refused as stale"
    code = ("import json\nfrom cairn.tools.bus_client.remote import exchange\n"
            "print(json.dumps(exchange({'op': 'stats', 'root': '/nowhere/bus-proof-root'})))\n")
    r = _py(home, code)
    try:
        reply = json.loads(r.stdout.strip().splitlines()[-1])
    except Exception:  # noqa: BLE001
        ok(name, False, f"rc={r.returncode} err={r.stderr.strip()[-300:]}")
        return
    ok(name, reply.get("ok") is False and reply.get("stale") is True, f"reply={reply}")


def tooth_reentry(home: Path) -> None:
    name = "a shim the bus hosts can reach the bus while it is being held, and nothing waits"
    spec = "cairn.devices.cairn.machines.bus.proofs.bus_proof_echo:BusProofReentrantShim"
    try:
        r = _py(home, "import json\n"
                      "from cairn.tools.bus_client.remote import RemoteBus\n"
                      f"print(json.dumps(RemoteBus().hold_shim({spec!r})))\n", timeout=30)
        held = json.loads(r.stdout.strip().splitlines()[-1]).get("held") or []
    except Exception as exc:  # noqa: BLE001 — a timeout here IS the deadlock
        ok(name, False, f"{type(exc).__name__}: {str(exc)[-300:]}")
        return
    ok(name, "bus_proof_reentrant" in held and "bus_proof_echo" in held, f"held={held}")


def tooth_sandbox(home: Path) -> None:
    """A caller in a mount namespace the user manager does not share (the tester's instance
    seal is bwrap) gets a bus spawned beside it, in its own namespace — a unit would run in
    the manager's and serve a filesystem the caller cannot see (measured 2026-10-03)."""
    name = "a caller in another mount namespace gets a bus in that namespace, not a unit outside it"
    if shutil.which("bwrap") is None:
        ok(name, False, "bwrap is not installed — the namespace this tooth needs cannot be made")
        return
    sandboxed = home / "sandboxed"
    code = ("import json, os\n"
            "from cairn.tools.bus_client.remote import ensure_bus, RemoteBus\n"
            "pid = ensure_bus()['pid']\n"
            "print(json.dumps({'mine': os.readlink('/proc/self/ns/mnt'),\n"
            "                  'bus': os.readlink(f'/proc/{pid}/ns/mnt'), 'pid': pid}))\n"
            "RemoteBus().shutdown()\n")
    env = _env(sandboxed)
    env.pop("CAIRN_BUS_UNIT", None)
    try:
        r = subprocess.run(["bwrap", "--dev-bind", "/", "/", sys.executable, "-c", code],
                           env=env, cwd=str(_REPO), capture_output=True, text=True, timeout=60)
        got = json.loads(r.stdout.strip().splitlines()[0])
    except Exception as exc:  # noqa: BLE001
        ok(name, False, f"{type(exc).__name__}: {str(exc)[-200:]} "
                        f"{getattr(locals().get('r'), 'stderr', '')[-300:]}")
        return
    ok(name, got["mine"] == got["bus"] and got["mine"] != os.readlink("/proc/self/ns/mnt"),
       f"courier={got['mine']} bus={got['bus']} outside={os.readlink('/proc/self/ns/mnt')}")


def main() -> int:
    print("one bus per instance hosts every shim")
    home = Path(tempfile.mkdtemp(prefix="bus-proof-home-"))
    empty = Path(tempfile.mkdtemp(prefix="bus-proof-empty-"))
    try:
        tooth_1(home)
        tooth_2(home)
        tooth_3()
        tooth_4(home)
        tooth_d1_flush(home)
        tooth_d1_nobody(empty)
        tooth_stale(home)
        tooth_reentry(home)
        tooth_sandbox(home)
    finally:
        _teardown(home)
        shutil.rmtree(home, ignore_errors=True)
        shutil.rmtree(empty, ignore_errors=True)
        shutil.rmtree(Path.home() / ".cairn" / "devices" / "bus_proof_echo", ignore_errors=True)
        shutil.rmtree(Path.home() / ".cairn" / "devices" / "bus_proof_reentrant", ignore_errors=True)
    print()
    if FAILURES:
        print(f"RED — {len(FAILURES)} failure(s):")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    print("GREEN — one bus process per instance, every shim inside it, the ring shared across callers.")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    raise SystemExit(main())
