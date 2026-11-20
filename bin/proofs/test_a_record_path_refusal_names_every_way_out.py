"""Proof for ticket 6cd13a3a5f42 — a record-path refusal names every way out, remove included.

MEASURED 2026-11-20: a Bash mv of the untracked wrong-OS seal
bin/validations/test_cairn_runs_from_cmd_with_no_bash.json was refused by bin/cmd/artifactgate,
and the refusal named only `cairn artifact write` and `cairn artifact hand-edit`. The door's
own exit for a record to delete or move away, `cairn artifact remove <path> --why`, was
found only by reading cairn/tools/artifact/__main__.py.

One tooth per falsifier clause, calling the gate's verdict() in process as
bin/proofs/test_artifact_gate.py does:

  1. a Bash mv and a Bash rm of that record each return refusal text naming
     `cairn artifact remove`;
  2. the after-run naming text (AFTER, formatted) names `cairn artifact remove`;
  3. what the gate refuses and allows is unchanged: bin/proofs/test_artifact_gate.py still
     passes, and `cairn artifact remove <record> --why x` is still allowed (verdict None).

    python3 bin/proofs/test_a_record_path_refusal_names_every_way_out.py     # exit 0 = green
"""

from __future__ import annotations

import importlib.machinery
import importlib.util
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]
_GATE = _REPO_ROOT / "bin" / "cmd" / "artifactgate"
_SIBLING = _REPO_ROOT / "bin" / "proofs" / "test_artifact_gate.py"
_RECORD = _REPO_ROOT / "bin" / "validations" / "test_cairn_runs_from_cmd_with_no_bash.json"
_WAY_OUT = "cairn artifact remove"

PROVES = {"6cd13a3a5f42": {"1": "test_a_mv_and_an_rm_of_a_record_name_remove",
                           "2": "test_the_after_run_naming_names_remove",
                           "3": "test_what_the_gate_refuses_is_unchanged"}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _load():
    """The subject is bound at CALL time: the hollow reading takes bin/cmd/artifactgate away."""
    spec = importlib.util.spec_from_loader(
        "artifactgate", importlib.machinery.SourceFileLoader("artifactgate", str(_GATE)))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _bash(gate, cmd: str):
    return gate.verdict("Bash", {"command": cmd})


def _teeth(gate) -> None:
    mv = _bash(gate, f"mv {_RECORD} /var/tmp/testing-6cd13a3a5f42-moved.json")
    rm = _bash(gate, f"rm {_RECORD}")
    check("test_a_mv_and_an_rm_of_a_record_name_remove",
          bool(mv) and bool(rm) and _WAY_OUT in mv and _WAY_OUT in rm,
          f"mv refused={bool(mv)} names remove={bool(mv) and _WAY_OUT in mv}; "
          f"rm refused={bool(rm)} names remove={bool(rm) and _WAY_OUT in rm}")

    after = gate.AFTER.format(paths="  " + str(_RECORD.relative_to(_REPO_ROOT)))
    check("test_the_after_run_naming_names_remove", _WAY_OUT in after,
          "AFTER lists no `cairn artifact remove`" if _WAY_OUT not in after else "")

    door = _bash(gate, f"cairn artifact remove {_RECORD} --why x")
    sib = subprocess.run([sys.executable, str(_SIBLING)], capture_output=True, text=True,
                         timeout=600, cwd=str(_REPO_ROOT))
    check("test_what_the_gate_refuses_is_unchanged", door is None and sib.returncode == 0,
          f"remove allowed={door is None}; test_artifact_gate rc={sib.returncode}"
          + ("" if sib.returncode == 0 else " " + sib.stdout[-600:]))


def main() -> int:
    if not _GATE.exists():
        print(f"the subject {_GATE} is absent")
        for n in PROVES["6cd13a3a5f42"].values():
            check(n, False, "subject absent")
        return 1
    try:
        _teeth(_load())
    except Exception as exc:  # noqa: BLE001 — a subject whose world was taken away
        print(f"the teeth could not run to the end: {exc!r}")
        for n in PROVES["6cd13a3a5f42"].values():
            if n not in FAILURES:
                check(n, False, f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
