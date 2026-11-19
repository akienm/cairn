#!/usr/bin/env python3
"""Proof that approve refuses a caller over ssh, Akien's included (ticket a9cf64d1f92e; outline 17.2.2, Q#115).

Measured 2026-11-18 on akiendelllinux: an ssh login's shell sits in session-<n>.scope, which
classify() reads as akien, under an sshd-session parent. CC on another box logs in with the same
key Akien's own ssh would use, so a CC over ssh could approve a hand edit as him. Until CC has its
own key (ticket 62e7bff757c0), approve refuses any caller with an sshd ancestor.

Teeth, one per outcome (PROVES below); the ancestry is injected (``ancestry`` replaced on the
module) except in tooth 1, which reads this process's own:
  (1) ancestry() records each pid's /proc comm;
  (2) caller() over an akien-scope leaf under sshd-session carries ssh = that pid;
  (3) caller() over an akien-scope leaf with no sshd ancestor carries no ssh;
  (4) approve refuses an akien caller carrying ssh, naming the ssh login;
  (5) approve from an akien caller without ssh is not refused for ssh (it reaches the words check).

    bin/cairn test --seal cairn/tools/artifact/proofs/test_approve_refuses_a_caller_over_ssh.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"a9cf64d1f92e": {
    "1": "test_ancestry_records_each_comm",
    "2": "test_an_sshd_ancestor_marks_the_caller",
    "3": "test_a_local_terminal_carries_no_ssh",
    "4": "test_approve_refuses_an_ssh_caller",
    "5": "test_approve_from_the_box_passes_the_ssh_check",
}}

SESSION = "/user.slice/user-1000.slice/session-4397.scope"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _A():
    """The door, bound at call time: a reverted subject reds the teeth instead of crashing the reader."""
    from cairn.tools.artifact import artifact as A
    return A


def _caller(chain_spec: list[tuple[str, str]]) -> dict:
    """caller() over an injected ancestry, leaf first: each (cgroup, comm)."""
    A = _A()
    chain = [{"pid": 2000 + i, "cgroup": cg, "class": A.classify(cg)["class"], "comm": comm}
             for i, (cg, comm) in enumerate(chain_spec)]
    env = {k: v for k, v in os.environ.items() if k not in ("CAIRN_USER", "CLAUDECODE")}
    with mock.patch.object(A, "ancestry", lambda *a, **k: chain), \
         mock.patch.dict(os.environ, env, clear=True):
        return A.caller()


def _approve_as(who: dict) -> str:
    """approve()'s refusal text for a given caller record, with empty words; '' if it did not refuse."""
    A = _A()
    with mock.patch.object(A, "caller", lambda: who):
        try:
            A.approve("no-such-park", "")
        except A.Refused as exc:
            return str(exc)
    return ""


def test_ancestry_records_each_comm() -> None:
    chain = _A().ancestry()
    want = Path(f"/proc/{os.getpid()}/comm").read_text().strip()
    got = chain[0].get("comm") if chain else None
    check("test_ancestry_records_each_comm", got == want and all("comm" in a for a in chain), f"{got!r} vs {want!r}")


def test_an_sshd_ancestor_marks_the_caller() -> None:
    got = _caller([(SESSION, "bash"), (SESSION, "sshd-session"), (SESSION, "sshd-session")])
    check("test_an_sshd_ancestor_marks_the_caller",
          got.get("class") == "akien" and got.get("ssh") == 2001, f"class={got.get('class')} ssh={got.get('ssh')}")


def test_a_local_terminal_carries_no_ssh() -> None:
    got = _caller([(SESSION, "bash"), (SESSION, "konsole")])
    check("test_a_local_terminal_carries_no_ssh",
          got.get("class") == "akien" and not got.get("ssh"), f"class={got.get('class')} ssh={got.get('ssh')}")


def test_approve_refuses_an_ssh_caller() -> None:
    said = _approve_as({"class": "akien", "who": "Akien", "cgroup": SESSION, "ssh": 2001})
    check("test_approve_refuses_an_ssh_caller", "ssh" in said and "needs his words" not in said, said)


def test_approve_from_the_box_passes_the_ssh_check() -> None:
    said = _approve_as({"class": "akien", "who": "Akien", "cgroup": SESSION})
    check("test_approve_from_the_box_passes_the_ssh_check", "needs his words" in said, said)


def main() -> int:
    for tooth in (test_ancestry_records_each_comm, test_an_sshd_ancestor_marks_the_caller,
                  test_a_local_terminal_carries_no_ssh, test_approve_refuses_an_ssh_caller,
                  test_approve_from_the_box_passes_the_ssh_check):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
