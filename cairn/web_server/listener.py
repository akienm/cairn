"""The web_server LISTENER — the thin http.server wrapper the proof cannot exercise.

NOT A DAEMON (the law: NO DAEMONS — UU grew daemons willy-nilly and shutting them down was
unreliable; that is WHY the ground loop exists, as the one heartbeat every daemon-like function
rides). This file passes the law because it does NOTHING on its own clock: every action it ever
takes is caused by an external call — a browser request arriving on the socket. No poll, no
timer, no background thread of its own. It listens; the name says so.

THERE IS ONLY EVER ONE WEB SERVER IN THE WHOLE SYSTEM — this one, the web_server DEVICE. A
device that wants a face owns a PAGE this server displays: its shim declares the surfaces
(BaseShim.active_page → declared panes) and the roster puts it in the nav. Nobody else binds
a port.

Everything UNDER this wrapper — routing (``server.serve``) and pure rendering (``render.py``)
— is proven green without a socket; only the socket bind lives here, instance-space.

v0 wiring: a ground loop with the LIBRARIAN's shim subscribed — so /device/librarian carries
the real conversation (learning always: every turn a core-loop crossing over the library tree;
summarizing when asked: the ``summarize:`` prefix), with the shim waking the device on the
first poke. The launcher wiring the FULL running heartbeat (all live devices) is still the
filed instance-space edge. The ⚓ HARBOR view is disk-computed and real from a bare start.

Start it:   python3 cairn/web_server/listener.py            # binds 0.0.0.0:80
            python3 cairn/web_server/listener.py --port 9000 --bind 127.0.0.1
(port 80 is privileged: the host-seam is net.ipv4.ip_unprivileged_port_start=80,
 applied via /etc/sysctl.d/90-cairn-port80.conf — Akien's ruling 2026-08-08.
 The bind is all interfaces — loopback AND the box's LAN address answer with one
 socket — Akien's ruling 2026-08-08: "it should answer on 10.0.0.229 too".)
Stop it:    Ctrl-C
"""

from __future__ import annotations

import argparse
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

# Run directly as a script — put the repo root on the path so `cairn` imports. listener.py is
# at cairn/web_server/listener.py, so the repo root is parents[2].
_REPO_ROOT = Path(__file__).resolve().parents[2]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.ground_loop.loop import GroundLoopDevice
from cairn.harbor_master import voyage
from cairn.librarian.shim import LibrarianShim
from cairn.web_server.server import WebServerDevice


def _handler_for(device: WebServerDevice):
    class _Handler(BaseHTTPRequestHandler):
        def _respond(self, status, content_type, body):
            encoded = body.encode("utf-8")
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(encoded)))
            self.end_headers()
            self.wfile.write(encoded)

        def do_GET(self):  # noqa: N802 — http.server's contract
            self._respond(*device.serve(self.path))

        def do_POST(self):  # noqa: N802 — a form posting to a device's page; serve() delivers it
            length = int(self.headers.get("Content-Length") or 0)
            raw = self.rfile.read(length).decode("utf-8", errors="replace")
            self._respond(*device.serve(self.path, method="POST", body=raw))

        def log_message(self, *args):  # keep the console quiet; the bus is the real record
            pass

    return _Handler


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="the Cairn web presentation surface")
    parser.add_argument("--port", type=int, default=80)
    parser.add_argument("--bind", default="0.0.0.0",
                        help="address to bind (default: all interfaces — loopback + LAN)")
    args = parser.parse_args(argv)

    # v0 wiring: the ground loop with the librarian's shim subscribed — the librarian rides the
    # roster like any device, its chat window a declared pane, its device woken by the shim on
    # the first poke (no host/DB touched until then). The harbor source is REAL (disk-computed).
    # The launcher wiring the FULL running heartbeat is the filed instance-space edge.
    heartbeat = GroundLoopDevice()
    heartbeat.subscribe(LibrarianShim())
    device = WebServerDevice(heartbeat, harbor_source=voyage.traffic_image, port=args.port)
    httpd = ThreadingHTTPServer((args.bind, args.port), _handler_for(device))
    print(f"[web_server] serving on http://{args.bind}:{args.port}  (Ctrl-C to stop)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[web_server] stopped", flush=True)
        httpd.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
