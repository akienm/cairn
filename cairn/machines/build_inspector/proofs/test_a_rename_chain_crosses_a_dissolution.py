"""A rename chain continues through a later dissolution's forwarding order (ticket 96541ff420bc).

Git's rename record can say a.py became b.py; it cannot say what b.py's later deletion
meant. That is a forwarding order, reached only at the end of the address's own rename
chain: the DELETING ticket's first (the deleting commit's subject opens with its id),
else the one place every other order agrees on. Six teeth build a synthetic repository
(a.py renamed to b.py, b.py and z.py then deleted, c.py, own.py and keep.py on disk)
with tickets under a tmp CairnCommons; the seventh runs inspect(component='ground_loop')
over the live repo, where 21 pre-absorb addresses stood unresolved on the day this was
cast.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"96541ff420bc": {
    "1": "test_the_chain_crosses_the_deleting_tickets_order",
    "2": "test_no_order_at_the_chain_end_resolves_nothing",
    "3": "test_the_charting_tickets_own_order_still_wins",
    "4": "test_an_order_never_answers_for_an_address_its_chain_never_reached",
    "5": "test_the_deleting_tickets_order_wins_over_a_disagreeing_copy",
    "6": "test_orders_that_disagree_with_no_deleter_answer_nothing",
    "7": "test_the_live_ground_loop_addresses_resolve",
}}

CHARTING, DELETING, OTHER = "aaaaaaaaaaaa", "bbbbbbbbbbbb", "cccccccccccc"


def _git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True, check=True)


def _commit(repo: Path, message: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.email=proof@cairn", "-c", "user.name=proof", "commit", "-q", "-m", message)


def _world(orders: dict, deleted_by: str = DELETING) -> tuple[Path, Path]:
    """d/cairn is the repo; d/CairnCommons/tickets holds one file per {ticket id: order}."""
    d = scratch_dir("cairn-rename-chain-crosses-a-dissolution-")
    repo = d / "cairn"
    repo.mkdir()
    _git(repo, "init", "-q")
    for name in ("a.py", "z.py", "c.py", "own.py", "keep.py"):
        (repo / name).write_text(name + "\n")
    _commit(repo, "born")
    _git(repo, "mv", "a.py", "b.py")
    _commit(repo, "a.py renamed to b.py")
    (repo / "b.py").unlink()
    (repo / "z.py").unlink()
    _commit(repo, (deleted_by + ": build — " if deleted_by else "") + "deletes b.py and z.py")
    tickets = d / "CairnCommons" / "tickets"
    tickets.mkdir(parents=True)
    for tid, order in orders.items():
        (tickets / (tid + ".json")).write_text(json.dumps({"id": tid, "forwarding": order}))
    return d, repo


def _order(to: str) -> dict:
    return {"to": to, "why": "the deleting build's own record of where this went"}


def _resolve(address: str, ticket: str, orders: dict, deleted_by: str = DELETING):
    from cairn.machines.build_inspector import inspector as insp
    assert callable(insp.continued_successor), "no continued_successor in inspector"
    d, repo = _world(orders, deleted_by)
    saved_root, saved_exists = insp._TICKETS_ROOT, insp.ref_exists
    try:
        insp._TICKETS_ROOT = str(repo)
        insp.ref_exists = lambda a: (repo / a).exists()
        return insp._resolves_to(address, ticket, repo_root=repo,
                                 exists=lambda a: (repo / a).exists())
    finally:
        insp._TICKETS_ROOT, insp.ref_exists = saved_root, saved_exists


def test_the_chain_crosses_the_deleting_tickets_order():
    got = _resolve("a.py", CHARTING, {CHARTING: {}, DELETING: {"b.py": _order("c.py")}})
    assert got == "c.py", got


def test_no_order_at_the_chain_end_resolves_nothing():
    got = _resolve("a.py", CHARTING, {CHARTING: {}, DELETING: {}})
    assert got is None, got


def test_the_charting_tickets_own_order_still_wins():
    got = _resolve("a.py", CHARTING, {CHARTING: {"a.py": _order("own.py")},
                                      DELETING: {"b.py": _order("c.py")}})
    assert got == "own.py", got


def test_an_order_never_answers_for_an_address_its_chain_never_reached():
    # z.py was deleted with no rename; the deleting ticket's order for z.py is that
    # ticket's record, and the charting ticket's resolution never reaches it
    got = _resolve("z.py", CHARTING, {CHARTING: {}, DELETING: {"z.py": _order("c.py")}})
    assert got is None, got


def test_the_deleting_tickets_order_wins_over_a_disagreeing_copy():
    got = _resolve("a.py", CHARTING, {CHARTING: {},
                                      DELETING: {"b.py": _order("c.py")},
                                      OTHER: {"b.py": _order("keep.py")}})
    assert got == "c.py", got


def test_orders_that_disagree_with_no_deleter_answer_nothing():
    orders = {CHARTING: {}, DELETING: {"b.py": _order("c.py")}, OTHER: {"b.py": _order("keep.py")}}
    assert _resolve("a.py", CHARTING, orders, deleted_by="") is None
    agreed = {CHARTING: {}, DELETING: {"b.py": _order("c.py")}, OTHER: {"b.py": _order("c.py")}}
    got = _resolve("a.py", CHARTING, agreed, deleted_by="")
    assert got == "c.py", got


def _live_tickets_root() -> str:
    """A cairn checkout whose sibling holds the live commons: this repo when CairnCommons sits beside
    it, else the home checkout — hollow's worktree under /tmp has no commons beside it, and
    the forwarding orders this tooth reads live only there (hollow.py resolves it the same way)."""
    if (_REPO_ROOT.parent / "CairnCommons" / "tickets").is_dir():
        return str(_REPO_ROOT)
    return str(Path.home() / "dev" / "src" / "cairn")


def test_the_live_ground_loop_addresses_resolve():
    from cairn.machines.build_inspector import inspector as insp
    assert callable(insp.continued_successor), "no continued_successor in inspector"
    from cairn.tools.chain import grammar
    live = _live_tickets_root()
    saved_root, saved_exists = insp._TICKETS_ROOT, insp.ref_exists
    try:
        # the code under test, over the live repo's records: forwarding orders and
        # commons-relative refs (tickets/...) are read where the commons actually is
        insp._TICKETS_ROOT = live
        insp.ref_exists = lambda r: saved_exists(r) or grammar.ref_exists(r, live)
        report = insp.inspect(component="ground_loop")
    finally:
        insp._TICKETS_ROOT, insp.ref_exists = saved_root, saved_exists
    mine = [f for f in report["findings"]
            if f.get("method") in ("survey_holdings_resolve", "charted_refs_resolve")]
    assert mine == [], [(f.get("method"), (f.get("values") or {}).get("address") or f.get("about"))
                        for f in mine]


def main() -> int:
    fails = 0
    for name in PROVES["96541ff420bc"].values():
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
