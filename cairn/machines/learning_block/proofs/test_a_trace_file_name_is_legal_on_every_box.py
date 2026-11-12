"""Proof for ticket a9709b744bf5 — a trace file's name is legal on every box and every
reader finds it.

The measured failure: ``write_trace("skill:intent", ...)`` named its file
``skill:intent.jsonl``; on NTFS ':' separates an alternate data stream, so every skill
door (/idea, /intent, /sorted ...) died with WinError 87 on akiendell.

Every tooth binds what the build ADDED at call time (never at import), so a hollow build
that lacks ``trace_path`` / ``trace_lines`` reds by tooth, not by an import crash.

A legacy file is named with a ':'. NTFS cannot hold one, so on Windows the legacy name
is supplied through the ``legacy_trace_path`` seam (a plain-named file) instead; on
POSIX the real colon name is written. The fold logic under test is the same.

    python3 cairn/machines/learning_block/proofs/test_a_trace_file_name_is_legal_on_every_box.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "a9709b744bf5": {
        "1": "a_colon_block_writes_a_legal_name_and_reads_back",
        "2": "read_returns_legacy_then_new",
        "3": "a_write_folds_the_legacy_file_and_retires_it",
        "4": "every_reader_counts_the_same_over_either_store",
        "5": "no_source_outside_learning_block_builds_a_trace_path_by_hand",
    },
}

NOW = datetime(2026, 11, 12, 12, 0, 0, tzinfo=timezone.utc)
RESERVED = set('<>:"|?*')
BLOCK = "skill:x"


def _lb():
    from cairn.machines.learning_block import learning_block as lb
    return lb


def _world(tag: str) -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir(f"tracename-{tag}-")


def _rec(block: str, event: str, n: int) -> str:
    return json.dumps({"id": f"r{n:02d}", "when": NOW.isoformat(), "block": block,
                       "event": event, "consumer": "training", "data": {"n": n}},
                      sort_keys=True)


@contextmanager
def _legacy(lb, root: Path, block: str, lines: list[str]):
    """Plant a legacy-named file holding ``lines``; yield its path."""
    if os.name == "nt":
        path = root / "legacy-store.jsonl"
        original = lb.legacy_trace_path
        lb.legacy_trace_path = lambda b, root=None: path if b == block else original(b, root)
        try:
            path.write_text("\n".join(lines) + "\n", encoding="utf-8")
            yield path
        finally:
            lb.legacy_trace_path = original
    else:
        path = root / f"{block}.jsonl"
        path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        yield path


# ── clause 1 ─────────────────────────────────────────────────────────────────

def a_colon_block_writes_a_legal_name_and_reads_back():
    lb = _lb()
    root = _world("c1")
    rec = lb.write_trace(BLOCK, "door_pass", "training", {"k": 1}, now=NOW, root=root)
    names = [p.name for p in root.iterdir()]
    assert names, "write_trace wrote no file"
    bad = [n for n in names if RESERVED & set(n)]
    assert not bad, f"file name carries a reserved character: {bad}"
    assert lb.trace_path(BLOCK, root=root).name in names, f"trace_path disagrees with disk: {names}"
    assert lb.read_trace(BLOCK, root=root) == [rec], "the record did not read back"


# ── clause 2 ─────────────────────────────────────────────────────────────────

def read_returns_legacy_then_new():
    lb = _lb()
    root = _world("c2")
    new = lb.trace_path(BLOCK, root=root)
    new.write_text(_rec(BLOCK, "door_pass", 2) + "\n", encoding="utf-8")
    with _legacy(lb, root, BLOCK, [_rec(BLOCK, "send_back", 1)]):
        got = [r["data"]["n"] for r in lb.read_trace(BLOCK, root=root)]
    assert got == [1, 2], f"legacy must come first, then new: {got}"


# ── clause 3 ─────────────────────────────────────────────────────────────────

def a_write_folds_the_legacy_file_and_retires_it():
    lb = _lb()
    root = _world("c3")
    with _legacy(lb, root, BLOCK, [_rec(BLOCK, "send_back", 1), _rec(BLOCK, "door_pass", 2)]) as legacy:
        lb.write_trace(BLOCK, "door_pass", "training", {"n": 3}, now=NOW, root=root)
        assert not legacy.exists(), "the legacy file must be retired by the write"
        got = [r["data"]["n"] for r in lb.read_trace(BLOCK, root=root)]
    assert got == [1, 2, 3], f"a fold lost or reordered a record: {got}"
    assert lb.trace_path(BLOCK, root=root).exists(), "the new-name file must hold the fold"


# ── clause 4 ─────────────────────────────────────────────────────────────────

def _counts():
    """Fire every reader over the CURRENT env root; return comparable counts."""
    from skills.intent.probes import intent_door_refusals as ip
    from skills.sorted.probes import sorted_door_refusals as sp
    from skills.saveslate.probes import slate_door_refusals as lp
    from cairn.devices.codemother.machines.clearance import clearance as cl
    out = {}
    for name, mod in (("intent", ip), ("sorted", sp), ("saveslate", lp)):
        s = mod.survey_the_firings()
        out[name] = (s["passes"], s["refusals"])
    a = cl.read_attempts()
    out["clearance"] = (len(a["attempts"]), a["unreadable_lines"])
    return out


def _seed_lines(block: str):
    if block == "harbor_master:clearance":
        return [json.dumps({"id": "a", "when": NOW.isoformat(), "block": block,
                            "event": "clearance_granted", "consumer": "training",
                            "data": {"actor": "cc", "boat": "b", "target": "t", "workflow": "w"}}),
                json.dumps({"id": "b", "when": NOW.isoformat(), "block": block,
                            "event": "clearance_refused", "consumer": "training",
                            "data": {"actor": "cc", "boat": "b", "target": "t", "workflow": "w"}}),
                "not json"]
    return [_rec(block, "door_pass", 1), _rec(block, "door_pass", 2), _rec(block, "send_back", 3)]


def every_reader_counts_the_same_over_either_store():
    lb = _lb()
    blocks = ["skill:intent", "skill:sorted", "skill:saveslate", "harbor_master:clearance"]
    old_env = os.environ.get("CAIRN_LB_TRACE_ROOT")
    try:
        # legacy-only store
        root_a = _world("c4a")
        os.environ["CAIRN_LB_TRACE_ROOT"] = str(root_a)
        if os.name == "nt":
            # one seam, many blocks: plant each legacy file and route by block name
            paths = {b: root_a / f"legacy-{i}.jsonl" for i, b in enumerate(blocks)}
            original = lb.legacy_trace_path
            lb.legacy_trace_path = lambda b, root=None: paths.get(b) or original(b, root)
            try:
                for b, p in paths.items():
                    p.write_text("\n".join(_seed_lines(b)) + "\n", encoding="utf-8")
                legacy_counts = _counts()
            finally:
                lb.legacy_trace_path = original
        else:
            for b in blocks:
                (root_a / f"{b}.jsonl").write_text("\n".join(_seed_lines(b)) + "\n", encoding="utf-8")
            legacy_counts = _counts()
        # new-name-only store
        root_b = _world("c4b")
        os.environ["CAIRN_LB_TRACE_ROOT"] = str(root_b)
        for b in blocks:
            lb.trace_path(b, root=root_b).write_text("\n".join(_seed_lines(b)) + "\n", encoding="utf-8")
        new_counts = _counts()
    finally:
        if old_env is None:
            os.environ.pop("CAIRN_LB_TRACE_ROOT", None)
        else:
            os.environ["CAIRN_LB_TRACE_ROOT"] = old_env
    assert new_counts["intent"] == (2, 1), f"new-name store miscounted: {new_counts}"
    assert new_counts["clearance"] == (2, 1), f"clearance miscounted: {new_counts}"
    assert legacy_counts == new_counts, f"legacy {legacy_counts} != new {new_counts}"


# ── clause 5 ─────────────────────────────────────────────────────────────────

def no_source_outside_learning_block_builds_a_trace_path_by_hand():
    out = subprocess.run(
        ["git", "grep", "-nE", r"""(QUEUE_BLOCK|block|skill:[a-z_]+)\}?\.jsonl|"skill:[a-z_]+\.jsonl""",
         "--", "*.py"],
        cwd=REPO, capture_output=True, text=True, encoding="utf-8").stdout.splitlines()
    hits = [l for l in out
            if "machines/learning_block/learning_block.py" not in l.replace("\\", "/")
            and "/proofs/" not in l.replace("\\", "/")]
    assert not hits, "hand-built trace paths remain:\n" + "\n".join(hits)


TEETH = [v for k, v in sorted(globals().items())
         if callable(v) and getattr(v, "__module__", None) == __name__
         and not k.startswith("_") and k in {n for d in PROVES.values() for n in d.values()}]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
