"""Proof for ticket b7d2e05a1c93 — two journals that grew apart meet without forking the chain.

Measured 2026-11-11 (6d324d26343d's PROVED push): two sessions appended to
``.artifact-journal.jsonl``, git text-merged the file, and upstream HEAD was forked at entry
16162 (a peer had chained off entry 16018). The repair was a hand re-link. Branch-per-ticket
(outline 3.3.6) makes every landing such a meeting.

The world is a scratch git repo with the root's own ``.gitattributes`` line and the driver
``install-merge-driver`` configures. Two branches each append two chained entries, then they
are merged one way and rebased the other. No live repo and no live journal are touched.

  1. a merge of two branches that both appended takes no conflict, holds every entry once, and
     replays clean from genesis (``verify_chain`` returns ``[]``);
  2. the side merged into keeps its own lines byte for byte, in order, and the incoming
     entries keep their bodies, re-linked only in ``prev`` and ``entry``;
  3. a rebase of one branch onto the other does the same, and re-linking an entry already
     present (a copy an earlier merge re-linked) does not duplicate it.

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


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True).stdout


def _attributes_line() -> str:
    for line in (_REPO / ".gitattributes").read_text(encoding="utf-8").splitlines():
        if line.split() and line.split()[0] == _J:
            return line
    raise AssertionError(f"the cairn root's .gitattributes names no driver for {_J}")


def _append(root: Path, why: str) -> None:
    from cairn.tools.artifact.artifact import _entry_sha
    jp = root / _J
    lines = [ln for ln in jp.read_text(encoding="utf-8").splitlines() if ln.strip()] if jp.exists() else []
    e = {"path": f"r/{why}.json", "verb": "cast", "why": why, "sha_before": "absent",
         "sha_after": why, "at": f"2026-11-12T00:00:{len(lines):02d}"}
    e["prev"] = json.loads(lines[-1])["entry"] if lines else "genesis"
    e["entry"] = _entry_sha(e)
    with open(jp, "a", encoding="utf-8") as fh:
        fh.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + "\n")
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
    _append(root, "base")
    _git(root, "checkout", "-qb", "side")
    _append(root, "side-1")
    _append(root, "side-2")
    _git(root, "checkout", "-q", "main")
    _append(root, "main-1")
    _append(root, "main-2")
    return root


def _entries(root: Path) -> list[dict]:
    return [json.loads(ln) for ln in (root / _J).read_text(encoding="utf-8").splitlines() if ln.strip()]


def _faults(root: Path) -> list[str]:
    from cairn.tools.artifact.artifact import verify_chain
    import cairn.tools.artifact.artifact as A
    real = A.journal_path
    A.journal_path = lambda r: Path(r) / _J
    try:
        return verify_chain(root)
    finally:
        A.journal_path = real


def test_a_merge_takes_no_conflict_and_replays_clean():
    with tempfile.TemporaryDirectory() as t:
        root = _world(Path(t))
        merged = subprocess.run(["git", "-C", str(root), "merge", "-q", "--no-edit", "side"],
                                capture_output=True, text=True)
        assert merged.returncode == 0, merged.stdout + merged.stderr
        whys = [e["why"] for e in _entries(root)]
        assert sorted(whys) == sorted(["base", "main-1", "main-2", "side-1", "side-2"]), whys
        assert _faults(root) == [], _faults(root)


def test_the_side_merged_into_keeps_its_lines():
    with tempfile.TemporaryDirectory() as t:
        root = _world(Path(t))
        before = (root / _J).read_bytes()
        side = _git(root, "show", f"side:{_J}")
        incoming = {json.loads(ln)["why"]: json.loads(ln) for ln in side.splitlines() if ln.strip()}
        _git(root, "merge", "-q", "--no-edit", "side")
        after = (root / _J).read_bytes()
        assert after.startswith(before), "the side merged into lost or moved its own lines"
        for e in _entries(root)[len(before.splitlines()):]:
            was = incoming[e["why"]]
            strip = lambda d: {k: v for k, v in d.items() if k not in ("prev", "entry")}
            assert strip(e) == strip(was), (e, was)


def test_a_rebase_meets_the_same_way_and_never_duplicates():
    with tempfile.TemporaryDirectory() as t:
        root = _world(Path(t))
        _git(root, "checkout", "-q", "side")
        rebased = subprocess.run(["git", "-C", str(root), "rebase", "-q", "main"],
                                 capture_output=True, text=True)
        assert rebased.returncode == 0, rebased.stdout + rebased.stderr
        whys = [e["why"] for e in _entries(root)]
        assert whys[:3] == ["base", "main-1", "main-2"], whys
        assert sorted(whys) == sorted(["base", "main-1", "main-2", "side-1", "side-2"]), whys
        assert _faults(root) == [], _faults(root)
        # main now meets the rebased side: each entry is there once, re-linked copies included.
        _git(root, "checkout", "-q", "main")
        _append(root, "main-3")
        _git(root, "merge", "-q", "--no-edit", "side")
        whys = [e["why"] for e in _entries(root)]
        assert sorted(whys) == sorted(["base", "main-1", "main-2", "main-3", "side-1", "side-2"]), whys
        assert _faults(root) == [], _faults(root)


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
