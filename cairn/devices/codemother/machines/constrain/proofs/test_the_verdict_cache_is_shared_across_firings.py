"""Proof for ticket 070c5fc9624c: constrain's instrument verdicts are shared across chart firings.

Measured 2026-11-04 (idea a85d2085d851): _RUN_CACHE is a per-process dict, so parallel chart
firings each re-ran the same unsealed proofs through the tester, and constrain timed out.
The verdict for one (path, source fingerprint) is now persisted under the codemother
instance's run_cache, read by any later process within the TTL, and asked once under a lock.

Every tooth runs constrain in fresh subprocesses, so an in-memory dict cannot pass it. The
asker is the injected tester call (D7); each call appends one line to a count file.

  1. test_a_second_process_reads_the_persisted_verdict: two processes in turn, one asker call.
  2. test_two_concurrent_processes_ask_once: two processes started together, one asker call.
  3. test_a_changed_file_asks_again: new bytes, new fingerprint, a second asker call.
  4. test_a_raising_asker_leaves_no_entry: the store stays empty and the next process asks.
  5. test_an_expired_entry_is_not_read: an entry older than _TTL_S is a miss.

    python3 cairn/devices/codemother/machines/constrain/proofs/test_the_verdict_cache_is_shared_across_firings.py
"""
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[5]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"070c5fc9624c": {
    "1": "test_a_second_process_reads_the_persisted_verdict",
    "2": "test_two_concurrent_processes_ask_once",
    "3": "test_a_changed_file_asks_again",
    "4": "test_a_raising_asker_leaves_no_entry",
    "5": "test_an_expired_entry_is_not_read",
}}

# One firing in a fresh process. constrain is bound by importlib at call time, so the
# hollow reading (constrain.py taken away) fails here rather than at the proof's import.
_FIRING = r"""
import importlib, json, sys, time
sys.path.insert(0, sys.argv[1])
root, rel, store, count, mode = sys.argv[2:7]
c = importlib.import_module("cairn.devices.codemother.machines.constrain.constrain")
def asker(abs_path):
    with open(count, "a") as f:
        f.write(abs_path + "\n")
    if mode == "raise":
        raise ConnectionError("the tester is unreachable")
    time.sleep(1.0)
    return {"verdict": "green"}
state = c._run_instrument(rel, root=root, store_dir=store, asker=asker)
print(json.dumps(state))
"""


class _World:
    """A temp root holding one proof file, a store dir and a count file."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="cairn-runcache-")
        self.root = Path(self.tmp.name) / "root"
        self.store = Path(self.tmp.name) / "store"
        self.count = Path(self.tmp.name) / "asked.txt"
        self.rel = "proofs/test_something.py"
        (self.root / "proofs").mkdir(parents=True)
        self.write("print('ok')\n")

    def write(self, text):
        (self.root / self.rel).write_text(text)

    def start(self, mode="ok"):
        return subprocess.Popen(
            [sys.executable, "-c", _FIRING, str(ROOT), str(self.root), self.rel,
             str(self.store), str(self.count), mode],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    def fire(self, mode="ok"):
        return self.finish(self.start(mode))

    @staticmethod
    def finish(proc):
        out, err = proc.communicate(timeout=120)
        assert proc.returncode == 0, f"the firing crashed: {err[-800:]}"
        return json.loads(out.strip().splitlines()[-1])

    def asked(self):
        return len(self.count.read_text().splitlines()) if self.count.exists() else 0

    def entries(self):
        return sorted(self.store.glob("*.json")) if self.store.is_dir() else []

    def close(self):
        self.tmp.cleanup()


def test_a_second_process_reads_the_persisted_verdict() -> None:
    w = _World()
    try:
        first = w.fire()
        assert first["verdict"] == "green", first
        second = w.fire()
        assert second["verdict"] == "green", second
        assert w.asked() == 1, f"two processes made {w.asked()} asker calls; the second should read the store"
    finally:
        w.close()
    print("ok test_a_second_process_reads_the_persisted_verdict")


def test_two_concurrent_processes_ask_once() -> None:
    w = _World()
    try:
        a, b = w.start(), w.start()
        states = [w.finish(a), w.finish(b)]
        assert all(s["verdict"] == "green" for s in states), states
        assert w.asked() == 1, f"two concurrent processes made {w.asked()} asker calls on one key"
    finally:
        w.close()
    print("ok test_two_concurrent_processes_ask_once")


def test_a_changed_file_asks_again() -> None:
    w = _World()
    try:
        w.fire()
        w.write("print('changed')\n")
        w.fire()
        assert w.asked() == 2, f"new bytes made {w.asked()} asker calls in total; expected a fresh ask"
    finally:
        w.close()
    print("ok test_a_changed_file_asks_again")


def test_a_raising_asker_leaves_no_entry() -> None:
    w = _World()
    try:
        state = w.fire("raise")
        assert state["verdict"] == "unrunnable", state
        assert w.entries() == [], f"an unrunnable was persisted: {w.entries()}"
        state = w.fire()
        assert state["verdict"] == "green", state
        assert w.asked() == 2, f"after a raising asker, {w.asked()} calls; the next process should ask"
    finally:
        w.close()
    print("ok test_a_raising_asker_leaves_no_entry")


def test_an_expired_entry_is_not_read() -> None:
    import importlib
    ttl = importlib.import_module("cairn.devices.codemother.machines.constrain.constrain")._TTL_S
    w = _World()
    try:
        w.fire()
        entries = w.entries()
        assert len(entries) == 1, f"expected one persisted entry, found {entries}"
        entry = json.loads(entries[0].read_text())
        entry["written_at"] = time.time() - ttl - 60
        entries[0].write_text(json.dumps(entry))
        w.fire()
        assert w.asked() == 2, f"an entry older than _TTL_S was read ({w.asked()} asker calls)"
    finally:
        w.close()
    print("ok test_an_expired_entry_is_not_read")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
