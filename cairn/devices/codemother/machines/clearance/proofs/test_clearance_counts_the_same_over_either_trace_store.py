#!/usr/bin/env python3
"""Proof for ticket 30896d454418, clause 3: clearance's read_attempts counts the same over
a legacy-only trace store and a new-name-only one.

This is the clearance half of ticket a9709b744bf5's clause 4 ("every reader counts the
same over either store"). It used to sit in learning_block's trace proof, which imported
this unpublished machine; RULE 1 forbids that, so the half is proven here, at codemother's
own address. learning_block is a top-level machine, so importing it from here is legal.

The seeds are the harbor_master:clearance lines from that proof's _seed_lines, verbatim:
a granted record, a refused record, and one unparseable line. A legacy file is named with
a ':'. NTFS cannot hold one, so on Windows the legacy name is supplied through learning_block's
``legacy_trace_path`` seam (patched, then restored); on POSIX the real colon name is written.

    bin/cairn test cairn/devices/codemother/machines/clearance/proofs/test_clearance_counts_the_same_over_either_trace_store.py
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"30896d454418": {"3": "clearance_counts_the_same_over_either_store"}}

NOW = datetime(2026, 11, 12, 12, 0, 0, tzinfo=timezone.utc)
BLOCK = "harbor_master:clearance"


def _seed_lines(block: str) -> list[str]:
    return [json.dumps({"id": "a", "when": NOW.isoformat(), "block": block,
                        "event": "clearance_granted", "consumer": "training",
                        "data": {"actor": "cc", "boat": "b", "target": "t", "workflow": "w"}}),
            json.dumps({"id": "b", "when": NOW.isoformat(), "block": block,
                        "event": "clearance_refused", "consumer": "training",
                        "data": {"actor": "cc", "boat": "b", "target": "t", "workflow": "w"}}),
            "not json"]


def _count(cl) -> tuple[int, int]:
    a = cl.read_attempts()
    return (len(a["attempts"]), a["unreadable_lines"])


def clearance_counts_the_same_over_either_store() -> None:
    from cairn.machines.learning_block import learning_block as lb
    from cairn.devices.codemother.machines.clearance import clearance as cl
    from cairn.tools.scratch.scratch import scratch_dir
    body = "\n".join(_seed_lines(BLOCK)) + "\n"
    old_env = os.environ.get("CAIRN_LB_TRACE_ROOT")
    try:
        # legacy-only store
        root_a = scratch_dir("clearance-tracename-legacy-")
        os.environ["CAIRN_LB_TRACE_ROOT"] = str(root_a)
        if os.name == "nt":
            legacy = root_a / "legacy-store.jsonl"
            original = lb.legacy_trace_path
            lb.legacy_trace_path = lambda b, root=None: legacy if b == BLOCK else original(b, root)
            try:
                legacy.write_text(body, encoding="utf-8", newline="\n")
                legacy_counts = _count(cl)
            finally:
                lb.legacy_trace_path = original
        else:
            (root_a / f"{BLOCK}.jsonl").write_text(body, encoding="utf-8", newline="\n")
            legacy_counts = _count(cl)
        # new-name-only store
        root_b = scratch_dir("clearance-tracename-new-")
        os.environ["CAIRN_LB_TRACE_ROOT"] = str(root_b)
        lb.trace_path(BLOCK, root=root_b).write_text(body, encoding="utf-8", newline="\n")
        new_counts = _count(cl)
    finally:
        if old_env is None:
            os.environ.pop("CAIRN_LB_TRACE_ROOT", None)
        else:
            os.environ["CAIRN_LB_TRACE_ROOT"] = old_env
    assert new_counts == (2, 1), f"new-name store miscounted: {new_counts}"
    assert legacy_counts == (2, 1), f"legacy store miscounted: {legacy_counts}"
    assert legacy_counts == new_counts, f"legacy {legacy_counts} != new {new_counts}"


def main() -> int:
    try:
        clearance_counts_the_same_over_either_store()
        print("  green  clearance_counts_the_same_over_either_store")
        return 0
    except Exception as e:  # noqa: BLE001
        print(f"  RED    clearance_counts_the_same_over_either_store: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
