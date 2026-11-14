"""Proof for ticket 3deafc9e36de "a client from another checkout refuses a stale live bus instead
of shutting it down".

MEASURED 2026-11-12 (memory: another root evicts the host bus): a run from an old sha or a git
worktree, on the live HOME, found the house bus answering ``stale`` (it serves the house root, not
the caller's), and ``_replace`` shut it down and started one from the worktree. Every other client
on the box was then served by a throwaway checkout's code. The fix: at the live home, a client
whose class root is not the house's own refuses, LOUDLY (Law 7), naming both roots and the way
out (``CAIRN_BUS_HOME=<scratch home>``), and sends no shutdown.

  1. test_a_foreign_root_at_the_live_home_sends_no_shutdown: through RemoteBus._call, a stale
     live bus meets a foreign root: BusStale names both roots and CAIRN_BUS_HOME, no shutdown;
  2. test_the_house_root_still_replaces_the_live_bus: the house root's client still shuts it down;
  3. test_a_foreign_root_at_a_scratch_home_still_replaces: a scratch home is the caller's own;
  4. test_no_resolvable_house_root_refuses_at_the_live_home: no env and no venv record: BusStale
     naming the venv and the env override, no shutdown (FIXME 1: the skip was a hidden green);
  5. test_the_real_resolver_finds_the_house_root_with_no_injection: a fresh interpreter, a real
     checkout on PYTHONPATH (its cairn.egg-info shadowing, as bin/cairn's does), no
     CAIRN_BUS_CLIENT_HOUSE_ROOT, and a venv holding an editable record: _house_root() is that
     checkout. Measured 2026-11-13: every live client read None, and teeth 1-3 stayed green
     because each injects the env.

The wire is replaced for the call (remote.exchange records and answers, so nothing dials),
``subprocess.run`` is replaced so no systemctl runs, and ``_spawn`` raises, so a build that
still replaced could never start a bus at the live home. The subject is bound inside each tooth.

    bin/cairn test cairn/tools/bus_client/proofs/test_a_foreign_root_refuses_a_stale_live_bus.py
"""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROVES = {"3deafc9e36de": {
    "1": "test_a_foreign_root_at_the_live_home_sends_no_shutdown",
    "2": "test_the_house_root_still_replaces_the_live_bus",
    "3": "test_a_foreign_root_at_a_scratch_home_still_replaces",
    "4": "test_no_resolvable_house_root_refuses_at_the_live_home",
    "5": "test_the_real_resolver_finds_the_house_root_with_no_injection",
}}

_FOREIGN_HOUSE = "/nonexistent/testing-3deaf-house-root"
_LIVE_BUS_ROOT = "/nonexistent/testing-3deaf-live-bus-root"
_ENV = "CAIRN_BUS_CLIENT_HOUSE_ROOT"


def _wired(monkeypatch, *, house: str | None):
    """Replace the wire and systemctl; set (or clear) the house root. Returns (remote, sent)."""
    from cairn.tools.bus_client import remote
    sent: list[dict] = []
    state = {"down": False}

    def exchange(req, h=None, timeout=None):
        sent.append(dict(req))
        op = req.get("op")
        if op == "shutdown":
            state["down"] = True
            return {"ok": True, "json": {"stopping": True}}
        if state["down"]:
            raise ConnectionRefusedError("testing-3deaf: the replaced bus is gone")
        return {"ok": False, "stale": True, "root": _LIVE_BUS_ROOT}

    def no_spawn(*a, **k):
        raise RuntimeError("testing-3deaf: this proof never spawns a bus")

    monkeypatch.setattr(remote, "exchange", exchange)
    monkeypatch.setattr(remote, "_spawn", no_spawn)
    monkeypatch.setattr(remote.subprocess, "run",
                        lambda args, *a, **k: remote.subprocess.CompletedProcess(args, 1, "", ""))
    if house is None:
        monkeypatch.delenv(_ENV, raising=False)
    else:
        monkeypatch.setenv(_ENV, house)
    return remote, sent


def _shutdowns(sent) -> int:
    return sum(1 for r in sent if r.get("op") == "shutdown")


def _scratch_home() -> Path:
    from cairn.tools.scratch.scratch import scratch_dir
    return Path(scratch_dir("testing-3deaf-home-"))


def test_a_foreign_root_at_the_live_home_sends_no_shutdown(monkeypatch):
    remote, sent = _wired(monkeypatch, house=_FOREIGN_HOUSE)
    live = remote._live_home()
    bus = remote.RemoteBus(live)
    try:
        bus.stats()
    except remote.BusStale as exc:
        said = str(exc)
    else:
        raise AssertionError(f"a foreign root at the live home did not refuse: {sent!r}")
    assert _shutdowns(sent) == 0, f"a foreign root sent shutdown to the live bus: {sent!r}"
    # Both roots are printed resolved (on Windows "/nonexistent/x" prints as C:\\nonexistent\\x);
    # the live bus's root is the string the bus answered, printed as it came.
    house = str(Path(_FOREIGN_HOUSE).resolve())
    mine = str(Path(remote._CLASS_ROOT).resolve())
    assert house in said, f"the refusal does not name the house root {house}: {said}"
    assert mine in said, f"the refusal does not name the caller's root {mine}: {said}"
    assert _LIVE_BUS_ROOT in said, f"the refusal does not name the live bus's root: {said}"
    assert "CAIRN_BUS_HOME=" in said, f"the refusal does not say the way out: {said}"


def test_the_house_root_still_replaces_the_live_bus(monkeypatch):
    from cairn.tools.bus_client import remote as r
    remote, sent = _wired(monkeypatch, house=str(r._CLASS_ROOT))
    remote._replace(remote._live_home())
    assert _shutdowns(sent) == 1, f"the house root's client did not replace the stale bus: {sent!r}"


def test_a_foreign_root_at_a_scratch_home_still_replaces(monkeypatch):
    remote, sent = _wired(monkeypatch, house=_FOREIGN_HOUSE)
    remote._replace(_scratch_home())
    assert _shutdowns(sent) == 1, f"a scratch home's stale bus was not replaced: {sent!r}"


def test_no_resolvable_house_root_refuses_at_the_live_home(monkeypatch):
    remote, sent = _wired(monkeypatch, house=None)
    empty = _scratch_home() / "testing-3deaf-no-venv"
    monkeypatch.setenv("CAIRN_VENV", str(empty))
    try:
        remote._replace(remote._live_home())
    except remote.BusStale as exc:
        said = str(exc)
    else:
        raise AssertionError(f"with no house root the live bus was replaced: {sent!r}")
    assert _shutdowns(sent) == 0, f"with no house root a shutdown was sent: {sent!r}"
    assert str(empty) in said, f"the refusal does not name the venv it read: {said}"
    assert _ENV in said, f"the refusal does not name the env override: {said}"


def _fixture_venv(checkout: Path) -> Path:
    """A venv holding only an editable cairn record pointing at ``checkout``."""
    venv = _scratch_home() / "testing-3deaf-venv"
    rec = venv / "lib" / "python3.99" / "site-packages" / "cairn-0.0.0.dist-info"
    rec.mkdir(parents=True)
    (rec / "direct_url.json").write_text(json.dumps(
        {"dir_info": {"editable": True}, "url": checkout.resolve().as_uri()}), encoding="utf-8")
    return venv


def test_the_real_resolver_finds_the_house_root_with_no_injection(monkeypatch):
    venv = _fixture_venv(_REPO)
    env = {k: v for k, v in os.environ.items() if k != _ENV}
    env.update(CAIRN_VENV=str(venv), PYTHONPATH=str(_REPO))
    got = subprocess.run(
        [sys.executable, "-c",
         "from cairn.tools.bus_client import remote; print(remote._house_root())"],
        capture_output=True, text=True, env=env, cwd=str(venv), timeout=60)
    assert got.returncode == 0, f"the resolver crashed: {got.stderr[-600:]}"
    seen = got.stdout.strip()
    assert seen != "None", (f"with no {_ENV} and a venv record naming {_REPO}, _house_root() "
                            "is None: the foreign-replace guard is off for every live client")
    assert Path(seen) == _REPO.resolve(), f"_house_root() is {seen}, not the venv's record {_REPO}"


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
