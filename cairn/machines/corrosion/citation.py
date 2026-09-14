"""Ruling-citation detector for the corrosion predicate.

Given a constraint-bearing artifact's path, determines whether a confirmed
ruling in CairnCommons/decisions/ covers the change. The ticket defines
'a ruling in the same act' as: a ruling packet whose id is cited in the
commit that weakened the constraint, or which lands in the same commit.

This implementation checks two things:
  1. Does a confirmed ruling's what_conforms include this path?
  2. Was a ruling file co-committed with the change to this path?

Since 2026-09-14 (ticket 9adc6fddf185) there is a third, and it is the live one: was an
ANSWERED question (CairnCommons/questions/open-<id>.json, the inbox lane) named in the
commit that made the change? A decision Akien makes is a question bound to its ticket
and answered in the inbox; ``cairn ruling open`` is retired and decisions/ is read-only
record, so the standing rulings keep resolving and new authority arrives as answers.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path

_CAIRN_ROOT = Path(__file__).resolve().parents[3]


def _commons_root() -> Path:
    """Where the commons is, resolved so a CHECKOUT OF THIS REPO still finds it.

    The sibling-of-my-own-root rule is right for the working checkout and WRONG
    for every git worktree, because a worktree has no commons beside it. That is
    not a hypothetical: measured 2026-09-10, the hollow runner builds its scratch
    worktree under /tmp, this resolver returned /tmp/<scratch>/CairnCommons, the
    store read as absent, and EVERY declared ruling silently stopped resolving —
    so a tooth asserting the live exemption set is justified failed at HEAD, and
    the hollow reading could not be taken at all. The failure is quiet in the
    dangerous direction: an absent store makes ruling_covers_path return None,
    which reads as "no ruling covers this" rather than "I could not look".

    Three resolutions, most explicit first. A worktree shares the main checkout's
    commons BY CONSTRUCTION — git's common dir names the checkout it was cut from —
    so the second rule is a fact about the repo, not a guess about the filesystem.
    """
    env = os.environ.get("CAIRN_COMMONS_ROOT")
    if env:
        return Path(env)
    beside = _CAIRN_ROOT.parent / "CairnCommons"
    if beside.is_dir():
        return beside
    try:
        common = subprocess.run(
            ["git", "-C", str(_CAIRN_ROOT), "rev-parse", "--git-common-dir"],
            capture_output=True, text=True, timeout=10)
        if common.returncode == 0 and common.stdout.strip():
            gitdir = Path(common.stdout.strip())
            if not gitdir.is_absolute():
                gitdir = (_CAIRN_ROOT / gitdir).resolve()
            main_checkout = gitdir.parent
            cut_from = main_checkout.parent / "CairnCommons"
            if cut_from.is_dir():
                return cut_from
    except Exception:
        pass
    return beside


def _rulings_store() -> Path:
    return _commons_root() / "decisions"


def _questions_store() -> Path:
    """Where answered questions live — the SAME lane the operator inbox reads. Since
    2026-09-14 (ticket 9adc6fddf185) a decision Akien makes is a question bound to its
    ticket and answered in the inbox, not a ruling; decisions/ is read-only record."""
    env = os.environ.get("CAIRN_QUESTIONS_DIR")
    if env:
        return Path(env)
    return _commons_root() / "questions"


_QUESTION_ID = re.compile(r"\bopen-[0-9a-f]{12}\b")


def answered_question(qid: str) -> tuple[bool, str]:
    """Does this question id open as an ANSWERED question? Returns (ok, why_not).

    Same-act evidence in the shape the question door writes (``cairn question answer``):
    the record is resolved and carries his words. An UNANSWERED question is not evidence —
    it is the decision still owed — so it resolves False, by design.
    """
    if not isinstance(qid, str) or not qid.strip():
        return False, "evidence is empty — a question kind must name an open-<id>"
    qid = qid.strip()
    if not qid.startswith("open-"):
        qid = "open-" + qid
    path = _questions_store() / (qid + ".json")
    if not path.is_file():
        return False, "no question file at %s" % path.name
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as e:
        return False, "question file unreadable: %s" % e
    if not isinstance(record, dict):
        return False, "question file is not an object"
    if not record.get("resolved"):
        return False, "question %s is still open — the decision is owed, not made" % qid
    if not (isinstance(record.get("answer"), str) and record["answer"].strip()):
        return False, "question %s is marked resolved but carries no answer" % qid
    return True, ""


def question_cited_in_commit(rel_path: str, commit: str | None = None,
                             repo: Path | None = None) -> str | None:
    """The id of an ANSWERED question named in the commit that last changed rel_path, or None.

    The question twin of ``ruling_cited_in_commit``: 'in the same act' is the commit
    message naming an open-<id> whose record is answered. A named-but-unanswered question
    does not count — see ``answered_question``.
    """
    repo = repo or _CAIRN_ROOT
    if commit is None:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo), "log", "-1", "--format=%H", "--", rel_path],
                capture_output=True, text=True, timeout=10)
            commit = result.stdout.strip()
        except Exception:
            return None
    if not commit:
        return None
    try:
        msg_result = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%B", commit],
            capture_output=True, text=True, timeout=10)
        message = msg_result.stdout
    except Exception:
        return None
    for qid in _QUESTION_ID.findall(message):
        ok, _ = answered_question(qid)
        if ok:
            return qid
    return None


def ruling_covers_path(rel_path: str) -> str | None:
    """Return the id of a confirmed ruling whose what_conforms includes rel_path, or None.

    A ruling covers a path when:
      - It is kind: "ruling" (not a legacy decision)
      - It is confirmed (has a confirmed field)
      - Its what_conforms list includes the path (exact match or prefix match)
    """
    store = _rulings_store()
    if not store.is_dir():
        return None
    for name in sorted(store.iterdir()):
        if not name.suffix == ".json":
            continue
        try:
            record = json.loads(name.read_text(encoding="utf-8"))
        except Exception:
            continue
        if not isinstance(record, dict):
            continue
        if record.get("kind") != "ruling":
            continue
        if not record.get("confirmed"):
            continue
        for p in record.get("what_conforms") or []:
            if p == rel_path or rel_path.startswith(p + "/"):
                return record.get("id")
    return None


def ruling_cited_in_commit(rel_path: str, commit: str | None = None,
                           repo: Path | None = None) -> str | None:
    """Check if a ruling was cited in the commit that last changed rel_path.

    Returns the ruling id if found, None otherwise.

    'Cited' means:
      - The commit message contains a ruling id (a YYYY-MM-DD-slug pattern
        matching a file in CairnCommons/decisions/), OR
      - A file in CairnCommons/decisions/ was also changed in the same commit
    """
    repo = repo or _CAIRN_ROOT
    if commit is None:
        try:
            result = subprocess.run(
                ["git", "-C", str(repo), "log", "-1", "--format=%H", "--", rel_path],
                capture_output=True, text=True, timeout=10)
            commit = result.stdout.strip()
        except Exception:
            return None
    if not commit:
        return None

    try:
        msg_result = subprocess.run(
            ["git", "-C", str(repo), "log", "-1", "--format=%B", commit],
            capture_output=True, text=True, timeout=10)
        message = msg_result.stdout
    except Exception:
        message = ""

    store = _rulings_store()
    if not store.is_dir():
        return None
    ruling_ids = set()
    for name in store.iterdir():
        if name.suffix == ".json":
            stem = name.stem
            ruling_ids.add(stem)

    for rid in ruling_ids:
        if rid in message:
            return rid

    try:
        files_result = subprocess.run(
            ["git", "-C", str(repo), "diff-tree", "--no-commit-id", "-r",
             "--name-only", commit],
            capture_output=True, text=True, timeout=10)
        changed_files = files_result.stdout.strip().splitlines()
    except Exception:
        changed_files = []

    commons_rel = os.path.relpath(str(store), str(repo))
    for f in changed_files:
        if f.startswith(commons_rel) or f.startswith("CairnCommons/decisions/"):
            stem = Path(f).stem
            if stem in ruling_ids:
                return stem

    return None
