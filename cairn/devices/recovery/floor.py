"""recovery's floor from Python — verify, apply, report; findings returned as data.

Ticket 8610b4aa2477 (child 2 of c3cd232ba0cf). Charter: cairn/devices/recovery/intention+why.json.
Ported from bootstrap.sh (cairn_bootstrap_verify/apply/report and its helpers) so a Python superclaude
runs the preflight with no shell. Outline 10.3.2.1 and 5.4.3.8; the finding text is the old text.

A finding is ``{"code": <slug>, "text": <what a fixer needs on the first report>}``. verify() returns the
findings (empty = the floor is up) and fixes nothing; apply() repairs and returns the findings that
survived; report(findings) writes ~/.cairn/logs/preflight.json and returns the text handed to Claude
Code (empty when the floor is up: the tool is silent when it works). None of them raises: a failure is
a finding, because the launch must always reach Claude Code (the rescue ethos, recovery charter).

RULE 1: device cc may not import this module, so the door is the command line:
``python floor.py verify|apply|report`` prints JSON and exits 0 when the floor is up, 1 when not, 2 for
an unknown verb. ``report`` reads the findings as a JSON list on stdin and prints
``{"floor_up", "text"}``. The module puts its own repo root on sys.path, so the command runs from any
cwd and before the venv exists.

Every OS answer comes from the system device's launch tool (venv_bin_dir, elevation); this module
tests no OS itself. The probe that measures ``import cairn`` runs from the filesystem root with
PYTHONPATH removed, because importing from the repo root proves nothing: that is the accident the
floor exists to stop relying on.
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[3]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from cairn.devices.system_rackmount.tools.launch.launch import elevation, venv_bin_dir  # noqa: E402
from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs  # noqa: E402

_HOST_PYTHONS = ("python3", "python", "py")
_VENV_NAMES = ("python3", "python3.exe", "python.exe", "python")


# ── the small answers ────────────────────────────────────────────────────────
def _finding(code: str, text: str) -> dict:
    return {"code": code, "text": text}


def _home() -> Path:
    return Path(os.environ.get("HOME") or os.environ.get("USERPROFILE") or Path.home())


def venv_dir() -> Path:
    """The venv: $CAIRN_VENV, else ~/.cairn/venv (instance-space, never the repo)."""
    return Path(os.environ.get("CAIRN_VENV") or (_home() / ".cairn" / "venv"))


def _log(line: str) -> None:
    """One line to ~/.cairn/logs/boot/floor.log, the trail the reported-but-unfixed probe reads."""
    try:
        d = _home() / ".cairn" / "logs" / "boot"
        d.mkdir(parents=True, exist_ok=True)
        with open(d / "floor.log", "a", encoding="utf-8") as fh:
            fh.write(f"{datetime.datetime.now().isoformat(timespec='seconds')} floor: {line}\n")
    except OSError:
        pass


def _run(args, cwd=None, env=None, timeout=900, stdin=None) -> tuple:
    """Run a command; (returncode, stdout+stderr). A command that will not start is rc 127, never a raise."""
    try:
        got = subprocess.run([str(a) for a in args], cwd=cwd, env=env, input=stdin, capture_output=False,
                             stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                             encoding="utf-8", errors="replace", timeout=timeout, **windowless_kwargs())
        return got.returncode, (got.stdout or "").strip()
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s: {args[0]}"
    except OSError as e:
        return 127, f"{type(e).__name__}: {e}"


def host_python() -> str | None:
    """The HOST interpreter that builds the venv: the first of python3, python, py that RUNS and is
    Python 3 (measured 2026-11-13: on a fresh Windows box python3 is the Store stub, exit 49)."""
    for name in _HOST_PYTHONS:
        exe = shutil.which(name)
        if exe and _run([exe, "-c", "import sys; sys.exit(0 if sys.version_info[0] == 3 else 1)"], timeout=60)[0] == 0:
            return exe
    return None


def venv_python(venv: Path) -> Path:
    """The venv's interpreter wherever the host keeps it; the expected path when none exists yet."""
    d = venv_bin_dir(venv)
    for name in _VENV_NAMES:
        if (d / name).is_file():
            return d / name
    return d / "python3"


def stamp_file(venv: Path) -> Path:
    return Path(venv) / ".cairn-stamp"


def stamp_want() -> str:
    """What a floor built now would stamp: repo root, python version, pyproject's hash. The stamp gates
    only the EXPENSIVE half (a rebuild); a matching stamp over a broken venv is a lie (Law 3), so verify
    also really imports."""
    hpy = host_python()
    version = _run([hpy, "-V"], timeout=60)[1] if hpy else ""
    try:
        digest = hashlib.sha256((_ROOT / "pyproject.toml").read_bytes()).hexdigest()
    except OSError:
        digest = ""
    return f"{_ROOT}\n{version}\n{digest}\n"


def _has_posix_names(venv: Path) -> bool:
    link = Path(venv) / "bin"
    return (link / "python3").is_file() or (link / "python3.exe").is_file()


def lay_posix_names(venv: Path) -> str | None:
    """Give a venv whose executables live in Scripts the POSIX names the shell launchers use:
    Scripts/python3.exe and bin -> Scripts. Nothing to do where the venv already keeps bin. None when it
    holds afterwards, else why it did not. (Readers remain: cairn/devices/librarian/0/bin/librarian and
    bin/cairn do `PATH=$CAIRN_VENV/bin; exec python3`; ticket 8610b4aa2477 measured.)"""
    venv = Path(venv)
    d = venv_bin_dir(venv)
    if d.name != "Scripts":
        return None
    exe = d / "python.exe"
    if not exe.is_file():
        return f"{exe} is absent"
    try:
        if not (d / "python3.exe").exists():
            shutil.copy2(exe, d / "python3.exe")
        if not (venv / "bin").exists():
            os.symlink("Scripts", venv / "bin", target_is_directory=True)
    except OSError as e:
        return f"{type(e).__name__}: {e}"
    return None if _has_posix_names(venv) else f"{venv / 'bin'} does not hold python3 after the link"


# ── verify — re-runnable, measures, repairs nothing ─────────────────────────
def verify() -> list:
    try:
        return _verify()
    except Exception as e:  # noqa: BLE001 — the launch must reach Claude Code
        return [_finding("floor-crashed", f"THE FLOOR PROBE CRASHED — {type(e).__name__}: {e}. This is a defect in cairn/devices/recovery/floor.py, not in the box.")]


def _verify() -> list:
    venv = venv_dir()
    vpy = venv_python(venv)
    pip = f"{venv_bin_dir(venv) / 'pip'} install -e {_ROOT}"
    _log(f"verify: begin — venv={venv} root={_ROOT}")

    if host_python() is None:
        _log("verify: FAIL no-python3")
        return [_finding("no-python", f"NO RUNNABLE PYTHON 3 ON PATH (tried {', '.join(_HOST_PYTHONS)}) — nothing below can be measured. PATH={os.environ.get('PATH', '')}")]

    if not vpy.is_file():
        _log(f"verify: FAIL venv-absent — {vpy} is not a file")
        return [_finding("venv-absent", f"VENV ABSENT at {venv} (no {vpy}). Nothing is installed; `cairn` imports only from the repo root, and only by cwd accident. Repair: apply (python {_ROOT / 'cairn/devices/recovery/floor.py'} apply), or `python -m venv {venv}` then `{pip}`.")]

    # The real measurement: does the import root resolve from a cwd that is NOT the repo?
    probe_env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    rc, out = _run([vpy, "-c", "import cairn, sys; print(cairn.__file__)"], cwd=str(_ROOT.anchor), env=probe_env, timeout=120)
    _log(f"verify: probe import-cairn-from-root -> rc={rc} out={out.replace(chr(10), ' | ')}")
    if rc != 0:
        return [_finding("import-broken", f"IMPORT ROOT BROKEN — `{vpy} -c 'import cairn'` run from {_ROOT.anchor} exited {rc}. Output: {out.replace(chr(10), ' | ')}. The venv exists but the editable install is missing or points elsewhere. Repair: {pip}")]
    try:
        here = _ROOT.resolve() in Path(out.splitlines()[-1]).resolve().parents
    except (OSError, IndexError):
        here = False
    if not here:
        _log(f"verify: FAIL import-points-elsewhere — {out}")
        return [_finding("import-elsewhere", f"IMPORT ROOT POINTS ELSEWHERE — `import cairn` resolves to {out} but this launcher lives under {_ROOT}. The venv is installed against a different checkout. Repair: {pip}")]

    rc, out = _run([vpy, "-c", "import psycopg2; print(psycopg2.__version__)"], cwd=str(_ROOT.anchor), env=probe_env, timeout=120)
    _log(f"verify: probe import-psycopg2 -> rc={rc} out={out.replace(chr(10), ' | ')}")
    if rc != 0:
        return [_finding("psycopg2-missing", f"psycopg2 MISSING from the venv — exited {rc}. Output: {out.replace(chr(10), ' | ')}. cairn/devices/db_domain/ imports it at module scope, so the db domain will fail far from this cause. Repair: {pip}")]

    try:
        have = stamp_file(venv).read_text(encoding="utf-8").strip()
    except OSError:
        have = ""
    if have != stamp_want().strip():
        _log("verify: FAIL stamp-mismatch — a rebuild is owed")
        return [_finding("stale", "FLOOR IS STALE — the venv works but its stamp does not match the current pyproject.toml / python / checkout path. Dependencies may have moved since it was built. Repair: apply")]

    if venv_bin_dir(venv).name == "Scripts" and not _has_posix_names(venv):
        _log(f"verify: FAIL windows-posix-names — {venv / 'bin' / 'python3'} absent")
        return [_finding("posix-names", f"WINDOWS VENV LACKS ITS POSIX NAMES — {venv / 'bin' / 'python3'} does not run, so every device launcher that does `PATH=$CAIRN_VENV/bin:$PATH; exec python3` falls through to the Microsoft Store stub (exit 49). Repair: apply (lays Scripts/python3.exe and bin -> Scripts)")]

    _log("verify: OK floor is up")
    return []


# ── apply — replayable, brings the floor up, never fatal ────────────────────
def apply() -> list:
    try:
        return _apply()
    except Exception as e:  # noqa: BLE001
        return [_finding("floor-crashed", f"THE FLOOR REPAIR CRASHED — {type(e).__name__}: {e}. This is a defect in cairn/devices/recovery/floor.py, not in the box.")]


def _sudo_prefix() -> list | None:
    """The sudo command that never prompts, or None: only where the launch tool says elevation holds."""
    how = elevation().get("how")
    if how == "passwordless":
        return ["sudo", "-n"]
    if how == "password-held" and os.environ.get("SUDO_ASKPASS"):
        return ["sudo", "-A"]
    return None


def _apply() -> list:
    findings: list = []
    venv = venv_dir()
    vpy = venv_python(venv)
    _log("apply: begin — the floor was not up")

    hpy = host_python()
    if hpy is None:
        return [_finding("cannot-repair", f"CANNOT REPAIR — no runnable python 3 on PATH (tried {', '.join(_HOST_PYTHONS)}) to build a venv with. This is below Cairn's floor; it needs a host fix (apt install python3; on Windows: winget install Python.Python.3.14) before anything here can run.")]

    # A half-built venv is not a venv (measured 2026-11-11): an interpreter with no pip is rebuilt with
    # --clear, never installed into. So is one whose interpreter was upgraded away (dangling link).
    rebuild = False
    if vpy.is_file() and _run([vpy, "-m", "pip", "--version"], timeout=120)[0] != 0:
        _log(f"apply: step half-built-venv — {vpy} exists but has no pip; rebuilding with --clear")
        rebuild = True
    if not vpy.is_file() and (venv / "pyvenv.cfg").exists():
        _log(f"apply: step stale-venv — {venv} exists but {vpy} does not run; rebuilding with --clear")
        rebuild = True

    if not vpy.is_file() or rebuild:
        venv.parent.mkdir(parents=True, exist_ok=True)   # `-m venv` makes no intermediate directories
        make = [hpy, "-m", "venv"] + (["--clear"] if rebuild else []) + [str(venv)]
        rc, out = _run(make, timeout=600)
        _log(f"apply: step create-venv -> rc={rc} out={out.replace(chr(10), ' | ')}")
        if rc != 0 and "ensurepip" in out and shutil.which("apt-get"):
            apt = ["env", "DEBIAN_FRONTEND=noninteractive", "apt-get"]
            pre = _sudo_prefix()
            if pre is None:
                apt_rc, apt_out = 1, ""
            else:
                apt_rc, apt_out = _run(pre + apt + ["install", "-y", "python3-venv"], timeout=600)
                if apt_rc != 0:
                    _run(pre + apt + ["update"], timeout=600)
                    apt_rc, apt_out = _run(pre + apt + ["install", "-y", "python3-venv"], timeout=600)
            _log(f"apply: step apt-python3-venv -> rc={apt_rc} out={' | '.join(apt_out.splitlines()[-3:])}")
            if apt_rc == 0:
                rc, out = _run([hpy, "-m", "venv", "--clear", str(venv)], timeout=600)
                _log(f"apply: step create-venv-retry -> rc={rc} out={out.replace(chr(10), ' | ')}")
            else:
                findings.append(_finding("venv-not-installable", f"PYTHON3-VENV NOT INSTALLABLE — the venv create reported ensurepip missing, and `sudo apt-get install -y python3-venv` exited {apt_rc}: {' | '.join(apt_out.splitlines()[-3:])}. sudo needs a password this launch does not hold, or apt is offline. Repair: sudo apt-get install -y python3-venv, then apply."))
        if rc != 0:
            findings.append(_finding("venv-create-failed", f"VENV CREATE FAILED — `{hpy} -m venv {venv}` exited {rc}. Output: {out.replace(chr(10), ' | ')}. Read that output first; candidates if it is unclear: ensurepip absent (apt install python3-venv), the path not writable, or the disk full."))
            return findings
        vpy = venv_python(venv)

    # --editable: the import root must FOLLOW the working tree, not snapshot it (Law 7).
    rc, out = _run([vpy, "-m", "pip", "install", "--quiet", "--editable", str(_ROOT)],
                  env=dict(os.environ, PIP_CACHE_DIR=str(_home() / ".cairn" / "cache" / "pip")), timeout=1800)
    _log(f"apply: step editable-install -> rc={rc} out={out.replace(chr(10), ' | ')}")
    if rc != 0:
        findings.append(_finding("editable-install-failed", f"EDITABLE INSTALL FAILED — `{vpy} -m pip install -e {_ROOT}` exited {rc}. Output: {out.replace(chr(10), ' | ')}. If this is a network failure the box is offline and the floor cannot be built from PyPI; the venv itself is fine and the repo-root cwd path still works."))
        return findings

    err = lay_posix_names(venv)
    if err:
        findings.append(_finding("posix-names-not-laid", f"WINDOWS POSIX NAMES NOT LAID — could not create {venv / 'Scripts' / 'python3.exe'} and/or the {venv / 'bin'} -> Scripts link ({err}). Device launchers will reach the Microsoft Store stub. Check that {venv} is writable and that symlinks are allowed (an elevated shell, or Developer Mode)."))
        _log("apply: step windows-posix-names -> FAIL")
        return findings

    # Stamp LAST and only on success: a stamp written before the install would mark a floor never laid.
    try:
        stamp_file(venv).write_text(stamp_want(), encoding="utf-8")
    except OSError as e:
        _log(f"apply: stamp not written: {e}")
    left = verify()
    _log(f"apply: end -> {len(left)} finding(s) (0 = the floor is up after repair)")
    return left


# ── report — what reaches Claude ────────────────────────────────────────────
def report(findings: list) -> str:
    """Write ~/.cairn/logs/preflight.json (durable, forensic) and return the text for
    --append-system-prompt. Empty when the floor is up."""
    findings = list(findings or [])
    logdir = _home() / ".cairn" / "logs"
    try:
        logdir.mkdir(parents=True, exist_ok=True)
        (logdir / "preflight.json").write_text(json.dumps({
            "component": "cairn/devices/recovery/floor.py",
            "measured_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "venv": str(venv_dir()),
            "repo_root": str(_ROOT),
            "floor_up": not findings,
            "findings": [f["text"] for f in findings],
        }, indent=2), encoding="utf-8")
    except OSError as e:
        _log(f"report: preflight.json not written: {e}")
    _log(f"report: findings={len(findings)} floor_up={'yes' if not findings else 'no'}")
    for f in findings:
        _log(f"report: unfixed — {f['text']}")
    if not findings:
        return ""
    lines = ["CAIRN PREFLIGHT — the launcher tried to bring the floor up and could not finish.",
             "These are MEASURED at launch (cairn/devices/recovery/floor.py), not guesses.",
             f"Full record: {logdir / 'preflight.json'}  ·  re-measure: python {Path(__file__).resolve()} verify",
             ""]
    lines += [f"  - {f['text']}" for f in findings]
    lines += ["", f"Until these are fixed, python3 outside {_ROOT} cannot import cairn."]
    return "\n".join(lines)


# ── the command line: recovery's face to device cc (RULE 1) ──────────────────
def main(argv: list | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    verb = argv[0] if argv else ""
    if verb == "verify":
        findings = verify()
        print(json.dumps(findings))
        return 1 if findings else 0
    if verb == "apply":
        findings = apply()
        print(json.dumps(findings))
        return 1 if findings else 0
    if verb == "report":
        try:
            given = json.loads(sys.stdin.read() or "[]")
        except ValueError as e:
            print(json.dumps({"error": f"stdin is not a JSON list of findings: {e}"}))
            return 2
        text = report(given)
        print(json.dumps({"floor_up": not given, "text": text}))
        return 1 if given else 0
    print(json.dumps({"error": "usage: floor.py verify|apply|report", "got": verb}))
    return 2


if __name__ == "__main__":
    sys.exit(main())
