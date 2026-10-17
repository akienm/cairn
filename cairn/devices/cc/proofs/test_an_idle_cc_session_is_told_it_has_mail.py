"""PROOF — when mail lands while CC's session is idle, the shim tells it so (ticket 1e2640bad4dd).

The mailcheck hook announces mail only inside an active turn, so mail delivered to an idle CC
waited unread. The build has deliver() call CCShim.poke_if_idle(), which reads Claude Code's own
session records for the session named <hostname>_cc_0 and, when it is idle, launches one detached
headless `claude -p` whose only act is SendMessage "you've got mail". Every decision is ledgered.

What a hollow build cannot pass (Law 8):
  - No poke: deliver() never runs the stand-in claude and writes no 'poked' line, so
    an_idle_session_is_poked_once and a_consume_rearms_the_poke read zero runs.
  - A poke without the guards: the busy tooth or the already-poked tooth sees a run.
  - A shim that names its host through socket: an_idle_session_is_poked_once sees the import.

Every sandboxed tooth runs over a temporary directory: shim._INSTANCE_ROOT, _MAIL_DIR, _LEDGER
and _SESSIONS_DIR point inside it, and _CLAUDE_CMD is a stand-in script that appends its argv to
a file, so no real claude is ever launched. The live tooth reads the real ledger and asserts an
invariant over it, never a snapshot (clause 4).

    python3 cairn/devices/cc/proofs/test_an_idle_cc_session_is_told_it_has_mail.py   # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
import time
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "1e2640bad4dd": {
        "1": "test_an_idle_session_is_poked_once",
        "2": "test_a_busy_session_is_not_poked",
        "3": "test_a_second_delivery_before_consume_is_not_poked",
        "4": "test_live_mail_to_an_idle_session_is_consumed_within_60s",
    },
}


@contextmanager
def _sandbox():
    """Point the shim at a temporary instance, sessions dir and stand-in claude; restore after."""
    from cairn.devices.cc import shim
    names = ("_INSTANCE_ROOT", "_MAIL_DIR", "_LEDGER", "_SESSIONS_DIR", "_CLAUDE_CMD")
    saved = {n: getattr(shim, n) for n in names}
    with tempfile.TemporaryDirectory(prefix="cc-idle-poke-proof-") as tmp:
        root = Path(tmp)
        runs = root / "claude_runs.jsonl"
        stand_in = root / "claude"
        stand_in.write_text("#!/usr/bin/env python3\nimport json, sys\n"
                            f"open({str(runs)!r}, 'a').write(json.dumps(sys.argv[1:]) + '\\n')\n")
        stand_in.chmod(0o755)
        shim._INSTANCE_ROOT = root / "instance"
        shim._MAIL_DIR = shim._INSTANCE_ROOT / "mail"
        shim._LEDGER = shim._INSTANCE_ROOT / "mail_ledger.jsonl"
        shim._SESSIONS_DIR = root / "sessions"
        shim._SESSIONS_DIR.mkdir()
        shim._CLAUDE_CMD = [str(stand_in)]
        try:
            yield shim, root, runs
        finally:
            for n, v in saved.items():
                setattr(shim, n, v)


def _session(shim, status: str, name: str | None = None, pid: int = 4242) -> None:
    rec = {"pid": pid, "name": name or shim.CCShim.poke_target(), "status": status}
    (shim._SESSIONS_DIR / f"{pid}.json").write_text(json.dumps(rec))


def _runs(runs: Path, want: int) -> list[list[str]]:
    """The stand-in is detached, so wait briefly for it to have written what it will."""
    deadline = time.monotonic() + 5
    while True:
        got = [json.loads(x) for x in runs.read_text().splitlines()] if runs.exists() else []
        if len(got) >= want or time.monotonic() > deadline:
            if want == 0:
                time.sleep(0.5)
                got = [json.loads(x) for x in runs.read_text().splitlines()] if runs.exists() else []
            return got
        time.sleep(0.05)


def _events(shim) -> list[dict]:
    return [json.loads(x) for x in Path(shim._LEDGER).read_text().splitlines() if x.strip()]


def _names_its_host_without_dialing(shim):
    """The poke's target is the name superclaude gives CC, read by os.uname(), and the shim
    imports no dialing module: socket, urllib and requests belong to the sole paths only
    (build_inspector sole_path_holds). The first build named the host by socket.gethostname()
    and PROVED refused it."""
    import ast
    import os
    tree = ast.parse(Path(shim.__file__).read_text())
    dialing = {"socket", "urllib", "requests"}
    imported = {a.name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    imported |= {(n.module or "").split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    assert not (imported & dialing), f"the shim imports {sorted(imported & dialing)}"
    assert shim.CCShim.poke_target() == f"{os.uname().nodename}_cc_0", shim.CCShim.poke_target()


# --- teeth ------------------------------------------------------------------

def test_an_idle_session_is_poked_once():
    """Clause (1): idle → a 'poked' line and exactly one launch, naming the target, by haiku."""
    with _sandbox() as (shim, root, runs):
        _session(shim, "idle")
        out = shim.CCShim().deliver({"from": "proof", "body": "hello"})
        assert out["persisted"] is True, out
        got = _runs(runs, 1)
        assert len(got) == 1, f"expected exactly one launch, got {got}"
        argv = got[0]
        _names_its_host_without_dialing(shim)
        target = shim.CCShim.poke_target()
        assert "-p" in argv and argv[argv.index("--model") + 1] == "haiku", argv
        assert target in argv[-1] and "SendMessage" in argv[-1], argv[-1]
        assert "hello" not in argv[-1], "the content must never ride the poke"
        kinds = [e["event"] for e in _events(shim)]
        assert kinds == ["delivered", "poked"], kinds


def test_a_busy_session_is_not_poked():
    """Clause (2): busy → a 'not-poked: busy' line and no launch."""
    with _sandbox() as (shim, root, runs):
        _session(shim, "busy")
        shim.CCShim().deliver({"from": "proof"})
        assert _runs(runs, 0) == []
        last = _events(shim)[-1]
        assert last["event"] == "not-poked" and last["reason"] == "busy", last


def test_a_second_delivery_before_consume_is_not_poked():
    """Clause (3): a second delivery before any 'consumed' line → no second launch."""
    with _sandbox() as (shim, root, runs):
        _session(shim, "idle")
        shim.CCShim().deliver({"from": "proof"})
        shim.CCShim().deliver({"from": "proof"})
        assert len(_runs(runs, 2)) == 1
        last = _events(shim)[-1]
        assert last["event"] == "not-poked" and last["reason"] == "already poked", last


def test_a_consume_rearms_the_poke():
    """After the session reads its mail, the next delivery to an idle session pokes again."""
    with _sandbox() as (shim, root, runs):
        _session(shim, "idle")
        shim.CCShim().deliver({"from": "proof"})
        shim.CCShim.consume_mail()
        shim.CCShim().deliver({"from": "proof"})
        assert len(_runs(runs, 2)) == 2
        assert [e["event"] for e in _events(shim)].count("poked") == 2


def test_no_session_or_garbage_still_persists():
    """No named session, a torn record, or two sessions sharing the name → no launch; mail stands."""
    with _sandbox() as (shim, root, runs):
        (shim._SESSIONS_DIR / "1.json").write_text("{torn")
        _session(shim, "idle", name="someone_else", pid=2)
        out = shim.CCShim().deliver({"from": "proof"})
        assert out["persisted"] is True and Path(out["path"]).exists()
        assert _events(shim)[-1]["reason"].startswith("no session named"), _events(shim)[-1]
        _session(shim, "idle", pid=3)
        _session(shim, "idle", pid=4)
        shim.CCShim().deliver({"from": "proof"})
        assert _events(shim)[-1]["reason"].startswith("two sessions are named")
        shim._SESSIONS_DIR = root / "absent"
        shim.CCShim().deliver({"from": "proof"})
        assert _runs(runs, 0) == []


def test_mail_outside_the_instance_pokes_nobody():
    """A proof that moves only _MAIL_DIR (as the older cc proofs do) launches nothing."""
    with _sandbox() as (shim, root, runs):
        _session(shim, "idle")
        shim._MAIL_DIR = root / "elsewhere"
        shim.CCShim().deliver({"from": "proof"})
        assert _runs(runs, 0) == []


def test_live_mail_to_an_idle_session_is_consumed_within_60s():
    """Clause (4), live: the real ledger holds a delivered → poked → consumed run, and the
    consume lands within 60 s of the delivery it answers. Invariant over live data."""
    from cairn.devices.cc import shim
    ledger = Path(shim._LEDGER)
    assert ledger.exists(), f"no live ledger at {ledger}: no mail has reached the live shim"
    events = [json.loads(x) for x in ledger.read_text().splitlines() if x.strip()]
    for i, e in enumerate(events):
        if e.get("event") != "poked":
            continue
        delivered = next((d for d in reversed(events[:i]) if d.get("event") == "delivered"), None)
        consumed = next((c for c in events[i + 1:] if c.get("event") == "consumed"), None)
        if delivered and consumed:
            dt = (datetime.fromisoformat(consumed["at"]) - datetime.fromisoformat(delivered["at"]))
            if dt.total_seconds() <= 60:
                return
    raise AssertionError("no live poke was followed by a consume within 60 s of its delivery")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
