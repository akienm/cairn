"""Proof for ticket 211facd306d7 — the launcher's help lists what bin_shortcuts lists.

Measured 2026-11-10 before the build: bin/cairn's _help checked the instance bin's folder before
calling cairn.tools.base.shim.bin_shortcuts (`(no bin under ...)`) and built the `cairn help`
roster from instance bins alone, so a device whose shortcuts live beside its code (outline
5.4.3.3) showed no shortcut, though bin_shortcuts reads both bins (ticket ba777080011b).

Teeth, one per falsifier clause:

  1. over a scratch instance root holding fxhc/0 with no bin and a scratch class root
     (CAIRN_CLASS_ROOT) holding an executable fxhc/bin/wave, `cairn help` exits 0 with an [fxhc]
     section listing `wave — waves`, and no line says `no bin under`;
  2. `cairn fxhc help` in the same world exits 0 and lists `wave — waves`;
  3. fxhd, whose instance bin holds only a non-executable file and which has no class bin, gets
     its section, reading `(none)`;
  4. the standing launcher proofs pass unchanged.

Every run is bin/cairn as a subprocess under a scratch HOME from the scratch door; the live
instance, bus, venv and db are never touched.

    python3 bin/proofs/test_help_lists_the_bin_beside_the_code_from_the_launcher.py   # exit 0 = green
"""
from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
CAIRN = REPO / "bin" / "cairn"

PROVES = {
    "211facd306d7": {
        "1": "help_lists_a_class_only_device",
        "2": "device_help_lists_the_class_bin",
        "3": "an_empty_device_reads_none",
        "4": "the_standing_launcher_proofs_pass",
    },
}

STANDING = ["bin/proofs/test_cairn_help_lists_in_the_operators_order.py",
            "bin/proofs/test_the_launcher_reads_the_bin_beside_the_code.py"]
FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1400]}", flush=True)
        FAILURES.append(name)


def _world() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    home = scratch_dir("211f-home-")
    (home / "devices" / "fxhc" / "0").mkdir(parents=True)
    nb = home / "devices" / "fxhd" / "0" / "bin"
    nb.mkdir(parents=True)
    (nb / "notes.txt").write_text("# not executable\n")
    os.chmod(nb / "notes.txt", 0o644)
    w = home / "classes" / "fxhc" / "bin" / "wave"
    w.parent.mkdir(parents=True)
    w.write_text("#!/bin/sh\n# wave — waves\necho wave\n")
    os.chmod(w, 0o755)
    (home / "nosock").mkdir()
    return home


def _run(home: Path, *args: str) -> subprocess.CompletedProcess:
    env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    env.update(HOME=str(home), CAIRN_INSTANCE_ROOT=str(home / "devices"),
               CAIRN_CLASS_ROOT=str(home / "classes"), CAIRN_VENV=str(home / "venv"),
               CAIRN_PG_SOCKET_DIR=str(home / "nosock"))
    return subprocess.run([str(CAIRN), *args], env=env, capture_output=True, text=True,
                          timeout=180, cwd="/")


def _sections(text: str) -> dict[str, list[str]]:
    out: dict[str, list[str]] = {}
    cur = None
    for ln in text.splitlines():
        s = ln.strip()
        if s.startswith("[") and s.endswith("]"):
            cur = s[1:-1]
            out[cur] = []
        elif cur is not None and s:
            out[cur].append(s)
    return out


def main() -> int:
    home = _world()

    r = _run(home, "help")
    sec = _sections(r.stdout)
    _check("help_lists_a_class_only_device",
           r.returncode == 0 and "wave — waves" in (sec.get("fxhc") or [])
           and "no bin under" not in r.stdout,
           f"rc={r.returncode} fxhc={sec.get('fxhc')} stdout={r.stdout[-900:]} stderr={r.stderr[-400:]}")

    r2 = _run(home, "fxhc", "help")
    _check("device_help_lists_the_class_bin", r2.returncode == 0 and "wave — waves" in r2.stdout,
           f"rc={r2.returncode} stdout={r2.stdout[-700:]} stderr={r2.stderr[-400:]}")

    _check("an_empty_device_reads_none", r.returncode == 0 and sec.get("fxhd") == ["(none)"],
           f"fxhd={sec.get('fxhd')}")

    bad = []
    for p in STANDING:
        rp = subprocess.run([sys.executable, str(REPO / p)], capture_output=True, text=True, timeout=900)
        if rp.returncode != 0:
            bad.append(f"{p}: rc={rp.returncode} {rp.stdout[-400:]!r}")
    _check("the_standing_launcher_proofs_pass", not bad, "; ".join(bad))

    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
