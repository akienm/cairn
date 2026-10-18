"""Proof for ticket a9d43ca95d78 — the unswapped arm measures free swap before it calls a
balloon contained, and no balloon scope outlives its run.

Measured 2026-10-12: test_superclaude_memory_scope.py's non-hollow arm ran a balloon under a
100M cap with swap unbounded and read rc=-9 as "does not escape" while SwapFree was 220 MiB —
the kernel had killed the balloon for want of swap, not the cap. And 10 failed run-p*.scope
balloons stood loaded in the user manager, because the balloon scopes carried no CollectMode.

1. with the swap reader at 220 MiB the arm records a FAIL naming the unmet precondition and
   runs no balloon; with it at 4096 MiB and a balloon that REACHED, the arm passes;
2. every balloon scope _run_ballooned starts carries -p CollectMode=inactive-or-failed.

The memory-scope proof is loaded by path INSIDE each tooth, so a reverted build reds a tooth
rather than crashing the import.

Run bare:  PYTHONPATH=. python3 launchers/proofs/test_the_unswapped_arm_measures_swap_first.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import json
import subprocess
import sys
import types
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "a9d43ca95d78": {
        "1": "an_arm_short_of_swap_reds_as_precondition_unmet",
        "2": "every_balloon_scope_is_collected_on_failure",
    },
}

SUBJECT = REPO / "launchers/proofs/test_superclaude_memory_scope.py"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:300]}")
    if not ok:
        FAILURES.append(name)


def _load():
    spec = importlib.util.spec_from_file_location("_memory_scope_under_proof", SUBJECT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def tooth_1() -> None:
    name = PROVES["a9d43ca95d78"]["1"]
    try:
        mod = _load()
        ran: list[list[str]] = []

        def balloon(stdout: str, rc: int):
            def run(limits):
                ran.append(limits)
                return subprocess.CompletedProcess(args=[], returncode=rc, stdout=stdout, stderr="")
            return run

        mod._swap_free_mib = lambda: 220
        mod._run_ballooned = balloon("", -9)
        mod.FAILURES.clear()
        # The arm prints its own PASS/FAIL lines; they are the fixture's, not this proof's teeth,
        # so they are captured — a green seal must not carry a FAIL line a reader parses as red.
        with contextlib.redirect_stdout(io.StringIO()):
            mod._unswapped_arm()
        short = list(mod.FAILURES)
        short_ran = len(ran)
        short_ok = (len(short) == 1 and "precondition unmet" in short[0]
                    and "220" in short[0] and "512" in short[0] and short_ran == 0)

        mod._swap_free_mib = lambda: 4096
        mod._run_ballooned = balloon("REACHED 400", 0)
        mod.FAILURES.clear()
        with contextlib.redirect_stdout(io.StringIO()):
            mod._unswapped_arm()
        roomy = list(mod.FAILURES)
        check(name, short_ok and roomy == [] and len(ran) == 1,
              json.dumps({"short": short, "balloons_run_when_short": short_ran, "roomy": roomy}))
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def tooth_2() -> None:
    name = PROVES["a9d43ca95d78"]["2"]
    try:
        mod = _load()
        seen: list[list[str]] = []

        def run(argv, **kw):
            seen.append(list(argv))
            return subprocess.CompletedProcess(argv, 0, "REACHED 400", "")

        mod.subprocess = types.SimpleNamespace(run=run, CompletedProcess=subprocess.CompletedProcess)
        mod._run_ballooned(["-p", "MemoryMax=100M"])
        argv = seen[0] if seen else []
        pairs = list(zip(argv, argv[1:]))
        check(name, ("-p", "CollectMode=inactive-or-failed") in pairs, json.dumps(argv))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    tooth_1()
    tooth_2()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
