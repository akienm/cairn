"""The deleter's own order answers for an address deleted with no rename (ticket 6e1d0a5c3b27).

96541ff420bc let a deleter's order answer only at the end of an address's rename chain. A
file deleted outright has no chain, so its deleter's order (the one record of where it
went) was unreachable from every ticket that had charted it. Measured 2026-11-19 on
akiendelllinux: e4a12d8e0cbf deleted press_office/CairnComponentOutline.txt (770decaf5, no
rename) and forwarded it to cairn/devices/cairn/requirements/TOC.md, and 109 constrain and
30 orient berths across ~100 tickets stood red behind it.

The narrowing is the point: ONLY the deleter speaks — found as 96541ff420bc finds it, by
the deleting commit's subject opening with its id. A non-deleter's order still never
answers for an address nothing chains it to, alone or with every copy agreeing.
Teeth 1-2 build a synthetic repository (z.py deleted outright, c.py on disk); tooth 3 reads
the live repo and commons.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"6e1d0a5c3b27": {
    "1": "test_the_deleters_own_order_answers_for_an_outright_deletion",
    "2": "test_no_order_but_the_deleters_answers_for_it",
    "3": "test_the_live_outline_resolves_for_a_ticket_that_carries_no_order",
}}

CHARTING, DELETING, OTHER = "aaaaaaaaaaaa", "bbbbbbbbbbbb", "cccccccccccc"
OUTLINE = "press_office/CairnComponentOutline.txt"
SCHEMATIC = "cairn/devices/cairn/requirements/TOC.md"
LIVE_CHARTER = "124c0312c2d8"  # charted the outline; red on the Dell at HEAD 73bfaf1d6


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=proof@cairn", "-c", "user.name=proof", "commit", "-q", "-m", message)


def _resolve(orders: dict, deleted_by: str = DELETING):
    """z.py born, then deleted outright by a commit whose subject opens with ``deleted_by``."""
    from cairn.machines.build_inspector import inspector as insp
    d = scratch_dir("cairn-a-deleters-order-answers-")
    repo = d / "cairn"
    repo.mkdir()
    _git(repo, "init", "-q")
    for name in ("z.py", "c.py"):
        (repo / name).write_text(name + "\n")
    _commit(repo, "born")
    (repo / "z.py").unlink()
    _commit(repo, (deleted_by + ": build — " if deleted_by else "") + "deletes z.py")
    tickets = d / "CairnCommons" / "tickets"
    tickets.mkdir(parents=True)
    for tid, order in orders.items():
        (tickets / (tid + ".json")).write_text(json.dumps({"id": tid, "forwarding": order}))
    for cache in ("_deleting_ticket", "_successor_index", "_hand_order_index"):
        getattr(insp, cache).cache_clear()
    saved_root, saved_exists = insp._TICKETS_ROOT, insp.ref_exists
    try:
        insp._TICKETS_ROOT = str(repo)
        insp.ref_exists = lambda a: (repo / a).exists()
        return insp._resolves_to("z.py", CHARTING, repo_root=repo,
                                 exists=lambda a: (repo / a).exists())
    finally:
        insp._TICKETS_ROOT, insp.ref_exists = saved_root, saved_exists
        for cache in ("_deleting_ticket", "_successor_index", "_hand_order_index"):
            getattr(insp, cache).cache_clear()


def _order(to: str) -> dict:
    return {"to": to, "why": "the deleting build's own record of where this went"}


def test_the_deleters_own_order_answers_for_an_outright_deletion():
    got = _resolve({CHARTING: {}, DELETING: {"z.py": _order("c.py")}})
    assert got == "c.py", got


def test_no_order_but_the_deleters_answers_for_it():
    alone = _resolve({CHARTING: {}, DELETING: {}, OTHER: {"z.py": _order("c.py")}})
    assert alone is None, ("a non-deleter's order answered", alone)
    agreed = _resolve({CHARTING: {}, OTHER: {"z.py": _order("c.py")}}, deleted_by="")
    assert agreed is None, ("a deletion naming no ticket was answered by a copy", agreed)


def _live_root() -> str:
    """A cairn checkout whose sibling holds the live commons (hollow's /tmp worktree has none)."""
    if (_REPO_ROOT.parent / "CairnCommons" / "tickets").is_dir():
        return str(_REPO_ROOT)
    return str(Path.home() / "dev" / "src" / "cairn")


def test_the_live_outline_resolves_for_a_ticket_that_carries_no_order():
    from cairn.machines.build_inspector import inspector as insp
    live = _live_root()
    saved_root = insp._TICKETS_ROOT
    try:
        insp._TICKETS_ROOT = live
        own = insp._forwarding_map(LIVE_CHARTER)
        assert OUTLINE not in own, "the subject carries its own order; this tooth would measure nothing"
        assert insp._forwarding_map("e4a12d8e0cbf").get(OUTLINE) == SCHEMATIC, \
            "the deleter's order is not what this tooth was cast against"
        got = insp._resolves_to(OUTLINE, LIVE_CHARTER, repo_root=_REPO_ROOT)
    finally:
        insp._TICKETS_ROOT = saved_root
    assert got == SCHEMATIC, got


def main() -> int:
    fails = 0
    for name in PROVES["6e1d0a5c3b27"].values():
        try:
            globals()[name]()
            print(f"  ok   {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none hides
            fails += 1
            print(f"  FAIL {name}: {type(exc).__name__}: {exc}")
    print("RED" if fails else "GREEN")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
