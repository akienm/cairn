"""PROOF — show and get resolve through declared_views() using the same dict-lookup pattern.

The universal query verbs: ``get`` returns JSON for machine consumption, ``show``
renders human-readable text. Both resolve what data to produce through
``declared_views()`` — same pattern as verb dispatch, different table.

What a hollow build cannot pass (Law 8):
  - One that hard-coded the view data passes every content check and fails
    test_get_resolves_through_declared_views, which adds a view at runtime and
    checks that get finds it — a hard-coded return cannot pick up the new entry.
  - One that returned data without rendering passes get tests and fails
    test_show_renders_text, which checks the text field is a string produced
    by _render_view.
  - One that accepted any view name passes the happy path and fails
    test_unknown_view_refuses, which checks the refusal shape.

    python3 cairn/tools/base/proofs/test_views.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.device import BaseDevice  # noqa: E402


class ViewDevice(BaseDevice):
    """A device that declares views — the smallest honest view provider."""

    def __init__(self) -> None:
        super().__init__()
        self._views = {"status": self._status_view}
        self._device_id = "view_test"

    @property
    def device_id(self) -> str:
        return self._device_id

    def intention(self) -> dict:
        return {"what": "proof device with views"}

    def state(self) -> dict:
        return {"at": "running"}

    def settings(self) -> dict:
        return {}

    def declared_views(self) -> dict:
        return dict(self._views)

    def _status_view(self) -> dict:
        return {"healthy": True, "uptime": 42}


class RenderedDevice(ViewDevice):
    """A device that overrides _render_view for pretty output."""

    def _render_view(self, name: str, data: dict) -> str:
        if name == "status":
            return f"Healthy: {data['healthy']}, Uptime: {data['uptime']}s"
        return super()._render_view(name, data)


def _envelope(verb: str, what: str) -> dict:
    return {"id": "test", "sender": "proof", "to": "test_device",
            "verb": verb, "body": {"what": what}}


# --- teeth ------------------------------------------------------------------

def test_get_resolves_through_declared_views():
    """get looks up the view name in declared_views() and returns its data.
    A hard-coded return fails here because a view added at runtime appears."""
    dev = ViewDevice()
    result = dev._handle_get(_envelope("get", "status"))
    assert result["accepted"] is True
    assert result["data"] == {"healthy": True, "uptime": 42}
    assert result["view"] == "status"
    dev._views["extra"] = lambda: {"n": 1}
    result2 = dev._handle_get(_envelope("get", "extra"))
    assert result2["accepted"] is True
    assert result2["data"] == {"n": 1}


def test_show_resolves_through_declared_views():
    """show resolves the same view and returns both text and data."""
    dev = ViewDevice()
    result = dev._handle_show(_envelope("show", "status"))
    assert result["accepted"] is True
    assert result["data"] == {"healthy": True, "uptime": 42}
    assert isinstance(result["text"], str)
    assert len(result["text"]) > 0


def test_show_renders_text():
    """A device that overrides _render_view gets its custom text in show."""
    dev = RenderedDevice()
    result = dev._handle_show(_envelope("show", "status"))
    assert result["text"] == "Healthy: True, Uptime: 42s"


def test_unknown_view_refuses():
    """An unknown view is an honest refusal, not a crash."""
    dev = ViewDevice()
    result = dev._handle_get(_envelope("get", "nonexistent"))
    assert result["accepted"] is False
    assert "nonexistent" in result["reason"]
    assert "status" in result["available"]


def test_show_and_get_share_the_same_table():
    """Both verbs resolve through the SAME declared_views() — not two tables."""
    dev = ViewDevice()
    get_result = dev._handle_get(_envelope("get", "status"))
    show_result = dev._handle_show(_envelope("show", "status"))
    assert get_result["data"] == show_result["data"]


def test_device_with_no_views_refuses_honestly():
    """A device that declares no views refuses show and get — empty is honest."""

    class BareDev(BaseDevice):
        @property
        def device_id(self): return "bare_test"
        def intention(self): return {}
        def state(self): return {}
        def settings(self): return {}

    dev = BareDev()
    result = dev._handle_get(_envelope("get", "anything"))
    assert result["accepted"] is False
    assert result["available"] == []


def test_base_verbs_include_show_and_get():
    """Every device inherits show and get as declared verbs."""
    dev = ViewDevice()
    verbs = dev.declared_verbs()
    assert "show" in verbs
    assert "get" in verbs
    assert callable(verbs["show"])
    assert callable(verbs["get"])


if __name__ == "__main__":
    checks = [
        test_get_resolves_through_declared_views,
        test_show_resolves_through_declared_views,
        test_show_renders_text,
        test_unknown_view_refuses,
        test_show_and_get_share_the_same_table,
        test_device_with_no_views_refuses_honestly,
        test_base_verbs_include_show_and_get,
    ]
    failures = 0
    for check in checks:
        try:
            check()
            print(f"  PASS  {check.__name__}")
        except Exception as exc:  # noqa: BLE001
            failures += 1
            print(f"  FAIL  {check.__name__}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — show and get resolve through declared_views(), "
          "same pattern, different table")
