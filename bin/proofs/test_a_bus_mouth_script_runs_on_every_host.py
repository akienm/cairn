"""Proof for ticket 5b0a7c2e91d4 — bin/cairn.py runs a CAIRN_BUS_MOUTH script through the shebang resolver.

Measured 2026-11-20 on akiendell (Windows): test_a_word_with_no_script_goes_onto_the_bus clause_3 and
test_the_launcher_reads_the_bin_beside_the_code a_word_in_no_bin_goes_to_the_bus both read red with rc=70 and
`OSError: [WinError 193] %1 is not a valid Win32 application`. bin/cairn.py `_bus` launched the
CAIRN_BUS_MOUTH override with a bare subprocess.call([mouth, ...]); `_run` goes through `_argv_for`, which
gives a shebang script its shell on Windows. Outline 5.4.3.8: one dispatcher serves both platforms.

Each tooth runs bin/cairn.py itself as a subprocess over a scratch CAIRN_INSTANCE_ROOT, so it reads the
behaviour the user gets, on any host.

  1. with CAIRN_BUS_MOUTH naming a shebang script, a typed word with no script reaches that script with
     argv [device, word, args...] (a spaced word stays whole) and bin/cairn.py exits the script's code;
  2. with CAIRN_BUS_MOUTH naming a script whose shebang interpreter this host does not have, bin/cairn.py
     exits 126 and names the script, never WinError 193 or the launcher-failed 70.

    python3 bin/proofs/test_a_bus_mouth_script_runs_on_every_host.py   # exit 0 = green
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

CAIRN_PY = REPO / "bin" / "cairn.py"
DEV = "testing-5b0a-device"

PROVES = {"5b0a7c2e91d4": {
    "1": "a_shebang_mouth_receives_the_typed_word_and_returns_its_code",
    "2": "a_mouth_this_host_cannot_run_exits_126_naming_it",
}}

FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1400]}", flush=True)
        FAILURES.append(name)


def _world() -> tuple[Path, Path]:
    from cairn.tools.scratch.scratch import scratch_dir
    root = scratch_dir("5b0a-root-")
    (root / DEV / "0" / "bin").mkdir(parents=True)
    return root, root / "mouth"


def _run(root: Path, mouth: Path, *args: str) -> subprocess.CompletedProcess:
    env = {**os.environ, "CAIRN_INSTANCE_ROOT": str(root), "CAIRN_BUS_MOUTH": str(mouth), "PYTHONUTF8": "1"}
    return subprocess.run([sys.executable, str(CAIRN_PY), *args], capture_output=True, text=True, env=env, timeout=120)


def a_shebang_mouth_receives_the_typed_word_and_returns_its_code() -> None:
    root, mouth = _world()
    log = root / "mouth.argv"
    mouth.write_text(f'#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "{log.as_posix()}"; echo "mouth answered"; exit 7\n')
    mouth.chmod(0o755)
    r = _run(root, mouth, DEV, "zork", "Two Words")
    argv = log.read_text().splitlines() if log.exists() else None
    _check("a_shebang_mouth_receives_the_typed_word_and_returns_its_code",
           argv == [DEV, "zork", "Two Words"] and r.returncode == 7 and r.stdout == "mouth answered\n",
           f"argv={argv!r} rc={r.returncode} out={r.stdout!r} err={r.stderr[-400:]!r}")


def a_mouth_this_host_cannot_run_exits_126_naming_it() -> None:
    root, mouth = _world()
    mouth.write_text("#!/usr/bin/env no_such_interpreter_5b0a\nexit 0\n")
    mouth.chmod(0o755)
    r = _run(root, mouth, DEV, "zork")
    _check("a_mouth_this_host_cannot_run_exits_126_naming_it",
           r.returncode == 126 and mouth.name in r.stderr and "WinError" not in r.stderr,
           f"rc={r.returncode} out={r.stdout!r} err={r.stderr[-400:]!r}")


def main() -> int:
    for fn in (a_shebang_mouth_receives_the_typed_word_and_returns_its_code,
               a_mouth_this_host_cannot_run_exits_126_naming_it):
        fn()
    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
