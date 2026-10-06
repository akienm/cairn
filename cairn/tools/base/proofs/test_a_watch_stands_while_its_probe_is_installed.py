"""Proof: a ticket's watch STANDS while its probe is installed — not only once the ticket rests
(ticket 8e37bf2be2dc).

MEASURED RED 2026-10-06, the reason this file exists. The cairn device's proof that "every
standing cairn probe reports to harbor_master's watch verb" (ticket f1da5944464e) decided
"standing" by hand: a ticket at PROVED or WATCHME, nothing else. 7a1265439f54 — the only
ticket naming a probe under ``cairn/devices/cairn/probes/`` — was sent to FIXME BY ITS OWN
WATCH, fixed forward, and now sits at PROVEME with the probe installed and firing. The
population read empty, the proof sealed red, ``component_color`` redded the cairn device, and
7a12 could not cross into the WATCHME that would make the population non-empty again. A
deadlock, and also a population bug: a probe whose ticket sits at FIXME or PROVEME is still
installed and still firing, and it got there THROUGH the watch, so counting only resting
tickets drops exactly the probes most likely to be red.

What a WATCHME spec means is this module's question, and ``armed_error`` already measures
"installed". So the reader lives here, and a proof elsewhere consumes it through the public
interface instead of re-deciding it.

Teeth a hollow build could not pass:
  1. a ticket at FIXME, or at PROVEME, whose spec's probe is armed STANDS;
  2. a ticket at PROVED or WATCHME stands unconditionally — even with its probe not armed —
     exactly as the hand rule counted it;
  3. a ticket at FIXME/PROVEME whose probe is NOT armed does not stand, and neither does one
     whose cursor has not yet reached the build's far side (TICKETME, BUILDME) though its
     probe is armed;
  4. over the REAL ticket corpus, every (ticket, spec) the old PROVED/WATCHME rule counted
     still stands — the widening only ADDS members, never removes one.

    python3 cairn/tools/base/proofs/test_a_watch_stands_while_its_probe_is_installed.py
"""
from __future__ import annotations

import atexit
import json
import shutil
import sys
import tempfile
from functools import cache
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import watchme_spec as ws

PROVES = {"8e37bf2be2dc": {
    "1": "test_a_ticket_off_rest_with_an_ARMED_probe_stands",
    "2": "test_a_resting_ticket_stands_UNCONDITIONALLY",
    "3": "test_an_unarmed_or_unbuilt_watch_does_NOT_stand",
    "4": "test_the_widening_only_ADDS_over_the_real_corpus",
}}

# The live commons, resolved as hollow.py resolves it (a /tmp worktree has none beside it).
_TICKETS = ws._TICKETS if ws._TICKETS.is_dir() else \
    Path.home() / "dev" / "src" / "CairnCommons" / "tickets"

_ARMED = '''
from cairn.tools.base.probe import Probe
PROBE = Probe(why="a fixture probe, armed", trigger=lambda *a: False, to="harbor_master",
              verb="watch", carry=lambda ctx: {}, enough=lambda ctx: True)
'''
_UNARMED = '''
from cairn.tools.base.probe import Probe
PROBE = Probe(why="a fixture probe with no carry and no enough", trigger=lambda *a: False,
              to="harbor_master", verb="watch")
'''


def _wf(here: str) -> str:
    path = ["THINKME", "TICKETME", "FIXME", "BUILDME", "PROVEME",
            "WATCHME(fixture-watch)", "PROVED"]
    shown = [f"[{p}]" if p.split("(")[0] == here else p for p in path]
    return "code-seam@v2: " + " -> ".join(shown)


def _ticket(here: str, probe: str) -> tuple[dict, dict]:
    spec = {"object": "fixture-watch", "probe": probe}
    return {"id": "fixture", "workflow_and_state": _wf(here), "watchme": spec}, spec


@cache
def _root() -> Path:
    root = Path(tempfile.mkdtemp(prefix="stands-watch-fixture-probes-"))
    atexit.register(shutil.rmtree, root, True)
    (root / "armed.py").write_text(_ARMED, encoding="utf-8")
    (root / "unarmed.py").write_text(_UNARMED, encoding="utf-8")
    return root


def test_a_ticket_off_rest_with_an_ARMED_probe_stands():
    root = _root()
    for here in ("FIXME", "PROVEME"):
        t, spec = _ticket(here, "armed.py")
        assert ws.stands_watch(t, spec, root=root), (
            f"a ticket at {here} whose probe is installed does not stand — the watch that "
            "sent it there is dropped from the population")


def test_a_resting_ticket_stands_UNCONDITIONALLY():
    root = _root()
    for here in ("PROVED", "WATCHME"):
        for probe in ("armed.py", "unarmed.py", "nowhere.py"):
            t, spec = _ticket(here, probe)
            assert ws.stands_watch(t, spec, root=root), (
                f"a ticket at {here} (probe {probe}) no longer stands — the widening removed "
                "a member the hand rule counted")


def test_an_unarmed_or_unbuilt_watch_does_NOT_stand():
    root = _root()
    for here in ("FIXME", "PROVEME"):
        for probe in ("unarmed.py", "nowhere.py"):
            t, spec = _ticket(here, probe)
            assert not ws.stands_watch(t, spec, root=root), (
                f"a ticket at {here} whose probe {probe} is not armed stands anyway")
    for here in ("TICKETME", "BUILDME"):
        t, spec = _ticket(here, "armed.py")
        assert not ws.stands_watch(t, spec, root=root), (
            f"a ticket at {here} stands though its build has not reached PROVEME")


def test_the_widening_only_ADDS_over_the_real_corpus():
    from cairn.tools.base.transitions import parse_workflow
    counted = 0
    for path in sorted(_TICKETS.glob("*.json")):
        try:
            doc = json.loads(path.read_text("utf-8"))
            here = parse_workflow(doc["workflow_and_state"]).here
        except Exception:
            continue
        if here not in ("PROVED", "WATCHME"):
            continue
        declared = doc.get("watchme")
        specs = declared if isinstance(declared, list) else [declared]
        for spec in specs:
            if isinstance(spec, dict) and spec.get("probe"):
                counted += 1
                assert ws.stands_watch(doc, spec), (
                    f"{doc.get('id')} at {here} was counted by the hand rule and no longer stands")
    assert counted, "the real corpus holds no resting ticket with a probe — the population vanished"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
