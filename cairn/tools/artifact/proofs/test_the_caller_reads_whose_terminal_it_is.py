#!/usr/bin/env python3
"""Proof that the caller record reads whose terminal it is from the environment (8a53046951bb).

Measured 2026-10-13: ``caller()`` decided the class from cgroups alone, so a terminal Akien
opens on the same box as CC's often read 'unknown' — someone answered a question and the
system could not tell who. Akien: *"if CAIRN_USER is set, then it's you... if it's not, then
it's me."* He put ``export CAIRN_OPERATOR=Akien`` in ~/.bashrc, and Claude Code snapshots
~/.bashrc, so CC's shells carry it too: CC evidence (a cc scope up the tree, CAIRN_USER,
CLAUDECODE) must win, and the environment may never turn a measured cc into akien.

Teeth, one per falsifier clause (PROVES below), with the ancestry and the environment
injected (``ancestry`` replaced on the module, ``os.environ`` patched for the call):
  (1) leaf unknown, CAIRN_OPERATOR=Akien, nothing else -> akien, who Akien, via env;
  (2) leaf unknown, CAIRN_USER=cc0, CAIRN_OPERATOR=Akien -> cc, who cc0;
  (3) leaf unknown, CLAUDECODE=1, CAIRN_OPERATOR=Akien -> cc, who cc;
  (4) a cc scope in the ancestry, CAIRN_OPERATOR=Akien, nothing else -> cc;
  (5) leaf unknown, nothing set -> unknown, who None.
Hollow: today's artifact.py reds 1, 2 and 3.

    bin/cairn test cairn/tools/artifact/proofs/test_the_caller_reads_whose_terminal_it_is.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest import mock

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"8a53046951bb": {
    "1": "test_an_operator_terminal_is_akien",
    "2": "test_cairn_user_names_the_cc",
    "3": "test_claudecode_is_cc",
    "4": "test_the_env_cannot_upgrade_a_measured_cc",
    "5": "test_nothing_set_stays_unknown",
}}

APP = "/user.slice/user-1000.slice/user@1000.service/app.slice"
UNKNOWN_LEAF = "/user.slice/user-1000.slice/user@1000.service"
ENV_KEYS = ("CAIRN_USER", "CLAUDECODE", "CAIRN_OPERATOR")
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _caller(cgroups: list[str], env: dict[str, str]) -> dict:
    """caller() over an injected ancestry (leaf first) and an injected environment.

    Bound at call time: a reverted subject reds the teeth instead of crashing the reader."""
    from cairn.tools.artifact import artifact as A
    chain = [{"pid": 1000 + i, "cgroup": cg, "class": A.classify(cg)["class"]}
             for i, cg in enumerate(cgroups)]
    base = {k: v for k, v in os.environ.items() if k not in ENV_KEYS}
    with mock.patch.object(A, "ancestry", lambda *a, **k: chain), \
         mock.patch.dict(os.environ, {**base, **env}, clear=True):
        return A.caller()


def _shape(got: dict) -> tuple:
    return got.get("class"), got.get("who"), got.get("via")


def test_an_operator_terminal_is_akien() -> None:
    got = _caller([UNKNOWN_LEAF], {"CAIRN_OPERATOR": "Akien"})
    check("test_an_operator_terminal_is_akien", _shape(got) == ("akien", "Akien", "env"), str(_shape(got)))


def test_cairn_user_names_the_cc() -> None:
    got = _caller([UNKNOWN_LEAF], {"CAIRN_USER": "cc0", "CAIRN_OPERATOR": "Akien"})
    check("test_cairn_user_names_the_cc", _shape(got)[:2] == ("cc", "cc0"), str(_shape(got)))


def test_claudecode_is_cc() -> None:
    got = _caller([UNKNOWN_LEAF], {"CLAUDECODE": "1", "CAIRN_OPERATOR": "Akien"})
    check("test_claudecode_is_cc", _shape(got)[:2] == ("cc", "cc"), str(_shape(got)))


def test_the_env_cannot_upgrade_a_measured_cc() -> None:
    got = _caller([UNKNOWN_LEAF, f"{APP}/superclaude-42.scope"], {"CAIRN_OPERATOR": "Akien"})
    check("test_the_env_cannot_upgrade_a_measured_cc", got.get("class") == "cc", str(_shape(got)))


def test_nothing_set_stays_unknown() -> None:
    got = _caller([UNKNOWN_LEAF], {})
    check("test_nothing_set_stays_unknown",
          got.get("class") == "unknown" and got.get("who") is None, str(_shape(got)))


def main() -> int:
    for tooth in (test_an_operator_terminal_is_akien, test_cairn_user_names_the_cc,
                  test_claudecode_is_cc, test_the_env_cannot_upgrade_a_measured_cc,
                  test_nothing_set_stays_unknown):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
