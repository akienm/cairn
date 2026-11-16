"""Proof for ticket e9dc9c77f30d: the artifact hooks install LF on every box.

akiendell_cc_0 measured 2026-11-16 that cairn/tools/artifact/hooks/pre-commit is CRLF in that
box's working tree (core.autocrlf=true, no .gitattributes rule), and that install-hook's
shutil.copyfile would lay it into .git/hooks as is, where bash refuses it on $'\\r'. Two halves
fix it, because an attribute does not rewrite a working copy already checked out CRLF:

1  git check-attr reports eol: lf for every file under cairn/tools/artifact/hooks/;
2  a scratch clone with core.autocrlf=true, of a repo holding this tree's .gitattributes and the
   artifact hooks, checks every hook out with no CR byte (git converts on checkout on Linux too);
3  install-hook and install-title-hook, handed CRLF sources, lay pre-commit, pre-merge-commit and
   commit-msg with no CR byte, each equal to its source folded to LF, and executable.

Run bare:  PYTHONPATH=. python3 cairn/tools/artifact/proofs/test_the_artifact_hooks_install_lf_on_every_box.py
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

TID = "e9dc9c77f30d"
PROVES = {TID: {
    "1": "test_every_artifact_hook_is_attributed_lf",
    "2": "test_an_autocrlf_checkout_gives_the_hooks_no_cr",
    "3": "test_the_installer_lays_lf_from_crlf_sources",
}}

FAILURES: list[str] = []
HOOKS_REL = "cairn/tools/artifact/hooks"
HOOKS = REPO / HOOKS_REL


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  [{sys.platform}] {name}  — {detail[:400]}")
    if not ok:
        FAILURES.append(name)


def _env(home: Path) -> dict:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update({"HOME": str(home), "GIT_CONFIG_NOSYSTEM": "1", "GIT_TERMINAL_PROMPT": "0"})
    return env


def _git(cwd: Path, env: dict, *args: str) -> subprocess.CompletedProcess:
    r = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=env)
    if r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.strip()[-300:]}")
    return r


def _names() -> list[str]:
    return sorted(p.name for p in HOOKS.iterdir() if p.is_file())


def test_every_artifact_hook_is_attributed_lf(tmp: Path) -> None:
    name = PROVES[TID]["1"]
    r = _git(REPO, _env(tmp), "check-attr", "eol", "--", *[f"{HOOKS_REL}/{n}" for n in _names()])
    eols = {ln.split(": ")[0].rsplit("/", 1)[-1]: ln.split(": ")[-1] for ln in r.stdout.splitlines()}
    check(name, bool(eols) and set(eols.values()) == {"lf"}, f"eol {eols}")


def test_an_autocrlf_checkout_gives_the_hooks_no_cr(tmp: Path) -> None:
    name = PROVES[TID]["2"]
    env = _env(tmp)
    src = tmp / "src"
    (src / HOOKS_REL).mkdir(parents=True)
    shutil.copyfile(REPO / ".gitattributes", src / ".gitattributes")
    for n in _names():
        (src / HOOKS_REL / n).write_bytes((HOOKS / n).read_bytes().replace(b"\r\n", b"\n"))
    _git(src, env, "init", "-q")
    _git(src, env, "add", "-A")
    _git(src, env, "-c", "user.email=proof@cairn", "-c", "user.name=proof", "commit", "-q", "--no-verify", "-m", "fixture")
    dst = tmp / "clone"
    subprocess.run(["git", "-c", "core.autocrlf=true", "clone", "-q", "--config", "core.autocrlf=true", str(src), str(dst)],
                   capture_output=True, env=env, check=True)
    cr = {n: b"\r" in (dst / HOOKS_REL / n).read_bytes() for n in _names()}
    check(name, bool(cr) and not any(cr.values()), f"CR in checkout {cr}")


def test_the_installer_lays_lf_from_crlf_sources(tmp: Path) -> None:
    name = PROVES[TID]["3"]
    root = tmp / "CairnCommons"
    root.mkdir()
    _git(root, _env(tmp), "init", "-q")
    crlf = tmp / "crlf"
    crlf.mkdir()
    for n in _names():
        (crlf / n).write_bytes((HOOKS / n).read_bytes().replace(b"\r\n", b"\n").replace(b"\n", b"\r\n"))
    os.environ["CAIRN_ARTIFACT_ROOTS"] = json.dumps({"CairnCommons": str(root), "parked": str(tmp / "parked")})
    from cairn.tools.artifact import __main__ as M
    M._HOOK_SRC, M._TITLE_HOOK_SRC = crlf / "pre-commit", crlf / "commit-msg"
    if hasattr(M, "_MERGE_HOOK_SRC"):
        M._MERGE_HOOK_SRC = crlf / "pre-merge-commit"
    M._install_hook("CairnCommons")
    M._install_title_hook("CairnCommons")
    got = {}
    for n in _names():
        laid = root / ".git" / "hooks" / n
        got[n] = laid.exists() and laid.read_bytes() == (crlf / n).read_bytes().replace(b"\r\n", b"\n") \
            and os.access(laid, os.X_OK)
    check(name, bool(got) and all(got.values()), f"laid LF and executable {got}")


TEETH = (test_every_artifact_hook_is_attributed_lf,
         test_an_autocrlf_checkout_gives_the_hooks_no_cr,
         test_the_installer_lays_lf_from_crlf_sources)


def main() -> int:
    for tooth in TEETH:
        with tempfile.TemporaryDirectory(prefix="cairn-artifact-hooks-lf-proof-") as d:
            try:
                tooth(Path(d))
            except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
                check(tooth.__name__, False, f"{type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else f'RED — {len(FAILURES)} failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
