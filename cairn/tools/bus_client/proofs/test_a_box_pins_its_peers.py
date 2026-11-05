"""Proof: a box pins its peers (ticket 5183005fa134, falsifier clause b).

The bus_client tool's ``tls`` module is the whole of box-to-box trust: an identity made by the
openssl CLI, a folder of pinned certificates, and the two contexts that refuse anything else.
This proof measures only that module, over loopback sockets of its own — no bus process.
Teeth, all printed, none stopping at the first red:

  1. make_identity makes key + certificate + name once; its fingerprint is openssl's own
     (``openssl x509 -fingerprint -sha256``); a second call keeps the same key.
  2. two boxes pinned to each other handshake both ways, and each names the other by pin.
  3. a client whose certificate is not pinned is refused by the server.
  4. a server whose certificate is not pinned is refused by the client.
  5. a client presenting no certificate gets through only as an asker: the server sees no
     peer box, and first_contact pins the server and hands over its own certificate,
     which ``accept`` turns into a pin (``decline`` drops it).

    python3 cairn/tools/bus_client/proofs/test_a_box_pins_its_peers.py
"""
from __future__ import annotations

import json
import socketserver
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

PROVES = {"5183005fa134": {"b": "test_a_box_pins_its_peers"}}


def _tls():
    from cairn.tools.bus_client import tls   # the subject, bound at call time
    return tls


class _Peer:
    """A one-shot TLS server on loopback using the tls module's server context; records what
    it saw of each connection."""

    def __init__(self, d: Path, n: int):
        self.d, self.seen = d, []
        # A listener only (socketserver binds and listens); every DIAL in this proof is the
        # subject's own tls.dial / first_contact, so the proof opens no door of its own.
        self.srv = socketserver.TCPServer(("127.0.0.1", 0), socketserver.BaseRequestHandler)
        self.sock = self.srv.socket
        self.port = self.srv.server_address[1]
        self.t = threading.Thread(target=self._run, args=(n,), daemon=True)
        self.t.start()

    def _run(self, n):
        tls = _tls()
        for _ in range(n):
            raw, _ = self.sock.accept()
            raw.settimeout(10)
            try:
                conn = tls.server_context(self.d).wrap_socket(raw, server_side=True)
                line = conn.makefile("r").readline()
                self.seen.append({"peer": tls.peer_box(self.d, conn), "op": json.loads(line)["op"]})
                conn.sendall((json.dumps({"ok": True, "box": tls.identity(self.d)["name"]}) + "\n").encode())
                conn.close()
            except Exception as exc:  # noqa: BLE001 — a refusal is what some teeth want
                self.seen.append({"refused": f"{type(exc).__name__}: {exc}"})
                raw.close()

    def done(self):
        self.t.join(15)
        self.srv.server_close()
        return self.seen


def _boxes(t: Path):
    tls = _tls()
    a, b, c = t / "a", t / "b", t / "c"
    for d, n in ((a, "boxa"), (b, "boxb"), (c, "boxc")):
        tls.make_identity(d, n)
    tls.trust(a, "boxb", (b / "box.crt").read_text())
    tls.trust(b, "boxa", (a / "box.crt").read_text())
    return a, b, c


def _ask_stats(tls, d, port):
    conn = tls.dial(d, "127.0.0.1", port, timeout=10)
    try:
        conn.sendall(b'{"op": "stats"}\n')
        return json.loads(conn.makefile("r").readline())
    finally:
        conn.close()


def tooth_identity_is_made_once_by_openssl():
    tls = _tls()
    with tempfile.TemporaryDirectory(prefix="tls-") as t:
        d = Path(t) / "id"
        fp = tls.make_identity(d, "boxa")
        assert tls.has_identity(d), "make_identity left no key/cert/name"
        r = subprocess.run([tls.openssl(), "x509", "-in", str(d / "box.crt"), "-noout",
                            "-fingerprint", "-sha256"], capture_output=True, text=True)
        theirs = r.stdout.strip().split("=", 1)[-1].replace(":", "").lower()
        assert fp == theirs, f"fingerprint {fp} is not openssl's {theirs}"
        key = (d / "box.key").read_bytes()
        assert tls.make_identity(d, "boxa") == fp and (d / "box.key").read_bytes() == key, \
            "a second make_identity replaced the key the peers pin"
        assert tls.identity(d)["name"] == "boxa"


def tooth_pinned_boxes_handshake_both_ways():
    tls = _tls()
    with tempfile.TemporaryDirectory(prefix="tls-") as t:
        a, b, _ = _boxes(Path(t))
        srv = _Peer(a, 1)
        reply = _ask_stats(tls, b, srv.port)
        seen = srv.done()
        assert reply == {"ok": True, "box": "boxa"}, f"pinned client got {reply}"
        assert seen == [{"peer": "boxb", "op": "stats"}], f"server saw {seen}"


def tooth_an_unpinned_client_is_refused():
    tls = _tls()
    with tempfile.TemporaryDirectory(prefix="tls-") as t:
        a, _, c = _boxes(Path(t))
        tls.trust(c, "boxa", (a / "box.crt").read_text())   # c trusts a; a does not know c
        srv = _Peer(a, 1)
        try:
            got = _ask_stats(tls, c, srv.port)
        except (ssl_errors()) as exc:
            got = f"refused: {exc}"
        seen = srv.done()
        assert str(got).startswith("refused"), f"an unpinned client was answered: {got}"
        assert seen and "refused" in seen[0], f"the server answered an unpinned client: {seen}"


def tooth_an_unpinned_server_is_refused():
    tls = _tls()
    with tempfile.TemporaryDirectory(prefix="tls-") as t:
        _, b, c = _boxes(Path(t))
        tls.trust(c, "boxb", (b / "box.crt").read_text())   # c knows b and would answer it...
        srv = _Peer(c, 1)                                    # ...but b pins only a, not c
        try:
            got = _ask_stats(tls, b, srv.port)
        except (ssl_errors()) as exc:
            got = f"refused: {exc}"
        srv.done()
        assert str(got).startswith("refused"), f"a client dialed a server it has not pinned: {got}"


def tooth_a_certless_client_can_only_ask():
    tls = _tls()
    with tempfile.TemporaryDirectory(prefix="tls-") as t:
        a, _, c = _boxes(Path(t))
        srv = _Peer(a, 1)
        first = tls.first_contact(c, "127.0.0.1", srv.port)
        seen = srv.done()
        assert seen == [{"peer": None, "op": "ask"}], f"server saw the asker as {seen}"
        assert first["home"] == "boxa" and first["home_fingerprint"] == tls.identity(a)["fingerprint"], \
            f"first contact pinned {first}"
        assert tls.known(c) == {"boxa": tls.identity(a)["fingerprint"]}
        tls.hold_ask(a, "boxc", tls.identity(c)["cert"])
        assert tls.asks(a) == {"boxc": tls.identity(c)["fingerprint"]}
        assert "boxc" not in tls.known(a), "an ask was pinned before the operator accepted"
        tls.accept(a, "boxc")
        assert tls.known(a)["boxc"] == tls.identity(c)["fingerprint"] and not tls.asks(a)
        srv = _Peer(a, 1)
        reply = _ask_stats(tls, c, srv.port)
        assert srv.done() == [{"peer": "boxc", "op": "stats"}] and reply["ok"], \
            "an accepted ask did not become a working pin"
        tls.hold_ask(a, "boxd", tls.identity(c)["cert"])
        tls.decline(a, "boxd")
        assert "boxd" not in tls.asks(a) and "boxd" not in tls.known(a)


def ssl_errors():
    import ssl
    return (ssl.SSLError, ConnectionError, OSError)


TEETH = [tooth_identity_is_made_once_by_openssl, tooth_pinned_boxes_handshake_both_ways,
         tooth_an_unpinned_client_is_refused, tooth_an_unpinned_server_is_refused,
         tooth_a_certless_client_can_only_ask]


def test_a_box_pins_its_peers():
    reds = []
    for t in TEETH:
        try:
            t()
            print(f"  GREEN  {t.__name__}")
        except Exception as e:  # every tooth prints; none stops the rest
            reds.append(t.__name__)
            print(f"  RED    {t.__name__}")
            print(f"         {type(e).__name__}: {e}")
    # The declared composite tooth (PROVES "b"): hollow reads THIS name, so it prints green
    # only when every narrow tooth above passed.
    print(f"  {'RED   ' if reds else 'GREEN '} test_a_box_pins_its_peers")
    assert not reds, f"red teeth: {reds}"


if __name__ == "__main__":
    try:
        test_a_box_pins_its_peers()
    except AssertionError as e:
        print(e)
        sys.exit(1)
