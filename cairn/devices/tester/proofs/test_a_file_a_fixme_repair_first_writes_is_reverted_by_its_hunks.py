"""Teeth for ticket 6beb45934ebd: a file that a FIXME repair first writes is reverted by the repair's hunks, not removed.

MEASURED 2026-11-22 on 69075b0e8212's hollow (/home/akien/.akien/temp/h69075.txt). The ticket's
first build was 11-12 (anchor ea34a5d66d56). Two bin proofs were created later by OTHER tickets
(7989bb520e14 on 11-18, 95557c2ed44f on 11-16), and 69075's FIXME 1 repair (f76659ed8) edited
them. The hollow reverted each to the anchor, where it was absent, so it REMOVED them. The
tooth scans files for a bare bash argv, so with the files gone it read green, and both read
HOLLOW. Reverted by hand to f76659ed8^, each one reds the tooth.

THE RULE THESE TEETH HOLD. A file in writes_to that is absent at the anchor, where the oldest
ticket build commit touching it found it already present, is measured with that ticket's
hunks taken away (_revert_hunks). Removing the file would delete another ticket's work as the
counterfactual. A file the ticket's own first build created is still removed. A file no
ticket build commit touched keeps today's reading: the widened retry needs a ticket commit.

The fixture is a scratch repo with its own journal and decompose berth, the pattern of
test_the_hollow_measures_the_repaired_build.py. The fixture proof has two teeth: a SCANNER
(no pkg file says BAD), which is green over an absent file, and a VALUE tooth (pkg.x reads 2).
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 900  # three scratch hollows; the sibling fixture proof needs 900 (ticket 8383a32d20c5)

from cairn.devices.tester.hollow import measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "6beb45934ebd": {
        "1": "test_a_file_a_fixme_repair_first_writes_is_reverted_by_its_hunks",
        "2": "test_a_file_the_first_build_created_is_still_removed",
        "3": "test_a_file_no_ticket_commit_touched_keeps_todays_reading",
    },
}

FIXTURE = "f1x76beb0001"
SCAN = "test_no_pkg_file_says_bad"
VALUE = "test_the_built_value_is_two"

_PROOF_SRC = '''\
import importlib, sys
from pathlib import Path
_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT))

PROVES = {"%(fx)s": {"1": "%(scan)s", "2": "%(value)s"}}

def %(scan)s():
    return not any("BAD" in p.read_text() for p in (_ROOT / "pkg").glob("*.py"))

def %(value)s():
    try:
        sys.modules.pop("pkg.x", None)
        sys.modules.pop("pkg", None)
        return importlib.import_module("pkg.x").VALUE == 2
    except Exception:
        return False

if __name__ == "__main__":
    bad = 0
    for t in (%(scan)s, %(value)s):
        ok = t()
        print(("ok" if ok else "FAIL") + " " + t.__name__)
        bad += not ok
    raise SystemExit(1 if bad else 0)
''' % {"fx": FIXTURE, "scan": SCAN, "value": VALUE}

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}

WRITES_TO = ["pkg/x.py", "pkg/y.py", "pkg/z.py"]

# 69075's shape: T builds x.py; another ticket creates y.py (saying BAD) and z.py; T is kicked
# to FIXME and its repair edits y.py to stop saying BAD. z.py no T commit touches.
EVENTS = [
    ("commit", "2020-01-01T00:00:00", "c0", {"pkg/__init__.py": "", "pkg/base.py": "B = 0\n"}, False),
    ("cross", "2020-01-01T12:00:00", "TICKETME", "BUILDME", "forward"),
    ("commit", "2020-01-02T00:00:00", "build", {"pkg/x.py": "VALUE = 2\n"}, True),
    ("cross", "2020-01-02T12:00:00", "BUILDME", "PROVEME", "forward"),
    ("commit", "2020-01-03T00:00:00", "another ticket",
     {"pkg/y.py": "Y = 'BAD'\nKEEP = 1\n", "pkg/z.py": "Z = 1\n"}, False),
    ("cross", "2020-01-04T00:00:00", "PROVEME", "FIXME", "back"),
    ("commit", "2020-01-04T06:00:00", "FIXME 1 repair", {"pkg/y.py": "Y = 'GOOD'\nKEEP = 1\n"}, True),
    ("cross", "2020-01-04T12:00:00", "FIXME", "BUILDME", "forward"),
]


def _git(repo, *args, at=None):
    env = dict(_ENV)
    if at:
        env.update(GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(events: list, writes_to: list[str]) -> tuple[Path, Path, Path, dict]:
    """A scratch repo, commons and berth store played from ``events``, oldest first.

    ("commit", at, label, {path: text}, names_ticket) writes and commits;
    ("cross", at, from, to, direction) journals one crossing. Returns the roots and {label: sha}.
    """
    tmp = scratch_dir("cairn-hollowfixmefile-")
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    for d in (repo / "proofs", commons / "tickets"):
        d.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / "proofs" / "test_fixture.py").write_text(_PROOF_SRC)
    shas, entries = {}, []
    for ev in events:
        if ev[0] == "commit":
            _, at, label, files, names = ev
            for rel, text in files.items():
                p = repo / rel
                p.parent.mkdir(parents=True, exist_ok=True)
                p.write_text(text)
            (repo / "log.txt").write_text(label)
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", f"{FIXTURE}: {label}" if names else f"unrelated: {label}",
                 at=at)
            shas[label] = _git(repo, "rev-parse", "HEAD").stdout.strip()
        else:
            _, at, frm, to, direction = ev
            entries.append({"ticket": FIXTURE, "direction": direction, "actor": "fixture",
                            "at": at, "from": frm, "to": to,
                            "proven_by": "proofs/test_fixture.py"})
    (repo / "history.json").write_text(json.dumps({"entries": entries}))
    berth = berths / "0" / "packets" / f"decompose-20200101T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": writes_to}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    return repo, commons, berths, shas


_CACHE: dict = {}


def _reading() -> dict:
    """One hollow over the fixture, shared by the three teeth (each tooth reads one file)."""
    if "f" not in _CACHE:
        repo, commons, berths, c = _fixture(EVENTS, WRITES_TO)
        _CACHE["f"] = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths,
                              timeout=60)
        _CACHE["c"] = c
    return _CACHE["f"]


def test_a_file_a_fixme_repair_first_writes_is_reverted_by_its_hunks():
    """y.py: another ticket created it after T's first build; T's FIXME repair edited it. The
    counterfactual takes the repair's hunk away (BAD comes back), so the scanner reds. Removing
    the file, as the anchor alone would, leaves the scanner green and reads HOLLOW."""
    f = _reading()
    assert f["revert_mode"].get("pkg/y.py") == "hunks", ("y.py was not reverted by its hunks",
                                                         f["revert_mode"], f["measured"])
    assert SCAN in f["measured"].get("pkg/y.py", []), ("y.py's tooth did not red",
                                                       f["measured"], f["hollow"])
    assert "pkg/y.py" not in f["hollow"], ("y.py read HOLLOW", f["hollow"])


def test_a_file_the_first_build_created_is_still_removed():
    """x.py: T's first build created it, so the counterfactual is its absence, as today: the
    value tooth reds, by a whole-file revert."""
    f = _reading()
    assert f["commit"] == _CACHE["c"]["c0"], ("anchored at", f["commit"], _CACHE["c"])
    assert f["measured"].get("pkg/x.py") == [VALUE], (f["measured"], f["hollow"])
    assert f["revert_mode"].get("pkg/x.py") == "whole-file", f["revert_mode"]


def test_a_file_no_ticket_commit_touched_keeps_todays_reading():
    """z.py: another ticket created it and no T build commit touched it. The widened retry needs
    a T commit that found the file present, so z.py keeps the whole-file reading it has today:
    no hunks taken away, and no tooth reds."""
    f = _reading()
    assert f["revert_mode"].get("pkg/z.py") == "whole-file", ("z.py was retried by hunks",
                                                              f["revert_mode"])
    assert f["measured"].get("pkg/z.py") == [], (f["measured"], f["unchanged"])


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
