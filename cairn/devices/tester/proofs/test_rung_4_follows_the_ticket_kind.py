"""Teeth for ticket e8be83a46ea9 — the tester's rung 4 follows the ticket's kind and no longer asks who answered.

Outline 19.14.8.2-3 (Akien, 2026-10-31: "for new/changed code tickets the rule is x, for fixit
tickets the rule is y"; "rung 4 no longer asks who answered"). Until this build rung 4 lifted
only for a question Akien answered or a confirmed legacy ruling, so a fixit could never change
the test case it fixes under its own ticket (1d23d635f7ca waits behind test_hollow.py), and a
question settled by measurement was refused for who wrote the answer.

WHY THE TEETH ARE THESE. Each is one clause of 19.14.8.2-3, read off the ticket and the proof's
bytes, so it stays deterministic; a hollow build fails at least one:
  (1) y: a bug whose ``fixes`` lists the moved proof, named in the proof, every removed tooth
      named, lifts rung 4;
  (2) y refuses when the why does not hold: ``fixes`` omits the proof, the proof does not name
      the ticket, or a removed tooth goes unnamed;
  (3) the removed teeth cannot be measured when git holds no blob with the ladder's hash, and
      what cannot be measured is refused;
  (4) x: a code-seam lifts rung 4 when its proof's PROVES names it, and is refused when not;
  (5) 19.14.8.3, a ticket cannot call itself a fixit: another kind, or an id resolving to no
      ticket, is refused;
  (6) a resolved question lifts rung 4 whoever answered it, measurement included;
  (7) ``cairn test --help`` tells the operator a ticket id is accepted, and no longer says the
      id is Akien's alone.

The world is a scratch git repo holding one component whose proof was committed, sealed red
under an open ladder bound to those committed bytes, then edited. Fixture tickets are plain
JSON in a scratch tickets dir passed as ``tickets_dir``; the question is a fixture in a scratch
root read through the question tool's ``root``. ``reseal`` is imported inside each tooth.
"""
from __future__ import annotations

import hashlib
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
    persist_validation, source_fingerprint,
)
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "e8be83a46ea9": {
        "1": "test_a_fixit_lifts_rung_4_for_the_proof_it_fixes",
        "2": "test_a_fixit_whose_why_does_not_hold_is_refused",
        "3": "test_bytes_git_cannot_find_are_refused",
        "4": "test_a_code_seam_lifts_rung_4_only_when_its_proof_names_it",
        "5": "test_another_kind_or_an_unknown_ticket_is_refused",
        "6": "test_a_measured_answer_lifts_rung_4",
        "7": "test_the_ruling_flag_names_a_ticket_and_not_who_answered",
    },
}

_TID = "f17e8be00001"
_V1 = "def test_one():\n    assert 1\n\n\ndef test_two():\n    assert 2\n"


def _git(root: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-C", str(root), "-c", "user.name=fixture", "-c",
                    "user.email=fixture@localhost", *args], check=True, capture_output=True, env=env)


def _world(v2: str, *, commit_v1: bool = True, proves: dict | None = None) -> Path:
    """A committed proof v1, sealed red under a ladder bound to v1's bytes, edited to ``v2``."""
    root = scratch_dir("cairn-rung4-kind-")
    proof = root / "widget" / "proofs" / "test_widget.py"
    proof.parent.mkdir(parents=True)
    (root / "widget" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    head = f"PROVES = {proves!r}\n\n\n" if proves is not None else ""
    proof.write_text(head + _V1, encoding="utf-8")
    bound = hashlib.sha256(proof.read_bytes()).hexdigest()
    _git(root, "init", "-q")
    if commit_v1:
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", "v1")
    from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
    ladder = {"proof_sha256": bound, "opened": "2026-10-31T10:00:00",
              "last_red": "2026-10-31T10:00:00", "passes": 1, "rung": 3,
              "trouble": "seal-red-fixture-widget", "ruling": None}
    persist_validation({
        "claim": "test_widget.py passes", "caller": "the ladder's fixture",
        "date": datetime.now().isoformat(timespec="seconds"), "method": "fixture",
        "verdict": "red", "falsifier": "the proof exits non-zero", "horizon": "until the proof changes",
        "evidence": {"source_fingerprint": source_fingerprint(str(proof)), "returncode": 1,
                     "seal": {"verdict": "open"}, "reseal_ladder": ladder}},
        proof_path=str(proof), unsealing_because=NETWORK_SEAL_RETIRED)
    proof.write_text(head + v2, encoding="utf-8")
    return proof


def _tickets(**ticket) -> Path:
    d = scratch_dir("cairn-rung4-kind-tickets-")
    (d / f"{_TID}-fixture.json").write_text(json.dumps({"id": _TID, **ticket}), encoding="utf-8")
    return d


def _ask(proof: Path, tickets: Path, tid: str = _TID):
    from cairn.devices.tester.reseal import rung4_refusal
    return rung4_refusal(proof, tid, tickets_dir=tickets)


# v2 removes test_two; WHY names the ticket and the removed tooth
_WHY = f'"""Repaired under {_TID}: test_two measured the old store and was removed."""\n'
_KEPT = "def test_one():\n    assert 1 == 1\n"


def test_a_fixit_lifts_rung_4_for_the_proof_it_fixes():
    proof = _world(_WHY + _KEPT)
    got = _ask(proof, _tickets(node_class="bug", fixes=[str(proof)]))
    assert got is None, f"y: a fixit naming the proof in fixes, its why whole, must lift rung 4: {got!r}"


def test_a_fixit_whose_why_does_not_hold_is_refused():
    cases = (
        ("fixes omits the proof", _WHY + _KEPT, lambda p: []),
        ("the proof does not name the ticket", '"""test_two was removed."""\n' + _KEPT, lambda p: [str(p)]),
        ("the removed tooth goes unnamed", f'"""Repaired under {_TID}."""\n' + _KEPT, lambda p: [str(p)]),
    )
    for label, v2, fixes in cases:
        proof = _world(v2)
        got = _ask(proof, _tickets(node_class="bug", fixes=fixes(proof)))
        assert isinstance(got, str) and _TID in got, f"y must refuse when {label}: {got!r}"


def test_bytes_git_cannot_find_are_refused():
    proof = _world(_WHY + _KEPT, commit_v1=False)
    got = _ask(proof, _tickets(node_class="bug", fixes=[str(proof)]))
    assert isinstance(got, str) and _TID in got, f"unmeasurable removed teeth must refuse: {got!r}"


def test_a_code_seam_lifts_rung_4_only_when_its_proof_names_it():
    named = _world(_WHY + _KEPT, proves={_TID: {"1": "test_one"}})
    got = _ask(named, _tickets(node_class="code-seam"))
    assert got is None, f"x: a code-seam whose PROVES names it must lift rung 4: {got!r}"
    other = _world(_WHY + _KEPT, proves={"someoneelse0": {"1": "test_one"}})
    got = _ask(other, _tickets(node_class="code-seam"))
    assert isinstance(got, str) and _TID in got, f"x must refuse a proof whose PROVES names another: {got!r}"


def test_another_kind_or_an_unknown_ticket_is_refused():
    proof = _world(_WHY + _KEPT, proves={_TID: {"1": "test_one"}})
    got = _ask(proof, _tickets(node_class="concept-piece", fixes=[str(proof)]))
    assert isinstance(got, str) and _TID in got, f"another kind must refuse: {got!r}"
    got = _ask(proof, _tickets(node_class="bug", fixes=[str(proof)]), tid="f17e8be00404")
    assert isinstance(got, str) and "f17e8be00404" in got, f"an unknown ticket must refuse: {got!r}"


def test_a_measured_answer_lifts_rung_4():
    from cairn.devices.tester.reseal import ruling_refusal
    root = scratch_dir("cairn-rung4-kind-q-")
    qid = "open-f17e8be00006"
    (root / f"{qid}.json").write_text(json.dumps({
        "id": qid, "date": "2026-10-31", "ticket": _TID, "question": "may the claim change?",
        "why_it_blocks": "fixture", "raised_by": "fixture", "born_of": None, "source": None,
        "resolved": True, "answer": "measured: yes",
        "answered_by": "measurement: /tmp/x.json, recorded by caller class cc",
        "answered_at": "2026-10-31T09:00:00", "spawned": []}), encoding="utf-8")
    got = ruling_refusal(qid, question_root=root)
    assert got is None, f"rung 4 no longer asks who answered: {got!r}"


def test_the_ruling_flag_names_a_ticket_and_not_who_answered():
    import contextlib
    import io
    from cairn.devices.tester.cli import main
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        try:
            main(["--help"])
        except SystemExit:
            pass
    text = " ".join(out.getvalue().split())
    assert "12-hex ticket" in text, f"--ruling's help must say a ticket id is accepted: {text[-800:]!r}"
    assert "Akien's alone" not in text, "--ruling's help must no longer say the id is Akien's alone"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
