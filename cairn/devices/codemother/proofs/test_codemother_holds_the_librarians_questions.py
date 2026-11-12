"""Proof for ticket d12fd9781fb6 — CodeMother holds the librarian's cross-domain questions by id.

One tooth per numbered falsifier clause:

  1. cognition_questions.json carries no question text for any corpus id, and no
     cognition_questions or novelty_matrix keys.
  2. Every held id resolves through the librarian's load(), and the holds list includes
     Q-cog-014..018 (the five UU questions she never had).
  3. seed(dry_run=True) returns one entry per held id plus one per coding_domain question, and
     each held entry's content starts with the corpus text.
  4. A holds list naming an unknown id is reported in errors, and the CLI exits non-zero.
  5. seed_trees.py reaches the corpus only through the module, never by a path to the JSON.
  6. Every held entry's provenance carries the corpus origin.

Every import of what the build changed happens inside a tooth.

    bin/cairn test cairn/devices/codemother/proofs/test_codemother_holds_the_librarians_questions.py
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"d12fd9781fb6": {
    "1": "test_her_file_carries_no_corpus_text",
    "2": "test_every_held_id_resolves_and_the_five_missing_are_held",
    "3": "test_a_dry_seed_lands_the_corpus_text",
    "4": "test_an_unknown_held_id_is_loud",
    "5": "test_seed_reaches_the_corpus_only_through_the_module",
    "6": "test_every_held_entry_carries_its_origin",
}}

HERE = _REPO_ROOT / "cairn" / "devices" / "codemother"
QFILE = HERE / "cognition_questions.json"
SEED = HERE / "seed_trees.py"


def _corpus() -> dict:
    from cairn.devices.librarian import cross_domain_questions
    return {q["id"]: q for q in cross_domain_questions.load()["questions"]}


def _seed():
    from cairn.devices.codemother import seed_trees
    return seed_trees


def _mine() -> dict:
    return json.loads(QFILE.read_text())


def _strings(o):
    if isinstance(o, dict):
        for v in o.values():
            yield from _strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from _strings(v)
    elif isinstance(o, str):
        yield o


def test_her_file_carries_no_corpus_text():
    mine = _mine()
    assert "cognition_questions" not in mine and "novelty_matrix" not in mine, sorted(mine)
    texts = {q["question"] for q in _corpus().values()}
    hits = [s for s in _strings(mine) if s in texts]
    assert not hits, f"corpus text still in her file: {hits}"
    assert mine.get("delegated_from") == "cairn/devices/librarian/cross_domain_questions.json", mine.get("delegated_from")


def test_every_held_id_resolves_and_the_five_missing_are_held():
    holds, corpus = _mine()["holds"], _corpus()
    assert holds, "no holds list"
    assert all(h in corpus for h in holds), [h for h in holds if h not in corpus]
    for n in range(14, 19):
        assert f"Q-cog-{n:03d}" in holds, f"Q-cog-{n:03d} is not held"


def _dry() -> dict:
    r = _seed().seed(dry_run=True)
    assert r["errors"] == 0, r["details"]["errors"]
    return r


def test_a_dry_seed_lands_the_corpus_text():
    r, mine, corpus = _dry(), _mine(), _corpus()
    entries = r["details"]["deposited"]
    held = [e for e in entries if e["section"] == "held"]
    coding = [e for e in entries if e["section"] == "coding_domain"]
    assert [e["id"] for e in held] == mine["holds"], [e["id"] for e in held]
    assert len(coding) == len(mine["coding_domain"]["questions"]), len(coding)
    assert len(entries) == len(mine["holds"]) + len(mine["coding_domain"]["questions"]), len(entries)
    for e in held:
        assert e["content"].startswith(corpus[e["id"]]["question"]), (e["id"], e["content"])


def test_an_unknown_held_id_is_loud():
    mine = _mine()
    mine["holds"] = mine["holds"] + ["Q-cog-999"]
    with tempfile.TemporaryDirectory() as d:
        p = Path(d) / "q.json"
        p.write_text(json.dumps(mine))
        r = _seed().seed(dry_run=True, questions_file=p)
        assert any(e["id"] == "Q-cog-999" for e in r["details"]["errors"]), r["details"]["errors"]
        cli = subprocess.run([sys.executable, "-m", "cairn.devices.codemother.seed_trees", "--dry-run",
                              "--questions", str(p)], cwd=_REPO_ROOT, capture_output=True, text=True,
                             timeout=60)
    assert cli.returncode != 0, f"CLI exited {cli.returncode}: {cli.stdout[-400:]}"
    assert "Q-cog-999" in cli.stdout, cli.stdout[-400:]


def test_seed_reaches_the_corpus_only_through_the_module():
    src = SEED.read_text()
    assert "cross_domain_questions.load()" in src, "seed_trees does not call the librarian's load()"
    for line in src.splitlines():
        if "cross_domain_questions.json" in line:
            assert "source" in line and "#" in line, f"a path to the corpus JSON: {line.strip()}"
    assert "librarian\" /" not in src and "librarian' /" not in src, "seed_trees builds a path into the librarian"


def test_every_held_entry_carries_its_origin():
    corpus = _corpus()
    for e in _dry()["details"]["deposited"]:
        if e["section"] != "held":
            continue
        prov = e["provenance"]
        assert prov.get("origin") == corpus[e["id"]]["origin"], (e["id"], prov)


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
