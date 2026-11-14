#!/usr/bin/env python3
"""Proof that corrosion berths among CodeMother's machines (ticket 47f5765e52a8, a child of
4c4addb09adb: the code pipeline's inspectors and gates live inside CodeMother).

The retired spellings are built from parts below, so this file never names them whole and
tooth (2) can read it like any other file.

  (1) no tracked file remains at the old directory; every moved file stands at the new one;
      the moved charter names codemother as owner, and its gated_by is the value it had before
      the move (['codemother', 'Akien', 'CC'], read off cairn at 4ec507b55);
  (2) no tracked .py, .json or bin/ file outside history, state, validations and journals
      names the old address, in its dotted, slashed or path-joined spelling (CLAUDE.md's two
      lines are not code and wait on open-c9643e21c368);
  (3) no RULE 1 breach (encapsulation_breaches, outline 17.13.1) names the machine, at either
      address. The other half of clause 3, every proof under the new address resealing green,
      is the tester's seal (bin/cairn test --seal --ruling 47f5765e52a8).

    bin/cairn test cairn/devices/codemother/machines/corrosion/proofs/test_corrosion_berths_in_codemother.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[6]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"47f5765e52a8": {"1": "test_the_machine_berths_in_codemother",
                           "2": "test_no_class_space_file_names_the_old_address",
                           "3": "test_no_breach_names_the_machine"}}

_M = "corr" + "osion"
NEW = "cairn/devices/codemother/machines/" + _M
OLD = "cairn/machines/" + _M
GATED_BY_BEFORE = ["codemother", "Akien", "CC"]
_CHARTER = "intention" + "+why.json"
_MOVED = ("__init__.py", "citation.py", "constraint_set.json", "history.json", _CHARTER,
          "probes/__init__.py", "probes/plaster_is_caught_not_argued.py",
          "probes/the_comparison_is_read.py",
          "proofs/test_corrosion_probes_report_to_the_watch.py", "proofs/test_corrosion_sieve.py",
          "state.json", "validations/test_corrosion_probes_report_to_the_watch.json",
          "validations/test_corrosion_sieve.json")

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _tracked(prefix: str) -> list[str]:
    r = subprocess.run(["git", "ls-files", "--", prefix + "/"], cwd=_REPO,
                       capture_output=True, text=True)
    return [l for l in r.stdout.splitlines() if l.strip()]


def test_the_machine_berths_in_codemother() -> None:
    bad = []
    left = _tracked(OLD)
    if left:
        bad.append(f"{len(left)} tracked file(s) still at the old address: {left[:4]}")
    missing = [f for f in _MOVED if not (_REPO / NEW / f).is_file()]
    if missing:
        bad.append(f"not at the new address: {missing}")
    charter = _REPO / NEW / _CHARTER
    if charter.is_file():
        d = json.loads(charter.read_text(encoding="utf-8"))
        if not str(d.get("owner", "")).startswith("codemother"):
            bad.append(f"owner does not name codemother first: {str(d.get('owner'))[:80]!r}")
        if d.get("gated_by") != GATED_BY_BEFORE:
            bad.append(f"gated_by {d.get('gated_by')!r} != before the move {GATED_BY_BEFORE!r}")
    check("test_the_machine_berths_in_codemother", not bad, "; ".join(bad))


def test_no_class_space_file_names_the_old_address() -> None:
    m = re.escape(_M)
    spellings = [r"(^|[^.\w])cairn\.machines\." + m + r"\b",
                 r"(^|[^/\w])cairn/machines/" + m + r"\b",
                 r"(^|[\s`\"'(])machines/" + m + r"\b",
                 r"\"machines\"\s*/\s*\"" + m + r"\"",
                 r"'machines'\s*/\s*'" + m + r"'"]
    r = subprocess.run(["git", "grep", "--untracked", "-nE", "|".join(spellings), "--", "*.py", "*.json", "bin/*",
                        ":!*.jsonl", ":!*history.json", ":!*state.json", ":!*/validations/*"],
                       cwd=_REPO, capture_output=True, text=True)
    hits = [l for l in r.stdout.splitlines() if l.strip()]
    # devices/codemother/machines/<m> also contains "machines/<m>" — that is the new address.
    hits = [l for l in hits if not all(
        "codemother/machines/" + _M in seg or "codemother.machines." + _M in seg
        for seg in re.findall(r"\S*machines[./]" + m + r"\S*", l))]
    check("test_no_class_space_file_names_the_old_address", r.returncode in (0, 1) and not hits,
          f"{len(hits)} hit(s): " + "; ".join(hits[:8]) if hits else r.stderr.strip())


def test_no_breach_names_the_machine() -> None:
    from cairn.devices.codemother.machines.build_inspector import inspector
    here = os.getcwd()
    os.chdir(_REPO)
    try:
        breaches = inspector.encapsulation_breaches(".")
    finally:
        os.chdir(here)
    named = [b for b in breaches if _M in str(b.get("module")) or _M in str(b.get("target"))
             or _M in str(b.get("source"))]
    check("test_no_breach_names_the_machine", not named,
          "; ".join(f"{b['file']}:{b['line']} {b.get('module')}" for b in named[:8]))


TEETH = (test_the_machine_berths_in_codemother,
         test_no_class_space_file_names_the_old_address,
         test_no_breach_names_the_machine)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
