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
PROVES = {"693e9f45e6f2": {"all": "test_every_built_probe_spec_names_a_file"}}

# Beside the checkout when there is one; hollow's /tmp worktree has none, so fall back
# to where hollow.py itself resolves the commons.
_COMMONS = _REPO_ROOT.parent / "CairnCommons"
_TICKETS = (_COMMONS if _COMMONS.is_dir() else Path.home() / "dev" / "src" / "CairnCommons") / "tickets"
_CURSOR = re.compile(r"\[([A-Z]+)")


def census(tickets: list[dict], repo: Path = _REPO_ROOT) -> list[dict]:
    """Every (ticket, probe) whose probe file is absent, with the ticket's cursor."""
    out = []
    for t in tickets:
        m = _CURSOR.search(t.get("workflow_and_state") or "")
        for p in _spec.absent_probes(t, root=repo):
            out.append({"tid": t.get("id"), "cursor": m.group(1) if m else "?",
                        "probe": p, "fixme": t.get("fixme") or []})
    return out


def _corpus() -> list[dict]:
    out = []
    for tp in sorted(_TICKETS.glob("*.json")):
        try:
            out.append(json.loads(tp.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            continue
    assert out, f"no tickets read under {_TICKETS}"
    return out


def test_no_proved_ticket_names_a_missing_probe():
    bad = [r for r in census(_corpus()) if r["cursor"] == "PROVED"]
    assert not bad, f"{len(bad)} PROVED ticket(s) name a missing probe:\n" + \
        "\n".join(f"  {r['tid']}  {r['probe']}" for r in bad)


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
