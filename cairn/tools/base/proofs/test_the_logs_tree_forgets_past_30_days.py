"""Proof for ticket ff881672ac57 — the logs tree forgets everything past 30 days, in one deletion.

Akien, 2026-08-18, giving the reason for the one logs root: "easy to delete everything in the
logs tree over 30 days old in one go." Measured 2026-10-02: ~/.cairn/logs held 228531 files
(988M), 36719 of them older than 30 days, and nothing deleted there.

One tooth per numbered falsifier clause, all under a temp roots table (never the live tree):

  1. A FILE 31 DAYS OLD UNDER logs/ IS GONE after address.sweep_logs().
  2. A FILE 29 DAYS OLD STAYS.
  3. NOTHING OUTSIDE logs/ IS TOUCHED: an old sibling under the instance root stays, and an
     old file reached through a symlink inside logs/ that points outside it stays.
  4. A DIRECTORY LEFT EMPTY BELOW logs/ IS REMOVED, and logs/ itself stays.
  5. THE COUNT IS TRUE: the returned 'deleted' equals the files that left disk.

    python3 cairn/tools/base/proofs/test_the_logs_tree_forgets_past_30_days.py
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import address
from cairn.tools.scratch.scratch import scratch_dir

PROVES = {"ff881672ac57": {
    "1": "a_file_31_days_old_is_gone",
    "2": "a_file_29_days_old_stays",
    "3": "nothing_outside_logs_is_touched",
    "4": "an_emptied_directory_goes_and_logs_stays",
    "5": "the_deleted_count_is_true",
}}

DAY = 86400
PASS = 0
FAIL = 0


def _file(path: Path, age_days: float) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("testing-ff881672ac57\n", encoding="utf-8")
    t = time.time() - age_days * DAY
    os.utime(path, (t, t))
    return path


def _rig():
    """A temp instance root: logs/ with old, young and soon-empty files, plus an outside."""
    tmp = scratch_dir("testing-ff881672ac57-")
    table = {**address.ROOTS, "instance": tmp}
    logs = tmp / "logs"
    rig = {
        "table": table, "logs": logs,
        "old": _file(logs / "dev_a" / "0" / "old.json", 31),
        "young": _file(logs / "dev_a" / "0" / "young.json", 29),
        "lonely": _file(logs / "dev_b" / "0" / "deep" / "only.json", 40),
        "outside_sibling": _file(tmp / "devices" / "dev_a" / "0" / "state.json", 90),
        "outside_target": _file(tmp / "elsewhere" / "kept.json", 90),
    }
    link = logs / "dev_a" / "0" / "link"
    link.symlink_to(rig["outside_target"].parent, target_is_directory=True)
    return rig


def _sweep(rig):
    before = sum(1 for p in rig["logs"].rglob("*") if p.is_file() and not p.is_symlink())
    result = address.sweep_logs(older_than_days=30, roots=rig["table"])
    after = sum(1 for p in rig["logs"].rglob("*") if p.is_file() and not p.is_symlink())
    return result, before - after


def a_file_31_days_old_is_gone():
    rig = _rig()
    _sweep(rig)
    assert not rig["old"].exists(), f"{rig['old']} is 31 days old and survived the sweep"


def a_file_29_days_old_stays():
    rig = _rig()
    _sweep(rig)
    assert rig["young"].exists(), f"{rig['young']} is 29 days old and was deleted"


def nothing_outside_logs_is_touched():
    rig = _rig()
    _sweep(rig)
    assert rig["outside_sibling"].exists(), "an old file outside logs/ was deleted"
    assert rig["outside_target"].exists(), "the sweep followed a symlink out of logs/"


def an_emptied_directory_goes_and_logs_stays():
    rig = _rig()
    _sweep(rig)
    assert not (rig["logs"] / "dev_b").exists(), "a directory left empty below logs/ survived"
    assert rig["logs"].is_dir(), "the sweep removed logs/ itself"


def the_deleted_count_is_true():
    rig = _rig()
    result, gone = _sweep(rig)
    assert result.get("deleted") == gone, f"returned {result!r}, but {gone} file(s) left disk"


TEETH = [a_file_31_days_old_is_gone, a_file_29_days_old_stays, nothing_outside_logs_is_touched,
         an_emptied_directory_goes_and_logs_stays, the_deleted_count_is_true]


def _tooth(fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {fn.__name__}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {fn.__name__}")


if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
