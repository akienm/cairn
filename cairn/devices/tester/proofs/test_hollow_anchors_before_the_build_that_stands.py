"""Teeth for ticket 06f0445e7a63 — the hollow reverts to the world before the build that stands.

MEASURED 2026-09-30: `cairn test --hollow 68f563403c8f` printed "unwritten ... a finding against
the chart's writes_to" for 4 of 4 files. The anchor was the commit before the LATEST forward
BUILDME crossing in the journals, and 68f5's only journaled crossing was a bookkeeping re-cross
made AFTER its build commit edb4e137 — so the anchor already held the build, every file was
byte-identical there, and the run blamed the chart for what was the anchor's fault (Law 7: the
wrong cause on a record of truth).

THE RULE THESE TEETH HOLD. Build commits are the commits that name the ticket id in their
message AND change a writes_to file. The build that stands begins at the first build commit
after the latest back-edge (out of BUILDME or PROVEME) that has a build commit after it; a
back-edge with none after it is a retreat-and-recross and bounds nothing. The anchor is the
EARLIER of that commit's parent and the journal's pre-build commit, and the reading says which
rule chose it ('journal' | 'first-build-commit') and both candidates. Where the chosen anchor
already holds every eligible file, the hollow says the anchor postdates the build instead of
calling each file unwritten.

Every fixture is a scratch repo with its own journal (history.json) and decompose berth. The
names this build adds (``build_anchor``, the ``anchor`` keyword) are looked up inside each tooth,
so a reverted hollow.py reds a tooth instead of breaking this file's import.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester import hollow  # noqa: E402
from cairn.devices.tester.hollow import HollowUnmeasurable, measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "06f0445e7a63": {
        "1": "test_a_build_committed_before_its_journaled_crossing_is_reverted_to_its_parent",
        "2": "test_a_kickback_and_rebuild_reverts_to_before_the_rebuild_not_the_first_build",
        "2b": "test_a_recross_with_no_build_between_keeps_the_build_it_followed",
        "3": "test_an_anchor_holding_every_file_raises_naming_the_anchor",
        "4": "test_the_reading_and_its_seal_carry_the_anchor_rule_and_both_candidates",
        "5": "test_the_live_anchors_of_68f5_and_c691_are_their_build_parents",
    },
    "c8e421aac06e": {
        "1": "test_off_the_charting_box_the_fixture_anchors_both_tickets",
        "2": "test_a_berth_that_moved_from_the_fixture_reds",
    },
}

FIXTURE = "f1x7a4c40001"

_PROOF_SRC = '''\
import importlib, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

PROVES = {"%s": {"1": "test_the_built_value_is_two"}}

def test_the_built_value_is_two():
    try:
        sys.modules.pop("subject", None)
        return importlib.import_module("subject").VALUE == 2
    except Exception:
        return False

def test_off_the_charting_box_the_fixture_anchors_both_tickets():
    """c8e421aac06e clause 1: with a berth store that holds neither ticket (the shape of every
    box but the one that charted them), the anchors still land on edb4e137^ and 448601ca^."""
    empty = scratch_dir("testing-c8e421aac06e-empty-")
    _live_anchors(berths_root=empty)


def test_a_berth_that_moved_from_the_fixture_reds():
    """c8e421aac06e clause 2: where a decompose berth claims 68f563403c8f with a writes_to that
    differs from the fixture, the live-equality check reds, naming the ticket."""
    berths = scratch_dir("testing-c8e421aac06e-moved-")
    berth = berths / "0" / "packets" / "decompose-20260906T111005-c8e421aac06e.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": "68f563403c8f", "stage": "decompose",
                                 "sub_problems": [{"what": "moved", "kind": "build",
                                                   "writes_to": ["skills/sail/reflection.py"]}]}))
    try:
        _live_anchors(berths_root=berths)
    except AssertionError as e:
        assert "68f563403c8f" in str(e) and "moved from the fixture" in str(e), str(e)
    else:
        raise AssertionError("a berth whose writes_to differs from the fixture read green")


if __name__ == "__main__":
    ok = test_the_built_value_is_two()
    print(("ok" if ok else "FAIL") + " test_the_built_value_is_two")
    raise SystemExit(0 if ok else 1)
''' % FIXTURE

_ENV = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
        "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}


def _git(repo, *args, at=None):
    env = dict(_ENV)
    if at:
        env.update(GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(events: list) -> tuple[Path, Path, Path, dict]:
    """A scratch repo, commons and berth store played from ``events``, oldest first.

    ("commit", at, label, value, names_ticket) writes subject.py with VALUE = value and commits
    it; ("cross", at, from, to, direction) journals one crossing. Returns the three roots and
    {label: sha}. The first commit ("c0") also lays down the fixture proof.
    """
    tmp = scratch_dir("cairn-hollowanchor-")
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    for d in (repo / "proofs", commons / "tickets"):
        d.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / "proofs" / "test_fixture.py").write_text(_PROOF_SRC)
    shas, entries = {}, []
    for ev in events:
        if ev[0] == "commit":
            _, at, label, value, names = ev
            (repo / "subject.py").write_text(f"VALUE = {value}\n")
            (repo / "log.txt").write_text(label)  # so a commit that keeps VALUE still commits
            _git(repo, "add", "-A")
            msg = f"{FIXTURE}: {label}" if names else f"unrelated: {label}"
            _git(repo, "commit", "-qm", msg, at=at)
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
                                                   "writes_to": ["subject.py"]}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    return repo, commons, berths, shas


def _measure(repo, commons, berths):
    return measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)


def test_a_build_committed_before_its_journaled_crossing_is_reverted_to_its_parent():
    """68f5's shape: the build commit, THEN the only journaled BUILDME crossing. Before the fix
    the anchor is the build itself and the file reads unwritten; after it, the build's parent."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", 1, False),
        ("commit", "2020-01-02T00:00:00", "build", 2, True),
        ("cross", "2020-01-03T00:00:00", "TICKETME", "BUILDME", "forward"),
    ])
    f = _measure(repo, commons, berths)
    assert f["commit"] == c["c0"], (f["commit"], c)
    assert f["measured"].get("subject.py") == ["test_the_built_value_is_two"], f["measured"]
    assert f["unchanged"] == [], f["unchanged"]
    assert f.get("anchor_rule") == "first-build-commit", f.get("anchor_rule")


def test_a_kickback_and_rebuild_reverts_to_before_the_rebuild_not_the_first_build():
    """A build, a kick-back INTO BUILDME (no forward re-cross), then a rebuild. The build that
    stands is the rebuild, so the anchor is its parent — never the world before the first build,
    which is where the latest forward crossing alone would put it."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", 1, False),
        ("cross", "2020-01-01T12:00:00", "TICKETME", "BUILDME", "forward"),
        ("commit", "2020-01-02T00:00:00", "first build", 3, True),
        ("cross", "2020-01-02T12:00:00", "BUILDME", "PROVEME", "forward"),
        ("cross", "2020-01-03T00:00:00", "PROVEME", "BUILDME", "back"),
        ("commit", "2020-01-04T00:00:00", "rebuild", 2, True),
    ])
    f = _measure(repo, commons, berths)
    assert f["commit"] == c["first build"], (f["commit"], c)
    assert f["commit"] != c["c0"], "reverted to before the FIRST build, not the rebuild"


def test_a_recross_with_no_build_between_keeps_the_build_it_followed():
    """A build, then a back-edge and a forward re-cross with no build commit between (a
    retreat-and-recross that names a proof). The back-edge bounds nothing, so the anchor is the
    build's parent, not the commit after the build that the re-cross would pick."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", 1, False),
        ("cross", "2020-01-01T12:00:00", "TICKETME", "BUILDME", "forward"),
        ("commit", "2020-01-02T00:00:00", "build", 2, True),
        ("cross", "2020-01-02T12:00:00", "BUILDME", "PROVEME", "forward"),
        ("cross", "2020-01-03T00:00:00", "PROVEME", "TICKETME", "back"),
        ("commit", "2020-01-03T06:00:00", "unrelated", 2, False),
        ("cross", "2020-01-03T12:00:00", "TICKETME", "BUILDME", "forward"),
    ])
    f = _measure(repo, commons, berths)
    assert f["commit"] == c["c0"], (f["commit"], c)
    assert f["measured"].get("subject.py") == ["test_the_built_value_is_two"], f["measured"]


def test_an_anchor_holding_every_file_raises_naming_the_anchor():
    """No commit names the ticket, so only the journal can anchor — and its crossing came after
    the build. Every eligible file is identical at that anchor: the run must refuse, naming the
    anchor as postdating the build, not return a reading that calls each file unwritten."""
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", 1, False),
        ("commit", "2020-01-02T00:00:00", "build without the id", 2, False),
        ("cross", "2020-01-03T00:00:00", "TICKETME", "BUILDME", "forward"),
    ])
    try:
        f = _measure(repo, commons, berths)
    except HollowUnmeasurable as why:
        text = str(why)
        assert c["build without the id"][:12] in text, text
        assert "postdates" in text, text
        return
    raise AssertionError(f"returned a reading instead of refusing: {f['reasons']}")


class _Quiet:
    """A trouble device that records and does nothing — the seal door must not reach the live
    trouble store from inside a proof."""
    def __getattr__(self, name):
        return lambda *a, **k: None


def test_the_reading_and_its_seal_carry_the_anchor_rule_and_both_candidates():
    """The finding names the rule and both candidates; and the seal the CLI writes through
    ``record_hollow(..., anchor=...)`` lands them as evidence.hollow_anchor[ticket] beside an
    evidence.hollow[ticket] that is still a pure {file: [teeth]} map the PROVED gate reads."""
    from cairn.tools.validation_store import validation_store as vs
    repo, commons, berths, c = _fixture([
        ("commit", "2020-01-01T00:00:00", "c0", 1, False),
        ("commit", "2020-01-02T00:00:00", "build", 2, True),
        ("cross", "2020-01-03T00:00:00", "TICKETME", "BUILDME", "forward"),
    ])
    f = _measure(repo, commons, berths)
    assert f.get("anchor_rule") in ("journal", "first-build-commit"), f.get("anchor_rule")
    assert f.get("anchor_journal") == c["build"], (f.get("anchor_journal"), c)
    assert f.get("anchor_first_build") == c["build"], (f.get("anchor_first_build"), c)

    proof = repo / "proofs" / "test_fixture.py"
    standing = json.loads((_REPO_ROOT / "cairn/devices/tester/validations/"
                           "test_hollow_follows_a_move.json").read_text())[-1]
    vpath = Path(vs.validations_path_for(str(proof)))
    vpath.parent.mkdir(parents=True, exist_ok=True)
    vpath.write_text(json.dumps([standing]))
    anchor = {k: f[k] for k in ("anchor_rule", "anchor_journal", "anchor_first_build", "commit")}
    try:
        landed = vs.record_hollow(str(proof), FIXTURE, f["measured"], anchor=anchor,
                                  trouble_device=_Quiet())
    except TypeError as why:
        raise AssertionError(f"record_hollow takes no anchor: {why}")
    assert landed, "no standing validation to land on"
    ev = vs.read_validations(str(proof))[-1]["evidence"]
    assert ev["hollow"][FIXTURE] == f["measured"], ev["hollow"]
    assert ev.get("hollow_anchor", {}).get(FIXTURE) == anchor, ev.get("hollow_anchor")

    # AND THE CLI IS THE WRITER THAT HANDS IT OVER. Measured at this ticket's own hollow
    # (2026-10-02): reverting cli.py redded nothing, because the store accepting an anchor
    # says nothing about the one caller passing it. So the CLI's seal path runs over this
    # finding with the door captured — nothing reaches a live validation.
    import argparse
    from cairn.devices.tester import cli
    seen: list[dict] = []
    finding = dict(f, ticket=FIXTURE, proofs=["proofs/test_fixture.py"], hollow=[],
                   skipped={}, unran={}, reasons=[], verdict="green")
    real_measure, real_record = hollow.measure, cli.record_hollow
    hollow.measure = lambda *a, **k: finding
    cli.record_hollow = lambda path, tid, reading, **k: seen.append(k) or False
    try:
        cli._hollow_run(argparse.Namespace(hollow=FIXTURE, timeout=60, quiet=True, seal=True))
    finally:
        hollow.measure, cli.record_hollow = real_measure, real_record
    assert seen and seen[0].get("anchor") == anchor, seen


# hollow.writes_to for each ticket, read on akiendelllinux 2026-11-13 (the boxes without the
# berths cannot read it; see the tooth below).
_BERTH_WRITES_TO = {
    "68f563403c8f": {"berth": "decompose-20260906T111005-e6c3a299ab9a",
                     "writes_to": ["skills/sail/reflection.py", "skills/sail/SKILL.md",
                                   "cairn/devices/codemother/shim.py",
                                   "cairn/devices/codemother/ingest.py",
                                   "cairn/devices/codemother/proofs/test_feedback_verb.py"]},
    "c691e19d5464": {"berth": "decompose-20260911T120642-bdf2ac680def",
                     "writes_to": ["cairn/devices/cairn/machines/ground_loop/intention+why.json",
                                   "cairn/devices/cc/intention+why.json",
                                   "cairn/tools/operator_inbox/intention+why.json",
                                   "cairn/machines/skill_block/intention+why.json",
                                   "skills/ruled/intention+why.json",
                                   "skills/intent/proofs/test_intent_skill.py"]},
}


def test_the_live_anchors_of_68f5_and_c691_are_their_build_parents():
    """Over the live repo and journals: the two tickets the rule was measured on anchor at the
    parents of their build commits (edb4e137 and 448601ca). These are historical commits, so the
    shas cannot drift.

    The RULE that finds the parent can, for c691. Its BUILDME crossing was journaled in the
    cairnmap tool's history.json, and that file left with the tool (d547b4859f9a, 3882dac1,
    2026-11-08). With no crossing to read, the anchor comes from `_anchor_without_a_crossing`
    ('first-build-commit-no-crossing'), which takes the same parent. Clause (5) is the
    commit, "reverts c691 to anything but 448601ca^", so each ticket asserts that commit by a
    first-build rule: 68f5, whose journal stands, by 'first-build-commit' itself; c691 by
    either first-build rule. A 'journal' anchor still reds both. Measured 2026-11-11.

    THE FILE LIST IS A MEASURED FIXTURE, NOT A LIVE READ (ticket c8e421aac06e). The
    decompose berths live in instance-space on the box that charted them, so on akienasus both
    chains read all-None and ``hollow.writes_to`` raised "names no decompose berth" while the
    Dell sealed green. The lists below are ``hollow.writes_to`` read on akiendelllinux on
    2026-11-13 from the berths named. On a box that holds a berth, the live read must still
    equal the fixture, so the fixture cannot drift from the berth unnoticed."""
    _live_anchors()


def _live_anchors(berths_root=None) -> None:
    """The anchor assertions over the live repo, reading each list from the fixture; where
    ``hollow.writes_to`` answers under ``berths_root``, it must equal the fixture."""
    build_anchor = getattr(hollow, "build_anchor", None)
    assert build_anchor is not None, "hollow.build_anchor does not exist"
    roots = hollow._roots()
    rules = {"68f563403c8f": {"first-build-commit"},
             "c691e19d5464": {"first-build-commit", "first-build-commit-no-crossing"}}
    for tid, build in (("68f563403c8f", "edb4e137"), ("c691e19d5464", "448601ca")):
        ticket = json.loads(hollow._ticket_path(tid).read_text(encoding="utf-8"))
        measured = _BERTH_WRITES_TO[tid]["writes_to"]
        try:
            live = hollow.writes_to(ticket, berths_root=berths_root)
        except hollow.HollowUnmeasurable:
            live = None                      # this box never charted it: the fixture stands in
        assert live is None or live == measured, (
            f"{tid}: the berth's writes_to moved from the fixture: {live} != {measured}")
        files = [hollow._inside(p, _REPO_ROOT) for p in measured]
        a = build_anchor(ticket, files, roots=roots, repo_root=_REPO_ROOT)
        parent = _git(_REPO_ROOT, "rev-parse", f"{build}^").stdout.strip()
        assert a["commit"] == parent, (tid, a)
        assert a["anchor_rule"] in rules[tid], (tid, a)


def test_off_the_charting_box_the_fixture_anchors_both_tickets():
    """c8e421aac06e clause 1: with a berth store that holds neither ticket (the shape of every
    box but the one that charted them), the anchors still land on edb4e137^ and 448601ca^."""
    empty = scratch_dir("testing-c8e421aac06e-empty-")
    _live_anchors(berths_root=empty)


def test_a_berth_that_moved_from_the_fixture_reds():
    """c8e421aac06e clause 2: where a decompose berth claims 68f563403c8f with a writes_to that
    differs from the fixture, the live-equality check reds, naming the ticket."""
    berths = scratch_dir("testing-c8e421aac06e-moved-")
    berth = berths / "0" / "packets" / "decompose-20260906T111005-c8e421aac06e.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": "68f563403c8f", "stage": "decompose",
                                 "sub_problems": [{"what": "moved", "kind": "build",
                                                   "writes_to": ["skills/sail/reflection.py"]}]}))
    try:
        _live_anchors(berths_root=berths)
    except AssertionError as e:
        assert "68f563403c8f" in str(e) and "moved from the fixture" in str(e), str(e)
    else:
        raise AssertionError("a berth whose writes_to differs from the fixture read green")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
