"""PROOF — the cairn device forgets its logs past 30 days when a sleep cycle it runs closes.

Ticket ff881672ac57 (the-logs-tree-forgets-past-30-days). Akien placed the cleanup in the
cairn device's sleep cycle (open-9d9c0b1ac3a9), so the sweep, its caller and this proof are
all inside the cairn device (RULE 1). One test per falsifier clause:

  (1) a file under logs/ 31 days old does not survive sweep_logs();
  (2) a file 29 days old is kept;
  (3) nothing outside logs/ is deleted or changed — a sibling under the instance root, and a
      file outside logs/ reached through an old symlink inside it (the link goes, the target
      stays byte-identical);
  (4) a directory left empty below logs/ is removed, and logs/ itself is not;
  (5) the returned 'deleted' count equals the number of files that left disk;
  (6) a CairnDevice whose sleep rotation closes (``sleep-cycle`` act mint over an empty roster)
      leaves no 31-day file under its roots' logs/, and its verb result carries 'logs' counts.

What a hollow build cannot pass (Law 8): with logs_sweep.py absent every key fails at import;
a sweep that judges by the target's mtime or follows the link fails (3); one that forgets the
empty directories, or removes the root, fails (4); a device.py that never calls the sweep on
the close fails (6).

THE WORLD IS A TEMP ROOTS TABLE. No live log is touched. Key 6's bus is a stand-in that only
records posts: over an empty roster token.py calls nothing on the bus but the close announce,
so no bus row is written anywhere.

    python3 cairn/devices/cairn/proofs/test_the_logs_tree_forgets_past_30_days.py   # exit 0 = green
"""

from __future__ import annotations

import os
import sys
import tempfile
import time
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "ff881672ac57": {
        "1": "test_a_file_past_30_days_is_deleted",
        "2": "test_a_file_inside_30_days_is_kept",
        "3": "test_nothing_outside_logs_is_touched",
        "4": "test_empty_directories_go_and_the_root_stays",
        "5": "test_the_deleted_count_is_what_left_disk",
        "6": "test_the_cairn_device_sweeps_when_its_sleep_cycle_closes",
    },
}

DAY = 86400
NOW = time.time()


def _world(tmp: Path) -> tuple[dict, Path]:
    roots = {"repo": tmp / "repo", "commons": tmp / "commons", "instance": tmp / "instance"}
    logs = roots["instance"] / "logs"
    logs.mkdir(parents=True)
    return roots, logs


def _plant(path: Path, age_days: float, text: str = "x") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
    t = NOW - age_days * DAY
    os.utime(path, (t, t))
    return path


def _age_link(link: Path, age_days: float) -> None:
    t = NOW - age_days * DAY
    os.utime(link, (t, t), follow_symlinks=False)


def _sweep(roots):
    from cairn.devices.cairn.logs_sweep import sweep_logs
    return sweep_logs(older_than_days=30, roots=roots, now=NOW)


def test_a_file_past_30_days_is_deleted():
    with tempfile.TemporaryDirectory(prefix="proof-logs-sweep-") as d:
        roots, logs = _world(Path(d))
        old = _plant(logs / "fx_dev" / "0" / "old.jsonl", 31)
        _sweep(roots)
        assert not old.exists(), "a 31-day-old log survived the sweep"


def test_a_file_inside_30_days_is_kept():
    with tempfile.TemporaryDirectory(prefix="proof-logs-sweep-") as d:
        roots, logs = _world(Path(d))
        young = _plant(logs / "fx_dev" / "0" / "young.jsonl", 29)
        result = _sweep(roots)
        assert young.is_file(), "a 29-day-old log was deleted"
        assert result["kept"] == 1, result


def test_nothing_outside_logs_is_touched():
    with tempfile.TemporaryDirectory(prefix="proof-logs-sweep-") as d:
        roots, logs = _world(Path(d))
        sibling = _plant(roots["instance"] / "other.txt", 400, "sibling")
        target = _plant(Path(d) / "outside" / "target.txt", 400, "target")
        link = logs / "fx_dev" / "0" / "link.txt"
        link.parent.mkdir(parents=True)
        link.symlink_to(target)
        _age_link(link, 31)
        before = (sibling.read_bytes(), target.read_bytes(), target.stat().st_mtime)
        _sweep(roots)
        assert not link.is_symlink(), "an old symlink inside logs/ survived the sweep"
        assert (sibling.read_bytes(), target.read_bytes(), target.stat().st_mtime) == before, (
            "something outside logs/ changed")
        # and a young link to an old target stays: the link is judged by its OWN mtime
        # (its emptied folder went with it, so it is made again)
        link.parent.mkdir(parents=True, exist_ok=True)
        link.symlink_to(target)
        _age_link(link, 1)
        _sweep(roots)
        assert link.is_symlink(), "a 1-day-old link was deleted for its target's age"


def test_empty_directories_go_and_the_root_stays():
    with tempfile.TemporaryDirectory(prefix="proof-logs-sweep-") as d:
        roots, logs = _world(Path(d))
        _plant(logs / "gone_dev" / "0" / "deep" / "old.jsonl", 31)
        _plant(logs / "kept_dev" / "0" / "young.jsonl", 2)
        (logs / "already_empty").mkdir()
        _sweep(roots)
        assert not (logs / "gone_dev").exists(), "a directory left empty below logs/ survived"
        assert not (logs / "already_empty").exists(), "an empty directory below logs/ survived"
        assert (logs / "kept_dev" / "0" / "young.jsonl").is_file()
        assert logs.is_dir(), "the sweep removed logs/ itself"
        # a tree that empties completely still keeps its root
        _plant(logs / "kept_dev" / "0" / "young.jsonl", 31)
        _sweep(roots)
        assert logs.is_dir() and not any(logs.iterdir()), sorted(logs.rglob("*"))


def test_the_deleted_count_is_what_left_disk():
    with tempfile.TemporaryDirectory(prefix="proof-logs-sweep-") as d:
        roots, logs = _world(Path(d))
        for i in range(7):
            _plant(logs / f"dev{i % 3}" / "0" / f"old{i}.jsonl", 31 + i, "abc")
        for i in range(4):
            _plant(logs / f"dev{i % 2}" / "0" / f"young{i}.jsonl", 5)
        before = {p for p in logs.rglob("*") if p.is_file()}
        result = _sweep(roots)
        after = {p for p in logs.rglob("*") if p.is_file()}
        assert result["deleted"] == len(before - after) == 7, (result, len(before - after))
        assert result["bytes"] == 7 * 3, result
        assert result["kept"] == len(after) == 4, result


class _PostOnlyBus:
    """Records posts; reads nothing. Over an empty roster token.py only posts the close."""

    def __init__(self) -> None:
        self.posts = []

    def post(self, **kw):
        self.posts.append(kw)
        return {"id": f"proof-logs-sweep-{len(self.posts)}"}

    def read(self, **kw):
        return []


def test_the_cairn_device_sweeps_when_its_sleep_cycle_closes():
    from cairn.devices.cairn.device import CairnDevice
    with tempfile.TemporaryDirectory(prefix="proof-logs-sweep-") as d:
        roots, logs = _world(Path(d))
        roster_root = Path(d) / "empty_roster"
        roster_root.mkdir()
        old = _plant(logs / "fx_dev" / "0" / "old.jsonl", 31)
        young = _plant(logs / "fx_dev" / "0" / "young.jsonl", 3)
        bus = _PostOnlyBus()
        device = CairnDevice(bus=bus, roots=roots, roster_root=roster_root)
        device.set_diagnostic_receiver(None)   # the logs_swept record is held, not written live
        handler = device.declared_verbs()["sleep-cycle"]
        result = handler({"verb": "sleep-cycle", "body": {"act": "mint"}})
        assert result["cycle"]["closed_at"] is not None, result
        assert not old.exists(), "the sleep cycle closed and a 31-day-old log survived"
        assert young.is_file()
        assert result.get("logs", {}).get("deleted") == 1, result
        swept = [r for r in device.held_diagnostics() if r.get("gate") == "logs_swept"]
        assert len(swept) == 1 and swept[0].get("values", {}).get("deleted") == 1, swept
        # 'show' does not sweep
        late = _plant(logs / "fx_dev" / "0" / "late.jsonl", 40)
        shown = handler({"verb": "sleep-cycle", "body": {"act": "show"}})
        assert late.is_file() and "logs" not in shown, shown


def main() -> int:
    failed = 0
    for name in [n for n in PROVES["ff881672ac57"].values()]:
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("GREEN" if not failed else f"RED ({failed} failed)")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
