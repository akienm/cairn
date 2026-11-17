"""Proof for ticket dd0f3e0e7225 — the commons md intentions fold into the schematic.

The teeth, one per clause:

  1. 19-the-roots.md is a piece TOC.md names, and it carries every CORE_VALUES narrative and
     why, whitespace-normalised;
  2. no .md remains in CairnCommons/intentions-not-beside-code/;
  3. no tracked cairn file outside validations/ and history.json names
     intentions-not-beside-code/<a folded name>.md (a scratch fixture that writes its own copy
     never spells the joined path);
  4. test_core_values reads its record from cairn/devices/cairn/requirements/19-the-roots.md.
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))
REQ = REPO / "cairn" / "devices" / "cairn" / "requirements"
ROOTS = REQ / "19-the-roots.md"
FOLDER = REPO.parent / "CairnCommons" / "intentions-not-beside-code"

PROVES = {
    "dd0f3e0e7225": {
        "1": "test_the_roots_piece_is_named_and_carries_every_core_value",
        "2": "test_no_md_remains_in_the_commons_intentions_folder",
        "3": "test_nothing_tracked_points_at_a_folded_md",
        "4": "test_core_values_reads_the_roots_piece",
    },
}

# the names folded, by stem. A scratch fixture that writes its own copy joins the folder
# name and the file name with os.path.join or '/', so the pattern never matches it.
FOLDED = [
    "telos", "core-values", "review-cc-patterns-for-cognition-gates",
    "I-a-dated-append-in-a-charter-is-a-red", "I-a-ticket-is-a-plan-and-a-log",
    "I-a-ticket-is-decisions-not-prose",
    "I-an-approved-proofs-only-build-crosses-proved-on-his-word",
    "I-an-artifact-is-present-tense-or-past-tense-never-both",
    "I-an-unfillable-request-is-a-counted-trouble-at-the-receiver",
    "I-an-unvouched-green-completes-and-notifies", "I-cairn-claude-md",
    "I-cognition-domains-general-coding-research", "I-complete-diagnostic-on-first-pass",
    "I-heartbeat-probes-and-bus", "I-learns-its-gates", "I-orient-is-a-universal-qualified-verb",
    "I-prebuild-cognition-compiles", "I-rule-1-encapsulation",
    "I-the-briefing-surface-is-charter-plus-state-never-history", "I-the-cairn-device",
    "I-the-cheapest-reader-proves-a-ticket-before-it-is-built",
    "I-the-command-lazy-inits-the-system", "I-the-system-is-a-learning-block",
    "I-the-vision-that-guides-every-decision", "I-ticket-and-task",
    "I-universal-addressing-and-bidirectional-links",
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def test_the_roots_piece_is_named_and_carries_every_core_value():
    from cairn.tools.base.core_values import CORE_VALUES
    toc = (REQ / "TOC.md").read_text(encoding="utf-8")
    assert "](19-the-roots.md)" in toc, "TOC.md does not name 19-the-roots.md"
    text = _norm(ROOTS.read_text(encoding="utf-8"))
    for v in CORE_VALUES:
        assert _norm(v.narrative) in text, (v.id, v.narrative)
        assert _norm(v.why) in text, (v.id, v.why)


def test_no_md_remains_in_the_commons_intentions_folder():
    left = sorted(p.name for p in FOLDER.glob("*.md")) if FOLDER.is_dir() else []
    assert left == [], left


def test_nothing_tracked_points_at_a_folded_md():
    pat = "intentions-not-beside-code/(" + "|".join(map(re.escape, FOLDED)) + r")\.md"
    out = subprocess.run(["git", "-C", str(REPO), "grep", "-nE", pat], capture_output=True,
                         text=True)
    assert out.returncode in (0, 1), out.stderr
    hits = []
    for line in out.stdout.splitlines():
        path = line.split(":", 1)[0]
        if "/validations/" in path or path.endswith("history.json"):
            continue
        hits.append(line[:200])
    assert hits == [], hits


def test_core_values_reads_the_roots_piece():
    import importlib
    sys.modules.pop("cairn.tools.base.proofs.test_core_values", None)
    m = importlib.import_module("cairn.tools.base.proofs.test_core_values")
    assert Path(m._COMMONS_RECORD).resolve() == ROOTS.resolve(), m._COMMONS_RECORD
    m.test_code_matches_the_commons_record()
    assert m._drift_gate_ran, "the drift gate abstained: it did not read the roots piece"


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
    print("green — 4 teeth: the roots piece carries the core values, the commons folder holds no md, "
          "nothing points at one, and the core values pin reads the roots piece")
    return 0


if __name__ == "__main__":
    sys.exit(main())
