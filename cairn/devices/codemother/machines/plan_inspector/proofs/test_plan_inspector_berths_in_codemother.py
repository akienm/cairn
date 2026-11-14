"""plan_inspector berths among CodeMother's machines (ticket f4f024a33c88, a child of 4c4addb09adb).

Outline 9.4.4 and ticket 4c4addb09adb: the code pipeline's inspectors and gates live inside
CodeMother. Measured 2026-11-13: plan_inspector stood at cairn/machines/plan_inspector/, owned
by no device, and no tracked code outside it imported or path-joined it.

One tooth per falsifier clause. Red-first, before the move: clause 1 reads red because the old
directory stands, and clause 2 reads red because the old module path is spelled in tracked
code.
  1. No tracked file remains under cairn/machines/plan_inspector/. The charter at the new
     address names codemother as owner, with gated_by unchanged from before the move (["CC"]).
  2. No tracked code imports or path-joins the old address, in its dotted, slash or Path-join
     spelling. Records are left as written: history.json, state.json, validations/ and .jsonl.
  3. Every proof under the new address runs green there, and encapsulation_holds reads no
     finding that names the machine.

    bin/cairn test cairn/devices/codemother/machines/plan_inspector/proofs/test_plan_inspector_berths_in_codemother.py
"""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {"f4f024a33c88": {
    "1": "test_nothing_stands_at_the_old_address_and_codemother_owns_the_charter",
    "2": "test_no_tracked_code_names_the_old_address",
    "3": "test_the_proofs_run_green_at_the_new_address_and_encapsulation_holds",
}}

_NAME = "plan_inspector"
_NEW = Path("cairn/devices/codemother/machines") / _NAME
_GATED_BEFORE = ["CC"]
# The old address, spelled so this file does not itself carry it.
_OLD_SLASH = "cairn/" + "machines/" + _NAME
_OLD_DOT = "cairn." + "machines." + _NAME
_OLD_JOIN = r"""['"]machines['"]\s*[,/]\s*['"]""" + _NAME + r"""['"]"""


def _git(*args: str) -> str:
    return subprocess.run(["git", "-C", str(_REPO_ROOT), *args], capture_output=True, text=True,
                          check=False).stdout


def _is_record(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return (name in ("history.json", "state.json") or "/validations/" in f"/{path}"
            or path.endswith(".jsonl"))


def test_nothing_stands_at_the_old_address_and_codemother_owns_the_charter():
    left = _git("ls-files", "--", _OLD_SLASH).split()
    assert not left, f"tracked files remain at the old address: {left}"
    charter = _REPO_ROOT / _NEW / "intention+why.json"
    assert charter.is_file(), f"no charter at {charter}"
    doc = json.loads(charter.read_text(encoding="utf-8"))
    assert doc.get("owner") == "codemother", f"the charter's owner is {doc.get('owner')!r}"
    assert doc.get("gated_by") == _GATED_BEFORE, f"gated_by changed: {doc.get('gated_by')!r}"
    print("ok test_nothing_stands_at_the_old_address_and_codemother_owns_the_charter")


def test_no_tracked_code_names_the_old_address():
    me = str(Path(__file__).resolve().relative_to(_REPO_ROOT))
    hits = []
    for path in _git("ls-files").splitlines():
        if path == me or _is_record(path):
            continue
        if not (path.endswith((".py", ".json")) or path.startswith("bin/")):
            continue
        f = _REPO_ROOT / path
        try:
            text = f.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        for n, line in enumerate(text.splitlines(), 1):
            if _OLD_SLASH in line or _OLD_DOT in line or re.search(_OLD_JOIN, line):
                hits.append(f"{path}:{n}: {line.strip()[:120]}")
    assert not hits, "tracked code still names the old address:\n  " + "\n  ".join(hits)
    print("ok test_no_tracked_code_names_the_old_address")


def test_the_proofs_run_green_at_the_new_address_and_encapsulation_holds():
    me = Path(__file__).resolve()
    proofs = sorted(p for p in (_REPO_ROOT / _NEW / "proofs").glob("test_*.py") if p.resolve() != me)
    assert proofs, f"no proofs under {_NEW / 'proofs'}"
    reds = []
    for p in proofs:
        r = subprocess.run([sys.executable, str(p)], cwd=_REPO_ROOT, capture_output=True, text=True,
                           timeout=600)
        if r.returncode != 0:
            reds.append((p.name, r.returncode, (r.stdout + r.stderr)[-600:]))
    assert not reds, f"proofs red at the new address: {reds}"
    from cairn.machines.build_inspector.inspector import encapsulation_breaches
    rows = [r for r in encapsulation_breaches(str(_REPO_ROOT))
            if _NAME in (r.get("file") or "") or _NAME in (r.get("target") or "")
            or _NAME in (r.get("module") or "")]
    assert not rows, [(r["file"], r["line"], r["module"]) for r in rows]
    print("ok test_the_proofs_run_green_at_the_new_address_and_encapsulation_holds")


if __name__ == "__main__":
    test_nothing_stands_at_the_old_address_and_codemother_owns_the_charter()
    test_no_tracked_code_names_the_old_address()
    test_the_proofs_run_green_at_the_new_address_and_encapsulation_holds()
