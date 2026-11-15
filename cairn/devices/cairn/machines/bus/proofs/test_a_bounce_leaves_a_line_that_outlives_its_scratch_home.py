"""PROOF for ticket 2a6adebdd79b: a no_receiver bounce leaves a line of the bus's wake state
that outlives its scratch HOME.

Measured 2026-11-14: 69cd150dc116's two real reds ("codemother's shim could not take the
envelope") left nothing but the refusal text. The scratch HOMEs holding their bus logs were
swept, and five reproduction shapes were green, so the bus's state at the bounce was never
measured. ``BusProcess.no_receiver`` wrote no line at a bounce.

One tooth per falsifier clause:

  (1) a bounce in a scratch-HOME bus process with test id T writes exactly one line for the
      letter at the ACCOUNT's tester run dir (runs/T/bus-bounces.jsonl), naming hook_before,
      hook_after, wired_before, wired_after, shim_class, bus_pid, bus_started, reason and the
      envelope id;
  (2) that line still reads after the launch block exits and its scratch HOME is swept;
  (3) with no test id the line lands in the account bus log, and a delivered post writes none;
  (4) an unwritable destination still bounces the letter to its sender and emits
      bounce_record_failed.

Clauses 1-2 launch a real bus process under a scratch HOME (scratch_bus.launch, holding
harbor_master, the sender), the shape both reds ran in. Clauses 3-4 run an in-process
``BusDevice.scratch`` bus. Every name is ``testing-2a6a-...``; the fixture run dir under the
account's logs is trashed at the end, never removed.

    PYTHONPATH=. python3 cairn/devices/cairn/machines/bus/proofs/test_a_bounce_leaves_a_line_that_outlives_its_scratch_home.py
"""
from __future__ import annotations

import contextlib
import json
import os
import secrets
import shutil
import subprocess
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.address import log_path  # noqa: E402
from cairn.tools.scratch.scratch import account_home  # noqa: E402

PROVES = {"2a6adebdd79b": {
    "1": "test_a_bounce_in_a_scratch_home_bus_writes_one_line_at_the_account_run_dir",
    "2": "test_the_line_still_reads_after_the_scratch_home_is_swept",
    "3": "test_outside_a_run_the_line_lands_in_the_bus_log_and_a_delivery_writes_none",
    "4": "test_an_unwritable_destination_still_bounces_and_is_loud",
}}

FIELDS = ("envelope", "hook_before", "hook_after", "wired_before", "wired_after", "shim_class",
          "bus_pid", "bus_started", "reason")
RUN_ID = f"testing-2a6a-{secrets.token_hex(4)}"
_ROOTS = {"instance": account_home() / ".cairn"}
RUN_LOG = log_path("tester", roots=_ROOTS) / "runs" / RUN_ID / "bus-bounces.jsonl"
BUS_LOG = log_path("cairn", roots=_ROOTS) / "machines" / "bus" / "0" / "bounces.jsonl"

_SCRATCH = contextlib.ExitStack()
_LAUNCHED: dict = {}


def _lines(path: Path, envelope_id: str) -> list[dict]:
    if not path.is_file():
        return []
    out = []
    for raw in path.read_text().splitlines():
        try:
            rec = json.loads(raw)
        except ValueError:
            continue
        if rec.get("envelope") == envelope_id:
            out.append(rec)
    return out


def _launched() -> dict:
    """One launched world for clauses 1-2: post from harbor_master to a name no shim answers,
    then leave the block and sweep its scratch HOME by hand (the sweep that lost both reds)."""
    if _LAUNCHED:
        return _LAUNCHED
    from cairn.devices.cairn.tools.scratch_bus.scratch_bus import launch
    with launch("harbor_master", {"CAIRN_TESTER_TEST_ID": RUN_ID}, prefix="testing-2a6a") as bus:
        home = Path(bus._env["HOME"]) if getattr(bus, "_env", None) else None
        env = bus.post(sender="harbor_master", to="testing-2a6a-nobody", channel="personal",
                       why="testing-2a6a a letter no shim answers")
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline and not _lines(RUN_LOG, env["id"]):
            time.sleep(0.1)
        _LAUNCHED["during"] = _lines(RUN_LOG, env["id"])
    _LAUNCHED.update(envelope=env["id"], home=home)
    if home is not None and home.exists():
        shutil.rmtree(home, ignore_errors=True)
    _LAUNCHED["home_gone"] = home is not None and not home.exists()
    return _LAUNCHED


def test_a_bounce_in_a_scratch_home_bus_writes_one_line_at_the_account_run_dir():
    w = _launched()
    got = w["during"]
    assert len(got) == 1, f"{len(got)} lines for the letter at {RUN_LOG}"
    lacks = [f for f in FIELDS if f not in got[0]]
    assert not lacks, f"the line lacks {lacks}: {got[0]}"
    rec = got[0]
    assert rec["hook_before"] is False and rec["shim_class"] is None, rec
    assert "no shim answers" in rec["reason"], rec["reason"]
    assert isinstance(rec["bus_pid"], int) and rec["bus_pid"] != os.getpid(), rec["bus_pid"]
    assert rec["bus_started"], rec
    assert w["home"] is None or not str(RUN_LOG).startswith(str(w["home"])), (
        f"the line was written under the scratch HOME {w['home']}")


def test_the_line_still_reads_after_the_scratch_home_is_swept():
    w = _launched()
    assert w["home_gone"], f"the scratch HOME {w['home']} was not swept"
    after = _lines(RUN_LOG, w["envelope"])
    assert len(after) == 1, f"{len(after)} lines read after the sweep at {RUN_LOG}"


class _Inbox:
    def __init__(self) -> None:
        self.records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self.records.append(record)


def _rig():
    from cairn.devices.cairn.machines.bus.bus import BusDevice
    from cairn.devices.cairn.machines.bus.server import BusProcess
    bus = _SCRATCH.enter_context(BusDevice.scratch("bus_2a6a"))
    inbox = _Inbox()
    bus.set_diagnostic_receiver(inbox)
    return bus, BusProcess(bus), inbox


@contextlib.contextmanager
def _no_test_id():
    saved = os.environ.pop("CAIRN_TESTER_TEST_ID", None)
    try:
        yield
    finally:
        if saved is not None:
            os.environ["CAIRN_TESTER_TEST_ID"] = saved


def test_outside_a_run_the_line_lands_in_the_bus_log_and_a_delivery_writes_none():
    bus, proc, _inbox = _rig()
    taken = []
    bus.wire_delivery("testing-2a6a-taker", lambda e: taken.append(e["id"]) or {"took": e["id"]})
    with _no_test_id():
        bounced = bus.post(sender="testing-2a6a-writer", to="testing-2a6a-nobody",
                           channel="personal", why="testing-2a6a outside a run")
        delivered = bus.post(sender="testing-2a6a-writer", to="testing-2a6a-taker",
                             channel="personal", why="testing-2a6a a delivered letter")
    got = _lines(BUS_LOG, bounced["id"])
    assert len(got) == 1, f"{len(got)} lines for the bounce at {BUS_LOG}"
    assert delivered["id"] in taken, "the wired addressee did not take its letter"
    assert not _lines(BUS_LOG, delivered["id"]), "a delivered letter wrote a bounce line"


def test_an_unwritable_destination_still_bounces_and_is_loud():
    from cairn.devices.cairn.machines.bus import server
    bus, proc, inbox = _rig()
    blocker = _SCRATCH.enter_context(_tmpfile())
    real = server._bounce_record_path
    server._bounce_record_path = lambda: blocker / "under-a-file" / "bounces.jsonl"
    try:
        env = bus.post(sender="testing-2a6a-writer", to="testing-2a6a-nobody",
                       channel="personal", why="testing-2a6a an unwritable record")
    finally:
        server._bounce_record_path = real
    bounces = [e for e in bus.read(to="testing-2a6a-writer", channel="personal")
               if (e.get("body") or {}).get("is_bounce") and e.get("reply_to") == env["id"]]
    assert len(bounces) == 1, f"{len(bounces)} bounces when the record could not be written"
    # The returned letter cannot land either (the writer has no shim), so its own disposal
    # records too; the tooth reads the letter's line, by its id.
    loud = [r for r in inbox.records
            if r.get("gate") == "bounce_record_failed" and r.get("pointer") == env["id"]]
    assert len(loud) == 1, f"bounce_record_failed emitted {len(loud)} times: {inbox.records[-3:]}"


@contextlib.contextmanager
def _tmpfile():
    import tempfile
    fd, name = tempfile.mkstemp(prefix="testing-2a6a-")
    os.close(fd)
    try:
        yield Path(name)
    finally:
        Path(name).unlink(missing_ok=True)


def _trash_fixture_run_dir() -> None:
    run_dir = RUN_LOG.parent
    if run_dir.exists():
        subprocess.run([sys.executable, str(_REPO_ROOT / "bin" / "cmd" / "trash"), str(run_dir)],
                       capture_output=True, text=True, timeout=60)


def main() -> int:
    fails = 0
    try:
        for name in PROVES["2a6adebdd79b"].values():
            try:
                globals()[name]()
                print(f"  ok   {name}")
            except Exception as exc:  # a crash in a tooth is a red for that tooth
                fails += 1
                print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    finally:
        _SCRATCH.close()
        _trash_fixture_run_dir()
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
