"""A TROUBLE'S LOCATION IS ITS LIVENESS (ticket 4ddc9df3369e).

Two state models meant guessing which vocabulary applied: CC once read the wrong field when
compiling the inbox. Location dissolves the guess. A trouble file at the top of the store is
live. Clearing moves it into the store's ``cleared/`` folder. The store is a logging artifact
(Akien, 2026-10-11: "trouble tickets are logging artifacts ... so they live in
.cairn/logs/cairn/troubletickets"), rooted at ``log_path('cairn', 0)/troubletickets`` so the
cairn device's 30-day sweep forgets it with the rest of the logs tree. Trouble tickets carry
the development-ticket fields under the ``trouble`` node class OPEN -> CLEARED: born red,
green when cleared (open-178c9f4b537c).

WHAT THIS PROVES, on scratch stores:
  (1) clearing moves the file out of the top of the store into ``cleared/``. live() is the
      top-level listing with no field check: a top-level file reads live whatever its
      standing says, and a malformed one too. A raise on a cleared identity brings the file
      back to the top and counts the recurrence. all() still reads both.
  (2) a raised trouble carries node_class, schema_version and a workflow_and_state that the
      development tickets' own parser reads with the cursor at OPEN, and at CLEARED once it
      clears. The trouble node class loads through the same class loader.
  (3) the default store is ``log_path('cairn', 0)/troubletickets`` under whatever instance
      root the caller names, and the cairn device's log sweep forgets an aged file in it.
  (4) migrate_from() moves an old store whole: live files to the top, CLEARED ones to
      ``cleared/``, nothing left behind and nothing lost.

Hollow: the field-filter, commons-rooted build reds every tooth.

    python3 cairn/devices/trouble/proofs/test_location_is_liveness.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {"4ddc9df3369e": {
    "1": "test_clearing_moves_the_file_into_cleared",
    "2": "test_a_trouble_carries_the_development_ticket_fields",
}}

IDENT = "a-proof-trouble-that-clears"


def _device(tmp: Path):
    from cairn.devices.trouble.trouble import TroubleDevice  # at call time (hollow-safe)
    dev = TroubleDevice(root=tmp)
    dev.set_diagnostic_receiver(None)  # keep this proof's trail out of the live logs tree
    return dev


def test_clearing_moves_the_file_into_cleared():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        dev = _device(tmp)
        dev.raise_trouble(IDENT, why="the proof raised it")
        assert (tmp / f"{IDENT}.json").is_file()
        dev.clear(IDENT, by="CC", what_changed="the proof cleared it")
        assert not (tmp / f"{IDENT}.json").exists(), "a cleared trouble still stands at the top"
        moved = tmp / "cleared" / f"{IDENT}.json"
        assert moved.is_file(), sorted(p.relative_to(tmp).as_posix() for p in tmp.rglob("*"))
        kept = json.loads(moved.read_text())
        assert kept["cleared_by"] and kept["cleared_by"][-1]["what_changed"] == "the proof cleared it"
        assert IDENT not in {t["id"] for t in dev.live()}
        assert IDENT in {t["id"] for t in dev.all()}, "all() lost the cleared trouble"


def test_live_is_the_top_level_listing():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        dev = _device(tmp)
        # A file at the top says CLEARED in its own field. Location decides, so it is live.
        (tmp / "a-proof-trouble-placed-by-hand.json").write_text(json.dumps(
            {"id": "a-proof-trouble-placed-by-hand", "standing": "CLEARED", "why": "placed"}))
        (tmp / "a-proof-trouble-malformed.json").write_text("{ not json")
        ids = {t.get("id") for t in dev.live()}
        assert "a-proof-trouble-placed-by-hand" in ids, ids
        assert len(dev.live()) == 2, dev.live()


def test_a_raise_on_a_cleared_trouble_brings_it_back():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        dev = _device(tmp)
        dev.raise_trouble(IDENT, why="the proof raised it")
        dev.clear(IDENT, by="CC", what_changed="the proof cleared it")
        assert (tmp / "cleared" / f"{IDENT}.json").is_file(), "the clear did not move it"
        dev.raise_trouble(IDENT, why="the proof raised it again")
        assert (tmp / f"{IDENT}.json").is_file(), "the recurrence did not come back to the top"
        assert not (tmp / "cleared" / f"{IDENT}.json").exists(), "the recurrence left a copy behind"
        back = json.loads((tmp / f"{IDENT}.json").read_text())
        assert back.get("prior_attempts", 0) >= 1, back
        assert back["cleared_by"], "the recurrence dropped the fix that did not hold"


def test_a_trouble_carries_the_development_ticket_fields():
    from cairn.tools.base.transitions import parse_workflow
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d)
        dev = _device(tmp)
        dev.raise_trouble(IDENT, why="the proof raised it")
        t = json.loads((tmp / f"{IDENT}.json").read_text())
        assert t.get("node_class") == "trouble", t.get("node_class")
        assert t.get("schema_version"), t
        w = parse_workflow(t["workflow_and_state"])
        assert (w.node_class, w.here) == ("trouble", "OPEN"), t["workflow_and_state"]
        dev.clear(IDENT, by="CC", what_changed="the proof cleared it")
        c = json.loads((tmp / "cleared" / f"{IDENT}.json").read_text())
        assert parse_workflow(c["workflow_and_state"]).here == "CLEARED", c["workflow_and_state"]


def test_the_trouble_node_class_loads():
    from cairn.tools.base.transitions import load_class_def
    cls = load_class_def("trouble")
    paths = [v["path"] for v in cls["workflow_versions"].values()]
    assert ["OPEN", "CLEARED"] in paths, paths


def test_the_default_store_is_under_the_instance_logs():
    from cairn.tools.base.address import log_path
    from cairn.devices.cairn.logs_sweep import sweep_logs
    from cairn.devices.trouble import trouble
    with tempfile.TemporaryDirectory() as d:
        roots = {"instance": Path(d)}
        store = trouble.store_root(roots)
        assert store == log_path("cairn", 0, roots) / "troubletickets", store
        assert trouble.store_root() == log_path("cairn", 0) / "troubletickets", trouble.store_root()
        dev = _device(store)
        dev.raise_trouble(IDENT, why="the proof raised it")
        dev.clear(IDENT, by="CC", what_changed="the proof cleared it")
        aged = store / "cleared" / f"{IDENT}.json"
        old = time.time() - 31 * 86400
        os.utime(aged, (old, old))
        sweep_logs(roots=roots)
        assert not aged.exists(), "the 30-day sweep did not reach the trouble store"


def test_migrate_from_moves_the_old_store_whole():
    with tempfile.TemporaryDirectory() as d:
        base = Path(d)
        old, new = base / "old", base / "new"
        old.mkdir()
        (old / "a-proof-live-one.json").write_text(json.dumps(
            {"id": "a-proof-live-one", "standing": "LIVE", "why": "still standing"}))
        (old / "a-proof-cleared-one.json").write_text(json.dumps(
            {"id": "a-proof-cleared-one", "standing": "CLEARED", "why": "fixed"}))
        (old / "a-proof-unreadable-one.json").write_text("{ not json")
        dev = _device(new)
        out = dev.migrate_from(old)
        assert sorted(p.name for p in old.glob("*.json")) == [], "the old store kept a file"
        assert sorted(p.name for p in new.glob("*.json")) == [
            "a-proof-live-one.json", "a-proof-unreadable-one.json"], sorted(new.rglob("*"))
        assert (new / "cleared" / "a-proof-cleared-one.json").is_file(), sorted(new.rglob("*"))
        assert out.get("live") == 2 and out.get("cleared") == 1, out


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
