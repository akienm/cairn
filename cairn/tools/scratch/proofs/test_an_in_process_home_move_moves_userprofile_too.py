"""Proof for ticket 4fb37aa5a13f — the scratch tool names a proof that moves HOME in its own
process and leaves USERPROFILE behind.

Measured 2026-11-13 on akienyoga9i: inferenceproxy's migration proof did
monkeypatch.setenv(HOME) and aider_shim's cold seam did os.environ[HOME] = ..., and on Windows
both read the live ~/.cairn, because Path.home() reads USERPROFILE there. scratch_home_bypass
read [] over both: it reads env copies handed to a child, and an in-process set copies nothing.

One tooth per falsifier clause:

  1. each in-process spelling that moves HOME alone is named: setenv, putenv,
     os.environ[K] = ..., os.environ.setdefault, os.environ.update and patch.dict(os.environ, ...);
  2. the same scopes moving USERPROFILE too are quiet, and so is an env copy handed to a child
     (scratch_home_bypass's jurisdiction: one mouth per defect);
  3. a seam string with %r placeholders that moves HOME alone is named at its line in the file.

The fixture sources are f-strings with the keys spelled apart, so the scan does not read
this proof's own text as a move.

    python cairn/tools/scratch/proofs/test_an_in_process_home_move_moves_userprofile_too.py
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {"4fb37aa5a13f": {
    "1": "test_every_in_process_spelling_that_moves_home_alone_is_named",
    "2": "test_a_scope_that_moves_userprofile_too_and_a_child_env_are_quiet",
    "3": "test_a_seam_string_that_moves_home_alone_is_named_at_its_line"}}

H, U = "HO" + "ME", "USER" + "PROFILE"

SPELLINGS = {
    "setenv": lambda k: f'    monkeypatch.setenv("{k}", "/x")\n',
    "putenv": lambda k: f'    os.putenv("{k}", "/x")\n',
    "subscript": lambda k: f'    os.environ["{k}"] = "/x"\n',
    "setdefault": lambda k: f'    os.environ.setdefault("{k}", "/x")\n',
    "update_kw": lambda k: f'    os.environ.update({k}="/x")\n',
    "update_dict": lambda k: f'    os.environ.update({{"{k}": "/x"}})\n',
    "patch_dict": lambda k: f'    with mock.patch.dict(os.environ, {{"{k}": "/x"}}):\n        pass\n',
}


def _scan(root):
    from cairn.tools.scratch.scratch import scratch_home_in_process   # bound in the tooth
    return scratch_home_in_process(root)


def _tree(files: dict) -> Path:
    root = Path(scratch_dir("testing-4fb3-"))
    (root / "proofs").mkdir()
    for name, src in files.items():
        (root / "proofs" / f"test_{name}.py").write_text(
            "import os\nfrom unittest import mock\n\n\n" + src, encoding="utf-8")
    return root


def test_every_in_process_spelling_that_moves_home_alone_is_named():
    root = _tree({n: f"def scope_{n}(monkeypatch):\n" + s(H) for n, s in SPELLINGS.items()})
    got = sorted(_scan(root))
    want = sorted(f"proofs/test_{n}.py:5 scope_{n}" for n in SPELLINGS)
    assert got == want, f"named {got}, want {want}"


def test_a_scope_that_moves_userprofile_too_and_a_child_env_are_quiet():
    files = {n: f"def scope_{n}(monkeypatch):\n" + s(H) + s(U) for n, s in SPELLINGS.items()}
    files["child_env"] = (f"def scope_child():\n    env = dict(os.environ, {H}='/x')\n"
                          "    return env\n")
    files["control"] = "def scope_control(monkeypatch):\n" + SPELLINGS["setenv"](H)
    got = _scan(_tree(files))     # the control keeps a scan that names nothing from passing
    assert got == ["proofs/test_control.py:5 scope_control"], f"named {got}, want only the control"


def test_a_seam_string_that_moves_home_alone_is_named_at_its_line():
    seam = (f"SEAM = '''\nimport os\nos.environ[\"{H}\"] = %r\nprint(%r)\n'''\n\n"
            f"FIXED = '''\nimport os\nos.environ[\"{H}\"] = os.environ[\"{U}\"] = %r\n'''\n")
    got = _scan(_tree({"seam": seam}))
    assert got == ["proofs/test_seam.py:7 <source string>"], got


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
