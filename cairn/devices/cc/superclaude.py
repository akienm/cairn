#!/usr/bin/env python3
"""superclaude — Cairn's Claude Code launcher, in Python (ticket 1941e93b25a3, child 3 of c3cd232ba0cf).

Ported from the shell launcher it replaced, which left once every caller launched this file (child 6,
ticket e179281f6eff). Measured 2026-11-22 on akiendell: `cairn superclaude` exited 127 silently
because where.exe lists WSL's launcher shell before Git Bash. A Python launcher needs no shell.

What it does, in the order it does it: parse our flags and forward the rest to claude; resolve the
context switch (command line > environment > file default > unconstrained); take the instance, moving
to the next free one when it is held; run the preflight by calling recovery's floor.py as a command
(RULE 1: cc may not import recovery) and put its report on --append-system-prompt; link CC's memory;
carry in the floor's findings; install claude if it is absent; start the ground loop and the web
server through the launch tool; trace the launch; then hand the terminal to the inner restart loop,
under the memory scope where the box has one.

Every OS question goes through cairn/devices/system_rackmount/tools/launch/launch.py. This module
never elevates and never asks for a password: elevation is the shell's, settled before Python starts
(outline 5.4.3.8.6, 10.3.2.1). Nothing between parse and the claude spawn may abort the launch (the
prime directive): every phase is guarded, and what it could not do is logged and, where it matters,
carried to claude in the report.

Test seams: main(argv, env, seams) takes a dict that replaces any of the OS-touching callables; the
proof uses it. In use the dict is empty.
"""
from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import time
from pathlib import Path

_FILE = Path(__file__).resolve()
_REPO = _FILE.parents[3]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from cairn.devices.system_rackmount.tools.host.host import host_name  # noqa: E402
from cairn.devices.system_rackmount.tools.launch import launch  # noqa: E402
from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs  # noqa: E402

# ── FILE DEFAULT — flip this ONE LINE to change the built-in default ─────────
#   0 = no file constraint: unconstrained (1M) when the environment is silent
#   1 = default to 200K when the environment is silent
FILE_DEFAULT_200K = 1

_DISABLE = "CLAUDE_CODE_DISABLE_1M_CONTEXT"
_MENU = ("COMMAND_RESTART.flag", "COMMAND_RESTART_FRESH.flag", "COMMAND_DO_NOT_RESTART.flag")
_GROUND_LOOP = ["-m", "cairn.devices.cairn.machines.ground_loop"]

HELP = """superclaude — Cairn's Claude Code launcher.

  Standing contract (always applied):
    --name <hostname>_cc_0              stable singleton session name
    --remote-control <hostname>_cc_0    remote control on, same name
    --dangerously-skip-permissions      bypass permission prompts

  Context window — a two-state switch; the command line always wins:
    --1m            opt UP: unset any 200K constraint (wins over a 200K environment)
    --200k, --no-1m opt DOWN: impose the 200K constraint
    (neither)       inherit the environment; if it is silent, the file default; if that is
                    silent too, launch unconstrained (1M)

  --tmux            launch CC inside a tmux session (or CAIRN_SUPERCLAUDE_TMUX=1)

  Restart flags — presence-based, in ~/.cairn/launchers/superclaude/<N>/ (an active signal is a
  copy of the menu file in flags/ one level up):
    COMMAND_RESTART.flag        on CC exit, relaunch with --continue (one-shot)
    COMMAND_RESTART_FRESH.flag  on CC exit, relaunch clean (one-shot)
    COMMAND_DO_NOT_RESTART.flag never relaunch; wins, and is not consumed

  Launcher-only:
    --instance=N    launch as instance N (default 0): session <host>_cc_N, own scope
    --name WORD     the same slot, as a word: <host>_cc_WORD, CAIRN_USER=ccWORD
    --dry-run       print the resolved context state + claude command, do not launch
    --no-preflight  skip the floor check (rescue hatch: the launch must always be reachable)
    -h, --help      this message

  All other arguments are forwarded to claude unchanged.
"""


# ── seams ────────────────────────────────────────────────────────────────────
def _one_line(argv) -> str:
    """argv quoted for a POSIX shell on ONE line, as the shell launcher's printf %q printed it.

    shlex.join keeps a newline inside its quotes, so a residue prompt split the dry run's exec line
    and a reader of that line got half an argv (ticket e179281f6eff). An argument carrying a control
    character is written in ANSI-C $'...' quoting instead."""
    out = []
    for a in argv:
        if any(ord(c) < 32 for c in a):
            esc = a.replace("\\", "\\\\").replace("'", "\\'")
            esc = "".join(c if ord(c) >= 32 else {"\n": "\\n", "\t": "\\t", "\r": "\\r"}.get(c, f"\\x{ord(c):02x}")
                          for c in esc)
            out.append(f"$'{esc}'")
        else:
            out.append(shlex.quote(a))
    return " ".join(out)


def _home(env) -> Path:
    return Path(env.get("HOME") or env.get("USERPROFILE") or Path.home())


def _pid_alive(pid: int) -> bool:
    if launch.runs_shell_scripts():
        try:
            os.kill(pid, 0)
        except PermissionError:
            return True
        except OSError:
            return False
        return True
    import ctypes
    k32 = ctypes.windll.kernel32
    handle = k32.OpenProcess(0x1000, False, pid)          # PROCESS_QUERY_LIMITED_INFORMATION
    if not handle:
        return False
    code = ctypes.c_ulong()
    k32.GetExitCodeProcess(handle, ctypes.byref(code))
    k32.CloseHandle(handle)
    return code.value == 259                              # STILL_ACTIVE


def _tmux_has(name: str) -> bool:
    if not shutil.which("tmux"):
        return False
    return subprocess.run(["tmux", "has-session", "-t", f"={name}"], capture_output=True,
                          **windowless_kwargs()).returncode == 0


def _floor_cli(verb: str, stdin=None):
    """recovery's published command: python floor.py verify|apply|report, JSON on stdout."""
    floor = _REPO / "cairn" / "devices" / "recovery" / "floor.py"
    env = dict(os.environ, PYTHONPATH=str(_REPO))
    got = subprocess.run([sys.executable, str(floor), verb], capture_output=True, text=True, env=env,
                         input=json.dumps(stdin) if stdin is not None else None, timeout=900,
                         **windowless_kwargs())
    return got.returncode, json.loads(got.stdout or "null")


def _memlink(cwd: str) -> str:
    script = _FILE.parent / "scripts" / "memory_link.py"
    got = subprocess.run([sys.executable, str(script), "--quiet", cwd], capture_output=True, text=True,
                         timeout=300, **windowless_kwargs())
    return ((got.stdout or "") + (got.stderr or "")).strip()


def _install(url: str, err) -> None:
    if launch.runs_shell_scripts():
        fetch = (["curl", "-fsSL", url] if shutil.which("curl") else ["wget", "-qO-", url])
        text = subprocess.run(fetch, capture_output=True, text=True, timeout=600).stdout
        subprocess.run(["sh"], input=text, text=True, timeout=900)
    else:
        subprocess.run(["powershell", "-NoProfile", "-Command",
                        f"irm {url.replace('install.sh', 'install.ps1')} | iex"], timeout=900)


def _trace(event: str, lacks) -> None:
    subprocess.Popen([sys.executable, "-m", "cairn.machines.learning_block", "trace", "--holder", "cc/0",
                      "superclaude", event, "launch", *lacks], stdin=subprocess.DEVNULL,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, cwd=str(_REPO),
                     env=dict(os.environ, PYTHONPATH=str(_REPO)), **windowless_kwargs())


def _run_claude(argv, env) -> int:
    """claude runs in THIS console, stdio inherited: no capture, no creation flags."""
    argv = list(argv)
    argv[0] = shutil.which(argv[0]) or argv[0]
    return subprocess.call(argv, env=env)


def _scope_exec(argv, mem_high, mem_max, swap_max, unit=None, log=None, env=None):
    os.environ.update(env or {})
    return launch.scoped_exec(argv, mem_high, mem_max, swap_max, unit=unit, log=log)


def _seams(given) -> dict:
    s = {"out": print, "err": lambda m: print(m, file=sys.stderr), "host": None, "cwd": None,
         "floor": _floor_cli, "memlink": _memlink, "which": shutil.which, "spawn": launch.service_spawn,
         "port": launch.port_listening, "claude": _run_claude, "trace": _trace, "pid_alive": _pid_alive,
         "tmux_has": _tmux_has, "scope_exec": _scope_exec, "install": _install, "repo": _REPO,
         "elevation": launch.elevation, "addresses": launch.box_addresses}
    s.update(given or {})
    return s


# ── the parts ────────────────────────────────────────────────────────────────
def parse(argv) -> dict:
    o = {"want_1m": False, "want_200k": False, "tmux": False, "dry_run": False, "no_preflight": False,
         "instance": "", "help": False, "pass": []}
    args = list(argv)
    while args:
        a = args.pop(0)
        if a == "--1m":
            o["want_1m"] = True
        elif a in ("--200k", "--no-1m"):
            o["want_200k"] = True
        elif a == "--tmux":
            o["tmux"] = True
        elif a == "--dry-run":
            o["dry_run"] = True
        elif a == "--no-preflight":
            o["no_preflight"] = True
        elif a.startswith("--instance="):
            o["instance"] = a.split("=", 1)[1]
        elif a.startswith("--name="):
            o["instance"] = a.split("=", 1)[1]
        elif a == "--name":
            o["instance"] = args.pop(0) if args else ""
        elif a in ("-h", "--help"):
            o["help"] = True
        else:
            o["pass"].append(a)
    return o


def resolve_context(o: dict, env: dict) -> str:
    """The two-state switch. The variable IS Claude Code's own control var; --1m unsets it (=0 is a no-op)."""
    if o["want_1m"]:
        env.pop(_DISABLE, None)
        return "1M (command line --1m)"
    if o["want_200k"]:
        env[_DISABLE] = "1"
        return "200K (command line --200k)"
    if env.get(_DISABLE):
        return "200K (environment)" if env[_DISABLE] == "1" else "1M (environment)"
    if FILE_DEFAULT_200K:
        env[_DISABLE] = "1"
        return "200K (file default)"
    return "1M (unconstrained — nothing decided)"


def _flags_home(home: Path, instance: str) -> Path:
    return home / ".cairn" / "launchers" / "superclaude" / instance


def _held(instance: str, home: Path, s: dict):
    """HELD is restart's own question: a live loop.pid, or a tmux session of that name."""
    try:
        pid = int((_flags_home(home, instance) / "loop.pid").read_text(encoding="utf-8").strip())
        if s["pid_alive"](pid):
            return f"live loop {pid}"
    except (OSError, ValueError):
        pass
    if s["tmux_has"](f"cairn_cc_{instance}"):
        return f"tmux session cairn_cc_{instance}"
    return None


def move_if_held(asked: str, home: Path, s: dict):
    """A held instance moves to the next free one: a number counts up, a word keeps its name + _N."""
    first = _held(asked, home, s)
    if not first:
        return asked, ""
    stem, n = ("", int(asked) + 1) if asked.isdigit() else (asked + "_", 1)
    while _held(f"{stem}{n}", home, s):
        n += 1
    new = f"{stem}{n}"
    return new, f"instance {asked} is held by {first}; launching as instance {new}"


def _is_cairn_home(env, me: str, s: dict) -> bool:
    h = (env.get("CAIRN_HOME_HOST") or "").lower().split(".")[0]
    if not h:
        return True
    if h in (me, "localhost", "127"):
        return True
    return env.get("CAIRN_HOME_HOST", "") in s["addresses"]()


def _consume(home: Path, name: str) -> None:
    """A one-shot is consumed by MOVING it to consumed/<flag>.<stamp>: instance-space has no undo."""
    try:
        (home / "consumed").mkdir(parents=True, exist_ok=True)
        os.replace(home / name, home / "consumed" / f"{name}.{time.strftime('%Y%m%dT%H%M%S')}")
    except OSError:
        pass


def inner(argv, env: dict, s: dict) -> int:
    """The restart loop: holds the terminal, relaunches claude on a flag. No flag = claude's exit is ours."""
    home = Path(env["SUPERCLAUDE_INNER_HOME"])
    claude_bin = env.get("CLAUDE_BIN") or "claude"
    child = {k: v for k, v in env.items() if k not in ("SUPERCLAUDE_INNER", "SUPERCLAUDE_INNER_HOME")}
    child["SUPERCLAUDE_FLAGS_HOME"] = str(home)
    child["IS_SANDBOX"] = "1"
    base, cur, rc = list(argv), list(argv), 0
    try:
        home.mkdir(parents=True, exist_ok=True)
        (home / "loop.pid").write_text(f"{os.getpid()}\n", encoding="utf-8")
    except OSError:
        pass
    while True:
        rc = s["claude"]([claude_bin, *cur], child)
        if (home / "COMMAND_DO_NOT_RESTART.flag").exists():
            break
        if (home / "COMMAND_RESTART_FRESH.flag").exists():
            _consume(home, "COMMAND_RESTART_FRESH.flag")
            cur = list(base)
            continue
        if (home / "COMMAND_RESTART.flag").exists():
            _consume(home, "COMMAND_RESTART.flag")
            cur = [*base, "--continue"]          # rebuilt from the base every time, never appended
            continue
        break
    return rc


def _safe(fn, default, note, log):
    try:
        return fn()
    except Exception as e:  # noqa: BLE001 — nothing between parse and claude may abort the launch
        log(f"{note}: {type(e).__name__}: {e}")
        return default


def _spawn_service(spawn, unit, argv, service_log, cwd, env):
    """Start a service through the launch tool, and when it started nothing (a held name, a
    refusal), write that answer into the service's own log too: a launch that started nothing
    must not look, in that file, like one that started something. The shell launcher this
    replaced appended systemd-run's refusal there; the ground_loop proof's taken-unit tooth
    reads it (cairn/devices/recovery/proofs/test_ground_loop_survives_its_caller.py)."""
    got = spawn(unit, argv, service_log, cwd=cwd, env=env)
    if isinstance(got, dict) and (not got.get("ok") or got.get("how") == "held"):
        try:
            Path(service_log).parent.mkdir(parents=True, exist_ok=True)
            with open(service_log, "a", encoding="utf-8") as fh:
                fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} superclaude: {unit} not started "
                         f"({got.get('how')}): {got.get('detail')}\n")
        except OSError:
            pass
    return got


def main(argv=None, env=None, seams=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    env = dict(os.environ if env is None else env)
    s = _seams(seams)
    if env.get("SUPERCLAUDE_INNER") == "1":
        return inner(argv, env, s)
    o = parse(argv)
    if o["help"]:
        s["out"](HELP.rstrip("\n"))
        return 0

    home = _home(env)
    # CAIRN_BOOT_LOG redirects the flight recorder, as it did in the shell launcher this replaced,
    # so a proof run writes a scratch log and never becomes evidence in the live one (ticket e179281f6eff).
    logfile = Path(env["CAIRN_BOOT_LOG"]) if env.get("CAIRN_BOOT_LOG") else home / ".cairn" / "logs" / "boot" / "superclaude.log"

    def log(msg: str) -> None:
        try:
            logfile.parent.mkdir(parents=True, exist_ok=True)
            with open(logfile, "a", encoding="utf-8") as fh:
                fh.write(f"{time.strftime('%Y-%m-%dT%H:%M:%S')} {msg}\n")
        except OSError:
            pass

    context = resolve_context(o, env)
    tmux_mode = o["tmux"] or env.get("CAIRN_SUPERCLAUDE_TMUX") == "1"
    me = (s["host"] or host_name()).split(".")[0].lower()
    asked = o["instance"] or "0"
    instance, moved = move_if_held(asked, home, s)
    if moved:
        s["err"](f"superclaude: {moved}")
    session = f"{me}_cc_{instance}"
    env["CAIRN_USER"] = f"cc{instance}"
    env["IS_SANDBOX"] = "1"
    log(f"launch: argv={argv} session={session} context={context} "
        f"preflight={'bypassed' if o['no_preflight'] else 'on'}")
    if moved:
        log(f"moved: {moved}")

    residue = ""
    if not o["no_preflight"]:
        def preflight():
            t0 = time.time()
            rc, found = s["floor"]("verify")
            if rc != 0:
                # A repair that fails ADDS to what verify measured, as the shell's findings array
                # did; it never replaces it. An apply that crashed would otherwise carry only its
                # crash, and the session would open without being told the venv is absent.
                before = list(found or [])
                rc, got = s["floor"]("apply")
                got = list(got or [])
                codes = {f.get("code") for f in got if isinstance(f, dict)}
                found = ([f for f in before if not isinstance(f, dict) or f.get("code") not in codes] + got
                         if got else [])
            venv = Path(env.get("CAIRN_VENV") or (home / ".cairn" / "venv"))
            vbin = launch.venv_bin_dir(venv)
            if vbin.is_dir():
                env["PATH"] = str(vbin) + os.pathsep + env.get("PATH", "")
            _, rep = s["floor"]("report", found or [])
            log(f"preflight: done in {int((time.time() - t0) * 1000)}ms · residue={'yes' if rep.get('text') else 'none'}")
            return (rep or {}).get("text") or ""
        residue = _safe(preflight, "", "preflight failed", log)
    else:
        log("preflight: skipped by --no-preflight")

    note = _safe(lambda: s["memlink"](s["cwd"] or os.getcwd()), "", "memory link failed", log)
    log(f"memory: link · {'said: ' + note if note else 'ok'}")
    if note:
        s["err"](f"superclaude: {note}")
        residue = f"{residue}\n{note}" if residue else note

    carried = env.pop("CAIRN_FLOOR_FINDINGS", "")
    if carried.strip():
        log("floor: carried in — " + carried.replace("\n", " | "))
        lines = "\n".join("  - " + l for l in carried.splitlines() if l.strip())
        head = "CAIRN FLOOR — bin/cairn's floor checks that did not pass (they would refuse any other command):"
        residue = (residue + "\n" if residue else "") + head + "\n" + lines
    if residue:
        el = _safe(s["elevation"], {}, "elevation unread", log)
        if el:
            residue += f"\n\nelevation: {el.get('how')} — {el.get('detail')} (the shell's; this session never asks again)"

    claude_bin = env.get("CLAUDE_BIN") or "claude"
    local = home / ".local" / "bin"

    def _look_in_local_bin() -> None:
        # env is a copy: the real which reads the process PATH, so the local bin is read by path
        nonlocal claude_bin
        env["PATH"] = str(local) + os.pathsep + env.get("PATH", "")
        found = shutil.which(claude_bin, path=str(local))
        if found:
            claude_bin = found
    if not s["which"](claude_bin):
        _look_in_local_bin()
    if not s["which"](claude_bin):
        url = env.get("CAIRN_CLAUDE_INSTALLER") or "https://claude.ai/install.sh"
        if o["dry_run"]:
            s["out"](f"# claude not found: a real launch would install it from {url}")
        else:
            s["err"](f"superclaude: {claude_bin} not found — installing Claude Code from {url}")
            log(f"claude: absent — installing from {url}")
            _safe(lambda: s["install"](url, s["err"]), None, "install failed", log)
            _look_in_local_bin()
            if not s["which"](claude_bin):
                s["err"](f"superclaude: FAILED — the installer ran but {claude_bin} is still not on PATH. "
                         "Install by hand: https://claude.ai/install")
                log("claude: install FAILED — nothing to launch")
                return 127

    flags_home = _flags_home(home, instance)
    try:
        (flags_home / "flags").mkdir(parents=True, exist_ok=True)
        for f in _MENU:
            (flags_home / "flags" / f).touch()
    except OSError as e:
        log(f"flags home not laid: {e}")

    claude_argv = ["--name", session, "--remote-control", session, "--dangerously-skip-permissions"]
    if residue:
        claude_argv += ["--append-system-prompt", residue]
    claude_argv += o["pass"]
    log(f"exec: {claude_bin} {_one_line(claude_argv)}")

    repo = Path(s["repo"])
    if not o["dry_run"]:
        mark = {"CAIRN_TESTER_TEST_ID": env["CAIRN_TESTER_TEST_ID"]} if env.get("CAIRN_TESTER_TEST_ID") else {}
        py = sys.executable
        loop = _safe(lambda: _spawn_service(s["spawn"], env.get("SUPERCLAUDE_GROUND_LOOP_UNIT") or "cairn-ground-loop",
                                            [py, *_GROUND_LOOP], home / ".cairn" / "logs" / "ground_loop_nohup.log",
                                            repo, mark), None, "ground loop spawn failed", log)
        log(f"ground_loop: {loop}")
        if not _is_cairn_home(env, me, s):
            log(f"web_server: not started: this box attaches to the cairn home {env.get('CAIRN_HOME_HOST')}")
        elif s["port"](80) and not env.get("SUPERCLAUDE_WEB_PORT_FREE"):
            # SUPERCLAUDE_WEB_PORT_FREE is a proof's knob, as the shell's `ss` on PATH was: it lets a
            # scratch run reach its own web unit while the live server holds :80.
            log("web_server: already listening on port 80")
        else:
            web = _safe(lambda: _spawn_service(s["spawn"], env.get("SUPERCLAUDE_WEB_UNIT") or "cairn-web-server",
                                               [py, str(repo / "cairn" / "devices" / "web_server" / "listener.py")],
                                               home / ".cairn" / "logs" / "web_server.log", repo, mark),
                        None, "web server spawn failed", log)
            log(f"web_server: {web}")
        if o["no_preflight"]:
            event, lacks = "send_back", ["preflight bypassed by --no-preflight"]
        elif residue:
            event, lacks = "send_back", [f"preflight residue: {residue}"]
        else:
            event, lacks = "door_pass", []
        _safe(lambda: s["trace"](event, lacks), None, "trace failed", log)

    if o["dry_run"]:
        s["out"]("# superclaude --dry-run")
        s["out"](f"# context: {context}")
        s["out"](f"# tmux: {'on (session: cairn_cc_' + instance + ')' if tmux_mode else 'off'}")
        s["out"](f"# {_DISABLE}={env.get(_DISABLE, '<unset>')}")
        s["out"](f"# CAIRN_USER={env['CAIRN_USER']}")
        s["out"](f"# instance: asked {asked}, launching {instance}")
        if moved:
            s["out"](f"# moved: {moved}")
        if tmux_mode:
            s["out"](f"tmux new-session -d -s cairn_cc_{instance} -- {claude_bin} {_one_line(claude_argv)}")
        else:
            s["out"](f"# flags home: {flags_home}")
            s["out"](f"exec {claude_bin} {_one_line(claude_argv)}")
        return 0

    if launch.stream_is_console(sys.stdout):
        sys.stdout.write("\033[2J\033[H")
        sys.stdout.flush()

    high = env.get("SUPERCLAUDE_MEM_HIGH") or "6G"
    mx = env.get("CAIRN_SUPERCLAUDE_MEMORY_MAX_PER_INSTANCE") or env.get("SUPERCLAUDE_MEM_MAX") or "8G"
    swap = env.get("SUPERCLAUDE_MEM_SWAP") or "1G"
    inner_env = {"SUPERCLAUDE_INNER": "1", "SUPERCLAUDE_INNER_HOME": str(flags_home), "CLAUDE_BIN": claude_bin}
    inner_argv = [sys.executable, str(_FILE), *claude_argv]
    if env.get("SUPERCLAUDE_NO_SCOPE"):
        log("scope: declined by SUPERCLAUDE_NO_SCOPE — launching unbounded")
        return inner(claude_argv, {**env, **inner_env}, s)
    if tmux_mode:
        name = f"cairn_cc_{instance}"
        if s["tmux_has"](name):
            log(f"tmux: session {name} already exists — attaching")
            return s["scope_exec"](["tmux", "attach-session", "-t", name], high, mx, swap, env=None)
        log(f"tmux: creating session {name}")
        wrapped = ["env", *[f"{k}={v}" for k, v in inner_env.items()], *inner_argv]
        return s["scope_exec"](["tmux", "new-session", "-d", "-s", name, *wrapped, ";", "attach-session", "-t", name],
                               high, mx, swap, unit=f"superclaude-{os.getpid()}", log=log)
    return s["scope_exec"](inner_argv, high, mx, swap, unit=f"superclaude-{os.getpid()}", log=log,
                           env={**inner_env, "CAIRN_USER": env["CAIRN_USER"], "IS_SANDBOX": "1",
                                **({_DISABLE: env[_DISABLE]} if _DISABLE in env else {})})


if __name__ == "__main__":
    sys.exit(main())
