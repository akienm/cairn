"""Proof for ticket 5bcceb08973f — a sealed run's snapshot carries no waiting metric.

Measured 2026-11-10: ticket 98ab0e9db57f's tooth 7, sealed, read metrics totals of 66,405 migrated
rows per name against 22,135 in the dump. The live recorder had not drained since the migration,
and each sealed run's metrics collect over the snapshot wrote its copied records into the live
table. A dedupe removed 199,215 copies.

The snapshot is built over a TEMP instance root (the module's root is swapped for the tooth's
length), so nothing here reads or writes ~/.cairn.

Teeth, one per falsifier clause:

  1. a snapshot of a root whose holder's metrics recorder waits with a record keeps that
     recorder's directory and reads empty through metric.recorder; the source recorder still
     holds its record;
  2. the same snapshot copies the holder's other data recorders and its other files byte-equal;
  3. the tester's charter says the snapshot leaves waiting metrics behind.

    python3 cairn/devices/tester/proofs/test_a_sealed_snapshot_leaves_waiting_metrics_behind.py   # exit 0 = green
"""
from __future__ import annotations

import json
import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
CHARTER = REPO / "cairn" / "devices" / "tester" / "intention+why.json"

PROVES = {
    "5bcceb08973f": {
        "1": "the_snapshot_keeps_the_metrics_recorder_and_none_of_its_records",
        "2": "the_snapshot_copies_every_other_file_byte_equal",
        "3": "the_charter_says_the_snapshot_leaves_waiting_metrics_behind",
    },
}

FAILURES: list[str] = []
HOLDER = Path("devices") / "fixture_holder" / "0"


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1600]}", flush=True)
        FAILURES.append(name)


def _seed(root: Path) -> None:
    """A holder whose metrics recorder waits with a record, beside another recorder and files."""
    from cairn.tools.data_recorder.data_recorder import DataRecorder
    from cairn.tools.metric import metric
    holder = root / HOLDER
    metric.recorder(holder).write({"finding": "fixture_metric", "inspector_target": metric.RECORDER,
                                   "probe_source": "fixture_holder/0",
                                   "at": "2026-11-10T00:00:00+00:00", "value": 1.0})
    DataRecorder(holder / "tools" / "data_recorder" / "other",
                 expected_read_frequency_seconds=86400).write(
        {"finding": "kept", "inspector_target": "other", "probe_source": "fixture_holder/0"})
    (holder / "state.json").write_text('{"fixture": "kept byte-equal"}\n')
    (root / "logs").mkdir(parents=True, exist_ok=True)


def _files(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*") if p.is_file()}


def main() -> int:
    from cairn.devices.tester import isolation
    from cairn.tools.metric import metric
    from cairn.tools.scratch.scratch import scratch_dir

    root = Path(scratch_dir("5bcc-root-")) / "cairn"
    root.mkdir(parents=True)
    _seed(root)
    before = _files(root)
    saved_root, saved_pristine = isolation._INSTANCE_ROOT, dict(isolation._pristine)
    isolation._INSTANCE_ROOT = str(root)
    isolation._pristine.update(dir=None, top=None)
    snap = None
    try:
        snap = Path(isolation.pristine_snapshot())
    finally:
        isolation._INSTANCE_ROOT = saved_root
        made = isolation._pristine.get("dir")
        isolation._pristine.clear()
        isolation._pristine.update(saved_pristine)

    try:
        src_rec = metric.recorder(root / HOLDER)
        snap_rec = metric.recorder(snap / HOLDER)
        snap_dir = snap / HOLDER / "tools" / "data_recorder" / metric.RECORDER
        src_read, snap_read = src_rec.read(), snap_rec.read()
        _check("the_snapshot_keeps_the_metrics_recorder_and_none_of_its_records",
               snap_dir.is_dir() and snap_read == [] and len(src_read) == 1,
               f"snapshot dir={snap_dir.is_dir()} snapshot reads {snap_read!r}; source reads {src_read!r}")

        after = _files(snap)
        metrics_prefix = (HOLDER / "tools" / "data_recorder" / metric.RECORDER).as_posix() + "/"
        wanted = {k: v for k, v in before.items()
                  if not (k.startswith(metrics_prefix) and k.endswith("/" + "records.jsonl"))}
        missing = sorted(set(wanted) - set(after))
        differ = sorted(k for k in wanted if k in after and after[k] != wanted[k])
        extra = sorted(set(after) - set(wanted))
        _check("the_snapshot_copies_every_other_file_byte_equal",
               len(wanted) >= 3 and not missing and not differ and not extra,
               f"wanted={sorted(wanted)} missing={missing} differ={differ} extra={extra}")
    finally:
        if made:
            shutil.rmtree(Path(made).parent, ignore_errors=True)

    text = json.dumps(json.loads(CHARTER.read_text(encoding="utf-8")))
    _check("the_charter_says_the_snapshot_leaves_waiting_metrics_behind",
           "leaves waiting metrics behind" in text.lower() and "5bcceb08973f" in text,
           "the tester's charter does not say the snapshot leaves waiting metrics behind (ticket 5bcceb08973f)")

    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
