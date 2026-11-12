"""Proof: the cairn device's trouble panel — pane declaration, handler data shape, the
store-to-pane read timed and read with no bus, the 30-day sweep reaching the store, and the
WATCHME probe. The render of the pane is the web server's and is proved in its own proofs
(RULE 1, ticket 6d324d26343d).

Teeth a hollow build could not pass: an unoverridden declared_panes returns [], a reader
that asks the bus reds against refused dials, and an absent probe module raises ImportError.
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
# function once per heartbeat is reciting, not measuring). So the clause is served by
# proofs, each owner timing its own seam (RULE 1, ticket 6d324d26343d): raise → store in
# trouble's, store → pane here, pane → HTML in the web server's.
PROVES = {
    "9579a6f9cec6": {
        "5": "test_a_stored_trouble_reaches_the_PANE_inside_the_budget",
    },
    "6d324d26343d": {
        "3": "test_a_stored_trouble_reaches_the_PANE_inside_the_budget",
        "4": "test_the_30_day_sweep_reaches_the_trouble_store",
    },
    "7a1265439f54": {
        "1": "test_the_panel_owns_no_route_of_its_own",
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


# ── end to end, the cairn half: store → pane, timed ──────────────────────────────

def test_a_stored_trouble_reaches_the_PANE_inside_the_budget():
    """Ticket 9579a6f9cec6 clause (5), the half that is the cairn device's (RULE 1, ticket
    6d324d26343d). The clause asks for a raised trouble VISIBLE within 1s of the raise. The lane has
    three owners and each times its own seam: the raise poked and folded into the store is
    timed in trouble's proofs (test_trouble_proofs_measure_only_trouble.py), the HTML in the
    web server's (test_the_web_server_renders_and_reads_troubles.py), and the read from the
    store into this pane's data is timed here. Asserted as a bound, never a snapshot."""
    from cairn.devices.cairn.device import CairnDevice
    with tempfile.TemporaryDirectory() as tmp:
        roots, _ = _store(tmp, [_row("a-fixture-trouble-for-the-pane")])
        started = time.monotonic()
        data = _pane(CairnDevice(roots=roots))["handler"]()
        elapsed = time.monotonic() - started
    assert [r["id"] for r in data] == ["a-fixture-trouble-for-the-pane"], data
    assert data[0]["standing"] == "OPEN" and data[0]["count"] == 1, data[0]
    assert elapsed < 1.0, f"store → pane took {elapsed:.3f}s, over the 1s budget the clause names"


class _Refused(Exception):
    pass


def _refuse_dials():
    """Refuse the bus client's reach() — the one door to any host — and return the undo."""
    import cairn.tools.bus_client as bc
    saved = bc.reach

    def no_reach(*a, **kw):
        raise _Refused(f"reach{a}")

    bc.reach = no_reach

    def undo():
        bc.reach = saved
    return undo


def test_the_pane_and_its_probe_read_with_no_bus():
    """The pane and the probe watching it read the store through trouble's published tool,
    every dial refused (ticket ee04bb869795; berthed here by 6d324d26343d). A seeded store reads its
    live rows in both; an absent store raises in the pane, and never as a bus ask."""
    from cairn.devices.cairn.device import CairnDevice
    from cairn.devices.cairn.probes import trouble_panel_surfaces_live_troubles as probe
    undo = _refuse_dials()
    try:
        with tempfile.TemporaryDirectory() as tmp:
            roots, _ = _store(tmp, [_row("proof-live-a"), _row("proof-live-b")])
            data = _pane(CairnDevice(roots=roots))["handler"]()
            got = probe._check({"roots": roots})
        with tempfile.TemporaryDirectory() as tmp:
            roots, _ = _store(tmp)
            with pytest.raises(FileNotFoundError):
                _pane(CairnDevice(roots=roots))["handler"]()
    finally:
        undo()
    assert [r["id"] for r in data] == ["proof-live-a", "proof-live-b"], data
    assert got.get("healthy") is True and got.get("live_count") == 2, got


def test_the_30_day_sweep_reaches_the_trouble_store():
    """The cairn device's log sweep reaches the trouble store's own address: a cleared ticket
    31 days old under the published tool's store_root is gone after one sweep, and a fresh one
    stays (moved here from trouble's proofs by 6d324d26343d)."""
    from pathlib import Path
    from cairn.devices.cairn.logs_sweep import sweep_logs
    from cairn.devices.trouble.tools.store import store
    with tempfile.TemporaryDirectory() as tmp:
        roots = {"instance": Path(tmp)}
        cleared = store.store_root(roots) / "cleared"
        cleared.mkdir(parents=True)
        aged, fresh = cleared / "proof-aged.json", cleared / "proof-fresh.json"
        for f in (aged, fresh):
            f.write_text(json.dumps(_row(f.stem, standing="CLEARED")), encoding="utf-8")
        old = time.time() - 31 * 86400
        os.utime(aged, (old, old))
        sweep_logs(roots=roots)
        assert not aged.exists(), "the 30-day sweep did not reach the trouble store"
        assert fresh.exists(), "the sweep took a cleared ticket younger than 30 days"


def test_the_panel_owns_no_route_of_its_own():
    """Clause (1) of 7a1265439f54: the panel is a PANE on the one web server, never its own
    route, port or server. The pane declaration carries no route, port or server key, and no
    module of the cairn device outside its proofs imports a web framework. The web server's
    own proofs hold that its socket route exists."""
    from pathlib import Path
    from cairn.devices.cairn.device import CairnDevice
    pane = _pane(CairnDevice())
    assert not {"route", "port", "path", "server", "url"} & set(pane), sorted(pane)
    here = Path(__file__).resolve().parents[1]
    hits = [str(f) for f in here.rglob("*.py") if "proofs" not in f.parts
            and any(w in f.read_text(encoding="utf-8") for w in ("import starlette", "from starlette",
                                                                 "import uvicorn", "from uvicorn"))]
    assert not hits, hits


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
