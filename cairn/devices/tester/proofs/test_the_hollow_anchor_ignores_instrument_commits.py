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

import ast
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 300  # measured 2026-11-21 (ticket 50987e27621c): 72 s solo through bin/cairn test once its standing tooth read seals instead of re-running three proofs; was 900 (8383a32d20c5)

from cairn.devices.tester.hollow import measure  # noqa: E402
from cairn.tools.scratch.scratch import git_env, scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402
from cairn.tools.validation_store.validation_store import (  # noqa: E402
    sealed_fingerprint_now, standing, validations_path_for)

PROVES = {"79aa8b19a840": {"1": "test_the_anchor_and_hollow_proofs_stay_green"},  # ticket 79aa8b19a840: the red tooth reseals green
          
    "479f75cc0917": {
        "1": "test_a_proofs_only_repair_does_not_bound_the_anchor",
        "2": "test_a_source_rebuild_still_bounds_the_anchor",
        "3": "test_the_anchor_and_hollow_proofs_stay_green",
    },
    # ticket 50987e27621c: the standing tooth reads the seals instead of re-running the proofs
    "50987e27621c": {"1": "test_the_anchor_and_hollow_proofs_stay_green",
                     "2": "test_a_red_or_stale_seal_reds_the_standing_reader",
                     "3": "test_the_standing_tooth_runs_no_proof"},
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


# TICKET 50987e27621c: THE STANDING PROOFS ARE READ FROM THEIR SEALS, NEVER RE-RUN. Measured
# 2026-11-21 on akiendelllinux, solo: re-running them took at least 1415 s, so one proof timed
# out at 900 s and the other sealed red after 1522 s. Each one carries its own seal, and validation_store.standing() reads
# that seal exactly as component_color does: a missing seal, a red seal, and a green seal
# whose source_fingerprint no longer matches the closure it recorded all read NOT proven. So
# the tooth trusts no stale green (Law 8) and re-derives nothing a seal already settled (Law 1).
STANDING = (
    "cairn/devices/tester/proofs/test_hollow_anchors_before_the_build_that_stands.py",
    "cairn/devices/tester/proofs/test_the_hollow_measures_the_repaired_build.py",
    "cairn/devices/tester/proofs/test_hollow.py",
)


def _unproven(paths, root=_REPO_ROOT):
    """``[(path, why)]`` for each named proof whose seal does not stand right now."""
    out = []
    for rel in paths:
        s = standing(str(Path(root) / rel))
        if not s["proven"]:
            out.append((str(rel), s["why"]))
    return out


def _plant(verdict, fingerprint):
    """A scratch component holding one proof and its seal; ``fingerprint`` is a string to
    record, or ``"match"`` for the one the proof's tree really has. Returns the proof path."""
    comp = scratch_dir("cairn-standplant-") / "comp"
    proof = comp / "proofs" / "test_planted.py"
    proof.parent.mkdir(parents=True)
    proof.write_text("def test_planted():\n    assert True\n")
    seal = {"claim": "planted", "caller": "fixture", "date": "2020-01-01T00:00:00",
            "verdict": verdict, "evidence": {"returncode": 0 if verdict == "green" else 1}}
    seal["evidence"]["source_fingerprint"] = (
        sealed_fingerprint_now(str(proof), seal) if fingerprint == "match" else fingerprint)
    seal_path = Path(validations_path_for(str(proof)))
    seal_path.parent.mkdir(parents=True)
    seal_path.write_text(json.dumps([seal]))
    return proof


def test_the_anchor_and_hollow_proofs_stay_green():
    """The named standing proofs each stand proven RIGHT NOW: read from their seals,
    fingerprint included, never re-run (ticket 50987e27621c)."""
    bad = _unproven(STANDING)
    assert not bad, "a standing proof's seal does not stand: %s" % bad


def test_a_red_or_stale_seal_reds_the_standing_reader():
    """Ticket 50987e27621c clause 2: a red seal and a green seal over a moved fingerprint both
    read unproven, and a green seal over the real fingerprint reads proven, so a reader that
    always says red cannot pass this tooth."""
    red, stale, good = _plant("red", "match"), _plant("green", "0" * 64), _plant("green", "match")
    assert [p for p, _ in _unproven([red])] == [str(red)], "a red seal read as standing"
    found = _unproven([stale])
    assert [p for p, _ in found] == [str(stale)], "a green seal over a moved fingerprint read as standing"
    assert "HORIZON HAS CLOSED" in found[0][1], found
    assert _unproven([good]) == [], "a green seal over the real fingerprint read as unproven"


def test_the_standing_tooth_runs_no_proof():
    """Ticket 50987e27621c clause 3: no subprocess call here runs a proof (none hands it
    sys.executable or a proofs/ path), and the standing tooth answers through standing()."""
    tree = ast.parse(Path(__file__).read_text())
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess"):
            continue
        seg = ast.dump(node)
        assert "attr='executable'" not in seg, ("a subprocess call runs python", node.lineno)
        names = [n.value for n in ast.walk(node)
                 if isinstance(n, ast.Constant) and isinstance(n.value, str)]
        assert not any("proofs/" in s or s.endswith(".py") for s in names), (
            "a subprocess call names a proof", node.lineno, names)
    funcs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    calls = lambda f: {c.func.id for c in ast.walk(funcs[f])
                       if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
    assert "_unproven" in calls("test_the_anchor_and_hollow_proofs_stay_green"), calls("test_the_anchor_and_hollow_proofs_stay_green")
    assert "standing" in calls("_unproven"), calls("_unproven")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
