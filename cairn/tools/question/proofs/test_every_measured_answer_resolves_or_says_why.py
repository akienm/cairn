#!/usr/bin/env python3
"""Proof for ticket cdfc928cc5ff: every measured answer resolves inside a durable root, or says why
it resolves nowhere.

Measured 2026-11-21: of 325 answered questions with ``measured`` set, 2 cited their record by a
dataref address (outline 17.28.1.1); 123 named it by a box-local absolute path, 106 by a path that
no longer exists (a cleared worktree, a Windows checkout, the old house path) though the record
lives on in a durable root, and 94 cited a record that is gone (the retired outline file, a session
scratchpad, runtime state). The backfill reads each and repoints it or marks it.

  (1) every answered question under the commons whose measured is set either resolves through
      Dataref (a cairn:///, cairncommons:/// or instance:/// address) to a file inside
      question.durable_roots(), or carries a non-empty measured_resolves_nowhere;
  (2) every answer whose measured is a dataref address resolves through Dataref to a file, and
      its answered_by names that address;
  (3) the scanner, over a scratch questions dir, reds a planted answer citing a missing path with
      no mark and one whose dataref measured names a missing file, and passes a marked one.

Teeth (1) and (2) READ LIVE DATA, read only; they write nothing. They enumerate the records from the
commons the artifact door names (door.roots()["CairnCommons"]): in the hollow's worktree that is the
worktree's commons, where a reverted record stands. durable_roots() follows a linked worktree to the
house checkout (bec37ac3ae5d), so it stays the resolver for an ADDRESS (where a cited file must live)
and never the enumerator (measured 2026-11-21: enumerating by it, the hollow read 323 of 323 reverts
as hollow). The subject (question.durable_roots) is imported inside each tooth, so a hollow build reds
per tooth.

    bin/cairn test cairn/tools/question/proofs/test_every_measured_answer_resolves_or_says_why.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"cdfc928cc5ff": {"1": "test_every_live_measured_answer_resolves_or_is_marked",
                           "2": "test_every_live_address_resolves_and_answered_by_names_it",
                           "3": "test_the_scanner_reds_the_planted_dangling_answers"}}

SCHEMES = ("cairn:///", "cairncommons:///", "instance:///")


def _dataref_roots(dr: dict) -> dict:
    return {"repo": dr["cairn"], "commons": dr["cairncommons"], "instance": dr["instance"]}


def scan(qdir: Path, dr: dict) -> dict:
    """``{"unresolved": [...], "unnamed": [...], "read": n}`` over every answered record in ``qdir``
    whose measured is set. unresolved: neither an address resolving to a file inside a durable root
    nor marked. unnamed: an address whose answered_by does not name it."""
    from cairn.tools.dataref.dataref import Dataref, DatarefMiss
    roots = [Path(p).resolve() for p in dr.values()]
    out = {"unresolved": [], "unnamed": [], "read": 0}
    for f in sorted(Path(qdir).glob("open-*.json")):
        rec = json.loads(f.read_text(encoding="utf-8"))
        m = rec.get("measured")
        if not (rec.get("resolved") and m):
            continue
        out["read"] += 1
        mark = rec.get("measured_resolves_nowhere")
        if isinstance(m, str) and m.startswith(SCHEMES):
            try:
                path = Dataref(m, roots=_dataref_roots(dr)).path
            except DatarefMiss:
                path = None
            inside = path is not None and any(path.resolve().is_relative_to(r) for r in roots)
            if not (inside and path.is_file()):
                out["unresolved"].append((rec["id"], m))
            if m not in (rec.get("answered_by") or ""):
                out["unnamed"].append((rec["id"], m))
        elif not (isinstance(mark, str) and mark.strip()):
            out["unresolved"].append((rec["id"], m))
    return out


def _records() -> Path:
    """The questions dir of the commons the artifact door writes: the records the build wrote."""
    from cairn.tools.artifact import artifact as A
    A.set_diagnostic_roots(None)
    return Path(A.roots()["CairnCommons"]) / "questions"


def _live() -> dict:
    from cairn.tools.question import question as Q
    qdir = _records()
    return scan(qdir, Q.durable_roots())


def test_every_live_measured_answer_resolves_or_is_marked() -> None:
    got = _live()
    assert got["read"] > 300, got["read"]
    assert not got["unresolved"], f"{len(got['unresolved'])} of {got['read']}: {got['unresolved'][:5]}"


def test_every_live_address_resolves_and_answered_by_names_it() -> None:
    got = _live()
    addressed = sum(1 for f in _records().glob("open-*.json")
                    if str(json.loads(f.read_text(encoding="utf-8")).get("measured") or "").startswith(SCHEMES))
    assert addressed > 200, addressed
    assert not got["unnamed"], f"{len(got['unnamed'])}: {got['unnamed'][:5]}"
    assert not [u for u in got["unresolved"] if u[1].startswith(SCHEMES)], got["unresolved"][:5]


def test_the_scanner_reds_the_planted_dangling_answers() -> None:
    from cairn.tools.question import question as Q
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("cairn-cdfc-scan-")
    dr = {"cairn": tmp / "cairn", "cairncommons": tmp / "CairnCommons", "instance": tmp / "instance"}
    for p in dr.values():
        p.mkdir(parents=True)
    assert callable(Q.durable_roots)
    (dr["cairncommons"] / "tickets").mkdir()
    (dr["cairncommons"] / "tickets" / "real.json").write_text("{}\n")
    qdir = dr["cairncommons"] / "questions"
    qdir.mkdir()

    def plant(qid: str, measured: str, **extra) -> None:
        by = f"measurement: {measured}, recorded by caller class cc"
        (qdir / f"{qid}.json").write_text(json.dumps(
            {"id": qid, "resolved": True, "answer": "planted", "answered_by": by,
             "measured": measured, **extra}) + "\n")

    plant("open-000000000001", str(tmp / "gone" / "record.json"))
    plant("open-000000000002", "cairncommons:///tickets/missing.json")
    plant("open-000000000003", str(tmp / "gone" / "record.json"),
          measured_resolves_nowhere="the planted record was never written")
    plant("open-000000000004", "cairncommons:///tickets/real.json")
    got = scan(qdir, dr)
    assert got["read"] == 4, got
    ids = sorted(i for i, _ in got["unresolved"])
    assert ids == ["open-000000000001", "open-000000000002"], got
    assert not got["unnamed"], got


def _main() -> int:
    from cairn.tools.artifact import artifact as A
    failed = []
    try:
        for name in [n for keys in PROVES.values() for n in keys.values()]:
            try:
                globals()[name]()
                print(f"  PASS  {name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
                print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
                failed.append(name)
    finally:
        A.set_diagnostic_roots(None)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all 3 teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
