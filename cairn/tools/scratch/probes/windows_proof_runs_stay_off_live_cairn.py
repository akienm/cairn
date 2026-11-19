"""WATCHME probe: windows_proof_runs_stay_off_live_cairn (ticket dda0e72b9c67, outcome 4 / D8).

THE HYPOTHESIS IT WATCHES (D8, CC's answer under outline 0.6.1, not a question). Windows has
no bwrap seal. There the tester's scratch HOME (d95796cdfb9b: HOME and USERPROFILE point at a
per-run scratch dir) is the seal, so the scratch door's check (D5, scratch.py
``_refuse_outside_the_seal``) counts a run as sealed when CAIRN_TESTER_TEST_ID is set; and with
no systemd-run on Windows the loop guard (D6) is a no-op. Nothing on Linux measured that. The
Linux teeth (bin/proofs/test_a_proof_run_by_any_spelling_is_sealed.py) list the live
~/.cairn/devices before and after a sealed run; this is the same listing, on Windows, over the
runs the tester actually makes there.

THE MEASUREMENT. Each ``cairn test`` run leaves its log directory at
``<instance>/logs/tester/0/runs/<test id>/`` (cairn/devices/tester/runs.py ``keep_output``),
read here BY PATH through address.log_path (no import of the tester device, RULE 1). A run's
window is [the directory's creation, the newest file in it]. An entry under the live
``~/.cairn/devices`` whose creation falls inside a window is NEW during that run. A real device
writes its own instance space while a run is in flight (the ground loop on its beat), so only
an entry at a DEVICE NAME THE REPO DOES NOT DECLARE (cairn/devices/<name>/ absent) counts: that
is the shape the 11-12 and 11-16 leaks took on Linux (fixture devices named by bare proof runs,
ticket measured). Coarse, n=1-grade by design (Law 10): a leak that writes into a real device's
instance space is not seen, and that blind spot is the one to sharpen if this ever reads clean
while a leak is reported by other means.

FIRES on the first run whose window holds such an entry (the hypothesis is killed: the scratch
HOME did not seal). ENOUGH once 10 runs have been read with none (the ticket's horizon).
Off Windows it neither fires nor clears: the Linux seal has its own proof.

AUTHORITY: none. It deposits and pokes codemother's WATCHME gate (Law 6).
"""
from __future__ import annotations

import os
import time
from pathlib import Path

from cairn.tools.base.address import log_path
from cairn.tools.base.probe import Probe, Threshold, once, watch_carry

_TICKET_ID = "dda0e72b9c67"
_REPO_ROOT = Path(__file__).resolve().parents[4]

ENOUGH_RUNS = 10


def _ctime(p: Path) -> float:
    st = p.stat()
    # On Windows st_ctime is the creation time; st_birthtime where the platform has it.
    return getattr(st, "st_birthtime", st.st_ctime)


def survey() -> dict:
    """Read every tester run's window and every live device entry born inside one."""
    if os.name != "nt":
        return {"windows": False, "runs": 0, "leaks": []}
    declared = {p.name for p in (_REPO_ROOT / "cairn" / "devices").iterdir() if p.is_dir()}
    runs_root = log_path("tester") / "runs"
    windows: list[tuple[str, float, float]] = []
    if runs_root.is_dir():
        for d in runs_root.iterdir():
            if not d.is_dir():
                continue
            try:
                files = [f for f in d.iterdir() if f.is_file()]
                start = _ctime(d)
                end = max([f.stat().st_mtime for f in files] or [start])
            except OSError:
                continue
            windows.append((d.name, start, end))
    live = Path.home() / ".cairn" / "devices"
    leaks: list[dict] = []
    if live.is_dir():
        for e in live.iterdir():
            if e.name in declared:
                continue
            try:
                born = _ctime(e)
            except OSError:
                continue
            for test, start, end in windows:
                if start <= born <= end:
                    leaks.append({"entry": str(e), "test": test,
                                  "born": time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(born))})
    return {"windows": True, "runs": len(windows), "leaks": leaks}


def _trigger(now, context: dict) -> bool:
    s = once(context, "survey", survey)
    return bool(s["leaks"])


def _enough(context: dict) -> bool:
    s = once(context, "survey", survey)
    return s["windows"] and s["runs"] >= ENOUGH_RUNS and not s["leaks"]


def _carry(context: dict) -> dict:
    s = once(context, "survey", survey)
    n = len(s["leaks"])
    return {
        "runs": s["runs"],
        "leaks": s["leaks"][:20],
        "finding": (
            "%d entr%s under the live ~/.cairn/devices, at a device name the repo does not "
            "declare, was born inside a tester run on Windows: the scratch HOME did not seal "
            "(D8 killed); the scratch door must learn the Windows seal" % (n, "y" if n == 1 else "ies")
        ) if n else (
            "%d tester run(s) on Windows, none put an undeclared device under the live "
            "~/.cairn/devices" % s["runs"]
        ),
    }


PROBE = Probe(
    why="on Windows the tester has no bwrap seal and D8 says the scratch HOME is the seal; "
        "nothing measured that there. This reads the live ~/.cairn/devices against every "
        "tester run's window and fires on the first fixture device born inside one.",
    trigger=_trigger,
    to="codemother",
    body={"nexus": "dda0e72b9c67 outcome 4", "kind": "efficacy"},
    verb="machines/watchme/watch",
    carry=watch_carry(_TICKET_ID, _carry, fails=_trigger),
    enough=_enough,
    thresholds=(
        Threshold(ENOUGH_RUNS, "tester runs read on Windows with no leak",
                  set_by="ticket dda0e72b9c67 watchme names the number (10 batches)"),
    ),
    horizon=1000,
)
