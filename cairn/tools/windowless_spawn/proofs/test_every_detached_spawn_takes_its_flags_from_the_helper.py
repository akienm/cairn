"""Proof for ticket bce45318b2e0 — the two hand-built detached spawns take their flags from windowless_spawn,
and the site check scans instead of listing.

Red first: written before pulse.py and memory_sync.py moved. Nothing is spawned: pulse.py and
memory_sync.py are device code, read as source and never loaded (ticket a0291e45630f). os.name is never patched (patching it breaks pathlib on Windows, the a3 lesson); the kwargs
are compared with the helper's own answer for the host OS. Teeth bind what the build added at call time.

    python <this file>
"""

from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
from pathlib import Path
from unittest import mock

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "bce45318b2e0": {
        "1": "pulse_detached_takes_the_helpers_flags",
        "2": "memory_sync_push_takes_the_helpers_flags",
        "3": "the_site_check_scans_and_reds_a_hand_built_site",
        "4": "memory_sync_without_cairn_skips_loudly_and_returns_zero",
    },
    "615164c15825": {
        "2": "the_site_check_scans_and_reds_a_hand_built_site",
    },
    "a0291e45630f": {
        "1": "memory_sync_push_takes_the_helpers_flags",
        "2": "memory_sync_without_cairn_skips_loudly_and_returns_zero",
        "3": "no_tooth_runs_a_devices_code",
    },
}

FLAG_KEYS = ("creationflags", "start_new_session")


def _flags(kw: dict) -> dict:
    return {k: kw[k] for k in FLAG_KEYS if k in kw}


def _takes_helper(kw: dict) -> bool:
    """Every key the helper returns is in kw with its value, and kw adds no flag key of its own."""
    from cairn.tools.windowless_spawn.windowless_spawn import detached_kwargs
    dk = detached_kwargs()
    return all(kw.get(k) == v for k, v in dk.items()) and _flags(kw) == _flags(dk)


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


PULSE = REPO / "cairn/devices/web_server/groundloop/pulse.py"


def pulse_detached_takes_the_helpers_flags():
    """Read from pulse's source, never imported (RULE 1: this proof measures windowless_spawn, and
    encapsulation_holds reds a tool proof that imports a device). The tool's own scan finds no
    unhelped site in it, and pulse's _detached spreads detached_kwargs() and sets no flag key itself."""
    import ast
    text = PULSE.read_text(encoding="utf-8")
    ws = _load(REPO / "cairn/tools/windowless_spawn/windowless_spawn.py", "ws_pulse_scan")
    with tempfile.TemporaryDirectory() as d:
        copy = Path(d) / "cairn" / "web_server" / "pulse.py"
        copy.parent.mkdir(parents=True)
        copy.write_text(text, encoding="utf-8")
        bad = ws.unhelped_sites(Path(d))
    assert bad == [], f"pulse spawns without the helper: {bad}"
    fn = next((n for n in ast.walk(ast.parse(text))
               if isinstance(n, ast.FunctionDef) and n.name == "_detached"), None)
    assert fn is not None, "pulse has no _detached: the spawn site moved and this tooth reads nothing"
    spread = [k for n in ast.walk(fn) if isinstance(n, ast.Dict) for k, v in zip(n.keys, n.values)
              if k is None and isinstance(v, ast.Call) and getattr(v.func, "id", "") == "detached_kwargs"]
    assert spread, "pulse's _detached does not spread **detached_kwargs()"
    own = [k.value for n in ast.walk(fn) if isinstance(n, ast.Dict) for k in n.keys
           if isinstance(k, ast.Constant) and k.value in FLAG_KEYS]
    own += [k.arg for n in ast.walk(fn) if isinstance(n, ast.Call) for k in n.keywords if k.arg in FLAG_KEYS]
    assert not own, f"pulse's _detached sets its own flag keys {own}"


MEMORY_SYNC = REPO / "cairn/devices/cc/scripts/memory_sync.py"


def _push_fn(text: str):
    import ast
    fn = next((n for n in ast.walk(ast.parse(text))
               if isinstance(n, ast.FunctionDef) and n.name == "push"), None)
    assert fn is not None, "memory_sync has no push(): the spawn site moved and this tooth reads nothing"
    return fn


def _is_popen(n) -> bool:
    import ast
    return isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) == "Popen"


def memory_sync_push_takes_the_helpers_flags():
    """Read from memory_sync's source, never loaded (RULE 1: this proof measures windowless_spawn;
    running a device's script through spec_from_file_location is the same reach as importing it,
    only invisible to encapsulation_holds). The tool's own scan finds no unhelped site in it, and
    push()'s one Popen runs `git ... push -q`, spreads **detached_kwargs() and sets no flag key."""
    import ast
    text = MEMORY_SYNC.read_text(encoding="utf-8")
    ws = _load(REPO / "cairn/tools/windowless_spawn/windowless_spawn.py", "ws_ms_scan")
    with tempfile.TemporaryDirectory() as d:
        copy = Path(d) / "cairn" / "cc" / "memory_sync.py"
        copy.parent.mkdir(parents=True)
        copy.write_text(text, encoding="utf-8")
        bad = ws.unhelped_sites(Path(d))
    assert bad == [], f"memory_sync spawns without the helper: {bad}"
    calls = [n for n in ast.walk(_push_fn(text)) if _is_popen(n)]
    assert len(calls) == 1, f"push() should spawn once, it has {len(calls)} Popen calls"
    call = calls[0]
    cmd = call.args[0] if call.args else None
    words = [e.value for e in getattr(cmd, "elts", []) if isinstance(e, ast.Constant)]
    assert words[:1] == ["git"] and words[-2:] == ["push", "-q"], f"push() spawns {words}, not git ... push -q"
    spread = [k for k in call.keywords if k.arg is None and isinstance(k.value, ast.Call)
              and getattr(k.value.func, "id", "") == "detached_kwargs"]
    assert spread, "push()'s Popen does not spread **detached_kwargs()"
    own = [k.arg for k in call.keywords if k.arg in FLAG_KEYS]
    assert not own, f"push()'s Popen sets its own flag keys {own}"


def the_site_check_scans_and_reds_a_hand_built_site():
    ws = _load(REPO / "cairn/tools/windowless_spawn/windowless_spawn.py", "ws_site_check")
    assert hasattr(ws, "unhelped_sites"), "the tool publishes no scan function (the check still reads a hard list)"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "cairn" / "x").mkdir(parents=True)
        (root / "cairn" / "x" / "proofs").mkdir()
        (root / "cairn/x/clean.py").write_text(
            "from cairn.tools.windowless_spawn.windowless_spawn import detached_kwargs\n"
            "import subprocess\nsubprocess.Popen(['a'], **detached_kwargs())\n", encoding="utf-8")
        # an attached child the caller waits on takes windowless_kwargs, the helper's other answer
        (root / "cairn/x/attached.py").write_text(
            "from cairn.tools.windowless_spawn.windowless_spawn import windowless_kwargs\n"
            "import subprocess\nkw = {}\nfor k, v in windowless_kwargs().items():\n"
            "    kw[k] = kw.get(k, 0) | v\nsubprocess.Popen(['a'], **kw)\n", encoding="utf-8")
        assert ws.unhelped_sites(root) == [], ws.unhelped_sites(root)
        (root / "cairn/x/hand.py").write_text(
            "import subprocess\nsubprocess.Popen(['a'], start_new_session=True)\n", encoding="utf-8")
        (root / "cairn/x/bare.py").write_text("import subprocess\nsubprocess.Popen(['a'])\n", encoding="utf-8")
        (root / "cairn/x/nowin.py").write_text(
            "import subprocess\nsubprocess.Popen(['a'], creationflags=subprocess.CREATE_NO_WINDOW)\n",
            encoding="utf-8")
        (root / "cairn/x/proofs/test_p.py").write_text(
            "import subprocess\nsubprocess.Popen(['a'], start_new_session=True)\n", encoding="utf-8")
        bad = " ".join(ws.unhelped_sites(root))
        assert "hand.py" in bad, f"a hand-built flag set was not seen: {bad!r}"
        assert "bare.py" in bad, f"a Popen with no helper was not seen: {bad!r}"
        assert "nowin.py: hand-builds CREATE_NO_WINDOW" in bad, f"a hand-built CREATE_NO_WINDOW was not seen: {bad!r}"
        assert "clean.py" not in bad and "test_p.py" not in bad, f"a clean file or a proof was flagged: {bad!r}"
    assert ws.windowless_kwargs("nt") == {"creationflags": ws.CREATE_NO_WINDOW}, \
        f"an attached Windows child must take CREATE_NO_WINDOW alone: {ws.windowless_kwargs('nt')}"
    assert ws.windowless_kwargs("posix") == {}, ws.windowless_kwargs("posix")
    # No live-repo scan here (RULE 1: this proof measures windowless_spawn). Every live site is the
    # build_inspector sieve's question; each component's own proof asks it of its own subtree.


def memory_sync_without_cairn_skips_loudly_and_returns_zero():
    """Read from memory_sync's source. In push() the helper's import sits in a try whose
    ImportError handler prints 'CC MEMORY SYNC' to stderr and returns 0, and the Popen is not
    reached from inside that try or its handler: no helper, no spawn, and the Stop hook never fails."""
    import ast
    fn = _push_fn(MEMORY_SYNC.read_text(encoding="utf-8"))
    guards = [t for t in ast.walk(fn) if isinstance(t, ast.Try)
              and any(isinstance(n, ast.ImportFrom) and n.module == "cairn.tools.windowless_spawn.windowless_spawn"
                      and any(a.name == "detached_kwargs" for a in n.names) for b in t.body for n in ast.walk(b))]
    assert guards, "push() does not import detached_kwargs inside a try: a missing cairn raises into the Stop hook"
    t = guards[0]
    handlers = [h for h in t.handlers if getattr(h.type, "id", "") == "ImportError"]
    assert handlers, "the helper's import is not guarded by an ImportError handler"
    h = handlers[0]
    loud = [n for b in h.body for n in ast.walk(b) if isinstance(n, ast.Call) and getattr(n.func, "id", "") == "print"
            and any(k.arg == "file" and getattr(k.value, "attr", "") == "stderr" for k in n.keywords)
            and "CC MEMORY SYNC" in ast.unparse(n)]
    assert loud, "the skip is silent: no print('CC MEMORY SYNC ...', file=sys.stderr) in the handler"
    rets = [n for n in h.body if isinstance(n, ast.Return)]
    assert rets and isinstance(rets[-1].value, ast.Constant) and rets[-1].value.value == 0, \
        "the handler does not return 0: the Stop hook would fail"
    inside = [n for part in (t.body, h.body) for b in part for n in ast.walk(b) if _is_popen(n)]
    assert not inside, "a Popen runs inside the guarded import or its handler: a detached push without the helper"


# ── ticket a0291e45630f ────────────────────────────────────────────────────────────

def no_tooth_runs_a_devices_code():
    """RULE 1: this proof measures windowless_spawn, so nothing in it imports cairn.devices or
    hands a path under cairn/devices to spec_from_file_location / _load (read by AST)."""
    import ast
    tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
    hits = []
    for n in ast.walk(tree):
        mods = ([a.name for a in n.names] if isinstance(n, ast.Import)
                else [n.module or ""] if isinstance(n, ast.ImportFrom) else [])
        hits += [f":{n.lineno} import {m}" for m in mods if m == "cairn.devices" or m.startswith("cairn.devices.")]
        if isinstance(n, ast.Call) and getattr(n.func, "attr", getattr(n.func, "id", "")) in (
                "_load", "spec_from_file_location", "run_path", "import_module"):
            src = ast.unparse(n)
            names = {x.id for x in ast.walk(n) if isinstance(x, ast.Name)}
            if "cairn/devices" in src or names & {"PULSE", "MEMORY_SYNC"}:
                hits.append(f":{n.lineno} {src}")
    assert not hits, "a tooth runs a device's code:\n" + "\n".join(hits)


TEETH = [pulse_detached_takes_the_helpers_flags, memory_sync_push_takes_the_helpers_flags,
         the_site_check_scans_and_reds_a_hand_built_site, memory_sync_without_cairn_skips_loudly_and_returns_zero,
         no_tooth_runs_a_devices_code]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  green  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  RED    {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
