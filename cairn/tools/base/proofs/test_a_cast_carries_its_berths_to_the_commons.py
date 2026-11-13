"""Proof for ticket d692ef650534: a ticket cast on a far box carries its berths to the commons.

MEASURED 2026-11-12, relayed verbatim from akiendelllinux: crossing 1029d5146152 to BUILDME
was refused with
    [buildme_rides_the_sorted] sorted berth readable (expected: True, actual: False)
Its sorted berth was fired on akienasus and sits in that box's instance-space
(~/.cairn/devices/skill_block/0/berths/sorted/), which the home box cannot read. Crossing
took an scp of each berth.

  1. test_a_cast_copies_its_berths: cast_ticket over a doc whose sorted_berth and intent_berth
     are files writes a byte-identical copy of each at <commons>/berths/<skill>/<basename>;
  2. test_read_berth_falls_back_to_the_commons: read_berth over a berth path that does not
     exist on this box returns the commons copy's document;
  3. test_a_none_because_intent_berth_copies_nothing: a 'none, because' intent_berth writes
     no copy, and the cast still lands.

Each tooth casts into a SCRATCH commons reached through ``artifact.set_diagnostic_roots``
(restored in ``finally``), the way skills/sorted/proofs/test_sorted_instructs_the_shaped_plan.py
does. The berths are fixture files under a scratch ``berths/<skill>/`` folder.

    bin/cairn test cairn/tools/base/proofs/test_a_cast_carries_its_berths_to_the_commons.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"d692ef650534": {
    "1": "test_a_cast_copies_its_berths",
    "2": "test_read_berth_falls_back_to_the_commons",
    "3": "test_a_none_because_intent_berth_copies_nothing",
}}

_WORKFLOW = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"


def _doc(tid: str, sorted_berth: str, intent_berth: str) -> dict:
    """A shaped ticket that the cast door admits, with only its id and berths varying."""
    return {
        "id": tid,
        "title": f"testing berths ride the cast {tid}",
        "date": "2026-11-12",
        "owner": "CC",
        "owning_intention": "cairn/tools/base/intention+why.json",
        "intention": "a fixture cast whose berths the door must carry to the commons.",
        "why": "Measured 2026-11-12: a berth fired on one box could not be read on another.",
        "traces_to": "the three roots (CLAUDE.md).",
        "how": "a fixture cast into a scratch commons.",
        "falsifier": {"clauses": [{"n": 1, "claim": "the berths ride the cast"}]},
        "decisions": [{"n": 1, "text": "D1: a fixture decision.",
                       "writes_to": [], "reads": ["cairn/tools/base/transitions.py"]}],
        "bounds": {"in": [], "out": ["every other component"]},
        "measured": [{"when": "2026-11-12", "saw": "a fixture", "how": "this proof"}],
        "node_class": "code-seam",
        "workflow_and_state": _WORKFLOW,
        "watchme": "none, because its proof cairn/tools/base/proofs/"
                   "test_a_cast_carries_its_berths_to_the_commons.py is the whole of its correctness",
        "sorted_berth": sorted_berth,
        "intent_berth": intent_berth,
    }


def _berth(tmp: Path, skill: str, name: str, doc: dict) -> Path:
    p = tmp / "berths" / skill / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(doc, indent=1) + "\n", encoding="utf-8")
    return p


def _sorted_berth(tmp: Path, tid: str) -> Path:
    return _berth(tmp, "sorted", f"sorted-20261112T000000-{tid}.json",
                  {"skill": "sorted", "answers": {"workflow": _WORKFLOW, "node_class": "code-seam"}})


class _Commons:
    """A scratch commons with the live ticket charter, the artifact door pointed at it."""

    def __init__(self, label: str) -> None:
        from cairn.tools.scratch.scratch import scratch_dir
        from cairn.tools.base.ticket_log import _LIVE_CHARTER
        self.tmp = scratch_dir(f"testing-d692ef650534-{label}-")
        self.commons = self.tmp / "CairnCommons"
        self.tickets = self.commons / "tickets"
        self.tickets.mkdir(parents=True)
        charter = _LIVE_CHARTER if _LIVE_CHARTER.is_file() else (
            Path.home() / "dev" / "src" / "CairnCommons" / "tickets" / "_charter+why.json")
        (self.tickets / "_charter+why.json").write_bytes(charter.read_bytes())

    def __enter__(self) -> "_Commons":
        from cairn.tools.artifact import artifact as A
        A.set_diagnostic_roots({"CairnCommons": self.commons, "cairn": _REPO})
        return self

    def __exit__(self, *exc) -> None:
        from cairn.tools.artifact import artifact as A
        A.set_diagnostic_roots(None)


def test_a_cast_copies_its_berths():
    from cairn.tools.base.transitions import cast_ticket
    with _Commons("copies") as c:
        tid = "d69200000001"
        s = _sorted_berth(c.tmp, tid)
        i = _berth(c.tmp, "intent", f"intent-20261112T000000-{tid}.json", {"skill": "intent"})
        cast_ticket(_doc(tid, str(s), str(i)), actor="proof-actor", tickets_dir=c.tickets)
        for src, skill in ((s, "sorted"), (i, "intent")):
            copy = c.commons / "berths" / skill / src.name
            assert copy.is_file(), f"no commons copy of the {skill} berth at {copy}"
            assert copy.read_bytes() == src.read_bytes(), f"the {skill} copy's bytes differ: {copy}"


def test_read_berth_falls_back_to_the_commons():
    from cairn.machines.skill_block.skill_block import read_berth
    with _Commons("reads") as c:
        name = "sorted-20261112T000000-d69200000002.json"
        doc = {"skill": "sorted", "answers": {"node_class": "code-seam"}, "mark": "the commons copy"}
        copy = c.commons / "berths" / "sorted" / name
        copy.parent.mkdir(parents=True)
        copy.write_text(json.dumps(doc), encoding="utf-8")
        far = c.tmp / "another-box" / ".cairn" / "devices" / "skill_block" / "0" / "berths" / "sorted" / name
        assert not far.exists(), f"the far path must not exist on this box: {far}"
        got = read_berth(far)
        assert got == doc, f"read_berth over a far path returned {got!r}, not the commons copy"
        # A berth fired on a Windows box is cited as a backslash string; on POSIX a plain Path
        # reads it as ONE name, so the commons address came out as berths/C:\Users\...
        # (measured 2026-11-12 on the Dell). Both spellings map to <commons>/berths/<skill>/<name>.
        from cairn.machines.skill_block.skill_block import commons_address
        want = c.commons / "berths" / "sorted" / name
        win = "C:" + chr(92) + "Users" + chr(92) + "akien" + chr(92) + ".cairn" + chr(92) + "devices" + chr(92) + "skill_block" + chr(92) + "0" + chr(92) + "berths" + chr(92) + "sorted" + chr(92) + name
        posix = "/home/akien/.cairn/devices/skill_block/0/berths/sorted/" + name
        for spelling in (win, posix):
            addr = commons_address(spelling)
            assert addr == want, f"commons_address({spelling!r}) -> {addr}, not {want}"
        assert read_berth(win) == doc, "read_berth over a backslash (Windows-written) berth path missed the commons copy"


def test_a_none_because_intent_berth_copies_nothing():
    from cairn.tools.base.transitions import cast_ticket
    with _Commons("none") as c:
        tid = "d69200000003"
        s = _sorted_berth(c.tmp, tid)
        none = "none, because a fixture cast has no intent; see cairn/tools/base/transitions.py"
        p = cast_ticket(_doc(tid, str(s), none), actor="proof-actor", tickets_dir=c.tickets)
        assert p.is_file(), f"the cast did not land: {p}"
        intent = c.commons / "berths" / "intent"
        assert not intent.exists() or not any(intent.iterdir()), (
            f"a 'none, because' intent_berth wrote a copy: {sorted(intent.iterdir())}")
        assert (c.commons / "berths" / "sorted" / s.name).is_file(), (
            "the sorted berth was not carried beside a 'none, because' intent_berth")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
