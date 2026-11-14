"""Proof for 15cd72404522: the proof-named crossing judge in CodeMother's process reads the inspector's launch roots.

Since 17d570c10390 the crossing judges run in CodeMother's process, and a proof can stand a fixture world behind them
only by her LAUNCH environment, which the inspector reads into ``_crossing_roots()`` (the world the exit gate reads).
``crossing_proof_named`` passed no roots to ``crossings.proven_by_since_buildme``, so it read the live world, and base's
proof for red ticket d3248e7cb2fd read red.

  1. crossing_proof_named, with a fixture world behind ``inspector._crossing_roots`` holding a BUILDME crossing and a
     since-named dead proof, reads that world: the dead name is in the union it judges.

The FIXME judge needs no such change: ``crossing_fixme`` resolves by ``_tf.find_ticket``, which reads
``ticket_file._TICKETS``, and the inspector bends that by the ``ticket_store`` launch (3e08102ef35a, on main). Measured
2026-11-14: resolving it under ``_TICKETS_ROOT`` instead bypassed that launch and redded test_fixme.py and
test_every_watching_class_can_fixme.py, whose fixtures launch with ``ticket_store=``.

Tooth 1 is d5ca3c7ae's in-process tooth (it stood in cairn/tools/base/proofs/, though it measures the inspector),
re-homed. It calls the judge in this process; no bus.

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
    "15cd72404522": {
        "1": "the_proof_named_judge_reads_the_world_the_exit_gate_reads",
    },
}

_TICKET = "fixture-15cd-proof-named-judge-reads-the-crossing-roots"
_GONE = "p/gone-15cd-this-proof-names-no-file.py"


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
        record = inspector.crossing_proof_named(
            _TICKET, {"proven_by": "cairn/tools/base/probes/does_optional_mean_never_carried.py"})
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
