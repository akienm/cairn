"""Proof for ticket 0482542c2b7c — the web server has a shim that receives the request and starts
the web server.

Teeth a hollow build could not pass:
  (1) with no device running, a GET for /device/librarian handed to WebServerShim starts the
      WebServerDevice and returns 200 with the librarian's page.
  (2) a second GET reuses the running device: WebServerDevice is built exactly once across both.
  (3) the shim holds the port the way open-68fe4af67c6d settled it, by the ground loop's pulse
      (groundloop/pulse.py). Over a scratch port, never 80: a silent port starts listener.py,
      which answers GET /device/librarian with 200; a second pulse spawns nothing; a box that
      attaches to another cairn home starts nothing (outline 15.3.5); instance 0 is declared.
  (4) the web server's standing transport teeth, which this build changed, stay green: the
      handlers route through the shim's serve(), and every pane URL renders identically
      through the ASGI app.

Every import of what the build added happens inside a tooth, so a hollow reading fails by
tooth rather than crashing at import.

Runnable bare:  python3 cairn/devices/web_server/proofs/test_web_server_shim.py   # exit 0 = green
"""

from __future__ import annotations

import importlib.util
import os
import signal
import socket
import sys
import time
import urllib.request
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
os.environ["CAIRN_LB_TRACE_ROOT"] = str(scratch_dir("ws-shim-proof-traces-"))

PROOF_TIMEOUT_S = 300  # tooth (3) starts a real listener in a child process; measured ~1 s up, 2026-11-12

PROVES = {
    "0482542c2b7c": {
        "1": "test_a_first_get_starts_the_device_and_serves_the_librarian",
        "2": "test_a_second_get_reuses_the_running_device",
        "3": "test_the_pulse_holds_the_port_on_the_home_only",
        "4": "test_the_standing_transport_teeth_stay_green",
    },
}


def _roster():
    """A real DeviceRoster over the live rack on disk, with no bus: the librarian's page
    renders from its shim's declared panes, the same way the live server builds it."""
    from cairn.tools.bus_client.roster import DeviceRoster
    return DeviceRoster(bus=None)


def _counted_shim():
    from cairn.devices.web_server.server import WebServerDevice
    from cairn.devices.web_server.shim import WebServerShim
    built: list = []
    roster = _roster()

    def factory():
        dev = WebServerDevice(roster)
        built.append(dev)
        return dev

    return WebServerShim(device_factory=factory), built


def test_a_first_get_starts_the_device_and_serves_the_librarian():
    shim, built = _counted_shim()
    assert built == [], "the device is not built before a request arrives"
    status, ctype, body = shim.serve("/device/librarian")
    assert len(built) == 1, f"the first GET starts the device once: built {len(built)}"
    assert status == 200, f"/device/librarian answered {status}"
    assert "text/html" in ctype, ctype
    assert "librarian" in body, "the page is the librarian's"


def test_a_second_get_reuses_the_running_device():
    shim, built = _counted_shim()
    first = shim.serve("/device/librarian")
    second = shim.serve("/device/librarian")
    assert len(built) == 1, f"two GETs, {len(built)} devices built: the second did not reuse"
    assert first[0] == second[0] == 200
    assert shim.device() is built[0], "the shim hands back the device it started"


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def test_the_pulse_holds_the_port_on_the_home_only():
    from cairn.devices.web_server.groundloop import pulse
    assert "0" in pulse.declared_instances(), "instance 0 is declared by its folder (5.7.3.4)"

    # an attaching box starts nothing, and never asks to
    asked: list = []
    out = pulse.pulse(env={"CAIRN_HOME_HOST": "some-other-box"}, me="this-box", addresses=set(),
                      ensure_fn=lambda port: asked.append(port) or {"spawned": "x"})
    assert asked == [], f"a box attaching to another home asked for a web server: {asked}"
    assert all(r["spawned"] == "none" for r in out), out
    # the home asks for instance 0's port
    out = pulse.pulse(env={"CAIRN_HOME_HOST": "this-box", "CAIRN_WEB_SERVER_PORT": "1234"},
                      me="this-box", addresses=set(),
                      ensure_fn=lambda port: asked.append(port) or {"spawned": "x"})
    assert asked == [1234], f"the home pulses instance 0 on its port: {asked}"

    port = _free_port()
    log = scratch_dir("ws-shim-pulse-") / "web_server.log"
    assert not pulse.listening(port, "127.0.0.1"), "the scratch port is silent before the pulse"
    first = pulse.ensure(port, "127.0.0.1", unit=None, log=log)
    pid = first.get("pid")
    try:
        assert first["spawned"] == "setsid" and pid, f"a silent port starts the shim: {first}"
        deadline = time.monotonic() + 90
        while not pulse.listening(port, "127.0.0.1") and time.monotonic() < deadline:
            time.sleep(0.25)
        assert pulse.listening(port, "127.0.0.1"), f"nothing answered on {port}: {log.read_text()}"
        with urllib.request.urlopen(f"http://127.0.0.1:{port}/device/librarian", timeout=60) as r:
            status, body = r.status, r.read().decode("utf-8", errors="replace")
        assert status == 200 and "librarian" in body, f"GET /device/librarian answered {status}"
        second = pulse.ensure(port, "127.0.0.1", unit=None, log=log)
        assert second["spawned"] == "none" and second["up"], f"a held port spawns nothing: {second}"
    finally:
        if pid:
            try:
                os.killpg(pid, signal.SIGTERM)
            except (ProcessLookupError, PermissionError, AttributeError):
                pass


def test_the_standing_transport_teeth_stay_green():
    path = _REPO_ROOT / "cairn/devices/web_server/proofs/test_web_server.py"
    spec = importlib.util.spec_from_file_location("_ws_standing", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.test_device_logic_stays_out_of_the_transport()
    mod.test_existing_pane_urls_render_identically_through_the_asgi_app()
    mod.test_there_is_one_web_server()


def main() -> int:
    teeth = [v for k, v in sorted(globals().items()) if k.startswith("test_") and callable(v)]
    failed = 0
    for t in teeth:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"{len(teeth) - failed}/{len(teeth)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
