"""Proofs for the charter_removal_repoints_its_owners sieve.

A build that deletes or renames an intention+why.json while a ticket's owning_intention still
names that path is red at its crossing. Two measured cases are why this tooth exists (census of
2026-11-14): f942a413f26d (60e1dd170) moved the inference proxy's charter as a git delete plus
add, with no forwarding order, and left 25 tickets naming the dead path. The 11-08 retirements
deleted six charters that 13 tickets still name. Every one of those crossings was green.

Every tooth builds its own scratch cairn repo plus a sibling CairnCommons/tickets, and calls the
sieve on the crossing's row. Nothing here reads the live commons or starts a device.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "cffcf4fb0335": {
        "1": "test_a_move_git_records_as_delete_plus_add_is_red_naming_ticket_path_and_commit",
        "2": "test_a_retirement_is_red_until_its_owner_is_repointed_or_retired",
        "3": "test_a_valid_forwarding_order_clears_it_and_a_hollow_one_does_not",
        "4": "test_no_charter_removed_adds_nothing_and_unreadable_git_is_its_own_finding",
    },
}

SIEVE = "charter_removal_repoints_its_owners"
CROSSER = "c0ffee000001"   # the crossing ticket: its build commits open their subject with this id
OWNER = "0aa000000001"     # a ticket whose owning_intention names the charter the build removes
OLD = "cairn/devices/x/intention+why.json"
NEW = "cairn/devices/y/intention+why.json"


def _inspector():
    """Bound when a tooth asks, so a reverted inspector.py reds each tooth by name."""
    from cairn.machines.build_inspector import inspector
    return inspector


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True,
                          text=True).stdout


def _charter(repo: Path, rel: str, why: str) -> None:
    p = repo / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps({"intention": why, "why": why * 3}, indent=2) + "\n", encoding="utf-8")


def _ticket(world: Path, tid: str, **fields) -> Path:
    tickets = world / "CairnCommons" / "tickets"
    tickets.mkdir(parents=True, exist_ok=True)
    p = tickets / f"{tid}-scratch.json"
    p.write_text(json.dumps({"ticket": tid, **fields}, indent=2) + "\n", encoding="utf-8")
    return p


def _world(prefix: str) -> tuple[Path, Path]:
    """A scratch cairn repo with charters x and z committed by a seed ticket, and the owner
    ticket naming x. Returns (world, repo)."""
    world = scratch_dir(prefix)
    repo = world / "cairn"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "proof@example.invalid")
    _git(repo, "config", "user.name", "proof")
    _charter(repo, OLD, "component x keeps the ledger of sightings")
    _charter(repo, "cairn/devices/z/intention+why.json", "component z stands throughout")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "5eed00000001: seed charters")
    _ticket(world, OWNER, owning_intention=OLD, workflow_and_state="[PROVED]")
    _ticket(world, CROSSER, owning_intention="cairn/devices/z/intention+why.json",
            workflow_and_state="[PROVEME]")
    return world, repo


def _commit(repo: Path, subject: str) -> str:
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", subject)
    return _git(repo, "rev-parse", "HEAD").strip()


def _shake(repo: Path, ticket: str | None = CROSSER) -> list[dict]:
    row = {"component": "z", **({"crossing_ticket": ticket} if ticket else {})}
    return _inspector().SIEVES[SIEVE](row, repo / "cairn" / "devices" / "z")


def test_the_sieve_is_registered_with_its_record():
    insp = _inspector()
    assert insp.SIEVES.get(SIEVE) is getattr(insp, SIEVE, None), sorted(insp.SIEVES)
    rec = json.loads((Path(insp.__file__).parent / "sieves" / f"{SIEVE}.json")
                     .read_text(encoding="utf-8"))
    assert rec["name"] == SIEVE and rec["band"] == 1, rec


def test_a_move_git_records_as_delete_plus_add_is_red_naming_ticket_path_and_commit():
    """Clause 1, the f942 case."""
    _world_, repo = _world("chartrm-f942")
    (repo / OLD).unlink()
    (repo / OLD).parent.rmdir()
    _charter(repo, NEW, "an entirely different proxy that answers every inference request")
    sha = _commit(repo, f"{CROSSER}: move x to y")
    status = _git(repo, "show", "--name-status", "-M", "--format=", "HEAD")
    assert f"D\t{OLD}" in status and f"A\t{NEW}" in status, \
        f"the fixture must be the delete-plus-add shape, not a rename: {status!r}"
    found = _shake(repo)
    assert len(found) == 1, found
    v = found[0]["values"]
    assert (v["ticket"], v["old_path"], v["commit"]) == (OWNER, OLD, sha), v


def test_a_retirement_is_red_until_its_owner_is_repointed_or_retired():
    """Clause 2, the 11-08 case: a commit that only deletes the charter."""
    world, repo = _world("chartrm-retire")
    (repo / OLD).unlink()
    _commit(repo, f"{CROSSER}: retire x")
    assert [f["values"]["ticket"] for f in _shake(repo)] == [OWNER]
    _ticket(world, OWNER, workflow_and_state="[PROVED]",
            owning_intention=f"none because {OLD} was retired by ticket {CROSSER} (abc1234, 2026-11-14)")
    assert _shake(repo) == [], "an owner retired in the same change still reds"
    _ticket(world, OWNER, owning_intention="cairn/devices/z/intention+why.json",
            workflow_and_state="[PROVED]")
    assert _shake(repo) == [], "an owner repointed to a standing charter still reds"


def test_a_valid_forwarding_order_clears_it_and_a_hollow_one_does_not():
    """Clause 3. Valid means from gone and to a standing charter."""
    world, repo = _world("chartrm-fwd")
    (repo / OLD).unlink()
    _charter(repo, NEW, "an entirely different proxy that answers every inference request")
    _commit(repo, f"{CROSSER}: move x to y")
    base = {"owning_intention": "cairn/devices/z/intention+why.json",
            "workflow_and_state": "[PROVEME]"}
    _ticket(world, CROSSER, **base,
            forwarding={OLD: {"to": "cairn/devices/nowhere/intention+why.json", "why": "moved"}})
    assert [f["values"]["ticket"] for f in _shake(repo)] == [OWNER], \
        "an order forwarding to nothing cleared the finding"
    # 6935a4a71f93's shape: the component forwarded to the proof of its absence. A valid order,
    # but not to a charter, so its owners stay dead and the finding stands.
    (repo / "bin" / "proofs").mkdir(parents=True)
    (repo / "bin" / "proofs" / "test_x_is_gone.py").write_text("", encoding="utf-8")
    _ticket(world, CROSSER, **base, forwarding={
        "cairn/devices/x": {"to": "bin/proofs/test_x_is_gone.py", "why": "retired"}})
    assert [f["values"]["ticket"] for f in _shake(repo)] == [OWNER],         "a forward to a non-charter (a retirement) cleared the finding"
    _ticket(world, CROSSER, **base, forwarding={OLD: {"to": NEW, "why": "x became y"}})
    assert _shake(repo) == [], "a valid forwarding order did not clear the finding"


def test_no_charter_removed_adds_nothing_and_unreadable_git_is_its_own_finding():
    """Clause 4."""
    _world_, repo = _world("chartrm-quiet")
    (repo / "cairn" / "devices" / "z" / "code.py").write_text("x = 1\n", encoding="utf-8")
    _commit(repo, f"{CROSSER}: touch only code")
    assert _shake(repo) == []
    # A removal by some other ticket is not this crossing's change.
    (repo / OLD).unlink()
    _commit(repo, "fade00000001: another ticket retires x")
    assert _shake(repo) == []
    assert _shake(repo, ticket=None) == [], "the sweep (no crossing) has no commit range to read"

    insp = _inspector()
    real = insp._git_lines

    def broken(*a, **k):
        raise insp.GitUnreadable("git log: simulated failure")
    insp._git_lines = broken
    try:
        found = _shake(repo)
    finally:
        insp._git_lines = real
    assert len(found) == 1 and found[0]["values"].get("git_unreadable"), found


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
