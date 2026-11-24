"""The bash superclaude is gone: its callers launch superclaude.py, and nothing live names it.

Ticket e179281f6eff (child 6 of c3cd232ba0cf). Outline 10.3.2.1: superclaude is Python on every
box. Measured 2026-11-23 at ef541167c: cairn/devices/cc/superclaude (the bash) still stands beside
superclaude.py; cairn/devices/cc/0/bin/restart:55 sets LAUNCHER to it and
cairn/devices/recovery/bootstrap.sh:484 links it as the verb superclaude, although bin/cairn has
dispatched the .py since 0b7a3f1d53f0. Two launchers beside each other drift.

PROVES (teeth below, one per falsifier clause):
  (1) cc/0/bin/restart and recovery/bootstrap.sh name cairn/devices/cc/superclaude.py and no
      longer name the bash path;
  (2) the four cc proofs that ran the bash (sets_cairn_user, wire, memory_scope, tmux_mode) name
      superclaude.py, not the bash, and read green; test_superclaude_bare_box.py is retired. The
      repointed proofs of the other components are measured by their own seals, never from here
      (outline 19.6: a proof measures only its own component);
  (3) the bash is absent from the tree and from git's index;
  (4) no tracked file under cairn/ or bin/ names the bash path, except the files listed in
      NOT_A_LAUNCHER, each with the reason it names the bash without launching it.

"The bash path" is cairn/devices/cc/superclaude not followed by `.py` or a word character, or the
path-join spelling "cc" / "superclaude". The instance verb ~/.cairn/devices/superclaude/0/bin/
superclaude is not the bash and is not matched. Records (history, state, validations, journals,
berths) are not scanned: they are the record of what was true.
"""
from __future__ import annotations

import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

BASH_REL = "cairn/devices/cc/superclaude"
PY_REL = "cairn/devices/cc/superclaude.py"
CALLERS = ("cairn/devices/cc/0/bin/restart", "cairn/devices/recovery/bootstrap.sh")
CC_PROOFS = ("cairn/devices/cc/proofs/test_superclaude_sets_cairn_user.py",
             "cairn/devices/cc/proofs/test_superclaude_wire.py",
             "cairn/devices/cc/proofs/test_superclaude_memory_scope.py",
             "cairn/devices/cc/proofs/test_tmux_mode.py")
BARE_BOX = "cairn/devices/cc/proofs/test_superclaude_bare_box.py"
THIS = "cairn/devices/cc/proofs/test_the_bash_superclaude_is_gone.py"
# Files that name the bash path without launching it. A file joins this list only with its reason.
NOT_A_LAUNCHER = {
    "bin/cairn.py": "_superclaude_stale reads the bash's bytes to tell an instance verb still "
                    "copied from it, so the floor relinks that verb to the .py (0b7a3f1d53f0)",
    "bin/proofs/test_cairn_dispatches_superclaude_py.py": "writes a bash stand-in in a scratch "
                    "class root as the stale verb the floor must replace",
    THIS: "names the path it proves absent",
}
BASH_NAMED = re.compile(r"devices/cc/superclaude(?![.\w])|[\"']cc[\"']\s*/\s*[\"']superclaude[\"'](?!\s*\.)")
RECORD = re.compile(r"(^|/)(history|state)\.json$|/validations/|\.jsonl$|/berths/")

PROVES = {"e179281f6eff": {
    "1": "test_the_two_callers_launch_superclaude_py",
    "2": "test_the_cc_proofs_that_ran_the_bash_run_the_py_and_bare_box_is_retired",
    "3": "test_the_bash_is_absent_from_the_tree_and_the_index",
    "4": "test_nothing_live_names_the_bash",
}}

_failures: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"  — {detail}"))
    if not ok:
        _failures.append(name)


def _text(rel: str) -> str:
    try:
        return (ROOT / rel).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def test_the_two_callers_launch_superclaude_py() -> None:
    bad = {rel: ("names the bash" if BASH_NAMED.search(_text(rel)) else "")
                + ("" if "superclaude.py" in _text(rel) else " does not name superclaude.py")
           for rel in CALLERS}
    bad = {k: v.strip() for k, v in bad.items() if v.strip()}
    check("test_the_two_callers_launch_superclaude_py", not bad, f"{bad}")


def test_the_cc_proofs_that_ran_the_bash_run_the_py_and_bare_box_is_retired() -> None:
    lacks: list[str] = []
    if (ROOT / BARE_BOX).exists():
        lacks.append(f"{BARE_BOX} still stands")
    for rel in CC_PROOFS:
        text = _text(rel)
        if BASH_NAMED.search(text):
            lacks.append(f"{rel} names the bash")
        if "superclaude.py" not in text:
            lacks.append(f"{rel} does not name superclaude.py")
    if not lacks:   # run them only once they point at the .py: a run of the bash measures nothing here
        for rel in CC_PROOFS:
            r = subprocess.run([sys.executable, str(ROOT / rel)], cwd=str(ROOT), capture_output=True,
                               text=True, timeout=600, stdin=subprocess.DEVNULL,
                               env={**os.environ, "PYTHONPATH": str(ROOT)})
            if r.returncode != 0:
                lacks.append(f"{rel} rc={r.returncode}: {(r.stdout + r.stderr)[-300:]!r}")
    check("test_the_cc_proofs_that_ran_the_bash_run_the_py_and_bare_box_is_retired", not lacks,
          "; ".join(lacks))


def test_the_bash_is_absent_from_the_tree_and_the_index() -> None:
    on_disk = (ROOT / BASH_REL).exists()
    r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--", BASH_REL], capture_output=True,
                       text=True, timeout=60)
    indexed = bool(r.stdout.strip())
    check("test_the_bash_is_absent_from_the_tree_and_the_index",
          r.returncode == 0 and not on_disk and not indexed,
          f"on_disk={on_disk} indexed={indexed} git_rc={r.returncode}")


def test_nothing_live_names_the_bash() -> None:
    r = subprocess.run(["git", "-C", str(ROOT), "ls-files", "--", "cairn", "bin"], capture_output=True,
                       text=True, timeout=60)
    hits = sorted(rel for rel in r.stdout.split("\n")
                  if rel and not RECORD.search(rel) and rel not in NOT_A_LAUNCHER
                  and BASH_NAMED.search(_text(rel)))
    check("test_nothing_live_names_the_bash", r.returncode == 0 and not hits,
          f"git_rc={r.returncode} {len(hits)} file(s) name the bash: {hits}")


def main() -> int:
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            try:
                fn()
            except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
                check(name, False, f"raised {type(exc).__name__}: {exc}")
    print("\nGREEN" if not _failures else f"\nRED — {len(_failures)} failure(s)")
    return 1 if _failures else 0


if __name__ == "__main__":
    raise SystemExit(main())
