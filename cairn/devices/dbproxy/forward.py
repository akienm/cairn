"""forward.py — the threaded TCP relay the database proxy runs (ticket a22eb3c25ccd).

Accepts on 127.0.0.1:<listen> (loopback only: the proxy is the box's own door, outline 11.3.7),
dials 127.0.0.1:<upstream> per connection, pumps both ways, and closes both ends when either
closes. A refused upstream closes the client and is counted. ``on_change`` is called after
every count change so the process can rewrite its record.
"""

from __future__ import annotations

import socket
import threading

from cairn.tools.base.diagnostic import DiagnosticBase

LOOPBACK = "127.0.0.1"


class Relay(DiagnosticBase):
    def __init__(self, listen_port: int, upstream_port: int, on_change=None) -> None:
        super().__init__()
        self.upstream_port = upstream_port
        self.on_change = on_change
        self.connections = 0
        self.refused = 0
        self._lock = threading.Lock()
        self._stopping = False
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):          # Windows: no port sharing
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        else:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            sock.bind((LOOPBACK, listen_port))               # EADDRINUSE raises: the held case
            sock.listen(64)
        except OSError:
            sock.close()
            raise
        self._sock = sock
        self.listen_port = sock.getsockname()[1]
        self._thread = threading.Thread(target=self._accept_loop, daemon=True, name="dbproxy-accept")

    @property
    def bound_address(self) -> tuple:
        return self._sock.getsockname()

    def start(self) -> "Relay":
        self._thread.start()
        return self

    def serve_forever(self) -> None:
        self._accept_loop()

    def stop(self) -> None:
        self._stopping = True
        try:
            self._sock.close()
        except OSError:
            pass

    def _count(self, field: str) -> None:
        with self._lock:
            setattr(self, field, getattr(self, field) + 1)
        if self.on_change:
            try:
                self.on_change(self)
            except Exception:  # noqa: BLE001 — a record write never kills the relay
                pass

    def _accept_loop(self) -> None:
        while not self._stopping:
            try:
                client, _ = self._sock.accept()
            except OSError:
                return
            threading.Thread(target=self._serve, args=(client,), daemon=True).start()

    def _serve(self, client: socket.socket) -> None:
        try:
            upstream = socket.create_connection((LOOPBACK, self.upstream_port), timeout=5)
        except OSError:
            self._count("refused")
            client.close()
            return
        upstream.settimeout(None)
        self._count("connections")
        done = threading.Event()

        def pump(src, dst):
            try:
                while True:
                    data = src.recv(65536)
                    if not data:
                        break
                    dst.sendall(data)
            except OSError:
                pass
            finally:
                done.set()

        threading.Thread(target=pump, args=(upstream, client), daemon=True).start()
        pump(client, upstream)
        done.wait()
        for s in (client, upstream):
            try:
                s.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass
            s.close()
