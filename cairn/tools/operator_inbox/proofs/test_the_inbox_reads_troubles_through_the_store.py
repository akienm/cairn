#!/usr/bin/env python3
"""Proof that the operator inbox reads troubles only through trouble's published store (RULE 1).

The build inspector's encapsulation_holds filed, 2026-11-11, three reaches from this tool into
trouble's device code: inbox.py:285 and inbox.py:996 built a TroubleDevice to read the store,
and test_operator_inbox.py:48 did the same for its independent read. Outline 2.3.7.1.3 names
trouble's published client tool as the one exception to "talk over the bus"; the tool is
cairn.devices.trouble.tools.store.store, and the cairn device and web_server already read the
store through it. A reader never folds pending emissions: folding is the owner's write
(Law 6), done by TroubleDevice in its own process. Ticket 5e1b0c7d2a94 moved the reads.

Teeth:
  (1) no RULE 1 breach from a file under operator_inbox lands on trouble's code;
  (2) read_troubles and read_all_troubles over a scratch store count the top as live and
      cleared/ as cleared, return the whole record, and change nothing in the store;
  (3) inbox.py names cairn.devices.trouble.tools.store and no other trouble module.

    bin/cairn test cairn/tools/operator_inbox/proofs/test_the_inbox_reads_troubles_through_the_store.py
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"5e1b0c7d2a94": {"1": "test_no_breach_from_the_inbox_lands_on_trouble",
                           "2": "test_the_store_reads_count_by_location_and_write_nothing",
                           "3": "test_the_inbox_names_only_the_published_store"}}

INBOX = "cairn/tools/operator_inbox"
TROUBLE = "cairn/devices/trouble"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def test_no_breach_from_the_inbox_lands_on_trouble() -> None:
    from cairn.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        breaches = inspector.encapsulation_breaches(".")
    finally:
        os.chdir(here)
    mine = [b for b in breaches if str(b.get("file", "")).startswith(INBOX + "/")
            and str(b.get("target", "")).startswith(TROUBLE)]
    # Not blind: the sieve read the tree and found breaches elsewhere. A sieve that returned
    # [] for everything would pass the first half alone.
    check("test_no_breach_from_the_inbox_lands_on_trouble", not mine and bool(breaches),
          f"{len(breaches)} breach(es) in all; inbox -> trouble: "
          + "; ".join(f"{b['file']}:{b['line']} imports {b['module']}" for b in mine))


def _snapshot(root: Path) -> dict:
    return {str(p.relative_to(root)): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def test_the_store_reads_count_by_location_and_write_nothing() -> None:
    from cairn.tools.operator_inbox.inbox import read_all_troubles, read_troubles
    with tempfile.TemporaryDirectory() as tmp:
        top = Path(tmp) / "troubletickets"
        (top / "cleared").mkdir(parents=True)
        # Location is liveness: the top is live whatever its standing field says.
        (top / "a-live-one.json").write_text(json.dumps(
            {"id": "a-live-one", "standing": "OPEN", "why": "fixture", "count": 2, "extra": "kept"}))
        (top / "says-cleared-but-stands-at-top.json").write_text(json.dumps(
            {"id": "says-cleared-but-stands-at-top", "standing": "CLEARED", "why": "fixture"}))
        (top / "cleared" / "a-cleared-one.json").write_text(json.dumps(
            {"id": "a-cleared-one", "standing": "CLEARED", "why": "fixture"}))
        before = _snapshot(Path(tmp))
        t = read_troubles(path=str(top))
        a = read_all_troubles(path=str(top))
        after = _snapshot(Path(tmp))
    live_ids = sorted(x["id"] for x in t["live"])
    ok = (t["live_count"] == 2 and t["total_count"] == 3 and a["count"] == 3
          and live_ids == ["a-live-one", "says-cleared-but-stands-at-top"]
          and any(x.get("extra") == "kept" for x in t["live"])
          and sorted(x["id"] for x in a["items"]) == ["a-cleared-one", "a-live-one",
                                                       "says-cleared-but-stands-at-top"]
          and before == after)
    check("test_the_store_reads_count_by_location_and_write_nothing", ok,
          f"live={t['live_count']} total={t['total_count']} all={a['count']} ids={live_ids} "
          f"store_changed={before != after}")


def test_the_inbox_names_only_the_published_store() -> None:
    import re
    src = (_REPO / INBOX / "inbox.py").read_text(encoding="utf-8")
    named = sorted(set(re.findall(r"cairn\.devices\.trouble(?:\.[A-Za-z_]+)*", src)))
    others = [m for m in named if not m.startswith("cairn.devices.trouble.tools.store")]
    check("test_the_inbox_names_only_the_published_store",
          bool(named) and not others, f"named: {named}")


TEETH = (test_no_breach_from_the_inbox_lands_on_trouble,
         test_the_store_reads_count_by_location_and_write_nothing,
         test_the_inbox_names_only_the_published_store)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
