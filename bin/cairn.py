"""cairn.py — the Python launcher: `cairn <device>[.<instance>] [verb] [args...]` (outline 5.4.3.8).

"The launcher is Python, run by Cairn's own interpreter, so Windows needs no bash."  bin/cairn.cmd
runs this file with the venv's python; nothing here names bash. It is the same dispatch bin/cairn
(bash) performs, in the same order, and it refuses in the same words with the same exit codes:

    help                      -> the verb table, read from disk (cairn.tools.base.shim)
    <device> help             -> one device's cold list, or its live answer over a running bus
    <word>   (not a device)   -> the cairn device's bin beside its code, then bin/cmd/<word>
    <device>[.<n>] [verb]     -> the instance's bin, else the class bin, else the bus (script else bus)

Running a target: a Python script runs under this interpreter; a shell script is the shell's, so
it runs under a bash only if one is on PATH and is otherwise refused by name (exit 126) — the
dispatcher itself never needs one. Not carried over from bin/cairn, because each is bash itself:
the floor's lay-down and instance wiring (bootstrap.sh). Windows has no venv or db floor by
decision, so only the wiring of a declared-but-unwired instance is left to bin/cairn.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
# bin/ holds this file, so as sys.path[0] it would shadow the `cairn` package with itself.
sys.path[:] = [p for p in sys.path if Path(p or ".").resolve() != HERE]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

INSTANCE_ROOT = Path(os.environ.get("CAIRN_INSTANCE_ROOT") or Path.home() / ".cairn" / "devices")
LEGACY_CMD_DIR = Path(os.environ.get("CAIRN_CMD_DIR") or HERE / "cmd")
CLASS_ROOT = Path(os.environ.get("CAIRN_CLASS_ROOT") or REPO / "cairn" / "devices")
_IS_WIN = os.name == "nt"


def _say(msg: str) -> None:
    print(msg, file=sys.stderr)


def _usage() -> None:
    _say("cairn: usage: cairn <device> [verb] [args...]")
    _say("")
    _say("devices:")
    found = [d.parent.parent.name for d in sorted(INSTANCE_ROOT.glob("*/0/bin")) if d.is_dir()]
    for name in found:
        _say(f"  {name}")
    if not found:
        _say("  (none wired yet)")


def _subdirs(top: Path) -> list[Path]:
    return [d for d in top.iterdir() if d.is_dir()] if top.is_dir() else []


def _help(mode: str, dev: str = "", n: int = 0) -> int:
    from cairn.tools.base.shim import ROOT_VERB_SEMANTICS, bin_shortcuts, cold_list

    def shortcuts(d: str) -> None:
        rows = bin_shortcuts(d, str(INSTANCE_ROOT), 0, class_root=str(CLASS_ROOT))
        for s in rows:
            print(f"  {s['name']}" + (f" — {s['about']}" if s["about"] else ""))
        if not rows:
            print("  (none)")

    if mode == "all":
        print("[all]")
        for verb, meaning in ROOT_VERB_SEMANTICS.items():
            print(f"  {verb} — {meaning}")
        rest = sorted({d.name for d in _subdirs(INSTANCE_ROOT) if (d / "0" / "bin").is_dir()}
                      | {d.name for d in _subdirs(CLASS_ROOT) if (d / "bin").is_dir()})
        for d in ["operator", "cairn"] + [x for x in rest if x not in ("operator", "cairn")]:
            print(f"\n[{d}]")
            shortcuts(d)
        return 0
    if not (INSTANCE_ROOT / dev / str(n)).is_dir():
        _say(f"cairn {dev}.{n} help: no such device instance at {INSTANCE_ROOT / dev / str(n)}")
        return 127
    print(f"[{dev}]")
    try:  # the device's own shim, over a bus that is already up — help never starts one
        from cairn.tools.bus_client.remote import exchange
        reply = exchange({"op": "verbs", "device": dev, "verbs": ["help"]}, timeout=10)
        if reply.get("ok") and reply.get("exit") == 0:
            print(reply.get("text", ""))
            return 0
        reason = ("it answered stale — it runs older code than this class root, and help never "
                  "replaces a bus (the next ordinary command does)" if reply.get("stale")
                  else reply.get("error") or reply.get("text") or f"it answered {reply!r}")
    except (OSError, ValueError, RuntimeError, LookupError, ImportError) as exc:
        reason = f"{type(exc).__name__}: {exc}"
    print(cold_list(dev, str(INSTANCE_ROOT), n)["text"])
    print(f"(the live answer — views and panes — needs the bus: {reason})")
    return 0


def _is_script(path: Path) -> bool:
    """A file the dispatcher may run: on Windows there is no exec bit, so a file is a script."""
    return path.is_file() and (_IS_WIN or os.access(path, os.X_OK))


def _argv_for(target: Path) -> list[str] | None:
    """The command that runs a script: its shebang's interpreter, mapped to what this host has."""
    try:
        with open(target, "rb") as fh:
            first = fh.readline(200).decode("utf-8", "replace").strip()
    except OSError:
        first = ""
    if not first.startswith("#!"):
        return [str(target)] if not _IS_WIN else None
    words = first[2:].split()
    interp = Path(words[-1] if words and words[0].endswith("/env") and len(words) > 1 else words[0]).name if words else ""
    if interp.startswith("python"):
        return [sys.executable, str(target)]
    if _IS_WIN:
        shell = shutil.which(interp)
        return [shell, str(target)] if shell else None
    return [str(target)]


def _run(target: Path, args: list[str]) -> int:
    argv = _argv_for(target)
    if argv is None:
        _say(f"cairn: {target.name} is a shell script and no shell is on PATH to run it")
        return 126
    return subprocess.call(argv + list(args))


def _bus(bus_name: str, args: list[str]) -> int:
    mouth = os.environ.get("CAIRN_BUS_MOUTH")
    if mouth:
        return subprocess.call([mouth, bus_name, *args])
    env = dict(os.environ, PYTHONPATH=os.pathsep.join(filter(None, [str(REPO), os.environ.get("PYTHONPATH", "")])))
    return subprocess.call([sys.executable, "-m", "cairn.tools.bus_client", bus_name, *args], cwd=str(REPO), env=env)


def _answers_as(device: str) -> str:
    """The folder whose charter declares answers_as: <device> (ticket f942a413f26d), else the word."""
    if (CLASS_ROOT / device).is_dir():
        return device
    pat = re.compile(r'^  "answers_as": "' + re.escape(device) + r'",?$', re.M)
    for charter in sorted(CLASS_ROOT.glob("*/intention+why.json")):
        try:
            if pat.search(charter.read_text(encoding="utf-8", errors="replace")):
                return charter.parent.name
        except OSError:
            continue
    return device


def _wire_link(script: Path, inst_bin: Path) -> None:
    """One class verb into one instance bin: bootstrap.sh's per-file rule (ticket 80a220a86873).
    Absent: link it (copy where Windows will not link). A stale link: repoint it. A real file
    that is not the class verb: leave it and say so. Nothing is ever pruned."""
    at = inst_bin / script.name
    try:
        if at.is_symlink():
            if at.resolve() != script.resolve():
                at.unlink()
                os.symlink(script, at)
        elif at.exists():
            if at.is_file() and at.read_bytes() != script.read_bytes():
                _say(f"cairn wire: hand-placed file stands where class verb {script.name} would link: {at}")
        else:
            inst_bin.mkdir(parents=True, exist_ok=True)
            try:
                os.symlink(script, at)
            except OSError:
                shutil.copy2(script, at)
    except OSError as exc:
        _say(f"cairn wire: could not lay {at}: {exc}")


def _wire_instances() -> None:
    """The floor's instance wiring (bootstrap.sh cairn_wire_instances, which bin/cairn ran before
    dispatching): superclaude, then every device's class bin into instance 0, and cairn/0 itself."""
    sc = CLASS_ROOT / "cc" / "superclaude"
    if sc.is_file():
        _wire_link(sc, INSTANCE_ROOT / "superclaude" / "0" / "bin")
    for bindir in sorted(CLASS_ROOT.glob("*/0/bin")):
        if bindir.is_dir():
            for script in sorted(bindir.iterdir()):
                if script.is_file():
                    _wire_link(script, INSTANCE_ROOT / bindir.parent.parent.name / "0" / "bin")
    try:
        (INSTANCE_ROOT / "cairn" / "0").mkdir(parents=True, exist_ok=True)
    except OSError:
        pass


def main(argv: list[str]) -> int:
    if not argv:
        _usage()
        return 127
    if argv[0].lower() == "help":
        return _help("all")
    if len(argv) >= 2 and argv[1].lower() == "help":
        hd, hn = argv[0].lower(), "0"
        if "." in hd:
            hd, hn = hd.split(".", 1)
        if not hn.isdigit():
            _say(f"cairn {argv[0].lower()}: instance must be a number, got: {hn or '<empty>'}")
            return 127
        return _help("device", hd, int(hn))

    _wire_instances()

    typed = argv[0].lower()
    rest = list(argv[1:])
    device, instance = typed, "0"
    if "." in device:
        device, instance = device.split(".", 1)
    if not instance.isdigit():
        _say(f"cairn {typed}: instance must be a number, got: {instance or '<empty>'}")
        return 127

    bus_name = device
    device = _answers_as(device)

    cairn_bin = CLASS_ROOT / "cairn" / "bin" / device
    if typed == device and device != "cairn" and _is_script(cairn_bin) and not cairn_bin.is_dir():
        if (INSTANCE_ROOT / device).is_dir() or (CLASS_ROOT / device).is_dir():
            _say(f"cairn: {device} hides the {device} device (cairn/devices/cairn/bin/{device} runs)")
        return _run(cairn_bin, rest)

    device_bin = INSTANCE_ROOT / device / instance / "bin"
    first = rest[0].lower() if rest else ""
    class_word = CLASS_ROOT / device / "bin" / first
    if (instance == "0" and rest and not rest[0].startswith("-") and not _is_script(device_bin / first)
            and _is_script(class_word) and not class_word.is_dir()):
        return _run(class_word, rest[1:])

    if device_bin.is_dir():
        if not rest:
            verb = device
        elif _is_script(device_bin / first):
            verb, rest = first, rest[1:]
        elif rest[0].startswith("-") or instance != "0":
            verb = device
        else:
            return _bus(bus_name, rest)
        target = device_bin / verb
        if not _is_script(target):
            _say(f"cairn {device}: no such verb: {verb}")
            _say(f"verbs for {device}:")
            names = sorted(f.name for f in device_bin.iterdir() if _is_script(f))
            for name in names:
                _say(f"  {name}")
            if not names:
                _say("  (none)")
            return 127
        return _run(target, rest)

    if (INSTANCE_ROOT / device).is_dir():
        insts = sorted(d.parent.name for d in (INSTANCE_ROOT / device).glob("*/bin") if d.is_dir())
        if insts:
            _say(f"cairn {typed}: no such instance: {instance}")
            _say(f"instances for {device}:")
            for name in insts:
                _say(f"  {name}")
            return 127

    if typed == device and _is_script(LEGACY_CMD_DIR / device):
        return _run(LEGACY_CMD_DIR / device, rest)

    _say(f"cairn: no such device or command: {typed}")
    _usage()
    return 127


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
