#!/usr/bin/env python3
"""Proof that build_inspector reds a ticket whose build is on main while its cursor stands
before BUILDME (ticket a4a3f5634e7c).

Measured 2026-11-14 on akiendell: 42 tickets at [TICKETME:...] were named by a code commit on
origin/main, built and landed without a BUILDME crossing. Measured 2026-11-22: 88e30cde9bd4's
build landed on main (b02b26a59, 13:45:42) while its cursor read FIXME, five minutes before its
BUILDME crossing (13:50:43), so the cursor test is every stage the ticket's own path places
before BUILDME, not TICKETME alone.

  (1) a ticket whose cursor stands before BUILDME in its path (TICKETME or FIXME) and whose id is
      named by a code commit newer than its latest forward BUILDME crossing is reported, with
      that commit's sha and the cursor;
  (2) a ticket whose only naming commit changes press_office/ or a .md file, a ticket named only
      after the subject's first colon, a ticket at or past BUILDME with a code commit, and a
      TICKETME ticket named by no commit are each NOT reported, and a FIXME ticket whose naming
      code commits all predate its latest forward BUILDME crossing is NOT reported.

Clause 1's tooth also reads that inspect() calls the scan and that one call runs one git log.

    PYTHONPATH=. python3 cairn/devices/codemother/machines/build_inspector/proofs/test_a_ticket_whose_build_is_on_main_has_crossed.py
"""

from __future__ import annotations

import inspect as _inspect
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(_REPO))

from cairn.devices.codemother.machines.build_inspector import inspector  # noqa: E402

PROVES = {"a4a3f5634e7c": {
    "1": "test_clause_1_a_build_on_main_before_buildme_is_reported",
    "2": "test_clause_2_the_lookalikes_are_not_reported",
}}

FAILURES: list[str] = []

A, B, H = "aaaaaaaaaaa1", "bbbbbbbbbbb2", "cccccccccc03"          # reported
DOC, AFTER, PAST, NONE, OLD = ("ddddddddddd4", "eeeeeeeeeee5", "fffffffffff6",
                               "aaaaaaaaaa07", "bbbbbbbbbb08")     # not reported

_TM = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
_FX = "code-seam@v2: THINKME -> TICKETME -> [FIXME] -> BUILDME -> PROVEME -> PROVED"
_BM = "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _git(repo: Path, *args: str, when: str | None = None) -> None:
    env = dict(os.environ, GIT_AUTHOR_NAME="t", GIT_AUTHOR_EMAIL="t@t", GIT_COMMITTER_NAME="t",
               GIT_COMMITTER_EMAIL="t@t", GIT_CONFIG_NOSYSTEM="1", HOME=str(repo.parent))
    if when:
        env["GIT_COMMITTER_DATE"] = env["GIT_AUTHOR_DATE"] = when
    subprocess.run(["git", "-C", str(repo), *args], check=True, env=env,
                   capture_output=True, text=True)


def _commit(repo: Path, subject: str, paths: list[str], when: str) -> None:
    for p in paths:
        f = repo / p
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(f.read_text() + "x\n" if f.exists() else "x\n")
    _git(repo, "add", "--", *paths)
    _git(repo, "commit", "-q", "-m", subject, when=when)


def _scratch(tmp: Path) -> Path:
    """<tmp>/repo (a git repo on main, holding cairn/) and <tmp>/CairnCommons/tickets."""
    repo, tickets = tmp / "repo", tmp / "CairnCommons" / "tickets"
    (repo / "cairn").mkdir(parents=True)
    tickets.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    for tid, wf in ((A, _TM), (B, _FX), (H, _TM), (DOC, _TM), (AFTER, _TM), (PAST, _BM),
                    (NONE, _TM), (OLD, _FX)):
        (tickets / f"{tid}-t.json").write_text(json.dumps(
            {"id": tid, "title": "t", "workflow_and_state": wf}), encoding="utf-8")
    # Forward BUILDME crossings at noon on the 20th for the FIXME tickets (B kicked back after).
    entries = [{"ticket": t, "at": "2026-11-20T12:00:00", "from": "TICKETME", "to": "BUILDME",
                "direction": "forward"} for t in (B, OLD, PAST)]
    (repo / "cairn" / "x" / "history.json").parent.mkdir(parents=True)
    (repo / "cairn" / "x" / "history.json").write_text(json.dumps({"entries": entries}))
    _commit(repo, "seed: start", ["cairn/x/seed.py"], "2026-11-01T00:00:00")
    _commit(repo, f"{OLD}: build", ["cairn/x/old.py"], "2026-11-19T12:00:00")
    _commit(repo, f"{A}: build", ["cairn/x/a.py"], "2026-11-21T12:00:00")
    _commit(repo, f"{B}: build", ["cairn/x/b.py"], "2026-11-21T12:00:00")
    _commit(repo, f"{H}, {A}: both", ["cairn/x/h.py"], "2026-11-21T13:00:00")
    _commit(repo, f"{DOC}: docs", ["press_office/x.py", "cairn/x/README.md"], "2026-11-21T12:00:00")
    _commit(repo, f"other: mentions {AFTER}", ["cairn/x/after.py"], "2026-11-21T12:00:00")
    _commit(repo, f"{PAST}: build", ["cairn/x/past.py"], "2026-11-21T12:00:00")
    return repo / "cairn"


def _run(root: Path) -> tuple[list[dict] | None, int]:
    scan = getattr(inspector, "built_before_buildme", None)
    if scan is None:
        return None, 0
    logs = 0
    real = subprocess.run

    def counting(cmd, *a, **k):
        nonlocal logs
        if isinstance(cmd, (list, tuple)) and "git" in str(cmd[0]) and "log" in cmd:
            logs += 1
        return real(cmd, *a, **k)

    subprocess.run = counting
    try:
        return scan(root), logs
    finally:
        subprocess.run = real


def _by_ticket(found: list[dict]) -> dict[str, dict]:
    return {(f.get("values") or {}).get("ticket"): f.get("values") or {} for f in found}


def test_clause_1_a_build_on_main_before_buildme_is_reported() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = _scratch(Path(td))
        found, logs = _run(root)
        if found is None:
            check("test_clause_1_a_build_on_main_before_buildme_is_reported", False,
                  "inspector.built_before_buildme does not exist")
            return
        got = _by_ticket(found)
        wired = "built_before_buildme(root)" in _inspect.getsource(getattr(inspector, "_inspect", None) or inspector.inspect)
        ok = (set(got) >= {A, B, H}
              and got.get(A, {}).get("cursor") == "TICKETME" and len(got.get(A, {}).get("commits", [])) == 2
              and got.get(B, {}).get("cursor") == "FIXME" and len(got.get(B, {}).get("commits", [])) == 1
              and len(got.get(H, {}).get("commits", [])) == 1
              and logs == 1 and wired)
        check("test_clause_1_a_build_on_main_before_buildme_is_reported", ok,
              f"reported {sorted(got)}; A {got.get(A)}; B {got.get(B)}; git log calls {logs}; "
              f"wired into inspect() {wired}")


def test_clause_2_the_lookalikes_are_not_reported() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = _scratch(Path(td))
        found, _ = _run(root)
        if found is None:
            check("test_clause_2_the_lookalikes_are_not_reported", False,
                  "inspector.built_before_buildme does not exist")
            return
        wrong = sorted(set(_by_ticket(found)) & {DOC, AFTER, PAST, NONE, OLD})
        check("test_clause_2_the_lookalikes_are_not_reported", not wrong and len(found) == 3,
              f"wrongly reported {wrong}; {len(found)} findings")


if __name__ == "__main__":
    test_clause_1_a_build_on_main_before_buildme_is_reported()
    test_clause_2_the_lookalikes_are_not_reported()
    print(f"{len(FAILURES)} failed" if FAILURES else "all teeth green")
    raise SystemExit(1 if FAILURES else 0)
