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
# where a raise, a real drain, a real store read and a real render can be run end to
# end in one process and TIMED — which is what the clause was actually after. What a
# proof cannot put in the loop is the socket itself; the budget measured is the poke
# path the socket pushes, and the tooth says so at its assertion.
PROVES = {
    "9579a6f9cec6": {
        "5": "test_a_raised_trouble_reaches_the_RENDERED_PANE_over_the_poke_path",
    },
    "7a1265439f54": {
        "1": "test_websocket_route_exists",
        "2": "test_an_UNHEALTHY_probe_NAMES_ITS_FINDING",
        "3": "test_the_panel_is_the_CAIRN_devices_not_the_hosts",
    },
}


def _store(tmp, rows=None):
    """A scratch trouble store holding ``rows`` as files, and the roots that find it.

    THE STAND-IN IS A DIRECTORY NOW (ticket ee04bb869795). The pane asked verb ``live`` over
    the bus until 2026-10-18 and this proof answered for it with a fake bus; every real reply
    stood as a bus row, and Akien ruled "TROUBLE TICKETS ARE A FILE ARTIFACT IN THE LOGGING
    TREE". So the pane reads files, and the honest fixture is files where the store lives.
    The path comes from the address door, so the proof still imports nothing from
    ``cairn.devices.trouble`` to stage it."""
    from pathlib import Path
    from cairn.tools.base.address import log_path
    roots = {k: Path(tmp) for k in ("repo", "commons", "instance")}
    store = log_path("cairn", 0, roots) / "troubletickets"
    if rows is not None:
        store.mkdir(parents=True)
        for i, r in enumerate(rows):
            (store / f"{i:02d}-{r['id']}.json").write_text(json.dumps(r), encoding="utf-8")
    return roots, store


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


def test_the_panel_is_the_CAIRN_devices_not_the_hosts():
    """Clause (3) of 7a1265439f54: the cairn device is the PROJECT, system_rackmount is the
    LAPTOP — different scopes, different devices. The pane is declared by the device whose
    id is ``cairn``, and that device states its scope as the system, not the host. Holds at
    every build that keeps the identity; it is here so the clause has a tooth that a
    rename into the host's address would red."""
    from cairn.devices.cairn.device import CairnDevice
    d = CairnDevice()
    assert d.device_id == "cairn", d.device_id
    assert "rackmount" not in d.device_id and "host" not in d.device_id
    assert [p for p in d.declared_panes() if p.get("kind") == "trouble"], (
        "the trouble pane is not declared by the cairn device")
    what = d.intention()["what"].lower()
    assert "cairn system device" in what and "rackmount" not in what, what


def test_handler_reads_the_store_as_files():
    """The pane READS trouble's store through the tool trouble publishes, and asks nobody
    (ticket ee04bb869795). A CairnDevice handed no bus at all answers, which is the
    claim: there is no ask left to fail."""
    from cairn.devices.cairn.device import CairnDevice
    with tempfile.TemporaryDirectory() as tmp:
        roots, _ = _store(tmp, [_row("test-trouble-1", count=3)])
        data = _pane(CairnDevice(roots=roots))["handler"]()
    assert len(data) == 1
    row = data[0]
    for key in ("id", "standing", "why", "count", "first_seen", "last_seen"):
        assert key in row, f"trouble row missing key: {key}"
    assert row["id"] == "test-trouble-1"
    assert row["standing"] == "OPEN"
    assert row["count"] == 3


def test_an_ABSENT_store_never_renders_as_ZERO_TROUBLES():
    """THE TOOTH THIS WHOLE PANE TURNS ON, and the one a hollow build fails by being tidy.

    An empty trouble panel is the NORMAL OPERATING STATE — it is what a healthy system
    looks like. So a handler that swallowed a failure and returned ``[]`` would render the
    calmest possible page at the exact moment the store could not be read, and it would be
    indistinguishable from good news. Raising is what makes the difference visible:
    ``BaseShim.active_page`` renders a raising handler as an ABSENT pane carrying the
    reason (Law 7 — a presentation surface may collapse an error into a coherent shape,
    and 'no troubles' is not a shape this error has)."""
    from cairn.devices.cairn.device import CairnDevice

    with tempfile.TemporaryDirectory() as tmp:
        roots, _ = _store(tmp)                           # no store at all
        with pytest.raises(FileNotFoundError):
            _pane(CairnDevice(roots=roots))["handler"]()

    # ...and the genuinely empty case is NOT an error — that is the distinction being drawn.
    with tempfile.TemporaryDirectory() as tmp:
        roots, _ = _store(tmp, [])
        assert _pane(CairnDevice(roots=roots))["handler"]() == []


def test_the_pane_projects_and_does_not_filter():
    """Which rows are LIVE is trouble's property — the top of its store is the live set,
    decided behind trouble's own gate — and the pane's job stops at projection. Asserted as
    a negative: whatever the store holds at its top is what appears, one row for one row.
    The old shape had this device holding the store and re-deriving liveness for itself —
    two hands on one question, and the pane's hand had no owner (Law 6)."""
    from cairn.devices.cairn.device import CairnDevice
    rows = [_row("t-0"), _row("t-1", standing="CLEARED"), _row("t-2")]
    with tempfile.TemporaryDirectory() as tmp:
        roots, _ = _store(tmp, rows)
        data = _pane(CairnDevice(roots=roots))["handler"]()
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


# ── end to end: raise → poke → drain → read → render ────────────────────────────

def test_a_raised_trouble_reaches_the_RENDERED_PANE_over_the_poke_path():
    """THE WHOLE LANE IN ONE PROCESS, and the only tooth here that runs it end to end.

    Ticket 9579a6f9cec6 clause (5). A component that holds nothing of ``cairn.devices``
    raises; the poke drains it into the held store; the cairn device's pane reads the
    store through trouble's tool (ticket ee04bb869795 — it asked ``live`` over the bus
    until 2026-10-18); the rows render. Each half of that is already proved separately —
    the raise in ``cairn/tools/base/proofs/test_raise_trouble.py``, the fold in trouble's
    own proof, the projection and the render above — and a lane can be green in every
    half and dark end to end, because the seams are where the store's address, the row shape
    and the drain's watermark all live. That is what this tooth is for.

    THE BUDGET, AND WHAT IT HONESTLY COVERS. The clause asks for the trouble VISIBLE
    within 1s of the raise. The socket is not in this loop — a proof cannot hold a
    browser — so what is timed is the path the socket pushes: raise → poke → drain →
    read → HTML. If that path is inside the budget the push is a transport question;
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
        shim = TroubleShim(roots=roots)  # the store the pane reads, under the roots

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

        data = _pane(CairnDevice(roots=roots))["handler"]()
        html = render_pane({"kind": "trouble", "label": "troubles", "data": data})
        elapsed = time.monotonic() - started

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
        shim = TroubleShim(roots=roots)  # the store the pane reads, under the roots
        raiser = _Raiser()
        raiser.set_diagnostic_roots(roots)
        raiser.set_trouble_notifier(shim.receive_raise)

        raiser.raise_trouble("one-defect", why="a why")
        raiser.raise_trouble("one-defect", why="a why")

        data = _pane(CairnDevice(roots=roots))["handler"]()
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


def test_an_UNHEALTHY_probe_NAMES_ITS_FINDING():
    """THE FIXME THIS TOOTH WAS WRITTEN AGAINST (7a1265439f54, 2026-10-05). An unhealthy
    pulse put its reason under ``error`` and nothing under ``finding``, so ``watch_carry``
    filed the generic _NO_FINDING and the ticket landed at FIXME saying only that the probe
    had nothing to say. The probe KNEW why — it had just written it down one key over. A
    watch whose red cannot name its cause sends a mind to re-derive what the probe already
    measured (Law 1), so each way to be unhealthy must arrive as the finding itself."""
    from cairn.devices.cairn.probes.trouble_panel_surfaces_live_troubles import PROBE
    from cairn.tools.base.probe import _NO_FINDING

    # The read is the probe's whole measurement since ticket ee04bb869795; an absent store
    # is the way it goes unhealthy, and the finding must say the store was not there.
    with tempfile.TemporaryDirectory() as tmp:
        roots, store = _store(tmp)
        out = PROBE.carry({"roots": roots})
        assert out["holds"] is False, out
        assert out["finding"] != _NO_FINDING, f"the carry named no finding: {out}"
        for needle in ("read failed", "no trouble store", str(store)):
            assert needle in out["finding"], f"{needle!r} not in the finding: {out['finding']!r}"

    with tempfile.TemporaryDirectory() as tmp:
        roots, _ = _store(tmp, [])
        healthy = PROBE.carry({"roots": roots})
    assert healthy["holds"] is True and healthy["finding"] == "", healthy


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
