"""Proof: the VOYAGE PANE (web-server child d) — the web surface renders harbor_master's
TRAFFIC IMAGE, and is honest when no harbor is wired.

The web server is a PRESENTATION surface (Law 7): it renders the DATA harbor_master.voyage
produces (the whole-fleet, state-right-now traffic image) and owns none of it. This proof wires
the REAL harbor source (the live fleet register → traffic image), so it shows the whole
route → fetch harbor DATA → render chain WITHOUT a socket, over the actual boats on disk.

Teeth a hollow pane could not pass:
  - THE ROUTE RENDERS THE EMERGENT GATES: '/harbor' shows the traffic image — the at-sea
    gates by transition-class, with each gate's underway COUNT (calm) and its flagged boats as
    readable lines (the silently-stuck mid-voyage boats — the boon of the broad view).
  - THE HARBOR IS REACHABLE FROM EVERY PAGE: the ⚓ Harbor link rides in the nav on the landing
    and on a device page, so the fleet view is one click from anywhere.
  - THE SURFACE OWNS NOTHING: what '/harbor' renders is byte-for-byte the harbor source's own
    image — the web server invents no boat, no count (Law 7). A hostile boat id would be escaped.
  - NOT WIRED IS SAID LOUDLY: a web server with NO harbor source answers '/harbor' with a
    coherent 404 that says why (never a crash, never a pretend-empty fleet) and drops the ⚓ link.

Composes a REAL ground_loop + REAL harbor_master.voyage over the live fleet. Runs bare.
    python3 cairn/web_server/proofs/test_voyage_pane.py     # exit 0 = green
"""

from __future__ import annotations

import html
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.device import BaseDevice
from cairn.base.shim import BaseShim
from cairn.ground_loop.loop import GroundLoopDevice
from cairn.harbor_master import voyage
from cairn.web_server import render
from cairn.web_server.server import WebServerDevice


class _Device(BaseDevice):
    def __init__(self, name) -> None:
        super().__init__()
        self._name = name

    def intention(self) -> dict:
        return {"what": f"device {self._name}", "why": "a spec device for the voyage-pane proof"}

    def state(self) -> dict:
        return {"note": "resting"}

    def settings(self) -> dict:
        return {"verbosity": "loud"}


class _Shim(BaseShim):
    def __init__(self, device: _Device) -> None:
        super().__init__(bus=None)
        self._dev = device

    @property
    def device_id(self) -> str:
        return self._dev.intention()["what"].split()[-1]

    def device(self):
        return self._dev


def _wired(*, with_harbor=True):
    """A real heartbeat with one device, and a web server whose harbor source is the REAL
    live traffic image (or none, to prove the not-wired path)."""
    gl = GroundLoopDevice()
    gl.subscribe(_Shim(_Device("alpha")))
    harbor = voyage.traffic_image if with_harbor else None
    return WebServerDevice(gl, harbor_source=harbor, port=8798), gl


def test_harbor_route_renders_the_emergent_gates():
    web, _ = _wired()
    status, ctype, body = web.serve("/harbor")
    assert status == 200 and "text/html" in ctype
    assert "Traffic Image" in body, "the harbor route renders the traffic image"
    img = voyage.traffic_image()
    # every emergent gate name reaches the page; the calm underway count is shown.
    for g in img["gates"]:
        assert html.escape(str(g["gate"])) in body, f"gate {g['gate']} missing from the rendered image"
    assert "underway" in body, "the calm underway count is rendered"
    # the flagged mid-voyage boats — the boon — reach the page as readable lines.
    flagged = [o for g in img["gates"] for o in g["flagged"]]
    assert flagged, "the live fleet has no flagged boat — this proof needs one to be meaningful"
    for o in flagged:
        assert html.escape(o["id"]) in body, f"flagged boat {o['id']} did not render"
    assert "mid-voyage" in body, "the flag condition is named on the page"


def test_the_harbor_link_is_on_every_page():
    web, _ = _wired()
    for path in ("/", "/device/alpha"):
        _s, _c, body = web.serve(path)
        assert 'href="/harbor"' in body, f"the ⚓ Harbor link is missing from {path} — the fleet view must be reachable"


def test_the_surface_owns_nothing_of_the_harbor():
    web, _ = _wired()
    _s, _c, body = web.serve("/harbor")
    # what renders IS the harbor source's own image — rendered by the SAME pure function, so the
    # surface added no boat and no count of its own (Law 7: a projection, not a rival record).
    expected = render.render_traffic_image(voyage.traffic_image())
    assert expected in body, "the page body is not the harbor's own image — the surface invented content"


def test_not_wired_is_said_loudly():
    web, _ = _wired(with_harbor=False)
    status, _c, body = web.serve("/harbor")
    assert status == 404, "no harbor source must be a loud 404, not a pretend-empty fleet"
    assert "not wired" in body, "the not-wired route says why (Law 7), coherently"
    # and with no harbor, the ⚓ link does not ride the nav (nothing to link to).
    _s2, _c2, landing = web.serve("/")
    assert 'href="/harbor"' not in landing, "the harbor link must not appear when no harbor is wired"


def _main() -> int:
    for check in (test_harbor_route_renders_the_emergent_gates,
                  test_the_harbor_link_is_on_every_page,
                  test_the_surface_owns_nothing_of_the_harbor,
                  test_not_wired_is_said_loudly):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — web_server child d: the /harbor route renders harbor_master's traffic image "
          "(emergent gates, the calm underway count, the flagged silently-stuck boats), the ⚓ link "
          "is reachable from every page, the surface owns nothing of the harbor (byte-equal to its "
          "own image), and a missing harbor source is a loud coherent 404")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
