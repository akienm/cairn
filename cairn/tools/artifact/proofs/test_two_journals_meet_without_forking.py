"""Proof for ticket b7d2e05a1c93 — two journals that grew apart meet without forking.

Measured 2026-11-11 (6d324d26343d's PROVED push): two sessions appended to
``.artifact-journal.jsonl``, git text-merged the file, and upstream HEAD was forked at entry
16162 (a peer had chained off entry 16018). The repair was a hand re-link. Branch-per-ticket
(outline 3.3.6) makes every landing such a meeting.

Since ticket b15da5656579 the journal is an index, one line per record path (its newest
entry), so two sides meet BY PATH: the newer ``at`` wins, a tie goes to the larger entry sha,
and nothing is re-linked. These teeth keep their names and measure that meeting.

The world is a scratch git repo with the root's own ``.gitattributes`` line and the driver
``install-merge-driver`` configures. Two branches each write a path of their own and one path
both share, then they are merged one way and rebased the other. No live repo and no live
journal are touched.

  1. a merge of two branches that both wrote takes no conflict, holds one line per path, the
     shared path at the newer side's entry, and the index verifies (``verify_journal`` is ``[]``);
  2. every line the merge keeps is one side's line, byte for byte, and the result is the same
     bytes whichever side git calls ours;
  3. a rebase of one branch onto the other meets the same way, and meeting again after a
     further write keeps one line per path, never a duplicate.

    python3 cairn/tools/artifact/proofs/test_two_journals_meet_without_forking.py   # exit 0 = green
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

PROVES = {
    "b7d2e05a1c93": {"1": "test_a_merge_takes_no_conflict_and_replays_clean",
                     "2": "test_the_side_merged_into_keeps_its_lines",
                     "3": "test_a_rebase_meets_the_same_way_and_never_duplicates"},
}

_REPO = Path(__file__).resolve().parents[4]
_J = ".artifact-journal.jsonl"
_CLOCK = [0]


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True).stdout


def _attributes_line() -> str:
    for line in (_REPO / ".gitattributes").read_text(encoding="utf-8").splitlines():
        if line.split() and line.split()[0] == _J:
            return line
    raise AssertionError(f"the cairn root's .gitattributes names no driver for {_J}")


def _write(root: Path, path: str, why: str) -> None:
    """What the door leaves in the index: the path's old line dropped, its new one last."""
    from cairn.tools.artifact.artifact import _entry_sha
    jp = root / _J
    lines = [ln for ln in jp.read_text(encoding="utf-8").splitlines() if ln.strip()] if jp.exists() else []
    lines = [ln for ln in lines if json.loads(ln)["path"] != path]
    _CLOCK[0] += 1
    e = {"path": path, "verb": "cast", "why": why, "sha_before": "absent",
         "sha_after": why, "at": f"2026-11-12T00:{_CLOCK[0] // 60:02d}:{_CLOCK[0] % 60:02d}+00:00"}
    e["entry"] = _entry_sha(e)
    lines.append(json.dumps(e, ensure_ascii=False, sort_keys=True))
    jp.write_text("\n".join(lines) + "\n", encoding="utf-8")
    _git(root, "add", _J)
    _git(root, "commit", "-qm", why)


def _world(tmp: Path) -> Path:
    from cairn.tools.artifact.__main__ import _install_merge_driver
    root = tmp / "repo"
    root.mkdir()
    _git(root, "init", "-q", "-b", "main")
    _git(root, "config", "user.email", "proof@example.invalid")
    _git(root, "config", "user.name", "proof")
    (root / ".gitattributes").write_text(_attributes_line() + "\n", encoding="utf-8")
    _git(root, "add", ".gitattributes")
    _git(root, "commit", "-qm", "attributes")
    _install_merge_driver(root)
    _write(root, "r/base.json", "base")
    _write(root, "r/shared.json", "shared-base")
    _git(root, "checkout", "-qb", "side")
    _write(root, "r/side.json", "side-1")
    _write(root, "r/shared.json", "shared-side")
    _git(root, "checkout", "-q", "main")
    _write(root, "r/main.json", "main-1")
    _write(root, "r/shared.json", "shared-main")      # the newer write to the shared path
    return root


def _entries(root: Path) -> list[dict]:
    return [json.loads(ln) for ln in (root / _J).read_text(encoding="utf-8").splitlines() if ln.strip()]


def _faults(root: Path) -> list[str]:
    import cairn.tools.artifact.artifact as A
    real = A.journal_path
    A.journal_path = lambda r: Path(r) / _J
    try:
        return A.verify_journal(root)
    finally:
        A.journal_path = real


def _by_path(root: Path) -> dict[str, str]:
    return {e["path"]: e["why"] for e in _entries(root)}


_MET = {"r/base.json": "base", "r/shared.json": "shared-main", "r/side.json": "side-1",
        "r/main.json": "main-1"}


def test_a_merge_takes_no_conflict_and_replays_clean():
    with tempfile.TemporaryDirectory() as t:
        root = _world(Path(t))
        merged = subprocess.run(["git", "-C", str(root), "merge", "-q", "--no-edit", "side"],
                                capture_output=True, text=True)
        assert merged.returncode == 0, merged.stdout + merged.stderr
        assert len(_entries(root)) == 4, [e["why"] for e in _entries(root)]
        assert _by_path(root) == _MET, _by_path(root)
        assert _faults(root) == [], _faults(root)


def test_the_side_merged_into_keeps_its_lines():
    from cairn.tools.artifact.artifact import merge_journals
    with tempfile.TemporaryDirectory() as t:
        root = _world(Path(t))
        ours = _git(root, "show", f"main:{_J}").encode()
        theirs = _git(root, "show", f"side:{_J}").encode()
        sides = {ln for blob in (ours, theirs) for ln in blob.decode().splitlines() if ln.strip()}
        _git(root, "merge", "-q", "--no-edit", "side")
        after = (root / _J).read_bytes()
        kept = [ln for ln in after.decode().splitlines() if ln.strip()]
        assert all(ln in sides for ln in kept), "a kept line is not either side's line byte for byte"
        assert merge_journals(ours, theirs) == merge_journals(theirs, ours) == after, \
            "the merge is not the same bytes in either order"


def test_a_rebase_meets_the_same_way_and_never_duplicates():
    with tempfile.TemporaryDirectory() as t:
        root = _world(Path(t))
        _git(root, "checkout", "-q", "side")
        rebased = subprocess.run(["git", "-C", str(root), "rebase", "-q", "main"],
                                 capture_output=True, text=True)
        assert rebased.returncode == 0, rebased.stdout + rebased.stderr
        assert _by_path(root) == _MET, _by_path(root)
        assert _faults(root) == [], _faults(root)
        # main meets the rebased side after a further write: one line per path, never two.
        _git(root, "checkout", "-q", "main")
        _write(root, "r/side.json", "side-from-main")
        _git(root, "merge", "-q", "--no-edit", "side")
        assert len(_entries(root)) == 4, [e["why"] for e in _entries(root)]
        assert _by_path(root) == dict(_MET, **{"r/side.json": "side-from-main"}), _by_path(root)
        assert _faults(root) == [], _faults(root)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
