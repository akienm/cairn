"""Proof: the installer's ensure_dev_extra carries pyproject's dev extra into the venv (ticket b3ecebdf9695).

Measured 2026-11-12: akienasus's ~/.cairn/venv had no pytest, so `cairn test` proved nothing there
until the dev extra was installed by hand. The step reads [project.optional-dependencies].dev,
asks the venv's python to import each name, and installs '<repo>[dev]' through the venv's own pip.

Nothing spawns and nothing reaches a network: ensure_dev_extra takes the runner it calls as `run`,
and these teeth pass a recording stub over a scratch venv and a scratch pyproject. The step is
imported inside each tooth, so a hollow build reds per tooth.

    python3 cairn/devices/recovery/machines/installer/proofs/test_install_carries_the_dev_extra.py
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
assert (REPO / "bin" / "cairn").exists(), f"REPO {REPO} does not hold bin/cairn"
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"b3ecebdf9695": {
    "1": "test_a_venv_missing_a_dev_module_is_offered_and_nothing_is_installed",
    "2": "test_a_run_installs_the_editable_checkout_with_dev_through_the_venvs_pip",
    "3": "test_a_venv_with_every_dev_module_reads_applied_and_runs_no_pip",
}}

_PYPROJECT = """[project]
name = "scratch"
version = "0"

[project.optional-dependencies]
dev = [
  "pytest>=7",
  # a comment between entries is not a requirement
  "wtree",
  "starlette",
]
"""


class Stub:
    """Stands in for subprocess.run: records every argv, answers `python -c import X` from `present`."""

    def __init__(self, present: set[str], pip_fixes: bool = True) -> None:
        self.present, self.pip_fixes, self.calls = set(present), pip_fixes, []

    def __call__(self, argv, **kw):
        argv = [str(a) for a in argv]
        self.calls.append(argv)
        if argv[1:2] == ["-c"]:
            mod = argv[2].split("import", 1)[1].strip()
            return subprocess.CompletedProcess(argv, 0 if mod in self.present else 1, "", "")
        if "pip" in Path(argv[0]).stem:
            if self.pip_fixes:
                self.present |= {"pytest", "wtree", "starlette"}
            return subprocess.CompletedProcess(argv, 0, "", "")
        raise AssertionError(f"unexpected call {argv}")

    def pip_calls(self) -> list[list[str]]:
        return [c for c in self.calls if "pip" in Path(c[0]).stem]


def _world() -> tuple[Path, Path]:
    venv, repo = scratch_dir("dev-extra-venv-"), scratch_dir("dev-extra-repo-")
    sub = "Scripts" if sys.platform == "win32" else "bin"
    (venv / sub).mkdir()
    exe = ".exe" if sys.platform == "win32" else ""
    (venv / sub / f"python{exe}").write_text("")
    (venv / sub / f"pip{exe}").write_text("")
    (repo / "pyproject.toml").write_text(_PYPROJECT, encoding="utf-8")
    return venv, repo


def test_a_venv_missing_a_dev_module_is_offered_and_nothing_is_installed() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_dev_extra
    venv, repo = _world()
    stub = Stub({"pytest", "starlette"})
    r = ensure_dev_extra(dry_run=True, venv=venv, repo=repo, run=stub)
    assert r["id"] == "dev_extra" and r["status"] == "offered", r
    assert "wtree" in r["detail"] and "pytest" not in r["detail"].replace("missing", ""), r
    assert not stub.pip_calls(), f"a dry run installed: {stub.pip_calls()}"


def test_a_run_installs_the_editable_checkout_with_dev_through_the_venvs_pip() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_dev_extra
    venv, repo = _world()
    stub = Stub({"pytest"})
    r = ensure_dev_extra(venv=venv, repo=repo, run=stub)
    assert r["status"] == "applied", r
    pips = stub.pip_calls()
    assert len(pips) == 1, pips
    pip = pips[0]
    assert Path(pip[0]).parent.parent == venv, f"not the venv's own pip: {pip[0]}"
    assert pip[1:] == ["install", "--editable", f"{repo}[dev]"], pip
    # a pip that exits 0 and fixes nothing is a red, not an applied
    stub2 = Stub({"pytest"}, pip_fixes=False)
    r2 = ensure_dev_extra(venv=venv, repo=repo, run=stub2)
    assert r2["status"] == "failed" and "wtree" in r2["detail"], r2


def test_a_venv_with_every_dev_module_reads_applied_and_runs_no_pip() -> None:
    from cairn.devices.recovery.machines.installer.installer import ensure_dev_extra
    venv, repo = _world()
    stub = Stub({"pytest", "wtree", "starlette"})
    r = ensure_dev_extra(venv=venv, repo=repo, run=stub)
    assert r["status"] == "already_applied", r
    assert not stub.pip_calls(), stub.pip_calls()
    assert len(stub.calls) == 3, f"expected one import probe per dev module: {stub.calls}"


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            failed.append(name)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all 3 teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
