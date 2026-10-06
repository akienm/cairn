"""runs — what a tester run owns, keyed by the test id it minted (ticket bf3c16162827).

Akien, 2026-10-05 (/home/akien/.cairn/foreground-decisions.md 8d, 8e): the tester "can throw away
(to logging) most of what it does. all we need are the results", a returned testing artifact
completes its test ("the tester would see that it's a returning message, from test abcdefg"),
and the tester kills what the run started.

One id per run, ``test-<12 hex>``, handed to the subject as ``CAIRN_TESTER_TEST_ID``. A proof
marks what it sends with ``testing_mark.mark(<that id>)``. Everything else hangs off the id:

  - the run's log directory, ``address.log_path('tester')/runs/<id>/`` — full stdout and
    stderr, and every return the shim took for it. The logs tree is forgotten after 30 days by
    the cairn device's sleep work, so nothing here needs a sweep of its own;
  - the processes the run started: anything whose environment still carries the id after the
    subject has exited. The environment survives setsid and a timed-out parent, which a
    process-group kill does not;
  - the systemd user units the run started: any service the manager records as handed the id.
    /proc cannot see these in two cases (measured 2026-10-05, found by f04d5ef26a48's seal): a
    unit that FAILED has no process left, and inside the seal's user namespace
    /proc/<pid>/environ of every process outside it reads "Permission denied". The manager's
    own record (``systemctl --user show -p Environment``) reads through the seal, so the run
    asks it, stops what carries the id and clears the failed ones.
"""
from __future__ import annotations

import json
import os
import re
import signal
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.address import log_path

ENV = "CAIRN_TESTER_TEST_ID"
_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
_GRACE_S = 2.0


def mint_test_id() -> str:
    return "test-" + os.urandom(6).hex()


def run_dir(test: str) -> Path:
    """The run's log directory. A test id is a path segment, so a malformed one is refused loudly."""
    if not isinstance(test, str) or not _ID.match(test):
        raise ValueError(f"a test id is one path segment of [A-Za-z0-9._-]; got {test!r}")
    return log_path("tester") / "runs" / test


def record_return(envelope: dict, test: str) -> dict:
    """Append one returned artifact to its test's run log; returns the line written."""
    body = envelope.get("body") or {}
    line = {"at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "test": test,
            "from": envelope.get("sender"), "return_id": envelope.get("id"),
            "reply_to": envelope.get("reply_to"), "original_verb": body.get("original_verb"),
            "original_addressee": body.get("original_addressee")}
    d = run_dir(test)
    d.mkdir(parents=True, exist_ok=True)
    with open(d / "returns.jsonl", "a", encoding="utf-8") as fh:
        fh.write(json.dumps(line, sort_keys=True) + "\n")
    return line


def returns_of(test: str) -> list[dict]:
    """Every return the shim has taken for ``test`` so far, oldest first."""
    path = run_dir(test) / "returns.jsonl"
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return []
    return [json.loads(x) for x in text.splitlines() if x.strip()]


def keep_output(test: str, stdout: str, stderr: str) -> str:
    """The run's whole output, to logging. Returns the directory it went to."""
    d = run_dir(test)
    d.mkdir(parents=True, exist_ok=True)
    (d / "stdout.txt").write_text(stdout or "", encoding="utf-8")
    (d / "stderr.txt").write_text(stderr or "", encoding="utf-8")
    return str(d)


def _carrying(test: str) -> list[dict]:
    tag = f"{ENV}={test}".encode()
    me = os.getpid()
    found = []
    for d in Path("/proc").iterdir():
        if not d.name.isdigit() or int(d.name) == me:
            continue
        try:
            if tag not in (d / "environ").read_bytes().split(b"\0"):
                continue
            cmd = (d / "cmdline").read_bytes().replace(b"\0", b" ").decode(errors="replace").strip()
            state = (d / "stat").read_text().rsplit(")", 1)[1].split()[0]
        except (OSError, IndexError):
            continue          # gone, or another user's: either way not ours to kill
        if state != "Z":
            found.append({"pid": int(d.name), "cmdline": cmd[:200]})
    return found


def _systemctl(*argv: str) -> subprocess.CompletedProcess:
    return subprocess.run(["systemctl", "--user", *argv], capture_output=True, text=True, timeout=30)


def _units_carrying(test: str) -> list[str]:
    """Every service the user manager records as handed the run's id, failed ones included."""
    listed = _systemctl("list-units", "--all", "--no-legend", "--plain", "--type=service")
    names = [line.split()[0] for line in listed.stdout.splitlines() if line.strip()]
    if not names:
        return []
    shown = _systemctl("show", "-p", "Id", "-p", "Environment", "--", *names)
    tag, found, unit = f"{ENV}={test}", [], None
    for line in shown.stdout.splitlines():
        if line.startswith("Id="):
            unit = line[3:]
        elif line.startswith("Environment=") and unit and tag in line[12:].split():
            found.append(unit)
    return found


def stop_its_units(test: str) -> list[dict]:
    """Stop every user service carrying the run's id and clear it from the manager. A manager
    that cannot be asked is named in what comes back, never passed over in silence (Law 7)."""
    try:
        units = _units_carrying(test)
    except (OSError, subprocess.TimeoutExpired) as exc:
        return [{"unit": None, "signal": f"none: the user manager could not be asked: {exc}"}]
    out = []
    for unit in units:
        stop = _systemctl("stop", unit)
        _systemctl("reset-failed", unit)
        out.append({"unit": unit, "signal": "stop" if stop.returncode == 0
                    else f"stop failed: {stop.stderr.strip()[:200]}"})
    return out


def kill_what_it_started(test: str) -> list[dict]:
    """Stop the user units carrying the run's id, then SIGTERM every live process still carrying
    it, SIGKILL what outlives the grace. Returns what was found, each with the signal that ended
    it (or the error that stopped us)."""
    units = stop_its_units(test)
    found = _carrying(test)
    for p in found:
        try:
            os.kill(p["pid"], signal.SIGTERM)
            p["signal"] = "TERM"
        except OSError as exc:
            p["signal"] = f"none: {exc.strerror}"
    deadline = time.time() + _GRACE_S
    left = {p["pid"] for p in found}
    while left and time.time() < deadline:
        time.sleep(0.05)
        left &= {p["pid"] for p in _carrying(test)}
    for p in found:
        if p["pid"] in left:
            try:
                os.kill(p["pid"], signal.SIGKILL)
                p["signal"] = "KILL"
            except OSError as exc:
                p["signal"] = f"KILL failed: {exc.strerror}"
    return units + found
