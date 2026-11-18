"""``python -m cairn.devices.dbproxy`` — the database proxy's own process (outline 2.3.2).

Holding the listen port is its singleton. It writes its record to
``~/.cairn/devices/dbproxy/0/relay.json`` on start and on every connection. Where the port is
already held (the home box: Postgres itself listens on 5432) it records ``held`` and exits 0,
forwarding nothing.
"""

from __future__ import annotations

import errno
import json
import os
import sys
import time


def ports() -> tuple[int, int]:
    return (int(os.environ.get("CAIRN_DBPROXY_LISTEN_PORT", "5432")),
            int(os.environ.get("CAIRN_DBPROXY_POSTGRES_PORT", "5433")))


def record_path():
    from cairn.tools.base.address import instance_path
    return instance_path("dbproxy", 0) / "relay.json"


def write_record(rec: dict) -> None:
    p = record_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(rec, indent=1))
    os.replace(tmp, p)


def main() -> int:
    from cairn.devices.dbproxy.forward import Relay
    listen, upstream = ports()
    base = {"pid": os.getpid(), "listen_port": listen, "upstream_port": upstream,
            "since": time.strftime("%Y-%m-%dT%H:%M:%S")}
    try:
        relay = Relay(listen, upstream)
    except OSError as exc:
        # held = someone else has the port: EADDRINUSE, or on Windows WSAEADDRINUSE (10048) and
        # WSAEACCES (10013, an exclusive holder). POSIX EACCES is a privileged port: it raises.
        if exc.errno == errno.EADDRINUSE or getattr(exc, "winerror", None) in (10048, 10013):
            write_record({**base, "state": "held", "connections": 0, "refused": 0,
                          "why": f"127.0.0.1:{listen} is already held: {exc}"})
            return 0
        raise

    def record(r) -> None:
        write_record({**base, "state": "listening", "connections": r.connections, "refused": r.refused})

    relay.on_change = record
    record(relay)
    relay.serve_forever()
    return 0


if __name__ == "__main__":
    sys.exit(main())
