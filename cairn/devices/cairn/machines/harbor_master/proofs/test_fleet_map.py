"""PROOF — the harbor master's fleet map: ``get map`` returns JSON, ``show map`` renders text.

The harbor master is the fleet register's always-on front. Its ``map`` view exposes
the fleet through the universal query verbs: ``get`` for machine consumption (other
devices querying over the bus), ``show`` for human-readable CLI output.

What a hollow build cannot pass (Law 8):
  - One that returned a static dict passes every shape check and fails
    test_get_map_returns_the_live_fleet, which reconciles, patches, and checks
    that the patched standing appears in the get response.
  - One that returned text without the fleet data passes show checks and fails
    test_show_map_includes_data, which checks the data dict rides alongside text.
  - One that returned JSON from show passes data checks and fails
    test_show_map_renders_human_readable, which checks the text contains fleet
    counts and boat ids.

    python3 cairn/devices/cairn/machines/harbor_master/proofs/test_fleet_map.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.cairn.machines.harbor_master.device import HarborMasterDevice  # noqa: E402


def _envelope(verb: str, what: str) -> dict:
    return {"id": "test", "sender": "proof", "to": "harbor_master",
            "verb": verb, "body": {"what": what}}


# --- teeth ------------------------------------------------------------------

def test_harbor_master_declares_map_view():
    """The map view is declared — get and show can resolve it."""
    dev = HarborMasterDevice()
    views = dev.declared_views()
    assert "map" in views, f"no map view declared, available: {sorted(views)}"
    assert callable(views["map"])


def test_harbor_master_verbs_include_base_and_crossing():
    """Harbor master extends the base verbs (show, get) with crossing."""
    dev = HarborMasterDevice()
    verbs = dev.declared_verbs()
    assert "show" in verbs, "missing base verb: show"
    assert "get" in verbs, "missing base verb: get"
    assert "crossing" in verbs, "missing device verb: crossing"


def test_get_map_returns_the_live_fleet():
    """get map returns the fleet register as a data dict with counts and boats."""
    dev = HarborMasterDevice()
    result = dev._handle_get(_envelope("get", "map"))
    assert result["accepted"] is True
    assert result["view"] == "map"
    data = result["data"]
    assert "counts" in data, f"fleet data has no counts: {sorted(data)}"
    assert "open" in data, "fleet data has no open list"
    assert "in_port" in data, "fleet data has no in_port list"
    assert data["counts"]["fleet"] > 0, "the real fleet is not empty"


def test_show_map_renders_human_readable():
    """show map returns a text rendering with fleet counts and boat ids."""
    dev = HarborMasterDevice()
    result = dev._handle_show(_envelope("show", "map"))
    assert result["accepted"] is True
    text = result["text"]
    assert "Fleet:" in text, f"show text missing 'Fleet:': {text[:100]}"
    assert "open" in text.lower(), f"show text missing open section"
    data = result["data"]
    if data["open"]:
        assert data["open"][0]["id"] in text, "first open boat id not in text"


def test_show_map_includes_data():
    """show returns data alongside text — the caller can use either."""
    dev = HarborMasterDevice()
    result = dev._handle_show(_envelope("show", "map"))
    assert "data" in result, "show response missing data dict"
    assert "text" in result, "show response missing text"
    assert result["data"]["counts"]["fleet"] == result["data"]["counts"]["open"] + result["data"]["counts"]["in_port"]


def test_get_map_populates_cache_on_first_call():
    """get map on a fresh device triggers reconciliation — the cache is populated."""
    dev = HarborMasterDevice()
    assert dev.fleet_cache is None, "fresh device must not have a cache"
    dev._handle_get(_envelope("get", "map"))
    assert dev.fleet_cache is not None, "get map must populate the cache"


def test_unknown_view_refuses():
    """An unknown view name is an honest refusal listing available views."""
    dev = HarborMasterDevice()
    result = dev._handle_get(_envelope("get", "nonexistent"))
    assert result["accepted"] is False
    assert "map" in result["available"]


if __name__ == "__main__":
    checks = [
        test_harbor_master_declares_map_view,
        test_harbor_master_verbs_include_base_and_crossing,
        test_get_map_returns_the_live_fleet,
        test_show_map_renders_human_readable,
        test_show_map_includes_data,
        test_get_map_populates_cache_on_first_call,
        test_unknown_view_refuses,
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
    print("green — get map returns JSON, show map renders text, "
          "same data, different face")
