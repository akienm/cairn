"""Proof: every data_recorder declares when it was started, last read, and how often it
expects reading — and the at-rest probe reds the undeclared and the overdue.

Ticket a4c2be029f49. Five teeth, each a clause a hollow build could pass without it:

  1. started is stamped on the FIRST write and never at construction, and does not move
  2. drain drains and hold holds under stamp_read; last_read moves under both
  3. a frozen clock at started + 2*frequency raises exactly recorder-read-overdue-<dev>-0-inbound
     and the emission lands under instance/logs/data_recorder/0/
  4. a frozen clock at started + frequency/2 raises nothing
  5. an undeclared frequency raises exactly recorder-declares-no-reader-<dev>-0-inbound
     and never the overdue identity; the reconcile carries the complete observed set

A scratch roots table keeps the glob and the raiser off the live tree. No proof reads
the live commons or instance-space.
"""
from __future__ import annotations

import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.data_recorder.data_recorder import DataRecorder, READING_FILE  # noqa: E402
from cairn.tools.data_recorder.probes import reading_is_declared_and_current as probe  # noqa: E402

T0 = datetime(2026, 9, 18, 8, 0, 0, tzinfo=timezone.utc)
RECORD = {"finding": "a finding", "inspector_target": "x", "probe_source": "y"}


def _world(tmp: Path) -> dict:
    world = tmp / "world"
    return {k: world for k in ("repo", "commons", "instance")}


def _recorder(roots: dict, device: str, name: str = "inbound", **settings) -> DataRecorder:
    base = roots["instance"] / "devices" / device / "0" / "tools" / "data_recorder" / name
    return DataRecorder(base, **settings)


def _emissions(roots: dict) -> list[dict]:
    home = roots["instance"] / "logs" / "data_recorder" / "0"
    if not home.is_dir():
        return []
    out = []
    for p in sorted(home.glob("*.json")):
        out.append(json.loads(p.read_text(encoding="utf-8")))
    return out


def test_started_is_stamped_on_the_first_write_and_never_moves():
    with tempfile.TemporaryDirectory() as tmp:
        roots = _world(Path(tmp))
        r = _recorder(roots, "alpha", expected_read_frequency_seconds=60, on_read="drain")
        assert r.reading() is None, "construction wrote a declaration"
        assert not r.reading_path.exists()
        r.write(dict(RECORD), now=T0)
        d = r.reading()
        assert d == {"started": T0.isoformat(), "last_read": None,
                     "expected_read_frequency_seconds": 60, "on_read": "drain"}, d
        assert (r.reading_path.parent / READING_FILE).is_file()
        r.write(dict(RECORD), now=T0 + timedelta(seconds=30))
        assert r.reading()["started"] == T0.isoformat(), "started moved on a second write"
        # bad declarations are refused at construction, not silently defaulted
        for bad in ({"on_read": "sometimes"}, {"expected_read_frequency_seconds": 0},
                    {"expected_read_frequency_seconds": True}):
            try:
                _recorder(roots, "beta", **bad)
            except ValueError:
                pass
            else:
                raise AssertionError("accepted %r" % bad)


def test_drain_drains_and_hold_holds_under_stamp_read():
    with tempfile.TemporaryDirectory() as tmp:
        roots = _world(Path(tmp))
        drain = _recorder(roots, "alpha", expected_read_frequency_seconds=60, on_read="drain")
        a = drain.write(dict(RECORD), now=T0)
        b = drain.write(dict(RECORD), now=T0)
        t1 = T0 + timedelta(seconds=10)
        assert drain.stamp_read([a], now=t1) == 1
        assert [x["id"] for x in drain.read()] == [b], "drain removed the wrong ids"
        assert drain.reading()["last_read"] == t1.isoformat()
        assert drain.reading()["started"] == T0.isoformat()

        hold = _recorder(roots, "gamma", expected_read_frequency_seconds=120, on_read="hold")
        c = hold.write(dict(RECORD), now=T0)
        assert hold.stamp_read([c], now=t1) == 0
        assert [x["id"] for x in hold.read()] == [c], "hold removed a record"
        assert hold.reading()["last_read"] == t1.isoformat()

        # a stamp with no ids under drain moves last_read and removes nothing
        assert drain.stamp_read(now=t1 + timedelta(seconds=1)) == 0
        assert [x["id"] for x in drain.read()] == [b]


def test_overdue_raises_exactly_the_overdue_identity_and_lands_in_the_log_home():
    with tempfile.TemporaryDirectory() as tmp:
        roots = _world(Path(tmp))
        r = _recorder(roots, "alpha", expected_read_frequency_seconds=60, on_read="drain")
        r.write(dict(RECORD), now=T0)
        c = probe.report(T0 + timedelta(seconds=120), roots=roots)
        assert c["recorders"] == 1, c
        assert c["raised"] == ["recorder-read-overdue-alpha-0-inbound"], c
        ems = _emissions(roots)
        kinds = [(e.get("event") or e.get("kind") or e.get("verb"), json.dumps(e)) for e in ems]
        assert any("recorder-read-overdue-alpha-0-inbound" in k[1] for k in kinds), \
            "no emission carrying the identity under instance/logs/data_recorder/0: %r" % (ems,)
        assert any("reconcile_troubles" in k[1] for k in kinds), "no reconcile emitted"
        # a read inside the window clears: the next census observes nothing under the scope
        r.stamp_read(now=T0 + timedelta(seconds=120))
        c2 = probe.report(T0 + timedelta(seconds=150), roots=roots)
        assert c2["raised"] == [], c2
        assert c2["current"] == ["alpha-0-inbound"], c2


def test_inside_the_declared_frequency_raises_nothing():
    with tempfile.TemporaryDirectory() as tmp:
        roots = _world(Path(tmp))
        r = _recorder(roots, "alpha", expected_read_frequency_seconds=60, on_read="drain")
        r.write(dict(RECORD), now=T0)
        c = probe.report(T0 + timedelta(seconds=30), roots=roots)
        assert c["raised"] == [], c
        assert c["current"] == ["alpha-0-inbound"], c
        ems = _emissions(roots)
        assert not any("raise_trouble" in json.dumps(e) and "recorder-" in json.dumps(e)
                       and "reconcile" not in json.dumps(e) for e in ems), ems
        # the trigger itself, through the beat's shape: no line crossed
        assert probe.census(T0 + timedelta(seconds=30), roots=roots)["troubles"] == {}


def test_undeclared_raises_no_reader_and_never_overdue():
    with tempfile.TemporaryDirectory() as tmp:
        roots = _world(Path(tmp))
        undeclared = _recorder(roots, "delta")          # the holder declared nothing
        undeclared.write(dict(RECORD), now=T0)
        assert undeclared.reading()["expected_read_frequency_seconds"] is None
        declared = _recorder(roots, "alpha", expected_read_frequency_seconds=60, on_read="hold")
        declared.write(dict(RECORD), now=T0)
        far = T0 + timedelta(days=30)
        c = probe.report(far, roots=roots)
        assert c["recorders"] == 2, c
        assert c["raised"] == ["recorder-declares-no-reader-delta-0-inbound",
                               "recorder-read-overdue-alpha-0-inbound"], c
        assert not any(i.startswith("recorder-read-overdue-delta") for i in c["raised"])
        # a recorder with records but no reading.json at all is also undeclared
        legacy = roots["instance"] / "devices" / "eps" / "0" / "tools" / "data_recorder" / "inbound"
        legacy.mkdir(parents=True)
        (legacy / "records.jsonl").write_text('{"id": "x"}\n', encoding="utf-8")
        c = probe.census(far, roots=roots)
        assert "recorder-declares-no-reader-eps-0-inbound" in c["troubles"], c
        assert c["troubles"]["recorder-declares-no-reader-eps-0-inbound"]["why"] == "no reading.json"
        # the reconcile carries the complete observed set under the scope
        ems = _emissions(roots)
        recs = [e for e in ems if "reconcile_troubles" in json.dumps(e)]
        assert recs, ems
        last = json.dumps(recs[-1])
        assert "recorder-declares-no-reader-delta-0-inbound" in last and \
               "recorder-read-overdue-alpha-0-inbound" in last, last


TEETH = [
    test_started_is_stamped_on_the_first_write_and_never_moves,
    test_drain_drains_and_hold_holds_under_stamp_read,
    test_overdue_raises_exactly_the_overdue_identity_and_lands_in_the_log_home,
    test_inside_the_declared_frequency_raises_nothing,
    test_undeclared_raises_no_reader_and_never_overdue,
]

if __name__ == "__main__":
    failed = 0
    for t in TEETH:
        try:
            t()
            print("  pass  %s" % t.__name__)
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print("  FAIL  %s: %r" % (t.__name__, exc))
    print("%d teeth: %d pass, %d fail" % (len(TEETH), len(TEETH) - failed, failed))
    sys.exit(1 if failed else 0)
