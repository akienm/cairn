"""Teeth for the root sieve: a proof that puts only a short root on sys.path (``<repo>/cairn``,
one level short) and imports ``cairn`` is red at PROVEME, by line.

Charter: cairn/tools/proof_coverage/intention+why.json
Ticket:  CairnCommons/tickets/8e73a9efa04a-a-proof-puts-its-own-checkout-on-sys-path-and-proof-coverage-reds-one-that-does.json

Run: python3 cairn/tools/proof_coverage/proofs/test_a_proof_roots_its_imports_at_its_own_checkout.py

WHY A SHORT ROOT IS HOLLOW. ``<repo>/cairn`` holds no ``cairn`` package, so ``import cairn``
falls through to whatever else is on the path, which in the house venv is the editable
install of the MAIN checkout. Under ``bin/cairn test`` the tester pins the proof's checkout
first on PYTHONPATH, which masks it; run any other way the proof measures main's code.
Measured 2026-11-12 on 0d3b8a51c9df's proof at 1bfc8f29f: run directly in a worktree
holding the old outline_check it printed 3/3 green; at parents[6] it reds 3/3.

``proof_coverage`` is bound at module level because the package existed before this build;
the added names are reached INSIDE each tooth, so hollow reds a tooth here and does not
crash the runner.
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from cairn.tools import proof_coverage as pc  # noqa: E402  (the package existed before the build)
from cairn.tools.proof_coverage.proofs.fixtures import historical_instances as H  # noqa: E402

TICKET = "8e73a9efa04a"
PROVES = {
    TICKET: {
        "1": "test_a_short_root_is_a_lack_by_line_and_the_right_shapes_are_not",
        "2": "test_the_real_case_reds_at_1bfc8f29f_and_not_at_87e4be347_and_lacks_carries_it",
        "3": "test_no_proof_in_the_repo_roots_short",
    }
}

KIND = "proof_roots_its_imports_at_its_checkout"
# The real case: 0d3b8a51c9df's proof, at its own address, as committed twice.
REAL = ("cairn/devices/codemother/machines/outline_check/proofs/"
        "test_an_open_question_opens_only_on_a_line_the_ticket_touches.py")
SHORT_AT, FIXED_AT = "1bfc8f29f", "87e4be347"
# The six the census found at 87e4be347, each fixed by this build.
FIXED = (
    "cairn/devices/cairn/machines/bus/proofs/test_pane_channel_identity.py",
    "cairn/devices/codemother/machines/constrain/proofs/"
    "test_the_floor_discovers_only_the_tickets_own_component.py",
    "cairn/devices/codemother/machines/verdict/proofs/test_a_live_logs_miss_names_its_cause.py",
    "cairn/devices/codemother/machines/verdict/proofs/test_the_instrument_is_run.py",
    "cairn/devices/codemother/machines/verdict/proofs/test_the_verdict_door_refuses_before_it_runs.py",
    "cairn/tools/feedback/proofs/test_feedback.py",
)
_SCRATCH: list[tempfile.TemporaryDirectory] = []


def _tmp() -> Path:
    d = tempfile.TemporaryDirectory(prefix="cairn_root_sieve_fixture_")
    _SCRATCH.append(d)
    return Path(d.name)


def _pcm():
    """The module, its added names reached at call time."""
    return pc.proof_coverage


# A fixture proof sits at <repo>/cairn/devices/fixture_device/proofs/, so parents[4] is the
# repo and parents[3] is <repo>/cairn, the short root.
_AT = "cairn/devices/fixture_device/proofs/test_fixture_root.py"

_SHAPES = {
    "short_direct": (True, (
        "import sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[3]))\n"
        "from cairn.tools import x  # noqa\n"), 3),
    "short_through_a_name": (True, (
        "import sys\nfrom pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parents[3]\n"
        "if str(ROOT) not in sys.path:\n"
        "    sys.path.insert(0, str(ROOT))\n"
        "import cairn.tools.x  # noqa\n"), 5),
    "right_depth": (False, (
        "import sys\nfrom pathlib import Path\n"
        "ROOT = Path(__file__).resolve().parents[4]\n"
        "sys.path.insert(0, str(ROOT))\n"
        "from cairn.tools import x  # noqa\n"), None),
    "insert_only_in_a_fixture_string": (False, (
        "from cairn.tools import x  # noqa\n"
        "SRC = 'import sys\\nsys.path.insert(0, str(Path(__file__).resolve().parents[3]))'\n"), None),
    "own_dir_beside_the_root": (False, (
        "import sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parent))\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[4]))\n"
        "from cairn.tools import x  # noqa\n"), None),
    "short_but_imports_no_cairn": (False, (
        "import sys\nfrom pathlib import Path\n"
        "sys.path.insert(0, str(Path(__file__).resolve().parents[3]))\n"
        "import json  # noqa\n"), None),
}


def _plant(text: str) -> tuple[Path, Path]:
    repo = _tmp() / "repo"
    proof = repo / _AT
    proof.parent.mkdir(parents=True)
    (repo / "cairn" / "__init__.py").write_text("", encoding="utf-8")
    proof.write_text(text, encoding="utf-8")
    return repo, proof


# ── clause 1 ──────────────────────────────────────────────────────────────────────────

def test_a_short_root_is_a_lack_by_line_and_the_right_shapes_are_not():
    m = _pcm()
    for name, (red, text, line) in _SHAPES.items():
        repo, proof = _plant(text)
        found = m.misrooted_inserts(proof, repo)
        lacks = m.proof_roots_its_imports_at_its_checkout({"id": TICKET}, repo_root=repo,
                                                           named=[_AT])
        if not red:
            assert found == [] and lacks == [], f"{name} must read green: {found} {lacks}"
            continue
        assert [f["line"] for f in found] == [line], f"{name}: {found}"
        assert found[0]["resolves_to"] == "cairn", f"{name}: {found}"
        assert len(lacks) == 1 and lacks[0]["kind"] == KIND, f"{name}: {lacks}"
        v = lacks[0]["values"]
        assert v["proof"] == _AT and v["line"] == line, f"{name}: {v}"
        assert f"{_AT}:{line}" in lacks[0]["why"], lacks[0]["why"]
    return True


# ── clause 2 ──────────────────────────────────────────────────────────────────────────

def _shown(commit: str) -> str:
    return subprocess.run(["git", "-C", str(REPO_ROOT), "show", f"{commit}:{REAL}"],
                          capture_output=True, text=True, check=True).stdout


def test_the_real_case_reds_at_1bfc8f29f_and_not_at_87e4be347_and_lacks_carries_it():
    m = _pcm()
    seen = {}
    for commit in (SHORT_AT, FIXED_AT):
        world = H.build_world(_tmp(), before={"cairn/__init__.py": ""},
                              build={REAL: _shown(commit)}, proof=REAL, writes_to=[REAL],
                              clauses=3, ticket=TICKET)
        direct = m.misrooted_inserts(world.repo / REAL, world.repo)
        full = [x for x in pc.lacks(world.ticket, repo_root=world.repo, roots=world.roots)
                if x["kind"] == KIND]
        seen[commit] = (direct, full)
    direct, full = seen[SHORT_AT]
    assert direct and all(f["resolves_to"] == "cairn" for f in direct), direct
    assert full and full[0]["values"]["proof"] == REAL, full
    assert {f["values"]["line"] for f in full} == {f["line"] for f in direct}, (full, direct)
    assert seen[FIXED_AT] == ([], []), seen[FIXED_AT]
    print(f"       ({SHORT_AT}: line(s) {sorted(f['line'] for f in direct)} put "
          f"{direct[0]['resolves_to']}/ on sys.path; {FIXED_AT}: none)")
    return True


# ── clause 3 ──────────────────────────────────────────────────────────────────────────

def test_no_proof_in_the_repo_roots_short():
    m = _pcm()
    found = m.misrooted_proofs(REPO_ROOT)
    assert found == {}, "misrooted proofs:\n" + "\n".join(
        f"  {p}:{f['line']} -> {f['resolves_to']}" for p, fs in found.items() for f in fs)
    for rel in FIXED:
        assert (REPO_ROOT / rel).is_file(), rel
        assert m.misrooted_inserts(REPO_ROOT / rel, REPO_ROOT) == [], rel
    n = sum(1 for p in REPO_ROOT.rglob("proofs/test_*.py") if ".git" not in p.parts)
    print(f"       (live corpus: {n} proofs read, none roots short; the six fixed root at the checkout)")
    return True


# ── runner ────────────────────────────────────────────────────────────────────────────

def main() -> int:
    reds = 0
    teeth = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in teeth:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception:  # noqa: BLE001 — a proof reports, never hides
            reds += 1
            print(f"RED  {name}")
            traceback.print_exc()
    for d in _SCRATCH:
        d.cleanup()
    print(f"{'GREEN' if not reds else 'RED'} — {len(teeth) - reds}/{len(teeth)} teeth")
    return 1 if reds else 0


if __name__ == "__main__":
    raise SystemExit(main())
