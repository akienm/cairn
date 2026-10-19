#!/usr/bin/env python3
"""Proof that a trouble is read and cleared as a file, and never asked over the bus.

Akien 2026-10-18: "TROUBLE TICKETS ARE A FILE ARTIFACT IN THE LOGGING TREE" / "THERE SHOULD BE
NO ROWS FOR TROUBLE TICKETS." Measured the same day: the cairn pane (device.py) and the
web_server socket (listener.py) asked verb `live`, counting_block asked verb `clears`, and
the CLI asked `live` and `clear` — 195 live replies (~325 KB) and 372 clears replies standing
as bus rows. The store is files under ~/.cairn/logs/cairn/0/troubletickets/, so every reader
reads them through the tool trouble publishes (tools/store/), and the CLI, which is trouble's
own code, clears by emitting and folding in its own process.

Teeth (PROVES below), each binding the new names at call time so the hollow revert reds tooth
by tooth instead of crashing the reader:
  the_lane_declares_no_trouble_verbs   — TroubleDevice's declared_verbs carry no live, clear
                                         or clears
  the_tool_reads_the_live_rows          — store.live(roots): the summary rows of the top of the
                                         store, an unreadable file surfaced, cleared/ left out,
                                         an absent store a raise and never []
  the_tool_reads_the_clears             — store.clears(prefix, roots): one row per clear, top
                                         and cleared/, an unknown hand classed from its cgroup
  the_tool_reaches_no_host              — importing the tool and calling both reads loads no
                                         bus client and no device code but its own package
  nothing_asks_trouble_over_the_bus     — no request addressed to trouble anywhere outside proofs
  the_cli_clears_with_no_bus            — `trouble live` and `trouble clear` over a scratch HOME
                                         with every bus dial and socket connect refused
  the_three_readers_read_with_no_bus    — the cairn pane, the web_server rows and counting_block's
                                         clears read a scratch store with the bus refused
  the_store_tool_is_published           — the tool's charter publishes its one module, the old
                                         door is gone, and no encapsulation breach names either

    bin/cairn test cairn/devices/trouble/proofs/test_trouble_never_rides_the_bus.py
"""

from __future__ import annotations

import ast
import importlib
import json
import os
import re
import socket
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_COMP = _REPO / "cairn" / "devices" / "trouble"
_TOOL = "cairn.devices.trouble.tools.store.store"
_OLD = "cairn.devices.trouble.store"
_CLI = _COMP / "0" / "bin" / "trouble"
_SUMMARY = {"id", "standing", "why", "count", "first_seen", "last_seen"}
_CLEAR_ROW = {"id", "standing", "by", "hand_class", "at"}
APP = "/user.slice/user-1000.slice/user@1000.service/app.slice"
TAB = f"{APP}/app-org.kde.konsole-78471.scope/tab(3360690).scope"

PROVES = {"ee04bb869795": {"all": "test_trouble_never_rides_the_bus"}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    # The detail rides its own line: the tester reads the whole PASS/FAIL line as the tooth name.
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:400]}")
    if not ok:
        FAILURES.append(name)


def _trouble(ident: str, *, notified=("cc",), cleared_by=(), standing="OPEN") -> dict:
    return {"id": ident, "standing": standing, "why": f"a proof's trouble ({ident})", "count": 2,
            "first_seen": "2026-10-18T00:00:00+00:00", "last_seen": "2026-10-18T00:01:00+00:00",
            "occurrences": [{"at": "2026-10-18T00:00:00+00:00"}], "notified": list(notified),
            "cleared_by": list(cleared_by), "recurred_after_clear": None, "prior_attempts": 0}


def _world(base: Path) -> tuple[dict, Path]:
    """Scratch roots whose instance root is ``base``, and the store under it."""
    roots = {"repo": _REPO, "commons": _REPO.parent / "CairnCommons", "instance": base}
    from cairn.tools.base.address import log_path
    return roots, log_path("cairn", 0, roots) / "troubletickets"


def _put(folder: Path, ticket: dict) -> None:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{ticket['id']}.json").write_text(json.dumps(ticket, indent=2) + "\n",
                                                 encoding="utf-8")


def _seed(store: Path) -> None:
    _put(store, _trouble("proof-live-a"))
    _put(store, _trouble("who-writes-what-proof-top", cleared_by=[
        {"by": "akien", "at": "2026-10-18T01:00:00+00:00",
         "hand": {"class": "unknown", "cgroup": TAB}}]))
    (store / "proof-unreadable.json").write_text("{not json", encoding="utf-8")
    _put(store / "cleared", _trouble("who-writes-what-proof-cleared", standing="CLEARED", cleared_by=[
        {"by": "cc", "at": "2026-10-18T02:00:00+00:00", "hand": {"class": "cc"}}]))
    _put(store / "cleared", _trouble("other-proof-cleared", standing="CLEARED", cleared_by=[
        {"by": "cc", "at": "2026-10-18T03:00:00+00:00", "hand": {"class": "cc"}}]))


class _Refused(Exception):
    pass


class _NoBus:
    """A bus whose every request is refused, so a reader that still asks reds."""

    def request(self, *a, **kw):
        raise _Refused(f"a trouble reader asked the bus: {kw.get('to')}/{kw.get('verb')}")


def _refuse_dials():
    """Refuse reach() and every socket connect; return the undo."""
    import cairn.tools.bus_client as bc
    saved = (bc.reach, socket.socket.connect)

    def no_reach(*a, **kw):
        raise _Refused(f"reach{a}")

    def no_connect(self, *a, **kw):
        raise _Refused(f"socket connect {a}")

    bc.reach = no_reach
    socket.socket.connect = no_connect

    def undo():
        bc.reach, socket.socket.connect = saved
    return undo


def test_the_lane_declares_no_trouble_verbs() -> None:
    from cairn.devices.trouble.trouble import TroubleDevice
    with tempfile.TemporaryDirectory(prefix="ee04-verbs-") as d:
        verbs = set(TroubleDevice(root=d).declared_verbs())
    held = sorted(verbs & {"live", "clear", "clears"})
    check("the_lane_declares_no_trouble_verbs", not held, f"still declared: {held}")


def test_the_tool_reads_the_live_rows() -> None:
    tool = importlib.import_module(_TOOL)
    with tempfile.TemporaryDirectory(prefix="ee04-live-") as d:
        roots, store = _world(Path(d))
        _seed(store)
        rows = tool.live(roots)
        by_id = {r.get("id"): r for r in rows}
        good = [by_id.get(i) for i in ("proof-live-a", "who-writes-what-proof-top")]
        bad = by_id.get("proof-unreadable") or {}
        shape = all(r is not None and set(r) == _SUMMARY for r in good)
        marked = bad.get("unreadable") is True and str(bad.get("why", "")).startswith("UNREADABLE")
        exact = sorted(by_id) == ["proof-live-a", "proof-unreadable", "who-writes-what-proof-top"]
        roots2, _ = _world(Path(d) / "nothing-here")
        try:
            absent = tool.live(roots2)
            absent_raises = False
        except Exception as exc:  # noqa: BLE001 — the raise is the claim
            absent, absent_raises = f"{type(exc).__name__}", True
    check("the_tool_reads_the_live_rows", shape and marked and exact and absent_raises,
          f"ids={sorted(by_id)} rows={rows} absent={absent!r}")


def test_the_tool_reads_the_clears() -> None:
    tool = importlib.import_module(_TOOL)
    from cairn.tools.artifact import artifact as door
    from cairn.tools.system_word import fold
    with tempfile.TemporaryDirectory(prefix="ee04-clears-") as d:
        roots, store = _world(Path(d))
        _seed(store)
        rows = tool.clears("who-writes-what-", roots)
        every = tool.clears("", roots)
    by_id = {r.get("id"): r for r in rows}
    want_tab = fold(door.classify(TAB)["class"])
    ok = (sorted(by_id) == ["who-writes-what-proof-cleared", "who-writes-what-proof-top"]
          and all(set(r) == _CLEAR_ROW for r in rows)
          and want_tab != "unknown"
          and by_id["who-writes-what-proof-top"]["hand_class"] == want_tab
          and by_id["who-writes-what-proof-cleared"]["hand_class"] == "cc"
          and by_id["who-writes-what-proof-cleared"]["standing"] == "CLEARED"
          and len(every) == 3)
    check("the_tool_reads_the_clears", ok, f"rows={rows} every={len(every)} tab={want_tab}")


def test_the_tool_reaches_no_host() -> None:
    with tempfile.TemporaryDirectory(prefix="ee04-light-") as d:
        roots, store = _world(Path(d))
        _seed(store)
        code = (
            "import json, sys\n"
            f"sys.path.insert(0, {str(_REPO)!r})\n"
            f"import {_TOOL} as tool\n"
            f"roots = {{k: __import__('pathlib').Path(v) for k, v in {json.dumps({k: str(v) for k, v in roots.items()})}.items()}}\n"
            "tool.live(roots); tool.clears('', roots)\n"
            "bad = sorted(m for m in sys.modules if 'bus_client' in m or (m.startswith('cairn.devices.')"
            " and m not in ('cairn.devices.trouble', 'cairn.devices.trouble.tools')"
            " and not m.startswith('cairn.devices.trouble.tools.store')))\n"
            "print(json.dumps(bad))\n")
        out = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, timeout=60)
    try:
        bad = json.loads(out.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        bad = None
    check("the_tool_reaches_no_host", out.returncode == 0 and bad == [],
          f"rc={out.returncode} loaded={bad} err={out.stderr[-300:]}")


def _consts(tree: ast.Module) -> dict:
    out = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant) \
                and isinstance(node.value.value, str):
            for tgt in node.targets:
                if isinstance(tgt, ast.Name):
                    out[tgt.id] = node.value.value
    return out


_TO_TROUBLE = re.compile(r"""\bto\s*=\s*['"]trouble['"]""")


def _asks_in(path: Path, rel: str) -> list[str]:
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return []
    if path.suffix != ".py":
        # A shell file carries its Python as text; the destination is a literal there.
        return [f"{rel}:{text.count(chr(10), 0, m.start()) + 1}" for m in _TO_TROUBLE.finditer(text)]
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return []
    consts = _consts(tree)
    hits = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        kw = {k.arg: k.value for k in node.keywords if k.arg}
        if "to" not in kw or "verb" not in kw:
            continue
        to = kw["to"]
        dest = to.value if isinstance(to, ast.Constant) else consts.get(getattr(to, "id", None))
        if dest == "trouble":
            hits.append(f"{rel}:{node.lineno}")
    return hits


def test_nothing_asks_trouble_over_the_bus() -> None:
    hits = []
    for top in ("cairn", "bin", "skills"):
        for p in sorted((_REPO / top).rglob("*")):
            parts = set(p.relative_to(_REPO).parts)
            if not p.is_file() or parts & {"proofs", "validations", "__pycache__"}:
                continue
            if p.suffix not in (".py", "") and p.suffix != ".sh":
                continue
            hits += _asks_in(p, str(p.relative_to(_REPO)))
    check("nothing_asks_trouble_over_the_bus", not hits, f"asks: {hits}")


_SITE = '''
import os, socket
def _log(what):
    with open(os.environ["EE04_DIALS"], "a", encoding="utf-8") as f:
        f.write(what + "\\n")
def _no_connect(self, *a, **kw):
    _log(f"connect {a}")
    raise ConnectionRefusedError("ee04 proof: no socket may be dialled")
socket.socket.connect = _no_connect
import cairn.tools.bus_client as _bc
def _no_reach(*a, **kw):
    _log(f"reach {a}")
    raise ConnectionRefusedError("ee04 proof: no bus may be reached")
_bc.reach = _no_reach
'''


def test_the_cli_clears_with_no_bus() -> None:
    with tempfile.TemporaryDirectory(prefix="ee04-cli-") as d:
        home = Path(d) / "home"
        site = Path(d) / "site"
        site.mkdir()
        (site / "sitecustomize.py").write_text(_SITE, encoding="utf-8")
        dials = Path(d) / "dials.log"
        dials.write_text("", encoding="utf-8")
        roots, store = _world(home / ".cairn")
        _put(store, _trouble("ee04-cli-proof"))
        env = {"HOME": str(home), "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
               "PYTHONPATH": f"{site}:{_REPO}", "EE04_DIALS": str(dials)}

        def run(*args):
            return subprocess.run(["bash", str(_CLI), *args], capture_output=True, text=True,
                                  env=env, timeout=120)
        live = run("live", "--json")
        try:
            live_ids = [t.get("id") for t in json.loads(live.stdout)]
        except ValueError:
            live_ids = None
        done = run("clear", "ee04-cli-proof", "--by", "cc", "--what-changed", "the proof cleared it")
        moved = store / "cleared" / "ee04-cli-proof.json"
        cleared = moved.is_file() and not (store / "ee04-cli-proof.json").exists()
        try:
            by = [c.get("by") for c in json.loads(moved.read_text())["cleared_by"]]
        except (OSError, ValueError, KeyError):
            by = None
        nope = run("clear", "no-such-trouble", "--by", "cc", "--what-changed", "nothing")
        dialled = dials.read_text(encoding="utf-8").strip()
    ok = (live.returncode == 0 and live_ids == ["ee04-cli-proof"]
          and done.returncode == 0 and cleared and by == ["cc"]
          and nope.returncode == 1 and "declined" in (nope.stdout + nope.stderr)
          and not dialled)
    check("the_cli_clears_with_no_bus", ok,
          f"live rc={live.returncode} ids={live_ids} err={live.stderr[-200:]!r} | clear rc={done.returncode} "
          f"cleared={cleared} by={by} out={(done.stdout + done.stderr)[-200:]!r} | not-live rc={nope.returncode} "
          f"out={(nope.stdout + nope.stderr)[-160:]!r} | dials={dialled[:200]!r}")


def test_the_three_readers_read_with_no_bus() -> None:
    from cairn.devices.cairn.device import CairnDevice
    from cairn.devices.web_server import listener
    from cairn.machines.counting_block import block
    got, errs = {}, []
    undo = _refuse_dials()
    try:
        with tempfile.TemporaryDirectory(prefix="ee04-readers-") as d:
            roots, store = _world(Path(d))
            _seed(store)
            for name, call in (
                    ("pane", lambda: CairnDevice(bus=_NoBus(), roots=roots)._trouble_pane_data()),
                    ("web", lambda: listener._trouble_rows(roots)),
                    ("counting", lambda: block._ask_clears(roots))):
                try:
                    got[name] = call()
                except Exception as exc:  # noqa: BLE001 — a reader that cannot read is the red
                    errs.append(f"{name}: {type(exc).__name__}: {exc}")
            roots2, _ = _world(Path(d) / "absent")
            try:
                CairnDevice(bus=_NoBus(), roots=roots2)._trouble_pane_data()
                errs.append("pane over an absent store answered instead of raising")
            except _Refused as exc:
                errs.append(f"pane over an absent store asked the bus: {exc}")
            except Exception:  # noqa: BLE001 — Law 7: absent is a raise, never zero troubles
                pass
    finally:
        undo()
    want = ["proof-live-a", "proof-unreadable", "who-writes-what-proof-top"]
    pane_ok = sorted(r.get("id") for r in got.get("pane") or []) == want
    web_ok = sorted(r.get("id") for r in got.get("web") or []) == want \
        and all(set(r) == {"id", "standing", "why", "count"} for r in got.get("web") or [])
    clears = ((got.get("counting") or {}).get("body") or {}).get("clears") or []
    count_ok = sorted(r.get("id") for r in clears) == ["who-writes-what-proof-cleared",
                                                        "who-writes-what-proof-top"]
    check("the_three_readers_read_with_no_bus", pane_ok and web_ok and count_ok and not errs,
          f"pane={pane_ok} web={web_ok} counting={count_ok} errs={errs}")


def test_the_store_tool_is_published() -> None:
    tool_dir = _COMP / "tools" / "store"
    charter = json.loads((tool_dir / "intention+why.json").read_text(encoding="utf-8"))
    device = json.loads((_COMP / "intention+why.json").read_text(encoding="utf-8"))
    from cairn.machines.build_inspector.inspector import encapsulation_breaches
    rows = [r for r in encapsulation_breaches(str(_REPO))
            if str(r.get("module") or "").startswith((_OLD, _TOOL))]
    ok = (charter.get("published_by_device") is True
          and charter.get("public_interface") == [_TOOL]
          and _OLD not in (device.get("public_interface") or [])
          and not (_COMP / "store.py").exists()
          and not rows)
    check("the_store_tool_is_published", ok,
          f"published={charter.get('published_by_device')} pi={charter.get('public_interface')} "
          f"device_pi={device.get('public_interface')} old_file={(_COMP / 'store.py').exists()} "
          f"breaches={rows[:5]}")


TEETH = (test_the_lane_declares_no_trouble_verbs, test_the_tool_reads_the_live_rows,
         test_the_tool_reads_the_clears, test_the_tool_reaches_no_host,
         test_nothing_asks_trouble_over_the_bus, test_the_cli_clears_with_no_bus,
         test_the_three_readers_read_with_no_bus, test_the_store_tool_is_published)


def main() -> int:
    for tooth in TEETH:
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__.removeprefix("test_"), False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
