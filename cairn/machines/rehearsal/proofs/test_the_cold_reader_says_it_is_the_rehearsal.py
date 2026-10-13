"""Proof for ticket ``a135bdb13646`` — a rehearsal's cold reader says it is the rehearsal.

Akien, 2026-10-13: *"if CAIRN_USER is set, then it's you... if it's not, then it's me."*
Measured the same day: ``claude_reader`` strips CLAUDECODE so ``claude -p`` runs outside the
session, and the child then carries neither marker — once CAIRN_OPERATOR rides every shell it
would read as Akien's hand. The child now carries CAIRN_USER=rehearsal.

``subprocess.run`` is monkeypatched to capture the child's env and return a minimal JSON
envelope, so no claude process is spawned. Teeth, one per falsifier clause (PROVES below):
  (1) the captured env has CAIRN_USER == 'rehearsal';
  (2) it has no CLAUDECODE.
Hollow: today's rehearsal.py reds 1.

    bin/cairn test cairn/machines/rehearsal/proofs/test_the_cold_reader_says_it_is_the_rehearsal.py
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"a135bdb13646": {
    "1": "test_the_child_says_it_is_the_rehearsal",
    "2": "test_the_child_is_outside_the_session",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _child_env() -> dict:
    """One claude_reader call with the parent in a session (CLAUDECODE set, no CAIRN_USER);
    returns the env the child would have been spawned with."""
    from cairn.machines.rehearsal import rehearsal

    seen: dict = {}

    def fake_run(cmd, **kw):
        seen.update(kw.get("env") or {})
        out = json.dumps({"structured_output": {"steps": []}, "is_error": False,
                          "total_cost_usd": 0, "duration_ms": 1, "session_id": "proof"})
        return subprocess.CompletedProcess(cmd, 0, stdout=out, stderr="")

    saved = {k: os.environ.get(k) for k in ("CLAUDECODE", "CAIRN_USER")}
    real = rehearsal.subprocess.run
    os.environ["CLAUDECODE"] = "1"
    os.environ.pop("CAIRN_USER", None)
    rehearsal.subprocess.run = fake_run
    try:
        rehearsal.claude_reader("prompt", {"type": "object"})
    finally:
        rehearsal.subprocess.run = real
        for k, v in saved.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
    return seen


def test_the_child_says_it_is_the_rehearsal() -> None:
    env = _child_env()
    check("test_the_child_says_it_is_the_rehearsal", env.get("CAIRN_USER") == "rehearsal",
          f"CAIRN_USER={env.get('CAIRN_USER')!r}")


def test_the_child_is_outside_the_session() -> None:
    env = _child_env()
    check("test_the_child_is_outside_the_session", bool(env) and "CLAUDECODE" not in env,
          f"{len(env)} vars, CLAUDECODE present: {'CLAUDECODE' in env}")


def main() -> int:
    for tooth in (test_the_child_says_it_is_the_rehearsal, test_the_child_is_outside_the_session):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
