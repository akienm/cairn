"""Proof for ticket 3dc005de27cf — db_domain reaches Postgres over TCP where there is no Unix socket.

Measured 2026-11-04 (ticket 5183005fa134's Windows live fire): the bus lazily started on
akiendell died in store.py ensure_database() -> psycopg2.connect(host='/var/run/postgresql')
with 'Network is down'. Windows has no socket directory, and store.py knew no other route.

The socket dir is CAIRN_PG_SOCKET_DIR (default /var/run/postgresql, the name bin/cairn already
reads). Where its .s.PGSQL.5432 exists the connection stays on the Unix socket (peer auth,
unchanged); where it does not, the connection goes to TCP 127.0.0.1:5432.
On the TCP branch libpq reads its password from passfile=~/.cairn/devices/db_domain/0/pgpass
(Akien 2026-11-08, open-d0399bd1d6f1: "the answer is in ~/.cairn/devices/<device>"); store.py
passes the path, never a secret.

Postgres on both boxes demands a password on 127.0.0.1 (measured 2026-11-04: here
'fe_sendauth: no password supplied'). So tooth 1 proves the ROUTE, not a login: a TCP attempt
earns the server's answer naming 'server at "127.0.0.1", port 5432', and a socket-only build
never produces that — it either connects over the socket or names the socket file. A live
TCP connection (once a credential exists) passes too, by conn.info.host.

  1. test_no_socket_dials_tcp_loopback — empty socket dir: connect() reaches 127.0.0.1:5432.
  2. test_a_present_socket_stays_on_the_socket — the real socket: conn.info.host is a path.
  3. test_the_choice_has_two_branches — _conn_args() on a dir with and without the socket file.

    python3 cairn/devices/db_domain/proofs/test_db_reaches_postgres_over_tcp.py   # exit 0 = green
"""
import importlib
import os
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"3dc005de27cf": {
    "1": "test_no_socket_dials_tcp_loopback",
    "2": "test_a_present_socket_stays_on_the_socket",
    "3": "test_the_choice_has_two_branches",
}}

_VAR = "CAIRN_PG_SOCKET_DIR"
_REAL = "/var/run/postgresql"


def _store():
    """Bound at call time: the hollow reading takes the build away and the teeth read red."""
    return importlib.import_module("cairn.devices.db_domain.tools.client.store")


class _SocketDir:
    """CAIRN_PG_SOCKET_DIR pointed at `path` for the block, restored after."""

    def __init__(self, path):
        self.path, self.old = path, None

    def __enter__(self):
        self.old = os.environ.get(_VAR)
        if self.path is None:
            os.environ.pop(_VAR, None)
        else:
            os.environ[_VAR] = str(self.path)

    def __exit__(self, *exc):
        if self.old is None:
            os.environ.pop(_VAR, None)
        else:
            os.environ[_VAR] = self.old


def test_no_socket_dials_tcp_loopback() -> None:
    with tempfile.TemporaryDirectory(prefix="cairn-nosock-") as empty, _SocketDir(empty):
        try:
            conn = _store().connect()
        except Exception as e:  # the server's auth demand is the evidence of the route
            text = str(e)
            assert 'server at "127.0.0.1", port 5432' in text, f"not a TCP loopback attempt: {text!r}"
            assert empty not in text and ".s.PGSQL" not in text, f"named a socket file: {text!r}"
        else:
            try:
                assert conn.info.host == "127.0.0.1", f"connected over {conn.info.host!r}, not TCP loopback"
                assert conn.info.port == 5432, conn.info.port
            finally:
                conn.close()
    print("ok test_no_socket_dials_tcp_loopback")


def test_a_present_socket_stays_on_the_socket() -> None:
    assert os.path.exists(os.path.join(_REAL, ".s.PGSQL.5432")), f"no Postgres socket at {_REAL} on this box"
    for setting in (None, _REAL):
        with _SocketDir(setting):
            conn = _store().connect()
            try:
                assert conn.info.host.startswith("/"), f"with the socket present, connected over {conn.info.host!r}"
            finally:
                conn.close()
    print("ok test_a_present_socket_stays_on_the_socket")


def test_the_choice_has_two_branches() -> None:
    with tempfile.TemporaryDirectory(prefix="cairn-sockdir-") as d:
        with _SocketDir(d):
            # Akien, open-d0399bd1d6f1: the TCP credential berths "in ~/.cairn/devices/<device>" —
            # the branch names the passfile there and carries no secret itself.
            from cairn.tools.base.address import instance_path
            want = {"host": "127.0.0.1", "port": 5432,
                    "passfile": str(instance_path("db_domain", 0) / "pgpass")}
            assert _store()._conn_args() == want, _store()._conn_args()
        Path(d, ".s.PGSQL.5432").touch()
        with _SocketDir(d):
            assert _store()._conn_args() == {"host": d}, _store()._conn_args()
    with _SocketDir(None):
        assert _store()._conn_args() == {"host": _REAL}, _store()._conn_args()
    print("ok test_the_choice_has_two_branches")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
