"""Teeth for ticket ce92eb562cf9 — hollow takes away the build, not the years since.

MEASURED 2026-10-13 on 6890cf7e4053: the anchor's domain.py died at its own import line (a
store module moved after the build), so the proof printed no teeth, the reading was UNRAN, and
UNRAN reds the PROVED gate — while removing only the build's hunk by hand redded clause 2. The
whole-file revert answered "this file as it stood at the anchor"; the counterfactual Law 8 asks
for is "this build never happened". So a file whose whole-file revert cannot run is retried
with only the build commits' own hunks taken away from HEAD's bytes, and a hunk that will not
reverse-apply is unmeasurable by name, never UNRAN.

The fixture: c0 lays down ``f.py`` (importing ``lib.store``) and two fixture proofs that import
``f`` at module level — so a world where ``f`` cannot import prints no teeth at all. Build
commit B (it names the ticket) appends ``built()``. Later commit L moves ``lib`` to ``lib2``
and repoints f.py's import, so the anchor's f.py cannot import at HEAD.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.hollow import HollowUnmeasurable, measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROOF_TIMEOUT_S = 900   # tooth 6 takes a live hollow reading of 6890cf7e4053

PROVES = {
    "ce92eb562cf9": {
        "1": "test_a_checked_build_hunk_reads_ok_in_hunk_mode_not_unran",
        "2": "test_an_unchecked_build_hunk_reads_hollow_not_unran",
        "3": "test_a_whole_file_revert_that_runs_keeps_its_reading",
        "4": "test_an_overlapping_later_change_is_unmeasurable_by_name",
        "5": "test_the_seal_carries_revert_mode_per_file",
        "6": "test_the_live_6890_clause_2_proof_reads_ok",
    },
}

FIXTURE = "f1x7ce92eb56"

_PAD = "".join(f"PAD_{i} = {i}\n" for i in range(12))  # keeps L's import edit outside B's hunk

_PROOF = '''\
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import f

PROVES = {"%s": {"%s": "%s"}}

def %s():
    try:
        return %s
    except Exception:
        return False

if __name__ == "__main__":
    ok = %s()
    print(("ok" if ok else "FAIL") + " %s")
    raise SystemExit(0 if ok else 1)
'''


def _proof_src(clause: str, name: str, expr: str) -> str:
    return _PROOF % (FIXTURE, clause, name, name, expr, name, name)


def _git(repo, *args, at=None):
    env = {**git_env(), "GIT_AUTHOR_NAME": "fixture", "GIT_AUTHOR_EMAIL": "f@x",
           "GIT_COMMITTER_NAME": "fixture", "GIT_COMMITTER_EMAIL": "f@x"}
    if at:
        env.update(GIT_AUTHOR_DATE=at, GIT_COMMITTER_DATE=at)
    return subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, env=env)


def _fixture(later: str) -> tuple[Path, Path, Path, str]:
    """later: 'breaks_import' (L repoints the import), 'overlaps' (L also edits B's own line),
    or 'none' (no L). Returns repo, commons, berths, and B's sha."""
    tmp = scratch_dir("cairn-hollowhunks-")
    repo, commons, berths = tmp / "repo", tmp / "commons", tmp / "berths"
    for d in (repo / "proofs", repo / "lib", commons / "tickets"):
        d.mkdir(parents=True)
    _git(repo, "init", "-q", "-b", "main")
    (repo / "lib" / "__init__.py").write_text("")
    (repo / "lib" / "store.py").write_text("def save():\n    return 1\n")
    (repo / "f.py").write_text("from lib.store import save\n\n\ndef base():\n    return 1\n\n" + _PAD)
    (repo / "proofs" / "test_checks.py").write_text(
        _proof_src("1", "test_built_is_two", "f.built() == 2"))
    (repo / "proofs" / "test_blind.py").write_text(
        _proof_src("2", "test_base_is_one", "f.base() == 1"))
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", "before the build", at="2020-01-01T00:00:00")

    with (repo / "f.py").open("a") as fh:
        fh.write("\n\ndef built():\n    return 2\n")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-qm", f"{FIXTURE}: the build", at="2020-01-03T00:00:00")
    b = _git(repo, "rev-parse", "HEAD").stdout.strip()

    if later != "none":
        _git(repo, "mv", "lib", "lib2")
        src = (repo / "f.py").read_text().replace("from lib.store", "from lib2.store")
        if later == "overlaps":
            src = src.replace("    return 2\n", "    return 2  # touched in the years since\n")
        (repo / "f.py").write_text(src)
        _git(repo, "add", "-A")
        _git(repo, "commit", "-qm", "the years since", at="2020-01-05T00:00:00")

    berth = berths / "0" / "packets" / f"decompose-20200103T000000-{FIXTURE}.json"
    berth.parent.mkdir(parents=True)
    berth.write_text(json.dumps({"ticket": FIXTURE, "stage": "decompose",
                                 "sub_problems": [{"what": "the build", "kind": "build",
                                                   "writes_to": ["f.py"]}]}))
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps({"id": FIXTURE}))
    (repo / "history.json").write_text(json.dumps({"entries": [
        {"ticket": FIXTURE, "direction": "forward", "actor": "fixture", "at": "2020-01-02T00:00:00",
         "to": "BUILDME"}]}))
    return repo, commons, berths, b


def _measure(later: str, proof: str):
    repo, commons, berths, b = _fixture(later)
    f = measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60,
                log=lambda m: None, proofs=[str(repo / "proofs" / proof)])
    return f, b


def test_a_checked_build_hunk_reads_ok_in_hunk_mode_not_unran():
    """Clause 1: the anchor's f.py cannot import at HEAD; taking away only B's hunk reds the
    tooth that checks it, and the file reads redded in hunk mode."""
    f, _ = _measure("breaks_import", "test_checks.py")
    assert f.get("unran", {}) == {}, f"whole-file UNRAN was not retried: {f.get('unran')}"
    assert f["measured"].get("f.py") == ["test_built_is_two"], f["measured"]
    assert f.get("revert_mode", {}).get("f.py") == "hunks", f.get("revert_mode")


def test_an_unchecked_build_hunk_reads_hollow_not_unran():
    """Clause 2: a proof that does not check B's hunk reads HOLLOW in hunk mode, not UNRAN."""
    f, _ = _measure("breaks_import", "test_blind.py")
    assert f.get("unran", {}) == {}, f.get("unran")
    assert f["hollow"] == ["f.py"], (f["hollow"], f["measured"])
    assert f.get("revert_mode", {}).get("f.py") == "hunks", f.get("revert_mode")


def test_a_whole_file_revert_that_runs_keeps_its_reading():
    """Clause 3: with no later change the whole-file revert imports and runs; the reading and
    the mode are what they were before this ticket."""
    f, _ = _measure("none", "test_checks.py")
    assert f["measured"].get("f.py") == ["test_built_is_two"], f["measured"]
    assert f.get("unran", {}) == {}, f.get("unran")
    assert f.get("revert_mode", {}).get("f.py") == "whole-file", f.get("revert_mode")


def test_an_overlapping_later_change_is_unmeasurable_by_name():
    """Clause 4: L also edits B's own line, so B's hunk will not reverse-apply: measure raises,
    naming f.py and B — it never returns UNRAN."""
    try:
        f, b = _measure("overlaps", "test_checks.py")
    except HollowUnmeasurable as why:
        repo_b = str(why)
        assert "f.py" in repo_b and "will not reverse-apply" in repo_b, repo_b
        return
    raise AssertionError(f"an overlapping later change returned a reading: unran={f.get('unran')} "
                         f"measured={f['measured']} revert_mode={f.get('revert_mode')}")


def test_the_seal_carries_revert_mode_per_file():
    """Clause 5: `cairn test --hollow <t> --seal` hands record_hollow an anchor carrying the
    finding's revert_mode. measure and the store's door are replaced on the modules for the
    call, so nothing runs and nothing is written."""
    from cairn.devices.tester import cli
    from cairn.devices.tester import hollow
    finding = {"ticket": FIXTURE, "measured": {"f.py": ["t"]}, "unran": {}, "skipped": [],
               "hollow": [], "reasons": [], "commit": "0" * 40, "anchor_rule": "journal",
               "anchor_journal": "0" * 40, "anchor_first_build": "1" * 40,
               "proofs": ["proofs/test_checks.py"], "revert_mode": {"f.py": "hunks"},
               "verdict": "green"}
    seen = []
    saved = (hollow.measure, cli.record_hollow, cli.read_validations)
    try:
        hollow.measure = lambda *a, **k: finding
        cli.record_hollow = lambda *a, anchor=None, **k: (seen.append(anchor) or False)
        cli.read_validations = lambda *a, **k: [{"verdict": "red"}]
        cli._hollow_run(argparse.Namespace(hollow=FIXTURE, seal=True, proof=[], timeout=1,
                                           quiet=True))
    finally:
        hollow.measure, cli.record_hollow, cli.read_validations = saved
    assert seen and seen[0].get("revert_mode") == {"f.py": "hunks"}, seen


def test_the_live_6890_clause_2_proof_reads_ok():
    """Clause 6, live: 6890cf7e4053's domain.py, whose anchor dies at its own import line, is
    read in hunk mode and its clause-2 tooth reds — ok, not UNRAN."""
    proof = _REPO_ROOT / "cairn/devices/inference_domain/proofs/test_inference_domain.py"
    tooth = "test_an_out_of_vocabulary_verdict_is_refused_at_the_database"
    f = measure("6890cf7e4053", repo_root=_REPO_ROOT, timeout=300, log=lambda m: None,
                proofs=[str(proof)])
    key = "cairn/devices/inference_domain/domain.py"
    assert key not in f.get("unran", {}), (f.get("unran"), f.get("revert_mode"))
    assert tooth in f["measured"].get(key, []), (f["measured"], f.get("revert_mode"))


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
