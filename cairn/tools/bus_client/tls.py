"""tls — a box's identity and the pinned TLS both ends of a box-to-box bus speak (ticket 5183005fa134).

Akien 2026-11-04 (open-06cfefbe745e): "TLS sounds like the win to me, more in line with 'no
extra things to set up'". So: stdlib ``ssl`` over the bus's own TCP socket, no tunnel, no
token, no certificate authority, no extra process (outline 5.4.2.11.5).

THE IDENTITY. ``<dir>/box.key`` + ``<dir>/box.crt`` + ``<dir>/box.name``: an EC prime256v1 key
and a self-signed certificate, made by the ``openssl`` CLI — stdlib ssl cannot make
certificates and the ``cryptography`` package is on neither box (measured 2026-11-04: Linux
/usr/bin/openssl 3.5.5; akiendell Git's openssl 3.5.4). ``<dir>`` is ``<bus home>/tls`` by
default — instance-space, never git.

THE PIN. ``<dir>/known/<box>.pem`` holds each peer's certificate; the file IS the pin. Both
contexts trust exactly those certificates as anchors, and after every handshake ``peer_box``
checks the peer's SHA-256 fingerprint against the same folder again — so a certificate some
pinned key signed is still not a pinned box. Mutual: the server checks the client too.

THE ASK. The server's context asks for a client certificate but does not demand one
(``CERT_OPTIONAL``): a client that presents one must chain to a pin or the handshake fails; a
client that presents NONE is an asker, and the only op the bus answers it is ``ask`` — its
name and certificate, held at ``<dir>/asks/<box>.pem`` for the operator (outline 7.3.9.4, Q#23:
"any device should be able to ask, and the operator can decline, accept now, accept always").
``accept`` moves an ask into ``known/``. The asker pins the server's certificate on that same
first contact (``first_contact``) — trust on first use, both fingerprints printed so the two
operators can compare them by eye.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import socket as _socket
import ssl
import subprocess
from pathlib import Path

_NAME_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,62}$")
# Git for Windows ships openssl; PATH in a PowerShell often does not carry it (measured
# 2026-11-04 on akiendell: `where openssl` found both, mingw64 first). mingw64's is a native
# Windows build, so argv reaches it unmangled.
_WINDOWS_OPENSSL = (r"C:\Program Files\Git\mingw64\bin\openssl.exe",
                    r"C:\Program Files\Git\usr\bin\openssl.exe")


# The bus's LAN port: CAIRN_BUS_TCP_PORT, default 7419 (unassigned by IANA; free on both boxes,
# measured 2026-11-04). Here, not in the bus, because both ends need it and this is the end
# every box carries.
LAN_PORT_VAR = "CAIRN_BUS_TCP_PORT"
LAN_PORT = 7419


def lan_port() -> int:
    return int(os.environ.get(LAN_PORT_VAR) or LAN_PORT)


def check_name(name: str) -> str:
    if not _NAME_RE.match(name or ""):
        raise ValueError(f"not a box name: {name!r}")
    return name


def openssl() -> str:
    """The openssl CLI on this box, or a loud error naming where it looked."""
    found = shutil.which("openssl")
    if found:
        return found
    for cand in _WINDOWS_OPENSSL:
        if Path(cand).is_file():
            return cand
    raise FileNotFoundError("no openssl on PATH or at " + ", ".join(_WINDOWS_OPENSSL))


def fingerprint_der(der: bytes) -> str:
    return hashlib.sha256(der).hexdigest()


def fingerprint_pem(pem: str) -> str:
    """SHA-256 of the certificate's DER bytes, lowercase hex — what `openssl x509 -fingerprint
    -sha256` prints, without the colons."""
    return fingerprint_der(ssl.PEM_cert_to_DER_cert(pem))


def has_identity(d: str | Path) -> bool:
    d = Path(d)
    return all((d / f).is_file() for f in ("box.key", "box.crt", "box.name"))


def make_identity(d: str | Path, name: str) -> str:
    """Make the box identity once; return its certificate's fingerprint. An identity already
    there is kept — a second run never regenerates the key, because the peers pin it."""
    d = Path(d)
    check_name(name)
    if has_identity(d):
        return identity(d)["fingerprint"]
    d.mkdir(parents=True, exist_ok=True)
    key, crt = d / "box.key", d / "box.crt"
    r = subprocess.run([openssl(), "req", "-x509", "-newkey", "ec",
                        "-pkeyopt", "ec_paramgen_curve:prime256v1", "-nodes",
                        "-keyout", str(key), "-out", str(crt), "-days", "36500",
                        "-subj", f"/CN={name}",
                        "-addext", "basicConstraints=critical,CA:TRUE",
                        "-addext", "keyUsage=critical,digitalSignature,keyCertSign"],
                       capture_output=True, text=True, timeout=60)
    if r.returncode or not key.is_file() or not crt.is_file():
        raise RuntimeError("openssl could not make the box identity: "
                           + (r.stderr or r.stdout).strip()[-400:])
    if os.name != "nt":
        os.chmod(key, 0o600)
    (d / "box.name").write_text(name + "\n")
    return identity(d)["fingerprint"]


def identity(d: str | Path) -> dict:
    d = Path(d)
    pem = (d / "box.crt").read_text()
    return {"name": (d / "box.name").read_text().strip(), "cert": pem,
            "fingerprint": fingerprint_pem(pem)}


def _pems(folder: Path) -> dict[str, str]:
    return {p.stem: p.read_text() for p in sorted(folder.glob("*.pem"))} if folder.is_dir() else {}


def known(d: str | Path) -> dict[str, str]:
    """``{box name: fingerprint}`` for every pinned peer."""
    return {n: fingerprint_pem(pem) for n, pem in _pems(Path(d) / "known").items()}


def asks(d: str | Path) -> dict[str, str]:
    """``{box name: fingerprint}`` for every ask the operator has not answered."""
    return {n: fingerprint_pem(pem) for n, pem in _pems(Path(d) / "asks").items()}


def _put(folder: Path, name: str, pem: str) -> str:
    fp = fingerprint_pem(pem)                # refuses anything that is not a certificate
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{check_name(name)}.pem").write_text(pem)
    return fp


def trust(d: str | Path, name: str, pem: str) -> str:
    """Pin ``pem`` as box ``name``; return its fingerprint."""
    return _put(Path(d) / "known", name, pem)


def hold_ask(d: str | Path, name: str, pem: str) -> str:
    return _put(Path(d) / "asks", name, pem)


def accept(d: str | Path, name: str) -> str:
    """The operator's accept: the held ask becomes a pin."""
    src = Path(d) / "asks" / f"{check_name(name)}.pem"
    fp = trust(d, name, src.read_text())
    src.unlink()
    return fp


def decline(d: str | Path, name: str) -> None:
    (Path(d) / "asks" / f"{check_name(name)}.pem").unlink()


def _context(server: bool, d: Path, *, present: bool = True) -> ssl.SSLContext:
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER if server else ssl.PROTOCOL_TLS_CLIENT)
    ctx.minimum_version = ssl.TLSVersion.TLSv1_3
    if present:
        ctx.load_cert_chain(str(d / "box.crt"), str(d / "box.key"))
    return ctx


def _load_pins(ctx: ssl.SSLContext, d: Path) -> int:
    pems = _pems(d / "known")
    if pems:
        ctx.load_verify_locations(cadata="".join(pems.values()))
    return len(pems)


def client_context(d: str | Path) -> ssl.SSLContext:
    """Presents this box's certificate; trusts only the pinned peers."""
    d = Path(d)
    ctx = _context(False, d)
    ctx.check_hostname = False               # a pin names a certificate, not a hostname
    ctx.verify_mode = ssl.CERT_REQUIRED
    if not _load_pins(ctx, d):
        raise ssl.SSLError(f"no pinned boxes under {d / 'known'} — run cairn install")
    return ctx


def server_context(d: str | Path) -> ssl.SSLContext:
    """Checks a presented client certificate against the pins; a client presenting none may
    only ask (see THE ASK). Built per connection, so an accepted ask counts at once."""
    d = Path(d)
    ctx = _context(True, d)
    ctx.verify_mode = ssl.CERT_OPTIONAL
    if not _load_pins(ctx, d):
        # Nothing pinned yet: an empty trust store would accept no presented certificate
        # anyway, and loading our own keeps the context well-formed.
        ctx.load_verify_locations(cadata=(d / "box.crt").read_text())
    return ctx


def peer_box(d: str | Path, conn: ssl.SSLSocket) -> str | None:
    """The pinned box this connection's peer is, by fingerprint — or None (no certificate, or
    one that is not pinned)."""
    der = conn.getpeercert(binary_form=True)
    if not der:
        return None
    fp = fingerprint_der(der)
    return next((n for n, pinned in known(d).items() if pinned == fp), None)


def dial(d: str | Path, host: str, port: int, *, timeout: float) -> ssl.SSLSocket:
    """A pinned, mutual TLS connection to the bus at ``host:port`` — refused unless the
    server's certificate is pinned here by fingerprint."""
    d = Path(d)
    raw = _socket.create_connection((host, port), timeout=timeout)
    try:
        conn = client_context(d).wrap_socket(raw)
    except BaseException:
        raw.close()
        raise
    if peer_box(d, conn) is None:
        fp = fingerprint_der(conn.getpeercert(binary_form=True) or b"")
        conn.close()
        raise ssl.SSLError(f"{host}:{port} presented {fp}, which is not pinned under {d / 'known'}")
    return conn


def first_contact(d: str | Path, host: str, port: int, *, timeout: float = 10.0) -> dict:
    """An attaching box's first touch of a home: pin the home's certificate (trust on first
    use) and leave this box's certificate there as an ask. Returns both fingerprints and the
    home's reply. Pinned calls are refused until the home's operator accepts."""
    d = Path(d)
    me = identity(d)
    ctx = _context(False, d, present=False)  # presenting none is what makes this an ask
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE           # nothing to pin against yet: this IS the pinning
    with _socket.create_connection((host, port), timeout=timeout) as raw:
        with ctx.wrap_socket(raw) as conn:
            home_pem = ssl.DER_cert_to_PEM_cert(conn.getpeercert(binary_form=True))
            conn.sendall((json.dumps({"op": "ask", "box": me["name"], "cert": me["cert"]})
                          + "\n").encode())
            with conn.makefile("r", encoding="utf-8") as fh:
                line = fh.readline()
    reply = json.loads(line) if line else {"ok": False, "error": "the home closed without an answer"}
    home = check_name(reply.get("box") or host.split(".")[0])
    return {"home": home, "home_fingerprint": trust(d, home, home_pem),
            "mine": me["fingerprint"], "reply": reply}
