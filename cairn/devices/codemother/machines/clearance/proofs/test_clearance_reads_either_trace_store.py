#!/usr/bin/env python3
"""Proof that clearance's read_attempts counts the same over either trace store.

Measured 2026-11-16: the claim "clearance's queue reader counts the same over a legacy-named
store and a new-name store" was proved only by learning_block's
test_a_trace_file_name_is_legal_on_every_box (ticket a9709b744bf5, clause 4), which imports
cairn.devices.codemother.machines.clearance — a machine proof measuring a device's reader
(RULE 1: a proof measures only its own component). The claim is CodeMother's, so it is proved
here, at the reader's own address; learning_block's clause then narrows to its skill readers.

A legacy file is named with the block verbatim ("harbor_master:clearance.jsonl"). NTFS cannot
hold a ':', so on Windows the legacy name is supplied through learning_block's
legacy_trace_path seam (a plain-named file), as the learning_block proof does.

Teeth, each binding the code under test at call time:
  (1) over a legacy-only store and a new-name-only store, read_attempts returns the same
      attempts and the same unreadable_lines: 2 attempts (one granted, one refused) and 1;
  (2) with both files present it returns the legacy file's attempts first, then the new one's.

    CAIRN_BUS_HOME=<scratch> bin/cairn test cairn/devices/codemother/machines/clearance/proofs/test_clearance_reads_either_trace_store.py
"""
from __future__ import annotations

import json
import os
import sys
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[6]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"20f7a78faaa5": {
    "1": "test_either_store_counts_the_same",
    "2": "test_both_stores_read_legacy_first",
}}

WHEN = "2026-11-16T12:00:00+00:00"


def _seed(cl, tag: str) -> list[str]:
    data = {"actor": "cc", "boat": f"b-{tag}", "target": "t", "workflow": "w"}
    return [json.dumps({"id": f"{tag}1", "when": WHEN, "block": cl.QUEUE_BLOCK,
                        "event": cl.GRANTED, "consumer": cl.QUEUE_CONSUMER, "data": data}),
            json.dumps({"id": f"{tag}2", "when": WHEN, "block": cl.QUEUE_BLOCK,
                        "event": cl.REFUSED, "consumer": cl.QUEUE_CONSUMER, "data": data}),
            "not json"]


@contextmanager
def _store(tag: str, legacy: list[str] | None, new: list[str] | None):
    """A scratch trace root holding the clearance block's legacy and/or new-name file."""
    from cairn.machines.learning_block import learning_block as lb
    from cairn.devices.codemother.machines.clearance import clearance as cl
    from cairn.tools.scratch.scratch import scratch_dir
    root = scratch_dir(f"testing-clearance-store-{tag}-")
    old_env, original = os.environ.get("CAIRN_LB_TRACE_ROOT"), lb.legacy_trace_path
    os.environ["CAIRN_LB_TRACE_ROOT"] = str(root)
    if os.name == "nt":
        planted = root / "legacy-store.jsonl"
        lb.legacy_trace_path = (lambda b, root=None, *, holder=None:
                                planted if b == cl.QUEUE_BLOCK else original(b, root, holder=holder))
    try:
        if legacy is not None:
            lb.legacy_trace_path(cl.QUEUE_BLOCK).write_text("\n".join(legacy) + "\n", encoding="utf-8")
        if new is not None:
            lb.trace_path(cl.QUEUE_BLOCK, root=root).write_text("\n".join(new) + "\n", encoding="utf-8")
        yield cl
    finally:
        lb.legacy_trace_path = original
        if old_env is None:
            os.environ.pop("CAIRN_LB_TRACE_ROOT", None)
        else:
            os.environ["CAIRN_LB_TRACE_ROOT"] = old_env


def _shape(got: dict) -> tuple:
    return ([(a["event"], a["boat"]) for a in got["attempts"]], got["unreadable_lines"])


def test_either_store_counts_the_same():
    from cairn.devices.codemother.machines.clearance import clearance as cl
    lines = _seed(cl, "x")
    with _store("legacy", lines, None) as c:
        legacy = _shape(c.read_attempts())
    with _store("new", None, lines) as c:
        new = _shape(c.read_attempts())
    want = ([(cl.GRANTED, "b-x"), (cl.REFUSED, "b-x")], 1)
    assert new == want, f"new-name store miscounted: {new}, want {want}"
    assert legacy == new, f"legacy store {legacy} != new-name store {new}"


def test_both_stores_read_legacy_first():
    from cairn.devices.codemother.machines.clearance import clearance as cl
    with _store("both", _seed(cl, "old"), _seed(cl, "new")) as c:
        got = _shape(c.read_attempts())
    boats = [b for _, b in got[0]]
    assert boats == ["b-old", "b-old", "b-new", "b-new"], f"legacy must come first, then new: {boats}"
    assert got[1] == 2, f"one unreadable line in each file, counted: {got[1]}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
