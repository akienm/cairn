"""Proof for ticket 30366e99655a — the cairn launcher runs a word from the bin/ beside a device's code.

Measured 2026-11-10 before the build: bin/cairn dispatched only ~/.cairn/devices/<device>/<n>/bin/<word>,
then the bus mouth, then bin/cmd; `cairn restart` answered "no such device or command". Outline
5.4.3.3: "Any device or machine may have a bin/ beside its code ... `cairn foo` whose first word is
not a device means `cairn cairn foo`: top-level shortcuts are the cairn device's bin/." 5.4.3.5: "If
a shortcut has the same name as a device, the launcher warns "x hides y" and then runs x." Akien's
answer open-8c01545a26d8 puts top-level shortcuts at cairn/devices/cairn/bin/.

Teeth, one per falsifier clause:

  1. `cairn greet a b` runs the scratch class root's cairn/bin/greet with argv a b, its exit code the command's;
  2. `cairn cairn greet a` runs the same script;
  3. `cairn <device> wave z` runs the device's class bin/wave when the instance bin lacks it, and a word the
     instance bin holds still runs the instance script;
  4. a word in neither bin still goes to the bus mouth with argv [<device>, <word>];
  5. a cairn/bin script named like a device prints a line containing 'hides' to stderr and runs, not the device;
  6. the standing launcher proofs pass unchanged.

Every tooth runs bin/cairn as a subprocess over a scratch CAIRN_INSTANCE_ROOT and a scratch
CAIRN_CLASS_ROOT from the scratch door; the bus mouth is a stub named by CAIRN_BUS_MOUTH.

    python3 bin/proofs/test_the_launcher_reads_the_bin_beside_the_code.py   # exit 0 = green
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
DEV = "testing-lw-device"
STANDING = ["bin/proofs/test_a_word_with_no_script_goes_onto_the_bus.py",
            "bin/proofs/test_cairn_command.py",
            "bin/proofs/test_cairn_instance_address.py"]

PROVES = {
    "30366e99655a": {
        "1": "a_top_level_word_runs_the_cairn_bin",
        "2": "the_long_form_runs_the_same_script",
        "3": "a_device_word_runs_its_class_bin",
        "4": "a_word_in_no_bin_goes_to_the_bus",
        "5": "a_shortcut_hides_a_device_and_says_so",
        "6": "the_standing_launcher_proofs_pass",
    },
}

FAILURES: list[str] = []


def _check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if not ok:
        if detail:
            print(f"        {detail[:1400]}", flush=True)
        FAILURES.append(name)


def _stub(path: Path, body: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("#!/usr/bin/env bash\n" + body + "\n")
    path.chmod(0o755)


class _World:
    def __init__(self, hiding: bool = False) -> None:
        from cairn.tools.scratch.scratch import scratch_dir
        self.root = scratch_dir("3036-inst-")
        self.cls = scratch_dir("3036-class-")
        _stub(self.root / DEV / "0" / "bin" / DEV, 'echo "self:$*"')
        _stub(self.root / DEV / "0" / "bin" / "hello", 'echo "instance-hello:$*"')
        _stub(self.cls / DEV / "bin" / "wave", 'echo "class-wave:$*"')
        _stub(self.cls / DEV / "bin" / "hello", 'echo "class-hello:$*"')
        _stub(self.cls / "cairn" / "bin" / "greet", 'echo "greet:$*"; exit 5')
        if hiding:
            _stub(self.cls / "cairn" / "bin" / DEV, 'echo "cairn-bin-shortcut:$*"')
        self.log = self.root / "mouth.argv"
        self.mouth = self.root / "mouth"
        _stub(self.mouth, f'printf "%s\\n" "$@" > "{self.log}"; echo "mouth answered"; exit 7')

    def cairn(self, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "CAIRN_INSTANCE_ROOT": str(self.root), "CAIRN_CLASS_ROOT": str(self.cls),
               "CAIRN_BUS_MOUTH": str(self.mouth)}
        return subprocess.run([str(CAIRN), *args], capture_output=True, text=True, env=env, timeout=120)


def a_top_level_word_runs_the_cairn_bin() -> None:
    w = _World()
    r = w.cairn("greet", "a", "b")
    _check("a_top_level_word_runs_the_cairn_bin",
           r.returncode == 5 and r.stdout == "greet:a b\n" and not w.log.exists(),
           f"rc={r.returncode} out={r.stdout!r} err={r.stderr[-400:]!r}")


def the_long_form_runs_the_same_script() -> None:
    w = _World()
    r = w.cairn("cairn", "greet", "a")
    _check("the_long_form_runs_the_same_script",
           r.returncode == 5 and r.stdout == "greet:a\n" and not w.log.exists(),
           f"rc={r.returncode} out={r.stdout!r} err={r.stderr[-400:]!r} mouth={w.log.exists()}")


def a_device_word_runs_its_class_bin() -> None:
    w = _World()
    r = w.cairn(DEV, "wave", "z")
    h = w.cairn(DEV, "hello", "q")
    _check("a_device_word_runs_its_class_bin",
           r.returncode == 0 and r.stdout == "class-wave:z\n" and h.stdout == "instance-hello:q\n"
           and not w.log.exists(),
           f"wave rc={r.returncode} out={r.stdout!r} err={r.stderr[-400:]!r}; hello out={h.stdout!r}")


def a_word_in_no_bin_goes_to_the_bus() -> None:
    w = _World()
    r = w.cairn(DEV, "zork", "Two Words")
    argv = w.log.read_text().splitlines() if w.log.exists() else None
    _check("a_word_in_no_bin_goes_to_the_bus",
           argv == [DEV, "zork", "Two Words"] and r.returncode == 7 and r.stdout == "mouth answered\n",
           f"argv={argv!r} rc={r.returncode} out={r.stdout!r} err={r.stderr[-400:]!r}")


def a_shortcut_hides_a_device_and_says_so() -> None:
    w = _World(hiding=True)
    r = w.cairn(DEV, "x")
    _check("a_shortcut_hides_a_device_and_says_so",
           r.returncode == 0 and r.stdout == "cairn-bin-shortcut:x\n" and "hides" in r.stderr,
           f"rc={r.returncode} out={r.stdout!r} err={r.stderr[-400:]!r}")


def the_standing_launcher_proofs_pass() -> None:
    bad = []
    for p in STANDING:
        r = subprocess.run([sys.executable, str(REPO / p)], cwd=REPO, capture_output=True, text=True, timeout=600)
        if r.returncode != 0:
            bad.append(f"{p}: rc={r.returncode} {r.stdout[-600:]}")
    _check("the_standing_launcher_proofs_pass", not bad, " | ".join(bad))


def main() -> int:
    for fn in (a_top_level_word_runs_the_cairn_bin, the_long_form_runs_the_same_script,
               a_device_word_runs_its_class_bin, a_word_in_no_bin_goes_to_the_bus,
               a_shortcut_hides_a_device_and_says_so, the_standing_launcher_proofs_pass):
        fn()
    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
