"""Proof for ticket 6ba77d0e0c32 — CodeMother finds her held questions through the trees tool.

RULE 1 (outline 2.3.7, 4.4.2): a device reaches the librarian only through the tools it
publishes, and a delegate holding questions works the librarian's trees through the trees
tool. d12fd9781fb6 had seed_trees import cairn.devices.librarian.cross_domain_questions;
the encapsulation_holds sieve reds it. One tooth per numbered falsifier clause:

  1. No file under cairn/devices/codemother imports librarian code but its published tools
     (encapsulation_breaches carries no codemother -> librarian row).
  2. seed(dry_run=True, table=<scratch keyed leaf>) takes each held entry's text, function,
     origin and said_by from the leaf found by its id, and an id the leaf does not carry is
     reported in errors.
  3. The trees tool names the corpus tree (trees.CROSS_DOMAIN_QUESTIONS), and every id
     cognition_questions.json holds is found there on the live store.

Every import of what the build changed happens inside a tooth.

    bin/cairn test cairn/devices/codemother/proofs/test_codemother_finds_held_questions_through_the_trees_tool.py
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"6ba77d0e0c32": {
    "1": "test_codemother_reaches_the_librarian_only_through_its_tools",
    "2": "test_a_dry_seed_takes_held_questions_from_the_tree",
    "3": "test_every_held_id_is_found_in_the_live_corpus_tree",
}}

HERE = _REPO_ROOT / "cairn" / "devices" / "codemother"
QFILE = HERE / "cognition_questions.json"


def test_codemother_reaches_the_librarian_only_through_its_tools():
    from cairn.machines.build_inspector.inspector import encapsulation_breaches
    rows = [r for r in encapsulation_breaches(str(_REPO_ROOT))
            if r["file"].startswith("cairn/devices/codemother/")
            and (r["target"] or "").startswith("cairn/devices/librarian")]
    assert not rows, [(r["file"], r["line"], r["module"]) for r in rows]


def test_a_dry_seed_takes_held_questions_from_the_tree():
    from cairn.devices.codemother import seed_trees
    from cairn.devices.librarian.tools.trees import trees

    plants = [
        ("Q-scratch-a", "How might a scratch question work here?", "verbatim", "Akien", "pattern"),
        ("Q-scratch-b", "What would a proof of the scratch question show?", "proposed", "", "test"),
    ]
    with trees.scratch_leaf("cmheld", keyed=True) as leaf:
        try:
            for qid, text, origin, said_by, fn in plants:
                trees.deposit_keyed(text, qid, {"source": f"proof#{qid}", "origin": origin, "said_by": said_by},
                                    table=leaf, meta={"function": fn, "origin": origin})
            with tempfile.TemporaryDirectory() as d:
                qf = Path(d) / "q.json"
                qf.write_text(json.dumps({"holds": [p[0] for p in plants] + ["Q-scratch-absent"],
                                          "coding_domain": {"questions": []}}))
                r = seed_trees.seed(dry_run=True, questions_file=qf, table=leaf)
        finally:
            trees.forget_leaf(leaf)
    held = {e["id"]: e for e in r["details"]["deposited"] if e["section"] == "held"}
    assert sorted(held) == ["Q-scratch-a", "Q-scratch-b"], sorted(held)
    for qid, text, origin, said_by, fn in plants:
        e = held[qid]
        assert e["content"] == f"{text}\n[{fn}]", (qid, e["content"])
        assert e["provenance"]["origin"] == origin, (qid, e["provenance"])
        assert e["provenance"]["said_by"] == said_by, (qid, e["provenance"])
    errs = r["details"]["errors"]
    assert [e["id"] for e in errs] == ["Q-scratch-absent"], errs
    assert leaf in errs[0]["error"], errs[0]


def test_every_held_id_is_found_in_the_live_corpus_tree():
    from cairn.devices.librarian.tools.trees import trees
    table = trees.CROSS_DOMAIN_QUESTIONS
    assert table == "librarian_cross_domain_questions", table
    holds = json.loads(QFILE.read_text())["holds"]
    assert holds, "cognition_questions.json holds nothing"
    missing = [h for h in holds if not trees.find(h, table=table)]
    assert not missing, f"held ids absent from {table}: {missing}"


def main() -> int:
    teeth = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    for t in teeth:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            failed += 1
            print(f"  FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    print(f"{len(teeth) - failed}/{len(teeth)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
