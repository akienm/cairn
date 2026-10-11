"""Proof for ticket c3f8efa612ce — a rehearsal read covers every decision of a long ticket.

Measured: the Haiku reader drops the TAIL decisions of a long ticket, and a whole re-read told
'missing D<n>' drops them again (cd8096f9eeca, 22 decisions, refused rc 2 twice on
2026-10-11). When a read's only lacks are missing decision ids, the re-read asks for exactly
those nodes and merges them into the tree it already returned.

1. a reader that returns D1..D17 of 22 on attempt 1 and, when handed the missing list,
   D18..D22 — read_tree returns one tree with exactly D1..D22 once each;
2. the patch attempt's prompt names exactly the missing ids, carries the earlier nodes, and
   is not the whole-tree HANDED_BACK; its attempt is recorded with kind 'patch';
3. a reader whose first tree has a doubled id still gets a whole re-read (the prompt is the
   full HANDED_BACK, not the patch).

A scripted fake Reader — no model call. ``rehearsal`` is imported inside the teeth.

Run bare:  PYTHONPATH=. python3 cairn/machines/rehearsal/proofs/test_a_long_ticket_is_read_whole.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "c3f8efa612ce": {
        "1": "a_dropped_tail_is_patched_into_one_whole_tree",
        "2": "the_patch_prompt_asks_for_exactly_the_missing_ids",
        "3": "a_doubled_id_still_gets_a_whole_re_read",
    },
}

TEXT = "# a long ticket\n\n" + "\n".join(f"D{i}: decision {i}" for i in range(1, 23)) + "\n"
IDS = set(range(1, 23))
WHOLE = "return the whole\ntree"   # HANDED_BACK's own words: the whole-tree re-read
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail[:300]}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _node(i: int) -> dict:
    return {"step": f"D{i}", "state": "builds_as_written", "assumption": f"marker-of-D{i}",
            "would_settle": "", "confidence": 0.9}


class _Scripted:
    """Returns ``trees[k]`` on call k (the last one repeats), recording every prompt."""

    def __init__(self, *trees):
        self.trees, self.prompts = list(trees), []

    def __call__(self, prompt_text: str, schema_doc: dict):
        self.prompts.append(prompt_text)
        tree = self.trees[min(len(self.prompts), len(self.trees)) - 1]
        return {"nodes": [dict(n) for n in tree]}, {"model": "scripted", "cost_usd": 0}


def _steps(tree: dict) -> list[str]:
    return [n["step"] for n in tree["nodes"]]


def main() -> int:
    from cairn.machines.rehearsal import rehearsal as R

    # 1 and 2 — the dropped tail
    reader = _Scripted([_node(i) for i in range(1, 18)], [_node(i) for i in range(18, 23)])
    tree, attempts = None, []
    try:
        tree, attempts = R.read_tree(TEXT, reader, 1, ticket="c3f8efa612ce", sha="x", decision_ids=IDS)
        got = _steps(tree)
        check(PROVES["c3f8efa612ce"]["1"], sorted(got, key=lambda s: int(s[1:])) == [f"D{i}" for i in range(1, 23)]
              and len(got) == 22 and len(attempts) == 2, f"steps={got}; attempts={len(attempts)}")
    except Exception as exc:  # noqa: BLE001
        check(PROVES["c3f8efa612ce"]["1"], False, f"{type(exc).__name__}: {exc}")
    p2 = reader.prompts[1] if len(reader.prompts) > 1 else ""
    named = set(re.findall(r"\bD(\d+)\b", p2[len(TEXT):]))
    asked_missing = {str(i) for i in range(18, 23)} <= named
    carries_earlier = all(f"marker-of-D{i}" in p2 for i in range(1, 18))
    kinds = [a.get("kind") for a in attempts]
    check(PROVES["c3f8efa612ce"]["2"],
          asked_missing and carries_earlier and WHOLE not in p2 and kinds[1:2] == ["patch"],
          f"asked_missing={asked_missing} carries_earlier={carries_earlier} "
          f"whole={WHOLE in p2} kinds={kinds}")

    # 3 — a doubled id is not a dropped tail
    doubled = [_node(i) for i in range(1, 23)] + [_node(3)]
    reader3 = _Scripted(doubled, [_node(i) for i in range(1, 23)])
    try:
        tree3, attempts3 = R.read_tree(TEXT, reader3, 1, ticket="c3f8efa612ce", sha="x", decision_ids=IDS)
        p = reader3.prompts[1] if len(reader3.prompts) > 1 else ""
        check(PROVES["c3f8efa612ce"]["3"],
              WHOLE in p and attempts3[1].get("kind") != "patch" and len(_steps(tree3)) == 22,
              f"whole={WHOLE in p} kinds={[a.get('kind') for a in attempts3]}")
    except Exception as exc:  # noqa: BLE001
        check(PROVES["c3f8efa612ce"]["3"], False, f"{type(exc).__name__}: {exc}")

    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
