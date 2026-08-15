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

Invariants over live state, never snapshots: no match list is pinned, no file
content is pinned — only "zero shapes stand" and "every cite's snippet stands".

    python3 cairn/tools/intentions_model_compiler/proofs/test_present_tense_sweep.py  # exit 0 = green
"""

from __future__ import annotations

import json
import re
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
    cites = 0
    for p in pairs:
        missing = {"path", "line", "matched", "shape", "judgment", "disposition"} - set(p)
        assert not missing, f"tooth (ii) RED: pair missing {missing}: {p}"
        assert p["judgment"] in ("narrate", "cite"), p["judgment"]
        if p["judgment"] != "cite":
            continue
        cites += 1
        artifact = (_REPO_ROOT / p["path"]).read_text()
        spans = re.findall(r'"([^"]{8,})"', p["disposition"]) + re.findall(
            r"'([^']{8,})'", p["disposition"]
        )
        assert spans, (
            f"tooth (ii) RED: cite pair at {p['path']}:{p['line']} carries no quoted "
            "surviving snippet in its disposition — an unverifiable stand"
        )
        assert any(s in artifact for s in spans), (
            f"tooth (ii) RED: cite at {p['path']}:{p['line']} — no quoted span from its "
            f"disposition exists in the artifact; the stand it recorded is gone: {spans!r}"
        )
    print(
        f"tooth (ii) green: 0 matches over {r['artifacts_scanned']} artifacts, "
        f"{len(pairs)} pairs ({cites} cites, every snippet standing)"
    )


if __name__ == "__main__":
    tooth_i_scanner_detects_a_planted_narration()
    tooth_ii_zero_live_and_every_cite_stands()
    print("GREEN: the present-tense corpus carries no dated appends, and every judgment is on record")
