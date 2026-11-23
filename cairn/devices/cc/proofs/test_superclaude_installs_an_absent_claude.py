#!/usr/bin/env python3
"""Proof for ticket 8219a855a7c1: superclaude.py installs Claude Code when it is absent.

Akien, 2026-11-11 (quoted at the bash cc/superclaude:461): "if claude is not installed, it should be".
The bash is retired by e179281f6eff; this proof carries the install tooth of its
test_superclaude_bare_box.py onto the Python launcher, on every box.

  1. With claude absent, --dry-run says a real launch would install it from the url (the default
     https://claude.ai/install.sh, or CAIRN_CLAUDE_INSTALLER), calls no installer, and exits 0.
  2. A real launch with claude absent looks in ~/.local/bin first (a claude found there is not
     installed over), else calls the installer with that url.
  3. An install after which claude is still not on PATH exits 127 with FAILED on stderr.
  4. _install fetches with curl or wget into sh where the launch tool says the box runs shell scripts,
     and runs the PowerShell installer where it does not.

CLAUDE_BIN names a binary no box has, so the real `which` answers absent whatever the host holds. The
installer is a seam that records its url; nothing is downloaded. The host half of tooth 4 (the live
installer URL) is a hypothesis: it is measured through the launch tool's answer, not over the network.

    bin/cairn test cairn/devices/cc/proofs/test_superclaude_installs_an_absent_claude.py
"""
from __future__ import annotations

import importlib
import os
import stat
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_MODULE = "cairn.devices.cc.superclaude"
_ABSENT = "cairn-proof-no-such-claude"
_DEFAULT_URL = "https://claude.ai/install.sh"

PROVES = {"8219a855a7c1": {
    "1": "test_dry_run_says_it_would_install_and_installs_nothing",
    "2": "test_a_real_launch_looks_in_local_bin_then_installs_from_the_url",
    "3": "test_an_install_that_leaves_claude_absent_exits_127_loudly",
    "4": "test_the_installer_follows_the_launch_tools_answer",
}}


def _sc():
    return importlib.import_module(_MODULE)


class Rig:
    def __init__(self, root: Path, installs_claude: bool = False):
        self.root = root
        self.out, self.err, self.installed, self.claude_calls = [], [], [], []
        self.installs_claude = installs_claude
        self.seams = {
            "out": self.out.append, "err": self.err.append, "host": "Testbox.lan", "cwd": str(root),
            "floor": lambda verb, stdin=None: (0, {}), "memlink": lambda cwd: "",
            "spawn": lambda unit, argv, log, cwd=None, env=None: {"ok": True, "how": "fake", "detail": ""},
            "port": lambda p: False, "claude": self._claude, "trace": lambda ev, lacks: None,
            "pid_alive": lambda pid: False, "tmux_has": lambda name: False,
            "scope_exec": lambda argv, *a, **k: self._claude(argv, k.get("env") or {}),
            "install": self._install, "repo": _REPO,
        }

    def _install(self, url, err):
        self.installed.append(url)
        if self.installs_claude:
            put_claude(self.root)

    def _claude(self, argv, env):
        self.claude_calls.append(list(argv))
        return 0

    def run(self, argv, env=None):
        e = {"HOME": str(self.root), "USERPROFILE": str(self.root), "PATH": os.environ.get("PATH", ""),
             "CLAUDE_BIN": _ABSENT}
        e.update(env or {})
        return _sc().main(list(argv), e, self.seams)


def put_claude(home: Path) -> Path:
    """Drop a runnable claude into <home>/.local/bin, the place the native installer puts it."""
    d = home / ".local" / "bin"
    d.mkdir(parents=True, exist_ok=True)
    for name in (_ABSENT, _ABSENT + ".exe"):
        p = d / name
        p.write_text("", encoding="utf-8")
        p.chmod(p.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
    return d


def rig(**kw):
    class _Cm:
        def __enter__(self_):
            self_.d = tempfile.TemporaryDirectory(prefix="sc-install-proof-")
            return Rig(Path(self_.d.name), **kw)

        def __exit__(self_, *a):
            self_.d.cleanup()
    return _Cm()


# ── 1 ────────────────────────────────────────────────────────────────────────
def test_dry_run_says_it_would_install_and_installs_nothing():
    for env, url in (({}, _DEFAULT_URL),
                     ({"CAIRN_CLAUDE_INSTALLER": "file:///proof/installer.sh"}, "file:///proof/installer.sh")):
        with rig() as r:
            rc = r.run(["--dry-run"], env)
            text = "\n".join(r.out)
            assert rc == 0, (rc, text, r.err)
            assert f"a real launch would install it from {url}" in text, text
            assert r.installed == [] and r.claude_calls == [], (r.installed, r.claude_calls)


# ── 2 ────────────────────────────────────────────────────────────────────────
def test_a_real_launch_looks_in_local_bin_then_installs_from_the_url():
    with rig() as r:                                  # claude already in ~/.local/bin: never installed over
        put_claude(r.root)
        rc = r.run(["--no-preflight"])
        assert rc == 0 and r.installed == [], (rc, r.installed, r.err)
        assert len(r.claude_calls) == 1, r.claude_calls
    for env, url in (({}, _DEFAULT_URL), ({"CAIRN_CLAUDE_INSTALLER": "file:///proof/i.sh"}, "file:///proof/i.sh")):
        with rig(installs_claude=True) as r:          # absent everywhere: the installer is called with the url
            rc = r.run(["--no-preflight"], env)
            assert rc == 0, (rc, r.err)
            assert r.installed == [url], (r.installed, url)
            assert any(url in m for m in r.err), r.err      # it says it is installing, on stderr
            assert len(r.claude_calls) == 1, r.claude_calls


# ── 3 ────────────────────────────────────────────────────────────────────────
def test_an_install_that_leaves_claude_absent_exits_127_loudly():
    with rig(installs_claude=False) as r:
        rc = r.run(["--no-preflight"])
        assert rc == 127, (rc, r.err)
        assert any("FAILED" in m and _ABSENT in m for m in r.err), r.err
        assert r.claude_calls == [], r.claude_calls


# ── 4 ────────────────────────────────────────────────────────────────────────
def test_the_installer_follows_the_launch_tools_answer():
    sc = _sc()
    calls = []
    real_run, real_which, real_runs = sc.subprocess.run, sc.shutil.which, sc.launch.runs_shell_scripts

    class _Done:
        stdout = "echo installed"

    def fake_run(argv, **kw):
        calls.append((list(argv), kw))
        return _Done()
    try:
        sc.subprocess.run = fake_run
        sc.launch.runs_shell_scripts = lambda: True
        sc.shutil.which = lambda n: "/fake/" + n if n == "curl" else None
        sc._install("https://example.test/install.sh", lambda m: None)
        assert calls[0][0][:2] == ["curl", "-fsSL"] and calls[1][0] == ["sh"], calls
        calls.clear()
        sc.shutil.which = lambda n: None                 # no curl: wget
        sc._install("https://example.test/install.sh", lambda m: None)
        assert calls[0][0][0] == "wget" and calls[1][0] == ["sh"], calls
        calls.clear()
        sc.launch.runs_shell_scripts = lambda: False     # a box that runs no shell scripts: PowerShell
        sc._install("https://example.test/install.sh", lambda m: None)
        assert len(calls) == 1 and calls[0][0][0] == "powershell", calls
        assert "install.ps1" in " ".join(calls[0][0]) and "install.sh" not in " ".join(calls[0][0]), calls
    finally:
        sc.subprocess.run, sc.shutil.which, sc.launch.runs_shell_scripts = real_run, real_which, real_runs


TEETH = [test_dry_run_says_it_would_install_and_installs_nothing,
         test_a_real_launch_looks_in_local_bin_then_installs_from_the_url,
         test_an_install_that_leaves_claude_absent_exits_127_loudly,
         test_the_installer_follows_the_launch_tools_answer]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}", flush=True)
        except Exception as e:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {e}", flush=True)
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
