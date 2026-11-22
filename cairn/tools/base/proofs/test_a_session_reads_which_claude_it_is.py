"""Proof: a session reads which Claude it is (ticket a1d3c9e4b702).

Four Claudes share one commons, and a record that says only "CC" cannot tell them apart.
claude_identity.who() reads Claude Code's own session record and names the session. Every
tooth runs over a scratch sessions dir; the live ~/.claude/sessions is never read. The
subject is imported inside each tooth, so a hollow build reds per tooth.

    python3 cairn/tools/base/proofs/test_a_session_reads_which_claude_it_is.py
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.devices.system_rackmount.tools.host.host import host_name  # noqa: E402

PROVES = {"a1d3c9e4b702": {
    "1": "test_a_session_id_names_its_session",
    "2": "test_no_id_falls_to_the_record_of_claude_pid",
    "3": "test_nothing_found_is_a_nameless_session_never_a_raise",
    "4": "test_two_records_of_one_session_read_the_newer",
},
    "ee2c8a73518b": {"1": "test_this_proof_asks_the_os_no_hostname",
                     "2": "test_this_proof_loads_with_os_uname_gone"}}

HOST = host_name()  # the system device answers which box (ticket ee2c8a73518b)


def _dir(*records, torn: bool = False) -> Path:
    d = scratch_dir("claude-identity-")
    for r in records:
        (d / f"{r['pid']}.json").write_text(json.dumps(r))
    if torn:
        (d / "999.json").write_text('{"pid": 999, "name": "half')
    return d


def _rec(pid, sid, name, former=(), updated=1):
    return {"pid": pid, "sessionId": sid, "name": name, "updatedAt": updated,
            "formerNames": [{"name": f, "until": 1} for f in former]}


def test_a_session_id_names_its_session() -> None:
    from cairn.tools.base.claude_identity import who
    d = _dir(_rec(100, "sid-orch", "orchestrator", former=["akiendelllinux_cc_RESCUE"]),
             _rec(200, "sid-asus", "akienasus_cc_0"))
    w = who("sid-orch", sessions_dir=d, environ={})
    assert w == {"name": "orchestrator", "former_names": ["akiendelllinux_cc_RESCUE"],
                 "host": HOST, "session": "sid-orch"}, w


def test_no_id_falls_to_the_record_of_claude_pid() -> None:
    from cairn.tools.base.claude_identity import who
    d = _dir(_rec(100, "sid-orch", "orchestrator"), _rec(200, "sid-asus", "akienasus_cc_0"))
    w = who(None, sessions_dir=d, environ={"CLAUDE_PID": "200"})
    assert w["name"] == "akienasus_cc_0" and w["session"] == "sid-asus", w


def test_nothing_found_is_a_nameless_session_never_a_raise() -> None:
    from cairn.tools.base.claude_identity import who
    d = _dir(_rec(100, "sid-orch", "orchestrator"), torn=True)
    w = who("sid-unknown", sessions_dir=d, environ={})
    assert w == {"name": "", "former_names": [], "host": HOST, "session": "sid-unknown"}, w
    gone = who("sid-orch", sessions_dir=d / "absent", environ={})
    assert gone["name"] == "" and gone["host"] == HOST, gone


def test_two_records_of_one_session_read_the_newer() -> None:
    from cairn.tools.base.claude_identity import who
    d = _dir(_rec(100, "sid-x", "old-name", updated=5), _rec(101, "sid-x", "new-name", updated=9))
    assert who("sid-x", sessions_dir=d, environ={})["name"] == "new-name"


_OS_HOSTNAME_CALLS = {("os", "uname"), ("platform", "node"), ("platform", "uname"),
                      ("socket", "gethostname")}


def test_this_proof_asks_the_os_no_hostname() -> None:
    """Ticket ee2c8a73518b clause 1: no call here asks the OS which box; HOST is the host tool's."""
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
    """Ticket ee2c8a73518b clause 2: with os.uname deleted (as on Windows) a second copy of this file
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
        spec = importlib.util.spec_from_file_location("_host_proof_copy_ee2c8a73518b", __file__)
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
