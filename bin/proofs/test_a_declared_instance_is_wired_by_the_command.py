"""Proof for ticket f0ffa0db0952, clause 6 — the command wires the declared instance it addresses.

Measured 2026-11-09: bin/cairn wired instance bins only when ~/.cairn/devices/cairn/0 was
absent, so `cairn cc.1 restart` refused "no such instance" for an instance whose bin had never
been made, and a verb added to a class bin was never linked into an existing real instance bin.
Outline 5.7.3.4: an instance is declared by its folder existing in class-space; 5.3.4.1: any
cairn command brings up whatever it needs.

  6. `cairn <dev>.<n> <word>`, where class-space declares cairn/devices/<dev>/<n>/ and
     instance-space has no bin for it, wires that bin before dispatch and the word reaches it;
     a class verb missing from an existing instance bin is linked the first time it is asked
     for; an undeclared instance still refuses "no such instance" and nothing is made for it.

It runs a COPY of bin/cairn and of cairn/devices/recovery/bootstrap.sh inside a scratch repo
(both derive the repo root from their own path, so the copies see only the fixture device)
against a scratch CAIRN_INSTANCE_ROOT. Never ~/.cairn, never the live repo's devices.

    python3 bin/proofs/test_a_declared_instance_is_wired_by_the_command.py
"""
from __future__ import annotations

import os
import shutil
import stat
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"f0ffa0db0952": {"6": "tooth_6_the_command_wires_the_declared_instance"}}
DEV = "fixture_declared"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if detail:
        print(f"        {detail[:1200]}", flush=True)
    if not ok:
        FAILURES.append(name)


def _stub(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\nprintf '%s\\n' \"$0\"\n")
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def tooth_6() -> None:
    name = PROVES["f0ffa0db0952"]["6"]
    base = scratch_dir("testing-f0ffa0db0952-bin-")
    try:
        repo = base / "repo"
        (repo / "bin").mkdir(parents=True)
        shutil.copy2(REPO / "bin" / "cairn", repo / "bin" / "cairn")
        (repo / "cairn" / "devices" / "recovery").mkdir(parents=True)
        shutil.copy2(REPO / "cairn" / "devices" / "recovery" / "bootstrap.sh",
                     repo / "cairn" / "devices" / "recovery" / "bootstrap.sh")
        cls = repo / "cairn" / "devices" / DEV / "0" / "bin"
        _stub(cls / "stub")
        (repo / "cairn" / "devices" / DEV / "2").mkdir()          # instance 2 is declared
        root = base / "instance"
        (root / "cairn" / "0").mkdir(parents=True)                # the instance floor stands
        mouth = base / "mouth"                                     # never the live bus
        mouth.write_text("#!/usr/bin/env bash\necho \"BUS $*\" >&2; exit 3\n")
        mouth.chmod(0o755)
        env = {**os.environ, "CAIRN_BUS_MOUTH": str(mouth), "CAIRN_INSTANCE_ROOT": str(root), "CAIRN_BOOT_LOG": str(base / "bootlog"),
               "CAIRN_CMD_DIR": str(base / "nocmd")}

        def run(*args: str) -> subprocess.CompletedProcess:
            return subprocess.run([*bash_script_argv(repo / "bin" / "cairn"), *args], capture_output=True,
                                  text=True, env=env, timeout=120)

        got = {}
        r = run(f"{DEV}.2", "stub")                                # (a) declared, bin never made
        want = str(root / DEV / "2" / "bin" / "stub")
        got["declared"] = (r.returncode == 0 and r.stdout.strip() == want,
                           f"rc={r.returncode} out={r.stdout!r} err={r.stderr[-300:]!r}")
        b0 = root / DEV / "0" / "bin"                              # (b) a real bin lacking a new verb
        b0.mkdir(parents=True)
        (b0 / "stub").symlink_to(cls / "stub")
        _stub(cls / "second")
        r = run(DEV, "second")
        want = str(b0 / "second")
        got["new_verb"] = (r.returncode == 0 and r.stdout.strip() == want
                           and (b0 / "second").resolve() == (cls / "second").resolve(),
                           f"rc={r.returncode} out={r.stdout!r} err={r.stderr[-300:]!r}")
        r = run(f"{DEV}.5", "stub")                                # (c) undeclared: still refused
        got["undeclared"] = (r.returncode == 127 and "no such instance" in r.stderr
                             and not (root / DEV / "5").exists(),
                             f"rc={r.returncode} err={r.stderr[-300:]!r} made={(root / DEV / '5').exists()}")
        check(name, all(ok for ok, _ in got.values()),
              "; ".join(f"{k}: {'ok' if ok else 'BAD ' + d}" for k, (ok, d) in got.items()))
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main() -> int:
    try:
        tooth_6()
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(PROVES["f0ffa0db0952"]["6"], False, f"{type(exc).__name__}: {exc}")
    print(f"{1 - len(FAILURES)} passed, {len(FAILURES)} failed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
