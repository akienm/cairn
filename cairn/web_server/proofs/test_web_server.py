"""Proof for web_server (web-server ticket, child b) — the routing + render core, no socket.

The web server is a thin PRESENTATION surface (Law 7): the devices on the heartbeat across the
top (the roster, child c), the selected device's ACTIVE page below (its panes, child a). It owns
NO device state — everything is pulled live from the heartbeat and the target device's shim. This
proof composes a REAL ground_loop + REAL BaseShims + a REAL device, so it shows the whole
route → fetch-through-the-heartbeat → render chain WITHOUT binding a socket (the socket lives in
daemon.py, the thin OS wrapper this stays provable without).

Teeth a hollow surface could not pass:
  - THE NAV IS THE ROSTER: '/' renders every device on the heartbeat, in order, and invites a pick.
  - A DEVICE PAGE RENDERS ITS PANES: '/device/<id>' shows that device's STATUS+SETTINGS floor and
    its declared panes — pulled live through the heartbeat, not stored on the web server.
  - AN UNKNOWN DEVICE IS A LOUD, COHERENT 404 that STILL renders the nav (Law 7 — the surface
    collapses the error into a legible shape you can navigate away from, never a raw crash).
  - EVERYTHING A DEVICE SAYS IS ESCAPED: a device whose state contains '<script>' is rendered as
    TEXT, never live markup — the surface never lets a device's data become the page's markup.
  - AN ABSENT PANE RENDERS ITS REASON (loud, not silent): child a's absent-with-reason survives to
    the surface.
  - THE WEB SERVER OWNS NO STATE: it is a device (Form v0 #2) and holds nothing — its state() is
    pulled live (served count + the current roster), never a cached copy of device internals.

Runnable bare (NO socket, NO DB, NO framework):
    python3 cairn/web_server/proofs/test_web_server.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# The trace wire fires on every serve(); a proof run is not a real firing, so its
# records go to a scratch berth — the live denominator stays honest.
import os, tempfile  # noqa: E401
os.environ["CAIRN_LB_TRACE_ROOT"] = tempfile.mkdtemp(prefix="ws-proof-traces-")

from cairn.base.core_values import CoreValuesMixin
from cairn.base.device import BaseDevice
from cairn.base.shim import BaseShim
from cairn.ground_loop.loop import GroundLoopDevice
from cairn.web_server.server import WebServerDevice


class _Device(BaseDevice):
    """A minimal device with a Form v0 #2 surface and optional declared panes. Its state can
    carry a hostile string, to prove escaping."""

    def __init__(self, name, *, hostile=False, extra_panes=None) -> None:
        super().__init__()
        self._name = name
        self._hostile = hostile
        self._extra = extra_panes or []

    def intention(self) -> dict:
        return {"what": f"device {self._name}", "why": "a spec device for the surface proof"}

    def state(self) -> dict:
        return {"note": "<script>alert(1)</script>" if self._hostile else "resting"}

    def settings(self) -> dict:
        return {"verbosity": "loud"}

    def declared_panes(self) -> list[dict]:
        return self._extra


class _Shim(BaseShim):
    def __init__(self, device: _Device) -> None:
        super().__init__(bus=None)
        self._dev = device

    @property
    def device_id(self) -> str:
        return self._dev.intention()["what"].split()[-1]  # the name

    def device(self):
        return self._dev


def _wired():
    """A real heartbeat with two real device-shims subscribed, and a web server over it."""
    gl = GroundLoopDevice()
    alpha = _Shim(_Device("alpha"))
    beta = _Shim(_Device("beta", hostile=True, extra_panes=[
        {"kind": "logging", "label": "Log", "handler": None},                     # absent
        {"kind": "interaction", "label": "Chat", "handler": lambda: {"turns": 0}},  # data
    ]))
    gl.subscribe(alpha)
    gl.subscribe(beta)
    return WebServerDevice(gl, port=8799), gl


def test_the_nav_is_the_roster():
    web, _ = _wired()
    status, ctype, body = web.serve("/")
    assert status == 200 and "text/html" in ctype
    assert '/device/alpha' in body and '/device/beta' in body, "the nav links every device on the heartbeat"
    assert body.index("alpha") < body.index("beta"), "the nav keeps roster (subscription) order"
    assert "Pick a device" in body, "the landing invites a pick"


def test_a_device_page_renders_its_panes():
    web, _ = _wired()
    status, _c, body = web.serve("/device/alpha")
    assert status == 200
    # The STATUS + SETTINGS floor both render for a device with no declared panes.
    assert ">Status<" in body and ">Settings<" in body, "the floor panes render"
    assert "a spec device for the surface proof" in body, "the device's own reported DATA is shown"


def test_an_unknown_device_is_a_coherent_404_that_still_shows_the_nav():
    web, _ = _wired()
    status, _c, body = web.serve("/device/ghost")
    assert status == 404, "an unknown device is a loud 404, not a pretend page"
    assert "not on the heartbeat" in body, "the 404 says why, in a coherent shape (Law 7)"
    assert '/device/alpha' in body, "the nav still renders so you can navigate away"


def test_everything_a_device_says_is_escaped():
    web, _ = _wired()
    _s, _c, body = web.serve("/device/beta")  # beta's state carries <script>
    assert "<script>alert(1)</script>" not in body, "a device's data must never become live markup"
    assert "&lt;script&gt;" in body, "the hostile string is rendered as escaped TEXT (Law 7)"


def test_an_absent_pane_renders_its_reason():
    web, _ = _wired()
    _s, _c, body = web.serve("/device/beta")  # beta's Log pane has no handler
    assert "absent" in body and "unwired" in body, "an absent pane says why, loudly (not silent)"
    assert "Chat" in body, "the panes after the absent one still render"


def test_the_web_server_owns_no_state_and_is_a_device():
    web, gl = _wired()
    assert isinstance(web, CoreValuesMixin), "the web server is a device (Law 2)"
    assert list(web.introspect()) == ["intention", "state", "settings", "other"], "Form v0 #2 order"
    # Its state is pulled live: the roster it reports IS the heartbeat's, not a stored copy.
    assert web.state()["roster"] == gl.roster(), "the web server holds no cached copy — it reads live"
    before = web.state()["served"]
    web.serve("/")
    assert web.state()["served"] == before + 1, "the only thing it counts is its own serving"


def test_the_crossings_are_no_longer_silent():
    """The silent_device disposition (troubles/silent-devices-2026-07-27.json): a request
    crossing the surface leaves ONE breadcrumb — per crossing (a request is an event, not
    a pulse) — and a 404 breadcrumbs the same as a 200: the surface may collapse an error
    into a coherent page (Law 7), never the record that it happened. HELD when no receiver
    is wired, never dropped."""
    web, _ = _wired()
    assert web.held_diagnostics() == [], "construction is not a crossing"
    web.serve("/")
    web.serve("/device/ghost")
    held = web.held_diagnostics()
    assert [h["gate"] for h in held] == ["serve", "serve"], (
        f"one breadcrumb per request, got {[h['gate'] for h in held]}"
    )
    assert held[0]["pointer"] == "/" and held[0]["values"] == {"status": 200}
    assert held[1]["pointer"] == "/device/ghost" and held[1]["values"] == {"status": 404}, \
        "the coherent 404 page does not collapse the RECORD of the 404 — the breadcrumb says it"
    assert all(h["home"] == "held" for h in held), \
        "with no receiver wired the records HOLD (Law 7) — never silently dropped"


def test_the_trace_wire_counts_a_pass_and_a_refusal():
    """Deploy pass 2026-08-01: a 200 traces door_pass, a 404 traces send_back with the
    lack named — the denominator exists, greens included (the Leah rule)."""
    from cairn.learning_block import learning_block as lb
    web, _ = _wired()
    seen_before = len(lb.read_trace("web_server"))
    web.serve("/device/alpha")
    web.serve("/device/ghost")
    recs = lb.read_trace("web_server")[seen_before:]
    events = [r["event"] for r in recs]
    assert events == ["door_pass", "send_back"], f"both firings counted: {events}"
    assert "404" in recs[1]["data"]["lacks"][0], "the refusal names its lack"
    assert all(r["consumer"] == "training" for r in recs), "the denominator must not expire"


def _main() -> int:
    for check in (test_the_nav_is_the_roster,
                  test_a_device_page_renders_its_panes,
                  test_an_unknown_device_is_a_coherent_404_that_still_shows_the_nav,
                  test_everything_a_device_says_is_escaped,
                  test_an_absent_pane_renders_its_reason,
                  test_the_web_server_owns_no_state_and_is_a_device,
                  test_the_crossings_are_no_longer_silent,
                  test_the_trace_wire_counts_a_pass_and_a_refusal):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — web_server: the nav IS the roster, a device page renders its panes pulled live "
          "through the heartbeat, an unknown device is a coherent 404, every device string is "
          "escaped, absent panes say why, and the surface owns no state")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
