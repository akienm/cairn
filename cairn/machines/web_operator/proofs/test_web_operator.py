"""Proof: a device holds the web_operator machine to operate web pages in a browser of its own.

Ticket 7a94c34cba52 (outline 17.14, 9.3.8). Measured 2026-11-05: the only web-operating code
on the box was ~/.local/bin/ccfox — one geckodriver on fixed port 4444, one profile, one state
directory, CC's alone. This machine is the general one: each holder (a device instance) gets
its own geckodriver port, its own Firefox profile, its own session, and its state at
machine_path(holder, n, 'web_operator').

The teeth drive a real headless Firefox against a scratch http.server fixture on localhost,
under a scratch instance root, with profiles under a scratch directory inside the snap's own
space (a snap Firefox cannot reach hidden folders in home, nor the host /tmp):

  1. alpha/0 starts headless, opens the fixture page, text() returns its visible text.
  2. type('#q','hello') then click('#go') writes 'got hello' into #out; text('#out') reads it.
  3. alpha/0 and beta/0 at once hold different ports, profiles and session ids; each where()
     reports its own page.
  4. each holder's port, session id and profile pointer are written under its
     machine_path(holder, 0, 'web_operator') and nowhere else in the scratch instance root;
     ~/.cairn/devices/cc/0/ccfox is byte-identical before and after.
  5. secret(css, KEY) types KEY's value from the holder's scratch .env; the value appears on
     no stdout, stderr or file under the machine's state.
  6. stop() on alpha ends its browser and geckodriver (its port refuses connections) while
     beta's session still answers.
  7. `python3 -m cairn.machines.web_operator --holder alpha/0 text` prints what text() returns.

    python3 cairn/machines/web_operator/proofs/test_web_operator.py
"""
from __future__ import annotations

import contextlib
import hashlib
import http.server
import io
import json
import os
import secrets
import shutil
import socket
import subprocess
import sys
import threading
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "7a94c34cba52": {
        "1": "tooth_1_text_reads_the_fixture_page",
        "2": "tooth_2_type_and_click_drive_the_form",
        "3": "tooth_3_two_holders_hold_their_own_browser",
        "4": "tooth_4_state_berths_under_the_holder_only",
        "5": "tooth_5_secret_types_without_showing",
        "6": "tooth_6_stop_ends_one_holder_only",
        "7": "tooth_7_the_cli_is_the_class",
    },
}

FAILURES: list[str] = []
CCFOX = Path.home() / ".cairn" / "devices" / "cc" / "0" / "ccfox"
PAGE = """<!doctype html><html><head><title>fixture {who}</title></head><body>
<h1 id="t">fixture page for {who}</h1>
<input id="q"><button id="go" onclick="document.getElementById('out').textContent='got '+document.getElementById('q').value">go</button>
<div id="out"></div><input id="pw" type="password">
</body></html>"""


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if detail:
        print(f"        {detail[:900]}", flush=True)
    if not ok:
        FAILURES.append(name)


class _Fixture(http.server.BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        who = self.path.strip("/") or "root"
        body = PAGE.format(who=who).encode()
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


def _tree_digest(root: Path) -> str:
    h = hashlib.sha256()
    if root.exists():
        for p in sorted(root.rglob("*")):
            h.update(str(p.relative_to(root)).encode())
            if p.is_file():
                h.update(p.read_bytes())
    return h.hexdigest()


def _refused(port: int) -> bool:
    try:
        with socket.create_connection(("127.0.0.1", port), timeout=2):
            return False
    except OSError:
        return True


class World:
    """The scratch world every tooth reads: one fixture server, two holders, one secret."""

    def __init__(self) -> None:
        from cairn.tools.scratch.scratch import scratch_dir
        self.root = scratch_dir("testing-7a94c34cba52-")
        self.roots = {"repo": REPO, "commons": REPO.parent / "CairnCommons", "instance": self.root}
        self.profiles = Path.home() / "snap" / "firefox" / "common" / f"cairn-testing-7a94c34cba52-{os.getpid()}"
        self.profiles.mkdir(parents=True, exist_ok=True)
        os.environ["CAIRN_WEB_OPERATOR_PROFILE_ROOT"] = str(self.profiles)
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), _Fixture)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        self.url = f"http://127.0.0.1:{self.server.server_address[1]}"
        self.secret = "s3cr3t-" + secrets.token_hex(8)
        env = self.root / "devices" / "alpha" / "0" / ".env"
        env.parent.mkdir(parents=True, exist_ok=True)
        env.write_text(f"OTHER=x\nWEB_OPERATOR_TEST_KEY={self.secret}\n")
        self.ccfox_before = _tree_digest(CCFOX)
        self.alpha = self.beta = None
        self.out = io.StringIO()
        self.err = io.StringIO()

    def holders(self):
        if self.alpha is None:
            from cairn.machines.web_operator import WebOperator
            self.alpha = WebOperator("alpha", 0, roots=self.roots)
            self.beta = WebOperator("beta", 0, roots=self.roots)
            with contextlib.redirect_stdout(self.out), contextlib.redirect_stderr(self.err):
                self.alpha.start()
                self.beta.start()
        return self.alpha, self.beta

    def close(self) -> None:
        for h in (self.alpha, self.beta):
            if h is not None:
                with contextlib.suppress(Exception):
                    h.stop()
        self.server.shutdown()
        shutil.rmtree(self.profiles, ignore_errors=True)


def tooth_1(w: World) -> None:
    name = PROVES["7a94c34cba52"]["1"]
    a, _ = w.holders()
    a.go(w.url + "/alpha")
    got = a.text()
    check(name, "fixture page for alpha" in got and a.headless, f"text()={got!r} headless={a.headless}")


def tooth_2(w: World) -> None:
    name = PROVES["7a94c34cba52"]["2"]
    a, _ = w.holders()
    a.go(w.url + "/alpha")
    a.type("#q", "hello")
    a.click("#go")
    got = a.text("#out")
    check(name, got.strip() == "got hello", f"text('#out')={got!r}")


def tooth_3(w: World) -> None:
    name = PROVES["7a94c34cba52"]["3"]
    a, b = w.holders()
    a.go(w.url + "/alpha")
    b.go(w.url + "/beta")
    wa, wb = a.where(), b.where()
    sa, sb = a.state(), b.state()
    ok = (sa["port"] != sb["port"] and sa["profile"] != sb["profile"] and sa["session"] != sb["session"]
          and wa[0].endswith("/alpha") and wb[0].endswith("/beta")
          and wa[1] == "fixture alpha" and wb[1] == "fixture beta")
    check(name, ok, f"alpha={sa} where={wa}; beta={sb} where={wb}")


def tooth_4(w: World) -> None:
    name = PROVES["7a94c34cba52"]["4"]
    from cairn.tools.base.address import machine_path
    a, b = w.holders()
    lacks = []
    homes = {h: machine_path(h.holder, 0, "web_operator", roots=w.roots) for h in (a, b)}
    for h, home in homes.items():
        st = home / "state.json"
        if not st.is_file():
            lacks.append(f"{h.holder}: no {st}")
            continue
        d = json.loads(st.read_text())
        for k in ("port", "session", "profile"):
            if not d.get(k):
                lacks.append(f"{h.holder}: state.json lacks {k}")
        if d.get("session") != h.state().get("session"):
            lacks.append(f"{h.holder}: state.json session is not the live one")
    stray = [str(p.relative_to(w.root)) for p in w.root.rglob("*") if p.is_file()
             and p.name != ".env" and not any(home in p.parents for home in homes.values())]
    if stray:
        lacks.append(f"files outside the machine homes: {stray}")
    if _tree_digest(CCFOX) != w.ccfox_before:
        lacks.append("~/.cairn/devices/cc/0/ccfox changed")
    check(name, not lacks, "; ".join(lacks) or f"homes={[str(p) for p in homes.values()]}")


def tooth_5(w: World) -> None:
    name = PROVES["7a94c34cba52"]["5"]
    from cairn.tools.base.address import machine_path
    a, _ = w.holders()
    a.go(w.url + "/alpha")
    with contextlib.redirect_stdout(w.out), contextlib.redirect_stderr(w.err):
        a.secret("#pw", "WEB_OPERATOR_TEST_KEY")
    typed = a.js("return document.getElementById('pw').value")
    lacks = []
    if typed != w.secret:
        lacks.append("the field does not hold the .env value")
    if w.secret in w.out.getvalue() or w.secret in w.err.getvalue():
        lacks.append("the value appeared on stdout/stderr")
    for h in ("alpha", "beta"):
        home = machine_path(h, 0, "web_operator", roots=w.roots)
        for p in home.rglob("*"):
            if p.is_file() and w.secret.encode() in p.read_bytes():
                lacks.append(f"the value is in {p.name}")
    check(name, not lacks, "; ".join(lacks) or "typed; value on no stream and no state file")


def tooth_7(w: World) -> None:
    name = PROVES["7a94c34cba52"]["7"]
    a, _ = w.holders()
    a.go(w.url + "/alpha")
    want = a.text()
    r = subprocess.run([sys.executable, "-m", "cairn.machines.web_operator", "--holder", "alpha/0",
                        "--instance-root", str(w.root), "text"],
                       capture_output=True, text=True, timeout=120, cwd=REPO,
                       env={**os.environ, "PYTHONPATH": str(REPO)})
    check(name, r.returncode == 0 and r.stdout.rstrip("\n") == want.rstrip("\n"),
          f"rc={r.returncode} cli={r.stdout!r} class={want!r} err={r.stderr[-300:]!r}")


def tooth_6(w: World) -> None:
    name = PROVES["7a94c34cba52"]["6"]
    a, b = w.holders()
    port, profile = a.state()["port"], a.state()["profile"]
    with contextlib.redirect_stdout(w.out):
        a.stop()
    browsers = subprocess.run(["pgrep", "-f", profile], capture_output=True, text=True).stdout.split()
    b.go(w.url + "/beta")
    wb = b.where()
    ok = _refused(port) and not browsers and wb[0].endswith("/beta")
    check(name, ok, f"alpha port {port} refused={_refused(port)}; alpha browser pids={browsers}; beta where={wb}")


def main() -> int:
    w = None
    teeth = (tooth_1, tooth_2, tooth_3, tooth_4, tooth_5, tooth_7, tooth_6)
    try:
        try:
            w = World()
        except Exception as exc:  # noqa: BLE001
            for t in teeth:
                check(PROVES["7a94c34cba52"][t.__name__.split("_")[1]], False, f"world: {type(exc).__name__}: {exc}")
        else:
            for t in teeth:
                try:
                    t(w)
                except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
                    check(PROVES["7a94c34cba52"][t.__name__.split("_")[1]], False, f"{type(exc).__name__}: {exc}")
    finally:
        if w is not None:
            w.close()
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
