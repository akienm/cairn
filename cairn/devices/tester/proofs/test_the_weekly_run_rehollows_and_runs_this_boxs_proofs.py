"""Teeth for ticket 346c75c2f8b7 — the weekly tier: ``weekly-run`` re-runs every sealed hollow,
then runs every proof this box tracks, and tickets what is new.

Outline 9.4.2.3.7.4 (Akien, 2026-11-13): weekly, every hollow is re-measured — a proof the build
once loaded can stop refusing a hollow build as the code around it moves — and each box runs its
own whole set. Before this ticket no verb did either on a clock.

WHY THE TEETH ARE THESE. One per falsifier clause; a hollow build fails at least one:
  (1) a proof whose hollow build now passes it (``hollow.measure`` reads red) is reported red
      and handed to red_tickets, which keys it by its proof, so it is ticketed once;
  (2) a proof whose hollow still fails it (``measure`` reads green) is reported green and casts
      nothing;
  (3) part 2 hands every proof the scratch box tracks to ``reseal.reseal_all`` and names each
      in the reply, and every seal written is written inside it — the hollow re-runs seal
      nothing, and they run BEFORE the reseal, which would otherwise drop the very reading they
      re-measure. (The ladder's rung 1 runs only a proof whose seal no longer holds: that is the
      one door's rule, so the proof with no seal is the one that runs and seals.)

THE WORLD. A scratch GIT repo: component cairn/alpha with three proofs, two of them standing on
a seal whose evidence carries a hollow reading (tickets HOLLOW_STILL and HOLLOW_PASSES), one with
none. Every tooth asks the tester's own ``weekly-run`` verb (declared_verbs, RULE 1). The edges
stood in, each at the module the tier reads it from at call time:
  - ``hollow.measure`` answers per ticket with the verdict the fixture fixes; the real measure
    reverts a ticket's build in a worktree, which is hollow.py's own proof (test_hollow.py);
  - ``reseal.reseal_all`` is the REAL ladder over a faked tester that sinks as
    ``TesterDevice.run_proof`` does; the seal trails are read at its edges, so a seal written
    anywhere but inside it shows as a trail that moved outside them;
  - ``red_tickets.ticket_what_is_new`` is a spy that finds what is new with red_tickets' OWN key
    finders over the repo it is handed (207c4074b3d5's proof measures the caster).
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
    "346c75c2f8b7": {
        "1": "test_a_proof_whose_hollow_now_passes_is_red_and_ticketed_once",
        "2": "test_a_proof_whose_hollow_still_fails_is_green_and_casts_nothing",
        "3": "test_part_two_runs_every_proof_and_seals_only_through_reseal_all",
    },
}

STILL = "cairn/alpha/proofs/test_alpha_still.py"
PASSES = "cairn/alpha/proofs/test_alpha_passes.py"
PLAIN = "cairn/alpha/proofs/test_alpha_plain.py"
HOLLOW_STILL, HOLLOW_PASSES = "a5511f000001", "a5511f000002"


def _git(root: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-C", str(root), "-c", "user.name=fixture", "-c",
                    "user.email=fixture@localhost", "-c", "core.autocrlf=false", *args],
                   check=True, capture_output=True, env=env)


def _record(proof: Path, verdict: str, hollow: dict | None = None) -> dict:
    evidence = {"source_fingerprint": source_fingerprint(str(proof)),
                "returncode": 0 if verdict == "green" else 1, "seal": {"verdict": "open"}}
    if hollow:
        evidence["hollow"] = hollow
    return {"claim": f"{proof.name} passes", "caller": "the weekly-run fixture",
            "date": datetime.now().isoformat(timespec="seconds"), "method": "fixture",
            "verdict": verdict, "falsifier": "the proof exits non-zero",
            "horizon": "until the proof changes", "evidence": evidence}


def _world() -> Path:
    from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
    root = scratch_dir("cairn-weekly-run-")
    (root / "cairn" / "alpha" / "proofs").mkdir(parents=True)
    (root / "cairn" / "alpha" / "intention+why.json").write_text(
        json.dumps({"component": "alpha"}), encoding="utf-8")
    (root / "cairn" / "alpha" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    for rel in (STILL, PASSES, PLAIN):
        (root / rel).write_text("assert 2 == 2\n", encoding="utf-8")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "the fixture")
    for rel, tid in ((STILL, HOLLOW_STILL), (PASSES, HOLLOW_PASSES)):
        persist_validation(_record(root / rel, "green", {tid: {"verdict": "green"}}),
                           proof_path=str(root / rel), unsealing_because=NETWORK_SEAL_RETIRED)
    return root


class _Tester:
    """Sinks as TesterDevice.run_proof does. Each sink notes whether the ladder was running
    when it landed."""

    def __init__(self) -> None:
        self.ran = []

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        proof = Path(proof_path)
        self.ran.append(proof.resolve())
        record = _record(proof, "green")
        if sink == "validations":
            from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
            persist_validation(record, proof_path=str(proof), unsealing_because=NETWORK_SEAL_RETIRED)
        return record


class _Raiser:
    def raise_trouble(self, identity, *, why, detail=None):
        pass

    def clear_trouble(self, identity, *, by, what_changed):
        pass


def _trails(root: Path) -> dict:
    """Every scratch proof's seal trail as it stands now."""
    return {p: read_validations(str(root / p)) for p in (STILL, PASSES, PLAIN)}


def _ask(monkeypatch, root: Path):
    """The tester's ``weekly-run`` verb answered over ``root``; returns (reply, world)."""
    from cairn.devices.tester import hollow, red_tickets, reseal, tiers
    from cairn.devices.tester.device import TesterDevice
    tester, cast, order, measured, handed, edges = _Tester(), [], [], [], [], {}
    real = reseal.reseal_all
    keys_of_reds, keys_of_orphans = red_tickets.red_keys, red_tickets.orphan_keys

    def measurer(tid, *, repo_root=None, proofs=None, **kw):
        order.append("hollow")
        measured.append((tid, list(proofs or [])))
        trail = {p: len(read_validations(str(Path(repo_root) / p))) for p in (STILL, PASSES, PLAIN)}
        measured[-1] += (trail,)
        if tid == HOLLOW_PASSES:
            return {"ticket": tid, "verdict": "red",
                    "reasons": ["hollow: cairn/alpha/code.py redded no declared tooth"]}
        return {"ticket": tid, "verdict": "green", "reasons": []}

    def resealer(proofs, **kw):
        order.append("reseal")
        handed.extend(Path(p).resolve() for p in proofs)
        edges["before"] = _trails(root)
        try:
            return real(proofs, tester=tester, raiser=_Raiser())
        finally:
            edges["after"] = _trails(root)

    def ticketer(results, *, scan_orphans=False, repo_root=None, **kw):
        repo = Path(repo_root).resolve()
        items = keys_of_reds(results, repo) + (keys_of_orphans(repo) if scan_orphans else [])
        cast.append({"results": list(results), "scan_orphans": scan_orphans, "items": items})
        return [root / "plans" / f"{i['kind']}-{Path(i['path']).name}.json" for i in items]

    monkeypatch.setattr(tiers, "REPO_ROOT", root)
    monkeypatch.setattr(hollow, "measure", measurer)
    monkeypatch.setattr(reseal, "reseal_all", resealer)
    monkeypatch.setattr(red_tickets, "ticket_what_is_new", ticketer)
    start = _trails(root)
    verb = TesterDevice().declared_verbs()["weekly-run"]
    reply = verb({"id": "testing-346c", "sender": "testing-346c", "verb": "weekly-run", "body": {}})
    return reply, {"tester": tester, "cast": cast, "order": order, "measured": measured,
                   "handed": handed, "edges": edges, "start": start, "final": _trails(root)}


def _reds(w, rel: str) -> list:
    return [i for c in w["cast"] for i in c["items"] if i["kind"] == "red" and i["path"].endswith(rel)]


def test_a_proof_whose_hollow_now_passes_is_red_and_ticketed_once(monkeypatch):
    root = _world()
    reply, w = _ask(monkeypatch, root)
    assert (HOLLOW_PASSES, [PASSES]) in [(t, p) for t, p, _ in w["measured"]], \
        f"the sealed hollow of {PASSES} was not re-run over it: {w['measured']}"
    assert reply.get("hollow", {}).get(f"{PASSES}::{HOLLOW_PASSES}") == "red", \
        f"a hollow build that passes its proof must read red: {reply}"
    assert len(w["cast"]) == 1 and w["cast"][0]["scan_orphans"] is True, \
        f"the weekly run hands red_tickets one whole-tree call: {w['cast']}"
    assert any(r.get("hollow") == HOLLOW_PASSES and r.get("outcome") == "red"
               for r in w["cast"][0]["results"]), \
        f"the hollow red was not handed to red_tickets: {w['cast'][0]['results']}"
    reds = _reds(w, PASSES)
    assert len(reds) == 1, f"{PASSES} must be ticketed once: {reds}"
    assert any(t.endswith(f"red-{Path(PASSES).name}.json") for t in reply.get("ticketed", [])), \
        f"the reply does not carry the ticket cast for {PASSES}: {reply}"


def test_a_proof_whose_hollow_still_fails_is_green_and_casts_nothing(monkeypatch):
    root = _world()
    reply, w = _ask(monkeypatch, root)
    assert (HOLLOW_STILL, [STILL]) in [(t, p) for t, p, _ in w["measured"]], \
        f"the sealed hollow of {STILL} was not re-run over it: {w['measured']}"
    assert reply.get("hollow", {}).get(f"{STILL}::{HOLLOW_STILL}") == "green", \
        f"a hollow build its proof still refuses must read green: {reply}"
    assert _reds(w, STILL) == [], f"a green hollow cast a ticket: {_reds(w, STILL)}"
    assert not any(t.endswith(f"red-{Path(STILL).name}.json") for t in reply.get("ticketed", [])), reply


def test_part_two_runs_every_proof_and_seals_only_through_reseal_all(monkeypatch):
    root = _world()
    reply, w = _ask(monkeypatch, root)
    assert reply.get("proofs") == sorted([STILL, PASSES, PLAIN]), f"the box's set: {reply}"
    assert sorted(w["handed"]) == sorted((root / p).resolve() for p in (STILL, PASSES, PLAIN)), \
        f"part 2 handed reseal_all {w['handed']}, not every proof the box tracks"
    assert all(any(k.endswith(p) for k in reply.get("verdicts", {})) for p in (STILL, PASSES, PLAIN)), \
        f"the reply does not name every proof's reseal outcome: {reply}"
    assert w["tester"].ran == [(root / PLAIN).resolve()], \
        f"the ladder ran {w['tester'].ran}: only the unsealed proof's seal does not hold"
    assert w["order"] and w["order"][-1] == "reseal" and set(w["order"][:-1]) == {"hollow"}, \
        f"the hollow re-runs must precede the one reseal: {w['order']}"
    assert w["edges"].get("before") == w["start"] and w["final"] == w["edges"].get("after"), \
        "a seal trail moved outside reseal_all: the hollow re-runs or the ticketing wrote one"
    assert [p for p in (STILL, PASSES, PLAIN) if w["edges"]["after"][p] != w["start"][p]] == [PLAIN], \
        f"reseal_all must write exactly the unsealed proof's seal: {w['edges']}"
    for _, _, trail in w["measured"]:
        assert trail == {STILL: 1, PASSES: 1, PLAIN: 0}, \
            f"the hollow re-runs saw seals other than the fixture's: {trail}"
    for rel in (STILL, PASSES, PLAIN):
        assert len(read_validations(str(root / rel))) == 1, \
            f"{rel}'s trail is not exactly one seal (the fixture's, or PLAIN's one reseal)"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
