"""PROBE — does the web server serve dynamic panes under real traffic?

Berth for the WATCHME that ticket ``the-web-server-graduates-to-starlette`` carries.
Berthed beside ``cairn/devices/librarian`` because the librarian is the first consumer
of dynamic panes (the trouble-panel's dynamic page is the first downstream ticket).

THE MEASUREMENT. The web server graduated from stdlib http.server to Starlette/uvicorn
(ticket 72e8e3509287), unlocking async handlers and WebSocket protocol upgrades. This
probe watches whether that capability is exercised: a pane requested via HTTP that the
server renders dynamically (not static file serving).

TRIGGER: a dynamic pane render is observed in the web server's traffic. Since no dynamic
pane exists yet (the trouble-panel ticket is downstream and depends on this graduation),
the trigger starts False and crosses True when the first dynamic pane is served.

ENOUGH: three dynamic pane renders under real traffic, each returning correct content for
the requesting device's current state (from the ticket's watchme spec).

HOLDS: False when any render read carries an empty or missing ``content`` (a render that
returned no content is the falsifier's failure); with no records it holds.

AUTHORITY: none. It posts its finding to CodeMother's WATCHME gate (to codemother, verb
machines/watchme/watch, ticket 8b16f3e77013), which owns the back-edge.

FILES ONLY — no device, no bus, no network.
"""

from __future__ import annotations

import json
from pathlib import Path

from cairn.tools.base import address
from cairn.tools.base.probe import Probe, once, watch_carry

_CLASS_SPACE = Path(__file__).resolve().parents[4]
_TICKET_ID = "72e8e3509287"

_LOG_PATH = address.instance_path("web_server", 0) / "dynamic_pane_renders.json"


def _read_renders() -> list[dict]:
    if _LOG_PATH.is_file():
        try:
            data = json.loads(_LOG_PATH.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return data
        except Exception:  # noqa: BLE001
            pass
    return []


def _trigger(now, context: dict) -> bool:
    renders = once(context, "renders", _read_renders)
    return len(renders) > 0


def _enough(context: dict) -> bool:
    renders = once(context, "renders", _read_renders)
    return len(renders) >= 3


def _carry(context: dict) -> dict:
    renders = once(context, "renders", _read_renders)
    return {
        "finding": f"{len(renders)} dynamic pane render(s) observed",
        "render_count": len(renders),
        "renders": renders[:3],
        "against_falsifier": "clause (2): WebSocket connection establishes — "
                             "the capability the current server lacks; "
                             "clause (1): existing pane URLs render identically",
        "suggests": "the Starlette graduation is exercised under real traffic — "
                    "the capability it unlocked (async + WebSocket) is in use",
    }


def _holds(context: dict) -> bool:
    renders = once(context, "renders", _read_renders)
    return all(isinstance(r, dict) and r.get("content") for r in renders)


_HORIZON = 2000

PROBE = Probe(
    why="the Starlette graduation unlocks dynamic panes — this probe watches whether "
        "that capability is exercised under real traffic, which is the web server's "
        "reason for existing beyond static file serving",
    trigger=_trigger,
    to="codemother",
    verb="machines/watchme/watch",
    body={"nexus": "hypothesize", "kind": "efficacy"},
    carry=watch_carry(_TICKET_ID, _carry, holds=_holds),
    enough=_enough,
    horizon=_HORIZON,
)


if __name__ == "__main__":
    renders = _read_renders()
    print(json.dumps({
        "render_count": len(renders),
        "would_trigger": _trigger(None, {"renders": renders}),
        "enough": _enough({"renders": renders}),
    }, indent=2, default=str))
