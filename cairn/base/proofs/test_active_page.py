"""Proof for the web presentation surface's DATA machinery (web-server ticket, child a).

A device's ACTIVE page is a stack of standard PANES. The assembly is STANDARD machinery
in ``BaseShim.active_page`` — not in each device (Law 6) and not in the web server (which
only renders). A device gets the STATUS + SETTINGS floor for free (projected from
``introspect()``, Form v0 #2) and DECLARES any extra panes with a handler that returns DATA.

Teeth a hollow build could not pass:
  - THE FLOOR IS ALWAYS THERE: a device declaring no extras yields exactly [status, settings],
    STATUS carrying the reported intention+state, SETTINGS carrying the settings — pulled live
    from the device's own introspect(), not stored on the shim.
  - DECLARED PANES ARE APPENDED IN ORDER, and MULTIPLES OF A KIND ARE ALLOWED (two interaction
    panes both render — the librarian's chat-page + tool-page fall out, not a special case).
  - AN OFFERED PANE WITH NO HANDLER RENDERS ABSENT (honest empty), and the page still assembles.
  - A HANDLER THAT RAISES RENDERS ABSENT-WITH-REASON (CP2, Law 7) — loud, not silent — and the
    REST of the page still assembles (one bad pane cannot abort the page).
  - THE PAYLOAD IS DATA, NEVER HTML: the whole page round-trips through json.dumps (no live
    objects, no templates, no callables leak through — Law 7, the shim produces data, the web
    server renders).

Runnable bare (no DB, no bus, no framework):
    python3 cairn/base/proofs/test_active_page.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.base.device import BaseDevice
from cairn.base.shim import BaseShim


class _Device(BaseDevice):
    """A minimal device with a fixed Form v0 #2 surface and a declarable extra-pane list."""

    def __init__(self, extra_panes=None) -> None:
        super().__init__()
        self._extra = extra_panes or []

    def intention(self) -> dict:
        return {"what": "a spec device", "why": "to prove the pane machinery"}

    def state(self) -> dict:
        return {"resting": "PROVED", "pulses": 3}

    def settings(self) -> dict:
        return {"verbosity": "loud", "bind": "localhost"}

    def declared_panes(self) -> list[dict]:
        return self._extra


class _Shim(BaseShim):
    """A concrete shim that fronts a given device instance directly (no lazy start needed)."""

    def __init__(self, device: _Device) -> None:
        super().__init__(bus=None)
        self._dev = device

    @property
    def device_id(self) -> str:
        return "spec"

    def device(self):
        return self._dev


def test_the_floor_is_always_present_and_pulled_from_introspect():
    dev = _Device()
    page = _Shim(dev).active_page()

    assert page["device"] == "spec"
    kinds = [p["kind"] for p in page["panes"]]
    assert kinds == ["status", "settings"], "a device with no extras gets exactly the floor"
    status = page["panes"][0]["data"]
    assert status["intention"] == dev.intention(), "STATUS carries the reported intention"
    assert status["state"] == dev.state(), "STATUS carries the reported state (drift's reported side)"
    assert page["panes"][1]["data"] == dev.settings(), "SETTINGS carries the device's settings"


def test_declared_panes_append_in_order_and_multiples_of_a_kind_are_allowed():
    dev = _Device(extra_panes=[
        {"kind": "interaction", "label": "Chat", "handler": lambda: {"turns": []}},
        {"kind": "interaction", "label": "Tools", "handler": lambda: {"tools": ["grep"]}},
        {"kind": "logging", "label": "Log", "handler": lambda: {"lines": 0}},
    ])
    page = _Shim(dev).active_page()

    kinds = [p["kind"] for p in page["panes"]]
    labels = [p["label"] for p in page["panes"]]
    assert kinds == ["status", "settings", "interaction", "interaction", "logging"]
    assert labels[2:] == ["Chat", "Tools", "Log"], "declared panes keep their order and labels"
    assert page["panes"][2]["data"] == {"turns": []}, "the chat handler's DATA is carried through"
    assert page["panes"][3]["data"] == {"tools": ["grep"]}, "two interaction panes, both rendered"


def test_an_offered_pane_with_no_handler_renders_absent():
    dev = _Device(extra_panes=[{"kind": "interaction", "label": "Chat", "handler": None}])
    page = _Shim(dev).active_page()

    assert [p["kind"] for p in page["panes"]] == ["status", "settings", "interaction"]
    unwired = page["panes"][2]
    assert unwired["data"] is None and "unwired" in unwired["absent"], "offered-but-unwired is honest empty"


def test_a_handler_that_raises_is_absent_with_reason_and_the_page_survives():
    def boom():
        raise RuntimeError("pane blew up")
    dev = _Device(extra_panes=[
        {"kind": "logging", "label": "Bad", "handler": boom},
        {"kind": "interaction", "label": "Good", "handler": lambda: {"ok": True}},
    ])
    page = _Shim(dev).active_page()

    bad = page["panes"][2]
    assert bad["data"] is None and "RuntimeError" in bad["absent"], "a raising handler is loud + absent (CP2)"
    good = page["panes"][3]
    assert good["data"] == {"ok": True}, "the page still assembles the panes AFTER the bad one"


def test_the_whole_page_is_data_not_html():
    dev = _Device(extra_panes=[
        {"kind": "interaction", "label": "Chat", "handler": lambda: {"turns": [{"who": "user"}]}},
        {"kind": "logging", "label": "Log", "handler": None},
    ])
    page = _Shim(dev).active_page()

    # If any live object, callable, or template leaked through, this raises — the shim
    # produces DATA and the web server renders (Law 7). Round-trips byte-for-byte structure.
    dumped = json.dumps(page)
    assert json.loads(dumped) == page, "the ACTIVE page is pure data — json-round-trips unchanged"


def _main() -> int:
    for check in (test_the_floor_is_always_present_and_pulled_from_introspect,
                  test_declared_panes_append_in_order_and_multiples_of_a_kind_are_allowed,
                  test_an_offered_pane_with_no_handler_renders_absent,
                  test_a_handler_that_raises_is_absent_with_reason_and_the_page_survives,
                  test_the_whole_page_is_data_not_html):
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the ACTIVE page machinery: the STATUS+SETTINGS floor is projected from "
          "introspect(), declared panes append in order (multiples allowed), a bad pane is "
          "loud+absent not fatal, and the whole page is DATA the web server renders")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
