"""Proof for ticket 750ead1af9c1 — `cairn codemother retire <path>...` checks the callers of what it
deletes in the same act as the deletion, and nothing checks afterwards (outline 1.3.7.1.1, Akien
2026-11-17).

The teeth, one per clause, over a scratch repo with the runner injected (each fixture proof is a
python file run with python3 in the scratch repo; exit 0 is green):

  1. a target whose namers' proofs stay green is deleted (a record through the artifact door), and the report names the namers, the
     proofs run and the namers not run;
  2. a target one of whose namers' proofs turns red is restored byte for byte, the exit is 1, and
     the red proof is named as the caller; a commons forwarding order to a target is a caller too;
  3. a code namer with no proof is reported as unmeasured, a code namer inside a component has its
     component's proofs run, and history.json, state.json, validations/ and dot-files are never
     namers;
  4. `cairn codemother retire` with no target exits 2 and prints its usage.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))
SHORTCUT = REPO / "cairn" / "devices" / "codemother" / "bin" / "retire"


class _CallTime:
    """A module under proof, bound at CALL time: the hollow reading takes it away."""

    def __init__(self, mod):
        self._mod = mod

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._mod), name)


R = _CallTime("cairn.devices.codemother.machines.retire.retire")

PROVES = {
    "750ead1af9c1": {
        "1": "test_a_target_whose_namers_stay_green_is_deleted_and_reported",
        "2": "test_a_target_whose_namer_turns_red_is_restored_and_the_caller_named",
        "3": "test_unproven_code_is_unmeasured_and_records_are_never_namers",
        "4": "test_no_target_exits_2_with_usage",
    },
}

GREEN = "import sys\nsys.exit(0)\n"


def _runner(repo, proofs):
    out = {}
    for p in proofs:
        r = subprocess.run([sys.executable, p], cwd=repo, capture_output=True, timeout=60)
        out[p] = "green" if r.returncode == 0 else "red"
    return out


def _put(root: Path, rel: str, text: str) -> None:
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text)


def test_a_target_whose_namers_stay_green_is_deleted_and_reported():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        tgt = "cairn/tools/a/a.py"
        _put(root, tgt, "X = 1\n")
        _put(root, "cairn/tools/b/proofs/test_b.py", f"# once cited {tgt}\n" + GREEN)
        _put(root, "docs/notes.md", f"The old module {tgt} was here.\n")
        rep = R.retire(root, [tgt], runner=_runner, commons=root / "nocommons")
        assert rep["exit"] == 0, rep
        assert not (root / tgt).exists(), "the target was not deleted"
        assert rep["retired"] == [tgt], rep
        assert set(rep["namers"]) == {"cairn/tools/b/proofs/test_b.py", "docs/notes.md"}, rep["namers"]
        assert rep["proofs_green"] == ["cairn/tools/b/proofs/test_b.py"], rep
        assert rep["not_run"] == ["docs/notes.md"], rep
        assert rep["callers"] == [], rep
    # a record target (a validation) leaves through the artifact door, never by a bare delete
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        rec = "bin/validations/test_gone.json"
        _put(root, rec, "[]\n")
        removed = []
        rep = R.retire(root, [rec], runner=_runner, commons=root / "nocommons",
                       remover=lambda repo, rel: (removed.append(rel), (Path(repo) / rel).unlink()))
        assert rep["exit"] == 0 and removed == [rec], (rep, removed)


def test_a_target_whose_namer_turns_red_is_restored_and_the_caller_named():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        tgt = "cairn/tools/c/c.py"
        body = "Y = 2  # bytes to restore exactly\n"
        _put(root, tgt, body)
        other = "cairn/tools/c/helper.py"
        _put(root, other, "Z = 3\n")
        caller = "cairn/tools/d/proofs/test_d.py"
        _put(root, caller, f"import os, sys\nsys.exit(0 if os.path.exists('{tgt}') else 1)\n")
        _put(root, "cairn/tools/e/proofs/test_e.py", f"# names {tgt} and {other}\n" + GREEN)
        rep = R.retire(root, [tgt, other], runner=_runner, commons=root / "nocommons")
        assert rep["exit"] == 1, rep
        assert (root / tgt).read_text() == body, "the target was not restored byte for byte"
        assert (root / other).read_text() == "Z = 3\n", "every target is restored, not only the called one"
        assert rep["callers"] == [caller], rep
        assert rep["retired"] == [], rep
        assert sorted(rep["restored"]) == sorted([tgt, other]), rep
    # a forwarding order in the commons that sends an address TO a target is a caller too: the
    # census reads it as a live pointer, and no text search of the repo can see it
    with tempfile.TemporaryDirectory() as td:
        root, commons = Path(td) / "repo", Path(td) / "CairnCommons"
        tgt = "bin/proofs/test_gone.py"
        _put(root, tgt, GREEN)
        _put(commons, "tickets/aaaaaaaaaaaa-x.state.json",
             json.dumps({"forwarding": {"cairn/old.py": {"to": tgt, "why": "x"}}}))
        rep = R.retire(root, [tgt], runner=_runner, commons=commons)
        assert rep["exit"] == 1 and (root / tgt).read_text() == GREEN, rep
        assert rep["callers"] == ["tickets/aaaaaaaaaaaa-x.state.json forwards cairn/old.py"], rep


def test_unproven_code_is_unmeasured_and_records_are_never_namers():
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        tgt = "cairn/tools/a/a.py"
        _put(root, tgt, "X = 1\n")
        _put(root, "cairn/tools/f/f.py", "from cairn.tools.a.a import X\n")          # no component
        _put(root, "cairn/tools/g/intention+why.json", "{}\n")
        _put(root, "cairn/tools/g/g.py", "import cairn.tools.a.a\n")                # a component
        _put(root, "cairn/tools/g/proofs/test_g.py", GREEN)
        _put(root, "cairn/tools/b/proofs/test_red.py", f"# {tgt}\nimport sys\nsys.exit(1)\n")
        for rec in ("cairn/tools/b/history.json", "cairn/tools/b/state.json",
                    "cairn/tools/b/validations/v.json", "cairn/tools/b/.note", ".hidden/x.py"):
            _put(root, rec, f"{tgt}\n")
        rep = R.retire(root, [tgt], runner=_runner, commons=root / "nocommons")
        assert rep["exit"] == 0, rep
        assert "cairn/tools/f/f.py" in rep["unmeasured"], rep
        assert "cairn/tools/g/proofs/test_g.py" in rep["proofs_green"], rep
        assert rep["red_before"] == ["cairn/tools/b/proofs/test_red.py"], rep
        for rec in ("history.json", "state.json", "validations/v.json", ".note", ".hidden/x.py"):
            assert not any(n.endswith(rec) for n in rep["namers"]), (rec, rep["namers"])


def test_no_target_exits_2_with_usage():
    r = subprocess.run([sys.executable, str(SHORTCUT)], capture_output=True, text=True, cwd=REPO,
                       timeout=60)
    assert r.returncode == 2, (r.returncode, r.stdout, r.stderr)
    assert "usage" in (r.stdout + r.stderr).lower(), r.stdout + r.stderr


def main() -> int:
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    assert len(teeth) == 4, len(teeth)
    failed = []
    for tooth in teeth:
        try:
            tooth()
        except Exception as e:                       # noqa: BLE001 — the reason is the record
            failed.append(tooth.__name__)
            print(f"  FAIL  {tooth.__name__}: {type(e).__name__}: {str(e)[:300]}")
            continue
        print(f"  PASS  {tooth.__name__}")
    if failed:
        print(f"red — {len(failed)} of {len(teeth)} teeth: {', '.join(failed)}")
        return 1
    print("green — 4 teeth: a green-namer target is deleted and reported, a turned-red namer "
          "restores every target and is named, unproven code is unmeasured and records are never "
          "namers, and no target exits 2")
    return 0


if __name__ == "__main__":
    sys.exit(main())
