"""Proof for ticket 266986fcda94 — bus_client dials the loopback port where Python has no AF_UNIX.

MEASURED 2026-11-20 on akiendell (Windows): every bus call died with
``UnboundLocalError: cannot access local variable 'rec' where it is not associated with a value``
at remote.py ``_dial``. Commit f36fa3fae (ticket f62f6b50b047) moved the dial into ``_dial`` and
indented the no-AF_UNIX block under ``if hasattr(socket, "AF_UNIX"):``, after that branch's
``return conn, None`` — so on a Python without AF_UNIX nothing reads ``bus.port`` and ``rec`` is
never bound. sail chart/cross, outlinecheck and hollow all stop on that host.

The proof runs on ANY host: each tooth deletes ``socket.AF_UNIX`` for its own duration (restored
in a finally), so the Windows branch is exercised on Linux too instead of reading UNRAN. Each
tooth writes its own scratch home; the stub bus is a listener on 127.0.0.1 in this process.

  1. with no AF_UNIX and a bus.port record naming a live loopback listener, ``_dial`` returns a
     connection to that listener and the record's key;
  2. with no AF_UNIX and no bus.port record, ``_dial`` raises FileNotFoundError naming the
     bus.port path (the missing-bus signal), never UnboundLocalError;
  3. with no AF_UNIX and a bus.port record that names no port, ``_dial`` raises FileNotFoundError
     saying it names no loopback port.

    bin/cairn test cairn/tools/bus_client/proofs/test_a_dial_without_af_unix_reaches_the_loopback_port.py
"""
from __future__ import annotations

import contextlib
import json
import socket
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"266986fcda94": {
    "1": "test_a_dial_with_no_af_unix_reaches_the_loopback_listener",
    "2": "test_a_dial_with_no_af_unix_and_no_port_record_names_the_missing_file",
    "3": "test_a_port_record_with_no_port_names_it",
}}


@contextlib.contextmanager
def _no_af_unix():
    had = hasattr(socket, "AF_UNIX")
    saved = getattr(socket, "AF_UNIX", None)
    if had:
        delattr(socket, "AF_UNIX")
    try:
        yield
    finally:
        if had:
            socket.AF_UNIX = saved


def _home() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return scratch_dir("busdial-266986fcda94-")


def test_a_dial_with_no_af_unix_reaches_the_loopback_listener():
    from cairn.tools.bus_client import remote
    home = _home()
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    srv.bind(("127.0.0.1", 0))
    srv.listen(1)
    try:
        (home / "bus.port").write_text(json.dumps({"port": srv.getsockname()[1], "key": "k-123"}), encoding="utf-8")
        with _no_af_unix():
            conn, key = remote._dial(str(home), 5.0)
        try:
            assert key == "k-123", f"the record's key was not returned: {key!r}"
            peer, _ = srv.accept()
            peer.close()
        finally:
            conn.close()
    finally:
        srv.close()


def test_a_dial_with_no_af_unix_and_no_port_record_names_the_missing_file():
    from cairn.tools.bus_client import remote
    home = _home()
    with _no_af_unix():
        try:
            remote._dial(str(home), 2.0)
        except FileNotFoundError as exc:
            assert "bus.port" in str(exc) or "bus.port" in str(getattr(exc, "filename", "")), (
                f"the missing-bus signal does not name bus.port: {exc}")
            return
    raise AssertionError("no FileNotFoundError was raised for a home with no bus.port")


def test_a_port_record_with_no_port_names_it():
    from cairn.tools.bus_client import remote
    home = _home()
    (home / "bus.port").write_text(json.dumps({"key": "k"}), encoding="utf-8")
    with _no_af_unix():
        try:
            remote._dial(str(home), 2.0)
        except FileNotFoundError as exc:
            assert "no loopback port" in str(exc), f"the signal does not say it names no port: {exc}"
            return
    raise AssertionError("no FileNotFoundError was raised for a bus.port naming no port")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
