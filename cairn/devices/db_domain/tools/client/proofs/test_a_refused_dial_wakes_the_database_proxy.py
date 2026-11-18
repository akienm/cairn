"""Proof for ticket 9166782e6101 — a refused loopback dial wakes the database proxy through the bus.

Measured 2026-11-18 on akiendelllinux at 44d22f516: store.connect() and ensure_database() dialed
psycopg2.connect once with no retry, so on a cache box whose database proxy was not running every
db call failed 'Connection refused' at 127.0.0.1:5432.

1. a refused TCP loopback dial wakes the proxy exactly once and the dial is retried until it connects;
2. a socket dial that fails, and a TCP failure that is not a refusal, raise at once and never wake;
3. a wake that fails, or a refusal still standing after the retry window, raises the refusal naming why;
4. the wake asks the bus for start on cairn.devices.dbproxy.shim:DatabaseProxyShim, a class that
   exists, and store.py imports nothing from cairn.devices.dbproxy.

Everything runs in-process: psycopg2.connect and the bus client are swapped for recorders, and the
proxy's class is read from its source, never imported.

    bin/cairn test cairn/devices/db_domain/tools/client/proofs/test_a_refused_dial_wakes_the_database_proxy.py
"""
from __future__ import annotations

import ast
import contextlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"9166782e6101": {
    "1": "test_a_refused_tcp_dial_wakes_once_and_retries",
    "2": "test_a_socket_failure_and_a_non_refusal_never_wake",
    "3": "test_a_failed_wake_and_a_standing_refusal_raise_naming_why",
    "4": "test_the_wake_names_an_existing_shim_and_store_imports_no_dbproxy",
}}

_STORE = REPO / "cairn/devices/db_domain/tools/client/store.py"
_SHIM = REPO / "cairn/devices/dbproxy/shim.py"
_TARGET = "cairn.devices.dbproxy.shim:DatabaseProxyShim"
_REFUSED = ('connection to server at "127.0.0.1", port 5432 failed: Connection refused\n'
            '\tIs the server running on that host and accepting TCP/IP connections?')


class _Conn:
    autocommit = False

    def close(self):
        pass


class _Bus:
    """Records every verbs call; answers `answer`, or raises it when it is an exception."""

    def __init__(self, calls, answer):
        self._calls, self._answer = calls, answer

    def verbs(self, target, argv):
        self._calls.append(("verbs", target, list(argv)))
        if isinstance(self._answer, BaseException):
            raise self._answer
        return self._answer


@contextlib.contextmanager
def _world(*, tcp=True, refusals=2, error=_REFUSED, wake_answer=None, window=None):
    """store with psycopg2.connect failing `refusals` times with `error`, then connecting."""
    import psycopg2
    from cairn.devices.db_domain.tools.client import store
    from cairn.tools.bus_client import remote
    calls: list = []
    dials = {"n": 0}

    def fake_connect(**kw):
        dials["n"] += 1
        if refusals is None or dials["n"] <= refusals:
            raise psycopg2.OperationalError(error)
        return _Conn()

    args = ({"host": "127.0.0.1", "port": 5432, "passfile": "/nonexistent/pgpass"} if tcp
            else {"host": "/var/run/postgresql"})
    answer = {"exit": 0, "text": "started", "data": None} if wake_answer is None else wake_answer
    saved = {"connect": store.psycopg2.connect, "args": store._conn_args,
             "ensure": remote.ensure_bus, "remote": remote.RemoteBus,
             "woken": getattr(store, "_woken", None), "seconds": getattr(store, "_WAKE_SECONDS", None),
             "poll": getattr(store, "_WAKE_POLL", None)}
    store.psycopg2.connect = fake_connect
    store._conn_args = lambda: dict(args)
    remote.ensure_bus = lambda *a, **k: calls.append(("ensure_bus",)) or {"ok": True}
    remote.RemoteBus = lambda *a, **k: _Bus(calls, answer)
    store._woken = False
    store._WAKE_POLL = 0.01
    if window is not None:
        store._WAKE_SECONDS = window
    try:
        yield store, psycopg2, calls, dials
    finally:
        store.psycopg2.connect = saved["connect"]
        store._conn_args = saved["args"]
        remote.ensure_bus = saved["ensure"]
        remote.RemoteBus = saved["remote"]
        for k, attr in (("woken", "_woken"), ("seconds", "_WAKE_SECONDS"), ("poll", "_WAKE_POLL")):
            if saved[k] is None:
                with contextlib.suppress(AttributeError):
                    delattr(store, attr)
            else:
                setattr(store, attr, saved[k])


def test_a_refused_tcp_dial_wakes_once_and_retries():
    with _world(refusals=3) as (store, psycopg2, calls, dials):
        conn = store._dial("cairn")
        assert isinstance(conn, _Conn), conn
        wakes = [c for c in calls if c[0] == "verbs"]
        assert wakes == [("verbs", _TARGET, ["start"])], calls
        assert dials["n"] == 4, dials
        # a second refusal in the same process does not wake again
        dials["n"] = 0
        conn = store._dial("cairn")
        assert len([c for c in calls if c[0] == "verbs"]) == 1, calls
    # connect() and ensure_database() both dial through _dial
    tree = ast.parse(_STORE.read_text(encoding="utf-8"))
    for fn in (n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("connect", "ensure_database")):
        names = {c.func.id for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Name)}
        attrs = {c.func.attr for c in ast.walk(fn) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}
        assert "_dial" in names, f"{fn.name} does not dial through _dial"
        assert "connect" not in attrs, f"{fn.name} still calls psycopg2.connect itself"
    print("a refused TCP dial woke the proxy once and connected on the retry")


def test_a_socket_failure_and_a_non_refusal_never_wake():
    with _world(tcp=False, refusals=None) as (store, psycopg2, calls, dials):
        try:
            store._dial("cairn")
            raise AssertionError("a failing socket dial connected")
        except psycopg2.OperationalError:
            pass
        assert calls == [] and dials["n"] == 1, (calls, dials)
    with _world(refusals=None, error='FATAL:  password authentication failed for user "x"') as (
            store, psycopg2, calls, dials):
        try:
            store._dial("cairn")
            raise AssertionError("a non-refusal connected")
        except psycopg2.OperationalError as exc:
            assert "password authentication failed" in str(exc), exc
        assert calls == [] and dials["n"] == 1, (calls, dials)
    print("socket failures and non-refusals raise at once and never wake")


def test_a_failed_wake_and_a_standing_refusal_raise_naming_why():
    with _world(refusals=None, wake_answer={"exit": 1, "text": "no such shim", "data": None}) as (
            store, psycopg2, calls, dials):
        try:
            store._dial("cairn")
            raise AssertionError("a failed wake connected")
        except psycopg2.OperationalError as exc:
            assert "Connection refused" in str(exc) and "no such shim" in str(exc), exc
        assert dials["n"] == 1, dials
    with _world(refusals=None, wake_answer=ConnectionError("the bus did not answer")) as (
            store, psycopg2, calls, dials):
        try:
            store._dial("cairn")
            raise AssertionError("a raising wake connected")
        except psycopg2.OperationalError as exc:
            assert "Connection refused" in str(exc) and "the bus did not answer" in str(exc), exc
    with _world(refusals=None, window=0.2) as (store, psycopg2, calls, dials):
        try:
            store._dial("cairn")
            raise AssertionError("a standing refusal connected")
        except psycopg2.OperationalError as exc:
            assert "Connection refused" in str(exc) and "still refused" in str(exc), exc
        assert dials["n"] > 2, dials
    print("a failed wake and a standing refusal raise the refusal, naming why")


def test_the_wake_names_an_existing_shim_and_store_imports_no_dbproxy():
    mod, cls = _TARGET.split(":")
    assert _SHIM == REPO / (mod.replace(".", "/") + ".py")
    shim_tree = ast.parse(_SHIM.read_text(encoding="utf-8"))
    assert any(isinstance(n, ast.ClassDef) and n.name == cls for n in shim_tree.body), \
        f"{cls} is not defined in {_SHIM}"
    text = _STORE.read_text(encoding="utf-8")
    assert f'"{_TARGET}"' in text, f"store.py does not name {_TARGET}"
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.ImportFrom):
            assert not (node.module or "").startswith("cairn.devices.dbproxy"), node.module
        if isinstance(node, ast.Import):
            assert not any(a.name.startswith("cairn.devices.dbproxy") for a in node.names), node.names
    print(f"the wake names {_TARGET}, which exists; store.py imports no dbproxy")


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except Exception as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {exc}")
    sys.exit(1 if failed else 0)
