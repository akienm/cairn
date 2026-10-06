"""Proof: the trouble pane's detail side shows the whole finding on select, and the panel
says it is read-only (ticket 1cafb10c2983, child of 7a1265439f54 for its clauses (4)/(5)).

MEASURED RED 2026-10-06, the reason this file exists: ``_render_trouble`` rendered the
detail side as a static "Select a trouble from the list." that nothing ever filled — the
page carries no script — and the only copy of a trouble's ``why`` sat in a list cell
clipped by ``text-overflow: ellipsis``. So the full finding was never on the page, and
7a1265439f54's 2026-09-04 PROVED stood over two clauses that were never true. Selecting is
a plain anchor: the list's id links to ``#trouble-<id>`` and CSS ``:target`` shows that
one section, which keeps the page script-free.

Teeth a hollow build could not pass:
  1. a 3,000-char why appears WHOLE (escaped) inside the detail side, in a section whose id
     the list row links to;
  2. the detail sections are hidden until selected and shown by ``:target`` — selection,
     not a wall of every finding at once;
  3. the panel says, in visible text, that it is read-only.

Runnable bare: ``python3 cairn/devices/web_server/proofs/test_the_trouble_pane_shows_the_whole_finding.py``
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "1cafb10c2983": {
        "1": "test_the_detail_holds_the_WHOLE_finding_of_the_selected_trouble",
        "2": "test_a_finding_shows_only_when_SELECTED",
        "3": "test_the_panel_SAYS_it_is_read_only",
    },
}

_LONG = "a<b & " + ("the full finding, every word of it; " * 90)


def _html():
    from cairn.devices.web_server.render import render_pane
    return render_pane({"kind": "trouble", "label": "troubles", "data": [
        {"id": "t-long", "standing": "OPEN", "why": _LONG, "count": 2,
         "first_seen": "2026-10-01T00:00:00Z", "last_seen": "2026-10-06T00:00:00Z"},
        {"id": "t-short", "standing": "OPEN", "why": "short", "count": 1}]})


def _detail(html: str) -> str:
    m = re.search(r'<div class="trouble-detail">(.*)</div></div></div>', html, re.S)
    assert m, f"no trouble-detail side in: {html[-400:]!r}"
    return m.group(1)


def test_the_detail_holds_the_WHOLE_finding_of_the_selected_trouble():
    from cairn.devices.web_server.render import _esc
    html = _html()
    assert 'href="#trouble-t-long"' in html, "the list row does not link to its detail"
    detail = _detail(html)
    m = re.search(r'<section id="trouble-t-long"[^>]*>(.*?)</section>', detail, re.S)
    assert m, f"no detail section for t-long in the detail side: {detail[:300]!r}"
    assert _esc(_LONG) in m.group(1), "the detail section does not carry the finding WHOLE"


def test_a_finding_shows_only_when_SELECTED():
    from cairn.devices.web_server.render import _STYLE
    css = re.sub(r"\s+", " ", _STYLE)
    assert re.search(r"\.trouble-full \{[^}]*display: none", css), (
        "detail sections are not hidden until selected")
    assert re.search(r"\.trouble-full:target \{[^}]*display: block", css), (
        "a selected detail section is not shown by :target")
    assert _html().count('class="trouble-full"') == 2, "not one detail section per trouble"


def test_the_panel_SAYS_it_is_read_only():
    text = re.sub(r"<[^>]+>", " ", _html()).lower()
    assert "read-only" in text, "nothing on the panel says it is read-only"


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
