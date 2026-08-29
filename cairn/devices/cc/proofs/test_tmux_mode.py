"""Proofs for superclaude tmux mode — teeth a hollow build could not pass.

Three concerns: (1) mail persistence and retrieval, (2) the mailcheck hook,
(3) idle detection guards injection.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


@pytest.fixture
def mail_dir():
    d = tempfile.mkdtemp(prefix="cairn-cc-mail-test-")
    yield Path(d)
    shutil.rmtree(d)


# ── mail persistence ────────────────────────────────────────────────────


def test_deliver_persists_mail_to_disk(mail_dir):
    from cairn.devices.cc.shim import CCShim

    with patch("cairn.devices.cc.shim._MAIL_DIR", mail_dir):
        shim = CCShim()
        result = shim.deliver({
            "from": "tester", "to": "cc", "channel": "personal",
            "body": {"text": "hello"}, "why": "proof",
        })
    assert result["persisted"] is True
    files = list(mail_dir.glob("msg-*.json"))
    assert len(files) == 1
    rec = json.loads(files[0].read_text())
    assert rec["envelope"]["from"] == "tester"
    assert rec["envelope"]["body"]["text"] == "hello"


def test_pending_mail_reads_what_deliver_wrote(mail_dir):
    from cairn.devices.cc.shim import CCShim

    with patch("cairn.devices.cc.shim._MAIL_DIR", mail_dir):
        shim = CCShim()
        shim.deliver({
            "from": "probe", "to": "cc", "channel": "personal",
            "body": {"finding": "something"}, "why": "proof",
        })
    pending = CCShim.pending_mail(mail_dir=mail_dir)
    assert len(pending) == 1
    assert pending[0]["envelope"]["from"] == "probe"


def test_consume_mail_reads_and_removes(mail_dir):
    from cairn.devices.cc.shim import CCShim

    with patch("cairn.devices.cc.shim._MAIL_DIR", mail_dir):
        shim = CCShim()
        shim.deliver({
            "from": "bus", "to": "cc", "channel": "personal",
            "body": {"msg": "work"}, "why": "proof",
        })
    consumed = CCShim.consume_mail(mail_dir=mail_dir)
    assert len(consumed) == 1
    assert consumed[0]["envelope"]["from"] == "bus"
    assert CCShim.pending_mail(mail_dir=mail_dir) == []


def test_pending_mail_returns_empty_for_no_dir():
    from cairn.devices.cc.shim import CCShim

    result = CCShim.pending_mail(mail_dir="/tmp/nonexistent-cc-mail-dir")
    assert result == []


# ── mailcheck hook ──────────────────────────────────────────────────────


@pytest.fixture
def fake_home():
    d = tempfile.mkdtemp(prefix="cairn-cc-fakehome-")
    yield Path(d)
    shutil.rmtree(d)


def test_mailcheck_outputs_notification_when_mail_waiting(fake_home):
    msg = {"id": "msg-test", "received": "2026-08-28T00:00:00",
           "envelope": {"from": "tester", "body": {"text": "hi"}}}
    cairn_mail = fake_home / ".cairn" / "devices" / "cc" / "0" / "mail"
    cairn_mail.mkdir(parents=True, exist_ok=True)
    (cairn_mail / "msg-test.json").write_text(json.dumps(msg))

    result = subprocess.run(
        [sys.executable, "bin/cmd/mailcheck"],
        capture_output=True, text=True,
        env={**os.environ, "HOME": str(fake_home)},
        cwd=os.getcwd(),
    )
    assert "waiting message" in result.stdout
    assert "tester" in result.stdout


def test_mailcheck_silent_when_no_mail(fake_home):
    result = subprocess.run(
        [sys.executable, "bin/cmd/mailcheck"],
        capture_output=True, text=True,
        env={**os.environ, "HOME": str(fake_home)},
        cwd=os.getcwd(),
    )
    assert result.stdout.strip() == ""


# ── idle detection ──────────────────────────────────────────────────────


def test_is_idle_returns_false_when_no_tmux_session():
    from cairn.devices.cc.shim import CCShim

    assert CCShim.is_idle("nonexistent-session-xyz") is False


def test_inject_refuses_when_not_idle():
    from cairn.devices.cc.shim import CCShim

    with patch.object(CCShim, "is_idle", return_value=False):
        result = CCShim.inject_command("test-session", "/sail next")
    assert result["injected"] is False
    assert "not idle" in result["reason"]


def test_inject_succeeds_when_idle():
    from cairn.devices.cc.shim import CCShim

    mock_run_result = type("R", (), {"returncode": 0, "stdout": "", "stderr": ""})()
    with patch.object(CCShim, "is_idle", return_value=True), \
         patch("cairn.devices.cc.shim.subprocess.run", return_value=mock_run_result):
        result = CCShim.inject_command("test-session", "/sail next")
    assert result["injected"] is True
    assert result["command"] == "/sail next"


# ── launcher flag ───────────────────────────────────────────────────────


def test_launcher_dry_run_shows_tmux_when_flag_set():
    result = subprocess.run(
        ["bash", "launchers/superclaude", "--tmux", "--dry-run"],
        capture_output=True, text=True, cwd=os.getcwd(),
    )
    assert "tmux: on" in result.stdout
    assert "tmux new-session" in result.stdout


def test_launcher_dry_run_no_tmux_by_default():
    result = subprocess.run(
        ["bash", "launchers/superclaude", "--dry-run"],
        capture_output=True, text=True, cwd=os.getcwd(),
    )
    assert "tmux: off" in result.stdout
    assert "tmux new-session" not in result.stdout


def test_launcher_env_var_enables_tmux():
    result = subprocess.run(
        ["bash", "launchers/superclaude", "--dry-run"],
        capture_output=True, text=True, cwd=os.getcwd(),
        env={**os.environ, "CAIRN_SUPERCLAUDE_TMUX": "1"},
    )
    assert "tmux: on" in result.stdout
