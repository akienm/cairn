#!/usr/bin/env python3
"""Proof for ticket 6560fdb5b935: exemptions berths among codemother's machines.

  1. no tracked file remains under the old address cairn/machines/exemptions/, and the moved
     charter names codemother as owner with gated_by unchanged (["codemother", "Akien", "CC"]);
  2. no tracked .py, .json or bin file imports or path-joins the old address: a git grep for its
     dotted, slash and Path-join spellings, history.json, state.json, validations/ and .jsonl
     records left as written;
  3. encapsulation_holds reads no finding naming exemptions (the other half of clause 3, every
     moved proof resealing green, is the seal itself);
  4. cairn/tools/question/proofs/test_question.py imports neither corrosion nor exemptions at
     either address (the answered-question tooth reads from test_an_answered_question_justifies.py
     beside this file, its own seal).

    bin/cairn test cairn/devices/codemother/machines/exemptions/proofs/test_exemptions_berths_in_codemother.py
"""
from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"6560fdb5b935": {
    "1": "nothing_stands_at_the_old_address_and_codemother_owns_it",
    "2": "no_tracked_code_imports_or_path_joins_the_old_address",
    "3": "encapsulation_names_no_exemptions_finding",
    "4": "the_question_tools_proof_imports_no_machine",
}}

_M, _E = "machines", "exemptions"
OLD = f"cairn/{_M}/{_E}"
NEW = f"cairn/devices/codemother/{_M}/{_E}"
GATED_BY = ["codemother", "Akien", "CC"]
# built from parts so this file does not spell what it greps for
_SPELLINGS = [re.escape(f"cairn.{_M}.{_E}"), re.escape(OLD),
              rf"""["']cairn["']\s*[/,]\s*["']{_M}["']\s*[/,]\s*["']{_E}["']"""]
_RECORD = re.compile(r"(^|/)(history|state)\.json$|/validations/|\.jsonl$")
_QUESTION_PROOF = "cairn/tools/question/proofs/test_question.py"
_FORBIDDEN = (f"cairn.{_M}.corrosion", f"cairn.{_M}.{_E}",
              f"cairn.devices.codemother.{_M}.corrosion", f"cairn.devices.codemother.{_M}.{_E}")


def _tracked() -> list[str]:
    out = subprocess.run(["git", "-C", str(_REPO), "ls-files", "-z"], capture_output=True,
                         check=True).stdout.decode("utf-8")
    return [f for f in out.split("\0") if f]


def nothing_stands_at_the_old_address_and_codemother_owns_it() -> None:
    left = [f for f in _tracked() if f.startswith(OLD + "/")]
    assert not left, f"{len(left)} tracked file(s) still at {OLD}/: {left[:5]}"
    charter = json.loads((_REPO / NEW / "intention+why.json").read_text(encoding="utf-8"))
    assert str(charter.get("owner", "")).startswith("codemother"), (
        f"the moved charter's owner does not name codemother first: {charter.get('owner', '')[:120]!r}")
    assert charter.get("gated_by") == GATED_BY, f"gated_by changed: {charter.get('gated_by')}"


def no_tracked_code_imports_or_path_joins_the_old_address() -> None:
    r = subprocess.run(["git", "-C", str(_REPO), "grep", "-n", "-I", "-E",
                        "|".join(f"({s})" for s in _SPELLINGS), "--", "*.py", "*.json", "bin/"],
                       capture_output=True, text=True)
    assert r.returncode in (0, 1), f"git grep failed: {r.stderr[:200]}"
    hits = [ln for ln in r.stdout.splitlines() if not _RECORD.search(ln.split(":", 1)[0])]
    assert not hits, f"{len(hits)} tracked line(s) still spell the old address: {hits[:8]}"


def encapsulation_names_no_exemptions_finding() -> None:
    from cairn.devices.codemother.tools.inspect_wire.inspect_wire import ask
    breaches = ask("encapsulation_breaches", str(_REPO))
    named = [b for b in breaches if _E in json.dumps(b, default=str)]
    assert not named, f"encapsulation_holds names exemptions: {named}"


def the_question_tools_proof_imports_no_machine() -> None:
    tree = ast.parse((_REPO / _QUESTION_PROOF).read_text(encoding="utf-8"))
    found = []
    for n in ast.walk(tree):
        mods = []
        if isinstance(n, ast.Import):
            mods = [a.name for a in n.names]
        elif isinstance(n, ast.ImportFrom) and n.module:
            mods = [n.module] + [f"{n.module}.{a.name}" for a in n.names]
        found += [f"{n.lineno}:{m}" for m in mods if any(m == f or m.startswith(f + ".") for f in _FORBIDDEN)]
    assert not found, f"{_QUESTION_PROOF} imports a machine: {found}"


def main() -> int:
    red = 0
    for fn in (nothing_stands_at_the_old_address_and_codemother_owns_it,
               no_tracked_code_imports_or_path_joins_the_old_address,
               encapsulation_names_no_exemptions_finding,
               the_question_tools_proof_imports_no_machine):
        try:
            fn()
            print(f"  green  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            red += 1
            print(f"  RED    {fn.__name__}: {type(e).__name__}: {e}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
