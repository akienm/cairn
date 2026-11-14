"""Proof: proof_coverage's label fallback never takes a filesystem path as a tooth label.

Measured 2026-11-14 on origin/main 2889bdd1f: test_proof_coverage.py's
test_NO_GREEN_SEAL_IN_THE_CORPUS_PARSES_TO_A_RED_TOOTH reds on exactly one green seal,
cairn/devices/tester/validations/test_a_host_seam_seals_on_this_box_only.json, whose stdout echoes the
host-seam verifier's own lines ('         red  /tmp/dfe6-.../host-testing-dfe6c1432fc8.json on
akiendelllinux': a verify that is MEANT to seal red). The label pattern read the path as a red tooth.
Adjudicated: the invariant tooth is right (a reader may not manufacture a red from a green proof's
output), the seal's echo is data, and the parser's own anchor is 'a report, not a sentence': a path is
no tooth label.

  1. an indented marker line whose label is a path (POSIX, home, or drive-letter) mints no tooth.
  2. a genuine indented tooth, a colon-form tooth and a test_-named tooth still read as before.
  3. over the repo's real seals no GREEN seal's stdout_tail parses to a red tooth.
  4. a RELATIVE path echo ('  red  cairn/x.json on box', yoga's review) mints no tooth, and a label with a
     slash but no file extension ('a/b tests pass') still does.

    python3 cairn/tools/proof_coverage/proofs/test_a_path_is_not_a_tooth_label.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"8f5ab45e64c5": {
    "1": "test_a_path_label_mints_no_tooth",
    "2": "test_a_real_tooth_still_reads_as_before",
    "3": "test_no_green_seal_in_the_corpus_parses_to_a_red_tooth",
    "4": "test_a_relative_path_label_mints_no_tooth_and_a_slash_in_a_sentence_still_does",
}}


def test_a_path_label_mints_no_tooth():
    from cairn.tools.proof_coverage import proof_coverage as pc
    out = "\n".join([
        "         red  /tmp/x/host-testing.json on akiendelllinux",
        "  red  C:\\Users\\akien\\x.json",
        "  red  ~/seal.json",
        "  green  D:/a/b.json",
    ])
    assert pc.teeth_printed(out) == {"green": [], "red": []}, pc.teeth_printed(out)


def test_a_real_tooth_still_reads_as_before():
    from cairn.tools.proof_coverage import proof_coverage as pc
    out = "\n".join([
        "  red  the backdate refusal",
        "  ok   the backdate refusal wrote no slate",
        "FAIL: a unified line",
        "  ok   test_a_named_tooth",
        "  red  /tmp/x/host.json on box",
        "  ok   a label that merely mentions /tmp/x later",
    ])
    got = pc.teeth_printed(out)
    assert got["red"] == ["the backdate refusal", "a unified line"], got
    assert got["green"] == ["the backdate refusal wrote no slate", "test_a_named_tooth",
                            "a label that merely mentions /tmp/x later"], got


def test_no_green_seal_in_the_corpus_parses_to_a_red_tooth():
    from cairn.tools.proof_coverage import proof_coverage as pc
    bad = []
    for v in sorted(REPO.rglob("validations/*.json")):
        try:
            d = json.loads(v.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        rec = d[0] if isinstance(d, list) else d
        if not isinstance(rec, dict) or rec.get("verdict") != "green":
            continue
        tail = (rec.get("evidence") or {}).get("stdout_tail") or ""
        if tail and pc.teeth_printed(tail)["red"]:
            bad.append((str(v.relative_to(REPO)), pc.teeth_printed(tail)["red"][:3]))
    assert not bad, f"a GREEN seal's own output parses to a red tooth: {bad[:5]}"


def test_a_relative_path_label_mints_no_tooth_and_a_slash_in_a_sentence_still_does():
    from cairn.tools.proof_coverage import proof_coverage as pc
    out = "\n".join([
        "  red  cairn/x.json on box",
        "  red  a\\b\\c.txt",
        "  ok   cairn/devices/y.py sealed",
        "  red  a/b tests pass",
        "  ok   the v1.2 migration holds",
    ])
    got = pc.teeth_printed(out)
    assert got == {"green": ["the v1.2 migration holds"], "red": ["a/b tests pass"]}, got


TEETH = [test_a_path_label_mints_no_tooth, test_a_real_tooth_still_reads_as_before,
         test_no_green_seal_in_the_corpus_parses_to_a_red_tooth,
         test_a_relative_path_label_mints_no_tooth_and_a_slash_in_a_sentence_still_does]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  RED  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"{'GREEN' if not failed else 'RED'} - {len(TEETH) - failed}/{len(TEETH)} teeth")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
