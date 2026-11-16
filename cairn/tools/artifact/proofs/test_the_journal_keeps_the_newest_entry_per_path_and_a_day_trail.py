"""Proof for ticket b15da5656579: the journal keeps the newest entry per path in the repo, and
every entry goes to a day trail under the logs root.

Akien, 2026-11-16: "the latest entry remains in cairn commons, and everything else broken
into... per day? per week? inside of our .cairn/logs folder". The orchestrator chose per day.
Measured the same day: the commons journal was 55 MB over 43908 entries and 8891 paths.

  1. writes to two paths, one of them three times: the index holds two lines, each its path's
     newest entry, the last line the newest write; today's trail file holds all four entries;
  2. verify_journal is clean over a clean index, names a line whose body was edited, and names a
     path with two lines; check_staged refuses while a fault stands;
  3. on the index, check_staged refuses bytes that are not the newest sha_after, park_hand_edit
     restores the newest journaled bytes, and genesis journals only never-journaled paths, so a
     hand-edited journaled record stays refused;
  4. the merge keeps one line per path, the newer at winning and a tie going to the larger entry
     sha, the same bytes in either order; a chained side with many lines per path merges to its
     newest;
  5. no line leaves the index without standing in the trail: a write over a chained journal puts
     the path's older lines in their own day files first, once; a diagnostic world with no
     "trail" key writes beside its root, never to the live logs;
  6. migrate writes every chained line to the day file of its at, sets a past day's mtime to the
     end of that day, and writes the newest-per-path index; a second run changes nothing;
  7. read_trail is exported by the package, and the callers_are_known probe counts the trail.

Every clause runs in a scratch git repo standing in for the commons root (set_diagnostic_roots).
No live repo, journal or log is touched; clause 5 reads the live trail address, read-only.

Run bare:  PYTHONPATH=. python3 cairn/tools/artifact/proofs/test_the_journal_keeps_the_newest_entry_per_path_and_a_day_trail.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {
    "b15da5656579": {
        "1": "test_the_index_keeps_the_newest_and_the_trail_keeps_every_entry",
        "2": "test_verify_journal_names_an_edited_line_and_a_doubled_path",
        "3": "test_the_commit_park_and_genesis_read_the_newest_entry",
        "4": "test_the_merge_keeps_the_newer_entry_per_path_in_either_order",
        "5": "test_no_line_leaves_the_index_without_standing_in_the_trail",
        "6": "test_migrate_files_every_line_by_its_day_and_runs_once",
        "7": "test_read_trail_is_public_and_the_caller_probe_counts_it",
    },
}

_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/bin/false", SSH_ASKPASS="/bin/false")
TODAY = datetime.now(timezone.utc).date().isoformat()


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True, env=_ENV).stdout


def _doc(n: int) -> str:
    return json.dumps({"n": n}, indent=2) + "\n"


def _tmp():
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("cairn-b15d-")


def _world(tmp: Path, *, trail: bool = True):
    from cairn.tools.artifact import artifact as A
    root = tmp / "CairnCommons"
    (root / "ideas").mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "proof@example.invalid")
    _git(root, "config", "user.name", "proof")
    world = {"CairnCommons": root, "parked": tmp / "parked"}
    if trail:
        world["trail"] = tmp / "trail"
    A.set_diagnostic_roots(world)
    return A, root


def _lines(root: Path) -> list[dict]:
    jp = root / ".artifact-journal.jsonl"
    return [json.loads(x) for x in jp.read_text(encoding="utf-8").splitlines() if x.strip()]


def _day_file(tmp: Path, day: str) -> Path:
    return tmp / "trail" / "CairnCommons" / f"{day}.jsonl"


def _day_lines(f: Path) -> list[dict]:
    if not f.exists():
        return []
    return [json.loads(x) for x in f.read_text(encoding="utf-8").splitlines() if x.strip()]


def _chained(A, rows: list[tuple[str, str, str]]) -> list[dict]:
    """Old-format entries (path, at, why), chained by prev the way the journal was until b15d."""
    out, prev = [], "genesis"
    for path, at, why in rows:
        e = {"at": at, "path": path, "verb": "cast", "why": why, "count": 1,
             "sha_before": "absent", "sha_after": A._sha(why.encode()),
             "caller": {"class": "cc"}, "stack": [], "prev": prev}
        e["entry"] = A._entry_sha(e)
        prev = e["entry"]
        out.append(e)
    return out


def _put_journal(root: Path, entries: list[dict]) -> None:
    (root / ".artifact-journal.jsonl").write_text(
        "".join(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n" for e in entries),
        encoding="utf-8")


def _ago(days: int) -> str:
    return (datetime.now(timezone.utc) - timedelta(days=days)).replace(microsecond=0).isoformat()


def test_the_index_keeps_the_newest_and_the_trail_keeps_every_entry():
    with _tmp() as t:
        A, root = _world(Path(t))
        try:
            wrote = [A.write(root / "ideas" / "a.json", _doc(1), verb="cast", why="a1")["entry"],
                     A.write(root / "ideas" / "a.json", _doc(2), verb="cast", why="a2")["entry"],
                     A.write(root / "ideas" / "b.json", _doc(1), verb="cast", why="b1")["entry"],
                     A.write(root / "ideas" / "a.json", _doc(3), verb="cast", why="a3")["entry"]]
            idx = _lines(root)
            assert [e["path"] for e in idx] == ["ideas/b.json", "ideas/a.json"], \
                f"the index holds {[e['path'] for e in idx]}, not one line per path in write order"
            assert idx == [wrote[2], wrote[3]], "an index line is not its path's newest entry"
            assert all("prev" not in e for e in idx), "a new entry still carries prev"
            day = _day_lines(_day_file(Path(t), TODAY))
            assert day == wrote, f"today's trail holds {len(day)} entries, not the 4 written verbatim"
            assert A.read_trail(root) == wrote, "read_trail does not return every entry in order"
        finally:
            A.set_diagnostic_roots(None)


def test_verify_journal_names_an_edited_line_and_a_doubled_path():
    with _tmp() as t:
        A, root = _world(Path(t))
        try:
            A.write(root / "ideas" / "a.json", _doc(1), verb="cast", why="a1")
            A.write(root / "ideas" / "b.json", _doc(1), verb="cast", why="b1")
            assert A.verify_journal(root) == [], f"a clean index faults: {A.verify_journal(root)}"
            jp = root / ".artifact-journal.jsonl"
            clean = jp.read_text(encoding="utf-8")
            jp.write_text(clean.replace('"why": "a1"', '"why": "a!"'), encoding="utf-8")
            faults = A.verify_journal(root)
            assert any("ideas/a.json" in f and "line 1" in f for f in faults), \
                f"an edited body is not named by line and path: {faults}"
            _git(root, "add", "ideas/a.json")
            assert any("ideas/a.json" in f for f in A.check_staged("CairnCommons")), \
                "check_staged passed over an edited journal line"
            first = clean.splitlines()[0]
            jp.write_text(clean + first + "\n", encoding="utf-8")
            faults = A.verify_journal(root)
            assert any("ideas/a.json" in f and "2 lines" in f for f in faults), \
                f"a path with two lines is not named: {faults}"
            assert A.check_staged("CairnCommons"), "check_staged passed over a doubled path"
        finally:
            A.set_diagnostic_roots(None)


def test_the_commit_park_and_genesis_read_the_newest_entry():
    with _tmp() as t:
        A, root = _world(Path(t))
        try:
            a = root / "ideas" / "a.json"
            A.write(a, _doc(1), verb="cast", why="a1")
            A.write(a, _doc(2), verb="cast", why="a2")
            _git(root, "add", "-A")
            assert A.check_staged("CairnCommons") == [], "the door's own bytes were refused"
            _git(root, "commit", "-qm", "base")
            a.write_text(_doc(9), encoding="utf-8")                 # around the door
            _git(root, "add", "ideas/a.json")
            refused = A.check_staged("CairnCommons")
            assert any("ideas/a.json" in f and "changed around the door" in f for f in refused), \
                f"a hand edit over the newest entry was not refused: {refused}"
            (root / "ideas" / "new.json").write_text(_doc(0), encoding="utf-8")
            out = A.genesis("CairnCommons", why="genesis over the index")
            assert out["journaled"] == 1, f"genesis journaled {out['journaled']}, not only the newcomer"
            assert [e["path"] for e in _lines(root)].count("ideas/a.json") == 1
            assert any("ideas/a.json" in f for f in A.check_staged("CairnCommons")), \
                "genesis blessed a hand-edited journaled record"
            _git(root, "reset", "-q")
            A.park_hand_edit(a, why="the proof parks the hand edit")
            assert a.read_text(encoding="utf-8") == _doc(2), "the park did not restore the newest bytes"
        finally:
            A.set_diagnostic_roots(None)


def test_the_merge_keeps_the_newer_entry_per_path_in_either_order():
    from cairn.tools.artifact import artifact as A

    def entry(path, at, why):
        e = {"at": at, "path": path, "verb": "cast", "why": why, "count": 1, "sha_before": "absent",
             "sha_after": A._sha(why.encode()), "caller": {"class": "cc"}, "stack": []}
        e["entry"] = A._entry_sha(e)
        return e

    def blob(entries):
        return "".join(json.dumps(e, sort_keys=True) + "\n" for e in entries).encode()

    t0, t1, t2 = "2026-11-16T10:00:00+00:00", "2026-11-16T11:00:00+00:00", "2026-11-16T12:00:00+00:00"
    ours = [entry("ideas/a.json", t1, "ours a"), entry("ideas/b.json", t0, "ours b"),
            entry("ideas/t.json", t2, "tie one")]
    theirs = [entry("ideas/a.json", t2, "theirs a"), entry("ideas/b.json", t0, "ours b"),
              entry("ideas/c.json", t0, "theirs c"), entry("ideas/t.json", t2, "tie two")]
    one, two = A.merge_journals(blob(ours), blob(theirs)), A.merge_journals(blob(theirs), blob(ours))
    assert one == two, "the merge is not the same bytes in either order"
    got = {e["path"]: e for e in (json.loads(x) for x in one.decode().splitlines())}
    assert len(one.decode().splitlines()) == 4 == len(got), "the merge does not keep one line per path"
    assert got["ideas/a.json"]["why"] == "theirs a", "the older entry won"
    tie = max(ours[2], theirs[3], key=lambda e: e["entry"])
    assert got["ideas/t.json"] == tie, "a tie did not go to the larger entry sha"
    chained = _chained(A, [("ideas/a.json", t0, "c1"), ("ideas/b.json", t0, "c2"),
                           ("ideas/a.json", t1, "c3")])
    merged = [json.loads(x) for x in A.merge_journals(blob(chained), b"").decode().splitlines()]
    assert [e["why"] for e in merged] == ["c2", "c3"], f"a chained side merged to {merged}"


def test_no_line_leaves_the_index_without_standing_in_the_trail():
    with _tmp() as t:
        A, root = _world(Path(t))
        try:
            old, mid = _ago(40)[:10], _ago(2)[:10]
            chained = _chained(A, [("ideas/a.json", _ago(40), "a old"), ("ideas/b.json", _ago(40), "b old"),
                                   ("ideas/a.json", _ago(2), "a mid")])
            _put_journal(root, chained)
            A.write(root / "ideas" / "a.json", _doc(5), verb="cast", why="a now")
            assert _day_lines(_day_file(Path(t), old)) == [chained[0]], "the oldest a line left without a trail"
            assert _day_lines(_day_file(Path(t), mid)) == [chained[2]], "the middle a line left without a trail"
            assert [e["path"] for e in _lines(root)] == ["ideas/b.json", "ideas/a.json"]
            A.write(root / "ideas" / "a.json", _doc(6), verb="cast", why="a again")
            assert len(_day_lines(_day_file(Path(t), old))) == 1, "a line went to the trail twice"
        finally:
            A.set_diagnostic_roots(None)
    from cairn.tools.artifact import artifact as A
    live = A.trail_dir("CairnCommons")
    seen = {f: f.stat().st_size for f in live.glob("*.jsonl")} if live.is_dir() else {}
    with _tmp() as t:
        A, root = _world(Path(t), trail=False)
        try:
            assert A.trail_dir("CairnCommons") != live, "a diagnostic world resolves the live trail"
            A.write(root / "ideas" / "a.json", _doc(1), verb="cast", why="scratch")
            assert Path(t) in A.trail_dir("CairnCommons").parents, "the scratch trail is not beside its root"
        finally:
            A.set_diagnostic_roots(None)
    now = {f: f.stat().st_size for f in live.glob("*.jsonl")} if live.is_dir() else {}
    assert all(now.get(f) == n for f, n in seen.items()), "a scratch write reached the live trail"


def test_migrate_files_every_line_by_its_day_and_runs_once():
    with _tmp() as t:
        A, root = _world(Path(t))
        try:
            rows = [("ideas/a.json", _ago(40), "a1"), ("ideas/b.json", _ago(40), "b1"),
                    ("ideas/a.json", _ago(3), "a2"), ("ideas/c.json", _ago(0), "c1")]
            chained = _chained(A, rows)
            _put_journal(root, chained)
            out = A.migrate("CairnCommons", why="the proof migrates a chained journal")
            days = sorted({r[1][:10] for r in rows})
            filed = [e for d in days for e in _day_lines(_day_file(Path(t), d))]
            assert sorted(e["entry"] for e in filed) == sorted(e["entry"] for e in chained), \
                "the trail does not hold every chained line exactly once"
            assert all(e["at"][:10] == f.stem for f in _day_file(Path(t), days[0]).parent.glob("*.jsonl")
                       for e in _day_lines(f)), "a line is filed under another day"
            end = datetime.fromisoformat(days[0] + "T23:59:59+00:00").timestamp()
            assert _day_file(Path(t), days[0]).stat().st_mtime <= end + 1, \
                "a past day's mtime is not the end of its day, so the sweep cannot age it"
            assert [e["why"] for e in _lines(root)] == ["b1", "a2", "c1"], \
                f"the index is not newest per path in write order: {[e['why'] for e in _lines(root)]}"
            assert A.verify_journal(root) == [], f"the migrated index faults: {A.verify_journal(root)}"
            assert out.get("entries") == 4 and out.get("paths") == 3, f"migrate reported {out}"
            before = (root / ".artifact-journal.jsonl").read_bytes()
            counts = {d: len(_day_lines(_day_file(Path(t), d))) for d in days}
            A.migrate("CairnCommons", why="a second run")
            assert (root / ".artifact-journal.jsonl").read_bytes() == before, "a second run moved the index"
            assert {d: len(_day_lines(_day_file(Path(t), d))) for d in days} == counts, \
                "a second run added trail lines"
        finally:
            A.set_diagnostic_roots(None)


def test_read_trail_is_public_and_the_caller_probe_counts_it():
    import cairn.tools.artifact as pkg
    assert getattr(pkg, "read_trail", None) is not None, "read_trail is not exported by the package"
    assert getattr(pkg, "verify_journal", None) is not None, "verify_journal is not exported by the package"
    from cairn.tools.artifact.probes import callers_are_known as probe
    with _tmp() as t:
        A, root = _world(Path(t))
        try:
            for n in range(3):
                A.write(root / "ideas" / "a.json", _doc(n), verb="cast", why=f"w{n}")
            ctx = probe._measure({})
            assert ctx["writes"] == 3, f"the probe counted {ctx['writes']} writes, not the trail's 3"
        finally:
            A.set_diagnostic_roots(None)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
