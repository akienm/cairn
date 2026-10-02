"""Proofs for cairn/devices/cairn/machines/ground_loop/cli.py — the operator's interface.

Each subcommand composes with an existing mechanism and adds no new state.
The proofs verify composition, not mechanism (those are proved elsewhere).
"""

import os
import sys
import tempfile

from cairn.tools.scratch.scratch import scratch_dir
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from cairn.devices.cairn.machines.ground_loop.cli import _status, _stop, _start, main
from cairn.devices.cairn.machines.ground_loop.liveness import write_liveness

PROVES = {"bae622881f03": {"6": "status prints each trigger the record lists and the changed count"}}

PASS = 0
FAIL = 0


def _tmp_instance():
    d = scratch_dir("gl_cli_")
    flags = Path(d) / "flags"
    flags.mkdir()
    (flags / "COMMAND_EXIT.flag").touch()
    (flags / "COMMAND_DO_NOT_RESTART.flag").touch()
    now = datetime.now(timezone.utc).astimezone()
    write_liveness(now, {"beats": 42, "subscribers": ["bus"]}, os.getpid(), Path(d))
    return d


def test_status_reads_liveness():
    global PASS, FAIL
    d = _tmp_instance()
    try:
        with patch("cairn.devices.cairn.machines.ground_loop.cli._home", return_value=Path(d)):
            rc = _status()
        if rc == 0:
            PASS += 1
            print("PASS: status returns 0 and reads liveness")
        else:
            FAIL += 1
            print(f"FAIL: status returned {rc}")
    finally:
        import shutil
        shutil.rmtree(d)


def test_status_prints_triggers_and_changed():
    """The heartbeat's record (ticket bae622881f03) carries the triggers called this beat and
    the own files changed since start; status prints one line per trigger and the count."""
    global PASS, FAIL
    import contextlib, io, shutil
    d = scratch_dir("gl_cli_triggers_")
    now = datetime.now(timezone.utc).astimezone()
    state = {"beats": 3, "changed": ["/x/a.py"], "triggers": [
        {"device_id": "alpha", "level": "class", "ok": True, "result": {}},
        {"device_id": "broken", "level": "instance", "ok": False, "error": "RuntimeError: boom"}]}
    write_liveness(now, state, os.getpid(), Path(d))
    out = io.StringIO()
    try:
        with patch("cairn.devices.cairn.machines.ground_loop.cli._home", return_value=Path(d)), \
                contextlib.redirect_stdout(out):
            _status()
        text = out.getvalue()
        want = ["trigger:     alpha (class) ok",
                "trigger:     broken (instance) FAILED RuntimeError: boom",
                "changed:     1 own file(s) since start"]
        missing = [w for w in want if w not in text]
        if not missing:
            PASS += 1
            print("PASS: status prints each trigger the record lists and the changed count")
        else:
            FAIL += 1
            print(f"FAIL: status prints each trigger the record lists and the changed count")
            print(f"      missing {missing}")
    finally:
        shutil.rmtree(d)


def test_stop_copies_flag():
    global PASS, FAIL
    d = _tmp_instance()
    try:
        signal = Path(d) / "COMMAND_EXIT.flag"
        assert not signal.exists(), "signal should not exist before stop"
        with patch("cairn.devices.cairn.machines.ground_loop.cli._home", return_value=Path(d)):
            rc = _stop()
        if rc == 0 and signal.exists():
            PASS += 1
            print("PASS: stop copies COMMAND_EXIT.flag to instance folder")
        else:
            FAIL += 1
            print(f"FAIL: stop rc={rc}, signal exists={signal.exists()}")
    finally:
        import shutil
        shutil.rmtree(d)


def test_stop_idempotent():
    global PASS, FAIL
    d = _tmp_instance()
    try:
        signal = Path(d) / "COMMAND_EXIT.flag"
        signal.touch()
        with patch("cairn.devices.cairn.machines.ground_loop.cli._home", return_value=Path(d)):
            rc = _stop()
        if rc == 0:
            PASS += 1
            print("PASS: stop is idempotent (already signaled)")
        else:
            FAIL += 1
            print(f"FAIL: stop rc={rc} when already signaled")
    finally:
        import shutil
        shutil.rmtree(d)


def test_help_output():
    global PASS, FAIL
    rc = main(["help"])
    if rc == 0:
        PASS += 1
        print("PASS: help returns 0")
    else:
        FAIL += 1
        print(f"FAIL: help returned {rc}")


def test_unknown_command():
    global PASS, FAIL
    rc = main(["bogus"])
    if rc == 1:
        PASS += 1
        print("PASS: unknown command returns 1")
    else:
        FAIL += 1
        print(f"FAIL: unknown command returned {rc}")


def test_dispatcher_exists_and_is_executable():
    global PASS, FAIL
    # proofs/ -> ground_loop/ -> machines/ -> cairn(device)/ -> devices/ -> cairn(pkg)/ -> repo root
    script = Path(__file__).resolve().parents[6] / "bin" / "cmd" / "groundloop"
    if script.exists() and os.access(str(script), os.X_OK):
        PASS += 1
        print("PASS: bin/cmd/groundloop exists and is executable")
    else:
        FAIL += 1
        print(f"FAIL: bin/cmd/groundloop exists={script.exists()}, "
              f"executable={os.access(str(script), os.X_OK) if script.exists() else 'n/a'}")


if __name__ == "__main__":
    test_status_reads_liveness()
    test_status_prints_triggers_and_changed()
    test_stop_copies_flag()
    test_stop_idempotent()
    test_help_output()
    test_unknown_command()
    test_dispatcher_exists_and_is_executable()
    print(f"\n{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
