#!/usr/bin/env python3
"""Proof that the two history rows written past the projector carry their predecessor's standing (ba8c62b8203e).

WHAT IT PROVES, and the reason is a measured leak: on 2026-10-02 CC appended tester history seq 64
and counting_block history seq 2 through ``artifact.write`` verb ``append``, past
``projector.append_entry``'s floor (``projector.UNIVERSAL_REQUIRED``), so neither carries
``standing``. 62a57b781efc closed that door; this ticket repairs the two rows that passed before it
closed. Akien chose the set and the rule — "i, leave the july one" (open-a13486d0510d): each row
takes the standing of the row before it, and diagnostic_inspector seq 4 (2026-07-25, pre-journal)
stays as written, the exhibit test_append_door_instrument.py keeps. Parent: 471aa05ba639.

One tooth, the falsifier's one clause (PROVES below), over the LIVE histories — history is
append-only, so a named row's identity is fixed and the assertion is an invariant, not a snapshot:
  each of the two rows carries a non-empty standing equal to its predecessor's, and
  diagnostic_inspector seq 4 still lacks it.

    bin/cairn test cairn/tools/charter/proofs/test_the_two_bypass_rows_carry_their_predecessors_standing.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

PROVES = {"ba8c62b8203e": {
    "all": "test_the_two_bypass_rows_carry_their_predecessors_standing",
}}

REPAIRED = [("cairn/devices/tester/history.json", 64), ("cairn/machines/counting_block/history.json", 2)]
KEPT = ("diagnostic_inspector", 4)


def _row_and_prev(rel: str, seq: int):
    body = json.loads((REPO / rel).read_text(encoding="utf-8"))
    idx = [i for i, r in enumerate(body) if r.get("seq") == seq]
    if len(idx) != 1 or idx[0] == 0:
        return None, None
    return body[idx[0]], body[idx[0] - 1]


def test_the_two_bypass_rows_carry_their_predecessors_standing() -> list[str]:
    bad = []
    for rel, seq in REPAIRED:
        row, prev = _row_and_prev(rel, seq)
        if row is None:
            bad.append(f"{rel}: seq {seq} not found once with a predecessor")
            continue
        if not row.get("standing"):
            bad.append(f"{rel}: seq {seq} carries no standing")
        elif row["standing"] != prev.get("standing"):
            bad.append(f"{rel}: seq {seq} standing {row['standing']!r} != predecessor seq "
                       f"{prev.get('seq')}'s {prev.get('standing')!r}")
    kept = [p for p in REPO.rglob(f"{KEPT[0]}/history.json") if ".git" not in p.parts]
    if len(kept) != 1:
        bad.append(f"{KEPT[0]}/history.json found {len(kept)} times")
    else:
        rows = [r for r in json.loads(kept[0].read_text()) if r.get("seq") == KEPT[1]]
        if len(rows) != 1 or rows[0].get("standing"):
            bad.append(f"{KEPT[0]} seq {KEPT[1]} is no longer the kept standing-less exhibit")
    return bad


def main() -> int:
    name = PROVES["ba8c62b8203e"]["all"]
    try:
        bad = test_the_two_bypass_rows_carry_their_predecessors_standing()
    except Exception as exc:  # noqa: BLE001
        bad = [f"aborted: {exc!r}"]
    print(f"  {'PASS' if not bad else 'FAIL'}  {name}" + (f"  — {'; '.join(bad)}" if bad else ""))
    print(f"\n{'GREEN' if not bad else 'RED — 1 failure(s)'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
