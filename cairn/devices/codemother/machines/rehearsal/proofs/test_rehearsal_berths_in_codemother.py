#!/usr/bin/env python3
"""Proof for ticket 36bbcb2b45c4: rehearsal berths among codemother's machines.

  1. no tracked file remains under the old address cairn/machines/rehearsal/, and the moved
     charter names codemother as owner with gated_by unchanged (["codemother", "Akien", "CC"]);
  2. no tracked .py, .json or bin file imports or path-joins the old address: a git grep for its
     dotted, slash and Path-join spellings, history.json, state.json, validations/, .jsonl
     records and the recorded reader replies under proofs/fixtures/ left as written;
  3. encapsulation_holds reads no finding naming rehearsal (the other half of clause 3, every
     moved proof resealing green, is the seal itself);
  4. the three-file teeth that need the machine read green from
     test_rehearsal_reads_the_three_file_ticket.py beside this file;
     cairn/tools/base/proofs/test_the_ticket_is_three_files.py names neither module path; and
     bin/cmd/rehearse --help still runs (argparse answers --help before it reads a ticket).

    bin/cairn test cairn/devices/codemother/machines/rehearsal/proofs/test_rehearsal_berths_in_codemother.py
"""
from __future__ import annotations

import importlib
import json
import re
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"36bbcb2b45c4": {
    "1": "nothing_stands_at_the_old_address_and_codemother_owns_it",
    "2": "no_tracked_code_imports_or_path_joins_the_old_address",
    "3": "encapsulation_names_no_rehearsal_finding",
    "4": "the_three_file_teeth_read_from_the_rehearsal",
}}

_M, _R = "machines", "rehearsal"
OLD = f"cairn/{_M}/{_R}"
NEW = f"cairn/devices/codemother/{_M}/{_R}"
GATED_BY = ["codemother", "Akien", "CC"]
_SPELLINGS = [re.escape(f"cairn.{_M}.{_R}"), re.escape(OLD),
              rf"""["']cairn["']\s*[/,]\s*["']{_M}["']\s*[/,]\s*["']{_R}["']"""]
_RECORD = re.compile(r"(^|/)(history|state)\.json$|/validations/|\.jsonl$|/proofs/fixtures/")
_THREE_FILES = "cairn/tools/base/proofs/test_the_ticket_is_three_files.py"
_MOVED = "cairn.devices.codemother.machines.rehearsal.proofs.test_rehearsal_reads_the_three_file_ticket"


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
    me = Path(__file__).resolve().relative_to(_REPO).as_posix()   # this file names what it greps for
    hits = [ln for ln in r.stdout.splitlines()
            if not _RECORD.search(ln.split(":", 1)[0]) and ln.split(":", 1)[0] != me]
    assert not hits, f"{len(hits)} tracked line(s) still spell the old address: {hits[:8]}"


def encapsulation_names_no_rehearsal_finding() -> None:
    from cairn.tools.inspect_wire.inspect_wire import ask
    breaches = ask("encapsulation_breaches", str(_REPO))
    named = [b for b in breaches if _R in json.dumps(b, default=str)]
    assert not named, f"encapsulation_holds names rehearsal: {named}"


def the_three_file_teeth_read_from_the_rehearsal() -> None:
    text = (_REPO / _THREE_FILES).read_text(encoding="utf-8")
    for mod in (f"cairn.{_M}.{_R}", f"cairn.devices.codemother.{_M}.{_R}"):
        assert mod not in text, f"{_THREE_FILES} still names {mod}"
    moved = importlib.import_module(_MOVED)
    assert moved.main() == 0, f"{_MOVED} read red"
    r = subprocess.run([str(_REPO / "bin" / "cmd" / "rehearse"), "--help"], capture_output=True,
                       text=True, timeout=60, cwd=str(_REPO))
    assert r.returncode == 0 and "cairn rehearse" in r.stdout, (
        f"bin/cmd/rehearse --help exit {r.returncode}: {(r.stderr or r.stdout)[-300:]}")


def main() -> int:
    red = 0
    for fn in (nothing_stands_at_the_old_address_and_codemother_owns_it,
               no_tracked_code_imports_or_path_joins_the_old_address,
               encapsulation_names_no_rehearsal_finding,
               the_three_file_teeth_read_from_the_rehearsal):
        try:
            fn()
            print(f"  green  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            red += 1
            print(f"  RED    {fn.__name__}: {type(e).__name__}: {e}")
    return 1 if red else 0


if __name__ == "__main__":
    sys.exit(main())
