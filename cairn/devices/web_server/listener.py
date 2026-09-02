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

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import Response
from starlette.routing import Route
import uvicorn

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base.bus_client import connect_system, harbor_source
from cairn.devices.web_server.server import WebServerDevice

_device: WebServerDevice | None = None


async def _handle_get(request: Request) -> Response:
    status, content_type, body = _device.serve(request.url.path)
    return Response(body, status_code=status, media_type=content_type)


async def _handle_post(request: Request) -> Response:
    raw = (await request.body()).decode("utf-8", errors="replace")
    status, content_type, body = _device.serve(
        request.url.path, method="POST", body=raw
    )
    return Response(body, status_code=status, media_type=content_type)


def _make_app() -> Starlette:
    routes = [
        Route("/{path:path}", _handle_get, methods=["GET"]),
        Route("/{path:path}", _handle_post, methods=["POST"]),
    ]
    return Starlette(routes=routes)


def main(argv=None) -> int:
    global _device

    parser = argparse.ArgumentParser(description="the Cairn web presentation surface")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--bind", default="0.0.0.0",
                        help="address to bind (default: all interfaces — loopback + LAN)")
    args = parser.parse_args(argv)

    _bus, heartbeat = connect_system(devices=["ground_loop", "librarian"])
    _device = WebServerDevice(heartbeat, harbor_source=harbor_source(), port=args.port)

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
