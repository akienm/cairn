"""Teeth for ticket 6fc14bbead55: rung 4 admits the union of code-seams that declared the proof.

Measured 2026-11-14 (q47): the seal on cairn/tools/import_sieve/proofs/test_import_sieve.py was
refused at rung 4. Its ladder bound the repair to the bytes hashing d7b07ed4cdd5, and two
code-seams moved the proof after that: dd79ed8a1ece (3073fed60) and 149b9a1ab9c4 (2b8400868,
8627334b2). Both name the proof in their bounds.in, and the proof text names both. Rung 4
refused each one alone because PROVES did not name it, and with no id it refused for want of a
ruling. So no single id could admit the proof.

Rung 4's why (outline 19.14.8.2-3) is that a proof's assertions move only under a recorded
reason. A code-seam whose cast-time bounds.in names the proof IS such a reason. When two tickets
move the proof under one ladder, the reason is their union. "Uncovered" is MEASURED: the tickets
that changed the proof are read from git, as the ticket id leading each commit subject that
touched the proof after the newest commit holding the bound bytes.

  (1) the import_sieve case as a fixture: two code-seams that declare the proof in bounds.in and
      are named in the proof text are admitted together, as "A,B";
  (2) either one alone is refused, and the refusal names the other, the uncovered changer;
  (3) a code-seam that names the proof in neither PROVES nor bounds.in is refused;
  (4) a removed tooth that the proof does not name is refused under the union.

The world is a scratch git repo. It holds a proof committed as v1 (the ladder's bound bytes,
sealed red under an open ladder) and then two commits, each led by one fixture ticket's id.
Fixture tickets are plain JSON in a scratch tickets dir. ``reseal`` is imported inside each tooth.
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
    "6fc14bbead55": {
        "1": "test_two_declaring_code_seams_are_admitted_together",
        "2": "test_either_alone_is_refused_naming_the_other",
        "3": "test_a_code_seam_declaring_the_proof_nowhere_is_refused",
        "4": "test_an_unnamed_removed_tooth_is_refused_under_the_union",
    },
}

_A, _B, _C = "f6c1aaaa0001", "f6c1bbbb0002", "f6c1cccc0003"
_V1 = "def test_one():\n    assert 1\n\n\ndef test_two():\n    assert 2\n"


def _git(root: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-C", str(root), "-c", "user.name=fixture", "-c",
                    "user.email=fixture@localhost", *args], check=True, capture_output=True, env=env)


def _world(by_a: str, by_b: str) -> Path:
    """v1 committed and sealed red under a ladder bound to it; then A's commit, then B's."""
    root = scratch_dir("cairn-rung4-union-")
    proof = root / "widget" / "proofs" / "test_widget.py"
    proof.parent.mkdir(parents=True)
    proof.write_text(_V1, encoding="utf-8", newline="\n")
    bound = hashlib.sha256(proof.read_bytes()).hexdigest()
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "v1")
    from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
    ladder = {"proof_sha256": bound, "opened": "2026-11-13T16:24:19",
              "last_red": "2026-11-13T16:24:19", "passes": 1, "rung": 3,
              "trouble": "seal-red-fixture-widget", "ruling": None}
    persist_validation({
        "claim": "test_widget.py passes", "caller": "the ladder's fixture",
        "date": datetime.now().isoformat(timespec="seconds"), "method": "fixture",
        "verdict": "red", "falsifier": "the proof exits non-zero", "horizon": "until the proof changes",
        "evidence": {"source_fingerprint": source_fingerprint(str(proof)), "returncode": 1,
                     "seal": {"verdict": "open"}, "reseal_ladder": ladder}},
        proof_path=str(proof), unsealing_because=NETWORK_SEAL_RETIRED)
    for tid, text in ((_A, by_a), (_B, by_b)):
        proof.write_text(text, encoding="utf-8", newline="\n")
        _git(root, "add", "-A")
        _git(root, "commit", "-q", "-m", f"{tid}: a change to the widget proof")
    return proof


def _tickets(proof: Path, **declares) -> Path:
    """One code-seam per id; ``declares[id]`` is True when its bounds.in names the proof."""
    d = scratch_dir("cairn-rung4-union-tickets-")
    for tid in (_A, _B, _C):
        bounds = [str(proof)] if declares.get(tid, True) else ["widget/code.py"]
        (d / f"{tid}-fixture.json").write_text(json.dumps({
            "id": tid, "node_class": "code-seam", "bounds": {"in": bounds, "out": []}}),
            encoding="utf-8")
    return d


def _ask(proof: Path, tickets: Path, ruling: str):
    from cairn.devices.tester.reseal import rung4_refusal
    return rung4_refusal(proof, ruling, tickets_dir=tickets)


# A keeps both teeth; B removes test_two and names it. Both name themselves: the
# import_sieve shape, where each ticket's change names the ticket that made it.
_BY_A = f"# {_A}: test_one's assertion follows A's change\n" + _V1.replace("assert 1", "assert 1 == 1")
_BY_B = (f"# {_A}: test_one's assertion follows A's change\n"
         f"# {_B}: test_two measured the old store and was removed\n"
         "def test_one():\n    assert 1 == 1\n")


def test_two_declaring_code_seams_are_admitted_together():
    proof = _world(_BY_A, _BY_B)
    got = _ask(proof, _tickets(proof), f"{_A},{_B}")
    assert got is None, f"two code-seams declaring the proof in bounds.in must lift rung 4 together: {got!r}"


def test_either_alone_is_refused_naming_the_other():
    proof = _world(_BY_A, _BY_B)
    tickets = _tickets(proof)
    for given, other in ((_A, _B), (_B, _A)):
        got = _ask(proof, tickets, given)
        assert isinstance(got, str) and other in got, \
            f"{given} alone must be refused naming {other}, which also changed the proof: {got!r}"


def test_a_code_seam_declaring_the_proof_nowhere_is_refused():
    proof = _world(_BY_A, _BY_B)
    got = _ask(proof, _tickets(proof, **{_B: False}), f"{_A},{_B}")
    assert isinstance(got, str) and _B in got, \
        f"a code-seam naming the proof in neither PROVES nor bounds.in must refuse: {got!r}"


def test_an_unnamed_removed_tooth_is_refused_under_the_union():
    silent = _BY_B.replace(" and was removed", "")
    silent = silent.replace("test_two measured", "a tooth measured")
    proof = _world(_BY_A, silent)
    got = _ask(proof, _tickets(proof), f"{_A},{_B}")
    assert isinstance(got, str) and "test_two" in got, \
        f"a removed tooth no ticket names must refuse under the union: {got!r}"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
