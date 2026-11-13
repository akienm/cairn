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

The map is read off the live bus as Akien types it, through the command, never the harbor's
module (RULE 1).

    python3 cairn/devices/codemother/proofs/test_the_harbor_word_answers_only_status_queries.py
"""
from __future__ import annotations

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


def _cairn(*argv: str) -> subprocess.CompletedProcess:
    from cairn.tools.base.script_argv import bash_script_argv
    return subprocess.run([*bash_script_argv(_REPO_ROOT / "bin" / "cairn"), *argv],
                          capture_output=True, text=True, timeout=120)


def test_the_word_answers_the_map_and_refuses_a_non_status_verb():
    r = _cairn("codemother", "harbor_master", "show", "map", "--filter", "open")
    assert r.returncode == 0, (
        f"`cairn codemother harbor_master show map --filter open` exited {r.returncode}: "
        f"{(r.stderr or r.stdout)[-400:]}")
    rows = [ln for ln in r.stdout.splitlines() if _ROW.match(ln)]
    assert rows, f"the map printed no rows: {r.stdout[-400:]!r}"

    r = _cairn("codemother", "harbor_master", "clear")
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
