"""Proof for ticket c7cb0de74f71 — the librarian harvests cross-domain questions in Akien's words.

One tooth per numbered falsifier clause:

  1. harvest over a fixture root (DATED-named .txt notes and a .jsonl with user and assistant
     turns) proposes exactly the question-shaped sentences seen on >= 3 distinct days in user
     turns or notes, and none taken only from assistant turns.
  2. A candidate whose normalized text is already in the corpus is not proposed.
  3. Proposals are sorted by days desc then count desc; each carries days, count and at most 5
     sources.
  4. Two harvests over the same roots write byte-identical proposals.json.
  5. confirm n over a scratch copy of the corpus appends one entry, origin verbatim, said_by
     Akien, date the earliest day, and load() still passes.
  6. add "<q?>" appends one verbatim entry dated today; add of a question already held is
     refused naming the holding id, and the corpus is unchanged.
  7. The corpus write is journaled by the artifact door (a journal line for the corpus path,
     verb write).
  8. The bin script's `proposals` prints one line per proposal.

The world is a temp tree: the door is pointed at a scratch cairn root (set_diagnostic_roots),
so no live record and no live journal is touched. Every import of what the build added happens
inside a tooth.

    bin/cairn test cairn/devices/librarian/proofs/test_the_librarian_harvests_cross_domain_questions.py
"""

from __future__ import annotations

import datetime as dt
import json
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"c7cb0de74f71": {
    "1": "test_harvest_proposes_his_recurring_questions_and_never_an_assistants",
    "2": "test_a_question_the_corpus_holds_is_not_proposed",
    "3": "test_proposals_are_sorted_and_carry_their_evidence",
    "4": "test_two_harvests_write_the_same_bytes",
    "5": "test_confirm_appends_one_verbatim_entry",
    "6": "test_add_appends_today_and_refuses_a_held_question",
    "7": "test_the_corpus_write_is_journaled",
    "8": "test_the_bin_script_prints_one_line_per_proposal",
}}

CORPUS_REL = "cairn/devices/librarian/cross_domain_questions.json"
BIN = _REPO_ROOT / "cairn" / "devices" / "librarian" / "0" / "bin" / "question"

# What the fixture says, and on how many distinct days.
CAT = "What would a cat do here?"          # user turns, 4 days, 4 times
FERN = "is the fern still watered?"        # notes + user, 3 days, 6 times
WATER = "Where does the water go?"         # notes + user, 3 days, 3 times; one lowercase spelling
ASSISTANT_ONLY = "Is this only assistant talk?"   # 5 assistant days, 1 user day
HELD = "How might that work?"              # Q-cog-013 in the corpus, 4 days
TWICE = "only seen twice here?"            # 2 days
LONG = "is this question far too long to count because it carries sixteen words in all of it?"  # 3 days

_W: dict = {}


def _hq():
    from cairn.devices.librarian import harvest_questions
    return harvest_questions


def _cdq():
    from cairn.devices.librarian import cross_domain_questions
    return cross_domain_questions


def _turn(kind: str, day: str, text: str) -> str:
    return json.dumps({"type": kind, "timestamp": f"{day}T10:00:00Z",
                       "message": {"role": kind, "content": text}})


def _world() -> dict:
    """The fixture roots and a scratch cairn root holding a copy of the corpus. Built once."""
    if _W:
        return _W
    from cairn.tools.scratch.scratch import scratch_dir
    base = scratch_dir("harvestproof-")
    dated = base / "DATED"
    dated.mkdir()
    (dated / "20260101.Notes.txt").write_text(
        f"Some prose. {WATER} More prose.\n{FERN} {FERN}\n{HELD}\n{TWICE}\n{LONG}\n", encoding="utf-8")
    (dated / "20260102.Notes.txt").write_text(
        f"{WATER.lower()}\n{FERN}\n{HELD}\n{LONG}\n", encoding="utf-8")
    (dated / "notdated.txt").write_text(f"{CAT}\n{CAT}\n", encoding="utf-8")  # no date: not read
    proj = base / "projects" / "p"
    proj.mkdir(parents=True)
    lines = []
    for i, day in enumerate(("2026-02-01", "2026-02-02", "2026-02-03", "2026-02-04")):
        lines.append(_turn("user", day, f"hmm. {CAT}"))
        lines.append(_turn("assistant", day, f"{ASSISTANT_ONLY} {WATER}"))
        if i < 2:
            lines.append(_turn("user", day, HELD))
    lines.append(_turn("assistant", "2026-02-05", ASSISTANT_ONLY))
    lines.append(_turn("user", "2026-02-01", ASSISTANT_ONLY))
    lines.append(_turn("user", "2026-02-02", f"{TWICE}"))
    lines.append(_turn("user", "2026-02-03", f"{WATER} {FERN} {FERN} {FERN}"))
    lines.append(_turn("user", "2026-02-04", LONG))
    lines.append(json.dumps({"type": "user", "timestamp": "2026-02-05T00:00:00Z",
                             "message": {"content": [{"type": "text", "text": CAT}]}}))  # list content: skipped
    (proj / "s.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
    scratch = base / "cairnroot"
    (scratch / CORPUS_REL).parent.mkdir(parents=True)
    shutil.copy(_REPO_ROOT / CORPUS_REL, scratch / CORPUS_REL)
    commons = base / "commonsroot"
    commons.mkdir()
    _W.update(base=base, roots=[dated, base / "projects"], scratch=scratch, commons=commons,
              corpus=scratch / CORPUS_REL, proposals=base / "proposals.json")
    return _W


def _props() -> list[dict]:
    w = _world()
    return _hq().harvest(w["roots"])


def _diag(fn):
    from cairn.tools.artifact import artifact
    w = _world()
    artifact.set_diagnostic_roots({"cairn": w["scratch"], "CairnCommons": w["commons"]})
    try:
        return fn()
    finally:
        artifact.set_diagnostic_roots(None)


def test_harvest_proposes_his_recurring_questions_and_never_an_assistants():
    got = [p["text"] for p in _props()]
    assert got == [CAT, FERN, WATER], got


def test_a_question_the_corpus_holds_is_not_proposed():
    hq = _hq()
    held = {hq.normalize(q["question"]) for q in _cdq().load()["questions"]}
    assert hq.normalize(HELD) in held, "the fixture's held question is not in the corpus"
    assert all(hq.normalize(p["text"]) not in held for p in _props())


def test_proposals_are_sorted_and_carry_their_evidence():
    props = _props()
    want = [(CAT, 4, 4), (FERN, 3, 6), (WATER, 3, 3)]
    assert [(p["text"], p["days"], p["count"]) for p in props] == want, props
    assert [p["n"] for p in props] == [1, 2, 3], props
    for p in props:
        assert 1 <= len(p["sources"]) <= 5, p
        assert all(":" in s for s in p["sources"]), p
    assert len(props[1]["sources"]) == 5, props[1]


def test_two_harvests_write_the_same_bytes():
    w, hq = _world(), _hq()
    a = w["base"] / "a.json"
    b = w["base"] / "b.json"
    hq.write_proposals(hq.harvest(w["roots"]), a)
    hq.write_proposals(hq.harvest(w["roots"]), b)
    assert a.read_bytes() == b.read_bytes(), "two harvests over the same roots differ"
    hq.write_proposals(hq.harvest(w["roots"]), w["proposals"])


def test_confirm_appends_one_verbatim_entry():
    w, hq, cdq = _world(), _hq(), _cdq()
    if not w["proposals"].exists():
        hq.write_proposals(hq.harvest(w["roots"]), w["proposals"])
    before = len(cdq.load(w["corpus"])["questions"])
    entry = _diag(lambda: hq.confirm(3, function="where it goes", corpus=w["corpus"],
                                     proposals=w["proposals"]))
    doc = cdq.load(w["corpus"])
    assert len(doc["questions"]) == before + 1, (before, len(doc["questions"]))
    last = doc["questions"][-1]
    assert last == entry, (last, entry)
    assert last["question"] == WATER and last["origin"] == "verbatim" and last["said_by"] == "Akien", last
    assert last["date"] == "2026-01-01", last
    assert last["id"].startswith("Q-xd-"), last
    _W["confirmed"] = last["id"]


def test_add_appends_today_and_refuses_a_held_question():
    w, hq, cdq = _world(), _hq(), _cdq()
    before = len(cdq.load(w["corpus"])["questions"])
    new = "what is the new thing here?"
    entry = _diag(lambda: hq.add(new, corpus=w["corpus"]))
    doc = cdq.load(w["corpus"])
    assert len(doc["questions"]) == before + 1
    assert doc["questions"][-1]["question"] == new and doc["questions"][-1]["origin"] == "verbatim", entry
    assert entry["date"] == dt.date.today().isoformat(), entry
    bytes_before = w["corpus"].read_bytes()
    try:
        _diag(lambda: hq.add(HELD.upper(), corpus=w["corpus"]))
    except hq.HarvestRefused as exc:
        assert "Q-cog-013" in str(exc), exc
    else:
        raise AssertionError("a held question was added")
    assert w["corpus"].read_bytes() == bytes_before, "a refused add changed the corpus"


def test_the_corpus_write_is_journaled():
    w, hq = _world(), _hq()
    _diag(lambda: hq.add("does the journal see this one?", corpus=w["corpus"]))
    journal = w["scratch"] / ".artifact-journal.jsonl"
    assert journal.exists(), "no journal in the scratch root"
    rows = [json.loads(line) for line in journal.read_text().splitlines() if line.strip()]
    hits = [r for r in rows if r.get("path") == CORPUS_REL and r.get("verb") == "write"]
    assert hits, f"no write journaled for {CORPUS_REL}: {[(r.get('path'), r.get('verb')) for r in rows]}"


def test_the_bin_script_prints_one_line_per_proposal():
    w, hq = _world(), _hq()
    hq.write_proposals(hq.harvest(w["roots"]), w["proposals"])
    from cairn.tools.base.script_argv import bash_script_argv  # ticket dd6be87bdb7e: a shebang script is not a Windows program
    out = subprocess.run([*bash_script_argv(BIN), "proposals", "--proposals", str(w["proposals"])],
                         capture_output=True, text=True, timeout=60)
    assert out.returncode == 0, out.stderr
    lines = [ln for ln in out.stdout.splitlines() if ln.strip()]
    assert len(lines) == 3, out.stdout
    assert lines[0].split()[:2] == ["1", "4"] and lines[0].endswith(CAT), lines[0]


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
        if _W:
            shutil.rmtree(_W["base"], ignore_errors=True)
    print(f"{len(teeth) - failed}/{len(teeth)} green")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
