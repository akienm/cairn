"""The lab-twin tooth of the commit door: a charter lands in cairn only after its lab copy lands
in the commons beside it.

    python3 -m cairn.devices.tester.lab_twin <repo>     # exit 0 clean, 2 refused

WHY (ticket 39be1c54f091, measured 2026-11-16). ``CairnCommons/intentions-congruency-lab/`` is a
committed copy, in a second repo, of every ``intention+why.json`` in this one. Since 2026-10-16,
304 charter writes landed on cairn main; the lab never held 13 of them and 64 more caught up
30 minutes to 19 hours late, and every proof that reads the lab reds in that window. Nothing
tied the cairn commit to its commons twin, so the twin landed whenever somebody happened to
recompile.

THE ORDER IS MECHANISM, NOT A QUESTION. The commons lands first: a cairn commit on main (or,
through pre-merge-commit, a land into main) that stages a charter is refused until the commons beside holds the
same bytes at its HEAD, under the name the compiler gives that charter. A charter the commit
deletes needs its lab copy already gone. The refusal names what to do:
``land the commons lab copy <name> first``.

ONLY MAIN IS JUDGED (orchestrator, 2026-11-16: the spec is "a cairn commit on main"). A builder's
branch commit cannot have its twin on commons main yet, because the twin lands with the branch,
and a detached HEAD (a hollow scratch worktree, a rebase step) is on no branch at all. So the
tooth asks only when HEAD is ``refs/heads/main``; a merge into main is judged because git runs
pre-merge-commit with HEAD still naming the branch being merged into.

The commons beside is ``<repo>/../CairnCommons``, the same sibling the compiler derives. Its
HEAD is read, never its working tree: an uncommitted lab copy has not landed.
"""

from __future__ import annotations

import os
import subprocess
import sys

from cairn.tools.intentions_model_compiler.compiler import gather_sources, lab_filename

CHARTER = "intention+why.json"
LAB = "intentions-congruency-lab"
MAIN = "refs/heads/main"


def _git(repo: str, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", repo, *args], capture_output=True)


def staged_charters(repo: str) -> list[tuple[str, str]]:
    """(status, path) for every charter the index changes against HEAD: A, M or D. Renames are
    split into a delete and an add, so each end is judged on its own."""
    r = _git(repo, "diff", "--cached", "--name-status", "--no-renames", "-z")
    if r.returncode != 0:
        raise RuntimeError(f"git diff --cached failed: {r.stderr.decode(errors='replace').strip()}")
    parts = r.stdout.decode().split("\0")
    out = []
    for i in range(0, len(parts) - 1, 2):
        status, path = parts[i], parts[i + 1]
        if os.path.basename(path) == CHARTER and status[:1] in "AMD":
            out.append((status[:1], path))
    return out


def _deleted_name(path: str) -> str:
    rel = os.path.dirname(path)
    return lab_filename({"kind": "component-charter",
                         "id": "repo-root" if rel in ("", ".") else rel.replace("/", "-")})


def on_main(repo: str) -> bool:
    """HEAD names main: a commit on main, or a merge into it (git has not moved HEAD yet)."""
    r = _git(repo, "symbolic-ref", "-q", "HEAD")
    return r.returncode == 0 and r.stdout.decode().strip() == MAIN


def lacks(repo: str) -> list[str]:
    """Every charter change in the index whose commons twin has not landed, one line each.
    Empty off main: only a commit or merge onto main is judged."""
    repo = os.path.abspath(repo)
    if not on_main(repo):
        return []
    changed = staged_charters(repo)
    if not changed:
        return []
    commons = os.path.join(os.path.dirname(repo), "CairnCommons")
    head = _git(commons, "rev-parse", "--short", "HEAD")
    if head.returncode != 0:
        return [f"{p}: no commons beside at {commons}, so its lab copy cannot have landed; "
                f"commit from a checkout with CairnCommons beside it" for _, p in changed]
    at = head.stdout.decode().strip()
    names = {os.path.relpath(s["path"], repo).replace(os.sep, "/"): lab_filename(s)
             for s in gather_sources(commons, repo) if s["kind"] == "component-charter"}
    found = []
    for status, path in changed:
        if status == "D":
            name = _deleted_name(path)
            if _git(commons, "cat-file", "-e", f"HEAD:{LAB}/{name}").returncode == 0:
                found.append(f"{path} is deleted but commons HEAD {at} still holds {LAB}/{name}: "
                             f"land the commons lab copy {name}'s removal first")
            continue
        name = names.get(path)
        if name is None:    # not a lab source (under proofs/, validations/ or a dot dir)
            continue
        staged = _git(repo, "show", f":{path}").stdout
        twin = _git(commons, "show", f"HEAD:{LAB}/{name}")
        if twin.returncode != 0:
            found.append(f"{path} is staged ({len(staged)} bytes) and commons HEAD {at} has no "
                         f"{LAB}/{name}: land the commons lab copy {name} first")
        elif twin.stdout != staged:
            found.append(f"{path} is staged ({len(staged)} bytes) and commons HEAD {at} holds "
                         f"{LAB}/{name} at {len(twin.stdout)} bytes: land the commons lab copy "
                         f"{name} first")
    return found


def main(argv: list[str]) -> int:
    repo = argv[0] if argv else "."
    try:
        found = lacks(repo)
    except Exception as exc:  # noqa: BLE001 — a door that cannot judge refuses, loudly (Law 7)
        print(f"lab twin: cannot judge the index: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if not found:
        return 0
    print("REFUSED — a charter lands in cairn only after its lab twin lands in the commons "
          "(recompile there with cairn/tools/intentions_model_compiler/recompile_gate.sh from "
          "this checkout, commit the lab copy, then commit here):", file=sys.stderr)
    for line in found:
        print(f"  {line}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
