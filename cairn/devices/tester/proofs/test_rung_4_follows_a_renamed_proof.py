"""Teeth for ticket 6eb235ee813d — rung 4 finds the bytes its ladder bounded a proof to across a rename.

Measured 2026-11-13: ticket 27e5f90dcfa7 was refused at rung 4 on
cairn/devices/inferenceproxy/proofs/test_host.py, renamed from inference_domain by f942a413f26d:
"git holds no blob of cairn/devices/inferenceproxy/proofs/test_host.py hashing f2dd2cd1…".
``_recorded_bytes`` ran ``git log`` without ``--follow``, so the bounded blob, which git holds
under the old name, was never found, and the seal had to go through open-157cfd5052c0.

WHY THE TEETH ARE THESE. One per falsifier clause; a hollow build fails at least one:
  (1) a proof committed at an old path, its ladder bound to those bytes, renamed with git mv and
      edited under a code-seam ticket its PROVES names, lifts rung 4 (red on the old reseal.py,
      which searched the new path's history only);
  (2) the same rename, where the edit removed a tooth the proof does not name, is refused and the
      refusal names that tooth, so the teeth were measured from the old name's bytes rather than
      refused as unfindable;
  (3) a ladder hash that git holds under no name the proof ever had is still refused as
      unmeasurable, so following the rename did not loosen the gate into "any blob will do".

The world copies test_rung_4_follows_the_ticket_kind.py's: a scratch git repo holding one
component whose proof v1 was committed at widget/proofs/test_old.py, git mv'd to
widget/proofs/test_new.py and committed with a one-line edit (as the measured rename was), sealed red under an open ladder bound to v1's bytes,
then edited. The fixture ticket is plain JSON in a scratch tickets dir passed as ``tickets_dir``.
``reseal`` is imported inside each tooth.
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
    "6eb235ee813d": {
        "1": "test_a_renamed_proof_lifts_rung_4_under_the_code_seam_it_names",
        "2": "test_a_tooth_removed_across_the_rename_is_named_in_the_refusal",
        "3": "test_a_hash_git_holds_under_no_name_is_still_unmeasurable",
    },
}

_TID = "f176eb200001"
_HEAD = f"PROVES = {{{_TID!r}: {{'1': 'test_one'}}}}\n\n\n"
_V1 = _HEAD + "def test_one():\n    assert 1\n\n\ndef test_two():\n    assert 2\n"
_KEPT = "def test_one():\n    assert 1 == 1\n"
# the edit removes test_two; this why names the ticket and the removed tooth
_NAMED = _HEAD + f'"""Repaired under {_TID}: test_two measured the old store and was removed."""\n' + _KEPT
# the same edit, its why naming the ticket but not the removed tooth
_UNNAMED = _HEAD + f'"""Repaired under {_TID}."""\n' + _KEPT


def _git(root: Path, *args: str) -> None:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    subprocess.run(["git", "-C", str(root), "-c", "user.name=fixture", "-c",
                    "user.email=fixture@localhost", "-c", "core.autocrlf=false", *args],
                   check=True, capture_output=True, env=env)


def _world(v2: str, *, bound_to: str = _V1) -> Path:
    """v1 committed at test_old.py, git mv'd to test_new.py and committed, a ladder bound to the
    sha256 of ``bound_to`` opened at the new path, then the new path edited to ``v2``."""
    root = scratch_dir("cairn-rung4-rename-")
    old = root / "widget" / "proofs" / "test_old.py"
    new = root / "widget" / "proofs" / "test_new.py"
    old.parent.mkdir(parents=True)
    (root / "widget" / "code.py").write_text("VALUE = 2\n", encoding="utf-8")
    old.write_text(_V1, encoding="utf-8", newline="\n")
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "v1 at the old name")
    # renamed and edited in one commit, as f942a413f26d moved test_host.py: the new name's own
    # history then never holds the bounded bytes, only the old name's does (a pure git mv
    # would commit v1 at the new name too, and the old reseal.py would find it there)
    _git(root, "mv", "widget/proofs/test_old.py", "widget/proofs/test_new.py")
    new.write_text(_V1 + "\n\n# moved to its new address\n", encoding="utf-8", newline="\n")
    _git(root, "add", "-A")
    _git(root, "commit", "-q", "-m", "renamed and edited")
    bound = hashlib.sha256(bound_to.encode("utf-8")).hexdigest()
    from cairn.devices.tester.isolation import NETWORK_SEAL_RETIRED
    ladder = {"proof_sha256": bound, "opened": "2026-11-13T17:00:00",
              "last_red": "2026-11-13T17:00:00", "passes": 1, "rung": 3,
              "trouble": "seal-red-fixture-widget", "ruling": None}
    persist_validation({
        "claim": "test_new.py passes", "caller": "the ladder's fixture",
        "date": datetime.now().isoformat(timespec="seconds"), "method": "fixture",
        "verdict": "red", "falsifier": "the proof exits non-zero", "horizon": "until the proof changes",
        "evidence": {"source_fingerprint": source_fingerprint(str(new)), "returncode": 1,
                     "seal": {"verdict": "open"}, "reseal_ladder": ladder}},
        proof_path=str(new), unsealing_because=NETWORK_SEAL_RETIRED)
    new.write_text(v2, encoding="utf-8", newline="\n")
    return new


def _tickets() -> Path:
    d = scratch_dir("cairn-rung4-rename-tickets-")
    (d / f"{_TID}-fixture.json").write_text(
        json.dumps({"id": _TID, "node_class": "code-seam"}), encoding="utf-8")
    return d


def _ask(proof: Path):
    from cairn.devices.tester.reseal import rung4_refusal
    return rung4_refusal(proof, _TID, tickets_dir=_tickets())


def test_a_renamed_proof_lifts_rung_4_under_the_code_seam_it_names():
    got = _ask(_world(_NAMED))
    assert got is None, (
        f"a proof renamed under an open ladder, its why whole, must lift rung 4 as an edited "
        f"proof does — git holds the bounded bytes under the old name: {got!r}")


def test_a_tooth_removed_across_the_rename_is_named_in_the_refusal():
    got = _ask(_world(_UNNAMED))
    assert isinstance(got, str) and "test_two" in got and "git holds no blob" not in got, (
        f"the removed tooth must be measured from the old name's bytes and named: {got!r}")


def test_a_hash_git_holds_under_no_name_is_still_unmeasurable():
    never = _HEAD + "def test_one():\n    assert 'never committed'\n"
    got = _ask(_world(_NAMED, bound_to=never))
    assert isinstance(got, str) and "git holds no blob" in got and _TID in got, (
        f"a ladder hash no name of the proof ever held must still be refused: {got!r}")


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
