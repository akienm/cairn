"""The proof_discovery tool resolves `cairn test` targets to proof files — measured over a
scratch tree, never over the live repo (ticket 67b78ae59c1d, which moved it down from the
tester device so validation.py stops reaching into a device for one stdlib function).

Three teeth, one per shape its charter names: a ``proofs/`` directory expands to its
``test_*.py``; any directory expands to every ``**/proofs/test_*.py`` beneath it, sorted and
deduped; a missing path is kept and announced on stderr, so the run reports it unrunnable
instead of passing over it (a typo that ran zero proofs is a hollow green — Law 8).

Run: python3 cairn/tools/proof_discovery/proofs/test_proof_discovery.py (exit 0 = green).
"""
from __future__ import annotations

import contextlib
import io
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.proof_discovery.proof_discovery import discover


def _tree(root: Path) -> dict[str, Path]:
    """Two components with proofs, one stray non-proof file, one non-proofs test file."""
    made = {}
    for rel in ("a/proofs/test_one.py", "a/proofs/test_two.py", "a/b/proofs/test_three.py"):
        p = root / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("", encoding="utf-8")
        made[rel] = p
    (root / "a/proofs/helper.py").write_text("", encoding="utf-8")
    (root / "a/test_not_in_proofs.py").write_text("", encoding="utf-8")
    return made


def test_a_proofs_directory_expands_to_its_proofs():
    with tempfile.TemporaryDirectory() as tmp:
        made = _tree(Path(tmp).resolve())
        got = discover([str(Path(tmp).resolve() / "a" / "proofs")])
        assert got == sorted([made["a/proofs/test_one.py"], made["a/proofs/test_two.py"]]), got


def test_a_directory_expands_to_every_proof_beneath_it_sorted_and_deduped():
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp).resolve()
        made = _tree(root)
        # the same directory named twice, plus one of its proofs by file: each lands once
        got = discover([str(root / "a"), str(root / "a"), str(made["a/proofs/test_one.py"])])
        assert got == sorted(made.values()), got


def test_a_missing_path_is_kept_and_announced():
    with tempfile.TemporaryDirectory() as tmp:
        missing = str(Path(tmp).resolve() / "no_such_dir_67b78ae59c1d")
        err = io.StringIO()
        with contextlib.redirect_stderr(err):
            got = discover([missing])
        assert got == [Path(missing)], got
        assert f"cairn test: no such path: {missing}" in err.getvalue(), err.getvalue()


TEETH = [test_a_proofs_directory_expands_to_its_proofs,
         test_a_directory_expands_to_every_proof_beneath_it_sorted_and_deduped,
         test_a_missing_path_is_kept_and_announced]

if __name__ == "__main__":
    failed = 0
    for fn in TEETH:
        try:
            fn()
            print(f"PASS {fn.__name__}")
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {fn.__name__}: {exc}")
    print(f"{len(TEETH) - failed} passed, {failed} failed out of {len(TEETH)}")
    sys.exit(1 if failed else 0)
