"""Proof for ticket e962afb4e8d9: a ref spelled CairnCommons/<rel> resolves under the commons.

Measured 2026-11-16: walking 3f2692580b2f (q173c), the survey judge refused "holding 0 names an
address that does not resolve" for CairnCommons/.gitattributes, a file that exists. grammar's
_ref_exists joins the ref onto the commons itself, so it looked for
CairnCommons/CairnCommons/.gitattributes. The same doubling was fixed in look() under ticket
7a31059daa23.

1. clause_1_the_commons_gitattributes_resolves: CairnCommons/.gitattributes resolves when the
   commons beside the root carries it;
2. clause_2_the_tickets_charter_resolves: CairnCommons/tickets/_charter+why.json resolves the
   same way;
3. clause_3_the_other_spellings_hold: a bare commons rel and a cairn rel still resolve, and
   CairnCommons/<a missing file> and CairnCommons/<a file only the cairn root holds> do not.

A scratch pair of roots (cairn + CairnCommons side by side) and the pure _ref_exists with an
empty roster, so no live tree is read.

Run bare:  PYTHONPATH=. python3 cairn/tools/chain/proofs/test_a_commons_ref_spelled_from_its_root_resolves.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "e962afb4e8d9": {
        "1": "clause_1_the_commons_gitattributes_resolves",
        "2": "clause_2_the_tickets_charter_resolves",
        "3": "clause_3_the_other_spellings_hold",
    },
}

FAILURES: list[str] = []
CHARTER = "tickets/_charter" + "+why.json"


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:600]}")
    if not ok:
        FAILURES.append(name)


def _pair() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("testing-rex-commons-ref-")
    cairn, commons = tmp / "cairn", tmp / "CairnCommons"
    (cairn / "cairn" / "tools").mkdir(parents=True)
    (cairn / "cairn" / "tools" / "testing_rex.py").write_text("# fixture\n", encoding="utf-8")
    (cairn / "testing_rex_cairn_only.txt").write_text("fixture\n", encoding="utf-8")
    (commons / "tickets").mkdir(parents=True)
    (commons / ".gitattributes").write_text("# fixture\n", encoding="utf-8")
    (commons / CHARTER).write_text("{}\n", encoding="utf-8")
    return cairn


def _resolves(ref: str, root: Path) -> bool:
    from cairn.tools.chain.grammar import _ref_exists
    return _ref_exists(ref, str(root), set())


def tooth(name: str, fn) -> None:
    try:
        ok, detail = fn()
        check(name, ok, detail)
    except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
        check(name, False, f"{type(exc).__name__}: {exc}")


def main() -> int:
    root = _pair()
    k = PROVES["e962afb4e8d9"]
    tooth(k["1"], lambda: (_resolves("CairnCommons/.gitattributes", root),
                           f"root={root}"))
    tooth(k["2"], lambda: (_resolves("CairnCommons/" + CHARTER, root), f"root={root}"))

    def three():
        want = {".gitattributes": True, CHARTER: True,
                "cairn/tools/testing_rex.py": True,
                "CairnCommons/testing_rex_missing.json": False,
                "CairnCommons/testing_rex_cairn_only.txt": False}
        got = {r: _resolves(r, root) for r in want}
        return got == want, f"want={want} got={got}"
    tooth(k["3"], three)
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
