"""Proof for ticket a4a3f5634e7c — a ticket whose build is on main has crossed BUILDME.

``built_but_uncrossed`` reds a ticket whose cursor still reads [TICKETME:...] while the repo's log carries a code commit
whose subject names its id before the first colon. The world is a scratch git repo with a sibling scratch commons, never
live origin/main, so the proof does not go red as the real backlog clears (the orchestrator's rule for this ticket).

    python <this file>
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.machines.build_inspector.inspector import built_but_uncrossed  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "a4a3f5634e7c": {
        "1": "a_ticketme_ticket_named_by_a_code_commit_is_reported_with_its_sha",
        "2": "the_non_cases_are_not_reported",
    },
}

TICKETME = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
PROVED = "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]"

BUILT = "aaaaaaaaaaaa"        # TICKETME, a build commit names it in the lead
SEALED = "111111111111"       # TICKETME, only a seal commit names it: the 31-of-47 case
DOCONLY = "bbbbbbbbbbbb"      # TICKETME, named only by an outline (press_office) and a .md commit
MENTION = "cccccccccccc"      # TICKETME, named only after the colon
PAST = "dddddddddddd"         # PROVED, named by a code commit
UNNAMED = "eeeeeeeeeeee"      # TICKETME, named by no commit


def _git(repo: Path, *args: str) -> str:
    env = dict(os.environ, GIT_AUTHOR_NAME="p", GIT_AUTHOR_EMAIL="p@p", GIT_COMMITTER_NAME="p", GIT_COMMITTER_EMAIL="p@p")
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env, check=True).stdout.strip()


def _commit(repo: Path, rel: str, subject: str) -> str:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(subject + "\n", encoding="utf-8", newline="\n")
    _git(repo, "add", rel)
    _git(repo, "-c", "commit.gpgsign=false", "commit", "-q", "-m", subject)
    return _git(repo, "rev-parse", "--short=9", "HEAD")


def _world():
    tmp = Path(str(scratch_dir("built_uncrossed_proof_")))
    repo = tmp / "repo"
    (repo / "cairn").mkdir(parents=True)
    _git(repo, "init", "-q")
    tickets = tmp / "CairnCommons" / "tickets"
    tickets.mkdir(parents=True)
    for tid, state in ((BUILT, TICKETME), (SEALED, TICKETME), (DOCONLY, TICKETME), (MENTION, TICKETME),
                       (PAST, PROVED), (UNNAMED, TICKETME)):
        (tickets / f"{tid}-a-ticket.state.json").write_text(json.dumps({"workflow_and_state": state}), encoding="utf-8", newline="\n")
    shas = {
        BUILT: _commit(repo, "cairn/x/x.py", f"{BUILT}: build the thing"),
        SEALED: _commit(repo, "cairn/y/validations/v.json", f"{SEALED}: Linux seal of its proofs"),
    }
    _commit(repo, "press_office/outline.txt", f"{DOCONLY}: outline 3.3.5 asked a question")
    _commit(repo, "notes/n.md", f"{DOCONLY}: a note")
    _commit(repo, "cairn/z/z.py", f"outline note: see {MENTION}")
    _commit(repo, "cairn/w/w.py", f"{PAST}: build the other thing")
    return tmp, repo / "cairn", shas


def a_ticketme_ticket_named_by_a_code_commit_is_reported_with_its_sha() -> None:
    tmp, root, shas = _world()
    try:
        found = {f["component"]: f for f in built_but_uncrossed(root)}
        for tid in (BUILT, SEALED):
            assert tid in found, f"{tid} is a TICKETME ticket named by a code commit and was not reported: {sorted(found)}"
            assert shas[tid] in found[tid]["values"]["commits"], f"the red for {tid} omits its commit {shas[tid]}: {found[tid]}"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def the_non_cases_are_not_reported() -> None:
    tmp, root, _ = _world()
    try:
        reported = {f["component"] for f in built_but_uncrossed(root)}
        for tid, why in ((DOCONLY, "named only by a press_office and a .md commit"), (MENTION, "named only after the colon"),
                         (PAST, "already past TICKETME"), (UNNAMED, "named by no commit")):
            assert tid not in reported, f"{tid} ({why}) was reported: a false red"
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


TEETH = [a_ticketme_ticket_named_by_a_code_commit_is_reported_with_its_sha, the_non_cases_are_not_reported]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:500]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
