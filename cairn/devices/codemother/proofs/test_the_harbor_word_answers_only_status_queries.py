"""`cairn codemother harbor_master` answers the harbor's status queries, and only those
(ticket ad6f3d0b265c; outline 9.4.1.5).

CodeMother answers every command about the code, and the harbor only reports. So the word
script ``cairn/devices/codemother/0/bin/harbor_master`` passes show/get/list through to
harbor_master on the bus and refuses every other verb, naming the outline line.

  1. ``cairn codemother harbor_master show map --filter open`` exits 0 and prints the map's
     rows: at least one ``<date> <stage> <12-hex id> <title>`` line. A non-status verb
     (``clear``) exits 2, and its stderr names 9.4.1.5.

Without the word script, the bare word falls through to CodeMother's shim, which declares
no ``harbor_master`` verb, and both halves red.

The map is read as Akien types it, through the command, never the harbor's module (RULE 1).
The world is this checkout's: bin/cairn runs under a scratch instance root, so the word it
dispatches is the one beside this code (the live instance bin links into the house tree), and
the bus it asks is a scratch bus process holding harbor_master from this checkout
(``scratch_bus.launch``). A hollow reading that reverts the word or the harbor's device
therefore reaches what answers.

    python3 cairn/devices/codemother/proofs/test_the_harbor_word_answers_only_status_queries.py
"""
from __future__ import annotations

import contextlib
import os
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"ad6f3d0b265c": {
    "1": "test_the_word_answers_the_map_and_refuses_a_non_status_verb",
}}

_ROW = re.compile(r"^\s*\d{4}-\d{2}-\d{2}\s+\S+\s+[0-9a-f]{12}\s+\S")


@contextlib.contextmanager
def _world():
    """This checkout's word and harbor: a scratch instance root and a scratch bus process."""
    from cairn.devices.cairn.tools.scratch_bus.scratch_bus import launch
    from cairn.tools.scratch.scratch import scratch_dir
    instances = scratch_dir("testing-ad6f-instances-")
    with launch("harbor_master", prefix="testing-ad6f") as bus:
        home = str(bus._home)
        yield {**os.environ, "CAIRN_BUS_HOME": home, "CAIRN_INSTANCE_ROOT": str(instances)}
    _wait_gone(home)


def _wait_gone(home: str, deadline_s: float = 20.0) -> None:
    """launch's shutdown is a request; wait for the process to stop answering, so the scratch
    bus never outlives this run (measured 2026-11-14: the runner ended it, "outlived its run")."""
    import time
    from cairn.tools.bus_client.remote import exchange
    end = time.monotonic() + deadline_s
    while time.monotonic() < end:
        try:
            exchange({"op": "ping"}, home, timeout=1)
        except (OSError, ValueError):
            return
        time.sleep(0.2)


def _cairn(env: dict, *argv: str) -> subprocess.CompletedProcess:
    from cairn.tools.base.script_argv import bash_script_argv
    return subprocess.run([*bash_script_argv(_REPO_ROOT / "bin" / "cairn"), *argv],
                          capture_output=True, text=True, timeout=300, env=env)


def test_the_word_answers_the_map_and_refuses_a_non_status_verb():
    with _world() as env:
        _the_word_answers(env)


def _the_word_answers(env: dict) -> None:
    r = _cairn(env, "codemother", "harbor_master", "show", "map", "--filter", "open")
    assert r.returncode == 0, (
        f"`cairn codemother harbor_master show map --filter open` exited {r.returncode}: "
        f"{(r.stderr or r.stdout)[-400:]}")
    rows = [ln for ln in r.stdout.splitlines() if _ROW.match(ln)]
    assert rows, f"the map printed no rows: {r.stdout[-400:]!r}"

    r = _cairn(env, "codemother", "harbor_master", "clear")
    assert r.returncode == 2, (
        f"`cairn codemother harbor_master clear` exited {r.returncode}, not 2: "
        f"{(r.stderr or r.stdout)[-400:]}")
    assert "9.4.1.5" in r.stderr, f"the refusal does not name 9.4.1.5: {r.stderr[-400:]!r}"


def main() -> int:
    fails = 0
    teeth = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in teeth:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001
            fails += 1
            print(f"  FAIL {name}  — {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not fails else 'RED'} — {len(teeth) - fails}/{len(teeth)}")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
