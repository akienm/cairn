"""Proof: the cairn device's trouble panel — pane declaration, handler data shape,
render kind output, and WATCHME probe.

Teeth a hollow build could not pass: an unoverridden declared_panes returns [],
an unregistered render kind falls to <pre>, and an absent probe module raises ImportError.
"""
from __future__ import annotations

import json
import os
import tempfile

import pytest


class _FakeBus:
    """The trouble lane as cairn now meets it — a bus, not a device it holds.

    THE POINT OF THE FAKE IS THAT IT IS POSSIBLE (ticket 9579a6f9cec6). Until 2026-09-07
    these teeth reached in and set ``d._trouble = TroubleDevice(root=td)``, which is the
    isolation defect stated as a test fixture: the proof could only be written that way
    because the device really did hold another device. Now the pane asks a verb, so the
    stand-in is an answer to a verb, and the proof imports nothing from
    ``cairn.devices.trouble``."""

    def __init__(self, reply):
        self._reply = reply
        self.asked = []

    def request(self, **kw):
        self.asked.append(kw)
        if isinstance(self._reply, Exception):
            raise self._reply
        return {"body": self._reply}


def _pane(device):
    return [p for p in device.declared_panes() if p.get("kind") == "trouble"][0]


def _row(tid, standing="OPEN", count=1):
    return {"id": tid, "standing": standing, "why": "a test trouble for the proof",
            "count": count, "first_seen": "2026-09-01T00:00:00Z",
            "last_seen": "2026-09-01T12:00:00Z"}


# ── pane declaration ────────────────────────────────────────────────────────────

def test_declared_panes_has_trouble():
    from cairn.devices.cairn.device import CairnDevice
    d = CairnDevice()
    panes = d.declared_panes()
    trouble = [p for p in panes if p.get("kind") == "trouble"]
    assert trouble, "CairnDevice.declared_panes() has no trouble pane"
    assert trouble[0]["label"] == "troubles"
    assert callable(trouble[0]["handler"])


def test_handler_asks_the_lane_over_the_bus():
    """The pane is a QUESTION now, and the question's addressing is part of the contract:
    the panel that renders on the cairn device's page must be the trouble device's own
    answer, obtained the way any device asks any other (memory
    inter-device-queries-via-bus-verbs)."""
    from cairn.devices.cairn.device import CairnDevice
    bus = _FakeBus({"troubles": [_row("test-trouble-1", count=3)]})
    d = CairnDevice(bus=bus)
    data = _pane(d)["handler"]()
    assert len(bus.asked) == 1, bus.asked
    assert bus.asked[0]["to"] == "trouble" and bus.asked[0]["verb"] == "live"
    assert bus.asked[0]["why"], "a bus request carries its why (CP3)"
    assert len(data) == 1
    row = data[0]
    for key in ("id", "standing", "why", "count", "first_seen", "last_seen"):
        assert key in row, f"trouble row missing key: {key}"
    assert row["id"] == "test-trouble-1"
    assert row["standing"] == "OPEN"
    assert row["count"] == 3


def test_an_UNREACHABLE_lane_never_renders_as_ZERO_TROUBLES():
    """THE TOOTH THIS WHOLE PANE TURNS ON, and the one a hollow build fails by being tidy.

    An empty trouble panel is the NORMAL OPERATING STATE — it is what a healthy system
    looks like. So a handler that swallowed a failure and returned ``[]`` would render the
    calmest possible page at the exact moment the lane was unreachable, and it would be
    indistinguishable from good news. Raising is what makes the difference visible:
    ``BaseShim.active_page`` renders a raising handler as an ABSENT pane carrying the
    reason (Law 7 — a presentation surface may collapse an error into a coherent shape,
    and 'no troubles' is not a shape this error has).

    Three ways to be unreachable, all of them asserted, because the first draft of this
    handler only guarded the first."""
    from cairn.devices.cairn.device import CairnDevice

    with pytest.raises(Exception):                       # no bus at all
        _pane(CairnDevice())["handler"]()

    with pytest.raises(Exception):                       # the ask itself fails
        _pane(CairnDevice(bus=_FakeBus(RuntimeError("no route to trouble"))))["handler"]()

    with pytest.raises(Exception):                       # answered, but not with a list
        _pane(CairnDevice(bus=_FakeBus({"outcome": "refused"})))["handler"]()

    # ...and the genuinely empty case is NOT an error — that is the distinction being drawn.
    assert _pane(CairnDevice(bus=_FakeBus({"troubles": []})))["handler"]() == []


def test_the_pane_projects_and_does_not_filter():
    """Which rows are LIVE is trouble's property, decided behind trouble's own gate, and
    the pane's job stops at projection. Asserted as a negative: whatever the lane answers
    with is what appears, one row for one row. The old shape had this device holding the
    store and re-deriving liveness for itself — two hands on one question, and the pane's
    hand had no owner (Law 6)."""
    from cairn.devices.cairn.device import CairnDevice
    rows = [_row("t-0"), _row("t-1", standing="CLEARED"), _row("t-2")]
    data = _pane(CairnDevice(bus=_FakeBus({"troubles": rows})))["handler"]()
    assert [r["id"] for r in data] == ["t-0", "t-1", "t-2"]
    assert [r["standing"] for r in data] == ["OPEN", "CLEARED", "OPEN"]


# ── render kind ─────────────────────────────────────────────────────────────────

def test_render_trouble_two_sided_layout():
    from cairn.devices.web_server.render import render_pane
    html = render_pane({
        "kind": "trouble",
        "label": "troubles",
        "data": [{"id": "t1", "standing": "OPEN", "why": "test", "count": 1,
                  "first_seen": "2026-09-01", "last_seen": "2026-09-01"}],
    })
    assert "trouble-list" in html, "no trouble-list class in output"
    assert "trouble-detail" in html, "no trouble-detail class in output"
    assert "red-light" in html, "no red-light indicator in output"


def test_render_trouble_red_light_live():
    from cairn.devices.web_server.render import render_pane
    html = render_pane({
        "kind": "trouble",
        "label": "troubles",
        "data": [{"id": "t1", "standing": "OPEN", "why": "test", "count": 1}],
    })
    assert "#d33" in html, "red light should be bright (#d33) when live troubles exist"


def test_render_trouble_red_light_none():
    from cairn.devices.web_server.render import render_pane
    html = render_pane({
        "kind": "trouble",
        "label": "troubles",
        "data": [],
    })
    assert "#998" in html, "red light should be dull (#998) when no live troubles"


def test_render_trouble_escapes_values():
    from cairn.devices.web_server.render import render_pane
    html = render_pane({
        "kind": "trouble",
        "label": "troubles",
        "data": [{"id": "<script>", "standing": "OPEN",
                  "why": "a&b", "count": 1}],
    })
    assert "<script>" not in html
    assert "&lt;script&gt;" in html
    assert "&amp;" in html


# ── WebSocket route ─────────────────────────────────────────────────────────────

def test_websocket_route_exists():
    from starlette.routing import WebSocketRoute
    from cairn.devices.web_server.listener import _make_app
    app = _make_app()
    ws_routes = [r for r in app.routes if isinstance(r, WebSocketRoute)]
    assert ws_routes, "no WebSocket routes in _make_app"
    paths = [r.path for r in ws_routes]
    assert "/ws/troubles" in paths, f"no /ws/troubles route, got {paths}"


# ── WATCHME probe ───────────────────────────────────────────────────────────────

def test_probe_importable():
    from cairn.devices.cairn.probes.trouble_panel_surfaces_live_troubles import PROBE
    from cairn.tools.base.probe import Probe
    assert isinstance(PROBE, Probe)


def test_probe_carry_returns_data():
    from cairn.devices.cairn.probes.trouble_panel_surfaces_live_troubles import PROBE
    ctx = {}
    result = PROBE.carry(ctx)
    assert result is not None
    assert isinstance(result, dict)
    assert "pane_declared" in result


def test_probe_enough_returns_bool():
    from cairn.devices.cairn.probes.trouble_panel_surfaces_live_troubles import PROBE
    ctx = {}
    e = PROBE.enough(ctx)
    assert isinstance(e, bool)
