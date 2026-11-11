"""Proof for ticket the-present-tense-corpus-rewrites-once — the one-time sweep.

The claim under test: the present-tense set (every cairn intention+why.json,
CLAUDE.md, MAP.md) carries ZERO standing dated-append shapes, and every one of
the 120 matches the sweep started from carries a recorded narrate|cite judgment
in the pairs store — with every cite's surviving snippet still present in its
artifact, so a cite is a reformatted stand, never a silent exemption.

Teeth a hollow sweep could not pass:

  - NON-VACUITY (tooth i). A planted narrating fixture — carrying all three v0
    shapes (bare RETIRED, "formerly", an open-paren date) — is detected by the
    probe's own scanner. A sweep that went green because the scanner broke (an
    empty pattern list, a scan that reads no lines) trips this: the zero below
    is only evidence while this tooth bites. Mutation check: disable _PLANT and
    this tooth reds.
  - THE ZERO IS LIVE AND THE JUDGMENTS ARE WHOLE (tooth ii). survey_the_corpus()
    returns zero matches over the live set; the pairs store holds >= 120 pairs,
    each well-formed (path, line, matched, shape, judgment in {narrate, cite},
    disposition); and for every CITE pair, a quoted span from its disposition
    still exists verbatim in the artifact it stands in. A cite whose snippet is
    gone is a judgment about text that no longer exists — narration (Law 3).
    A cite whose ARTIFACT is gone stands only when git records the commit that
    deleted it (ticket c5875eb0d2d3): the deletion is the history, kept and
    greppable (Law 5), and nothing present-tense remains to contradict.
  - A CITE STANDS ONLY WHERE ITS BYTES OR THEIR DELETION ARE ON RECORD (tooth iii).
    In a scratch git repo, _cite_red stands a committed-then-deleted path, and reds
    a path never tracked and a present artifact without its snippet — so the
    deletion rule cannot exempt whatever happens to be missing.

Invariants over live state, never snapshots: no match list is pinned, no file
content is pinned — only "zero shapes stand" and "every cite's snippet stands".

    python3 cairn/tools/intentions_model_compiler/proofs/test_present_tense_sweep.py  # exit 0 = green
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.intentions_model_compiler.probes.present_tense_artifacts_carry_no_dated_appends import (  # noqa: E402
    _matches_in,
    survey_the_corpus,
)

_PAIRS = Path(__file__).resolve().parents[1] / "probes" / "dated_append_judgments.json"

PROVES = {
    "c5875eb0d2d3": {
        "1": "tooth_ii_zero_live_and_every_cite_stands",
        "2": "tooth_iii_a_cite_stands_only_where_its_bytes_or_their_deletion_are_on_record",
        "3": "tooth_iii_a_cite_stands_only_where_its_bytes_or_their_deletion_are_on_record",
    },
}

GONE = "gone"


def _cite_red(p: dict, root: Path):
    """Why this cite pair does not stand, or None when it stands — GONE when its artifact
    is absent and git under ``root`` records the commit that deleted it."""
    path = root / p["path"]
    if not path.is_file():
        out = subprocess.run(["git", "-C", str(root), "log", "--diff-filter=D", "--format=%h",
                              "--", p["path"]], capture_output=True, text=True)
        if out.returncode == 0 and out.stdout.strip():
            return GONE
        return (f"cite at {p['path']}:{p['line']} — the artifact is absent and no commit "
                f"records its deletion (git: {out.stderr.strip() or 'no deleting commit'})")
    spans = re.findall(r'"([^"]{8,})"', p["disposition"]) + re.findall(
        r"'([^']{8,})'", p["disposition"]
    )
    if not spans:
        return (f"cite pair at {p['path']}:{p['line']} carries no quoted surviving snippet "
                "in its disposition — an unverifiable stand")
    artifact = path.read_text(encoding="utf-8")
    if not any(s in artifact for s in spans):
        return (f"cite at {p['path']}:{p['line']} — no quoted span from its disposition exists "
                f"in the artifact; the stand it recorded is gone: {spans!r}")
    return None

# Mutation check flips this to False: the fixture goes unplanted, the scanner
# finds nothing, and tooth (i) must red — proving the tooth is not vacuous.
_PLANT = True

_FIXTURE = (
    "edge (q) RETIRED 2026-08-09 (ticket some-ticket): the thing formerly\n"
    "known as the widget was replaced (2026-08-05, when the registry died).\n"
)


def tooth_i_scanner_detects_a_planted_narration() -> None:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        if _PLANT:
            f.write(_FIXTURE)
        planted = Path(f.name)
    try:
        found = _matches_in(planted)
        assert found, "tooth (i) RED: the scanner found nothing in a narrating fixture"
        texts = " ".join(m["matched"] for m in found)
        for shape in ("RETIRED", "formerly", "(2026-"):
            assert shape in texts, (
                f"tooth (i) RED: shape {shape!r} planted but not detected — "
                f"scanner is blind to one of its own patterns (found: {texts!r})"
            )
    finally:
        planted.unlink()
    print(f"tooth (i) green: planted fixture detected ({len(found)} matches, all three shapes)")


def tooth_ii_zero_live_and_every_cite_stands() -> None:
    r = survey_the_corpus()
    assert r["matches"] == [], (
        f"tooth (ii) RED: {len(r['matches'])} dated-append shape(s) still standing: "
        + json.dumps(r["matches"][:5])
    )
    assert r["artifacts_scanned"] >= 50, (
        f"tooth (ii) RED: only {r['artifacts_scanned']} artifacts scanned — "
        "the present-tense set shrank; a zero over a vanished corpus proves nothing"
    )

    store = json.loads(_PAIRS.read_text())
    pairs = store["pairs"]
    assert len(pairs) >= 120, (
        f"tooth (ii) RED: {len(pairs)} pairs recorded, sweep started from 120 matches"
    )
    cites = gone = 0
    for p in pairs:
        missing = {"path", "line", "matched", "shape", "judgment", "disposition"} - set(p)
        assert not missing, f"tooth (ii) RED: pair missing {missing}: {p}"
        assert p["judgment"] in ("narrate", "cite"), p["judgment"]
        if p["judgment"] != "cite":
            continue
        cites += 1
        red = _cite_red(p, _REPO_ROOT)
        if red == GONE:
            gone += 1
            continue
        assert red is None, f"tooth (ii) RED: {red}"
    print(
        f"tooth (ii) green: 0 matches over {r['artifacts_scanned']} artifacts, "
        f"{len(pairs)} pairs ({cites} cites: {cites - gone} snippets standing, "
        f"{gone} on an artifact a commit deleted)"
    )


def tooth_iii_a_cite_stands_only_where_its_bytes_or_their_deletion_are_on_record() -> None:
    with tempfile.TemporaryDirectory(prefix="c587-cite-") as tmp:
        root = Path(tmp)

        def git(*a):
            subprocess.run(["git", "-C", tmp, "-c", "user.name=t", "-c", "user.email=t@t",
                            "-c", "commit.gpgsign=false", *a], check=True, capture_output=True)

        git("init", "-q")
        (root / "deleted.json").write_text('"the snippet that stood here"\n')
        (root / "present.json").write_text('"some other words entirely"\n')
        git("add", "-A")
        git("commit", "-qm", "both")
        git("rm", "-q", "deleted.json")
        git("commit", "-qm", "delete one")
        cite = "stands: 'the snippet that stood here'"
        pair = lambda path: {"path": path, "line": 1, "disposition": cite}  # noqa: E731
        got = _cite_red(pair("deleted.json"), root)
        assert got == GONE, f"tooth (iii) RED: a committed-then-deleted artifact read {got!r}"
        got = _cite_red(pair("never-tracked.json"), root)
        assert got not in (None, GONE), (
            f"tooth (iii) RED: a path never tracked in git stood ({got!r})")
        got = _cite_red(pair("present.json"), root)
        assert got not in (None, GONE), (
            f"tooth (iii) RED: a present artifact without its snippet stood ({got!r})")
    print("tooth (iii) green: a deletion on record stands; a never-tracked path and a lost "
          "snippet red")


if __name__ == "__main__":
    tooth_i_scanner_detects_a_planted_narration()
    tooth_ii_zero_live_and_every_cite_stands()
    tooth_iii_a_cite_stands_only_where_its_bytes_or_their_deletion_are_on_record()
    print("GREEN: the present-tense corpus carries no dated appends, and every judgment is on record")
