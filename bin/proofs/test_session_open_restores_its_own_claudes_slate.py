"""Proof: session open restores its own Claude's slate (ticket c3f5e1a0d924).

Measured 2026-11-12: akienasus_cc_0 opened on akiendelllinux's slate as if it were its
own, because bin/cmd/slate restored the newest slate of all. The reader now restores the
newest slate THIS Claude wrote and lists the other Claudes' newest slates. Each tooth runs
bin/cmd/slate --hook as a subprocess with the hook JSON on stdin, every store at a scratch
dir and the sessions dir at a scratch fixture, so nothing live is read.

    python3 bin/proofs/test_session_open_restores_its_own_claudes_slate.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

SLATE = REPO / "bin" / "cmd" / "slate"
TODAY = date.today().isoformat()

PROVES = {"c3f5e1a0d924": {
    "1": "test_a_named_claude_restores_its_own_slate_over_a_newer_one",
    "2": "test_the_other_claudes_newest_slate_is_listed",
    "3": "test_a_claude_with_no_slate_is_not_handed_another",
    "4": "test_a_legacy_cc_slate_of_this_session_is_this_claudes",
    "5": "test_no_identity_falls_back_and_says_so",
}}

SESSIONS = {
    "sid-asus": {"pid": 301, "sessionId": "sid-asus", "name": "akienasus_cc_0", "updatedAt": 1},
    "sid-linux": {"pid": 302, "sessionId": "sid-linux", "name": "akiendelllinux_cc_0", "updatedAt": 1},
    "sid-new": {"pid": 303, "sessionId": "sid-new", "name": "akiendell_cc_0", "updatedAt": 1},
    "sid-old": {"pid": 304, "sessionId": "sid-old", "name": "orchestrator", "updatedAt": 1},
}


def _world(*slates: dict) -> Path:
    root = scratch_dir("slate-own-claude-")
    (root / "slates").mkdir()
    (root / "sessions").mkdir()
    for rec in SESSIONS.values():
        (root / "sessions" / f"{rec['pid']}.json").write_text(json.dumps(rec))
    for s in slates:
        body = dict({"date": TODAY, "session": "", "host": "", "at_sea": f"{s['id']} at sea",
                     "next_direction": "next", "open_threads": []}, **s)
        (root / "slates" / f"{s['id']}.json").write_text(json.dumps(body))
    return root


def _open(root: Path, session_id: str | None) -> str:
    env = {k: v for k, v in os.environ.items()
           if k not in ("CLAUDE_PID", "CLAUDE_CODE_SESSION_ID")}
    env.update({
        "CAIRN_SLATES_DIR": str(root / "slates"),
        "CAIRN_CLAUDE_SESSIONS_DIR": str(root / "sessions"),
        "CAIRN_TROUBLES_DIR": str(root / "troubles"),
        "CAIRN_QUESTIONS_DIR": str(root / "questions"),
        "CAIRN_ADJUDICATIONS_DIR": str(root / "adjudications"),
        "CAIRN_SKILL_BERTHS": str(root / "berths"),
        "CAIRN_SKILL_REVIEWED_LOG": str(root / "reviewed.jsonl"),
        "CAIRN_LB_TRACE_ROOT": str(root / "traces"),
    })
    stdin = json.dumps({"session_id": session_id, "hook_event_name": "SessionStart"}) \
        if session_id else ""
    r = subprocess.run([sys.executable, str(SLATE), "--hook"], input=stdin,
                       capture_output=True, text=True, env=env, timeout=60)
    assert r.returncode == 0, r.stderr
    return json.loads(r.stdout)["hookSpecificOutput"]["additionalContext"]


def _two() -> Path:
    return _world(
        {"id": "asus-older", "author": "akienasus_cc_0", "host": "akienasus",
         "written_at": f"{TODAY}T08:00:00"},
        {"id": "linux-newer", "author": "akiendelllinux_cc_0", "host": "akiendelllinux",
         "written_at": f"{TODAY}T09:00:00"})


def test_a_named_claude_restores_its_own_slate_over_a_newer_one() -> None:
    banner = _open(_two(), "sid-asus")
    assert "SLATE  asus-older" in banner, banner
    assert "author: akienasus_cc_0 @ akienasus" in banner, banner
    assert "linux-newer at sea" not in banner, banner


def test_the_other_claudes_newest_slate_is_listed() -> None:
    banner = _open(_two(), "sid-asus")
    assert "OTHER CLAUDES" in banner, banner
    assert f"akiendelllinux_cc_0 @ akiendelllinux  {TODAY}T09:00:00  linux-newer" in banner, banner


def test_a_claude_with_no_slate_is_not_handed_another() -> None:
    banner = _open(_two(), "sid-new")
    assert "NO SLATE OF YOURS (akiendell_cc_0)" in banner, banner
    assert "SLATE  linux-newer" not in banner and "SLATE  asus-older" not in banner, banner
    assert "linux-newer" in banner and "asus-older" in banner, "the roster is missing"


def test_a_legacy_cc_slate_of_this_session_is_this_claudes() -> None:
    root = _world(
        {"id": "legacy-mine", "author": "CC", "session": "sid-old",
         "written_at": f"{TODAY}T07:00:00"},
        {"id": "legacy-other", "author": "CC", "session": "sid-someone",
         "written_at": f"{TODAY}T10:00:00"})
    banner = _open(root, "sid-old")
    assert "SLATE  legacy-mine" in banner, banner
    assert "legacy-other" not in banner, banner


def test_no_identity_falls_back_and_says_so() -> None:
    banner = _open(_two(), None)
    assert "SLATE  linux-newer" in banner, banner
    assert "could not tell which Claude this session is" in banner, banner


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
            print(f"  FAIL  {name}: {type(exc).__name__}: {str(exc)[:600]}")
            failed.append(name)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all 5 teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
