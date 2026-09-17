"""Proof for web_server (web-server ticket, child b) — the routing + render core, no socket.

The web server is a thin PRESENTATION surface (Law 7): the devices on the heartbeat across the
top (the roster, child c), the selected device's ACTIVE page below (its panes, child a). It owns
NO device state — everything is pulled live from the heartbeat and the target device's shim. This
proof composes a REAL ground_loop + REAL BaseShims + a REAL device, so it shows the whole
route → fetch-through-the-heartbeat → render chain WITHOUT binding a socket (the socket lives in
daemon.py, the thin OS wrapper this stays provable without).

Teeth a hollow surface could not pass:
  - THE NAV IS THE ROSTER: '/' renders every device on the heartbeat, in order, and invites a pick.
  - A DEVICE PAGE RENDERS ITS PANES: '/device/<id>' shows that device's STATUS+SETTINGS floor and
    its declared panes — pulled live through the heartbeat, not stored on the web server.
  - AN UNKNOWN DEVICE IS A LOUD, COHERENT 404 that STILL renders the nav (Law 7 — the surface
    collapses the error into a legible shape you can navigate away from, never a raw crash).
  - EVERYTHING A DEVICE SAYS IS ESCAPED: a device whose state contains '<script>' is rendered as
    TEXT, never live markup — the surface never lets a device's data become the page's markup.
  - AN ABSENT PANE RENDERS ITS REASON (loud, not silent): child a's absent-with-reason survives to
    the surface.
  - THE WEB SERVER OWNS NO STATE: it is a device (Form v0 #2) and holds nothing — its state() is
    pulled live (served count + the current roster), never a cached copy of device internals.
  - THE GRADUATION TO STARLETTE (ticket 72e8e3509287, five teeth at the foot, declared in PROVES):
    one web server in the tree; logic stays out of the transport; every pane URL renders
    identically through the ASGI app driven in-process over a raw scope, and a WebSocket is
    accepted and pushed to; no dependency beyond the graft source; the graft names its ticket
    and its source.

Runnable bare (NO socket, NO DB, NO framework):
    python3 cairn/devices/web_server/proofs/test_web_server.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# The trace wire fires on every serve(); a proof run is not a real firing, so its
# records go to a scratch berth — the live denominator stays honest.
import os, tempfile  # noqa: E401
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402
os.environ["CAIRN_LB_TRACE_ROOT"] = str(scratch_dir("ws-proof-traces-"))

from cairn.tools.base.core_values import CoreValuesMixin
from cairn.tools.base.device import BaseDevice
from cairn.tools.base.shim import BaseShim
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice
from cairn.devices.web_server.server import WebServerDevice

# Ticket 72e8e3509287 (the web server graduates to Starlette) — five numbered proves_red clauses,
# one tooth each; the teeth stand at the foot of this file.
PROVES = {
    "72e8e3509287": {
        "1": "test_there_is_one_web_server",
        "2": "test_device_logic_stays_out_of_the_transport",
        "3": "test_existing_pane_urls_render_identically_through_the_asgi_app",
        "4": "test_the_graft_brings_no_dependency_beyond_its_source",
        "5": "test_the_graft_carries_its_ticket_and_proof",
    },
}



class _Device(BaseDevice):
    """A minimal device with a Form v0 #2 surface and optional declared panes. Its state can
    carry a hostile string, to prove escaping."""

    def __init__(self, name, *, hostile=False, extra_panes=None) -> None:
        super().__init__()
        self._name = name
        self._hostile = hostile
        self._extra = extra_panes or []

    def intention(self) -> dict:
        return {"what": f"device {self._name}", "why": "a spec device for the surface proof"}

    def state(self) -> dict:
        return {"note": "<script>alert(1)</script>" if self._hostile else "resting"}

    def settings(self) -> dict:
        return {"verbosity": "loud"}

    def declared_panes(self) -> list[dict]:
        return self._extra


class _Shim(BaseShim):
    def __init__(self, device: _Device) -> None:
        super().__init__(bus=None)
        self._dev = device

    @property
    def device_id(self) -> str:
        return self._dev.intention()["what"].split()[-1]  # the name

    def device(self):
        return self._dev


def _wired():
    """A real heartbeat with two real device-shims subscribed, and a web server over it."""
    gl = GroundLoopDevice()
    alpha = _Shim(_Device("alpha"))
    beta = _Shim(_Device("beta", hostile=True, extra_panes=[
        {"kind": "logging", "label": "Log", "handler": None},                     # absent
        {"kind": "interaction", "label": "Chat", "handler": lambda: {"turns": 0}},  # data
    ]))
    gl.subscribe(alpha)
    gl.subscribe(beta)
    web = WebServerDevice(gl, port=8799)
    # SILENCED (ticket a-device-logs-without-being-wired, 2026-08-18): un-wired now WRITES to
    # ~/.cairn/logs/<device>/<instance>/ instead of holding, which would both empty the lists this
    # proof reads and seed the live tree from a proof. Holding is now asked for, not an accident.
    gl.set_diagnostic_receiver(None)
    web.set_diagnostic_receiver(None)
    return web, gl


def test_the_nav_is_the_roster():
    web, _ = _wired()
    status, ctype, body = web.serve("/")
    assert status == 200 and "text/html" in ctype
    assert '/device/alpha' in body and '/device/beta' in body, "the nav links every device on the heartbeat"
    assert body.index("alpha") < body.index("beta"), "the nav keeps roster (subscription) order"
    assert "Pick a device" in body, "the landing invites a pick"


def test_a_device_page_renders_its_panes():
    web, _ = _wired()
    status, _c, body = web.serve("/device/alpha")
    assert status == 200
    # The STATUS + SETTINGS floor both render for a device with no declared panes.
    assert ">Status<" in body and ">Settings<" in body, "the floor panes render"
    assert "a spec device for the surface proof" in body, "the device's own reported DATA is shown"


def test_an_unknown_device_is_a_coherent_404_that_still_shows_the_nav():
    web, _ = _wired()
    status, _c, body = web.serve("/device/ghost")
    assert status == 404, "an unknown device is a loud 404, not a pretend page"
    assert "not on the heartbeat" in body, "the 404 says why, in a coherent shape (Law 7)"
    assert '/device/alpha' in body, "the nav still renders so you can navigate away"


def test_everything_a_device_says_is_escaped():
    web, _ = _wired()
    _s, _c, body = web.serve("/device/beta")  # beta's state carries <script>
    assert "<script>alert(1)</script>" not in body, "a device's data must never become live markup"
    assert "&lt;script&gt;" in body, "the hostile string is rendered as escaped TEXT (Law 7)"


def test_an_absent_pane_renders_its_reason():
    web, _ = _wired()
    _s, _c, body = web.serve("/device/beta")  # beta's Log pane has no handler
    assert "absent" in body and "unwired" in body, "an absent pane says why, loudly (not silent)"
    assert "Chat" in body, "the panes after the absent one still render"


def test_the_web_server_owns_no_state_and_is_a_device():
    web, gl = _wired()
    assert isinstance(web, CoreValuesMixin), "the web server is a device (Law 2)"
    assert list(web.introspect()) == ["intention", "state", "settings", "other"], "Form v0 #2 order"
    # Its state is pulled live: the roster it reports IS the heartbeat's, not a stored copy.
    assert web.state()["roster"] == gl.roster(), "the web server holds no cached copy — it reads live"
    before = web.state()["served"]
    web.serve("/")
    assert web.state()["served"] == before + 1, "the only thing it counts is its own serving"


def test_the_crossings_are_no_longer_silent():
    """The silent_device disposition (troubles/silent-devices-2026-07-27.json): a request
    crossing the surface leaves ONE breadcrumb — per crossing (a request is an event, not
    a pulse) — and a 404 breadcrumbs the same as a 200: the surface may collapse an error
    into a coherent page (Law 7), never the record that it happened. The device is SILENCED in
    ``_wired`` so the crossings hold here and this proof leaves no trail in the live logs tree."""
    web, _ = _wired()
    assert web.held_diagnostics() == [], "construction is not a crossing"
    web.serve("/")
    web.serve("/device/ghost")
    held = web.held_diagnostics()
    assert [h["gate"] for h in held] == ["serve", "serve"], (
        f"one breadcrumb per request, got {[h['gate'] for h in held]}"
    )
    assert held[0]["pointer"] == "/" and held[0]["values"] == {"status": 200}
    assert held[1]["pointer"] == "/device/ghost" and held[1]["values"] == {"status": 404}, \
        "the coherent 404 page does not collapse the RECORD of the 404 — the breadcrumb says it"
    assert all(h["home"] == "held" for h in held), \
        "with no receiver wired the records HOLD (Law 7) — never silently dropped"


def test_the_trace_wire_counts_a_pass_and_a_refusal():
    """Deploy pass 2026-08-01: a 200 traces door_pass, a 404 traces send_back with the
    lack named — the denominator exists, greens included (the Leah rule)."""
    from cairn.machines.learning_block import learning_block as lb
    web, _ = _wired()
    seen_before = len(lb.read_trace("web_server"))
    web.serve("/device/alpha")
    web.serve("/device/ghost")
    recs = lb.read_trace("web_server")[seen_before:]
    events = [r["event"] for r in recs]
    assert events == ["door_pass", "send_back"], f"both firings counted: {events}"
    assert "404" in recs[1]["data"]["lacks"][0], "the refusal names its lack"
    assert all(r["consumer"] == "training" for r in recs), "the denominator must not expire"


# ---------------------------------------------------------------------------------------------
# TICKET 72e8e3509287 — the web server graduates to Starlette. The proves_red falsifier has five
# numbered clauses, one tooth each. Every tooth resolves the LISTENER at call time (importlib,
# never a module-level import) so a hollow reading that reverts listener.py to the stdlib version
# still reaches a check and prints a red tooth rather than dying on import.
# ---------------------------------------------------------------------------------------------

_LISTENER_REL = "cairn/devices/web_server/listener.py"


def _listener_module():
    import importlib
    return importlib.import_module("cairn.devices.web_server.listener")


def _listener_source() -> str:
    return (_REPO_ROOT / _LISTENER_REL).read_text(encoding="utf-8")


def _py_files_under(root: Path):
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        yield p


def _asgi_http(app, path: str, *, method: str = "GET", body: bytes = b"") -> tuple[int, str, str]:
    """Drive the ASGI app IN-PROCESS over a raw scope — no socket, no client library. This is the
    transport the listener hands to uvicorn, exercised exactly as uvicorn would, minus the bind."""
    import asyncio

    scope = {"type": "http", "asgi": {"version": "3.0"}, "http_version": "1.1", "method": method,
             "scheme": "http", "path": path, "raw_path": path.encode(), "query_string": b"",
             "root_path": "", "headers": [(b"host", b"proof")], "client": ("127.0.0.1", 1),
             "server": ("proof", 80)}
    sent: list[dict] = []
    handed = {"body": False}

    async def receive():
        if handed["body"]:
            return {"type": "http.disconnect"}
        handed["body"] = True
        return {"type": "http.request", "body": body, "more_body": False}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    start = next(m for m in sent if m["type"] == "http.response.start")
    headers = {k.decode(): v.decode() for k, v in start["headers"]}
    text = b"".join(m.get("body", b"") for m in sent if m["type"] == "http.response.body").decode("utf-8")
    return start["status"], headers.get("content-type", ""), text


def _asgi_websocket(app, path: str) -> list[dict]:
    """Open a WebSocket over a raw scope: connect, let the server push, then disconnect. Returns
    every message the server sent."""
    import asyncio

    scope = {"type": "websocket", "asgi": {"version": "3.0"}, "scheme": "ws", "path": path,
             "raw_path": path.encode(), "query_string": b"", "root_path": "",
             "headers": [(b"host", b"proof")], "client": ("127.0.0.1", 1), "server": ("proof", 80),
             "subprotocols": []}
    inbound = [{"type": "websocket.connect"}, {"type": "websocket.disconnect", "code": 1000}]
    sent: list[dict] = []

    async def receive():
        return inbound.pop(0) if inbound else {"type": "websocket.disconnect", "code": 1000}

    async def send(message):
        sent.append(message)

    asyncio.run(app(scope, receive, send))
    return sent


def test_there_is_one_web_server():
    """Clause (1): no second web server. Census every module in the tree that BINDS a server
    (uvicorn.Server, http.server's HTTPServer/ThreadingHTTPServer, serve_forever) and keep the
    ones that are a PRESENTATION surface — they render text/html or hold the WebServerDevice.
    Exactly one may: the listener. (Measured 2026-09-17: cairn/machines/openai_wire/serve.py also
    builds a ThreadingHTTPServer — an OpenAI-shaped JSON wire with injected answerers, no page,
    no pane, no html; the one-web-server rule is about FACES, and the tooth says so by predicate
    rather than by exempting a name.)"""
    import re
    binder = re.compile(r"uvicorn\.Server\(|ThreadingHTTPServer\(|HTTPServer\(|serve_forever\(")
    face = re.compile(r"text/html|WebServerDevice|web_server\.render|web_server\.server")
    binders, faces = [], []
    for p in _py_files_under(_REPO_ROOT / "cairn"):
        if "proofs" in p.parts:
            continue
        src = p.read_text(encoding="utf-8", errors="replace")
        if binder.search(src):
            rel = str(p.relative_to(_REPO_ROOT))
            binders.append(rel)
            if face.search(src):
                faces.append(rel)
    assert _LISTENER_REL in binders, f"the listener binds the one server; binders: {binders}"
    assert faces == [_LISTENER_REL], (
        f"exactly one module may serve a FACE — the web_server listener; found {faces} "
        f"(all binders: {binders})")


def test_device_logic_stays_out_of_the_transport():
    """Clause (2): routing and rendering are server.py and render.py; the listener is TRANSPORT.
    Measured on the source, not asserted: the listener's request handlers call the device's
    ``serve`` and carry no markup, no content-type, no route table beyond the catch-all; the
    listener never imports render/html; and the logic files never import the transport."""
    import ast
    src = _listener_source()
    tree = ast.parse(src)
    strings = [n.value for n in ast.walk(tree) if isinstance(n, ast.Constant) and isinstance(n.value, str)]
    leaked = [s for s in strings if "<" in s and ">" in s or "text/html" in s]
    assert leaked == [], f"markup or a content-type in the transport is rendering leaking upward: {leaked}"
    imported = {(n.module or "") for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)}
    imported |= {a.name for n in ast.walk(tree) if isinstance(n, ast.Import) for a in n.names}
    assert not any(m.endswith("render") or m == "html" for m in imported), \
        f"the listener imports a renderer: {sorted(imported)}"
    handlers = [n for n in tree.body if isinstance(n, ast.AsyncFunctionDef) and n.name.startswith("_handle_")
                and "ws" not in n.name]
    assert len(handlers) >= 2, "a GET and a POST handler are the whole HTTP face"
    for h in handlers:
        calls = [ast.unparse(c.func) for c in ast.walk(h) if isinstance(c, ast.Call)]
        assert "_device.serve" in calls, f"{h.name} must route through the device's serve(): {calls}"
    for logic in ("server.py", "render.py"):
        lsrc = (_REPO_ROOT / "cairn/devices/web_server" / logic).read_text(encoding="utf-8")
        assert "starlette" not in lsrc and "uvicorn" not in lsrc, \
            f"{logic} is the logic layer and must not know the transport"


def test_existing_pane_urls_render_identically_through_the_asgi_app():
    """Clause (3): no pane URL regresses — the Starlette app, driven in-process over a raw ASGI
    scope, returns byte-for-byte what ``WebServerDevice.serve`` returns for every URL the
    surface teeth above exercise, 200s and the 404 alike; a POST reaches serve() with its body.
    And proves_green (2): a WebSocket connection is accepted and RECEIVES A SERVER PUSH — the
    capability the stdlib listener lacked — with the trouble lane asked over the bus, never
    imported."""
    listener = _listener_module()
    web, _ = _wired()

    class _Bus:
        asked: list[dict] = []

        def request(self, **kw):
            self.asked.append(kw)
            return {"body": {"troubles": [{"id": "t-1", "standing": "live", "why": "a fixture trouble",
                                           "count": 2}]}}

    saved = (listener._device, listener._bus)
    listener._device, listener._bus = web, _Bus()
    try:
        app = listener._make_app()
        for path in ("/", "/device/alpha", "/device/beta", "/device/ghost", "/nowhere"):
            expect = web.serve(path)
            got = _asgi_http(app, path)
            assert got[0] == expect[0], f"{path}: status {got[0]} through the app, {expect[0]} direct"
            assert got[2] == expect[2], f"{path}: the body through the app differs from serve()'s"
            assert expect[1].split(";")[0] in got[1], f"{path}: content-type {got[1]!r} vs {expect[1]!r}"
        status, _ct, body = _asgi_http(app, "/device/alpha", method="POST", body=b"say=hello")
        assert status == web.serve("/device/alpha", method="POST", body="say=hello")[0], \
            "a POST reaches serve() with its body"
        pushed = _asgi_websocket(app, "/ws/troubles")
        kinds = [m["type"] for m in pushed]
        assert kinds[0] == "websocket.accept", f"the upgrade is accepted first: {kinds}"
        sends = [m for m in pushed if m["type"] == "websocket.send"]
        assert sends, f"the server PUSHES without being asked — that is the capability: {kinds}"
        import json as _json
        payload = _json.loads(sends[0]["text"])
        assert payload == [{"id": "t-1", "standing": "live", "why": "a fixture trouble", "count": 2}], payload
        assert listener._bus.asked and listener._bus.asked[0]["to"] == "trouble" \
            and listener._bus.asked[0]["verb"] == "live", "the lane is ASKED over the bus"
        assert len(listener._ws_clients) == 0, "a disconnected client is dropped from the set"
    finally:
        listener._device, listener._bus = saved


def test_the_graft_brings_no_dependency_beyond_its_source():
    """Clause (4): the graft source (TheIgors' utility_closet_server.py) imports the stdlib,
    starlette and uvicorn — the listener may import those and cairn itself, nothing else."""
    import ast
    allowed_roots = set(sys.stdlib_module_names) | {"starlette", "uvicorn", "cairn"}
    tree = ast.parse(_listener_source())
    roots = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            roots |= {a.name.split(".")[0] for a in n.names}
        elif isinstance(n, ast.ImportFrom) and n.module:
            roots.add(n.module.split(".")[0])
    extra = sorted(roots - allowed_roots)
    assert extra == [], f"the listener grew a dependency the graft source never had: {extra}"
    assert {"starlette", "uvicorn"} <= roots, f"the listener IS the Starlette/uvicorn transport: {sorted(roots)}"


def test_the_graft_carries_its_ticket_and_proof():
    """Clause (5): bytes enter by graft with a ticket and a proof (Law 8). The listener's own
    docstring names the ticket and the graft source; this proof declares a tooth for every
    clause of that ticket."""
    import ast
    doc = ast.get_docstring(ast.parse(_listener_source())) or ""
    assert "72e8e3509287" in doc, "the listener names the graft ticket"
    assert "utility_closet_server.py" in doc, "the listener names its graft source"
    assert set(PROVES["72e8e3509287"]) == {"1", "2", "3", "4", "5"}, "every clause has a tooth"
    for tooth in PROVES["72e8e3509287"].values():
        assert callable(globals().get(tooth)), f"declared tooth {tooth} exists"



def _main() -> int:
    red: list[str] = []
    for check in (test_the_nav_is_the_roster,
                  test_a_device_page_renders_its_panes,
                  test_an_unknown_device_is_a_coherent_404_that_still_shows_the_nav,
                  test_everything_a_device_says_is_escaped,
                  test_an_absent_pane_renders_its_reason,
                  test_the_web_server_owns_no_state_and_is_a_device,
                  test_the_crossings_are_no_longer_silent,
                  test_the_trace_wire_counts_a_pass_and_a_refusal,
                  test_there_is_one_web_server,
                  test_device_logic_stays_out_of_the_transport,
                  test_existing_pane_urls_render_identically_through_the_asgi_app,
                  test_the_graft_brings_no_dependency_beyond_its_source,
                  test_the_graft_carries_its_ticket_and_proof):
        # EVERY TOOTH RUNS AND EACH RED IS PRINTED AS ITSELF. A run that stops at the first red
        # leaves every later tooth unprinted, and a hollow reading (cairn test --hollow) cannot
        # tell "this tooth caught the reversion" from "this tooth never ran". Ticket c5b6b128a376.
        try:
            check()
        except Exception as e:  # noqa: BLE001 — the red is the finding, printed by name
            import traceback
            traceback.print_exc()
            print(f"  FAIL  {check.__name__}: {type(e).__name__}: {e}")
            red.append(check.__name__)
            continue
        print(f"  PASS  {check.__name__}")
    if red:
        print(f"red — web_server: {len(red)} tooth/teeth failed: {', '.join(red)}")
        return 1
    print("green — web_server: the nav IS the roster, a device page renders its panes pulled live "
          "through the heartbeat, an unknown device is a coherent 404, every device string is "
          "escaped, absent panes say why, and the surface owns no state")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
