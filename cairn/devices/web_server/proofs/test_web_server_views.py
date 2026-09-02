"""Proof for web_server view kinds and bounded panes (ticket a-pane-declares-its-view).

Teeth a hollow build could not pass:
  - RECORD renders as a <dl> (definition list), not <pre>.
  - TABLE renders as an <table>, not <pre>.
  - SEQUENCE renders as an <ol>, not <pre>.
  - TREE renders as nested <details>/<summary>, not <pre>.
  - SCALAR renders as a <span>, not <pre>.
  - UNKNOWN KIND falls back to <pre> with pretty JSON.
  - BOUNDED PANE shows 'showing N of M' when count > len(window).
  - BOUNDED PANE renders prev/next pager anchors with cursor query params.
  - ALL renderers escape device-derived strings (_esc applied).

Runnable bare (NO socket, NO DB, NO framework):
    python3 cairn/devices/web_server/proofs/test_web_server_views.py   # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.web_server.render import render_pane


def test_record_renders_as_dl():
    pane = {"kind": "record", "label": "Config", "data": {"host": "localhost", "port": 8080}}
    html = render_pane(pane)
    assert "<dl" in html, "record renders as a <dl>"
    assert "<dt>" in html and "<dd>" in html, "record has dt/dd pairs"
    assert "<pre>" not in html, "record does NOT fall through to <pre>"
    assert "localhost" in html and "8080" in html, "record data is rendered"
    assert 'data-kind="record"' in html, "data-kind attribute is record"


def test_table_renders_as_table():
    pane = {"kind": "table", "label": "Devices",
            "data": [{"name": "alpha", "awake": True}, {"name": "beta", "awake": False}]}
    html = render_pane(pane)
    assert "<table>" in html, "table renders as a <table>"
    assert "<th>" in html, "table has header cells"
    assert "<td>" in html, "table has data cells"
    assert "<pre>" not in html, "table does NOT fall through to <pre>"
    assert "alpha" in html and "beta" in html, "table data is rendered"
    assert 'data-kind="table"' in html, "data-kind attribute is table"


def test_sequence_renders_as_ol():
    pane = {"kind": "sequence", "label": "Log", "data": ["started", "loaded", "ready"]}
    html = render_pane(pane)
    assert "<ol" in html, "sequence renders as an <ol>"
    assert "<li>" in html, "sequence has list items"
    assert "<pre>" not in html, "sequence does NOT fall through to <pre>"
    assert "started" in html and "ready" in html, "sequence data is rendered"
    assert 'data-kind="sequence"' in html, "data-kind attribute is sequence"


def test_tree_renders_as_details():
    pane = {"kind": "tree", "label": "Config",
            "data": {"server": {"host": "localhost", "port": 8080}, "debug": True}}
    html = render_pane(pane)
    assert "<details" in html, "tree renders nested <details>"
    assert "<summary>" in html, "tree has summary elements"
    assert "<pre>" not in html, "tree does NOT fall through to <pre>"
    assert "server" in html and "localhost" in html, "tree data is rendered"
    assert 'data-kind="tree"' in html, "data-kind attribute is tree"


def test_scalar_renders_as_span():
    pane = {"kind": "scalar", "label": "Count", "data": 42}
    html = render_pane(pane)
    assert '<span class="scalar">' in html, "scalar renders as a <span>"
    assert "<pre>" not in html, "scalar does NOT fall through to <pre>"
    assert "42" in html, "scalar data is rendered"
    assert 'data-kind="scalar"' in html, "data-kind attribute is scalar"


def test_unknown_kind_falls_back_to_pre():
    pane = {"kind": "unknown_thing", "label": "Mystery", "data": {"x": 1}}
    html = render_pane(pane)
    assert "<pre>" in html, "unknown kind falls back to <pre>"
    assert "<dl" not in html and "<table>" not in html, "unknown kind does NOT dispatch to a view"
    assert 'data-kind="unknown_thing"' in html, "data-kind attribute is preserved"


def test_bounded_pane_shows_window_meta():
    pane = {"kind": "sequence", "label": "Log",
            "data": [1, 2, 3], "count": 10, "window": [1, 2, 3], "cursor": 0}
    html = render_pane(pane)
    assert "showing 3 of 10" in html, "bounded pane shows 'showing N of M'"


def test_bounded_pane_renders_pager():
    pane = {"kind": "sequence", "label": "Log",
            "data": [6, 7, 8, 9, 10], "count": 20, "window": [6, 7, 8, 9, 10], "cursor": 5}
    html = render_pane(pane, base_path="/device/cairn/0")
    assert "cursor=" in html, "bounded pane renders pager with cursor query param"
    assert "<a " in html, "pager uses anchor elements"
    assert "prev" in html.lower(), "pager has a prev link (cursor > 0)"
    assert "next" in html.lower(), "pager has a next link (more items ahead)"


def test_all_renderers_escape_device_strings():
    hostile = "<script>alert(1)</script>"
    for kind in ("record", "table", "sequence", "tree", "scalar", "unknown"):
        if kind == "record":
            data = {hostile: hostile}
        elif kind in ("table",):
            data = [{hostile: hostile}]
        elif kind in ("sequence",):
            data = [hostile]
        elif kind == "tree":
            data = {hostile: hostile}
        else:
            data = hostile
        pane = {"kind": kind, "label": "test", "data": data}
        html = render_pane(pane)
        assert "<script>" not in html, f"kind={kind}: device string was NOT escaped"
        assert "&lt;script&gt;" in html, f"kind={kind}: device string IS escaped"


# ---------------------------------------------------------------------------

_TEETH = [fn for name, fn in sorted(locals().items()) if name.startswith("test_")]


def _run():
    failed = 0
    for fn in _TEETH:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except Exception as exc:
            print(f"  FAIL  {fn.__name__}: {exc}")
            failed += 1
    if failed:
        print(f"RED — {failed} tooth/teeth failed")
        sys.exit(1)
    print(f"green — web_server/views: {len(_TEETH)} teeth, all view kinds dispatch to "
          f"their own renderer, unknown falls back to <pre>, bounded panes show metadata "
          f"and pager, all device strings escaped")


if __name__ == "__main__":
    _run()
