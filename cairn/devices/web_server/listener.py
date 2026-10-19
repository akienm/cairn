"""The web_server LISTENER — the thin Starlette/uvicorn wrapper the proof cannot exercise.

Graduated from stdlib http.server to Starlette/uvicorn (ticket 72e8e3509287,
grafting the wiring pattern from TheIgors/lab/claudecode/utility_closet_server.py).
The graduation unlocks async handlers and WebSocket protocol upgrades for
downstream consumers (the trouble-panel's dynamic page is the first).

NOT A DAEMON (the law: NO DAEMONS). This file acts only when an external call
arrives — a browser request on the socket. No poll, no timer, no background
thread of its own.

THERE IS ONLY EVER ONE WEB SERVER IN THE WHOLE SYSTEM — this one, the web_server
DEVICE. A device that wants a face owns a PAGE this server displays.

Everything UNDER this wrapper — routing (``server.serve``) and pure rendering
(``render.py``) — is proven green without a socket; only the socket bind lives
here, instance-space.

Start it:   python3 cairn/devices/web_server/listener.py            # binds 0.0.0.0:80
            python3 cairn/devices/web_server/listener.py --port 9000 --bind 127.0.0.1
Stop it:    Ctrl-C
"""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

import json

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket
import uvicorn

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.bus_client import connect_system, harbor_source
from cairn.devices.web_server.server import WebServerDevice

_device: WebServerDevice | None = None
# The bus, held at module scope so the WebSocket handler can reach the trouble lane
# without importing it (ticket 9579a6f9cec6 — no device imports another device).
_bus = None


async def _handle_get(request: Request) -> Response:
    status, content_type, body = _device.serve(request.url.path)
    return Response(body, status_code=status, media_type=content_type)


async def _handle_post(request: Request) -> Response:
    raw = (await request.body()).decode("utf-8", errors="replace")
    status, content_type, body = _device.serve(
        request.url.path, method="POST", body=raw
    )
    return Response(body, status_code=status, media_type=content_type)


_ws_clients: set[WebSocket] = set()


def _trouble_rows(roots: dict | None = None) -> list[dict]:
    """The live troubles the socket pushes, read as files through the tool trouble publishes
    (ticket ee04bb869795) — never asked over the bus, where every reply stood as a row. An
    absent store raises (Law 7)."""
    from cairn.devices.trouble.tools.store import store
    return [{"id": t.get("id", "?"), "standing": t.get("standing", "?"),
             "why": t.get("why", ""), "count": t.get("count", 0)}
            for t in store.live(roots)]


async def _handle_ws_troubles(websocket: WebSocket) -> None:
    await websocket.accept()
    _ws_clients.add(websocket)
    try:
        # A failure to read the store falls to the handler below and CLOSES the socket —
        # deliberately, because sending an empty list would render as the normal operating
        # state (zero live troubles) when the truth is that we could not look (Law 7).
        await websocket.send_json(_trouble_rows())
        while True:
            await websocket.receive_text()
    except Exception:
        pass
    finally:
        _ws_clients.discard(websocket)


def _make_app() -> Starlette:
    routes = [
        WebSocketRoute("/ws/troubles", _handle_ws_troubles),
        Route("/{path:path}", _handle_get, methods=["GET"]),
        Route("/{path:path}", _handle_post, methods=["POST"]),
    ]
    return Starlette(routes=routes)


def main(argv=None) -> int:
    global _device, _bus

    parser = argparse.ArgumentParser(description="the Cairn web presentation surface")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--bind", default="0.0.0.0",
                        help="address to bind (default: all interfaces — loopback + LAN)")
    args = parser.parse_args(argv)

    # No device is special-cased; the roster lists every fitted device and loads a shim from
    # disk the first time its page or its mail asks for one (ticket efb670ff1dd8).
    _bus, roster = connect_system(devices=["librarian"])
    _device = WebServerDevice(roster, harbor_source=harbor_source(), port=args.port)

    app = _make_app()
    config = uvicorn.Config(
        app,
        host=args.bind,
        port=args.port,
        log_level="warning",
    )
    server = uvicorn.Server(config)

    print(f"[web_server] serving on http://{args.bind}:{args.port}  (Ctrl-C to stop)", flush=True)
    try:
        asyncio.run(server.serve())
    except KeyboardInterrupt:
        print("\n[web_server] stopped", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
