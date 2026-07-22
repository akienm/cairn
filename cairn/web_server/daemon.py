"""The web_server daemon — the thin http.server wrapper the proof cannot exercise.

Everything UNDER it — routing a request to a rendered page (``server.serve``) and the pure HTML
rendering (``render.py``) — is proven green without a socket. Here we only bind a LOCALHOST port
and hand each GET to ``serve``. This is the OS-specific thin wrapper, exactly like ground_loop's
wall-clock daemon and sudo_relay's daemon.py: the SHAPE is proven, the bind is instance-space.

v0 is a stub wiring: it stands up a WebServerDevice over a freshly built ground_loop with no
subscribers, so a bare run serves an honest empty nav. Wiring the REAL running heartbeat (the
one the launcher starts, with the live devices subscribed) is the launcher's job — instance-space
under ~/.cairn/devices/web_server/0/ — and lands with the multi-process runtime.

Start it:   python3 cairn/web_server/daemon.py            # binds localhost:8787
            python3 cairn/web_server/daemon.py --port 9000
Stop it:    Ctrl-C
"""

from __future__ import annotations

import argparse
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Run directly as a script — put the repo root on the path so `cairn` imports. daemon.py is at
# cairn/web_server/daemon.py, so the repo root is parents[2].
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.ground_loop.loop import GroundLoopDevice
from cairn.web_server.server import WebServerDevice


def _handler_for(device: WebServerDevice):
    class _Handler(BaseHTTPRequestHandler):
        def do_GET(self):  # noqa: N802 — http.server's contract
            status, content_type, body = device.serve(self.path)
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def log_message(self, *args):  # keep the console quiet; the bus is the real record
            pass

    return _Handler


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="the Cairn web presentation surface (localhost)")
    parser.add_argument("--port", type=int, default=8787)
    args = parser.parse_args(argv)

    # v0 stub wiring: an empty heartbeat → an honest empty nav. The launcher wires the real one.
    device = WebServerDevice(GroundLoopDevice(), port=args.port)
    httpd = ThreadingHTTPServer(("127.0.0.1", args.port), _handler_for(device))
    print(f"[web_server] serving on http://127.0.0.1:{args.port}  (Ctrl-C to stop)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[web_server] stopped", flush=True)
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
