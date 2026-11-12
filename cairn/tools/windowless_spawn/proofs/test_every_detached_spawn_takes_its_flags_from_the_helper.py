"""Proof for ticket bce45318b2e0 — the two hand-built detached spawns take their flags from windowless_spawn,
and the site check scans instead of listing.

Red first: written before pulse.py and memory_sync.py moved. Popen is mocked in every tooth, so nothing
is spawned. os.name is never patched (patching it breaks pathlib on Windows, the a3 lesson); the kwargs
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


def pulse_detached_takes_the_helpers_flags():
    from cairn.devices.web_server.groundloop import pulse
    from cairn.tools.windowless_spawn.windowless_spawn import detached_kwargs
    seen = {}

    def popen(cmd, **kw):
        seen["cmd"], seen["kw"] = cmd, kw
        return mock.Mock(pid=1)

    with tempfile.TemporaryDirectory() as d, mock.patch.object(pulse.subprocess, "Popen", popen):
        pulse._detached(["python", "listener.py", "--port", "1"], Path(d) / "pulse.log")
    assert _takes_helper(seen["kw"]), (
        f"pulse spawns with {_flags(seen['kw'])}, the helper says {detached_kwargs()}")


def memory_sync_push_takes_the_helpers_flags():
    from cairn.tools.windowless_spawn.windowless_spawn import detached_kwargs
    ms = _load(REPO / "cairn/devices/cc/scripts/memory_sync.py", "memory_sync_under_proof")
    seen = {}

    def popen(cmd, **kw):
        seen["cmd"], seen["kw"] = cmd, kw
        return mock.Mock()

    with tempfile.TemporaryDirectory() as d:
        ms.CLONE = Path(d)
        with mock.patch.object(ms, "git", lambda *a, **k: mock.Mock(stdout="M x\n", returncode=0)), \
                mock.patch.object(ms.subprocess, "Popen", popen):
            rc = ms.push()
    assert rc == 0, rc
    assert seen["cmd"][:1] == ["git"] and seen["cmd"][-2:] == ["push", "-q"], seen.get("cmd")
    assert _takes_helper(seen["kw"]), (
        f"memory_sync spawns with {_flags(seen['kw'])}, the helper says {detached_kwargs()}")


def the_site_check_scans_and_reds_a_hand_built_site():
    ws = _load(REPO / "cairn/tools/windowless_spawn/proofs/test_a_cairn_spawn_opens_no_console_window.py",
               "ws_site_check")
    assert hasattr(ws, "unhelped_sites"), "the site check has no scan function (it still reads a hard list)"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d)
        (root / "cairn" / "x").mkdir(parents=True)
        (root / "cairn" / "x" / "proofs").mkdir()
        (root / "cairn/x/clean.py").write_text(
            "from cairn.tools.windowless_spawn.windowless_spawn import detached_kwargs\n"
            "import subprocess\nsubprocess.Popen(['a'], **detached_kwargs())\n", encoding="utf-8")
        assert ws.unhelped_sites(root) == [], ws.unhelped_sites(root)
        (root / "cairn/x/hand.py").write_text(
            "import subprocess\nsubprocess.Popen(['a'], start_new_session=True)\n", encoding="utf-8")
        (root / "cairn/x/bare.py").write_text("import subprocess\nsubprocess.Popen(['a'])\n", encoding="utf-8")
        (root / "cairn/x/proofs/test_p.py").write_text(
            "import subprocess\nsubprocess.Popen(['a'], start_new_session=True)\n", encoding="utf-8")
        bad = " ".join(ws.unhelped_sites(root))
        assert "hand.py" in bad, f"a hand-built flag set was not seen: {bad!r}"
        assert "bare.py" in bad, f"a Popen with no helper was not seen: {bad!r}"
        assert "clean.py" not in bad and "test_p.py" not in bad, f"a clean file or a proof was flagged: {bad!r}"
    live = ws.unhelped_sites(REPO)
    assert live == [], "\n".join(live)


def memory_sync_without_cairn_skips_loudly_and_returns_zero():
    ms = _load(REPO / "cairn/devices/cc/scripts/memory_sync.py", "memory_sync_no_cairn")
    spawned = []
    err = io.StringIO()
    with tempfile.TemporaryDirectory() as d:
        ms.CLONE = Path(d)
        blocked = {"cairn.tools.windowless_spawn": None, "cairn.tools.windowless_spawn.windowless_spawn": None}
        with mock.patch.object(ms, "git", lambda *a, **k: mock.Mock(stdout="M x\n", returncode=0)), \
                mock.patch.object(ms.subprocess, "Popen", lambda *a, **k: spawned.append(a)), \
                mock.patch.dict(sys.modules, blocked), contextlib.redirect_stderr(err):
            rc = ms.push()
    assert rc == 0, f"the Stop hook would fail: push returned {rc}"
    assert not spawned, f"a detached push was spawned without the helper: {spawned}"
    assert "CC MEMORY SYNC" in err.getvalue(), f"the skip was silent: {err.getvalue()!r}"


TEETH = [pulse_detached_takes_the_helpers_flags, memory_sync_push_takes_the_helpers_flags,
         the_site_check_scans_and_reds_a_hand_built_site, memory_sync_without_cairn_skips_loudly_and_returns_zero]


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
