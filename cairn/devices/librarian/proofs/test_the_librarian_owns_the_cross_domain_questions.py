"""Proof for ticket 2248911aaf05 — the librarian owns the cross-domain question corpus.

One tooth per numbered falsifier clause:

  1. load() returns the corpus; every origin is verbatim or proposed, and every verbatim entry
     carries said_by, date and source.
  2. All 18 UU Q-cog texts are present verbatim, character for character, as this proof's own
     literal copy of the UU corpus.
  3. Q-nov-001..003 are verbatim, sourced to 20260714.Novelty.txt; Q-nov-004..014 are proposed,
     said_by Gemini.
  4. A corpus with a duplicate id, a missing origin, a verbatim entry without a source and a
     sequence naming an unknown id raises CorpusRefused naming all four in one pass.
  5. plant into a scratch keyed table lands one leaf per question; find(id) returns its text; no
     cairn_embeddings row is written for any question node.
  6. A second plant leaves the leaf and link counts unchanged.
  7. After plant, each consecutive pair of each sequence has a cairn_links row whose source_id
     is the earlier question's node and whose target_id is the later's.
  8. The librarian charter's public_interface names cairn.devices.librarian.cross_domain_questions.

The scratch leaf drops at exit. Its question NODES are not forgotten, and the reason is not a
courtesy: a node is content-addressed, so these are the same nodes the live plant of this corpus
holds (librarian_cross_domain_questions), and forgetting them would take the live tree's nodes
with them. The links are the same pairs the live plant writes, for the same reason.

Every import of what the build added happens inside a tooth.

    bin/cairn test cairn/devices/librarian/proofs/test_the_librarian_owns_the_cross_domain_questions.py
"""

from __future__ import annotations

import contextlib
import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 300  # two plants of 32 keyed deposits + 7 links over live pg

PROVES = {"2248911aaf05": {
    "1": "test_every_entry_says_where_its_words_came_from",
    "2": "test_the_eighteen_uu_questions_are_verbatim",
    "3": "test_the_novelty_questions_are_marked_by_who_worded_them",
    "4": "test_a_bad_corpus_is_refused_naming_every_lack",
    "5": "test_plant_lands_one_keyed_leaf_per_question_and_no_embedding",
    "6": "test_a_second_plant_changes_nothing",
    "7": "test_each_sequence_is_linked_followed_by",
    "8": "test_the_charter_names_the_module",
}}

CHARTER = _REPO_ROOT / "cairn" / "devices" / "librarian" / "intention+why.json"

# The literal copy of UU's corpus (UnseenUniversity/devlab/runtime/memory/questions/*Q-cog-0NN*.json,
# body.question), taken 2026-11-12. Typos and all: they are his.
UU_QCOG = {
    'Q-cog-001': 'What does it mean to me?',
    'Q-cog-002': 'What does that mean?',
    'Q-cog-003': 'How must that work? / how would that have to work?',
    'Q-cog-004': "Which choice is most in alignment with who I'd most like to be?",
    'Q-cog-005': "What's the first thing i say in repsonse to that?",
    'Q-cog-006': 'What looks like it would fit there?',
    'Q-cog-007': 'How could we get around that?',
    'Q-cog-008': 'Where is the lever?',
    'Q-cog-009': 'How will us monkeys screw that up such that i get support questions?',
    'Q-cog-010': 'which of these patterns would be best for this?',
    'Q-cog-011': 'does that leave any gaps?',
    'Q-cog-012': 'are there any patterns that could be trimmed to fit into that gap?',
    'Q-cog-013': 'how might that work?',
    'Q-cog-014': 'what levers exist here?',
    'Q-cog-015': 'What would make this easier (suck less).',
    'Q-cog-016': 'how can i make that stop? (suck less)',
    'Q-cog-017': 'how can i share that?',
    'Q-cog-018': 'if I did this differently, could I find a way that was easier?',
}

_SCRATCH = contextlib.ExitStack()
_TABLE: list[str] = []


def _cdq():
    from cairn.devices.librarian import cross_domain_questions
    return cross_domain_questions


def _trees():
    from cairn.devices.librarian.tools.trees import trees
    return trees


def _store():
    from cairn.devices.db_domain.tools.client import store
    return store


def _planted() -> str:
    """One scratch keyed leaf, planted once, shared by teeth 5-7."""
    if not _TABLE:
        table = _SCRATCH.enter_context(_trees().scratch_leaf("cdqproof", keyed=True))
        _TABLE.append(table)
        _TABLE.append(_cdq().plant(table=table))
    return _TABLE[0]


def _by_id() -> dict:
    return {q["id"]: q for q in _cdq().load()["questions"]}


def test_every_entry_says_where_its_words_came_from():
    doc = _cdq().load()
    assert len(doc["questions"]) == 32, len(doc["questions"])
    for q in doc["questions"]:
        assert q["origin"] in ("verbatim", "proposed"), q
        if q["origin"] == "verbatim":
            assert q.get("said_by") and q.get("date") and q.get("source"), q


def test_the_eighteen_uu_questions_are_verbatim():
    got = _by_id()
    for qid, text in UU_QCOG.items():
        assert qid in got, f"{qid} is missing"
        assert got[qid]["question"] == text, f"{qid}: {got[qid]['question']!r} != {text!r}"
        assert got[qid]["origin"] == "verbatim" and got[qid]["said_by"] == "Akien", got[qid]


def test_the_novelty_questions_are_marked_by_who_worded_them():
    got = _by_id()
    for n in range(1, 4):
        q = got[f"Q-nov-{n:03d}"]
        assert q["origin"] == "verbatim" and q["said_by"] == "Akien", q
        assert "20260714.Novelty.txt" in q["source"], q
    for n in range(4, 15):
        q = got[f"Q-nov-{n:03d}"]
        assert q["origin"] == "proposed" and q["said_by"] == "Gemini", q


def test_a_bad_corpus_is_refused_naming_every_lack():
    cdq = _cdq()
    bad = {"questions": [
        {"id": "A", "question": "a?", "origin": "verbatim", "said_by": "Akien", "date": "2026-01-01", "source": "s"},
        {"id": "A", "question": "dup?", "origin": "proposed"},
        {"id": "B", "question": "no origin?"},
        {"id": "C", "question": "no source?", "origin": "verbatim", "said_by": "Akien", "date": "2026-01-01"},
    ], "sequences": [{"name": "s1", "order": ["A", "Z"]}]}
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "bad.json"
        p.write_text(json.dumps(bad))
        try:
            cdq.load(p)
        except cdq.CorpusRefused as exc:
            msg = str(exc)
        else:
            raise AssertionError("a bad corpus loaded")
    for want in ("duplicate id A", "question B has origin None", "question C is verbatim without source",
                 "names 'Z', which resolves to no question"):
        assert want in msg, f"{want!r} not named: {msg}"


def test_plant_lands_one_keyed_leaf_per_question_and_no_embedding():
    table = _planted()
    trees, store = _trees(), _store()
    assert _TABLE[1]["planted"] == 32, _TABLE[1]
    rows = store.read(table)
    assert len(rows) == 32, f"{len(rows)} leaves"
    for qid, text in UU_QCOG.items():
        found = trees.find(qid, table=table)
        assert len(found) == 1 and found[0]["content"] == text, (qid, found)
    nids = [r["node_id"] for r in rows]
    emb = store.read(trees.EMBEDDINGS_TABLE, where="node_id = ANY(%s)", params=(nids,))
    assert emb == [], f"{len(emb)} embedding rows written for question nodes"


def test_a_second_plant_changes_nothing():
    table = _planted()
    store, trees = _store(), _trees()
    nids = [r["node_id"] for r in store.read(table)]
    before_links = len(store.read(trees.LINKS_TABLE, where="source_id = ANY(%s)", params=(nids,)))
    again = _cdq().plant(table=table)
    assert len(store.read(table)) == 32, "a second plant added leaves"
    after_links = len(store.read(trees.LINKS_TABLE, where="source_id = ANY(%s)", params=(nids,)))
    assert after_links == before_links, f"links {before_links} -> {after_links}"
    assert again == _TABLE[1], (again, _TABLE[1])


def test_each_sequence_is_linked_followed_by():
    table = _planted()
    trees, store = _trees(), _store()
    doc = _cdq().load()
    node = {qid: trees.find(qid, table=table)[0]["node_id"] for qid in _by_id()}
    for s in doc["sequences"]:
        for a, b in zip(s["order"], s["order"][1:]):
            lid = trees.link_id_for(node[a], node[b])
            rows = store.read(trees.LINKS_TABLE, where="link_id = %s", params=(lid,))
            assert rows, f"{s['name']}: no link {a} -> {b}"
            assert rows[0]["source_id"] == node[a] and rows[0]["target_id"] == node[b], \
                f"{s['name']}: {a} -> {b} is linked the wrong way round"


def test_the_charter_names_the_module():
    charter = json.loads(CHARTER.read_text())
    assert any("cairn.devices.librarian.cross_domain_questions" in str(e)
               for e in charter.get("public_interface", [])), charter.get("public_interface")


def main() -> int:
    teeth = [v for k, v in globals().items() if k.startswith("test_") and callable(v)]
    failed = 0
    try:
        for t in teeth:
            try:
                t()
                print(f"  ok   {t.__name__}")
            except Exception as exc:  # noqa: BLE001
                failed += 1
                print(f"  FAIL {t.__name__}: {type(exc).__name__}: {exc}")
    finally:
        _SCRATCH.close()
    print(f"{len(teeth) - failed}/{len(teeth)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
