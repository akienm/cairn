"""Proof for ticket 693e9f45e6f2 — no WATCHME spec on a built ticket points at a probe file that is not there.

Child 1 of 835b5736bf2b (every-probe-has-a-receiver). Akien, W2 (~/.cairn/foreground-decisions.md
item 2): "if the WATCHME step is incomplete ... then it's a fault and goes back for fixing".

THE MEASURED FAILURE THIS EXISTS FOR. Census 2026-10-02 over CairnCommons/tickets: 50 probe-bearing
specs named a file that did not exist. Eleven had moved (builder -> codemother, harbor_master ->
cairn/machines/harbor_master, tools/base -> tools/bus_client) and still named the old path; twelve
sat on PROVED tickets whose probe was deleted or parked in probes_disabled/. A spec naming a missing
file is a record of truth that lies (Law 7): the ticket reads as watched, and nothing watches.

The instrument is the REAL corpus, never a fixture, so the teeth assert invariants over live data:

  1. NO PROVED TICKET NAMES A MISSING PROBE. A ticket whose cursor stands at PROVED has finished
     its WATCHME; every probe its spec names exists on disk.
  2. A TICKET SENT BACK FOR AN ABSENT PROBE NAMES IT. A ticket at FIXME whose spec names a missing
     probe carries that path in its fixme list, so the fault says what is missing.
  3. THE CENSUS IS NOT VACUOUS. The same function reds a fixture PROVED ticket naming a path that
     does not exist — a check that passes everything is not a check.

    python3 cairn/tools/base/proofs/test_every_built_probe_spec_names_a_file.py   # exit 0 = green
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

class _Late:
    """The build's names resolve AT CALL TIME, so `cairn test --hollow` reverting
    watchme_spec.py reads as red teeth rather than an import that never ran."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_spec = _Late("cairn.tools.base.watchme_spec")

# The ticket's falsifier is one unnumbered clause ("all"), so ONE composite tooth claims it;
# the three named teeth below are its parts and still print one by one.
PROVES = {
    "693e9f45e6f2": {"all": "test_every_built_probe_spec_names_a_file"},
    "7088856d2150": {
        "1": "test_no_proved_ticket_names_a_missing_probe",
        "2": "test_a_ticket_sent_back_for_an_absent_probe_names_it",
        "3": "test_a_watchme_ticket_naming_nothing_reds",
        "4": "test_a_valid_forwarding_order_disposes_the_absent_probe",
        "5": "test_a_broken_or_folder_order_grants_nothing",
    },
}

# Beside the checkout when there is one; hollow's /tmp worktree has none, so fall back
# to where hollow.py itself resolves the commons.
_COMMONS = _REPO_ROOT.parent / "CairnCommons"
_TICKETS = (_COMMONS if _COMMONS.is_dir() else Path.home() / "dev" / "src" / "CairnCommons") / "tickets"
_CURSOR = re.compile(r"\[([A-Z]+)")


def census(tickets: list[dict], repo: Path = _REPO_ROOT) -> list[dict]:
    """Every (ticket, probe) whose probe file is absent and not validly forwarded by any
    ticket in the same list (ticket 7088856d2150), with the ticket's cursor."""
    forwarded = _spec.forwarded_paths(tickets, root=repo)
    out = []
    for t in tickets:
        m = _CURSOR.search(t.get("workflow_and_state") or "")
        for p in _spec.absent_probes(t, root=repo):
            if p in forwarded:
                continue
            out.append({"tid": t.get("id"), "cursor": m.group(1) if m else "?",
                        "probe": p, "fixme": t.get("fixme") or []})
    return out


def _corpus() -> list[dict]:
    """Every ticket read WHOLE — plan and state merged (284798998ab0 D11: a ticket is three
    files). A glob of *.json read each .state.json as a ticket of its own, with no id."""
    from cairn.tools.base.ticket_file import plans, read_ticket
    out = []
    for tp in plans(_TICKETS):
        try:
            out.append(read_ticket(tp))
        except (OSError, ValueError):
            continue
    assert out, f"no tickets read under {_TICKETS}"
    return out


def test_no_proved_ticket_names_a_missing_probe():
    rows = census(_corpus())
    nameless = [r for r in rows if not r["tid"]]
    assert not nameless, f"census rows without a ticket id: {nameless}"
    bad = [r for r in rows if r["cursor"] in ("PROVED", "WATCHME")]
    assert not bad, f"{len(bad)} PROVED or WATCHME ticket(s) name a missing probe:\n" + \
        "\n".join(f"  {r['tid']}  {r['cursor']}  {r['probe']}" for r in bad)


_GHOST = "cairn/no/such/dir/fixture_probe_that_never_existed.py"
_PRESENT = "bin/proofs/test_retired_components_are_gone.py"


def _fixture(cursor: str, tid: str = "fixture-names-a-ghost") -> dict:
    return {"id": tid, "workflow_and_state": f"code-seam@v2: THINKME -> PROVEME -> [{cursor}]",
            "watchme": [{"probe": _GHOST}]}


def _forwarder(order: dict) -> dict:
    return {"id": "fixture-forwarder", "workflow_and_state": "code-seam@v2: [PROVED]",
            "forwarding": order}


def test_a_watchme_ticket_naming_nothing_reds():
    for cursor in ("PROVED", "WATCHME"):
        got = census([_fixture(cursor)])
        assert [(r["tid"], r["cursor"]) for r in got] == [("fixture-names-a-ghost", cursor)], got
    print("ok test_a_watchme_ticket_naming_nothing_reds")


def test_a_valid_forwarding_order_disposes_the_absent_probe():
    order = {_GHOST: {"to": _PRESENT, "why": "fixture: the retirement deleted it"}}
    got = census([_fixture("PROVED"), _forwarder(order)])
    assert got == [], f"a valid forwarding order did not dispose the probe: {got}"
    print("ok test_a_valid_forwarding_order_disposes_the_absent_probe")


def test_a_broken_or_folder_order_grants_nothing():
    present_from = str(Path(__file__).relative_to(_REPO_ROOT))
    orders = {
        "to does not exist": {_GHOST: {"to": "cairn/no/such/target.py", "why": "x"}},
        "no why": {_GHOST: {"to": _PRESENT, "why": ""}},
        "parent folder only": {"cairn/no/such/dir": {"to": _PRESENT, "why": "x"}},
    }
    for name, order in orders.items():
        got = census([_fixture("PROVED"), _forwarder(order)])
        assert [r["tid"] for r in got] == ["fixture-names-a-ghost"], f"{name}: granted {got}"
    still = {"id": "fixture-still-there", "workflow_and_state": "x [PROVED]",
             "watchme": [{"probe": present_from}]}
    assert _spec.forwarded_paths(
        [_forwarder({present_from: {"to": _PRESENT, "why": "x"}}), still],
        root=_REPO_ROOT) == set(), "an order whose from still exists was granted"
    print("ok test_a_broken_or_folder_order_grants_nothing")


def test_a_ticket_sent_back_for_an_absent_probe_names_it():
    bad = [r for r in census(_corpus())
           if r["cursor"] == "FIXME" and r["probe"] not in json.dumps(r["fixme"])]
    assert not bad, f"{len(bad)} FIXME ticket(s) do not name their absent probe:\n" + \
        "\n".join(f"  {r['tid']}  {r['probe']}" for r in bad)


def test_the_census_reds_a_missing_probe():
    fixture = {"id": "fixture-proved-names-nothing",
               "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]",
               "watchme": [{"probe": "cairn/no/such/dir/fixture_probe_that_never_existed.py"}]}
    present = dict(fixture, id="fixture-proved-names-this-file",
                   watchme=[{"probe": str(Path(__file__).relative_to(_REPO_ROOT))}])
    got = census([fixture, present])
    assert [r["tid"] for r in got] == ["fixture-proved-names-nothing"], got


def test_every_built_probe_spec_names_a_file():
    test_no_proved_ticket_names_a_missing_probe()
    test_a_ticket_sent_back_for_an_absent_probe_names_it()
    test_the_census_reds_a_missing_probe()


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))
