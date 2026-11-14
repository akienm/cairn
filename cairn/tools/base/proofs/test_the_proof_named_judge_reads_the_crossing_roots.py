"""Proof for red ticket d3248e7cb2fd — the proof-named judge reads the world the exit gate reads.

``crossing_proof_named`` (build_inspector) builds its union from ``crossings.proven_by_since_buildme``. Since 17d570c10390
(850d9d327) it runs in CodeMother's process, and a proof can stand a fixture world behind a judge only by her LAUNCH
environment, the inspector's ``_crossing_roots()`` (the exit gate already reads it: ``build_started(ticket, roots=
_crossing_roots())``). The proof-named judge passed no roots, so test_a_dead_proof_name_is_refused_at_proveme's tooth 3,
which substitutes ``crossings.ROOTS`` in the ASKER, never reached it: the union read the live journals and the crossing
crossed ungated. This tooth needs no bus: it calls the judge in this process and stands the world behind
``inspector._crossing_roots``, the one seam the launch environment feeds.

    python <this file>
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "d3248e7cb2fd": {
        "1": "the_proof_named_judge_reads_the_world_the_exit_gate_reads",
    },
}

_TICKET = "fixture-d324-proof-named-judge-reads-the-crossing-roots"
_GONE = "p/gone-d324-this-proof-names-no-file.py"


def the_proof_named_judge_reads_the_world_the_exit_gate_reads() -> None:
    from cairn.machines.build_inspector import inspector
    world = Path(str(scratch_dir("proof_named_roots_")))
    repo, commons = world / "repo", world / "commons"
    (repo / "fx").mkdir(parents=True)
    commons.mkdir()
    (repo / "fx" / "history.json").write_text(json.dumps({"entries": [{
        "from": "TICKETME", "to": "BUILDME", "direction": "forward", "ticket": _TICKET,
        "proven_by": _GONE, "at": "2026-01-01T10:00:00", "seq": 1}]}), encoding="utf-8", newline="\n")
    roots = {"repo": repo, "commons": commons}
    real = inspector._crossing_roots
    inspector._crossing_roots = lambda: roots
    try:
        record = inspector.crossing_proof_named(_TICKET, {"proven_by": "cairn/tools/base/probes/does_optional_mean_never_carried.py"})
    finally:
        inspector._crossing_roots = real
    values = record[0]["values"]
    assert values["since_buildme"] == [_GONE], f"the judge did not read the world _crossing_roots names: {values}"
    assert [d["name"] for d in values["dead"]] == [_GONE], f"the dead name from the union was not reported: {values['dead']}"


TEETH = [the_proof_named_judge_reads_the_world_the_exit_gate_reads]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
