#!/usr/bin/env python3
"""Proof for ticket 8610b4aa2477: recovery's floor (verify, apply, report) runs from Python and
returns its findings as data.

Measured 2026-11-22 on akiendell: `cairn superclaude` resolved bash to WSL's bash.exe; the preflight
(cairn_bootstrap_verify/apply/report in bootstrap.sh) lives in that bash, so a Python superclaude
(child 3 of c3cd232ba0cf) has no floor to call.

  1. verify() over scratch venv states returns [] for a good venv and, for each broken state, one
     finding whose text leads with the bash's own words.
  2. apply() over an absent venv brings the floor up (verify() is then empty), and over a half-built
     venv (no pip) rebuilds it so pip runs.
  3. report([]) returns '' and report(findings) writes preflight.json with floor_up false and
     returns text naming each finding.
  4. `python floor.py verify` prints the findings as JSON and exits 0 with none, 1 with some, from a
     cwd that is not the repo root.
  5. floor.py names no os.name, sys.platform, platform.system, the word bash, or a sudo password
     flag; it asks the launch tool its OS questions.

Teeth that need a native Windows run (the POSIX-names finding) print UNMEASURED off nt; a tooth whose
install needs a network prints UNMEASURED without one. A state, never a green. The module is imported
inside each tooth, so an absent build reds the tooth, not the run.

    bin/cairn test cairn/devices/recovery/proofs/test_recovery_s_floor_runs_from_python.py
"""
from __future__ import annotations

import contextlib
import importlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_MODULE = "cairn.devices.recovery.floor"
_FLOOR = _REPO / "cairn" / "devices" / "recovery" / "floor.py"
_LAUNCH = "cairn.devices.system_rackmount.tools.launch.launch"

PROVES = {"8610b4aa2477": {
    "1": "test_verify_names_each_broken_state_in_the_bash_words",
    "2": "test_apply_brings_an_absent_venv_up_and_rebuilds_a_half_built_one",
    "3": "test_report_is_silent_when_up_and_writes_preflight_when_not",
    "4": "test_the_cli_prints_json_findings_and_its_exit_says_the_floor",
    "5": "test_floor_asks_the_launch_tool_and_tests_no_os_itself",
}}


class Unmeasured(Exception):
    """The tooth cannot run here; that is a state, never a green."""


def _floor():
    return importlib.import_module(_MODULE)


def _launch():
    return importlib.import_module(_LAUNCH)


@contextlib.contextmanager
def _scratch(**env):
    """A scratch dir as HOME, with CAIRN_VENV and PYTHONPATH set the way a launch sets them."""
    root = Path(tempfile.mkdtemp(prefix="floor-proof-"))
    keys = ["HOME", "USERPROFILE", "CAIRN_VENV", "PYTHONPATH", "PATH"]
    saved = {k: os.environ.get(k) for k in keys}
    try:
        os.environ["HOME"] = os.environ["USERPROFILE"] = str(root)
        os.environ["CAIRN_VENV"] = str(root / "venv")
        os.environ.pop("PYTHONPATH", None)
        for k, v in env.items():
            os.environ[k] = v
        yield root
    finally:
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        shutil.rmtree(root, ignore_errors=True)


def _vpy(venv: Path) -> Path:
    for name in ("python3", "python3.exe", "python.exe", "python"):
        p = _launch().venv_bin_dir(venv) / name
        if p.is_file():
            return p
    raise AssertionError(f"no interpreter under {_launch().venv_bin_dir(venv)}")


def _bare_venv(venv: Path, pip: bool = False) -> Path:
    args = [sys.executable, "-m", "venv"] + ([] if pip else ["--without-pip"]) + [str(venv)]
    got = subprocess.run(args, capture_output=True, text=True, timeout=300)
    assert got.returncode == 0, f"could not make a scratch venv: {got.stderr}"
    return _vpy(venv)


def _purelib(vpy: Path) -> Path:
    out = subprocess.run([str(vpy), "-c", "import sysconfig;print(sysconfig.get_path('purelib'))"],
                         capture_output=True, text=True, timeout=60)
    return Path(out.stdout.strip())


def _good_venv(floor, venv: Path, root: Path, repo_pth: Path = _REPO, psycopg2: bool = True) -> Path:
    """A venv that imports this checkout's cairn, has a psycopg2, and carries the current stamp."""
    vpy = _bare_venv(venv)
    lib = _purelib(vpy)
    (lib / "cairn_floor_proof.pth").write_text(str(repo_pth) + "\n", encoding="utf-8")
    if psycopg2:
        (lib / "psycopg2.py").write_text("__version__ = 'proof'\n", encoding="utf-8")
    floor.stamp_file(venv).write_text(floor.stamp_want(), encoding="utf-8")
    if _launch().venv_bin_dir(venv).name == "Scripts":
        err = floor.lay_posix_names(venv)
        if err:
            raise Unmeasured(f"this box would not lay the POSIX names: {err}")
    return vpy


def _lead(findings, lead: str) -> bool:
    return len(findings) == 1 and findings[0]["text"].startswith(lead) and findings[0].get("code")


# ── 1 ────────────────────────────────────────────────────────────────────────
def test_verify_names_each_broken_state_in_the_bash_words():
    floor = _floor()
    with _scratch() as root:
        venv = root / "venv"
        got = floor.verify()
        assert _lead(got, "VENV ABSENT"), f"absent venv: {got}"

        _good_venv(floor, venv, root)
        assert floor.verify() == [], f"a good venv read as broken: {floor.verify()}"

        floor.stamp_file(venv).write_text("not the stamp\n", encoding="utf-8")
        got = floor.verify()
        assert _lead(got, "FLOOR IS STALE"), f"stale stamp: {got}"
        shutil.rmtree(venv)

        # import root broken: a venv with no .pth to this checkout.
        _bare_venv(venv)
        got = floor.verify()
        assert _lead(got, "IMPORT ROOT BROKEN"), f"no import root: {got}"
        shutil.rmtree(venv)

        # import root elsewhere: a .pth to a different tree that has its own `cairn`.
        other = root / "other"
        (other / "cairn").mkdir(parents=True)
        (other / "cairn" / "__init__.py").write_text("", encoding="utf-8")
        _good_venv(floor, venv, root, repo_pth=other)
        got = floor.verify()
        assert _lead(got, "IMPORT ROOT POINTS ELSEWHERE"), f"another checkout: {got}"
        shutil.rmtree(venv)

        # psycopg2 missing.
        _good_venv(floor, venv, root, psycopg2=False)
        got = floor.verify()
        assert _lead(got, "psycopg2 MISSING"), f"no psycopg2: {got}"
        shutil.rmtree(venv)

        # no runnable python on PATH at all.
        empty = root / "empty"
        empty.mkdir()
        os.environ["PATH"] = str(empty)
        got = floor.verify()
        assert _lead(got, "NO RUNNABLE PYTHON 3"), f"empty PATH: {got}"
    if _launch().venv_bin_dir(Path("x")).name != "Scripts":
        raise Unmeasured("the POSIX-names finding (WINDOWS VENV LACKS ITS POSIX NAMES) is measured on nt only; "
                         "every other state above was measured")


# ── 2 ────────────────────────────────────────────────────────────────────────
def test_apply_brings_an_absent_venv_up_and_rebuilds_a_half_built_one():
    floor = _floor()
    with _scratch() as root:
        venv = root / "deep" / "venv"                      # parent absent too
        os.environ["CAIRN_VENV"] = str(venv)
        left = floor.apply()
        assert isinstance(left, list), f"apply returned {type(left).__name__}, not findings"
        no_net = [f for f in left if f["text"].startswith("EDITABLE INSTALL FAILED")]
        if no_net:
            raise Unmeasured(f"the editable install could not run here: {no_net[0]['text'][:200]}")
        assert left == [], f"apply left findings: {left}"
        assert floor.verify() == [], f"the floor is not up after apply: {floor.verify()}"
        shutil.rmtree(venv)

        _bare_venv(venv, pip=False)                        # half-built: an interpreter, no pip
        floor.apply()
        got = subprocess.run([str(_vpy(venv)), "-m", "pip", "--version"], capture_output=True, text=True, timeout=120)
        assert got.returncode == 0, f"the half-built venv still has no pip: {got.stderr}"


# ── 3 ────────────────────────────────────────────────────────────────────────
def test_report_is_silent_when_up_and_writes_preflight_when_not():
    floor = _floor()
    with _scratch() as root:
        assert floor.report([]) == "", "a floor that is up must report nothing"
        up = json.loads((root / ".cairn" / "logs" / "preflight.json").read_text(encoding="utf-8"))
        assert up["floor_up"] is True and up["findings"] == [], up

        found = [{"code": "venv-absent", "text": "VENV ABSENT at /x (proof one)"},
                 {"code": "stale", "text": "FLOOR IS STALE — proof two"}]
        text = floor.report(found)
        for f in found:
            assert f["text"] in text, f"the report does not name {f['code']}: {text!r}"
        down = json.loads((root / ".cairn" / "logs" / "preflight.json").read_text(encoding="utf-8"))
        assert down["floor_up"] is False and down["findings"] == [f["text"] for f in found], down


# ── 4 ────────────────────────────────────────────────────────────────────────
def test_the_cli_prints_json_findings_and_its_exit_says_the_floor():
    with _scratch() as root:
        env = dict(os.environ, PYTHONPATH=str(_REPO))

        def run(*verb):
            return subprocess.run([sys.executable, str(_FLOOR), *verb], cwd=str(root), env=env,
                                  capture_output=True, text=True, timeout=300)

        bad = run("verify")
        assert bad.returncode == 1, f"absent venv exited {bad.returncode}: {bad.stdout!r} {bad.stderr!r}"
        data = json.loads(bad.stdout)
        assert len(data) == 1 and data[0]["text"].startswith("VENV ABSENT"), data

        _good_venv(_floor(), root / "venv", root)
        good = run("verify")
        assert good.returncode == 0 and json.loads(good.stdout) == [], (good.returncode, good.stdout, good.stderr)

        assert run("nonsense").returncode == 2, "an unknown verb must exit 2"


# ── 5 ────────────────────────────────────────────────────────────────────────
def test_floor_asks_the_launch_tool_and_tests_no_os_itself():
    assert _FLOOR.is_file(), f"{_FLOOR} is absent"
    text = _FLOOR.read_text(encoding="utf-8")
    bad = [t for t in ("os.name", "sys.platform", "platform.system", "bash", "sudo -S", "sudo -s")
           if t in text]
    assert not bad, f"floor.py names {bad}"
    assert "system_rackmount.tools.launch" in text, "floor.py does not ask the launch tool"


TEETH = [test_verify_names_each_broken_state_in_the_bash_words,
         test_apply_brings_an_absent_venv_up_and_rebuilds_a_half_built_one,
         test_report_is_silent_when_up_and_writes_preflight_when_not,
         test_the_cli_prints_json_findings_and_its_exit_says_the_floor,
         test_floor_asks_the_launch_tool_and_tests_no_os_itself]


def main() -> int:
    failed = unmeasured = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}", flush=True)
        except Unmeasured as e:
            unmeasured += 1
            print(f"  UNMEASURED  {t.__name__}: {e}", flush=True)
        except Exception as e:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {e}", flush=True)
    print(f"\n{len(TEETH) - failed - unmeasured}/{len(TEETH)} teeth green, {unmeasured} unmeasured")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
