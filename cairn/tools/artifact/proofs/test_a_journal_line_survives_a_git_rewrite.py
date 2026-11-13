"""Proof for ticket 0f8aefbba1d0 — a git rewrite never drops a journal line silently.

Measured 2026-11-13: f695fac922cd's PROVEME cursor write kept its bytes but lost its journal
line inside a batch's ``pull --rebase --autostash``. The autostash replaced the journal file
under ``_append``'s open handle, so the line went to the orphaned file and the record rode the
stash back. Re-landing the line in the file at the path mid-stash makes the pop refuse
(measured too), so the door holds a lock that git rewrites can share (``cairn artifact quiet``),
and it parks the entry and raises when a rewrite ignores that lock.

The world is a scratch git repo standing in for the commons root (``set_diagnostic_roots``).
No live repo and no live journal are touched.

  1. a git rewrite run under quiet cannot interleave with a door write; a rewrite that ignores
     it makes the door raise and park the entry, never drop it. Three shapes:
     (a) ``quiet -- stash; sleep; pop`` holds the lock while a door write starts: the write
         lands after the pop, the record has its bytes, the line stands once, the chain is
         clean, and no stash is left;
     (b) a stash landing mid-append, ignoring the lock: the door raises
         JournalLineOrphaned and the entry stands in the park file, its sha_after the record's;
     (c) a file replaced at the path between open and lock: the line lands in the file at the
         path, once, and the chain is clean;
  2. an append with no rewrite writes exactly one line, chained on the prior tail.

    python3 cairn/tools/artifact/proofs/test_a_journal_line_survives_a_git_rewrite.py   # exit 0 = green
"""
from __future__ import annotations

import builtins
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {
    "0f8aefbba1d0": {"1": "test_a_rewrite_cannot_drop_a_line",
                     "2": "test_an_undisturbed_append_writes_one_chained_line"},
}

_REPO = Path(__file__).resolve().parents[4]
_ENV = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_ASKPASS="/bin/false", SSH_ASKPASS="/bin/false")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True, env=_ENV).stdout


def _doc(n: int) -> str:
    return json.dumps({"n": n}, indent=2) + "\n"


def _world(tmp: Path):
    from cairn.tools.artifact import artifact as A
    root = tmp / "commons"
    (root / "ideas").mkdir(parents=True)
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "proof@example.invalid")
    _git(root, "config", "user.name", "proof")
    A.set_diagnostic_roots({"CairnCommons": root, "parked": tmp / "parked"})
    A.write(root / "ideas" / "a.json", _doc(0), verb="cast", why="base a")
    A.write(root / "ideas" / "b.json", _doc(0), verb="cast", why="base b")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "base")
    A.write(root / "ideas" / "b.json", _doc(1), verb="cast", why="uncommitted, as live always is")
    return A, root


def _lines(A, root: Path) -> list[dict]:
    return A.read_journal(root)


def _stash_list(root: Path) -> str:
    return _git(root, "stash", "list").strip()


class _OnFirstJournalOpen:
    """Shadow ``open`` inside the artifact module: the first open of the journal runs ``act``
    right after it returns — a rewrite that does not take the door lock."""

    def __init__(self, A, root: Path, act):
        self.A, self.jp, self.act, self.fired = A, A.journal_path(root), act, False

    def __call__(self, file, *a, **k):
        fh = builtins.open(file, *a, **k)
        if not self.fired and Path(file) == self.jp:
            self.fired = True
            self.act()
        return fh

    def __enter__(self):
        self.A.open = self
        return self

    def __exit__(self, *exc):
        del self.A.open


class _MidAppend:
    """Shadow ``_entry_sha`` inside the artifact module: its first call — inside ``_append``,
    after the handle is locked and checked, before the line is written — runs ``act`` first."""

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


def _tmp():
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("cairn-0f8a-")


def _shape_a():
    # (a) quiet holds the lock across stash … pop; the door write waits for it.
    with _tmp() as t:
        A, root = _world(Path(t))
        try:
            ready = Path(t) / "ready"
            env = dict(_ENV, PYTHONPATH=str(_REPO))
            q = subprocess.Popen(
                [sys.executable, "-m", "cairn.tools.artifact", "quiet", "-C", str(root), "--", "sh", "-c",
                 f"git stash push -q && touch {ready} && sleep 2 && git stash pop -q"],
                env=env, cwd=str(root))
            deadline = time.time() + 60
            while not ready.exists():
                assert q.poll() is None, f"quiet exited {q.returncode} before its stash stood"
                assert time.time() < deadline, "quiet's stash never stood"
                time.sleep(0.05)
            out = A.write(root / "ideas" / "a.json", _doc(7), verb="cast", why="written while quiet held")
            assert q.wait(timeout=60) == 0, "the quiet command failed"
            eid = out["entry"]["entry"]
            ids = [e["entry"] for e in _lines(A, root)]
            assert ids.count(eid) == 1, f"(a) the line stands {ids.count(eid)} times, not once"
            assert (root / "ideas" / "a.json").read_text() == _doc(7), "(a) the record lost its bytes"
            assert (root / "ideas" / "b.json").read_text() == _doc(1), "(a) the stashed record did not come back"
            assert A.verify_chain(root) == [], f"(a) chain faults: {A.verify_chain(root)}"
            assert _stash_list(root) == "", "(a) a stash was left behind"
        finally:
            A.set_diagnostic_roots(None)

def _shape_b():
    # (b) a stash that ignores the lock, landing mid-append (after the handle was checked, before
    #     the line is written — where the measured loss landed): raise and park, never drop.
    with _tmp() as t:
        A, root = _world(Path(t))
        try:
            raised = None
            with _MidAppend(A, lambda: _git(root, "stash", "push", "-q")):
                try:
                    A.write(root / "ideas" / "a.json", _doc(8), verb="cast", why="written under a stash")
                except A.JournalLineOrphaned as exc:
                    raised = exc
            assert raised is not None, "(b) the door did not raise: the line was dropped silently"
            _git(root, "stash", "pop", "-q")
            park = A.orphan_park(root)
            parked = [json.loads(x) for x in park.read_text(encoding="utf-8").splitlines() if x.strip()]
            assert len(parked) == 1, f"(b) the park holds {len(parked)} entries, not 1"
            assert parked[0]["entry"] in str(raised), "(b) the error does not name the entry id"
            assert parked[0]["path"] == "ideas/a.json" and parked[0]["path"] in str(raised)
            assert parked[0]["sha_after"] == A._sha((root / "ideas" / "a.json").read_bytes()), \
                "(b) the parked entry does not describe the record's landed bytes"
        finally:
            A.set_diagnostic_roots(None)

def _shape_c():
    # (c) the journal replaced at the path between open and lock: the line lands in that file, once.
    with _tmp() as t:
        A, root = _world(Path(t))
        try:
            jp = A.journal_path(root)

            def replace():
                tmp = jp.with_name(jp.name + ".swap")
                shutil.copyfile(jp, tmp)
                os.replace(tmp, jp)

            with _OnFirstJournalOpen(A, root, replace):
                out = A.write(root / "ideas" / "a.json", _doc(9), verb="cast", why="written across a swap")
            ids = [e["entry"] for e in _lines(A, root)]
            assert ids.count(out["entry"]["entry"]) == 1, f"(c) the line stands {ids.count(out['entry']['entry'])} times"
            assert A.verify_chain(root) == [], f"(c) chain faults: {A.verify_chain(root)}"
        finally:
            A.set_diagnostic_roots(None)


def test_a_rewrite_cannot_drop_a_line():
    """Every shape runs, and every failure is named in one pass."""
    faults = []
    for shape in (_shape_a, _shape_b, _shape_c):
        try:
            shape()
        except Exception as exc:          # an assertion or the door's own raise: both are faults
            faults.append(f"{shape.__name__}: {type(exc).__name__}: {exc}")
    assert not faults, "\n".join(faults)


def test_an_undisturbed_append_writes_one_chained_line():
    with _tmp() as t:
        A, root = _world(Path(t))
        try:
            before = _lines(A, root)
            out = A.write(root / "ideas" / "a.json", _doc(5), verb="cast", why="no rewrite")
            after = _lines(A, root)
            assert len(after) == len(before) + 1, f"{len(after) - len(before)} lines, not 1"
            assert after[:-1] == before, "the prior lines changed"
            assert after[-1]["entry"] == out["entry"]["entry"]
            assert after[-1]["prev"] == before[-1]["entry"], "the line is not chained on the prior tail"
            assert A.verify_chain(root) == []
        finally:
            A.set_diagnostic_roots(None)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
