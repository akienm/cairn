"""Proof for ticket 0156856b1fae — Cairn's own spawns open no console on Windows.

Measured 2026-11-12 on akiendell: of four python processes bin/cairn's lazy-init started,
the two CHILDREN owned a console and the venv launchers that started them did not.

Tooth 2 is the experiment that settles the launcher hypothesis. It SPAWNS A PROCESS, which
on Windows may briefly allocate a console if the hypothesis is false — that is the red it
is built to show. Pass ``--no-spawn`` to run teeth 1 and 3 only (tooth 2 reports UNMEASURED).

Every tooth binds what the build ADDED at call time, never at import.

    python <this file> [--no-spawn]
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "0156856b1fae": {
        "1": "the_helper_kwargs_carry_the_windows_flags",
        "2": "a_spawned_child_leaves_no_console_in_its_tree",
        "3": "no_site_hand_builds_a_flag_set",
    },
}

SITES = [
    "cairn/tools/base/shim.py",
    "cairn/devices/cairn/machines/ground_loop/cli.py",
    "cairn/devices/cairn/machines/ground_loop/heartbeat.py",
    "cairn/devices/cc/shim.py",
    "cairn/machines/web_operator/web_operator.py",
    "cairn/tools/bus_client/remote.py",
]


class Unmeasured(Exception):
    """The tooth cannot run here; that is a state, never a green."""


def _ws():
    from cairn.tools.windowless_spawn import windowless_spawn as ws
    return ws


def the_helper_kwargs_carry_the_windows_flags():
    ws = _ws()
    nt = ws.detached_kwargs("nt")
    flags = nt.get("creationflags", 0)
    assert flags & 0x08000000, f"CREATE_NO_WINDOW missing: {nt}"
    assert flags & 0x00000008, f"DETACHED_PROCESS missing: {nt}"
    assert "start_new_session" not in nt, f"start_new_session is a no-op on NT: {nt}"
    posix = ws.detached_kwargs("posix")
    assert posix.get("start_new_session") is True and "creationflags" not in posix, posix
    # the interpreter: inside a venv on nt it must not be the launcher
    base = Path(ws.background_python("nt"))
    cfg = Path(sys.executable).resolve().parent.parent / "pyvenv.cfg"
    if os.name == "nt" and cfg.exists():
        assert base.resolve() != Path(sys.executable).resolve(), f"still the venv launcher: {base}"
    assert ws.background_python("posix", executable="/usr/bin/python3") == "/usr/bin/python3"


def _tree(root_pid: int) -> list[dict]:
    """Every process under root_pid, as {pid, parent, name}."""
    out = subprocess.run(
        ["powershell", "-NoProfile", "-Command",
         "Get-CimInstance Win32_Process | ForEach-Object { \"$($_.ProcessId),$($_.ParentProcessId),$($_.Name)\" }"],
        capture_output=True, text=True, creationflags=0x08000000).stdout.splitlines()
    procs = []
    for line in out:
        parts = line.strip().split(",", 2)
        if len(parts) == 3 and parts[0].isdigit() and parts[1].isdigit():
            procs.append({"pid": int(parts[0]), "parent": int(parts[1]), "name": parts[2]})
    seen, frontier = {root_pid}, [root_pid]
    while frontier:
        nxt = [p["pid"] for p in procs if p["parent"] in frontier and p["pid"] not in seen]
        seen.update(nxt)
        frontier = nxt
    return [p for p in procs if p["pid"] in seen or p["parent"] in seen]


def a_spawned_child_leaves_no_console_in_its_tree():
    if os.name != "nt":
        raise Unmeasured("not a Windows box: the launcher hypothesis can only be measured on NT")
    if "--no-spawn" in sys.argv:
        raise Unmeasured("--no-spawn: this tooth spawns a process and was not asked to")
    ws = _ws()
    child = subprocess.Popen([ws.background_python(), "-c", "import time; time.sleep(6)"],
                             stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL, **ws.detached_kwargs())
    try:
        time.sleep(2.5)
        tree = _tree(child.pid)
        consoles = [p for p in tree if p["name"].lower() in ("conhost.exe", "openconsole.exe")]
        print(f"    tree under {child.pid}: {[(p['name'], p['pid']) for p in tree]}")
        assert not consoles, f"a console host sits in the spawned tree: {consoles}"
    finally:
        child.kill()


def no_site_hand_builds_a_flag_set():
    bad = []
    for rel in SITES:
        text = (REPO / rel).read_text(encoding="utf-8")
        if "detached_kwargs" not in text:
            bad.append(f"{rel}: does not take its keywords from the helper")
        for needle in ("start_new_session=True", "creationflags="):
            if needle in text:
                bad.append(f"{rel}: hand-builds {needle}")
    assert not bad, "\n".join(bad)


TEETH = [the_helper_kwargs_carry_the_windows_flags,
         a_spawned_child_leaves_no_console_in_its_tree,
         no_site_hand_builds_a_flag_set]


def main() -> int:
    failed = unmeasured = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except Unmeasured as e:
            unmeasured += 1
            print(f"  UNMEASURED  {t.__name__}: {e}")
        except Exception as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {e}")
    print(f"\n{len(TEETH) - failed - unmeasured}/{len(TEETH)} teeth green, {unmeasured} unmeasured")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
