"""Proof: the cairn device's trouble panel — pane declaration, handler data shape,
render kind output, and WATCHME probe.

Teeth a hollow build could not pass: an unoverridden declared_panes returns [],
an unregistered render kind falls to <pre>, and an absent probe module raises ImportError.
"""
from __future__ import annotations

import json
import os
import tempfile
import time

import pytest

# WHICH TICKET CLAUSES THESE TEETH COVER (read by cairn/tools/proof_coverage, ticket
# feeb4c786b14). Clause (5) of 9579a6f9cec6 asks for a raised fixture trouble visible in
# the rendered pane within 1s of the raise, over the poke path. It asks it OF THE PROBE,
# and that is the one place it cannot be honoured: the probe deliberately stopped
# importing the renderer on 2026-09-07 (see the probe's own docstring — a cross-device
# import from a watch is the very defect this ticket closes, and re-asserting a pure
# function once per heartbeat is reciting, not measuring). So the clause is served HERE,
# where a raise, a real drain, a real ``live`` verb and a real render can be run end to
# end in one process and TIMED — which is what the clause was actually after. What a
# proof cannot put in the loop is the socket itself; the budget measured is the poke
# path the socket pushes, and the tooth says so at its assertion.
PROVES = {
    "9579a6f9cec6": {
        "5": "test_a_raised_trouble_reaches_the_RENDERED_PANE_over_the_poke_path",
    },
}


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


# ── end to end: raise → poke → drain → live → render ────────────────────────────

class _RoutingBus:
    """A bus that actually ROUTES, to the real trouble shim, instead of answering for it.

    Every other tooth in this file uses ``_FakeBus`` and is right to: they are measuring
    the pane, and a stand-in keeps the trouble device out of the measurement. This one is
    measuring the ROUTE, so the reply has to come from the lane that would really answer
    it — through ``deliver``, which is the same door the real bus knocks on, verb
    canonicalisation and all."""

    def __init__(self, shim):
        self._shim = shim
        self.asked = []

    def request(self, *, to, verb, why=None, body=None, **kw):
        self.asked.append({"to": to, "verb": verb, "why": why})
        assert to == "trouble", f"the pane asked {to!r}, not the trouble lane"
        return {"body": self._shim.deliver(
            {"id": "proof-envelope", "sender": "cairn", "addressee": to, "verb": verb,
             "body": body or {}})}


def test_a_raised_trouble_reaches_the_RENDERED_PANE_over_the_poke_path():
    """THE WHOLE LANE IN ONE PROCESS, and the only tooth here that runs it end to end.

    Ticket 9579a6f9cec6 clause (5). A component that holds nothing of ``cairn.devices``
    raises; the poke drains it into the held store; the cairn device's pane asks ``live``
    over the bus; the answer renders. Each half of that is already proved separately —
    the raise in ``cairn/tools/base/proofs/test_raise_trouble.py``, the fold in trouble's
    own proof, the projection and the render above — and a lane can be green in every
    half and dark end to end, because the seams are where the verb name, the reply shape
    and the drain's watermark all live. That is what this tooth is for.

    THE BUDGET, AND WHAT IT HONESTLY COVERS. The clause asks for the trouble VISIBLE
    within 1s of the raise. The socket is not in this loop — a proof cannot hold a
    browser — so what is timed is the path the socket pushes: raise → poke → drain →
    ``live`` → HTML. If that path is inside the budget the push is a transport question;
    if it were not, no transport could rescue it. Asserted as an invariant (a bound), not
    a snapshot, because a recorded duration is a number that reds on a loaded laptop and
    teaches nobody."""
    from cairn.devices.cairn.device import CairnDevice
    from cairn.devices.trouble.shim import TroubleShim
    from cairn.devices.web_server.render import render_pane
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Raiser(DiagnosticBase):
        @property
        def diagnostic_device(self) -> str:
            return "a_fixture_component"

    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        roots = {k: Path(tmp) for k in ("repo", "commons", "instance")}
        shim = TroubleShim(roots=roots, root=Path(tmp) / "troubles")

        raiser = _Raiser()
        raiser.set_diagnostic_roots(roots)
        raiser.set_trouble_notifier(shim.receive_raise)

        started = time.monotonic()
        rec = raiser.raise_trouble(
            "a-fixture-trouble-for-the-pane",
            why="the pane must show a trouble nobody put in the store by hand")
        assert rec["poke"] == "sent", (
            f"the notifier was not reached: {rec['poke']} — without the poke this tooth "
            f"would be measuring the beat, which is a different budget")

        bus = _RoutingBus(shim)
        data = _pane(CairnDevice(bus=bus))["handler"]()
        html = render_pane({"kind": "trouble", "label": "troubles", "data": data})
        elapsed = time.monotonic() - started

        assert bus.asked and bus.asked[0]["verb"] == "live", bus.asked
        assert [r["id"] for r in data] == ["a-fixture-trouble-for-the-pane"], data
        assert data[0]["standing"] == "OPEN" and data[0]["count"] == 1, data[0]
        assert "a-fixture-trouble-for-the-pane" in html, (
            "the raised trouble reached the pane's DATA but not its HTML — the render "
            "dropped it, which is the panel dark while the page still loads")
        assert "#d33" in html, "live troubles held, and the red light rendered dull"
        assert elapsed < 1.0, (
            f"raise → rendered pane took {elapsed:.3f}s, over the 1s budget the clause "
            f"names; the socket is not in this loop, so no transport can recover it")

        # ...and the emission is the raiser's own breadcrumb, not something the pane
        # invented: the drain is a real read of a real file, so deleting the log home
        # would empty the panel.
        home = Path(tmp) / "logs" / "a_fixture_component" / "0"
        assert len(list(home.glob("*.raise_trouble.json"))) == 1, sorted(home.iterdir())


def test_a_SECOND_raise_of_one_identity_does_not_become_a_SECOND_ROW():
    """The pane projects what the lane holds, and what the lane holds folds. Beside the
    tooth above because the panel is where a broken fold would actually be SEEN — fifty
    rows of one flapping defect is the shape the damping exists to prevent, and it is
    the pane, not the store, that a human reads."""
    from cairn.devices.cairn.device import CairnDevice
    from cairn.devices.trouble.shim import TroubleShim
    from cairn.tools.base.diagnostic import DiagnosticBase

    class _Raiser(DiagnosticBase):
        @property
        def diagnostic_device(self) -> str:
            return "a_fixture_component"

    with tempfile.TemporaryDirectory() as tmp:
        from pathlib import Path
        roots = {k: Path(tmp) for k in ("repo", "commons", "instance")}
        shim = TroubleShim(roots=roots, root=Path(tmp) / "troubles")
        raiser = _Raiser()
        raiser.set_diagnostic_roots(roots)
        raiser.set_trouble_notifier(shim.receive_raise)

        raiser.raise_trouble("one-defect", why="a why")
        raiser.raise_trouble("one-defect", why="a why")

        data = _pane(CairnDevice(bus=_RoutingBus(shim)))["handler"]()
        assert [r["id"] for r in data] == ["one-defect"], data
        assert data[0]["count"] == 2, (
            f"the pane shows count {data[0]['count']} for two raises of one identity — "
            f"either the fold or the watermark is broken, and the panel is where a human "
            f"would meet it")


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


if __name__ == "__main__":
    # THIS FILE HAD NO ``__main__`` BLOCK AT ALL until 2026-09-07, and the tester runs a
    # proof as ``python3 <proof>``. So every seal it ever carried was an exit code from a
    # process that defined fourteen functions and ran none of them — a green over zero
    # teeth, which is the hollow build Law 8 exists to refuse. Measured, not guessed: nine
    # more proofs in the corpus are in the same state on the day this line was written.
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
