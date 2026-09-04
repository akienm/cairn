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


# ── pane declaration ────────────────────────────────────────────────────────────

def test_declared_panes_has_trouble():
    from cairn.devices.cairn.device import CairnDevice
    d = CairnDevice()
    panes = d.declared_panes()
    trouble = [p for p in panes if p.get("kind") == "trouble"]
    assert trouble, "CairnDevice.declared_panes() has no trouble pane"
    assert trouble[0]["label"] == "troubles"
    assert callable(trouble[0]["handler"])


def test_handler_returns_list_of_dicts():
    from cairn.devices.cairn.device import CairnDevice
    d = CairnDevice()
    panes = d.declared_panes()
    trouble = [p for p in panes if p.get("kind") == "trouble"][0]
    data = trouble["handler"]()
    assert isinstance(data, list)
    if data:
        row = data[0]
        assert isinstance(row, dict)
        for key in ("id", "standing", "why", "count"):
            assert key in row, f"trouble row missing key: {key}"


def test_handler_with_fixture_data():
    from cairn.devices.trouble.trouble import TroubleDevice
    from cairn.devices.cairn.device import CairnDevice
    with tempfile.TemporaryDirectory() as td:
        trouble_file = os.path.join(td, "test-trouble-1.json")
        with open(trouble_file, "w") as f:
            json.dump({
                "id": "test-trouble-1",
                "standing": "OPEN",
                "why": "a test trouble for the proof",
                "count": 3,
                "first_seen": "2026-09-01T00:00:00Z",
                "last_seen": "2026-09-01T12:00:00Z",
                "occurrences": [],
                "notified": [],
                "cleared_by": [],
            }, f)
        d = CairnDevice()
        d._trouble = TroubleDevice(root=td)
        panes = d.declared_panes()
        trouble = [p for p in panes if p.get("kind") == "trouble"][0]
        data = trouble["handler"]()
        assert len(data) == 1
        assert data[0]["id"] == "test-trouble-1"
        assert data[0]["standing"] == "OPEN"
        assert data[0]["count"] == 3


def test_handler_excludes_cleared():
    from cairn.devices.trouble.trouble import TroubleDevice
    from cairn.devices.cairn.device import CairnDevice
    with tempfile.TemporaryDirectory() as td:
        for i, standing in enumerate(["OPEN", "CLEARED", "OPEN"]):
            with open(os.path.join(td, f"t-{i}.json"), "w") as f:
                json.dump({"id": f"t-{i}", "standing": standing,
                           "why": "test", "count": 1,
                           "first_seen": "", "last_seen": "",
                           "occurrences": [], "notified": [], "cleared_by": []}, f)
        d = CairnDevice()
        d._trouble = TroubleDevice(root=td)
        data = d.declared_panes()[0]["handler"]()
        assert len(data) == 2, f"expected 2 live, got {len(data)}"


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
