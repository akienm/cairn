"""Proof for ticket 0539e85f8b2d — the counting block learns from an akien hand on the trouble's
own record.

Measured 2026-10-11: every who-writes-what clear lands in the commons journal with caller class
'gate' (the write happens in the trouble device's process at the drain), so the block, which
taught a row only from a journal clear of class 'akien', taught nothing. The hand is now
measured in the clearer's process (c2172127d7a4) and kept on the trouble's cleared_by
(1c1b18bac2eb); the block reads it through the trouble lane's 'clears' verb.

1. a raised triple whose trouble has one clears row of hand_class 'akien' gets +1 on its row,
   its raise reads 'cleared:akien', and the next entry of that triple counts instead of raising;
2. a clears row of hand_class 'cc' (by 'akien'), beside a journal clear whose caller class is
   'akien', adds nothing: the row stays 0 and the next entry raises again;
3. a trouble lane that does not answer: pulse writes increments 'unknown' and the row is
   unchanged.

The journals are fixtures; teeth 1-2 run the pure fold, tooth 3 the beat over a scratch world
with a scratch raiser and table dir and an ``ask`` that raises. Nothing live is read or
written but the artifact door's jurisdiction rules. ``block`` is imported inside the teeth.

Run bare:  PYTHONPATH=. python3 cairn/machines/counting_block/proofs/test_an_akien_hand_teaches_the_row.py
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
    "0539e85f8b2d": {
        "1": "an_akien_hand_adds_one_to_its_row",
        "2": "a_cc_hand_by_akien_adds_nothing",
        "3": "an_unanswered_lane_is_unknown_and_teaches_nothing",
    },
}

CHARTER_REL = "cairn/machines/counting_block/intention+why.json"
NEW = ("CairnCommons", "slates/s2.json", "remove", "gate")
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail[:300]}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _e(sec: int, rel: str, verb: str, cls: str) -> dict:
    return {"at": f"2026-10-11T12:00:{sec:02d}+00:00", "path": rel, "verb": verb,
            "caller": {"class": cls}}


def _journals(journal_clear_class: str | None = None) -> dict:
    """Prior, arming, one raise of NEW at :10, (a journal clear at :20), NEW again at :30."""
    common = [_e(1, "tickets/aaaa.json", "cast", "cc"), _e(2, "slates/s1.json", "slate", "cc"),
              _e(3, "troubles/old.json", "clear", "gate"), _e(4, "troubles/old.json", "clear", "akien"),
              _e(10, NEW[1], NEW[2], NEW[3])]
    if journal_clear_class:
        common.append(_e(20, "troubles/WHO.json", "clear", journal_clear_class))
    common.append(_e(30, NEW[1], NEW[2], NEW[3]))
    return {"cairn": [_e(5, CHARTER_REL, "genesis", "cc")], "CairnCommons": common}


def _ident(block) -> str:
    return block.slug(block.identity(block.path_class(NEW[0], NEW[1]), NEW[2], NEW[3]))


def _row(block, hand_class: str) -> dict:
    return {"id": _ident(block), "standing": "CLEARED", "by": "akien", "hand_class": hand_class,
            "at": "2026-10-11T12:00:20.500000+00:00"}


def _fix(j: dict, block) -> dict:
    for e in j["CairnCommons"]:
        e["path"] = e["path"].replace("WHO", _ident(block))
    return j


def test_1() -> None:
    name = PROVES["0539e85f8b2d"]["1"]
    try:
        from cairn.machines.counting_block import block
        t = block.compile(_fix(_journals("gate"), block), clears=[_row(block, "akien")])
        key = block.triple(block.path_class(NEW[0], NEW[1]), NEW[2], NEW[3])
        news = [r for r in t["raises"] if r["triple"] == key]
        check(name, t["rows"].get(key) == 2 and len(news) == 1
              and news[0]["disposition"] == "cleared:akien"
              and [i["triple"] for i in t["increments"]] == [key],
              json.dumps({"row": t["rows"].get(key), "raises": [(r["triple"], r["disposition"]) for r in t["raises"]],
                          "increments": t["increments"]}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def test_2() -> None:
    name = PROVES["0539e85f8b2d"]["2"]
    try:
        from cairn.machines.counting_block import block
        t = block.compile(_fix(_journals("akien"), block), clears=[_row(block, "cc")])
        key = block.triple(block.path_class(NEW[0], NEW[1]), NEW[2], NEW[3])
        news = [r for r in t["raises"] if r["triple"] == key]
        check(name, t["rows"].get(key) == 0 and len(news) == 2 and t["increments"] == []
              and news[0]["disposition"] == "cleared:cc",
              json.dumps({"row": t["rows"].get(key), "raises": [(r["triple"], r["disposition"]) for r in t["raises"]],
                          "increments": t["increments"]}))
    except Exception as exc:  # noqa: BLE001
        check(name, False, f"{type(exc).__name__}: {exc}")


def test_3() -> None:
    name = PROVES["0539e85f8b2d"]["3"]
    try:
        from cairn.machines.counting_block import block
        from cairn.tools.base.diagnostic import ModuleRaiser
        with tempfile.TemporaryDirectory(prefix="cairn-akien-hand-proof-") as d:
            base = Path(d)
            roots = {"cairn": base / "cairn", "CairnCommons": base / "CairnCommons"}
            j = _fix(_journals("akien"), block)
            from cairn.tools.artifact import artifact as door
            for r, entries in j.items():
                jp = door.journal_path(roots[r])
                jp.parent.mkdir(parents=True, exist_ok=True)
                jp.write_text("".join(json.dumps(e) + "\n" for e in entries), encoding="utf-8")

            def _down():
                raise ConnectionRefusedError("the trouble lane is not answering")

            block.pulse(roots=roots, raiser=ModuleRaiser(block.COMPONENT, roots={"instance": base / "i"}),
                        where=base / "table", ask=_down)
            t = json.loads((base / "table" / block.TABLE_FILE).read_text(encoding="utf-8"))
            key = block.triple(block.path_class(NEW[0], NEW[1]), NEW[2], NEW[3])
            check(name, t["increments"] == "unknown" and t["rows"].get(key) == 0
                  and "not answering" in json.dumps(t.get("clears_error")),
                  json.dumps({"increments": t["increments"], "row": t["rows"].get(key),
                              "clears_error": t.get("clears_error")}))
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
