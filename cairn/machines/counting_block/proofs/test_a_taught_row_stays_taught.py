"""Proof for ticket 01d34298ecae — what the counting block learned stays learned.

Measured 2026-10-12: compile() derives every row increment from the clears the trouble lane
serves NOW. A re-raise of a CLEARED trouble starts fresh with cleared_by [] (trouble.py:271),
and troubles expire after 30 days, so a row Akien taught un-learns as soon as the clear leaves
the lane. pulse() now keeps taught.json beside table.json — the akien clears compile() applied
— and unions it with the live clears on every pulse.

1. a pulse where an akien clear teaches a row, then a pulse where ask() no longer returns that
   clear: the row's count is unchanged and no raise is reported for it;
2. a cc-class clear never enters taught.json;
3. with taught.json deleted, a pulse equals today's: the row drops back, and table.json is
   byte-identical to a pulse over a fresh world whose lane serves no clears.

The world is the sibling proof's (test_an_akien_hand_teaches_the_row.py): fixture journals,
a scratch raiser and table dir, and an ``ask`` that answers what the tooth says. Nothing live is
read or written but the artifact door's jurisdiction rules. ``block`` is imported inside the
teeth, so a reverted build reds a tooth rather than crashing the import.

Run bare:  PYTHONPATH=. python3 cairn/machines/counting_block/proofs/test_a_taught_row_stays_taught.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "01d34298ecae": {
        "1": "a_taught_row_stays_taught_when_its_clear_leaves_the_lane",
        "2": "a_cc_clear_never_enters_the_ledger",
        "3": "without_the_ledger_the_pulse_is_todays",
    },
}

CHARTER_REL = "cairn/machines/counting_block/intention+why.json"
NEW = ("CairnCommons", "slates/s2.json", "remove", "gate")
TAUGHT = "taught.json"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:300]}")
    if not ok:
        FAILURES.append(name)


def _e(sec: int, rel: str, verb: str, cls: str) -> dict:
    return {"at": f"2026-10-11T12:00:{sec:02d}+00:00", "path": rel, "verb": verb,
            "caller": {"class": cls}}


def _journals() -> dict:
    """Prior, arming, one raise of NEW at :10, NEW again at :30."""
    common = [_e(1, "tickets/aaaa.json", "cast", "cc"), _e(2, "slates/s1.json", "slate", "cc"),
              _e(3, "troubles/old.json", "clear", "gate"), _e(4, "troubles/old.json", "clear", "akien"),
              _e(10, NEW[1], NEW[2], NEW[3]), _e(30, NEW[1], NEW[2], NEW[3])]
    return {"cairn": [_e(5, CHARTER_REL, "genesis", "cc")], "CairnCommons": common}


def _ident(block) -> str:
    return block.slug(block.identity(block.path_class(NEW[0], NEW[1]), NEW[2], NEW[3]))


def _key(block) -> str:
    return block.triple(block.path_class(NEW[0], NEW[1]), NEW[2], NEW[3])


def _row(block, hand_class: str, at: str = "2026-10-11T12:00:20.500000+00:00") -> dict:
    return {"id": _ident(block), "standing": "CLEARED", "by": "akien", "hand_class": hand_class, "at": at}


def _world(base: Path) -> dict:
    from cairn.tools.artifact import artifact as door
    roots = {"cairn": base / "cairn", "CairnCommons": base / "CairnCommons"}
    for r, entries in _journals().items():
        jp = door.journal_path(roots[r])
        jp.parent.mkdir(parents=True, exist_ok=True)
        jp.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")
    return roots


def _pulse(block, base: Path, roots: dict, clears: list[dict]) -> dict:
    from cairn.tools.base.diagnostic import ModuleRaiser
    return block.pulse(roots=roots, raiser=ModuleRaiser(block.COMPONENT, roots={"instance": base / "i"}),
                       where=base / "table", ask=lambda: {"body": {"clears": clears}})


def _table(base: Path) -> dict:
    return json.loads((base / "table" / "table.json").read_text(encoding="utf-8"))


def _taught(base: Path) -> list:
    p = base / "table" / TAUGHT
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def test_1() -> None:
    name = PROVES["01d34298ecae"]["1"]
    try:
        from cairn.machines.counting_block import block
        with tempfile.TemporaryDirectory(prefix="cairn-taught-row-proof-") as d:
            base = Path(d)
            roots = _world(base)
            _pulse(block, base, roots, [_row(block, "akien")])
            first = _table(base)["rows"].get(_key(block))
            second = _pulse(block, base, roots, [])
            after = _table(base)["rows"].get(_key(block))
            mine = [r for r in second["raised"] if block.slug(r["identity"]) == _ident(block)]
            check(name, first == 2 and after == 2 and mine == [],
                  json.dumps({"row_first": first, "row_after": after, "raised_after": mine,
                              "taught": _taught(base)}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def test_2() -> None:
    name = PROVES["01d34298ecae"]["2"]
    try:
        from cairn.machines.counting_block import block
        with tempfile.TemporaryDirectory(prefix="cairn-taught-cc-proof-") as d:
            base = Path(d)
            roots = _world(base)
            _pulse(block, base, roots, [_row(block, "akien"),
                                        _row(block, "cc", "2026-10-11T12:00:20.600000+00:00")])
            taught = _taught(base)
            check(name, isinstance(taught, list)
                  and all(isinstance(t, dict) and t.get("hand_class") == "akien" for t in taught),
                  json.dumps({"taught": taught}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def test_3() -> None:
    name = PROVES["01d34298ecae"]["3"]
    try:
        from cairn.machines.counting_block import block
        with tempfile.TemporaryDirectory(prefix="cairn-taught-gone-proof-") as d, \
                tempfile.TemporaryDirectory(prefix="cairn-taught-fresh-proof-") as f:
            base, fresh = Path(d), Path(f)
            roots = _world(base)
            _pulse(block, base, roots, [_row(block, "akien")])
            (base / "table" / TAUGHT).unlink(missing_ok=True)
            (base / "table" / "table.json").unlink()
            _pulse(block, base, roots, [])
            gone = (base / "table" / "table.json").read_bytes()
            _pulse(block, fresh, _world(fresh), [])
            today = (fresh / "table" / "table.json").read_bytes()
            row = _table(base)["rows"].get(_key(block))
            check(name, row == 0 and gone == today,
                  json.dumps({"row": row, "byte_identical": gone == today}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    test_1()
    test_2()
    test_3()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
