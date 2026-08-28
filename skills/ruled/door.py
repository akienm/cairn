"""skills/ruled/door.py — Akien's RULED marker fires the ruling door.

Three modes:
  cairn ruled <id>        confirm the named packet; show verify result
  cairn ruled             list open unmarked rulings
  cairn ruled <bogus>     refuse loudly, naming the store searched
"""

from __future__ import annotations

import json
import sys

from cairn.machines.ruling import ruling


def _confirm(ruling_id: str) -> int:
    evidence = f"cairn ruled {ruling_id}"
    try:
        path = ruling.confirm(ruling_id, evidence)
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"confirmed: {path}")
    record = json.load(open(path, encoding="utf-8"))
    verdict = ruling.verify(record)
    mark = "green" if verdict["green"] else "RED"
    ruled = "RULED" if verdict["ruled"] else "mine"
    print(f"  verify: {mark}  {ruled}")
    for failure in verdict["failures"]:
        print(f"  ! {failure}")
    return 0


def _list_open() -> int:
    reds = ruling.open_rulings()
    if not reds:
        print("no open unmarked rulings")
        return 0
    for v in reds:
        mark = "RULED" if v["ruled"] else "mine"
        print(f"  RED  {mark:5}  {v['id']}")
        for failure in v["failures"]:
            print(f"       ! {failure}")
    print(f"\n{len(reds)} open ruling(s)")
    return 0


def _refuse(ruling_id: str) -> int:
    store = ruling.store_dir()
    print(f"no such ruling: {ruling_id}", file=sys.stderr)
    print(f"store searched: {store}", file=sys.stderr)
    all_ids = [r.get("id", "?") for r in ruling.load_all()]
    if all_ids:
        print(f"known rulings: {', '.join(all_ids)}", file=sys.stderr)
    else:
        print("the store is empty", file=sys.stderr)
    return 1


def main(argv: list[str]) -> int:
    if not argv:
        return _list_open()
    ruling_id = argv[0]
    known = {r.get("id") for r in ruling.load_all()}
    if ruling_id in known:
        return _confirm(ruling_id)
    return _refuse(ruling_id)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
