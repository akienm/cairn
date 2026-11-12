"""Proof: a slate names the Claude that wrote it (ticket b2e4dafc5813).

Four Claudes share one commons, and every slate said author "CC": akienasus_cc_0 opened
on 2026-11-12 on akiendelllinux's slate as if it were its own. The door now stamps the
writing session's name and box, both minted by the door. Every fire runs with a scratch
slates dir, berths, traces and sessions dir, so the live store and the live repos are
never touched (the slates_dir seam keeps the door's auto-commit off).

    python3 skills/saveslate/proofs/test_a_slate_names_the_claude_that_wrote_it.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "skills" / "saveslate"))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"b2e4dafc5813": {
    "1": "test_a_named_session_stamps_its_name_and_box",
    "2": "test_a_session_with_no_record_reads_cc_and_still_the_box",
    "3": "test_a_packet_carrying_author_or_host_is_refused",
}}

HOST = os.uname().nodename
HEADS = {"cairn": "aaa111", "CairnCommons": "bbb222"}


def _good(slate_id: str) -> dict:
    return {"slate_id": slate_id, "at_sea": "fixture voyage", "next_direction": "fixture next",
            "open_threads": ["one thread"],
            "instruments_read": {"git_heads": dict(HEADS)},
            "bullets": [{"text": "fixture close", "stratum": "code"}],
            "exit": "routed_forward"}


def _roots() -> dict:
    tmp = scratch_dir("slate-author-")
    (tmp / "slates").mkdir()
    sessions = tmp / "sessions"
    sessions.mkdir()
    (sessions / "4242.json").write_text(json.dumps(
        {"pid": 4242, "sessionId": "sid-asus", "name": "akienasus_cc_0", "updatedAt": 1}))
    return dict(heads=HEADS, slates_dir=tmp / "slates", berths=tmp / "berths",
                trace_root=tmp / "traces", sessions_dir=sessions)


def test_a_named_session_stamps_its_name_and_box() -> None:
    import door
    r = door.fire(_good("2026-11-12-fixture-named"), session="sid-asus", **_roots())
    rec = json.loads(Path(r["slate"]).read_text())
    assert rec["author"] == "akienasus_cc_0" and rec["host"] == HOST, rec
    assert rec["session"] == "sid-asus", rec


def test_a_session_with_no_record_reads_cc_and_still_the_box() -> None:
    import door
    r = door.fire(_good("2026-11-12-fixture-unnamed"), session="sid-nobody", **_roots())
    rec = json.loads(Path(r["slate"]).read_text())
    assert rec["author"] == "CC" and rec["host"] == HOST, rec


def test_a_packet_carrying_author_or_host_is_refused() -> None:
    import door
    from cairn.machines.learning_block.learning_block import DoorRefused
    for key, value in (("author", "akiendelllinux_cc_0"), ("host", "elsewhere")):
        roots = _roots()
        sid = f"2026-11-12-fixture-{key}"
        try:
            door.fire(dict(_good(sid), **{key: value}), session="sid-asus", **roots)
        except DoorRefused as exc:
            fields = [l["field"] for l in (getattr(exc, "lacks", None) or [])]
            assert any(key in f for f in fields), (key, fields)
        else:
            raise AssertionError(f"a packet carrying {key} was not refused")
        assert not (roots["slates_dir"] / f"{sid}.json").exists(), f"{key}: a slate landed"


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            failed.append(name)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all 3 teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
