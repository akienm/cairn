"""Proof for ticket 7507a6051073: a child of the bus starts with the stop signals unblocked.

MEASURED 2026-11-19 (akienasus_cc_0, walking 287e241f61f3): ``_signal_stops`` blocks SIGHUP,
SIGINT and SIGTERM for the bus's whole life (``/proc/<bus>/status`` SigBlk 0x4003). A blocked
mask survives fork and exec, so every instrument a verdict held by the bus ran started deaf to
SIGTERM, and the ground_loop proof's --force tooth timed out on a child it could not stop.

Each tooth runs the real ``serve`` at a scratch home through a driver that replaces
``serve_forever`` on the server class with the work a device held by the bus does: it spawns
from a worker thread, which inherits the bus's mask like every handler thread does.

  1. test_a_child_the_bus_spawns_starts_with_the_stop_signals_unblocked: a ``subprocess``
     child's /proc/self/status SigBlk carries none of HUP, INT, TERM while the spawning thread
     still blocks all three; a ``sleep 30`` child sent SIGTERM is gone within 5 s, by that
     signal; and an ``os.fork`` child's mask carries none of the three;
  2. test_a_sigterm_from_a_child_still_names_its_sender: a child the bus spawned sends the bus
     SIGTERM, and stops.jsonl records cause 'signal' with that child's pid as sender (D3 of
     ticket 73c58a1dcad7 holds under the fix);
  3. test_the_watch_reads_blocked_descendants_and_nameless_stops: the WATCHME probe's survey,
     over a scratch bus home and a scratch /proc, counts the descendants of the bus with a stop
     signal blocked and the signal stops after the era that name no sender, and its holds
     predicate is true only when none is blocked and at most 1 is nameless.

The server module is imported by the driver at run time, never by this proof.

    python3 cairn/devices/cairn/machines/bus/proofs/test_a_child_of_the_bus_starts_with_the_stop_signals_unblocked.py
"""
from __future__ import annotations

import json
import os
import signal
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"7507a6051073": {
    "1": "test_a_child_the_bus_spawns_starts_with_the_stop_signals_unblocked",
    "2": "test_a_sigterm_from_a_child_still_names_its_sender",
    "3": "test_the_watch_reads_blocked_descendants_and_nameless_stops",
}}

_STOP_BITS = {"SIGHUP": 1 << (signal.SIGHUP - 1), "SIGINT": 1 << (signal.SIGINT - 1),
              "SIGTERM": 1 << (signal.SIGTERM - 1)}
_RUN_S = 90

# serve() with serve_forever replaced by what a held device does: work on a worker thread,
# whose mask is the bus's. The readings land in <home>/readings.json; then it returns.
_DRIVER = r"""
import json, os, signal, subprocess, sys, threading, time
from pathlib import Path
sys.path.insert(0, sys.argv[1])
home, mode = Path(sys.argv[2]), sys.argv[3]
from cairn.devices.cairn.machines.bus import server
from cairn.devices.cairn.machines.bus.bus import BusDevice

def _sigblk(text):
    for line in text.splitlines():
        if line.startswith("SigBlk:"):
            return int(line.split()[1], 16)
    return None

def _work(out):
    out["thread_mask"] = sorted(int(s) for s in signal.pthread_sigmask(signal.SIG_BLOCK, []))
    if mode == "spawn":
        r = subprocess.run(["cat", "/proc/self/status"], capture_output=True, text=True, timeout=30)
        out["child_sigblk"] = _sigblk(r.stdout)
        p = subprocess.Popen(["sleep", "30"])
        time.sleep(0.2)
        t0 = time.monotonic()
        p.send_signal(signal.SIGTERM)
        try:
            out["sleep_exit"] = p.wait(timeout=5)
        except subprocess.TimeoutExpired:
            out["sleep_exit"] = "alive after 5 s"
            p.kill(); p.wait()
        out["sleep_s"] = round(time.monotonic() - t0, 2)
        rd, wr = os.pipe()
        pid = os.fork()
        if pid == 0:
            os.close(rd)
            with open("/proc/self/status") as fh:
                os.write(wr, str(_sigblk(fh.read())).encode())
            os._exit(0)
        os.close(wr)
        out["fork_sigblk"] = int(os.read(rd, 64) or b"-1")
        os.waitpid(pid, 0)
    elif mode == "killer":
        p = subprocess.Popen(["sh", "-c", "echo $$; kill -TERM %d; sleep 5" % os.getpid()],
                             stdout=subprocess.PIPE, text=True)
        out["killer_pid"] = int(p.stdout.readline())
        p.wait(timeout=30)

def _forever(self, poll_interval=0.5):
    out = {}
    t = threading.Thread(target=_work, args=(out,))
    t.start(); t.join(60)
    (home / "readings.json").write_text(json.dumps(out))
    return None

server._Server.serve_forever = _forever
with BusDevice.scratch("bus_child_mask_proof") as bus:
    sys.exit(server.serve(home, bus, lan=0, scratch=True))
"""


def _run(mode: str) -> tuple[dict, list[dict], str]:
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("testing-7507a6051073-bus-child-")
    env = dict(os.environ)
    env["CAIRN_BUS_HOME"] = str(home)
    env["PYTHONPATH"] = str(_REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    r = subprocess.run([sys.executable, "-c", _DRIVER, str(_REPO), str(home), mode],
                       cwd=str(_REPO), env=env, stdin=subprocess.DEVNULL, capture_output=True,
                       text=True, timeout=_RUN_S)
    said = (r.stdout + r.stderr)[-1200:]
    path = home / "readings.json"
    assert path.is_file(), f"the driver wrote no readings (exit {r.returncode}): {said}"
    stops = home / "stops.jsonl"
    lines = [json.loads(x) for x in stops.read_text().splitlines() if x.strip()] if stops.is_file() else []
    return json.loads(path.read_text()), lines, said


def _blocked(mask: int | None) -> list[str]:
    assert isinstance(mask, int), f"no SigBlk read: {mask!r}"
    return [n for n, bit in _STOP_BITS.items() if mask & bit]


def test_a_child_the_bus_spawns_starts_with_the_stop_signals_unblocked():
    out = _run("spawn")[0]
    held = {signal.Signals(s).name for s in out["thread_mask"]}
    assert set(_STOP_BITS) <= held, f"the bus thread no longer blocks the stop signals: {sorted(held)}"
    blocked = _blocked(out["child_sigblk"])
    assert not blocked, (f"a subprocess child the bus spawned starts with {blocked} blocked "
                         f"(SigBlk {out['child_sigblk']:#x})")
    assert out["sleep_exit"] == -signal.SIGTERM, (
        f"a child the bus spawned, sent SIGTERM, returned {out['sleep_exit']!r} "
        f"after {out['sleep_s']} s")
    blocked = _blocked(out["fork_sigblk"])
    assert not blocked, f"an os.fork child of the bus starts with {blocked} blocked"


def test_a_sigterm_from_a_child_still_names_its_sender():
    out, lines, said = _run("killer")
    assert len(lines) == 1, f"expected one stop line, got {lines!r}; bus said {said}"
    detail = lines[0].get("detail") or {}
    assert lines[0].get("cause") == "signal" and detail.get("signal") == "SIGTERM", lines[0]
    assert detail.get("sender_pid") == out["killer_pid"], (
        f"sender_pid {detail.get('sender_pid')!r}, the sender was {out['killer_pid']}")


def test_the_watch_reads_blocked_descendants_and_nameless_stops():
    import datetime
    from cairn.devices.cairn.machines.bus.probes import a_child_of_the_bus_starts_clean as watch
    from cairn.tools.scratch.scratch import scratch_dir
    root = scratch_dir("testing-7507a6051073-watch-")
    home, proc = root / "bus", root / "proc"
    home.mkdir()
    (home / "bus.port").write_text(json.dumps({"pid": 100}))
    era = datetime.datetime(2026, 11, 19, 12, 0, 0)
    rows = [("2026-11-19T11:00:00", None), ("2026-11-19T13:00:00", None),
            ("2026-11-19T13:30:00", 4242), ("2026-11-19T14:00:00", None)]
    (home / "stops.jsonl").write_text("".join(json.dumps(
        {"at": at, "cause": "signal", "detail": {"signal": "SIGTERM", "sender_pid": who}}) + "\n"
        for at, who in rows) + json.dumps({"at": "2026-11-19T15:00:00", "cause": "stop_verb"}) + "\n")
    for pid, ppid, blk in ((100, 1, "0000000000004003"), (101, 100, "0000000000000000"),
                           (102, 101, "0000000000004000"), (103, 1, "0000000000004003")):
        (proc / str(pid)).mkdir(parents=True)
        (proc / str(pid) / "status").write_text(f"Name:\tx\nPPid:\t{ppid}\nSigBlk:\t{blk}\n")
    s = watch.survey(home, era, proc)
    assert s["bus_pid"] == 100 and s["descendants"] == 2, s
    assert s["blocked"] == [{"pid": 102, "blocked": ["SIGTERM"]}], s["blocked"]
    assert (s["signal_stops"], s["null_senders"]) == (3, 2), s
    assert not s["unreadable"], s["unreadable"]
    assert watch._holds({"survey": s}) is False, s
    assert watch._holds({"survey": dict(s, blocked=[])}) is False, "two nameless stops still hold"
    assert watch._holds({"survey": dict(s, blocked=[], null_senders=1)}) is True

if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
