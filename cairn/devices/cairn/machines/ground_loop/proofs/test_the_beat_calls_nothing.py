"""Teeth for ticket 164da559823d — nothing fires on the heartbeat but its listeners.

MEASURED 2026-10-02: the beat called every ``groundloop/pulse.py`` (nine tracked, eight after
e0f318650123 deletes codemother's), most of them firing probes through
``cairn/tools/base/beat_probes.py``. Akien's ruling (2026-09-30): nothing fires on the
heartbeat but the messaging, and a probe fires on its event, never the beat. The build deletes
every pulse file, beat_probes.py, and the beat's ``pulse_sites``/``Triggers`` call, so the beat
writes its record and calls nothing. Probes stay where they stand (open-291189a9766a): wiring
each to its receiver and event is 835b5736bf2b's work.

Clause keys follow the falsifier's (N) markers. Teeth (1), (3) and (4) read the tracked tree
by ``git ls-files``, a census of the corpus, never an import of another component (RULE 1).
Tooth (2) runs the loop in a subprocess over a temp instance root, so the live loop and its
record are never touched. Tooth (5) reads the live heartbeat, and tooth (6) asks the post-commit
fan-out's own CLI whether codemother's subscriber is installed.
"""
from __future__ import annotations

import inspect
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "164da559823d": {
        "1": "test_no_pulse_file_and_no_beat_probes_are_tracked",
        "2": "test_the_beat_calls_no_pulse_and_records_no_triggers",
        "3": "test_the_build_deleted_no_probe",
        "4": "test_nothing_tracked_reaches_the_pulse_machinery",
        "5": "test_the_live_heartbeat_beats_without_triggers",
        "6": "test_codemother_hears_the_commit_through_the_fanout",
    },
}

_TICKET = "164da559823d"
# Exactly the heartbeat's keys: bae622881f03's four plus a808e21d646f's ``devices`` (the rack's
# ids, its clause 6, proved in test_heartbeat.py). Exact, so a "triggers" key reads red.
_STATE_KEYS = {"beats", "started", "recorded_mtimes", "current_mtimes", "changed", "devices"}
_PULSE_MACHINERY = ("beat_probes", "pulse_sites", "Triggers", "load_pulse")


def _git(*args: str) -> str:
    out = subprocess.run(["git", "-C", str(_REPO), *args], capture_output=True, text=True,
                         timeout=60)
    assert out.returncode == 0, f"git {args}: {out.stderr.strip()}"
    return out.stdout


def _tracked(*pathspecs: str) -> list[str]:
    return [p for p in _git("ls-files", "-z", "--", *pathspecs).split("\0") if p]


def test_no_pulse_file_and_no_beat_probes_are_tracked():
    pulses = _tracked("*/groundloop/pulse.py")
    assert pulses == [], f"pulse files still tracked: {pulses}"
    beat = _tracked("cairn/tools/base/beat_probes.py")
    assert beat == [], "cairn/tools/base/beat_probes.py is still tracked"
    assert not (_REPO / "cairn/tools/base/beat_probes.py").exists(), \
        "beat_probes.py is untracked but still on disk"


def test_the_beat_calls_no_pulse_and_records_no_triggers():
    td = Path(str(scratch_dir("beat-calls-nothing-proof-")))
    marker = td / "a-pulse-was-called.txt"
    pulse = (f"from pathlib import Path\n"
             f"def on_pulse(now, context=None):\n"
             f"    Path({str(marker)!r}).write_text('called')\n"
             f"    return {{'called': True}}\n")
    class_root = td / "class"
    for d in (class_root / "devices" / "alpha" / "groundloop",
              td / "inst" / "devices" / "beta" / "0" / "groundloop"):
        d.mkdir(parents=True)
        (d / "pulse.py").write_text(pulse, encoding="utf-8")
    watch = td / "watch"
    watch.mkdir()
    (watch / "loop_file.py").write_text("", encoding="utf-8")
    from cairn.devices.cairn.machines.ground_loop.__main__ import main
    extra = (f", class_root=Path({str(class_root)!r})"
             if "class_root" in inspect.signature(main).parameters else "")
    src = ("import sys; sys.path.insert(0, %r)\n"
           "from pathlib import Path\n"
           "from cairn.tools.base.address import ROOTS\n"
           "from cairn.devices.cairn.machines.ground_loop.__main__ import main\n"
           "roots = dict(ROOTS); roots['instance'] = Path(%r)\n"
           "raise SystemExit(main(roots=roots, cadence=0.2, watch=Path(%r)%s))\n"
           % (str(_REPO), str(td / "inst"), str(watch), extra))
    home = td / "inst" / "devices" / "cairn" / "0" / "machines" / "ground_loop"
    proc = subprocess.Popen([sys.executable, "-c", src], cwd=str(_REPO),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                            env={**os.environ, "PYTHONPATH": str(_REPO)})
    record: dict = {}
    try:
        end = time.monotonic() + 30
        while time.monotonic() < end:
            try:
                record = json.loads((home / "liveness.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                record = {}
            if (record.get("state") or {}).get("beats", 0) >= 3:
                break
            time.sleep(0.1)
        (home / "COMMAND_EXIT.flag").touch()
        rc = proc.wait(timeout=30)
    finally:
        if proc.poll() is None:
            proc.kill()
            proc.wait(timeout=30)
    state = record.get("state") or {}
    assert state.get("beats", 0) >= 3, f"the loop did not beat 3 times: {record} {proc.stderr.read()[-400:]}"
    assert rc == 0, f"COMMAND_EXIT did not stop the loop cleanly: rc={rc}"
    assert not marker.exists(), "a groundloop/pulse.py was called by the beat"
    assert set(state) == _STATE_KEYS, f"the record's state keys are {sorted(state)}, " \
                                      f"want exactly {sorted(_STATE_KEYS)}"


def test_the_build_deleted_no_probe():
    builds = [h for h in _git("log", "--format=%H", f"--grep={_TICKET}: build").split() if h]
    assert builds, f"no commit whose message carries '{_TICKET}: build' — the build has not landed"
    for commit in builds:
        lines = _git("diff", "--name-status", "--no-renames", f"{commit}^", commit).splitlines()
        gone = [ln.split("\t", 1)[1] for ln in lines
                if ln.startswith("D\t") and "/probes/" in ln and ln.endswith(".py")]
        assert gone == [], f"build {commit[:12]} deleted probe modules: {gone}"


def test_nothing_tracked_reaches_the_pulse_machinery():
    hits = []
    for rel in _tracked("*.py"):
        if "/proofs/" in rel or rel.endswith("test_the_beat_calls_nothing.py"):
            continue
        try:
            text = (_REPO / rel).read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        hits += [f"{rel}: {name}" for name in _PULSE_MACHINERY if name in text]
    assert hits == [], f"code still reaches the pulse machinery: {hits}"


def test_the_live_heartbeat_beats_without_triggers():
    active = subprocess.run(["systemctl", "--user", "is-active", "cairn-ground-loop.service"],
                            capture_output=True, text=True, timeout=30).stdout.strip()
    assert active == "active", f"cairn-ground-loop.service is {active!r}"
    from cairn.tools.liveness.liveness import read_liveness
    found = read_liveness(datetime.now(timezone.utc).astimezone())
    assert found["verdict"] == "LIVE", f"the live heartbeat is {found['verdict']}: {found}"
    state = (found.get("record") or {}).get("state") or {}
    assert set(state) == _STATE_KEYS, f"the live record's state keys are {sorted(state)} — " \
                                      f"the running loop still lists triggers"
    pid = (found.get("record") or {}).get("pid")
    main_pid = subprocess.run(["systemctl", "--user", "show", "-p", "MainPID", "--value",
                               "cairn-ground-loop.service"],
                              capture_output=True, text=True, timeout=30).stdout.strip()
    assert str(pid) == main_pid, f"the record's pid {pid} is not the unit's MainPID {main_pid}"


def test_codemother_hears_the_commit_through_the_fanout():
    assert _tracked("cairn/devices/codemother/hooks/post-commit"), \
        "codemother carries no tracked hooks/post-commit subscriber"
    got = subprocess.run([sys.executable, "-m", "cairn.tools.post_commit", "verify-hook"],
                         capture_output=True, text=True, cwd=str(_REPO), timeout=120)
    assert got.returncode == 0, f"the post-commit fan-out is not installed: {got.stdout}{got.stderr}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
