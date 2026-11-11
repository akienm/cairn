"""PROOF for ticket 054a03f974f6: a reply to a request a bus stop cut short is receipted.

An asker waits for its reply inside the bus process: ``request()`` runs there (op_call). A stop
ends that wait. The bus after it held no record of the ask, so when the answer came there was
no hook, no ``_abandoned`` entry and nobody to take it. It stood until report_stood raised
mail-<asker>-stood-600s, once per bus life. Measured 2026-11-11 by CC: tester->constrain
'run reply' c363a743 answered request 947d23ec, posted at 16:40:44Z, the same second a stale
client shut bus pid 427135 down. The reply came 127 s later and stood, and the trouble reached
10x. A repro, a request to the tester on a 20 s proof with the bus shut down 5 s in, left its
reply 05be8bdd standing the same way.

Each stop now writes the unanswered asks to ``<home>/asks_in_flight.json``. The next bus holds
them as given up, so a late reply takes the ``bus-asker-gave-up`` receipt (ticket cd2d27fe3261).

One tooth per numbered falsifier clause. Teeth 1 and 2 run ``serve`` over a scratch table at a
scratch home through a driver that replaces ``serve_forever`` (the stop proof's method). The
driver's body is the bus's life between start and stop:

  1. test_a_stop_hands_over_the_asks_still_in_flight: life A posts an ask (``_asked``, the
     state ``request()`` holds while it waits) and stops. The home then names that ask and
     its asker.
  2. test_the_next_bus_receipts_their_late_reply_as_given_up: life B starts at that home, the
     answer to the ask lands and is receipted ``bus-asker-gave-up``, and the file is retired.
  3. test_a_reply_to_an_ask_never_handed_over_still_stands: in the same life B, a reply to an
     id no stop handed over stays undelivered, as cd2d27fe3261 tooth 3 requires.
  4. test_an_ask_past_the_horizon_is_not_taken_over: a handed-over ask older than
     ASK_HORIZON_S is not held, and its reply stands.

Requires Postgres.

    python3 cairn/devices/cairn/machines/bus/proofs/test_a_reply_across_a_bus_stop_is_receipted.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"054a03f974f6": {
    "1": "test_a_stop_hands_over_the_asks_still_in_flight",
    "2": "test_the_next_bus_receipts_their_late_reply_as_given_up",
    "3": "test_a_reply_to_an_ask_never_handed_over_still_stands",
    "4": "test_an_ask_past_the_horizon_is_not_taken_over",
}}

_ASKER = "testing-054a03f974f6-asker"
_SILENT = "testing-054a03f974f6-silent"
_RUN_S = 60.0

# serve() with serve_forever replaced by one life of the bus: 'ask' posts an ask as request()
# does and stops with it unanswered; 'answer' posts the late reply and a stray one, flushes,
# and writes what it measured to <home>/measured.json.
_DRIVER = r"""
import json, sys, threading, uuid
from pathlib import Path
sys.path.insert(0, sys.argv[1])
home, mode = Path(sys.argv[2]), sys.argv[3]
from cairn.devices.cairn.machines.bus import server
from cairn.devices.cairn.machines.bus.bus import BusDevice
from cairn.devices.db_domain.tools.client import store
from cairn.tools.base import testing_mark
ASKER, SILENT = sys.argv[4], sys.argv[5]
with BusDevice.scratch("bus_ask_stop") as bus:
    def _forever(self, poll_interval=0.5):
        # The start's backlog pass creates the tables too; let it finish before this life does.
        for t in threading.enumerate():
            if t.name == "bus-backlog":
                t.join(timeout=30)
        if mode == "ask":
            # Marked: SILENT has no receiver, and an unmarked bounce raises in the live lane.
            ask = bus.post(sender=ASKER, to=SILENT, channel="personal", verb="run", why="testing-054a03f974f6 the ask",
                           body={testing_mark.FIELD: testing_mark.mark("054a03f974f6")}, _asked=True)
            (home / "ask.json").write_text(json.dumps({"id": ask["id"]}))
            return None
        ask_id = json.loads((home / "ask.json").read_text())["id"]
        held_file = (home / server.ASKS_FILE).exists()
        late = bus.post(sender=SILENT, to=ASKER, channel="personal", reply_to=ask_id,
                        why="testing-054a03f974f6 run reply", body={"verdict": "green"})
        stray = bus.post(sender=SILENT, to=ASKER, channel="personal", reply_to=uuid.uuid4().hex,
                         why="testing-054a03f974f6 a reply to nothing handed over", body={})
        bus.flush()
        waiting = {e["id"] for e in bus.undelivered(to=ASKER, limit=1000)}
        rows = store.read(bus.delivery_table, where="envelope = %s", params=(late["id"],))
        (home / "measured.json").write_text(json.dumps({
            "file_at_serve": held_file, "late_waiting": late["id"] in waiting,
            "late_by": [r["by"] for r in rows], "stray_waiting": stray["id"] in waiting}))
        return None
    server._Server.serve_forever = _forever
    sys.exit(server.serve(home, bus, lan=0, scratch=True))
"""


def _home() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("testing-054a03f974f6-asks-")


def _env(home: Path) -> dict:
    env = dict(os.environ)
    env["CAIRN_BUS_HOME"] = str(home)
    env["PYTHONPATH"] = str(_REPO) + os.pathsep + env.get("PYTHONPATH", "")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def _life(home: Path, mode: str) -> None:
    r = subprocess.run([sys.executable, "-c", _DRIVER, str(_REPO), str(home), mode, _ASKER, _SILENT],
                       cwd=str(_REPO), env=_env(home), capture_output=True, text=True,
                       timeout=_RUN_S)
    assert r.returncode == 0, f"bus life {mode!r} exited {r.returncode}: {(r.stdout + r.stderr)[-1200:]}"


_STOPPED: dict = {}


def _stopped_home() -> Path:
    """One home where life A asked and stopped; teeth 1-3 read it, built once."""
    if "home" not in _STOPPED:
        home = _home()
        _life(home, "ask")
        _STOPPED["home"] = home
    return _STOPPED["home"]


def _answered() -> dict:
    if "measured" not in _STOPPED:
        home = _stopped_home()
        _life(home, "answer")
        _STOPPED["measured"] = json.loads((home / "measured.json").read_text())
    return _STOPPED["measured"]


def test_a_stop_hands_over_the_asks_still_in_flight():
    home = _stopped_home()
    ask_id = json.loads((home / "ask.json").read_text())["id"]
    path = home / "asks_in_flight.json"
    assert path.is_file(), f"the stop left no {path.name} at {home}: the ask died with the bus"
    rows = json.loads(path.read_text())
    assert rows.get(ask_id, {}).get("asker") == _ASKER, (
        f"the handed-over asks do not name {ask_id[:8]} -> {_ASKER}: {rows!r}")


def test_the_next_bus_receipts_their_late_reply_as_given_up():
    m = _answered()
    assert m["file_at_serve"] is False, "the next bus served with the hand-over file still present"
    assert m["late_waiting"] is False, "the late reply to a handed-over ask stands undelivered"
    assert m["late_by"] == ["bus-asker-gave-up"], f"the late reply's receipts: {m['late_by']!r}"


def test_a_reply_to_an_ask_never_handed_over_still_stands():
    m = _answered()
    assert m["stray_waiting"] is True, (
        "a reply to an id no stop handed over was receipted: the take-over swallowed it")


def test_an_ask_past_the_horizon_is_not_taken_over():
    from cairn.devices.cairn.machines.bus.bus import ASK_HORIZON_S, BusDevice
    home = _home()
    path = home / "asks_in_flight.json"
    old_id = "testing-054a03f974f6-old-ask"
    path.write_text(json.dumps({old_id: {"asker": _ASKER,
                                         "since": time.time() - ASK_HORIZON_S - 60}}))
    with BusDevice.scratch("bus_ask_horizon") as bus:
        taken = bus.take_over_asks(path)
        assert taken == {"taken_over": 0}, f"an ask past the horizon was taken over: {taken!r}"
        reply = bus.post(sender=_SILENT, to=_ASKER, channel="personal", reply_to=old_id,
                         why="testing-054a03f974f6 a reply past the horizon", body={})
        assert reply["id"] in {e["id"] for e in bus.undelivered(to=_ASKER, limit=1000)}, (
            "the reply to an ask past the horizon was receipted")
    assert not path.exists(), "take_over_asks left the hand-over file in place"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
