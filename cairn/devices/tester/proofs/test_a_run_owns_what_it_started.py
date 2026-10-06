"""A tester run owns what it started (ticket bf3c16162827, child of 71d1bbfa98b0; re-plan step 4).

Akien, 2026-10-05 (/home/akien/.cairn/foreground-decisions.md 8d, 8e): the tester "can throw
away (to logging) most of what it does. all we need are the results"; a returned testing
artifact means "Yep, got here", and "the tester would see that it's a returning message, from
test abcdefg, and that test can now be marked complete". He also agreed the tester kills what
the run started (8e). Measured 2026-10-05 (8c): two scratch bus servers had leaked from proof
runs, one up 2d9h.

So every run_proof mints a test id, hands it to its subject as CAIRN_TESTER_TEST_ID (the mark a
proof puts on what it sends, testing_mark.mark(<that id>)), and afterwards owns everything
carrying it:

  1. A RUN HANDS ITS SUBJECT A TEST ID: the subject sees CAIRN_TESTER_TEST_ID; the record's
     evidence carries the same id under "test"; two runs never share one; and the id stays out
     of the measured conditions, which digest every CAIRN_ variable (f0aad0cd0f56), or every
     green over a red would read as conditions moved.
  2. A RETURN IS MATCHED TO ITS TEST: a return delivered to the tester's shim is written to that
     test's run log (who returned it, what verb it was), nothing is posted and no device wakes,
     and the run whose id it carries reports it in evidence "returns".
  3. THE RUN'S FULL OUTPUT GOES TO LOGGING: the record keeps a 20-line tail (a diagnostic
     surface); the whole stdout and stderr land in the run's log directory under
     address.log_path('tester'), which the cairn device forgets after 30 days.
  4. WHAT THE RUN STARTED IS KILLED: a process the subject started in its own session
     (setsid, so a process-group kill would miss it) is dead after the run, and evidence
     "killed" names it.
  5. A TIMED-OUT RUN LEAVES NOTHING RUNNING: the same, when the subject itself hangs past its
     budget.

Every tooth imports the tester inside its body, so a reverted file reds teeth rather than this
file's import. Fixture subjects live in scratch directories; run logs land under the live
logs tree, named test-<12 hex>, and age out with it.

    python3 cairn/devices/tester/proofs/test_a_run_owns_what_it_started.py
"""
from __future__ import annotations

import json
import os
import re
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"bf3c16162827": {
    "1": "test_a_run_hands_its_subject_a_test_id",
    "2": "test_a_return_is_matched_to_its_test",
    "3": "test_the_runs_full_output_goes_to_logging",
    "4": "test_what_the_run_started_is_killed",
    "5": "test_a_timed_out_run_leaves_nothing_running",
}}

_ENV = "CAIRN_TESTER_TEST_ID"
_ID = re.compile(r"^test-[0-9a-f]{12}$")

_SEES_ID = f'''import os
print("SAW " + os.environ.get("{_ENV}", ""))
print("ok   test_fixture_tooth")
'''
_CHATTY = '''import sys
for i in range(50):
    print(f"line {i}")
for i in range(30):
    print(f"err {i}", file=sys.stderr)
print("ok   test_fixture_tooth")
'''
_LEAKS = '''import subprocess, sys
p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)"], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print(f"CHILD {p.pid}")
print("ok   test_fixture_tooth")
'''
_LEAKS_THEN_HANGS = '''import subprocess, sys, time
p = subprocess.Popen([sys.executable, "-c", "import time; time.sleep(300)"], start_new_session=True,
                     stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
open(sys.argv[0] + ".child", "w").write(str(p.pid))
time.sleep(300)
'''


def _proof(prefix: str, body: str) -> Path:
    root = scratch_dir(prefix) / "fixture_component"
    (root / "proofs").mkdir(parents=True)
    proof = root / "proofs" / "test_fixture.py"
    proof.write_text(body)
    return proof


def _run(proof: Path, timeout: int = 60) -> dict:
    from cairn.devices.tester.device import TesterDevice
    return TesterDevice().run_proof(proof, sink="none", caller="proof-fixture-bf3c",
                                    timeout=timeout, isolation="none")


def _run_dir(test: str) -> Path:
    from cairn.tools.base.address import log_path
    return log_path("tester") / "runs" / test


def _alive(pid: int) -> bool:
    """Running, not a zombie waiting on a reaper."""
    try:
        stat = Path(f"/proc/{pid}/stat").read_text()
    except OSError:
        return False
    return stat.rsplit(")", 1)[1].split()[0] != "Z"


def _stdout_line(rec: dict, prefix: str) -> str:
    for line in (rec["evidence"].get("stdout_tail") or "").splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    raise AssertionError(f"no {prefix!r} line in {rec['evidence'].get('stdout_tail')!r}")


def test_a_run_hands_its_subject_a_test_id():
    proof = _proof("cairn-bf3c-1-", _SEES_ID)
    first, second = _run(proof), _run(proof)
    for rec in (first, second):
        assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
        test = rec["evidence"].get("test")
        assert isinstance(test, str) and _ID.match(test), f"no minted test id in evidence: {test!r}"
        assert _stdout_line(rec, "SAW ") == test, "the subject did not see the run's test id"
        assert _ENV not in (rec["evidence"]["conditions"].get("env") or {}), \
            "the per-run id rides the measured conditions, so every run would read as conditions moved"
    assert first["evidence"]["test"] != second["evidence"]["test"], "two runs shared one test id"


class _SpyBus:
    def __init__(self) -> None:
        self.posted: list = []

    def post(self, **envelope):
        self.posted.append(envelope)
        return envelope

    def wire_delivery(self, device_id, deliver):
        pass


def test_a_return_is_matched_to_its_test():
    import cairn.devices.tester.device as device_mod
    from cairn.devices.tester.shim import TesterShim
    from cairn.tools.base import testing_mark as tm
    minted = "test-" + os.urandom(6).hex()

    started: list = []
    bus = _SpyBus()
    shim = TesterShim(bus=bus)
    shim._start_device = lambda: started.append(1)
    shim.emit = lambda *a, **kw: None
    back = {"id": "ret-bf3c", "sender": "codemother", "addressee": "tester", "reply_to": "env-bf3c",
            "body": {tm.FIELD: tm.mark(minted), "is_return": True,
                     "original_verb": "ping", "original_addressee": "codemother"}}
    result = shim.deliver(back)
    assert isinstance(result, dict) and result.get("handled") is True, f"the return was not handled: {result}"
    assert bus.posted == [] and started == [], "a return posted mail or woke the device"
    ledger = _run_dir(minted) / "returns.jsonl"
    assert ledger.is_file(), f"no return written at {ledger}"
    lines = [json.loads(x) for x in ledger.read_text().splitlines() if x.strip()]
    assert [(r.get("from"), r.get("original_verb")) for r in lines] == [("codemother", "ping")], lines

    saved = device_mod.mint_test_id
    device_mod.mint_test_id = lambda: minted
    try:
        rec = _run(_proof("cairn-bf3c-2-", _SEES_ID))
    finally:
        device_mod.mint_test_id = saved
    returns = rec["evidence"].get("returns")
    assert isinstance(returns, list) and [r.get("from") for r in returns] == ["codemother"], \
        f"the run did not report its test's return: {returns!r}"


def test_the_runs_full_output_goes_to_logging():
    rec = _run(_proof("cairn-bf3c-3-", _CHATTY))
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    run = _run_dir(rec["evidence"]["test"])
    out = (run / "stdout.txt").read_text() if (run / "stdout.txt").is_file() else ""
    err = (run / "stderr.txt").read_text() if (run / "stderr.txt").is_file() else ""
    assert all(f"line {i}\n" in out for i in range(50)), f"stdout not kept whole in {run}"
    assert all(f"err {i}\n" in err for i in range(30)), f"stderr not kept whole in {run}"
    assert len(rec["evidence"]["stdout_tail"].splitlines()) <= 20, "the record's tail grew"


def test_what_the_run_started_is_killed():
    rec = _run(_proof("cairn-bf3c-4-", _LEAKS))
    assert rec["verdict"] == "green", rec["evidence"].get("stderr_tail")
    pid = int(_stdout_line(rec, "CHILD "))
    deadline = time.time() + 5
    while _alive(pid) and time.time() < deadline:
        time.sleep(0.1)
    try:
        assert not _alive(pid), f"pid {pid}, started by the run in its own session, outlived it"
        killed = rec["evidence"].get("killed")
        assert isinstance(killed, list) and pid in [k.get("pid") for k in killed], \
            f"evidence does not name the killed process: {killed!r}"
    finally:
        if _alive(pid):
            os.kill(pid, 9)


def test_a_timed_out_run_leaves_nothing_running():
    proof = _proof("cairn-bf3c-5-", _LEAKS_THEN_HANGS)
    rec = _run(proof, timeout=3)
    assert rec["verdict"] == "red" and "timed out" in str(rec["evidence"].get("stderr_tail")), rec["evidence"]
    pid = int(Path(str(proof) + ".child").read_text())
    deadline = time.time() + 5
    while _alive(pid) and time.time() < deadline:
        time.sleep(0.1)
    try:
        assert not _alive(pid), f"pid {pid} outlived a timed-out run"
        assert pid in [k.get("pid") for k in rec["evidence"].get("killed") or []], rec["evidence"].get("killed")
    finally:
        if _alive(pid):
            os.kill(pid, 9)


def main() -> int:
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
                print(f"  ok   {name}")
            except Exception as exc:  # noqa: BLE001
                fails += 1
                print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
