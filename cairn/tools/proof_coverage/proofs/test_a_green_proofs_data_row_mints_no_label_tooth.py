#!/usr/bin/env python3
"""Proof that proof_coverage's label fallback mints a tooth only from the report words proofs
print as tooth markers (ticket 9ac5f5e882f1).

Measured 2026-11-22: the GREEN seal cairn/devices/cc/validations/test_a_close_over_a_diverged_repo_rebases_or_stops.json
carried teeth_red ['pull: rc 5, named, no crossing, 1 ahead, no rebase left open'], parsed from
its indented data row '    failed pull: rc 5, ...' by _MARKER_LABEL. Over 900 sealed stdout
tails the label markers that occur as tooth markers are ok, pass, green and red (and their
casings); fail is the red a helper prints. So the label fallback resolves its marker against
that set, and any other red- or green-vocabulary word opening a data row mints nothing.

  (1) teeth_printed over that cc seal's stdout_tail returns its 4 test_ teeth green, red empty;
  (2) over every other validations/*.json stdout_tail in the repo, teeth_printed returns the
      same green and red lists as the pre-change parser (copied below as the baseline);
  (3) a label line under ok, pass, green, red or fail still mints its tooth in either indented
      or colon form, and one under failed, error, errored, broken, passed or good mints none.

    PYTHONPATH=. python3 cairn/tools/proof_coverage/proofs/test_a_green_proofs_data_row_mints_no_label_tooth.py
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO))

from cairn.tools.proof_coverage import proof_coverage as pc  # noqa: E402

PROVES = {"9ac5f5e882f1": {
    "1": "test_clause_1_the_cc_data_row_mints_no_red",
    "2": "test_clause_2_every_other_seal_reads_as_before",
    "3": "test_clause_3_only_the_report_words_mint_a_label_tooth",
}}

CC_SEAL = _REPO / "cairn" / "devices" / "cc" / "validations" / "test_a_close_over_a_diverged_repo_rebases_or_stops.json"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


# THE BASELINE: teeth_printed as it stood before this ticket (cairn main at e77c3bc5d), copied
# whole so clause 2 compares against bytes the build cannot reach.
_B_GREEN = frozenset({"ok", "pass", "passed", "green", "good"})
_B_RED = frozenset({"fail", "failed", "red", "error", "errored", "broken"})
_B_FIRST = re.compile(r"^\s*([A-Za-z]+)[\s:]+(test_[A-Za-z0-9_]+)")
_B_LAST = re.compile(r"(test_[A-Za-z0-9_]+)\s+([A-Za-z]+)\s*$")
_B_LABEL = re.compile(r"^(?:[ \t]+([A-Za-z]+)[ \t]+|([A-Za-z]+)[ \t]*:[ \t]+)(\S.*?)[ \t]*$")
_B_PATH = re.compile(r"^(?:/|~[/\\]|[A-Za-z]:[/\\])")


def _baseline(stdout: str) -> dict:
    green: list[str] = []
    red: list[str] = []
    for line in (stdout or "").splitlines():
        for pattern, marker_group, name_group in ((_B_FIRST, 1, 2), (_B_LAST, 2, 1), (_B_LABEL, None, 3)):
            m = pattern.search(line)
            if not m:
                continue
            marker = pc.fold(m.group(marker_group) if marker_group is not None
                             else (m.group(1) or m.group(2)))
            name = m.group(name_group)
            if pattern is _B_LABEL and _B_PATH.match(name):
                break
            if marker in _B_RED:
                red.append(name)
            elif marker in _B_GREEN:
                green.append(name)
            break
    red_set = set(red)
    return {"green": [t for t in dict.fromkeys(green) if t not in red_set],
            "red": list(dict.fromkeys(red))}


def _tails(path: Path) -> list[str]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return []
    out = []
    for rec in doc if isinstance(doc, list) else [doc]:
        tail = (rec.get("evidence") or {}).get("stdout_tail") if isinstance(rec, dict) else None
        if isinstance(tail, str):
            out.append(tail)
    return out


def test_clause_1_the_cc_data_row_mints_no_red() -> None:
    tails = _tails(CC_SEAL)
    got = pc.teeth_printed(tails[-1]) if tails else {"green": [], "red": ["<no stdout_tail>"]}
    want = ["test_a_diverged_commons_is_rebased_and_pushed_or_named",
            "test_a_pull_that_fails_stops_the_close_before_any_crossing",
            "test_a_repo_in_sync_closes_as_before",
            "test_a_commit_that_does_not_land_stops_prove_before_proveme"]
    check("test_clause_1_the_cc_data_row_mints_no_red", got == {"green": want, "red": []},
          f"got {got}")


def test_clause_2_every_other_seal_reads_as_before() -> None:
    seals = [p for p in sorted(_REPO.glob("**/validations/*.json"))
             if p.resolve() != CC_SEAL.resolve() and "/.git/" not in p.as_posix()]
    differ = []
    n = 0
    for p in seals:
        for tail in _tails(p):
            n += 1
            if pc.teeth_printed(tail) != _baseline(tail):
                differ.append(p.relative_to(_REPO).as_posix())
    check("test_clause_2_every_other_seal_reads_as_before", n >= 500 and not differ,
          f"{n} tails read, {len(differ)} differ: {differ[:5]}")


def test_clause_3_only_the_report_words_mint_a_label_tooth() -> None:
    wrong = []
    for word, side in (("ok", "green"), ("pass", "green"), ("PASS", "green"), ("green", "green"),
                       ("GREEN", "green"), ("red", "red"), ("RED", "red"), ("fail", "red"), ("FAIL", "red")):
        for line in (f"    {word}  a labelled tooth", f"{word}: a labelled tooth"):
            got = pc.teeth_printed(line)
            if got[side] != ["a labelled tooth"] or got["green" if side == "red" else "red"]:
                wrong.append((line, got))
    for word in ("failed", "error", "errored", "broken", "passed", "good", "Failed", "ERROR"):
        for line in (f"    {word} a data row: rc 5", f"{word}: a data row"):
            got = pc.teeth_printed(line)
            if got != {"green": [], "red": []}:
                wrong.append((line, got))
    check("test_clause_3_only_the_report_words_mint_a_label_tooth", not wrong, f"wrong: {wrong[:4]}")


if __name__ == "__main__":
    test_clause_1_the_cc_data_row_mints_no_red()
    test_clause_2_every_other_seal_reads_as_before()
    test_clause_3_only_the_report_words_mint_a_label_tooth()
    print(f"{len(FAILURES)} failed" if FAILURES else "all teeth green")
    raise SystemExit(1 if FAILURES else 0)
