"""Proof for ticket 8c5fdb750b75 — bin/cairn maps a typed word to the folder whose charter
declares it as answers_as whenever no class folder carries the word, even when instance-space
holds a directory of that name (outline 11.3.2, 11.4.2).

The shim keeps last_known under its device_id, which for the two proxies is their answers_as
name, so the first run leaves ~/.cairn/devices/inference/0/ (measured on akiendelllinux
2026-11-18) and ~/.cairn/devices/database/0/ (akienlivingroom). The resolver looked the name up
only when no instance dir carried it either, so the alias sealed itself. Teeth, one per clause:

  1. with stray inference/0 and database/0 dirs, `cairn inference show` and `cairn database show`
     reach the bus mouth with argv [<typed name>, show] and never print 'no such device';
  2. `cairn inferenceproxy show` still resolves as itself: argv [inferenceproxy, show];
  3. a word no folder carries and no charter declares still reads 'no such device or command'
     and never reaches the mouth.

Every tooth runs bin/cairn as a subprocess over a scratch CAIRN_INSTANCE_ROOT from the scratch
door, with a stub CAIRN_BUS_MOUTH that records its argv (never a live bus).

    python3 bin/proofs/test_a_declared_name_outranks_a_stray_instance_dir.py   # exit 0 = green
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402
CAIRN = REPO / "bin" / "cairn"

PROVES = {
    "8c5fdb750b75": {
        "1": "clause_1_a_declared_name_resolves_past_a_stray_instance_dir",
        "2": "clause_2_a_folder_name_resolves_as_itself",
        "3": "clause_3_an_undeclared_word_is_still_no_such_device",
    },
}

FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1400]}", flush=True)
        FAILURES.append(name)


def _world() -> tuple[Path, Path, Path]:
    from cairn.tools.scratch.scratch import scratch_dir
    root = scratch_dir("8c5f-root-")
    for stray in ("inference", "database"):
        (root / stray / "0").mkdir(parents=True)
        (root / stray / "0" / "last_known.json").write_text("{}\n")
    log = root / "mouth.argv"
    mouth = root / "mouth"
    mouth.write_text(f'#!/usr/bin/env bash\nprintf "%s\\n" "$@" > "{log}"\necho "mouth answered"\n')
    mouth.chmod(0o755)
    return root, mouth, log


def _cairn(root: Path, mouth: Path, log: Path, *args: str) -> tuple[subprocess.CompletedProcess, list | None]:
    if log.exists():
        log.unlink()
    env = {**os.environ, "CAIRN_INSTANCE_ROOT": str(root), "CAIRN_BUS_MOUTH": str(mouth)}
    r = subprocess.run([*bash_script_argv(CAIRN), *args], capture_output=True, text=True, env=env,
                       timeout=300, stdin=subprocess.DEVNULL)
    return r, (log.read_text().splitlines() if log.exists() else None)


def clause_1_a_declared_name_resolves_past_a_stray_instance_dir(root: Path, mouth: Path, log: Path) -> None:
    seen = {}
    ok = True
    for name in ("inference", "database"):
        r, argv = _cairn(root, mouth, log, name, "show")
        seen[name] = (r.returncode, argv, r.stderr[-300:])
        ok = ok and argv == [name, "show"] and "no such device" not in r.stderr
    _check("clause_1_a_declared_name_resolves_past_a_stray_instance_dir", ok, repr(seen))


def clause_2_a_folder_name_resolves_as_itself(root: Path, mouth: Path, log: Path) -> None:
    r, argv = _cairn(root, mouth, log, "inferenceproxy", "show")
    _check("clause_2_a_folder_name_resolves_as_itself",
           argv == ["inferenceproxy", "show"] and "no such device" not in r.stderr,
           f"rc={r.returncode} argv={argv!r} err={r.stderr[-300:]!r}")


def clause_3_an_undeclared_word_is_still_no_such_device(root: Path, mouth: Path, log: Path) -> None:
    r, argv = _cairn(root, mouth, log, "zz8c5fnothing", "show")
    _check("clause_3_an_undeclared_word_is_still_no_such_device",
           argv is None and r.returncode != 0 and "no such device or command: zz8c5fnothing" in r.stderr,
           f"rc={r.returncode} argv={argv!r} err={r.stderr[-300:]!r}")


def main() -> int:
    for fn in (clause_1_a_declared_name_resolves_past_a_stray_instance_dir,
               clause_2_a_folder_name_resolves_as_itself,
               clause_3_an_undeclared_word_is_still_no_such_device):
        root, mouth, log = _world()
        fn(root, mouth, log)
    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
