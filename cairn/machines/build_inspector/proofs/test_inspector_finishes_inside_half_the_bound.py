"""Teeth for "test_inspector.py finishes inside the verdict's 600 s bound, and a kill is told apart
from slow" (ticket e7d244d66bd7).

MEASURED: the 9cfc verdict was refused "TIMEOUT, not disagreement" at 643.708 s against the 600 s
bound, and an earlier re-run exited -9. 2026-11-14 on akiendelllinux, under /usr/bin/time -v:
564 s of teeth, 570 s wall, peak RSS 180 MB (so not memory), and three teeth took 544 s of it:
two whole-tree ``inspect()`` sweeps (233 s, 223 s) and a two-sieve whole-tree sweep (88 s).
The two whole-tree teeth moved to test_inspector_over_the_real_tree.py (one shared sweep) and
the two-sieve one runs over the fixture root.

  1. test_test_inspector_exits_0_in_under_300_s_with_every_tooth_printed: one run of
     test_inspector.py exits 0 in under half the verdict's bound, with no FAIL line and at least
     the teeth PROVES names. A signal exit (-9) is reported as KILLED, with the peak RSS, and a
     run past the bound as SLOW, so the two causes never read as one;
  2. test_every_tooth_prints_its_wall_time: in that run's output every ``ok`` line is followed
     by its ``took <s> s`` line, so a slow tooth names itself.

"Three consecutive runs" is three seals of this proof on the Dell, not a loop inside it (a loop
would put this file itself past the bound).

    bin/cairn test cairn/machines/build_inspector/proofs/test_inspector_finishes_inside_half_the_bound.py
"""
from __future__ import annotations

import re
import os
import resource
import signal
import subprocess
import sys
import time
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_REPO = _HERE.parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"e7d244d66bd7": {
    "1": "test_test_inspector_exits_0_in_under_300_s_with_every_tooth_printed",
    "2": "test_every_tooth_prints_its_wall_time",
}}

SUBJECT = _HERE / "test_inspector.py"
BOUND_S = 300          # half the verdict door's 600 s
PROOF_TIMEOUT_S = 360  # the subject's bound plus this file's own start-up

_RUN: dict = {}


def _run() -> dict:
    """One run of the subject, shared by both teeth."""
    if _RUN:
        return _RUN
    began = time.monotonic()
    try:
        p = subprocess.run([sys.executable, str(SUBJECT)], capture_output=True, text=True,
                           timeout=BOUND_S, cwd=str(_HERE),
                           env={**os.environ, "PYTHONUNBUFFERED": "1"})  # a timeout keeps what printed
        _RUN.update(rc=p.returncode, out=p.stdout, err=p.stderr, slow=False)
    except subprocess.TimeoutExpired as e:
        out = e.stdout.decode(errors="replace") if isinstance(e.stdout, bytes) else (e.stdout or "")
        _RUN.update(rc=None, out=out, err="", slow=True)
    _RUN["wall"] = time.monotonic() - began
    # ru_maxrss is KiB on Linux: the largest child this process has waited on, the subject.
    _RUN["peak_mb"] = resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024
    return _RUN


def _slowest(out: str, n: int = 3) -> str:
    rows, name = [], None
    for line in out.splitlines():
        m = re.match(r"  ok    (.*)", line)
        if m:
            name = m.group(1)
            continue
        m = re.match(r"\s+took ([\d.]+) s", line)
        if m and name:
            rows.append((float(m.group(1)), name[:70]))
            name = None
    return "; ".join(f"{t:.0f} s {nm}" for t, nm in sorted(rows, reverse=True)[:n]) or "none timed"


def test_test_inspector_exits_0_in_under_300_s_with_every_tooth_printed():
    r = _run()
    if r["slow"]:
        raise AssertionError(f"SLOW, not killed: test_inspector.py did not finish inside {BOUND_S} s "
                             f"(slowest timed so far: {_slowest(r['out'])})")
    if r["rc"] is not None and r["rc"] < 0:
        sig = signal.Signals(-r["rc"]).name
        raise AssertionError(f"KILLED by {sig} after {r['wall']:.0f} s, not slow: peak RSS "
                             f"{r['peak_mb']:.0f} MB; read `journalctl -k | grep -i oom` for a "
                             f"memory-cgroup kill")
    assert r["rc"] == 0, f"test_inspector.py exited {r['rc']}: {r['err'][-800:]}"
    assert r["wall"] < BOUND_S, f"{r['wall']:.0f} s is not under {BOUND_S} s"
    assert "  FAIL" not in r["out"], "a tooth printed FAIL"
    from cairn.tools.proof_coverage.proof_coverage import teeth_printed
    green = set(teeth_printed(r["out"])["green"])
    import ast
    tree = ast.parse(SUBJECT.read_text(encoding="utf-8"))
    declared = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                    and any(getattr(t, "id", None) == "PROVES" for t in n.targets))
    missing = {t for m in declared.values() for t in m.values()} - green
    assert not missing, f"teeth PROVES names did not print green: {sorted(missing)}"
    print(f"        test_inspector.py: {r['wall']:.1f} s wall, peak RSS {r['peak_mb']:.0f} MB, "
          f"slowest: {_slowest(r['out'])}")


def test_every_tooth_prints_its_wall_time():
    lines = _run()["out"].splitlines()
    oks = [i for i, line in enumerate(lines) if line.startswith("  ok    ")]
    assert oks, "the run printed no ok tooth, so nothing here could be timed"
    untimed = [lines[i][8:80] for i in oks
               if i + 1 >= len(lines) or not re.match(r"\s+took [\d.]+ s$", lines[i + 1])]
    assert not untimed, f"{len(untimed)} of {len(oks)} teeth printed no wall time: {untimed[:3]}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
