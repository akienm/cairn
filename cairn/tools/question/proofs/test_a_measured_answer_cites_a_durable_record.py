#!/usr/bin/env python3
"""Proof for ticket bec37ac3ae5d: a measured answer cites a durable record by its dataref address.

Measured 2026-11-21: 34 of 319 measured answers under CairnCommons/questions/ cited a record
outside this box's durable roots, and 32 of them no longer resolved here (worktrees cleared at
their land, /tmp scratchpads, another box's home). The answer door now refuses a --measured
record inside no durable root and records an accepted one as its outline 17.28.1.1 address.

  (1) over a scratch world whose door root is a LINKED git worktree, a record inside that
      worktree is refused, the refusal naming the path and the main checkout (never the
      worktree) as a root, and the question file's bytes are unchanged;
  (2) a record in a scratch dir outside every durable root is refused the same way;
  (3) a record under the durable commons is accepted: measured reads
      'cairncommons:///<path>', answered_by starts 'measurement: cairncommons:///', and
      Dataref over the address is that record;
  (4) open-2921d9c2dbb8 and open-a9795e2009c1 (LIVE records, read only) record measured as
      'cairn:///cairn/devices/cairn/requirements/<file>.md', resolving to a file on the main
      checkout.

The subject is imported inside each tooth, so a hollow build reds per tooth.

    bin/cairn test cairn/tools/question/proofs/test_a_measured_answer_cites_a_durable_record.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"bec37ac3ae5d": {"1": "test_a_record_inside_a_linked_worktree_is_refused",
                           "2": "test_a_record_in_a_scratch_dir_is_refused",
                           "3": "test_a_commons_record_is_recorded_by_its_dataref_address",
                           "4": "test_the_two_named_answers_cite_the_main_checkout"}}

TICKET = "bec37ac3ae5d"
LIVE = {"open-2921d9c2dbb8": "cairn:///cairn/devices/cairn/requirements/17-tools.md",
        "open-a9795e2009c1": "cairn:///cairn/devices/cairn/requirements/00-how-to-read-this.md"}
_WORLD: dict = {}


def _git(cwd: Path, *args: str) -> None:
    env = dict(os.environ, GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=os.devnull,
               GIT_TERMINAL_PROMPT="0")
    subprocess.run(["git", "-c", "user.name=testing-bec3", "-c", "user.email=testing@bec3.invalid",
                    "-c", "init.defaultBranch=main", *args],
                   cwd=cwd, env=env, check=True, capture_output=True, timeout=60)


def _world() -> dict:
    """tmp/cairn (a git repo, one commit), tmp/wt/cairn (a linked worktree of it, the door's
    'cairn' root), tmp/CairnCommons (the door's commons, the main checkout's sibling)."""
    if _WORLD:
        return _WORLD
    from cairn.tools.artifact import artifact as A
    from cairn.tools.scratch.scratch import scratch_dir
    tmp = scratch_dir("cairn-bec3-world-")
    main = tmp / "cairn"
    main.mkdir()
    _git(main, "init", "-q")
    (main / "README").write_text("scratch main checkout\n")
    _git(main, "add", "README")
    _git(main, "commit", "-q", "-m", "testing-bec3 first commit")
    _git(main, "worktree", "add", "-q", "-b", "testing-bec3-wt", str(tmp / "wt" / "cairn"))
    commons = tmp / "CairnCommons"
    (commons / "questions").mkdir(parents=True)
    (commons / "tickets").mkdir()
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "wt" / "cairn",
                            "parked": tmp / "parked"})
    _WORLD.update(tmp=tmp, main=main, wt=tmp / "wt" / "cairn", commons=commons,
                  qdir=commons / "questions")
    return _WORLD


def _refused(record: Path) -> tuple:
    from cairn.tools.question import question as Q
    w = _world()
    q = Q.open_question(TICKET, f"does {record.name} settle this?", "the proof's own question",
                        root=w["qdir"])
    qpath = w["qdir"] / f"{q['id']}.json"
    before = qpath.read_bytes()
    try:
        Q.answer(q["id"], "it reads clean", spawned=[], measured=str(record), root=w["qdir"])
    except Q.Refused as exc:
        return str(exc), qpath.read_bytes() == before
    return None, qpath.read_bytes() == before


def test_a_record_inside_a_linked_worktree_is_refused() -> None:
    from cairn.tools.question import question as Q
    w = _world()
    assert Q.durable_roots()["cairn"] == w["main"].resolve(), Q.durable_roots()
    record = w["wt"] / "measured_in_the_worktree.json"
    record.write_text('{"clean": true}\n')
    why, unchanged = _refused(record)
    assert why is not None, "a worktree record was accepted"
    assert str(record) in why and f"cairn:/// = {w['main'].resolve()}" in why, why
    assert f"= {w['wt'].resolve()}," not in why and not why.endswith(str(w["wt"].resolve())), why
    assert unchanged, "the refused answer wrote the question file"


def test_a_record_in_a_scratch_dir_is_refused() -> None:
    from cairn.tools.scratch.scratch import scratch_dir
    _world()
    record = scratch_dir("cairn-bec3-elsewhere-") / "measured_in_scratch.json"
    record.write_text('{"clean": true}\n')
    why, unchanged = _refused(record)
    assert why is not None and "inside no durable root" in why and str(record) in why, why
    assert unchanged, "the refused answer wrote the question file"


def test_a_commons_record_is_recorded_by_its_dataref_address() -> None:
    from cairn.tools.dataref.dataref import Dataref
    from cairn.tools.question import question as Q
    w = _world()
    record = w["commons"] / "measured" / "in_the_commons.json"
    record.parent.mkdir(exist_ok=True)
    record.write_text('{"clean": true}\n')
    q = Q.open_question(TICKET, "does a commons record settle this?", "the proof's own question",
                        root=w["qdir"])
    ans = Q.answer(q["id"], "it reads clean", spawned=[], measured=str(record), root=w["qdir"])
    want = "cairncommons:///measured/in_the_commons.json"
    assert ans["measured"] == want, ans
    assert ans["answered_by"].startswith("measurement: " + want), ans["answered_by"]
    back = json.loads((w["qdir"] / f"{q['id']}.json").read_text())
    assert back["measured"] == want and back["resolved"] is True, back
    got = Dataref(want, roots={"commons": w["commons"]}).path
    assert got.resolve() == record.resolve(), got


def test_the_two_named_answers_cite_the_main_checkout() -> None:
    """Reads LIVE records (the two answers this ticket repoints); writes nothing."""
    from cairn.tools.artifact import artifact as A
    from cairn.tools.dataref.dataref import Dataref
    from cairn.tools.question import question as Q
    A.set_diagnostic_roots(None)
    dr = Q.durable_roots()
    for qid, want in LIVE.items():
        rec = json.loads((dr["cairncommons"] / "questions" / f"{qid}.json").read_text())
        assert rec.get("measured") == want, (qid, rec.get("measured"))
        assert want in (rec.get("answered_by") or ""), (qid, rec.get("answered_by"))
        path = Dataref(want, roots={"repo": dr["cairn"]}).path
        assert path.is_file(), (qid, path)


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
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all 4 teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
