"""Teeth for ticket 479f75cc0917 — the hollow's anchor ignores a commit that changes only instruments.

MEASURED 2026-10-03 on 7cb1989e7825's hollow (HEAD c3f72a3f). Its build 209bae65 stood on
ab8d52d3; the ticket was kicked PROVEME -> BUILDME at 00:50 and repaired by c3f72a3f, which
changed only two proofs, their seal records and the bus history/state. That commit names the
ticket and changes writes_to files, so build_anchor counted it as a rebuild: the back-edge
bounded, the anchor became c3f72a3f^ (e2a73b43), every eligible file was byte-identical there,
and the run refused that the anchor postdates the build.

THE RULE THESE TEETH HOLD. A build commit names the ticket and changes a writes_to file the
hollow would MEASURE — never one ``_classify`` skips (under proofs/, a record, outside the
repo). A repair that touches only those is a retreat-and-recross and bounds nothing; a repair
that touches source still bounds (06f0445e7a63's rebuild rule).

Every fixture is a scratch repo with its own journal and decompose berth, the pattern of
test_the_hollow_measures_the_repaired_build.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 900  # measured 2026-10-04: times out at the reseal door's 120s, green at 900s (ticket 8383a32d20c5)

from cairn.devices.tester.hollow import measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "479f75cc0917": {
        "1": "test_a_proofs_only_repair_does_not_bound_the_anchor",
        "2": "test_a_source_rebuild_still_bounds_the_anchor",
        "3": "test_the_anchor_and_hollow_proofs_stay_green",
    },
}

FIXTURE = "f1x7479f0001"
TOOTH = "test_the_built_value_is_two"

_PROOF_SRC = '''\
import importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROVES = {"%s": {"1": "%s"}}

def %s():
    try:
        sys.modules.pop("pkg.subject", None)
        sys.modules.pop("pkg", None)
        return importlib.import_module("pkg.subject").VALUE == 2
    except Exception:
        return False

if __name__ == "__main__":
    ok = %s()
    print(("ok" if ok else "FAIL") + " %s")
    raise SystemExit(0 if ok else 1)
''' % (FIXTURE, TOOTH, TOOTH, TOOTH, TOOTH)

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}

_MOVED = "".join(f"LINE_{i} = {i}\n" for i in range(40))  # big enough for git's rename record


def _git(repo, *args, at=None):
    env = dict(_ENV)
    if at:
        env.update(GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(events: list, writes_to: list[str]) -> tuple[Path, Path, Path, dict]:
    """A scratch repo, commons and berth store played from ``events``, oldest first.

    ("commit", at, label, {path: text | None}, names_ticket) writes (None removes) and commits;
    ("mv", at, label, src, dst) is a git mv committed without the ticket id;
    ("cross", at, from, to, direction) journals one crossing. Returns the roots and {label: sha}.
    """
    tmp = scratch_dir("cairn-hollowinstr-")
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
                if text is None:
                    p.unlink()
                else:
                    p.parent.mkdir(parents=True, exist_ok=True)
                    p.write_text(text)
            (repo / "log.txt").write_text(label)
            _git(repo, "add", "-A")
            _git(repo, "commit", "-qm", f"{FIXTURE}: {label}" if names else f"unrelated: {label}",
                 at=at)
            shas[label] = _git(repo, "rev-parse", "HEAD").stdout.strip()
        elif ev[0] == "mv":
            _, at, label, src, dst = ev
            (repo / dst).parent.mkdir(parents=True, exist_ok=True)
            _git(repo, "mv", src, dst)
            _git(repo, "commit", "-qm", f"unrelated: {label}", at=at)
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


def _measure(repo, commons, berths):
    return measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)


def test_a_proofs_only_repair_does_not_bound_the_anchor():
    """7cb1's shape: a build, PROVEME -> BUILDME, a repair naming the ticket that changes only the
    proof and its seal record. The anchor is the BUILD's parent and the build is measured."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", {"pkg/subject.py": "VALUE = 1\n"}, False),
        ("cross", "2020-01-01T12:00:00", "TICKETME", "BUILDME", "forward"),
        ("commit", "2020-01-02T00:00:00", "build", {"pkg/subject.py": "VALUE = 2\n"}, True),
        ("cross", "2020-01-02T12:00:00", "BUILDME", "PROVEME", "forward"),
        ("cross", "2020-01-03T00:00:00", "PROVEME", "BUILDME", "back"),
        ("commit", "2020-01-03T06:00:00", "proofs-only repair",
         {"proofs/test_fixture.py": _PROOF_SRC + "# repaired\n",
          "validations/test_fixture.json": "{}\n"}, True),
        ("cross", "2020-01-03T12:00:00", "BUILDME", "PROVEME", "forward"),
    ], ["pkg/subject.py", "proofs/test_fixture.py", "validations/test_fixture.json"])
    f = _measure(repo, commons, berths)
    assert f["commit"] == c["c0"], ("anchored at", f["commit"], c)
    assert f["measured"].get("pkg/subject.py") == [TOOTH], (f["measured"], f["unchanged"])


def test_a_source_rebuild_still_bounds_the_anchor():
    """06f0's rule kept: after PROVEME -> BUILDME, a commit naming the ticket that changes SOURCE
    is the build that stands, so the anchor is that rebuild's parent."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", {"pkg/subject.py": "VALUE = 1\n"}, False),
        ("cross", "2020-01-01T12:00:00", "TICKETME", "BUILDME", "forward"),
        ("commit", "2020-01-02T00:00:00", "build", {"pkg/subject.py": "VALUE = 2\nX = 0\n"}, True),
        ("cross", "2020-01-02T12:00:00", "BUILDME", "PROVEME", "forward"),
        ("cross", "2020-01-03T00:00:00", "PROVEME", "BUILDME", "back"),
        ("commit", "2020-01-03T06:00:00", "rebuild",
         {"pkg/subject.py": "VALUE = 2\nX = 1\n",
          "proofs/test_fixture.py": _PROOF_SRC + "# rebuilt\n"}, True),
        ("cross", "2020-01-03T12:00:00", "BUILDME", "PROVEME", "forward"),
    ], ["pkg/subject.py", "proofs/test_fixture.py"])
    f = _measure(repo, commons, berths)
    assert f["commit"] == c["build"], ("anchored at", f["commit"], c)


def test_the_anchor_and_hollow_proofs_stay_green():
    """06f0445e7a63's rebuild rule, e08c996f939c's repair rule and the hollow's own proof hold."""
    for rel in ("cairn/devices/tester/proofs/test_hollow_anchors_before_the_build_that_stands.py",
                "cairn/devices/tester/proofs/test_the_hollow_measures_the_repaired_build.py",
                "cairn/devices/tester/proofs/test_hollow.py"):
        r = subprocess.run([sys.executable, str(_REPO_ROOT / rel)], capture_output=True,
                           text=True, timeout=900, cwd=_REPO_ROOT)
        assert r.returncode == 0, (rel, r.stdout[-1500:], r.stderr[-1500:])


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
