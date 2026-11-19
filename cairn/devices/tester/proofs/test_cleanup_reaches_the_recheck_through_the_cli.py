"""Proof for ticket ea354f41ec67 — `cairn cleanup` clears a gone proof's seal-red through the tester's CLI.

Ticket 17b087f2483f's hollow read cairn/devices/tester/cli.py (the --recheck-troubles flag) and
bin/cmd/cleanup (the seals step) HOLLOW: its five teeth call recheck() in-process, so reverting
either file redded none of them (operator notices n-def5539f538c, n-9be844494f16). This tooth
runs the wiring itself, as a hand does, so removing either piece reds it.

1. In a scratch HOME, a seal-red-* trouble naming a proof file that does not exist is raised
   and drained OPEN; `bin/cairn cleanup` then reports it cleared on its seals line, and
   `cairn trouble live` no longer lists it.

Everything runs as subprocesses under the scratch HOME (`cairn.tools.scratch.scratch_dir`, which
removes it and reaps what ran under it): the trouble store, the tester's emissions and the bus
the drain starts all live there, and the bus runs under this proof's own unit name
(CAIRN_BUS_UNIT), stopped and reset at the end. Nothing is written outside the scratch HOME.

Run through the tester (scratch_dir refuses a bare run):
    bin/cairn test cairn/devices/tester/proofs/test_cleanup_reaches_the_recheck_through_the_cli.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"ea354f41ec67": {"1": "cleanup_clears_a_gone_proofs_seal_red_through_the_cli"}}
GONE = "cairn/devices/tester/proofs/test_a_proof_that_was_never_written.py"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:400]}")
    if not ok:
        FAILURES.append(name)


def _run(env: dict, *argv: str, timeout: int = 300) -> subprocess.CompletedProcess:
    return subprocess.run(list(argv), cwd=REPO, env=env, capture_output=True, text=True,
                          timeout=timeout)


def main() -> int:
    from cairn.tools.scratch.scratch import scratch_dir

    home = scratch_dir("cleanupwire")
    unit = f"cairn-proof-cleanupwire-{os.getpid()}"
    env = dict(os.environ, HOME=str(home), CAIRN_BUS_UNIT=unit, GIT_TERMINAL_PROMPT="0",
               PYTHONPATH=str(REPO))
    cairn = str(REPO / "bin" / "cairn")
    try:
        raise_it = (
            "from cairn.tools.base.diagnostic import ModuleRaiser\n"
            "from cairn.tools.validation_store.validation_store import seal_trouble_identity\n"
            f"i = seal_trouble_identity({GONE!r})\n"
            "ModuleRaiser('tester').raise_trouble(i, why='a seal-red for a proof that is gone')\n"
            "print(i)\n")
        r = _run(env, sys.executable, "-c", raise_it)
        ident = r.stdout.strip().splitlines()[-1] if r.stdout.strip() else ""
        drained = _run(env, cairn, "trouble", "drain")

        def live() -> list[str]:
            out = _run(env, cairn, "trouble", "live", "--json")
            try:
                return [t["id"] for t in json.loads(out.stdout)]
            except Exception:
                return [f"unreadable: {out.stdout[-200:]} {out.stderr[-200:]}"]

        before = live()
        cleanup = _run(env, cairn, "cleanup")
        seals = next((ln for ln in cleanup.stdout.splitlines() if ln.startswith("seals ")), "")
        after = live()
        check(PROVES["ea354f41ec67"]["1"],
              bool(ident) and ident in before and ident not in after
              and " ok " in seals and ident in seals,
              f"identity={ident!r} raise_rc={r.returncode} drain_rc={drained.returncode} "
              f"open_before={ident in before} seals_line={seals!r} cleanup_rc={cleanup.returncode} "
              f"live_after={after}")
    finally:
        for verb in ("stop", "reset-failed"):
            subprocess.run(["systemctl", "--user", verb, f"{unit}.service"],
                           capture_output=True, text=True)
    print(f"\n{1 - len(FAILURES)}/1 passed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
