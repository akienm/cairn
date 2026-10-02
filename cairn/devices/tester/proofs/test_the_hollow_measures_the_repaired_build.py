"""Teeth for ticket e08c996f939c — the hollow measures the build that stands after a FIXME repair.

MEASURED 2026-10-02 on efb670ff1dd8's hollow (HEAD d95e8cbe). The build 4313a42d was kicked
PROVEME -> FIXME and repaired by c2d2fedf. The hollow anchored at c2d2fedf^, so the original
build fell outside the window, and the run then misread what was left:
  - the writes_to entry ``cairn/devices/cairn/machines/ground_loop/`` (a directory, present at
    HEAD, holding the repair) was skipped as "not present at HEAD";
  - ``ground_loop/liveness.py`` (moved to cairn/tools/liveness earlier, byte-identical at the
    anchor) read HOLLOW, because the "moved from" suffix was added before the "unchanged" test;
  - four files the build did write read "unwritten", blaming the chart.

THE RULE THESE TEETH HOLD. A back-edge INTO FIXME repairs the standing build and does not bound
the anchor (back-edges to BUILDME or TICKETME are rebuilds and still do — 06f0445e7a63's teeth
stay the arbiter of that). A writes_to directory is measured file by file over the files changed
between the anchor and HEAD. A moved file whose successor is byte-identical at the anchor, and
whose source is absent there, reads unwritten.

Every fixture is a scratch repo with its own journal and decompose berth, the pattern of
test_hollow_anchors_before_the_build_that_stands.py.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.hollow import measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "e08c996f939c": {
        "1": "test_a_fixme_back_edge_does_not_bound_the_anchor",
        "2": "test_a_writes_to_directory_is_measured_per_file",
        "3": "test_an_unchanged_move_reads_unwritten",
        "4": "test_the_anchor_and_hollow_proofs_stay_green",
        "5": "test_a_removed_file_takes_its_empty_directory_with_it",
    },
}

FIXTURE = "f1x7e08c0001"
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
    tmp = scratch_dir("cairn-hollowrepair-")
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


def test_a_fixme_back_edge_does_not_bound_the_anchor():
    """efb's shape: a build, PROVEME -> FIXME, a repair touching another writes_to file. The
    anchor is the BUILD's parent, so the file the build wrote is measured, not called unwritten."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0",
         {"pkg/subject.py": "VALUE = 1\n", "pkg/helper.py": "H = 0\n"}, False),
        ("cross", "2020-01-01T12:00:00", "TICKETME", "BUILDME", "forward"),
        ("commit", "2020-01-02T00:00:00", "build", {"pkg/subject.py": "VALUE = 2\n"}, True),
        ("cross", "2020-01-02T12:00:00", "BUILDME", "PROVEME", "forward"),
        ("cross", "2020-01-03T00:00:00", "PROVEME", "FIXME", "back"),
        ("commit", "2020-01-03T06:00:00", "FIXME 1 repair", {"pkg/helper.py": "H = 1\n"}, True),
        ("cross", "2020-01-03T12:00:00", "FIXME", "BUILDME", "forward"),
    ], ["pkg/subject.py", "pkg/helper.py"])
    f = _measure(repo, commons, berths)
    assert f["commit"] == c["c0"], ("anchored at", f["commit"], c)
    assert f["measured"].get("pkg/subject.py") == [TOOTH], f["measured"]
    assert "pkg/subject.py" not in f["unchanged"], f["unchanged"]


def test_a_writes_to_directory_is_measured_per_file():
    """A writes_to entry naming a directory present at HEAD is expanded to the files the
    ticket's own build commits changed under it, and each is measured — never skipped as 'not
    present', and never a file another ticket's commit changed after the anchor (FIXME 1,
    measured on efb670ff1dd8: four files other hands edited read HOLLOW)."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0",
         {"pkg/subject.py": "VALUE = 1\n", "pkg/other.py": "O = 0\n"}, False),
        ("cross", "2020-01-01T12:00:00", "TICKETME", "BUILDME", "forward"),
        ("commit", "2020-01-02T00:00:00", "build", {"pkg/subject.py": "VALUE = 2\n"}, True),
        ("commit", "2020-01-03T00:00:00", "another ticket", {"pkg/other.py": "O = 1\n"}, False),
    ], ["pkg/"])
    f = _measure(repo, commons, berths)
    assert f["measured"].get("pkg/subject.py") == [TOOTH], (f["measured"], f["skipped"])
    assert not any(s["file"].rstrip("/") == "pkg" for s in f["skipped"]), f["skipped"]
    assert "pkg/other.py" not in f["measured"] and "pkg/other.py" not in f["hollow"], \
        ("another ticket's edit was measured as this build", f["measured"], f["hollow"])


def test_an_unchanged_move_reads_unwritten():
    """A charted file moved BEFORE the build (git's rename record names the successor) and not
    touched by it: successor identical at the anchor, source absent there. It reads unwritten —
    reverting nothing and calling the result hollow blames the proof for a no-op."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0",
         {"pkg/subject.py": "VALUE = 1\n", "old/mod.py": _MOVED}, False),
        ("mv", "2020-01-01T06:00:00", "move", "old/mod.py", "new/mod.py"),
        ("cross", "2020-01-01T12:00:00", "TICKETME", "BUILDME", "forward"),
        ("commit", "2020-01-02T00:00:00", "build", {"pkg/subject.py": "VALUE = 2\n"}, True),
    ], ["pkg/subject.py", "old/mod.py"])
    f = _measure(repo, commons, berths)
    assert "new/mod.py" not in f["hollow"], ("an unchanged move read hollow", f["hollow"])
    assert "new/mod.py" in f["unchanged"], (f["unchanged"], f["measured"], f["skipped"])
    assert f["measured"].get("pkg/subject.py") == [TOOTH], f["measured"]


def test_a_removed_file_takes_its_empty_directory_with_it():
    """FIXME 2, measured on efb670ff1dd8: the build added ground_loop/probes/__init__.py, and a
    folder named probes/ IS a registration. Reverting by removal left the folder, empty, so the
    device stayed registered and the file read HOLLOW. A clean checkout of the anchor has no such
    folder; the reversion must not keep one. Here the subject reads its value off a directory."""
    subject = ("from pathlib import Path\n"
               "VALUE = 2 if (Path(__file__).parent / 'reg').is_dir() else 1\n")
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", {"pkg/subject.py": subject}, False),
        ("cross", "2020-01-01T12:00:00", "TICKETME", "BUILDME", "forward"),
        ("commit", "2020-01-02T00:00:00", "build", {"pkg/reg/marker.py": ""}, True),
    ], ["pkg/reg/marker.py"])
    f = _measure(repo, commons, berths)
    assert f["measured"].get("pkg/reg/marker.py") == [TOOTH], \
        ("the empty directory survived the reversion", f["measured"], f["hollow"])


def test_the_anchor_and_hollow_proofs_stay_green():
    """06f0445e7a63's rebuild rule and the hollow's own proof are untouched by this change."""
    for rel in ("cairn/devices/tester/proofs/test_hollow_anchors_before_the_build_that_stands.py",
                "cairn/devices/tester/proofs/test_hollow.py"):
        r = subprocess.run([sys.executable, str(_REPO_ROOT / rel)], capture_output=True,
                           text=True, timeout=900, cwd=_REPO_ROOT)
        assert r.returncode == 0, (rel, r.stdout[-1500:], r.stderr[-1500:])


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
