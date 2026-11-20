"""Proof for ticket f62f6b50b047 — bus_client publishes a held connection to a home's bus.

MEASURED 2026-11-20 on akiendelllinux: c234aae2c0b9's PROVED was refused at clearance,
[sole_path_holds] bus/proofs/test_a_scratch_bus_with_no_caller_ends_itself.py imports
['socket']: its _open_connection_guard dialled a raw AF_UNIX socket to hold a connection open,
because bus_client had no door to hold one through. ``remote.held_connection(home)`` is that
door: one connection, dialled at ``socket_path(home)``, held until the with block ends.

Each tooth starts its own scratch bus (``ensure_bus(home, scratch=True)``) at its own scratch
home with CAIRN_BUS_IDLE_S=3, reads ``<home>/stops.jsonl`` (the home is the tooth's own), and
stops the unit it started by name in a finally. This file imports no socket.

  1. while held, a short-idle scratch bus stays up past N + slack, with no stop record;
  2. after the with block, the same bus exits by idle within N + slack, cause 'idle';
  3. an exception raised inside the with block reaches the caller unchanged, and the bus still
     idles out after it;
  4. with no bus at home, entering held_connection(home) raises naming str(socket_path(home)),
     and nothing is created at that path.

    bin/cairn test cairn/tools/bus_client/proofs/test_a_held_connection_holds_the_bus_open.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"f62f6b50b047": {
    "1": "test_while_held_the_bus_stays_up",
    "2": "test_released_the_bus_idles_out",
    "3": "test_an_exception_inside_still_releases",
    "4": "test_the_holder_dials_socket_path",
}}

_N = 3.0
_SLACK = 3.0
_EXIT_S = 30.0


class _World:
    """A scratch home, its bus started with a short N, stopped by unit name on exit. The
    caller's CAIRN_BUS_UNIT is out of the environment while it stands, so the unit (and the
    stop by name) is the home's own."""

    def __init__(self, tag: str, *, start: bool = True):
        from cairn.tools.scratch.scratch import scratch_dir
        self.home = scratch_dir(f"testing-f62f6b50b047-{tag}-")
        self.start = start

    def __enter__(self):
        from cairn.tools.bus_client import remote
        self.saved = os.environ.pop("CAIRN_BUS_UNIT", None)
        if self.start:
            env = dict(os.environ, CAIRN_BUS_HOME=str(self.home), CAIRN_BUS_IDLE_S=str(_N),
                       PYTHONDONTWRITEBYTECODE="1")
            remote.ensure_bus(self.home, scratch=True, env=env)
        return self

    def __exit__(self, *exc):
        from cairn.tools.bus_client import remote
        try:
            subprocess.run(["systemctl", "--user", "stop", f"{remote._unit(self.home)}.service"],
                           capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            pass   # no systemd here: the bus idles out on its own at N
        finally:
            if self.saved is not None:
                os.environ["CAIRN_BUS_UNIT"] = self.saved
        return False

    def stops(self) -> list[dict]:
        path = self.home / "stops.jsonl"
        if not path.is_file():
            return []
        return [json.loads(x) for x in path.read_text(encoding="utf-8").splitlines() if x.strip()]

    def idled(self, within: float) -> list[dict]:
        deadline = time.monotonic() + within
        while time.monotonic() < deadline:
            lines = self.stops()
            if lines:
                return lines
            time.sleep(0.2)
        return self.stops()

    def answers(self) -> bool:
        from cairn.tools.bus_client.remote import exchange
        try:
            return bool(exchange({"op": "stats"}, self.home, timeout=10).get("ok"))
        except (OSError, ValueError):
            return False


def test_while_held_the_bus_stays_up():
    from cairn.tools.bus_client.remote import held_connection   # the build's addition: bound here
    with _World("held") as w:
        with held_connection(w.home):
            time.sleep(_N + _SLACK)
            assert w.stops() == [], f"a stop while the connection was held: {w.stops()!r}"
            assert w.answers(), f"the bus at {w.home} did not answer {_N + _SLACK:.0f}s into the hold"


def test_released_the_bus_idles_out():
    from cairn.tools.bus_client.remote import held_connection
    with _World("released") as w:
        with held_connection(w.home):
            time.sleep(_N + 1.0)
            assert w.stops() == [], f"a stop while held: {w.stops()!r}"
        released = time.monotonic()
        lines = w.idled(_N + _SLACK + _EXIT_S)
        took = time.monotonic() - released
        assert len(lines) == 1 and lines[0].get("cause") == "idle", (
            f"after the release the bus did not leave by idle: {lines!r}")
        assert took <= _N + _SLACK + 2.0, f"the bus idled out {took:.1f}s after the release, N={_N}"


def test_an_exception_inside_still_releases():
    from cairn.tools.bus_client.remote import held_connection

    class Planted(Exception):
        pass

    with _World("raised") as w:
        raised = None
        try:
            with held_connection(w.home):
                raise Planted("testing-f62f6b50b047: raised inside the hold")
        except Planted as exc:
            raised = exc
        assert raised is not None and str(raised) == "testing-f62f6b50b047: raised inside the hold", (
            f"the exception did not reach the caller unchanged: {raised!r}")
        lines = w.idled(_N + _SLACK + _EXIT_S)
        assert len(lines) == 1 and lines[0].get("cause") == "idle", (
            f"after an exception inside the hold the bus did not idle out: {lines!r}")


def test_the_holder_dials_socket_path():
    from cairn.tools.bus_client.remote import held_connection, socket_path
    with _World("nobus", start=False) as w:
        where = socket_path(w.home)
        assert not where.exists(), f"a socket stands at {where} before any bus"
        err = None
        try:
            with held_connection(w.home):
                pass
        except Exception as exc:   # noqa: BLE001 — the tooth reads what was raised
            err = exc
        assert err is not None, "held_connection entered with no bus at the home"
        assert str(where) in str(err), f"the error does not name {where}: {type(err).__name__}: {err}"
        assert not where.exists(), f"entering held_connection created {where}"
        assert not (w.home / "bus.sock").exists(), "entering held_connection created <home>/bus.sock"
        assert w.stops() == [], "a bus was started by held_connection"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
