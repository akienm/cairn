"""Proof for ticket 73c58a1dcad7 — every stop of the bus process records its cause.

MEASURED 2026-10-05: the live bus (pid 3498615) ended at 16:36:00 during a chart's proof runs
and nothing recorded why. systemd logged only CPU and memory, and the bus home held no log. A
proof that can stop the bus has to be named by the stop itself.

Each tooth starts a bus over a scratch table (``serve --scratch``, ``--lan 0``) at a scratch
home, stops it one way, and reads ``<home>/stops.jsonl``. After each stop the record holds
exactly one new line naming that cause, and a positive maxrss.

  1. test_sigterm_names_the_signal_and_its_sender: cause 'signal', SIGTERM, sender = this pid;
  2. test_sigint_names_the_signal_and_its_sender: the same for SIGINT;
  3. test_an_exception_in_serve_forever_names_its_type: serve_forever raises; cause
     'exception', the type, the message and a traceback;
  4. test_a_clean_return_says_clean: serve_forever returns with nothing asked; cause 'clean';
  5. test_the_shutdown_verb_names_its_caller: op shutdown over the socket; cause 'verb',
     op 'shutdown', caller pid = this pid.

Teeth 3 and 4 run ``serve`` through a driver that replaces ``serve_forever`` on the server
class (``server._Server``), which is the only way to make serve_forever raise or return on
cue. The server module is imported by the driver at run time, never by this proof.

    python3 cairn/devices/cairn/machines/bus/proofs/test_every_stop_records_its_cause.py
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"73c58a1dcad7": {
    "1": "test_sigterm_names_the_signal_and_its_sender",
    "2": "test_sigint_names_the_signal_and_its_sender",
    "3": "test_an_exception_in_serve_forever_names_its_type",
    "4": "test_a_clean_return_says_clean",
    "5": "test_the_shutdown_verb_names_its_caller",
}}

_MODULE = "cairn.devices.cairn.machines.bus"
_START_S = 30.0
_STOP_S = 30.0

# serve() with serve_forever replaced: 'raise' raises inside it, 'clean' returns from it.
_DRIVER = r"""
import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
home, mode = Path(sys.argv[2]), sys.argv[3]
from cairn.devices.cairn.machines.bus import server
from cairn.devices.cairn.machines.bus.bus import BusDevice
def _forever(self, poll_interval=0.5):
    if mode == "raise":
        raise RuntimeError("testing-73c58a1dcad7 raised inside serve_forever")
    return None
server._Server.serve_forever = _forever
with BusDevice.scratch("bus_stop_proof") as bus:
    sys.exit(server.serve(home, bus, lan=0, scratch=True))
"""


def _home() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("testing-73c58a1dcad7-bus-stop-")


def _env(home: Path) -> dict:
    env = dict(os.environ)
    env["CAIRN_BUS_HOME"] = str(home)
    env["PYTHONPATH"] = str(_REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _stops(home: Path) -> list[dict]:
    path = home / "stops.jsonl"
    if not path.is_file():
        return []
    return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]


def _serve(home: Path) -> subprocess.Popen:
    """A real bus process at ``home``, answering on bus.sock when this returns."""
    proc = subprocess.Popen(
        [sys.executable, "-m", _MODULE, "serve", "--home", str(home), "--scratch", "--lan", "0"],
        cwd=str(_REPO), env=_env(home), stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    deadline = time.monotonic() + _START_S
    while time.monotonic() < deadline:
        if (home / "bus.sock").exists():
            return proc
        if proc.poll() is not None:
            raise AssertionError(f"the bus exited {proc.returncode} before it answered: "
                                 f"{proc.stdout.read()[-800:]}")
        time.sleep(0.05)
    proc.kill()
    raise AssertionError(f"no bus.sock at {home} within {_START_S:.0f}s")


def _stopped(proc: subprocess.Popen) -> str:
    try:
        out, _ = proc.communicate(timeout=_STOP_S)
    except subprocess.TimeoutExpired:
        proc.kill()
        out, _ = proc.communicate()
        raise AssertionError(f"the bus did not stop within {_STOP_S:.0f}s: {out[-800:]}")
    return out


def _one_line(home: Path, out: str) -> dict:
    lines = _stops(home)
    assert len(lines) == 1, f"expected one stop line, got {len(lines)}: {lines!r}; bus said {out[-800:]}"
    line = lines[0]
    assert isinstance(line.get("maxrss"), int) and line["maxrss"] > 0, f"no positive maxrss: {line!r}"
    assert line.get("pid") and line.get("at"), f"the line lacks pid or at: {line!r}"
    return line


def _signal_tooth(sig: signal.Signals) -> None:
    home = _home()
    proc = _serve(home)
    proc.send_signal(sig)
    out = _stopped(proc)
    line = _one_line(home, out)
    assert line.get("pid") == proc.pid, f"the line names pid {line.get('pid')}, the bus was {proc.pid}"
    assert line.get("cause") == "signal", f"cause is {line.get('cause')!r}: {line!r}"
    detail = line.get("detail") or {}
    assert detail.get("signal") == sig.name, f"signal is {detail.get('signal')!r}, sent {sig.name}"
    assert detail.get("sender_pid") == os.getpid(), (
        f"sender_pid is {detail.get('sender_pid')!r}, the sender was {os.getpid()}")


def test_sigterm_names_the_signal_and_its_sender():
    _signal_tooth(signal.SIGTERM)


def test_sigint_names_the_signal_and_its_sender():
    _signal_tooth(signal.SIGINT)


def _driven(mode: str) -> tuple[Path, subprocess.CompletedProcess]:
    home = _home()
    r = subprocess.run([sys.executable, "-c", _DRIVER, str(_REPO), str(home), mode],
                       cwd=str(_REPO), env=_env(home), capture_output=True, text=True,
                       timeout=_START_S + _STOP_S)
    return home, r


def test_an_exception_in_serve_forever_names_its_type():
    home, r = _driven("raise")
    assert r.returncode != 0, "an exception inside serve_forever must still end the process loud"
    line = _one_line(home, r.stdout + r.stderr)
    assert line.get("cause") == "exception", f"cause is {line.get('cause')!r}: {line!r}"
    detail = line.get("detail") or {}
    assert detail.get("type") == "RuntimeError", detail
    assert "testing-73c58a1dcad7" in (detail.get("message") or ""), detail
    tb = detail.get("traceback") or ""
    assert "_forever" in tb and "RuntimeError" in tb, f"no traceback through the raise: {tb[-400:]!r}"


def test_a_clean_return_says_clean():
    home, r = _driven("clean")
    assert r.returncode == 0, f"a clean return exits 0, got {r.returncode}: {r.stderr[-800:]}"
    line = _one_line(home, r.stdout + r.stderr)
    assert line.get("cause") == "clean", f"cause is {line.get('cause')!r}: {line!r}"


def test_the_shutdown_verb_names_its_caller():
    from cairn.tools.bus_client.remote import exchange
    home = _home()
    proc = _serve(home)
    reply = exchange({"op": "shutdown"}, home, timeout=30)
    out = _stopped(proc)
    line = _one_line(home, out)
    assert line.get("cause") == "verb", f"cause is {line.get('cause')!r}: {line!r}; reply {reply!r}"
    detail = line.get("detail") or {}
    assert detail.get("op") == "shutdown", detail
    assert detail.get("caller_pid") == os.getpid(), (
        f"caller_pid is {detail.get('caller_pid')!r}, the caller was {os.getpid()}")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
