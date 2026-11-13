"""Proof for ticket b80c6d5637fe — a parked journal line is re-landed through the door.

Since 0f8aefbba1d0 the door parks an entry whose line git replaced under it, in
``<git dir>/cairn-orphaned-lines.jsonl``, and leaves the re-land as a later act on a settled
tree. Measured 2026-11-13: the only repair was a scratch script calling ``_entry``/``_append``
by hand. ``cairn artifact reland <root> --why`` is that act, through the door.

The world is a scratch git repo standing in for the commons root (``set_diagnostic_roots``);
a real parked entry is made the way the loss happens: a stash landing mid-append, then the pop.
No live repo and no live journal are touched.

  1. a parked entry whose record stands at its sha_after and whose sha_before is the journal's
     last for its path is appended once, chained, verify_chain clean, check_staged passing for
     the record, and the park emptied;
  2. a parked entry whose record moved on, or whose sha_before is not the journal's last for
     its path, stays parked and is named, the journal is unchanged, and the verb exits 1;
  3. reland over an empty park, or over a parked entry already landed, appends nothing and
     leaves the park empty.

    python3 cairn/tools/artifact/proofs/test_a_parked_line_is_relanded_through_the_door.py   # exit 0 = green
"""
from __future__ import annotations

import contextlib
import io
import json
import os
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {
    "b80c6d5637fe": {"1": "test_a_parked_line_lands_once_chained",
                     "2": "test_a_line_over_moved_bytes_stays_parked",
                     "3": "test_a_second_reland_appends_nothing"},
}

_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/bin/false", SSH_ASKPASS="/bin/false")
_ROOT = "CairnCommons"


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True, env=_ENV).stdout


def _doc(n: int) -> str:
    return json.dumps({"n": n}, indent=2) + "\n"


def _tmp():
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("cairn-b80c-")


class _MidAppend:
    """Shadow ``_entry_sha``: its first call, inside ``_append`` after the handle is checked and
    before the line is written, runs ``act`` first — the measured window."""

    def __init__(self, A, act):
        self.A, self.act, self.fired, self.real = A, act, False, A._entry_sha

    def __call__(self, entry):
        if not self.fired:
            self.fired = True
            self.act()
        return self.real(entry)

    def __enter__(self):
        self.A._entry_sha = self
        return self

    def __exit__(self, *exc):
        self.A._entry_sha = self.real


@contextlib.contextmanager
def _parked_world():
    """A scratch commons with one real parked entry for ideas/a.json, the tree settled."""
    from cairn.tools.artifact import artifact as A
    with _tmp() as t:
        tmp = Path(t)
        root = tmp / "commons"
        (root / "ideas").mkdir(parents=True)
        _git(root, "init", "-q", "-b", "main")
        _git(root, "config", "user.email", "proof@example.invalid")
        _git(root, "config", "user.name", "proof")
        A.set_diagnostic_roots({_ROOT: root, "parked": tmp / "parked"})
        try:
            A.write(root / "ideas" / "a.json", _doc(0), verb="cast", why="base a")
            A.write(root / "ideas" / "b.json", _doc(0), verb="cast", why="base b")
            _git(root, "add", "-A")
            _git(root, "commit", "-qm", "base")
            A.write(root / "ideas" / "b.json", _doc(1), verb="cast", why="uncommitted, as live always is")
            raised = None
            with _MidAppend(A, lambda: _git(root, "stash", "push", "-q")):
                try:
                    A.write(root / "ideas" / "a.json", _doc(8), verb="cast", why="the lost write")
                except A.JournalLineOrphaned as exc:
                    raised = exc
            assert raised is not None, "the world could not park an entry: the door did not raise"
            _git(root, "stash", "pop", "-q")
            parked = _park_lines(A, root)
            assert len(parked) == 1, f"the world parked {len(parked)} entries, not 1"
            yield A, root, parked[0]
        finally:
            A.set_diagnostic_roots(None)


def _park_lines(A, root: Path) -> list[dict]:
    park = A.orphan_park(root)
    if not park.exists():
        return []
    return [json.loads(x) for x in park.read_text(encoding="utf-8").splitlines() if x.strip()]


def _cli(*argv: str) -> tuple[int, str]:
    from cairn.tools.artifact.__main__ import main
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        rc = main(list(argv))
    return rc, out.getvalue() + err.getvalue()


def test_a_parked_line_lands_once_chained():
    with _parked_world() as (A, root, lost):
        assert hasattr(A, "reland"), "the door has no reland: a parked line cannot be re-landed"
        before = A.read_journal(root)
        rc, text = _cli("reland", _ROOT, "--why", "re-land the line the stash took")
        assert rc == 0, f"reland exited {rc}: {text}"
        after = A.read_journal(root)
        assert len(after) == len(before) + 1, f"{len(after) - len(before)} lines appended, not 1"
        assert after[:-1] == before, "the prior lines changed"
        line = after[-1]
        assert line["prev"] == before[-1]["entry"], "the line is not chained on the journal's tail"
        assert line["relanded_from"] == lost["entry"], "the line does not name the entry it re-lands"
        assert line["relanded_why"] == "re-land the line the stash took"
        assert line["why"] == lost["why"] and line["caller"] == lost["caller"], \
            "the line lost the original writer's why or caller"
        assert line["path"] == "ideas/a.json" and line["sha_after"] == lost["sha_after"]
        assert "relanded_by" in line, "the line does not say who re-landed it"
        assert A.verify_chain(root) == [], f"chain faults: {A.verify_chain(root)}"
        _git(root, "add", "ideas/a.json")
        faults = A.check_staged(_ROOT)
        assert faults == [], f"the record still fails the commit check: {faults}"
        assert _park_lines(A, root) == [], "the park still holds the re-landed entry"


def test_a_line_over_moved_bytes_stays_parked():
    faults = []
    for shape, move in (
        ("written again through the door",
         lambda A, root: A.write(root / "ideas" / "a.json", _doc(9), verb="cast", why="moved on")),
        ("overwritten around the door",
         lambda A, root: (root / "ideas" / "a.json").write_text(_doc(10), encoding="utf-8")),
    ):
        try:
            with _parked_world() as (A, root, lost):
                assert hasattr(A, "reland"), "the door has no reland"
                move(A, root)
                before = A.read_journal(root)
                rc, text = _cli("reland", _ROOT, "--why", "try to re-land over moved bytes")
                assert rc == 1, f"reland exited {rc}, not 1: {text}"
                assert lost["entry"] in text, "the kept entry is not named"
                assert A.read_journal(root) == before, "the journal changed"
                kept = _park_lines(A, root)
                assert [e["entry"] for e in kept] == [lost["entry"]], f"the park holds {kept}"
        except Exception as exc:
            faults.append(f"{shape}: {type(exc).__name__}: {exc}")
    assert not faults, "\n".join(faults)


def test_a_second_reland_appends_nothing():
    with _parked_world() as (A, root, lost):
        assert hasattr(A, "reland"), "the door has no reland"
        first = A.reland(_ROOT, why="the first re-land")
        assert len(first["relanded"]) == 1, f"the first reland: {first}"
        n = len(A.read_journal(root))
        second = A.reland(_ROOT, why="again, over an empty park")
        assert second == {"relanded": [], "dropped": [], "kept": []}, f"the second reland: {second}"
        assert len(A.read_journal(root)) == n, "a reland over an empty park appended"
        # the same entry parked again (a copy of the park line): it already stands, so it is dropped
        with open(A.orphan_park(root), "a", encoding="utf-8") as ph:
            ph.write(json.dumps(lost, ensure_ascii=False, sort_keys=True) + "\n")
        third = A.reland(_ROOT, why="over an entry already landed")
        assert third["relanded"] == [] and third["dropped"] == [lost["entry"]], f"the third: {third}"
        assert len(A.read_journal(root)) == n, "a reland over a landed entry appended"
        assert _park_lines(A, root) == [], "the park was not emptied"
        assert A.verify_chain(root) == []


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
