#!/usr/bin/env python3
"""Proof for ticket 284798998ab0, the rehearsal's half: the rehearsal reads a ticket split into
plan, state and log.

Moved here from cairn/tools/base/proofs/test_the_ticket_is_three_files.py by ticket
36bbcb2b45c4 (RULE 1): base's proof measured this machine, so the two teeth that need it berth
with it. Each runs over a scratch tickets dir whose store charter is the live one with its three
field lists set to the census ``CairnCommons/measurements/2026-10-29-ticket-fields-plan-state-log.json``.

  - a crossing moves only the state file: set_phase changes the state file and leaves the plan's
    bytes, and the rehearsal's design_sha of them, unchanged (base keeps the bytes half);
  - the failed-run probe counts no state file: a rehearsal record with ran false whose ticket
    has only an orphan .state.json (no plan beside it) is not counted as a failed run, because
    the probe finds tickets through ticket_file.plans_of, which yields plans alone.

The declared tooth, ``test_rehearsal_reads_the_three_file_ticket``, is both together (the
falsifier carries no numbered clauses).

    bin/cairn test cairn/devices/codemother/machines/rehearsal/proofs/test_rehearsal_reads_the_three_file_ticket.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

COMMONS = REPO.parent / "CairnCommons"
LIVE_CHARTER = COMMONS / "tickets" / "_charter+why.json"
CENSUS = COMMONS / "measurements" / "2026-10-29-ticket-fields-plan-state-log.json"

PROVES = {"284798998ab0": {"all": "test_rehearsal_reads_the_three_file_ticket"}}

CURSOR = "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED"
TID2 = "bbbbbbbbbbb2"


def _tickets(commons: Path) -> Path:
    t = commons / "tickets"
    t.mkdir(parents=True)
    charter = json.loads(LIVE_CHARTER.read_text(encoding="utf-8"))
    c = json.loads(CENSUS.read_text(encoding="utf-8"))["summary"]
    charter["plan_fields"], charter["state_fields"], charter["log_fields"] = c["plan"], c["state"], c["log"]
    (t / "_charter+why.json").write_text(json.dumps(charter, indent=2, ensure_ascii=False) + "\n",
                                          encoding="utf-8")
    return t


def _doc(tid: str) -> dict:
    return {"id": tid, "title": "a proof world ticket", "intention": "a fixture", "why": "a proof",
            "how": "none", "falsifier": "none", "decisions": [{"n": 1, "text": "D1: a line"}],
            "date": "2026-10-29", "owner": "CC", "node_class": "code-seam",
            "workflow_and_state": CURSOR, "watchme": "none, because a fixture",
            "questions": ["open-000000000000"]}


def _world(fn):
    """Run fn(tickets_dir) inside a scratch commons with the artifact roots pointed at it."""
    from cairn.tools.artifact import artifact as A
    with tempfile.TemporaryDirectory(prefix="cairn-rehearsal-three-files-proof-") as d:
        tmp = Path(d)
        commons = tmp / "CairnCommons"
        t = _tickets(commons)
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "cairn", "parked": tmp / "parked"})
        try:
            return fn(t)
        finally:
            A.set_diagnostic_roots(None)


def test_a_crossing_leaves_the_design_sha_unchanged() -> None:
    from cairn.devices.codemother.machines.rehearsal import rehearsal as R
    from cairn.tools.base import ticket_file as TF
    from cairn.tools.base import transitions as T

    def run(t: Path) -> None:
        plan = t / "eeee5555ffff-phase.json"
        TF.write_ticket(plan, _doc("eeee5555ffff"), False, True, why="proof")
        pb, sb = plan.read_bytes(), TF.state_path(plan).read_bytes()
        saved = TF._TICKETS
        TF._TICKETS = t
        try:
            T.set_phase(CURSOR, "hold", release="CLAUDE.md", actor="proof", ticket="eeee5555ffff")
        finally:
            TF._TICKETS = saved
        assert TF.state_path(plan).read_bytes() != sb, "the crossing did not move the state file"
        assert R.design_sha(plan.read_bytes()) == R.design_sha(pb), "the crossing changed the design_sha"
    _world(run)


def test_the_failed_run_probe_counts_no_state_file() -> None:
    from cairn.devices.codemother.machines.rehearsal.probes import a_failed_run_is_counted as P

    def run(t: Path) -> None:
        (t / (TID2 + "-an-orphan-state.state.json")).write_text(
            json.dumps({"workflow_and_state": CURSOR, "watchme": "none, because a fixture"}) + "\n",
            encoding="utf-8")
        r = t.parent / "rehearsals"
        r.mkdir()
        (r / "x.json").write_text(json.dumps({"ran": False, "ticket": TID2}), encoding="utf-8")
        got = P._measure({}, commons=t.parent)["failed"]
        assert got == 0, f"the probe counted {got} failed run(s) over an orphan state file"
    _world(run)


def test_rehearsal_reads_the_three_file_ticket() -> None:
    """The composite tooth."""
    test_a_crossing_leaves_the_design_sha_unchanged()
    test_the_failed_run_probe_counts_no_state_file()


def main() -> int:
    red = 0
    for fn in (test_a_crossing_leaves_the_design_sha_unchanged,
               test_the_failed_run_probe_counts_no_state_file,
               test_rehearsal_reads_the_three_file_ticket):
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            red += 1
            print(f"  FAIL  {fn.__name__}: {type(e).__name__}: {e}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
