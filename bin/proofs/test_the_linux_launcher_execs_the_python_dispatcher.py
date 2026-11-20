"""Proof for ticket 8b94ca4536c9 — on Linux, bin/cairn keeps its floor and execs the Python dispatcher bin/cairn.py.

Measured 2026-11-20 on akiendell: bin/cairn is 479 lines, 295 of code; lines 94-217 are the bash floor, lines 218-313
the help, lines 314-479 a bash dispatch (token fold, instance split, device and bus resolution, exec) that
bin/cairn.py (ticket 380d524e6e9c) now carries a second copy of. Outline 5.4.3.8: after the floor, the launcher execs
the venv python on bin/cairn.py, so one dispatcher serves both platforms; 5.4.3.8.1: the floor stays bash.

Every tooth runs bin/cairn as a subprocess over a scratch CAIRN_INSTANCE_ROOT and CAIRN_CLASS_ROOT. The venv is a
scratch one whose python is a recording wrapper: it appends its argv to a log, then runs the real interpreter. So
"the launcher exec'd the Python dispatcher" is READ off the log, not inferred from a result the bash dispatch
also gives. A tooth that reads the same with or without the build is not a tooth.

  1. the standing launcher proofs read green, and a typed word reached the venv python as `bin/cairn.py <word>`;
  2. a fixed list of typed addresses resolves to the same target and exit code, each through exactly one exec of
     bin/cairn.py carrying the typed argv;
  3. bin/cairn, after its floor, holds no device or bus resolution of its own: its only exec of a dispatch is the
     Python dispatcher (no `exec "$target"`, no bus mouth, no instance split);
  4. on a fresh instance root, the exec leaves the instance wiring in place, laid by bin/cairn.py before it
     dispatches (the log shows cairn.py ran, and the wiring is there).

    python3 bin/proofs/test_the_linux_launcher_execs_the_python_dispatcher.py   # exit 0 = green
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.base.script_argv import bash_script_argv  # noqa: E402
CAIRN = REPO / "bin" / "cairn"
DEV = "testing-8b94-device"
STANDING = ["bin/proofs/test_a_word_with_no_script_goes_onto_the_bus.py",
            "bin/proofs/test_cairn_command.py",
            "bin/proofs/test_cairn_instance_address.py",
            "bin/proofs/test_the_launcher_reads_the_bin_beside_the_code.py"]

PROVES = {
    "8b94ca4536c9": {
        "1": "the_standing_launcher_proofs_pass_through_the_python_dispatcher",
        "2": "typed_addresses_resolve_the_same_through_the_python_dispatcher",
        "3": "the_launcher_holds_no_dispatch_of_its_own",
        "4": "the_exec_leaves_the_instance_wiring",
    },
}

FAILURES: list[str] = []
NOTRAN: list[str] = []


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
    def __init__(self) -> None:
        from cairn.tools.scratch.scratch import scratch_dir
        self.root = scratch_dir("8b94-inst-")
        self.cls = scratch_dir("8b94-class-")
        self.venv = scratch_dir("8b94-venv-")
        _stub(self.root / DEV / "0" / "bin" / DEV, 'echo "self:$*"')
        _stub(self.root / DEV / "0" / "bin" / "hello", 'echo "instance-hello:$*"')
        _stub(self.cls / DEV / "bin" / "wave", 'echo "class-wave:$*"')
        _stub(self.cls / "cairn" / "bin" / "greet", 'echo "greet:$*"; exit 5')
        self.mouthlog = self.root / "mouth.argv"
        self.mouth = self.root / "mouth"
        _stub(self.mouth, f'printf "%s\\n" "$@" > "{self.mouthlog}"; echo "mouth answered"; exit 7')
        # the recording interpreter: one line per exec, then the real python
        self.log = self.root / "python.execs"
        sub, exe = ("Scripts", "python.exe") if sys.platform == "win32" else ("bin", "python3")
        _stub(self.venv / sub / exe, f'printf "%s" "$@" >> "{self.log}"; printf "\n" >> "{self.log}"; exec "{sys.executable}" "$@"')

    def cairn(self, *args: str) -> subprocess.CompletedProcess:
        env = {**os.environ, "CAIRN_INSTANCE_ROOT": str(self.root), "CAIRN_CLASS_ROOT": str(self.cls),
               "CAIRN_BUS_MOUTH": str(self.mouth), "CAIRN_VENV": str(self.venv)}
        return subprocess.run([*bash_script_argv(CAIRN), *args], capture_output=True, text=True, env=env, timeout=120)

    def execs(self) -> list[list[str]]:
        """One list of argv words per exec: the log separates words with 0x1f, so a word holding a
        space ('Two Words') stays one word."""
        lines = self.log.read_text().splitlines() if self.log.exists() else []
        return [ln.rstrip("").split("") for ln in lines]


def the_standing_launcher_proofs_pass_through_the_python_dispatcher() -> None:
    w = _World()
    r = w.cairn("greet", "a", "b")
    execs = w.execs()
    # the floor may fire its own backgrounded learning-block trace through the venv python; the tooth
    # counts the execs OF the dispatcher, which is what clause 3 says there is exactly one of
    py = [e for e in execs if e and e[0].endswith("cairn.py")]
    reached = len(py) == 1 and py[0][1:] == ["greet", "a", "b"]
    bad = []
    for p in STANDING:
        s = subprocess.run([sys.executable, str(REPO / p)], cwd=REPO, capture_output=True, text=True, timeout=900)
        if s.returncode != 0:
            bad.append(f"{p}: rc={s.returncode} {s.stdout[-500:]}")
    _check("the_standing_launcher_proofs_pass_through_the_python_dispatcher",
           reached and r.stdout == "greet:a b\n" and r.returncode == 5 and not bad,
           f"execs={execs!r} rc={r.returncode} out={r.stdout!r} err={r.stderr[-300:]!r} standing={' | '.join(bad)}")


# (typed argv, expected rc, expected stdout, expected stderr fragment, expected mouth argv)
_ADDRESSES = [
    (["greet", "a", "b"], 5, "greet:a b\n", "", None),
    ([DEV, "wave", "z"], 0, "class-wave:z\n", "", None),
    ([f"{DEV}.0", "hello", "q"], 0, "instance-hello:q\n", "", None),
    ([DEV.upper(), "hello", "q"], 0, "instance-hello:q\n", "", None),
    ([DEV, "zork", "Two Words"], 7, "mouth answered\n", "", [DEV, "zork", "Two Words"]),
    (["nosuchthing"], 127, "", "no such device or command: nosuchthing", None),
    ([f"{DEV}.x", "hello"], 127, "", "instance must be a number", None),
]


def typed_addresses_resolve_the_same_through_the_python_dispatcher() -> None:
    bad = []
    for argv, rc, out, err, mouth in _ADDRESSES:
        w = _World()
        r = w.cairn(*argv)
        execs = w.execs()
        py = [e for e in execs if e and e[0].endswith("cairn.py")]
        got_mouth = w.mouthlog.read_text().splitlines() if w.mouthlog.exists() else None
        ok = (r.returncode == rc and r.stdout == out and err in r.stderr and got_mouth == mouth
              and len(py) == 1 and py[0][1:] == argv)
        if not ok:
            bad.append(f"{argv}: rc={r.returncode} out={r.stdout!r} err={r.stderr[-200:]!r} mouth={got_mouth!r} execs={execs!r}")
    _check("typed_addresses_resolve_the_same_through_the_python_dispatcher", not bad, " | ".join(bad))


def the_launcher_holds_no_dispatch_of_its_own() -> None:
    text = CAIRN.read_text(encoding="utf-8")
    lines = text.splitlines()
    # the floor and help end where the typed-word handling begins; whatever follows must be the one exec
    start = next((i for i, ln in enumerate(lines) if "instance comes off the device token" in ln), len(lines))
    tail = "\n".join(lines[start:])
    forbidden = [r'exec\s+"\$target"', r"CAIRN_BUS_MOUTH", r"_class_bin=", r"device_bin=", r'exec\s+"\$CLASS_ROOT',
                 r'case\s+"\$instance"']
    hit = [p for p in forbidden if re.search(p, tail)]
    pyexec = re.findall(r"exec\s+[^\n]*cairn\.py", text)
    _check("the_launcher_holds_no_dispatch_of_its_own", not hit and len(pyexec) == 1,
           f"dispatch still in bin/cairn: {hit}; exec-of-cairn.py count={len(pyexec)}")


def the_exec_leaves_the_instance_wiring() -> None:
    w = _World()
    for d in (w.root / DEV / "0" / "bin",):
        for f in d.iterdir():
            f.unlink()
        d.rmdir()
    (w.cls / DEV / "0").mkdir(parents=True, exist_ok=True)
    r = w.cairn(DEV, "wave", "z")
    py = [e for e in w.execs() if e and e[0].endswith("cairn.py")]
    wired = (w.root / DEV / "0" / "bin").exists()
    _check("the_exec_leaves_the_instance_wiring", len(py) == 1 and wired and r.stdout == "class-wave:z\n",
           f"execs={w.execs()!r} wired={wired} rc={r.returncode} out={r.stdout!r} err={r.stderr[-300:]!r}")


def main() -> int:
    for fn in (the_standing_launcher_proofs_pass_through_the_python_dispatcher,
               typed_addresses_resolve_the_same_through_the_python_dispatcher,
               the_launcher_holds_no_dispatch_of_its_own, the_exec_leaves_the_instance_wiring):
        fn()
    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
