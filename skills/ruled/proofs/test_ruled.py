"""Proof for skills/ruled — Akien's RULED marker fires the ruling door.

Teeth a hollow build could not pass:

  - /ruled <valid-id> CONFIRMS THE PACKET and records the invocation as evidence.
    A door.py that never calls ruling.confirm trips this.
  - /ruled <bogus-id> REFUSES LOUDLY, naming the store searched. A door.py that
    silently exits 0 on a miss trips this.
  - Bare /ruled LISTS OPEN UNMARKED RULINGS. A door.py that always demands an id
    trips this.
  - THE EVIDENCE IS THE INVOCATION ITSELF — recorded verbatim, not an empty string
    or CC's prose. A door.py that passes a blank evidence trips this.

Self-contained (a synthetic world in a temp dir) and self-cleaning.

    PYTHONPATH=. python3 -m pytest skills/ruled/proofs/test_ruled.py -v
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.ruling import ruling
from skills.ruled import door


def _world(d: str) -> str:
    os.makedirs(os.path.join(d, "CairnCommons", "decisions"))
    os.makedirs(os.path.join(d, "cairn", "cairn", "tools"))
    Path(d, "cairn", "cairn", "tools", "something.py").write_text("# exists\n")
    return d


def _ruling_packet(ruling_id: str = "2026-08-15-test-ruling") -> dict:
    return {
        "id": ruling_id,
        "kind": "ruling",
        "date": "2026-08-15",
        "ruled_by": "Akien",
        "recorded_by": "CC",
        "the_ruling_verbatim": ["RULED — this is a test ruling."],
        "now_the_spec_says": "Test ruling for the /ruled skill proof.",
        "what_dies": [],
        "what_conforms": ["cairn/cairn/tools/something.py"],
    }


def _seed_ruling(world: str, ruling_id: str = "2026-08-15-test-ruling") -> str:
    packet = _ruling_packet(ruling_id)
    path = ruling.open_ruling(packet, roots_parent=world)
    return path


def test_confirm_records_evidence():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        ruling_path = _seed_ruling(d)
        ruling_id = "2026-08-15-test-ruling"

        evidence = f"cairn ruled {ruling_id}"
        result_path = ruling.confirm(ruling_id, evidence, roots_parent=d)

        record = json.load(open(result_path, encoding="utf-8"))
        assert record["confirmed"] is True, "packet must be confirmed after /ruled <id>"
        reaffs = record.get("reaffirmations", [])
        assert any(evidence in r for r in reaffs) or record.get("confirmation_verbatim") == evidence, (
            f"evidence must be recorded verbatim; got confirmation_verbatim={record.get('confirmation_verbatim')!r}, "
            f"reaffirmations={reaffs!r}")


def test_confirm_verify_green_ruled():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        _seed_ruling(d)
        ruling_id = "2026-08-15-test-ruling"

        ruling.confirm(ruling_id, f"cairn ruled {ruling_id}", roots_parent=d)

        Path(d, "cairn", "cairn", "tools", "something.py").write_text("# conformed\n")

        records = ruling.load_all(roots_parent=d)
        record = [r for r in records if r.get("id") == ruling_id][0]
        verdict = ruling.verify(record, roots_parent=d)
        assert verdict["green"], f"verify must be green after confirm; failures: {verdict['failures']}"
        assert verdict["ruled"], "verdict must show ruled=True (RULED marker is in the verbatim)"


def test_refuse_on_no_match(capsys):
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        os.environ["CAIRN_ROOTS_PARENT"] = d
        try:
            exit_code = door._refuse("bogus-nonexistent-id-12345")
        finally:
            del os.environ["CAIRN_ROOTS_PARENT"]

        assert exit_code != 0, "/ruled <no-match> must exit non-zero"
        captured = capsys.readouterr()
        assert "bogus-nonexistent-id-12345" in captured.err, (
            "refusal must name the id that was searched for")
        assert "decisions" in captured.err.lower() or "store" in captured.err.lower(), (
            f"refusal must name the store searched; got stderr: {captured.err!r}")


def test_list_open_shows_unmarked(capsys):
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        packet = _ruling_packet()
        packet["the_ruling_verbatim"] = ["this is a test ruling without RULED marker."]
        ruling.open_ruling(packet, roots_parent=d)

        os.environ["CAIRN_ROOTS_PARENT"] = d
        try:
            exit_code = door._list_open()
        finally:
            del os.environ["CAIRN_ROOTS_PARENT"]

        assert exit_code == 0, "bare /ruled must exit 0"
        captured = capsys.readouterr()
        assert "2026-08-15-test-ruling" in captured.out, (
            f"bare /ruled must list open rulings; got: {captured.out!r}")


def test_main_dispatches_correctly():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        _seed_ruling(d)

        os.environ["CAIRN_ROOTS_PARENT"] = d
        try:
            exit_confirm = door.main(["2026-08-15-test-ruling"])
            assert exit_confirm == 0, "main(<valid-id>) must exit 0"

            exit_refuse = door.main(["definitely-not-a-ruling"])
            assert exit_refuse != 0, "main(<no-match>) must exit non-zero"

            exit_list = door.main([])
            assert exit_list == 0, "main([]) must exit 0 (listing mode)"
        finally:
            del os.environ["CAIRN_ROOTS_PARENT"]


if __name__ == "__main__":
    import pytest
    sys.exit(pytest.main([__file__, "-v"]))
