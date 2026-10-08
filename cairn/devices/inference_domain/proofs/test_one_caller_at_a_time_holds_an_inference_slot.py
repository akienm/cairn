"""Proof for inference_domain — one caller at a time holds an inference slot.

Ticket d0672a46aa7e. The tester's network namespace is being retired (d80360545e91), and
its only recorded why was the 2026-07-13 incident: nine test runs saturating the single
inference slot. So the slot's owner protects it. ``host._urllib_transport`` — the one
function that opens the slot — takes an exclusive lock per endpoint, waits for it no longer
than the call's own timeout, and raises ``SlotHeld`` when the slot stays held.

Teeth a hollow build could not pass, each driven in REAL separate processes, because a lock
held inside one interpreter proves nothing about two:

  1. ONE ENDPOINT, NEVER TWO CALLERS INSIDE IT. Two processes call ``_urllib_transport``
     against one endpoint, with ``urllib.request.urlopen`` replaced in each by a stand-in that
     stamps when it enters, sleeps, and stamps when it leaves. The two intervals never overlap.
  2. A HELD SLOT REFUSES BY NAME AND NEVER DIALS. While one process holds the slot, a second
     with a short timeout raises ``SlotHeld`` carrying the endpoint and the lock path, and its
     stand-in records no call.
  3. THE LOCK IS PER ENDPOINT, NOT GLOBAL. Two processes against two different endpoints DO
     overlap. Without this tooth a single global lock would pass teeth 1 and 2 and serialize
     every host in the failover list behind the slowest.

The lock directory lives under ``$XDG_RUNTIME_DIR``, not ``~/.cairn``: the tester's instance
seal swaps ``~/.cairn`` per run, and a lock there would never be shared with a live caller.
Each tooth points ``XDG_RUNTIME_DIR`` at its own scratch directory, so the proof measures the
lock without touching the live one, and the endpoints are fixture names nobody dials.

    python3 cairn/devices/inference_domain/proofs/test_one_caller_at_a_time_holds_an_inference_slot.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROOF_TIMEOUT_S = 180

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"d0672a46aa7e": {
    "1": "test_one_endpoint_never_holds_two_callers",
    "2": "test_a_held_slot_refuses_by_name_and_never_dials",
    "3": "test_two_endpoints_do_overlap",
}}

_ENDPOINT_A = "http://slot-proof-fixture-a.invalid:11434"
_ENDPOINT_B = "http://slot-proof-fixture-b.invalid:11434"

# The child: replace urlopen with a stand-in that stamps enter/exit around a sleep, then call
# the transport once. It reports what happened as one JSON line; a SlotHeld is reported, not raised.
_CHILD = r'''
import json, sys, time, urllib.request
sys.path.insert(0, sys.argv[1])
from cairn.devices.inference_domain import host
url, hold, timeout, stamps = sys.argv[2], float(sys.argv[3]), float(sys.argv[4]), sys.argv[5]

class _Resp:
    status = 200
    def __enter__(self): return self
    def __exit__(self, *a): return False
    def read(self): return b"{}"

def stand_in(req, timeout=None):
    with open(stamps, "a") as f:
        f.write(json.dumps({"enter": time.time()}) + "\n")
    time.sleep(hold)
    with open(stamps, "a") as f:
        f.write(json.dumps({"exit": time.time()}) + "\n")
    return _Resp()

urllib.request.urlopen = stand_in
out = {"called": False}
try:
    host._urllib_transport(url + "/api/chat", b"{}", timeout)
    out["called"] = True
except Exception as e:
    out.update(error=type(e).__name__, message=str(e),
               endpoint=getattr(e, "endpoint", None), lock_path=getattr(e, "lock_path", None))
print(json.dumps(out))
'''


def _spawn(runtime: Path, url: str, hold: float, timeout: float, stamps: Path) -> subprocess.Popen:
    env = {**os.environ, "XDG_RUNTIME_DIR": str(runtime)}
    return subprocess.Popen(
        [sys.executable, "-c", _CHILD, str(_REPO_ROOT), url, str(hold), str(timeout), str(stamps)],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, env=env)


def _finish(p: subprocess.Popen) -> dict:
    out, err = p.communicate(timeout=60)
    assert p.returncode == 0, f"child crashed (exit {p.returncode}): {err[-600:]}"
    return json.loads(out.strip().splitlines()[-1])


def _interval(stamps: Path) -> tuple[float, float]:
    rows = [json.loads(l) for l in stamps.read_text().splitlines() if l.strip()]
    enter = [r["enter"] for r in rows if "enter" in r]
    exit_ = [r["exit"] for r in rows if "exit" in r]
    assert len(enter) == 1 and len(exit_) == 1, f"expected one call through the stand-in, read {rows}"
    return enter[0], exit_[0]


def _wait_for(path: Path, seconds: float) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        if path.exists() and path.read_text().strip():
            return
        time.sleep(0.02)
    raise AssertionError(f"the holding child never entered the stand-in within {seconds}s ({path})")


def test_one_endpoint_never_holds_two_callers():
    root = scratch_dir("slot_proof_fixture_one_endpoint_")
    s1, s2 = root / "first.stamps", root / "second.stamps"
    p1 = _spawn(root, _ENDPOINT_A, 1.0, 20, s1)
    p2 = _spawn(root, _ENDPOINT_A, 1.0, 20, s2)
    r1, r2 = _finish(p1), _finish(p2)
    assert r1["called"] and r2["called"], f"both callers should get the slot in turn: {r1} {r2}"
    (a0, a1), (b0, b1) = _interval(s1), _interval(s2)
    assert a1 <= b0 or b1 <= a0, \
        f"two callers were inside one endpoint at once: [{a0:.3f}, {a1:.3f}] and [{b0:.3f}, {b1:.3f}]"


def test_a_held_slot_refuses_by_name_and_never_dials():
    from cairn.devices.inference_domain import host
    assert getattr(host, "SlotHeld", None) is not None, "host publishes no SlotHeld"
    root = scratch_dir("slot_proof_fixture_held_")
    holder_stamps, waiter_stamps = root / "holder.stamps", root / "waiter.stamps"
    holder = _spawn(root, _ENDPOINT_A, 3.0, 20, holder_stamps)
    try:
        _wait_for(holder_stamps, 20)
        waiter = _finish(_spawn(root, _ENDPOINT_A, 0.0, 0.5, waiter_stamps))
    finally:
        held = _finish(holder)
    assert held["called"], f"the holder never got the slot: {held}"
    assert waiter.get("error") == "SlotHeld", f"a caller past its timeout must raise SlotHeld: {waiter}"
    assert not waiter["called"] and not waiter_stamps.exists(), \
        f"the refused caller reached urlopen anyway: {waiter}"
    assert waiter.get("endpoint") and "slot-proof-fixture-a.invalid" in waiter["endpoint"], \
        f"SlotHeld does not carry the endpoint: {waiter}"
    lock = waiter.get("lock_path") or ""
    assert lock.startswith(str(root)) and lock.endswith(".lock"), \
        f"SlotHeld does not carry a lock path under $XDG_RUNTIME_DIR ({root}): {waiter}"
    assert waiter["endpoint"] in waiter["message"] and lock in waiter["message"], \
        f"the message must name the endpoint and the lock path: {waiter['message']}"


def test_two_endpoints_do_overlap():
    root = scratch_dir("slot_proof_fixture_two_endpoints_")
    s1, s2 = root / "a.stamps", root / "b.stamps"
    p1 = _spawn(root, _ENDPOINT_A, 1.5, 20, s1)
    p2 = _spawn(root, _ENDPOINT_B, 1.5, 20, s2)
    r1, r2 = _finish(p1), _finish(p2)
    assert r1["called"] and r2["called"], f"both callers should get their own slot: {r1} {r2}"
    (a0, a1), (b0, b1) = _interval(s1), _interval(s2)
    assert a0 < b1 and b0 < a1, \
        f"two endpoints were serialized — the lock is global, not per endpoint: [{a0:.3f}, {a1:.3f}] and [{b0:.3f}, {b1:.3f}]"


def _main() -> int:
    checks = [
        test_one_endpoint_never_holds_two_callers,
        test_a_held_slot_refuses_by_name_and_never_dials,
        test_two_endpoints_do_overlap,
    ]
    # EVERY TOOTH PRINTS, red ones too, so a red names which clause fell.
    failed = []
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as e:  # noqa: BLE001 — a crash in a tooth is that tooth's red
            failed.append(check.__name__)
            print(f"  FAIL  {check.__name__}: {type(e).__name__}: {e}")
    if failed:
        print(f"red — {len(failed)} of {len(checks)} teeth failed")
        return 1
    print("green — one caller at a time holds an inference slot, per endpoint")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
