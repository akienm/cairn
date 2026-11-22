"""Proof: a slate names the Claude that wrote it (ticket b2e4dafc5813).

Four Claudes share one commons, and every slate said author "CC": akienasus_cc_0 opened
on 2026-11-12 on akiendelllinux's slate as if it were its own. The door now stamps the
writing session's name and box, both minted by the door. Every fire runs with a scratch
slates dir, berths, traces and sessions dir, so the live store and the live repos are
never touched (the slates_dir seam keeps the door's auto-commit off).

    python3 skills/saveslate/proofs/test_a_slate_names_the_claude_that_wrote_it.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))
sys.path.insert(0, str(_REPO / "skills" / "saveslate"))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.devices.system_rackmount.tools.host.host import host_name  # noqa: E402

PROVES = {"b2e4dafc5813": {
    "1": "test_a_named_session_stamps_its_name_and_box",
    "2": "test_a_session_with_no_record_reads_cc_and_still_the_box",
    "3": "test_a_packet_carrying_author_or_host_is_refused",
},
    "4366edb56144": {"1": "test_this_proof_asks_the_os_no_hostname",
                     "2": "test_this_proof_loads_with_os_uname_gone"}}

HOST = host_name()  # the system device answers which box (ticket 4366edb56144)
HEADS = {"cairn": "aaa111", "CairnCommons": "bbb222"}


def _good(slate_id: str) -> dict:
    return {"slate_id": slate_id, "at_sea": "fixture voyage", "next_direction": "fixture next",
            "open_threads": ["one thread"],
            "instruments_read": {"git_heads": dict(HEADS)},
            "bullets": [{"text": "fixture close", "stratum": "code"}],
            "exit": "routed_forward"}


def _roots() -> dict:
    tmp = scratch_dir("slate-author-")
    (tmp / "slates").mkdir()
    sessions = tmp / "sessions"
    sessions.mkdir()
    (sessions / "4242.json").write_text(json.dumps(
        {"pid": 4242, "sessionId": "sid-asus", "name": "akienasus_cc_0", "updatedAt": 1}))
    return dict(heads=HEADS, slates_dir=tmp / "slates", berths=tmp / "berths",
                trace_root=tmp / "traces", sessions_dir=sessions)


def test_a_named_session_stamps_its_name_and_box() -> None:
    import door
    r = door.fire(_good("2026-11-12-fixture-named"), session="sid-asus", **_roots())
    rec = json.loads(Path(r["slate"]).read_text())
    assert rec["author"] == "akienasus_cc_0" and rec["host"] == HOST, rec
    assert rec["session"] == "sid-asus", rec


def test_a_session_with_no_record_reads_cc_and_still_the_box() -> None:
    import door
    r = door.fire(_good("2026-11-12-fixture-unnamed"), session="sid-nobody", **_roots())
    rec = json.loads(Path(r["slate"]).read_text())
    assert rec["author"] == "CC" and rec["host"] == HOST, rec


def test_a_packet_carrying_author_or_host_is_refused() -> None:
    import door
    from cairn.machines.learning_block.learning_block import DoorRefused
    for key, value in (("author", "akiendelllinux_cc_0"), ("host", "elsewhere")):
        roots = _roots()
        sid = f"2026-11-12-fixture-{key}"
        try:
            door.fire(dict(_good(sid), **{key: value}), session="sid-asus", **roots)
        except DoorRefused as exc:
            fields = [l["field"] for l in (getattr(exc, "lacks", None) or [])]
            assert any(key in f for f in fields), (key, fields)
        else:
            raise AssertionError(f"a packet carrying {key} was not refused")
        assert not (roots["slates_dir"] / f"{sid}.json").exists(), f"{key}: a slate landed"


_OS_HOSTNAME_CALLS = {("os", "uname"), ("platform", "node"), ("platform", "uname"),
                      ("socket", "gethostname")}


def test_this_proof_asks_the_os_no_hostname() -> None:
    """Ticket 4366edb56144 clause 1: no call here asks the OS which box; HOST is the host tool's."""
    import ast
    tree = ast.parse(Path(__file__).read_text())
    bare = {a.asname or a.name for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)
            and n.module in {m for m, _ in _OS_HOSTNAME_CALLS} for a in n.names
            if (n.module, a.name) in _OS_HOSTNAME_CALLS}
    found = []
    for n in ast.walk(tree):
        if not isinstance(n, ast.Call):
            continue
        f = n.func
        if (isinstance(f, ast.Attribute) and isinstance(f.value, ast.Name)
                and (f.value.id, f.attr) in _OS_HOSTNAME_CALLS):
            found.append((n.lineno, f.value.id + "." + f.attr))
        elif isinstance(f, ast.Name) and f.id in bare:
            found.append((n.lineno, f.id))
    assert not found, found
    from cairn.devices.system_rackmount.tools.host import host
    assert HOST == host.host_name(), (HOST, host.host_name())


def test_this_proof_loads_with_os_uname_gone() -> None:
    """Ticket 4366edb56144 clause 2: with os.uname deleted (as on Windows) a second copy of this file
    loads, and its HOST is the host tool's answer."""
    import importlib.util
    from cairn.devices.system_rackmount.tools.host import host
    had = hasattr(os, "uname")
    saved = getattr(os, "uname", None)
    import platform
    platform._uname_cache = None   # platform caches uname(): ask it fresh, with os.uname gone
    if had:
        del os.uname
    try:
        spec = importlib.util.spec_from_file_location("_host_proof_copy_4366edb56144", __file__)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        assert mod.HOST == host.host_name(), (mod.HOST, host.host_name())
    finally:
        if had:
            os.uname = saved
        platform._uname_cache = None   # never leave the uname-less answer cached for later proofs


def _main() -> int:
    failed = []
    for name in [n for keys in PROVES.values() for n in keys.values()]:
        try:
            globals()[name]()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — every tooth reports, none aborts the run
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
            failed.append(name)
    print(f"\n{'RED — ' + str(len(failed)) + ' failed' if failed else 'GREEN — all ' + str(sum(len(k) for k in PROVES.values())) + ' teeth pass'}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(_main())
