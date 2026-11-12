"""Proof: a session reads which Claude it is (ticket a1d3c9e4b702).

Four Claudes share one commons, and a record that says only "CC" cannot tell them apart.
claude_identity.who() reads Claude Code's own session record and names the session. Every
tooth runs over a scratch sessions dir; the live ~/.claude/sessions is never read. The
subject is imported inside each tooth, so a hollow build reds per tooth.

    python3 cairn/tools/base/proofs/test_a_session_reads_which_claude_it_is.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"a1d3c9e4b702": {
    "1": "test_a_session_id_names_its_session",
    "2": "test_no_id_falls_to_the_record_of_claude_pid",
    "3": "test_nothing_found_is_a_nameless_session_never_a_raise",
    "4": "test_two_records_of_one_session_read_the_newer",
}}

HOST = os.uname().nodename


def _dir(*records, torn: bool = False) -> Path:
    d = scratch_dir("claude-identity-")
    for r in records:
        (d / f"{r['pid']}.json").write_text(json.dumps(r))
    if torn:
        (d / "999.json").write_text('{"pid": 999, "name": "half')
    return d


def _rec(pid, sid, name, former=(), updated=1):
    return {"pid": pid, "sessionId": sid, "name": name, "updatedAt": updated,
            "formerNames": [{"name": f, "until": 1} for f in former]}


def test_a_session_id_names_its_session() -> None:
    from cairn.tools.base.claude_identity import who
    d = _dir(_rec(100, "sid-orch", "orchestrator", former=["akiendelllinux_cc_RESCUE"]),
             _rec(200, "sid-asus", "akienasus_cc_0"))
    w = who("sid-orch", sessions_dir=d, environ={})
    assert w == {"name": "orchestrator", "former_names": ["akiendelllinux_cc_RESCUE"],
                 "host": HOST, "session": "sid-orch"}, w


def test_no_id_falls_to_the_record_of_claude_pid() -> None:
    from cairn.tools.base.claude_identity import who
    d = _dir(_rec(100, "sid-orch", "orchestrator"), _rec(200, "sid-asus", "akienasus_cc_0"))
    w = who(None, sessions_dir=d, environ={"CLAUDE_PID": "200"})
    assert w["name"] == "akienasus_cc_0" and w["session"] == "sid-asus", w


def test_nothing_found_is_a_nameless_session_never_a_raise() -> None:
    from cairn.tools.base.claude_identity import who
    d = _dir(_rec(100, "sid-orch", "orchestrator"), torn=True)
    w = who("sid-unknown", sessions_dir=d, environ={})
    assert w == {"name": "", "former_names": [], "host": HOST, "session": "sid-unknown"}, w
    gone = who("sid-orch", sessions_dir=d / "absent", environ={})
    assert gone["name"] == "" and gone["host"] == HOST, gone


def test_two_records_of_one_session_read_the_newer() -> None:
    from cairn.tools.base.claude_identity import who
    d = _dir(_rec(100, "sid-x", "old-name", updated=5), _rec(101, "sid-x", "new-name", updated=9))
    assert who("sid-x", sessions_dir=d, environ={})["name"] == "new-name"


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            failed.append(name)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all 4 teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
