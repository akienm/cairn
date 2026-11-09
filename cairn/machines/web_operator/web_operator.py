"""cairn/machines/web_operator/web_operator.py — a browser of the holder's own, driven over WebDriver.

The general machine a device holds to operate web pages, for reading and other purposes
(outline 17.14; ticket 7a94c34cba52). Akien 2026-11-05 (Q#28): "i believe we built one for you,
but we need a general one. i envision a couple of different devices that would use this, the
librarian is just the first." The one built for CC is ~/.local/bin/ccfox — one geckodriver on
fixed port 4444, one profile, one state directory. This ports its verbs onto a class whose every
address derives from the HOLDER, so two holders never share a port, a profile or a session:

  port, websocket port   the first free ones, bound and released at start, recorded in state
                         (geckodriver's BiDi port defaults to 9222, so two holders left at the
                         default collide on it)
  profile                <profile root>/cairn-<holder>-<n>-profile; the root is
                         $CAIRN_WEB_OPERATOR_PROFILE_ROOT, default ~/snap/firefox/common/ — a snap
                         Firefox cannot reach hidden folders in home, nor the host /tmp
  state                  machine_path(holder, n, 'web_operator')/state.json — the holder's to own
                         (Law 6); the geckodriver log beside it
  secrets                read from the holder's own .env as a Secret
                         (secret:instance:///devices/<holder>/<n>/.env#KEY, cairn/tools/dataref), typed
                         into the page, never printed and never stored

Headless unless the holder asks for a window. The verbs are ccfox's: start, stop, go, where,
text, find, click, type, secret, key, shot, js. A refusal from the driver raises
WebOperatorError naming the WebDriver error, never a quiet empty answer (Law 7).
"""
from __future__ import annotations

import base64
import json
import os
import signal
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

from cairn.tools.base.address import machine_path
from cairn.tools.base.diagnostic import DiagnosticBase
from cairn.tools.dataref import Secret

MACHINE = "web_operator"
PROFILE_ROOT_ENV = "CAIRN_WEB_OPERATOR_PROFILE_ROOT"
DEFAULT_PROFILE_ROOT = Path.home() / "snap" / "firefox" / "common"
GECKODRIVER_ENV = "CAIRN_WEB_OPERATOR_GECKODRIVER"
FIREFOX_ENV = "CAIRN_WEB_OPERATOR_FIREFOX"
# The snap's own binaries, run directly. Measured 2026-11-06: under no_new_privs (every proof runs
# inside the tester's bwrap seal, which sets it) snap-confine refuses to start ANY snap ("has
# elevated permissions and is not confined but should be"), so /snap/bin/geckodriver exits 1.
# The binaries inside the squashfs run under NNP and outside it alike, so the holder and the proof
# take ONE path. The price, said plainly: Firefox runs without the snap's AppArmor confinement.
SNAP_LIB = Path("/snap/firefox/current/usr/lib/firefox")
ELEMENT = "element-6066-11e4-a52e-4f735466cecf"
KEYS = {"enter": "", "tab": "", "escape": ""}


class WebOperatorError(Exception):
    """The driver refused, or the holder has no live browser. Loud, named, never an empty answer."""


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _binaries() -> tuple[str, str | None]:
    """(geckodriver, firefox binary or None) — the env override, else the snap's inner binaries,
    else geckodriver on PATH finding Firefox itself."""
    gd = os.environ.get(GECKODRIVER_ENV) or (str(SNAP_LIB / "geckodriver")
                                             if (SNAP_LIB / "geckodriver").exists() else "geckodriver")
    ff = os.environ.get(FIREFOX_ENV) or (str(SNAP_LIB / "firefox") if (SNAP_LIB / "firefox").exists() else None)
    return gd, ff


def _alive(pid: int | None) -> bool:
    if not pid:
        return False
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


class WebOperator(DiagnosticBase):
    """One holder's browser: ``WebOperator('librarian', 0).start()``."""

    def __init__(self, holder: str, instance: int = 0, roots: dict[str, Path] | None = None,
                 headless: bool = True, profile_root: Path | str | None = None) -> None:
        super().__init__()
        self.holder = str(holder)
        self.instance = int(instance)
        self.roots = roots
        self.headless = headless
        self.home = machine_path(self.holder, self.instance, MACHINE, roots=roots)
        root = Path(profile_root or os.environ.get(PROFILE_ROOT_ENV) or DEFAULT_PROFILE_ROOT)
        self.profile = root / f"cairn-{self.holder}-{self.instance}-profile"

    # -- state: the holder's, at its machine_path ---------------------------------------------
    def state(self) -> dict:
        f = self.home / "state.json"
        return json.loads(f.read_text()) if f.is_file() else {}

    def _save(self, d: dict) -> None:
        self.home.mkdir(parents=True, exist_ok=True)
        tmp = self.home / "state.json.tmp"
        tmp.write_text(json.dumps(d, indent=1, sort_keys=True) + "\n")
        tmp.replace(self.home / "state.json")

    # -- the wire ------------------------------------------------------------------------------
    def _base(self) -> str:
        port = self.state().get("port")
        if not port:
            raise WebOperatorError(f"{self.holder}/{self.instance}: no browser; start it first")
        return f"http://127.0.0.1:{port}"

    def _call(self, method: str, path: str, body: dict | None = None, base: str | None = None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request((base or self._base()) + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                return json.load(r)["value"]
        except urllib.error.HTTPError as e:
            v = json.load(e).get("value", {})
            msg = (v.get("message") or "").splitlines()
            raise WebOperatorError(f"{v.get('error')}: {msg[0] if msg else ''}") from None
        except OSError as e:
            raise WebOperatorError(f"{self.holder}/{self.instance}: driver unreachable: {e}") from None

    def _driver_up(self, port: int) -> bool:
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{port}/status", timeout=2)
            return True
        except OSError:
            return False

    def _session_alive(self) -> bool:
        st = self.state()
        if not st.get("session") or not st.get("port"):
            return False
        try:
            with urllib.request.urlopen(f"http://127.0.0.1:{st['port']}/session/{st['session']}/url",
                                        timeout=5) as r:
                return r.status == 200
        except OSError:
            return False

    def _sid(self) -> str:
        if not self._session_alive():
            raise WebOperatorError(f"{self.holder}/{self.instance}: no live browser; start it first")
        return self.state()["session"]

    # -- the verbs -----------------------------------------------------------------------------
    def start(self) -> None:
        if self._session_alive():
            return
        self.stop(quiet=True)
        self.home.mkdir(parents=True, exist_ok=True)
        self.profile.mkdir(parents=True, exist_ok=True)
        port, ws = _free_port(), _free_port()
        log = open(self.home / "geckodriver.log", "a")
        gd, ff = _binaries()
        proc = subprocess.Popen([gd, "--host", "127.0.0.1", "--port", str(port),
                                 "--websocket-port", str(ws)],
                                stdout=log, stderr=log, stdin=subprocess.DEVNULL,
                                start_new_session=True)
        log.close()
        for _ in range(100):
            if self._driver_up(port):
                break
            if proc.poll() is not None:
                raise WebOperatorError(f"geckodriver exited {proc.returncode}; see {self.home / 'geckodriver.log'}")
            time.sleep(0.2)
        else:
            raise WebOperatorError(f"geckodriver did not come up; see {self.home / 'geckodriver.log'}")
        args = ["-profile", str(self.profile)] + (["-headless"] if self.headless else [])
        options = {"args": args, **({"binary": ff} if ff else {})}
        caps = {"capabilities": {"alwaysMatch": {"browserName": "firefox", "moz:firefoxOptions": options}}}
        st = {"port": port, "websocket_port": ws, "driver_pid": proc.pid,
              "profile": str(self.profile), "headless": self.headless, "session": None}
        self._save(st)
        v = self._call("POST", "/session", caps, base=f"http://127.0.0.1:{port}")
        st["session"] = v["sessionId"]
        self._save(st)

    def stop(self, quiet: bool = False) -> None:
        st = self.state()
        if self._session_alive():
            try:
                self._call("DELETE", f"/session/{st['session']}")
            except WebOperatorError:
                if not quiet:
                    raise
        pid = st.get("driver_pid")
        if _alive(pid):
            try:
                os.killpg(pid, signal.SIGTERM)
            except OSError:
                os.kill(pid, signal.SIGTERM)
        for _ in range(75):
            left = subprocess.run(["pgrep", "-f", str(self.profile)], capture_output=True,
                                  text=True).stdout.split()
            if not _alive(pid) and not left:
                break
            time.sleep(0.2)
        else:
            for p in left:
                try:
                    os.kill(int(p), signal.SIGKILL)
                except OSError:
                    pass
        if st:
            st.update(session=None, driver_pid=None)
            self._save(st)

    def go(self, url: str) -> None:
        self._call("POST", f"/session/{self._sid()}/url", {"url": url})

    def where(self) -> tuple[str, str]:
        s = self._sid()
        return self._call("GET", f"/session/{s}/url"), self._call("GET", f"/session/{s}/title")

    def _matches(self, css: str) -> list:
        return self._call("POST", f"/session/{self._sid()}/elements", {"using": "css selector", "value": css})

    def _nth(self, css: str, n: int = 0) -> str:
        els = self._matches(css)
        if len(els) <= n:
            raise WebOperatorError(f"{len(els)} match(es) for {css!r}, wanted index {n}")
        return els[n][ELEMENT]

    def text(self, css: str | None = None) -> str:
        s = self._sid()
        if css:
            return self._call("GET", f"/session/{s}/element/{self._nth(css)}/text")
        return self.js("return document.body.innerText")

    def find(self, css: str) -> list[list]:
        script = ("return arguments[0].map((e,i)=>[i,e.tagName.toLowerCase(),e.id||e.name||'',"
                  "(e.innerText||e.value||e.placeholder||e.getAttribute('aria-label')||'').trim().slice(0,60)])")
        return self._call("POST", f"/session/{self._sid()}/execute/sync",
                          {"script": script, "args": [self._matches(css)]})

    def click(self, css: str, n: int = 0) -> None:
        self._call("POST", f"/session/{self._sid()}/element/{self._nth(css, n)}/click", {})

    def type(self, css: str, text: str, n: int = 0) -> None:
        s, e = self._sid(), self._nth(css, n)
        self._call("POST", f"/session/{s}/element/{e}/clear", {})
        self._call("POST", f"/session/{s}/element/{e}/value", {"text": text})

    def secret(self, css: str, key: str, n: int = 0) -> None:
        """Type KEY's value from the holder's .env. The value is never returned, printed or stored."""
        ref = Secret(f"secret:instance:///devices/{self.holder}/{self.instance}/.env#{key}", self.roots)
        self.type(css, ref.secret, n)

    def key(self, name: str) -> None:
        k = KEYS[name.lower()]
        self._call("POST", f"/session/{self._sid()}/actions", {"actions": [{"type": "key", "id": "kb", "actions": [
            {"type": "keyDown", "value": k}, {"type": "keyUp", "value": k}]}]})

    def shot(self, path: Path | str) -> Path:
        p = Path(path)
        p.write_bytes(base64.b64decode(self._call("GET", f"/session/{self._sid()}/screenshot")))
        return p

    def js(self, script: str, *args):
        return self._call("POST", f"/session/{self._sid()}/execute/sync", {"script": script, "args": list(args)})
