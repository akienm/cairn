#!/usr/bin/env python3
"""Proof for ticket 1941e93b25a3: superclaude is Python (cairn/devices/cc/superclaude.py), so no
bash is in the launch path.

Measured 2026-11-22 on akiendell: `cairn superclaude` exited 127 silently, because where.exe lists
WSL's bash.exe before Git Bash, which is not on PATH. The launcher is 882 lines of bash.

  1. --dry-run prints the resolved context state and claude command with the bash's semantics.
  2. A held instance (a live loop.pid) moves to the next free one: a number counts up, a word takes _N.
  3. The preflight runs floor.py verify, then apply on a miss, then report; its text rides
     --append-system-prompt, nothing when the floor is up; --no-preflight skips it and is traced.
  4. The ground loop and web server start through launch.service_spawn, neither under --dry-run, the
     web server not when port 80 listens or CAIRN_HOME_HOST names another box.
  5. The restart loop: RESTART relaunches with --continue, RESTART_FRESH clean, both consumed by a
     move; DO_NOT_RESTART wins and stays; loop.pid names the loop.
  6. claude is spawned in this console: no capture, no creation flags.
  7. The module text has no os.name, sys.platform, platform.system, bash, sudo password flag or
     password prompt, and it never elevates.
  8. claude starts through the launch tool's memory scope: MemoryHigh 6G, MemoryMax 8G, MemorySwapMax 1G.

The module is imported inside each tooth and its seams (the `seams` dict main() takes) are injected, so
an absent build reds the tooth, not the run.

    bin/cairn test cairn/devices/cc/proofs/test_superclaude_runs_from_python.py
"""
from __future__ import annotations

import contextlib
import importlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_MODULE = "cairn.devices.cc.superclaude"
_FILE = _REPO / "cairn" / "devices" / "cc" / "superclaude.py"

PROVES = {"1941e93b25a3": {
    "1": "test_dry_run_resolves_the_context_switch_like_the_bash",
    "2": "test_a_held_instance_moves_to_the_next_free_one",
    "3": "test_the_preflight_runs_floor_verify_apply_report_and_its_text_rides_the_prompt",
    "4": "test_services_start_through_the_launch_tool_and_never_under_dry_run",
    "5": "test_the_restart_loop_honours_the_flags",
    "6": "test_claude_is_spawned_in_this_console",
    "7": "test_the_module_tests_no_os_and_never_elevates",
    "8": "test_claude_starts_under_the_memory_scope",
}}


def _sc():
    return importlib.import_module(_MODULE)


class Rig:
    """A scratch HOME and fakes for every seam; records what the launcher did."""

    def __init__(self, root: Path, **over):
        self.root = root
        self.out, self.err, self.verbs, self.spawns, self.claude_calls = [], [], [], [], []
        self.traces, self.scoped, self.alive = [], [], set()
        self.port80 = False
        self.findings = []          # what verify finds
        self.survive = []           # what apply leaves
        self.residue = ""
        self.seams = {
            "out": self.out.append, "err": self.err.append, "home": root, "host": "Testbox.lan",
            "cwd": str(root), "floor": self._floor, "memlink": lambda cwd: "",
            "which": lambda n: "/fake/" + n, "spawn": self._spawn, "port": lambda p: self.port80 and p == 80,
            "claude": self._claude, "trace": lambda ev, lacks: self.traces.append((ev, list(lacks))),
            "pid_alive": lambda pid: pid in self.alive, "tmux_has": lambda name: False,
            "scope_exec": self._scope, "repo": _REPO,
        }
        self.seams.update(over)

    def _floor(self, verb, stdin=None):
        self.verbs.append(verb)
        if verb == "verify":
            return (1 if self.findings else 0), self.findings
        if verb == "apply":
            return (1 if self.survive else 0), self.survive
        return (1 if stdin else 0), {"floor_up": not stdin, "text": self.residue if stdin else ""}

    def _spawn(self, unit, argv, log, cwd=None, env=None):
        self.spawns.append((unit, [str(a) for a in argv]))
        return {"ok": True, "how": "systemd", "detail": ""}

    def _claude(self, argv, env):
        self.claude_calls.append((list(argv), dict(env)))
        return 0

    def _scope(self, argv, mem_high, mem_max, swap_max, unit=None, log=None, env=None):
        self.scoped.append((list(argv), mem_high, mem_max, swap_max))
        self.scoped_env = dict(env or {})
        return 0

    def run(self, argv, env=None):
        e = {"HOME": str(self.root), "USERPROFILE": str(self.root)}
        e.update(env or {})
        return _sc().main(list(argv), e, self.seams)

    def text(self):
        return "\n".join(self.out)


@contextlib.contextmanager
def rig(**over):
    with tempfile.TemporaryDirectory(prefix="sc-proof-") as d:
        yield Rig(Path(d), **over)


def _line(r: Rig, prefix: str) -> str:
    got = [l for l in r.out if l.startswith(prefix)]
    assert got, f"no {prefix!r} line in:\n{r.text()}"
    return got[0]


# ── 1 ────────────────────────────────────────────────────────────────────────
def test_dry_run_resolves_the_context_switch_like_the_bash():
    sc = _sc()
    cases = [
        ([], {}, "200K (file default)", "1"),
        ([], {"CLAUDE_CODE_DISABLE_1M_CONTEXT": "1"}, "200K (environment)", "1"),
        ([], {"CLAUDE_CODE_DISABLE_1M_CONTEXT": "0"}, "1M (environment)", "0"),
        (["--1m"], {"CLAUDE_CODE_DISABLE_1M_CONTEXT": "1"}, "1M (command line --1m)", "<unset>"),
        (["--200k"], {}, "200K (command line --200k)", "1"),
        (["--no-1m"], {}, "200K (command line --200k)", "1"),
    ]
    for argv, env, state, var in cases:
        with rig() as r:
            assert r.run(["--dry-run", *argv, "--model", "m"], env) == 0
            assert _line(r, "# context:") == f"# context: {state}", (argv, env, r.text())
            assert _line(r, "# CLAUDE_CODE_DISABLE_1M_CONTEXT=") == f"# CLAUDE_CODE_DISABLE_1M_CONTEXT={var}", r.text()
            ex = _line(r, "exec ")
            for want in ("--name testbox_cc_0", "--remote-control testbox_cc_0",
                         "--dangerously-skip-permissions", "--model m"):
                assert want in ex, f"{want!r} missing from {ex!r}"
            assert "--1m" not in ex and "--200k" not in ex, "our flags were forwarded to claude"
            assert _line(r, "# CAIRN_USER=") == "# CAIRN_USER=cc0", r.text()
    was = sc.FILE_DEFAULT_200K
    try:
        sc.FILE_DEFAULT_200K = 0
        with rig() as r:
            r.run(["--dry-run"], {})
            assert "1M (unconstrained" in _line(r, "# context:"), r.text()
            assert _line(r, "# CLAUDE_CODE_DISABLE_1M_CONTEXT=").endswith("<unset>"), r.text()
    finally:
        sc.FILE_DEFAULT_200K = was


# ── 2 ────────────────────────────────────────────────────────────────────────
def test_a_held_instance_moves_to_the_next_free_one():
    with rig() as r:
        for i in ("0", "1", "builder"):
            d = r.root / ".cairn" / "launchers" / "superclaude" / i
            d.mkdir(parents=True)
            (d / "loop.pid").write_text("4242\n" if i != "builder" else "4343\n", encoding="utf-8")
        r.alive.update({4242, 4343})
        r.run(["--dry-run"])
        assert "--name testbox_cc_2 " in _line(r, "exec ") + " ", r.text()
        assert _line(r, "# CAIRN_USER=") == "# CAIRN_USER=cc2", r.text()
        assert "instance 0 is held by" in _line(r, "# moved:"), r.text()
        assert any("instance 0 is held by" in e for e in r.err), "the move must be said on stderr"
        assert _line(r, "# instance:") == "# instance: asked 0, launching 2", r.text()
    with rig() as r:
        d = r.root / ".cairn" / "launchers" / "superclaude" / "builder"
        d.mkdir(parents=True)
        (d / "loop.pid").write_text("4343\n", encoding="utf-8")
        r.alive.add(4343)
        r.run(["--dry-run", "--name", "builder"])
        assert "testbox_cc_builder_1" in _line(r, "exec "), r.text()
        assert _line(r, "# CAIRN_USER=") == "# CAIRN_USER=ccbuilder_1", r.text()
    with rig() as r:                                   # a dead pid holds nothing
        d = r.root / ".cairn" / "launchers" / "superclaude" / "0"
        d.mkdir(parents=True)
        (d / "loop.pid").write_text("4242\n", encoding="utf-8")
        r.run(["--dry-run"])
        assert "testbox_cc_0" in _line(r, "exec ") and not [l for l in r.out if l.startswith("# moved:")], r.text()


# ── 3 ────────────────────────────────────────────────────────────────────────
def test_the_preflight_runs_floor_verify_apply_report_and_its_text_rides_the_prompt():
    miss = [{"code": "venv-absent", "text": "VENV ABSENT at /x"}]
    with rig() as r:
        r.findings, r.survive, r.residue = miss, miss, "CAIRN PREFLIGHT — RESIDUE-MARKER"
        r.run(["--dry-run"])
        assert r.verbs == ["verify", "apply", "report"], r.verbs
        ex = _line(r, "exec ")
        assert "--append-system-prompt" in ex and "RESIDUE-MARKER" in ex, ex
    with rig() as r:
        r.run(["--dry-run"])
        assert r.verbs == ["verify", "report"], f"a floor that is up must not apply: {r.verbs}"
        assert "--append-system-prompt" not in _line(r, "exec "), r.text()
    with rig() as r:
        r.run(["--dry-run", "--no-preflight"])
        assert r.verbs == [], f"--no-preflight still ran the floor: {r.verbs}"
    with rig() as r:                                   # the bypass is counted, not hidden
        r.run(["--no-preflight"])
        assert r.traces and r.traces[0][0] == "send_back" and "--no-preflight" in " ".join(r.traces[0][1]), r.traces
    with rig() as r:                                   # carried-in floor findings ride the residue
        r.run(["--dry-run"], {"CAIRN_FLOOR_FINDINGS": "db is down\nno instance"})
        ex = _line(r, "exec ")
        assert "CAIRN FLOOR" in ex and "db is down" in ex, ex
    with rig() as r:                                   # a clean launch traces door_pass
        r.run([])
        assert r.traces and r.traces[0][0] == "door_pass", r.traces
    with rig() as r:                                   # nothing in the floor path may abort the launch
        def boom(verb, stdin=None):
            raise OSError("floor cannot run")
        r.seams["floor"] = boom
        assert r.run(["--dry-run"]) == 0 and "exec " in r.text(), r.text()


# ── 4 ────────────────────────────────────────────────────────────────────────
def test_services_start_through_the_launch_tool_and_never_under_dry_run():
    with rig() as r:
        r.run(["--dry-run"])
        assert r.spawns == [], f"--dry-run spawned {r.spawns}"
    with rig() as r:
        r.run([])
        units = {u: a for u, a in r.spawns}
        assert "cairn-ground-loop" in units and units["cairn-ground-loop"][-2:] == ["-m", "cairn.devices.cairn.machines.ground_loop"], r.spawns
        assert "cairn-web-server" in units and units["cairn-web-server"][-1].endswith("listener.py"), r.spawns
    with rig() as r:
        r.port80 = True
        r.run([])
        assert [u for u, _ in r.spawns] == ["cairn-ground-loop"], f"web started with 80 listening: {r.spawns}"
    with rig() as r:
        r.run([], {"CAIRN_HOME_HOST": "elsewhere"})
        assert [u for u, _ in r.spawns] == ["cairn-ground-loop"], f"web started on a non-home box: {r.spawns}"
    with rig() as r:
        r.run([], {"CAIRN_HOME_HOST": "TESTBOX.example"})
        assert "cairn-web-server" in [u for u, _ in r.spawns], "this box IS the home; the web server must start"
    with rig() as r:                                   # a spawn that raises costs the launch nothing
        def boom(*a, **k):
            raise OSError("no spawn")
        r.seams["spawn"] = boom
        assert r.run([]) == 0 and r.scoped, "the launch must still reach claude"


# ── 5 ────────────────────────────────────────────────────────────────────────
def test_the_restart_loop_honours_the_flags():
    with rig() as r:
        home = r.root / "flags-home"
        home.mkdir()
        rounds = []

        def claude(argv, env):
            rounds.append((list(argv), dict(env)))
            n = len(rounds)
            if n == 1:
                (home / "COMMAND_RESTART.flag").write_text("")
            elif n == 2:
                (home / "COMMAND_RESTART_FRESH.flag").write_text("")
            elif n == 3:
                (home / "COMMAND_RESTART.flag").write_text("")
                (home / "COMMAND_DO_NOT_RESTART.flag").write_text("")
            return 7 if n == 3 else 0

        r.seams["claude"] = claude
        rc = r.run(["--name", "x", "--k"], {"SUPERCLAUDE_INNER": "1", "SUPERCLAUDE_INNER_HOME": str(home),
                                           "CLAUDE_BIN": "claude"})
        assert rc == 7, f"the loop must exit with claude's last code, got {rc}"
        assert [a for a, _ in rounds] == [["claude", "--name", "x", "--k"],
                                          ["claude", "--name", "x", "--k", "--continue"],
                                          ["claude", "--name", "x", "--k"]], [a for a, _ in rounds]
        assert (home / "loop.pid").read_text().strip() == str(os.getpid())
        done = sorted(p.name.split(".flag")[0] for p in (home / "consumed").iterdir())
        assert done == ["COMMAND_RESTART", "COMMAND_RESTART_FRESH"], done
        assert (home / "COMMAND_DO_NOT_RESTART.flag").exists(), "DO_NOT_RESTART is a standing state, never consumed"
        assert (home / "COMMAND_RESTART.flag").exists(), "DO_NOT_RESTART won, so the pending RESTART stays"
        for _, env in rounds:
            assert env.get("SUPERCLAUDE_FLAGS_HOME") == str(home) and "SUPERCLAUDE_INNER" not in env, env
    with rig() as r:                                   # no flag: the launcher exits with claude
        home = r.root / "h2"
        home.mkdir()
        assert r.run(["--a"], {"SUPERCLAUDE_INNER": "1", "SUPERCLAUDE_INNER_HOME": str(home)}) == 0
        assert len(r.claude_calls) == 1, r.claude_calls


# ── 6 ────────────────────────────────────────────────────────────────────────
def test_claude_is_spawned_in_this_console():
    sc = _sc()
    seen = {}

    def fake_call(argv, **kw):
        seen["argv"], seen["kw"] = argv, kw
        return 5

    real = sc.subprocess.call
    sc.subprocess.call = fake_call
    try:
        rc = sc._run_claude(["claude", "--x"], {"A": "1"})
    finally:
        sc.subprocess.call = real
    assert rc == 5, "the exit code must be claude's"
    banned = {"stdin", "stdout", "stderr", "capture_output", "creationflags", "startupinfo", "input"}
    assert not banned & set(seen["kw"]), f"claude was spawned with {sorted(banned & set(seen['kw']))}: it must inherit the console"


# ── 7 ────────────────────────────────────────────────────────────────────────
def test_the_module_tests_no_os_and_never_elevates():
    assert _FILE.is_file(), f"{_FILE} is absent"
    text = _FILE.read_text(encoding="utf-8")
    bad = [t for t in ("os.name", "sys.platform", "platform.system", "bash", "sudo -S", "sudo -s",
                       "getpass", "SUDO_ASKPASS", "CAIRN_SUDO_PW", "input(") if t in text]
    assert not bad, f"superclaude.py names {bad}"
    assert "system_rackmount.tools.launch" in text, "superclaude.py does not ask the launch tool"
    assert not re.search(r"import\s+cairn\.devices\.recovery|from\s+cairn\.devices\.recovery", text), \
        "RULE 1: cc reaches recovery through floor.py's CLI, never an import"
    with rig() as r:
        r.run(["--dry-run"])
        assert not [l for l in r.out + r.err if "sudo" in l.lower() and "password" in l.lower()], r.text()
    with rig() as r:                                   # claude accepts bypass permissions under root
        home = r.root / "h"
        home.mkdir()
        r.run(["--a"], {"SUPERCLAUDE_INNER": "1", "SUPERCLAUDE_INNER_HOME": str(home)})
        assert r.claude_calls and r.claude_calls[0][1].get("IS_SANDBOX") == "1", r.claude_calls


# ── 8 ────────────────────────────────────────────────────────────────────────
def test_claude_starts_under_the_memory_scope():
    with rig() as r:
        r.run(["--name", "w"])
        assert len(r.scoped) == 1, f"claude must go through the scope once: {r.scoped}"
        argv, high, mx, swap = r.scoped[0]
        assert (high, mx, swap) == ("6G", "8G", "1G"), (high, mx, swap)
        assert str(_FILE) in argv, f"the scope must run the inner launcher: {argv}"
        assert r.scoped_env.get("SUPERCLAUDE_INNER") == "1" and r.scoped_env.get("SUPERCLAUDE_INNER_HOME"), \
            f"the inner launcher is told it is inner: {r.scoped_env}"
        assert os.environ.get("SUPERCLAUDE_INNER") is None, "inner mode leaked into the caller's environment"
    with rig() as r:
        r.run([], {"SUPERCLAUDE_MEM_MAX": "3G", "SUPERCLAUDE_MEM_HIGH": "2G", "SUPERCLAUDE_MEM_SWAP": "0"})
        assert r.scoped[0][1:] == ("2G", "3G", "0"), r.scoped
    with rig() as r:                                   # SUPERCLAUDE_NO_SCOPE declines the scope
        r.run([], {"SUPERCLAUDE_NO_SCOPE": "1"})
        assert r.scoped == [] and len(r.claude_calls) == 1, (r.scoped, r.claude_calls)


TEETH = [test_dry_run_resolves_the_context_switch_like_the_bash,
         test_a_held_instance_moves_to_the_next_free_one,
         test_the_preflight_runs_floor_verify_apply_report_and_its_text_rides_the_prompt,
         test_services_start_through_the_launch_tool_and_never_under_dry_run,
         test_the_restart_loop_honours_the_flags,
         test_claude_is_spawned_in_this_console,
         test_the_module_tests_no_os_and_never_elevates,
         test_claude_starts_under_the_memory_scope]


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
