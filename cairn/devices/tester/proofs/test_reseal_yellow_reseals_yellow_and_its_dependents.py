"""Teeth for ticket 810fb2fc4a15 — the hourly tier: ``reseal-yellow`` reseals every yellow
component's proofs and every proof waiting on one, and tickets the new reds.

Outline 9.4.2.3.7.2 (Akien, 2026-11-13): a component that passed its own proofs at commit is in
service, YELLOW, until what depends on it is measured again (ticket ee4e874a2d61). Before this
ticket nothing reran them: the tester declared ``run`` for one proof and no tier at all.

WHY THE TEETH ARE THESE. One per falsifier clause; a hollow build fails at least one:
  (1) with A yellow on B's proof, the verb reseals A's two proofs and B's proof, never C's, and A
      then reads green: each of A's proofs stands on a green seal over its current source;
  (2) with nothing yellow, the verb runs no proof and replies an empty set;
  (3) a dependent proof that reseals red reaches red_tickets.ticket_what_is_new, orphan scan
      off, and the reply names it red.
  A fourth tooth, under no clause, holds the loud edge D2 names: a CodeMother that refuses is a
  refusal in the reply, and nothing is resealed.

THE WORLD. Every tooth asks the tester's own ``reseal-yellow`` verb (declared_verbs, RULE 1)
over a SCRATCH repo of three components. Only the edges are stood in, each at the module the
tier reads it from at call time:
  - ``bus_client.reach`` returns a bus whose CodeMother answers ``inspect`` with the fixture's
    yellow list, wire-encoded as inspect_wire encodes it (the live ask needs CodeMother on a
    bus: a Linux sealer's tooth, not this proof's);
  - ``reseal.reseal_all`` is the REAL ladder over a faked tester that sinks exactly as
    ``TesterDevice.run_proof`` does, so the seals land through the real store door into the
    scratch components' own validations (the pattern of
    test_a_reseal_names_the_tickets_whose_hollow_it_voids.py);
  - ``red_tickets.ticket_what_is_new`` is a spy: casting commits to the commons, and this proof
    measures that the tier HANDS the reds over, not the caster (207c4074b3d5's own proofs).
"""
from __future__ import annotations

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
    "810fb2fc4a15": {
        "1": "test_a_yellow_component_and_its_dependent_are_resealed_and_a_reads_green",
        "2": "test_nothing_yellow_runs_no_proof_and_replies_empty",
        "3": "test_a_dependent_that_reseals_red_is_ticketed_and_named_red",
    },
}

A1, A2 = "cairn/alpha/proofs/test_alpha_one.py", "cairn/alpha/proofs/test_alpha_two.py"
B, C = "cairn/beta/proofs/test_beta.py", "cairn/gamma/proofs/test_gamma.py"


def _world() -> Path:
    root = scratch_dir("cairn-reseal-yellow-")
    for comp in ("alpha", "beta", "gamma"):
        (root / "cairn" / comp / "proofs").mkdir(parents=True)
        (root / "cairn" / comp / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    for rel in (A1, A2, B, C):
        (root / rel).write_text("assert 2 == 2\n", encoding="utf-8")
    return root


def _yellow_on_b() -> list:
    return [{"kind": "component-waits-on-dependents", "component": "alpha", "at": "alpha",
             "waiting_on": [B]}]


class _CodeMother:
    """A bus whose CodeMother answers ``inspect`` with ``yellow``, or refuses."""

    def __init__(self, yellow, *, refuse: str | None = None) -> None:
        self.yellow, self.refuse, self.asked = yellow, refuse, []

    def request(self, **kw):
        from cairn.devices.codemother.tools.inspect_wire.inspect_wire import wire_encode
        self.asked.append(kw)
        if self.refuse:
            return {"sender": "codemother", "body": {"accepted": False, "reason": self.refuse}}
        return {"sender": "codemother",
                "body": {"accepted": True, "data": wire_encode({"yellow": self.yellow,
                                                                "findings": []})}}


def _record(proof: Path, verdict: str) -> dict:
    return {"claim": f"{proof.name} passes", "caller": "the reseal-yellow fixture",
            "date": datetime.now().isoformat(timespec="seconds"), "method": "fixture",
            "verdict": verdict, "falsifier": "the proof exits non-zero",
            "horizon": "until the proof changes",
            "evidence": {"source_fingerprint": source_fingerprint(str(proof)),
                         "returncode": 0 if verdict == "green" else 1, "seal": {"verdict": "open"}}}


class _Tester:
    """Sinks as TesterDevice.run_proof does; a proof named in ``red`` reads red."""

    def __init__(self, red=()) -> None:
        self.red, self.ran = set(red), []

    def run_proof(self, proof_path, *, sink, caller=None, timeout=120, isolation="none",
                  scratch_sweep=None):
        proof = Path(proof_path)
        self.ran.append(proof.resolve())
        record = _record(proof, "red" if proof.name in self.red else "green")
        if sink == "validations":
            from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
            persist_validation(record, proof_path=str(proof), unsealing_because=NETWORK_SEAL_RETIRED)
        return record


class _Raiser:
    def raise_trouble(self, identity, *, why, detail=None):
        pass

    def clear_trouble(self, identity, *, by, what_changed):
        pass


def _ask(monkeypatch, root: Path, codemother: _CodeMother, *, red=()):
    """The tester's ``reseal-yellow`` verb answered over ``root``; returns (reply, tester, cast)."""
    from cairn.devices.tester import red_tickets, reseal, tiers
    from cairn.devices.tester.device import TesterDevice
    import cairn.tools.bus_client.bus_client as bus_client
    tester, cast = _Tester(red), []
    real = reseal.reseal_all

    def ticketer(results, **kw):
        cast.append((list(results), kw))
        return [root / "plans" / f"red-{Path(str(r['proof'])).name}.json"
                for r in results if r.get("outcome") == "red"]

    monkeypatch.setattr(bus_client, "reach", lambda *names, **kw: codemother)
    monkeypatch.setattr(tiers, "REPO_ROOT", root)
    monkeypatch.setattr(reseal, "reseal_all",
                        lambda proofs, **kw: real(proofs, tester=tester, raiser=_Raiser()))
    monkeypatch.setattr(red_tickets, "ticket_what_is_new", ticketer)
    verb = TesterDevice().declared_verbs()["reseal-yellow"]
    reply = verb({"id": "testing-810f", "sender": "testing-810f", "verb": "reseal-yellow", "body": {}})
    return reply, tester, cast


def test_a_yellow_component_and_its_dependent_are_resealed_and_a_reads_green(monkeypatch):
    root = _world()
    cm = _CodeMother(_yellow_on_b())
    reply, tester, _ = _ask(monkeypatch, root, cm)
    assert cm.asked and cm.asked[0]["to"] == "codemother" and cm.asked[0]["verb"] == "inspect", \
        f"the yellow set was not asked of CodeMother's inspect verb: {cm.asked}"
    assert reply.get("proofs") == sorted([A1, A2, B]), f"the resealed set: {reply}"
    assert sorted(tester.ran) == sorted((root / p).resolve() for p in (A1, A2, B)), \
        f"the tester ran {tester.ran}, not A's proofs and B's"
    for rel in (A1, A2):
        standing = read_validations(str(root / rel))
        assert standing and standing[-1]["verdict"] == "green", f"{rel} does not read green: {standing}"
        assert standing[-1]["evidence"]["source_fingerprint"] == source_fingerprint(str(root / rel)), \
            f"{rel}'s seal is not over its current source"
    assert not read_validations(str(root / C)), "gamma is not yellow and was sealed"
    verdicts = reply.get("verdicts", {})
    assert len(verdicts) == 3 and all(any(k.endswith(p) for k in verdicts) for p in (A1, A2, B)) \
        and set(verdicts.values()) == {"sealed"}, \
        f"the reply must name each proof and its verdict, sealed: {reply}"


def test_nothing_yellow_runs_no_proof_and_replies_empty(monkeypatch):
    root = _world()
    reply, tester, cast = _ask(monkeypatch, root, _CodeMother([]))
    assert tester.ran == [] and cast == [], f"nothing yellow ran {tester.ran} and cast {cast}"
    assert reply == {"tier": "hourly", "proofs": [], "verdicts": {}, "refusals": [], "ticketed": []}, reply


def test_a_dependent_that_reseals_red_is_ticketed_and_named_red(monkeypatch):
    root = _world()
    reply, tester, cast = _ask(monkeypatch, root, _CodeMother(_yellow_on_b()),
                               red={Path(B).name})
    assert len(cast) == 1, f"the tier must hand its results to red_tickets once: {cast}"
    results, kw = cast[0]
    assert kw.get("scan_orphans") is False, f"the hourly tier is not a whole-tree run: {kw}"
    reds = [str(r["proof"]).replace("\\", "/") for r in results if r.get("outcome") == "red"]
    assert len(reds) == 1 and reds[0].endswith(B), f"red_tickets was not handed B's red: {reds}"
    named = {k: v for k, v in reply.get("verdicts", {}).items() if k.endswith(B)}
    assert list(named.values()) == ["red"], f"the reply does not name B red: {reply}"
    assert any(t.endswith(f"red-{Path(B).name}.json") for t in reply.get("ticketed", [])), \
        f"the reply does not carry the ticket cast for B: {reply}"


def test_a_refusing_codemother_reseals_nothing_and_says_so(monkeypatch):
    root = _world()
    reply, tester, cast = _ask(monkeypatch, root,
                               _CodeMother(_yellow_on_b(), refuse="testing-810f: no inspector"))
    assert tester.ran == [] and cast == [], "a tier that could not read its set resealed"
    assert "testing-810f: no inspector" in str(reply.get("refused")), reply


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
