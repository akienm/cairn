"""Proof for ticket 99258e9bbdb1: a client that finds its stale bus draining uses it instead of spawning a loser.

From remote.py source (2026-11-12): ensure_bus spawns after every _replace. While the old bus
still holds bus.lock, the spawn exits EXIT_HELD, and ensure_bus raises "no bus process
answered" after _START_WAIT_S. Once a bus drains what it holds (sibling ticket 1029d5146152:
it replies {ok, draining, drain_s} and keeps serving), a client arriving mid-drain must be
served by that bus, not race it.

  1. test_a_draining_bus_is_used: a stale bus answers shutdown with draining; ensure_bus
     returns that bus's stats and spawns nothing;
  2. test_an_idle_replace_still_spawns: a shutdown reply without draining keeps today's path.
     ensure_bus waits for the old bus to stop answering, then spawns once;
  3. test_a_drained_use_is_noted: the drained use writes one line to the client log naming
     the draining count.

The bus here is the proof's own fixture: an AF_UNIX server on a thread at a scratch home's
bus.sock, speaking the wire's one-JSON-line shape. It imports nothing of the bus machine
(RULE 1). ``_spawn`` and ``_beside_the_manager`` are replaced for the call, so no process
or unit is started.

    bin/cairn test cairn/tools/bus_client/proofs/test_a_draining_bus_is_used_not_raced.py
"""
from __future__ import annotations

import json
import socketserver
import sys
import threading
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"99258e9bbdb1": {
    "1": "test_a_draining_bus_is_used",
    "2": "test_an_idle_replace_still_spawns",
    "3": "test_a_drained_use_is_noted",
}}


class _FakeBus:
    """A bus at ``home/bus.sock``. mode 'draining': stale until shutdown, then answers
    {draining: 1} and serves on. mode 'idle': stale until shutdown, then replies the flush
    shape and stops listening. mode 'fresh': answers stats ok."""

    def __init__(self, home: Path, mode: str) -> None:
        self.home, self.mode, self.shut = home, mode, False
        fake = self

        class _H(socketserver.StreamRequestHandler):
            def handle(self) -> None:
                line = self.rfile.readline()
                if not line:
                    return
                reply = fake.answer(json.loads(line))
                self.wfile.write((json.dumps(reply) + "\n").encode())
                self.wfile.flush()
                if fake.mode == "idle" and fake.shut:
                    threading.Thread(target=fake.close, daemon=True).start()

        self.sock = home / "bus.sock"
        self.sock.unlink(missing_ok=True)
        self.server = socketserver.ThreadingUnixStreamServer(str(self.sock), _H)
        self.server.daemon_threads = True
        threading.Thread(target=self.server.serve_forever, daemon=True).start()

    def answer(self, req: dict) -> dict:
        op = req.get("op")
        if self.mode == "fresh":
            return {"ok": True, "json": {"pid": 2, "who": "fresh"}}
        if op == "shutdown":
            self.shut = True
            if self.mode == "draining":
                return {"ok": True, "draining": 1, "drain_s": 600}
            return {"ok": True, "json": {"flushed": 0, "receipts": 0}}
        if self.mode == "draining" and self.shut:
            return {"ok": True, "json": {"pid": 1, "who": "draining"}}
        return {"ok": False, "stale": True, "root": "/elsewhere"}

    def close(self) -> None:
        self.server.shutdown()
        self.server.server_close()
        self.sock.unlink(missing_ok=True)


def _home() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("testing-99258e9bbdb1-drain-client-")


def _run(home: Path, mode: str) -> dict:
    """ensure_bus over a fake bus in ``mode``; what it returned, the spawns, the log."""
    from cairn.tools.bus_client import remote
    old = _FakeBus(home, mode)
    spawns: list[dict] = []
    log = home / "client.log"

    def spawn(h, scratch, *, via_unit=True):
        spawns.append({"old_answering": remote._answers(h) is not None})
        _FakeBus(Path(h), "fresh")
        return "unit"

    saved = (remote._spawn, remote._beside_the_manager, remote._LOG)
    remote._spawn, remote._beside_the_manager, remote._LOG = spawn, (lambda: True), log
    try:
        got = remote.ensure_bus(home)
    finally:
        remote._spawn, remote._beside_the_manager, remote._LOG = saved
        if mode == "draining":
            old.close()
    lines = log.read_text(encoding="utf-8").splitlines() if log.is_file() else []
    return {"got": got, "spawns": spawns, "log": lines}


def test_a_draining_bus_is_used():
    r = _run(_home(), "draining")
    assert r["spawns"] == [], f"a draining bus was raced by a spawn: {r!r}"
    assert r["got"] == {"pid": 1, "who": "draining"}, f"ensure_bus returned {r['got']!r}"


def test_an_idle_replace_still_spawns():
    r = _run(_home(), "idle")
    assert len(r["spawns"]) == 1, f"an idle replace must spawn once: {r!r}"
    assert r["spawns"][0]["old_answering"] is False, f"spawned while the old bus answered: {r!r}"
    assert r["got"] == {"pid": 2, "who": "fresh"}, f"ensure_bus returned {r['got']!r}"


def test_a_drained_use_is_noted():
    r = _run(_home(), "draining")
    noted = [x for x in r["log"] if "draining 1" in x]
    assert len(noted) == 1, f"one note naming the drain, got {r['log']!r}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
