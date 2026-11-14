"""Teeth for ticket cd40ac53f08a — the daily tier: ``run-every-proof`` reseals every proof git
tracks and tickets each new red and every orphan.

Outline 9.4.2.3.7.3 (Akien, 2026-11-13): the daily run, in sleep, measures the whole tree, and
*"every test failure, every orphaned file, HAS TO BE FIXED ... reds don't get lost"*. Before this
ticket the tester declared ``run`` for one proof and the hourly ``reseal-yellow``; no verb ran
every proof.

WHY THE TEETH ARE THESE. One per falsifier clause; a hollow build fails at least one:
  (1) over three tracked proofs — one green, one red, one whose every tooth printed NOTRUN — the
      verb seals the green one over its current source, hands the red to red_tickets once, and
      names the not-run one in ``not_run`` with no seal written for it (ticket eb27604ab267's
      shape: a not-run measured nothing, so the door writes nothing);
  (2) the run hands its results over with the orphan scan ON, against the repo it ran, so the
      orphan in the scratch repo comes back ticketed.

THE WORLD. A scratch GIT repo (the daily set is what ``git ls-files`` tracks): component
cairn/alpha with a charter and three proofs, and cairn/stray/loose.py under no charter. Every
tooth asks the tester's own ``run-every-proof`` verb (declared_verbs, RULE 1). Only the edges are
stood in, each at the module the tier reads it from at call time:
  - ``reseal.reseal_all`` is the REAL ladder over a faked tester that sinks exactly as
    ``TesterDevice.run_proof`` does (the pattern of the 810f proof beside this one);
  - ``red_tickets.ticket_what_is_new`` is a spy that finds what is new with red_tickets' OWN key
    finders (``red_keys``, ``orphan_keys``) over the repo it is handed and returns one plan per
    key. Casting commits to the commons and asks the inspector over 5432; that the caster casts
    is 207c4074b3d5's proof, and this one measures that the tier hands it the right run.
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.validation_store.validation_store import (  # noqa: E402
    persist_validation, read_validations, source_fingerprint,
)
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "cd40ac53f08a": {
        "1": "test_every_proof_is_resealed_green_sealed_red_ticketed_notrun_reported",
        "2": "test_the_orphan_scan_runs_and_the_orphan_is_ticketed",
    },
}

GREEN_P = "cairn/alpha/proofs/test_alpha_green.py"
RED_P = "cairn/alpha/proofs/test_alpha_red.py"
NOTRUN_P = "cairn/alpha/proofs/test_alpha_notrun.py"
ORPHAN = "cairn/stray/loose.py"


def _git(root: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-C", str(root), "-c", "user.name=fixture", "-c",
                    "user.email=fixture@localhost", "-c", "core.autocrlf=false", *args],
                   check=True, capture_output=True, env=env)


def _world() -> Path:
    root = scratch_dir("cairn-run-every-proof-")
    (root / "cairn" / "alpha" / "proofs").mkdir(parents=True)
    (root / "cairn" / "stray").mkdir(parents=True)
    (root / "cairn" / "alpha" / "intention+why.json").write_text(
        json.dumps({"component": "alpha"}), encoding="utf-8")
    (root / "cairn" / "alpha" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    for rel in (GREEN_P, RED_P, NOTRUN_P):
        (root / rel).write_text("assert 2 == 2\n", encoding="utf-8")
    (root / ORPHAN).write_text("x = 1\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the fixture")
    return root


def _record(proof: Path, verdict: str) -> dict:
    return {"claim": f"{proof.name} passes", "caller": "the run-every-proof fixture",
            "date": datetime.now().isoformat(timespec="seconds"), "method": "fixture",
            "verdict": verdict, "falsifier": "the proof exits non-zero",
            "horizon": "until the proof changes",
            "evidence": {"source_fingerprint": source_fingerprint(str(proof)),
                         "returncode": 0 if verdict == "green" else 1, "seal": {"verdict": "open"}}}


class _Tester:
    """Sinks as TesterDevice.run_proof does: green and red persist, not-run writes nothing
    (eb27604ab267's run_proof returns a NOTRUN record without sinking)."""

    VERDICT = {Path(GREEN_P).name: "green", Path(RED_P).name: "red", Path(NOTRUN_P).name: "not-run"}

    def __init__(self) -> None:
        self.ran = []

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        proof = Path(proof_path)
        self.ran.append(proof.resolve())
        verdict = self.VERDICT[proof.name]
        record = _record(proof, verdict)
        if sink == "validations" and verdict != "not-run":
            from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
            persist_validation(record, proof_path=str(proof), unsealing_because=NETWORK_SEAL_RETIRED)
        return record


class _Raiser:
    def raise_trouble(self, identity, *, why, detail=None):
        pass

    def clear_trouble(self, identity, *, by, what_changed):
        pass


def _ask(monkeypatch, root: Path):
    """The tester's ``run-every-proof`` verb answered over ``root``; returns (reply, tester, cast)."""
    from cairn.devices.tester import red_tickets, reseal, tiers
    from cairn.devices.tester.device import TesterDevice
    tester, cast = _Tester(), []
    real = reseal.reseal_all
    keys_of_reds, keys_of_orphans = red_tickets.red_keys, red_tickets.orphan_keys

    def ticketer(results, *, scan_orphans=False, repo_root=None, **kw):
        repo = Path(repo_root).resolve()
        items = keys_of_reds(results, repo) + (keys_of_orphans(repo) if scan_orphans else [])
        cast.append({"results": list(results), "scan_orphans": scan_orphans, "repo": repo,
                     "items": items})
        return [root / "plans" / f"{i['kind']}-{Path(i['path']).name}.json" for i in items]

    monkeypatch.setattr(tiers, "REPO_ROOT", root)
    monkeypatch.setattr(reseal, "reseal_all",
                        lambda proofs, **kw: real(proofs, tester=tester, raiser=_Raiser()))
    monkeypatch.setattr(red_tickets, "ticket_what_is_new", ticketer)
    verb = TesterDevice().declared_verbs()["run-every-proof"]
    reply = verb({"id": "testing-cd40", "sender": "testing-cd40", "verb": "run-every-proof",
                  "body": {}})
    return reply, tester, cast


def _named(reply: dict, rel: str):
    return [v for k, v in (reply.get("verdicts") or {}).items() if k.endswith(rel)]


def test_every_proof_is_resealed_green_sealed_red_ticketed_notrun_reported(monkeypatch):
    root = _world()
    reply, tester, cast = _ask(monkeypatch, root)
    assert reply.get("proofs") == sorted([GREEN_P, RED_P, NOTRUN_P]), f"the daily set: {reply}"
    assert sorted(tester.ran) == sorted((root / p).resolve() for p in (GREEN_P, RED_P, NOTRUN_P)), \
        f"the tester ran {tester.ran}, not every tracked proof"
    standing = read_validations(str(root / GREEN_P))
    assert standing and standing[-1]["verdict"] == "green" and \
        standing[-1]["evidence"]["source_fingerprint"] == source_fingerprint(str(root / GREEN_P)), \
        f"the green proof does not stand on a green seal over its current source: {standing}"
    assert _named(reply, GREEN_P) == ["sealed"], f"the green proof is not named sealed: {reply}"
    assert _named(reply, RED_P) == ["red"], f"the red proof is not named red: {reply}"
    assert len(cast) == 1, f"the tier must hand its results to red_tickets once: {cast}"
    reds = [i for i in cast[0]["items"] if i["kind"] == "red"]
    assert len(reds) == 1 and reds[0]["path"].endswith(RED_P), f"the red was not ticketed once: {reds}"
    assert _named(reply, NOTRUN_P) == ["not-run"], \
        f"a proof whose every tooth printed NOTRUN must read not-run, not red: {reply}"
    assert any(p.endswith(NOTRUN_P) for p in reply.get("not_run") or []), \
        f"the reply does not report the not-run proof: {reply}"
    assert not read_validations(str(root / NOTRUN_P)), \
        f"a not-run proof was sealed: {read_validations(str(root / NOTRUN_P))}"


def test_the_orphan_scan_runs_and_the_orphan_is_ticketed(monkeypatch):
    root = _world()
    reply, _, cast = _ask(monkeypatch, root)
    assert len(cast) == 1 and cast[0]["scan_orphans"] is True, \
        f"the daily tier is the whole-tree run: the orphan scan must be on: {cast}"
    assert cast[0]["repo"] == root.resolve(), \
        f"the orphans were scanned in {cast[0]['repo']}, not the repo that ran"
    orphans = [i["path"] for i in cast[0]["items"] if i["kind"] == "orphan"]
    assert ORPHAN in orphans, f"the scratch repo's orphan was not found: {orphans}"
    assert any(t.endswith(f"orphan-{Path(ORPHAN).name}.json") for t in reply.get("ticketed", [])), \
        f"the reply does not carry the orphan's ticket: {reply}"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
