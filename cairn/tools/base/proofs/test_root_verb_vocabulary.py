"""Proof for ticket 15d6a0ef9c11 — valid verbs: the standard CLI vocabulary.

The falsifier is numbered, so four teeth (PROVES keys follow the falsifier markers):
(1) the root shim class declares the standard verbs WITH semantics as ONE data structure
    (``ROOT_VERB_SEMANTICS``), ROOT_VERBS is derived from it, and ``list`` carries the
    table — the vocabulary is data a device answers with, not prose (WRONG INTENT clause);
(2) every device on the live roster (``cairn/devices/*/shim.py``) inherits the common
    handlers: none overrides ``resolve``, and a cold ``list`` on each names the six —
    no device opts in (WRONG INTENT clause);
(3) a collision is refused AT REGISTRATION: a device declaring a view named after a root
    view, or a bus verb named after a root verb bound to its own handler, is refused with
    exit 2 the moment it wakes — ``start`` fails, presence never reads ONLINE, no snapshot
    is written — while a device that extends ``declared_verbs`` with ``**super()`` wakes;
    and every live roster device registers clean against the root vocabulary;
(4) ``cairn <device> get status`` works uniformly: on every roster device it is one line
    of JSON with exactly device/view/cached/timestamp/data and the device's own id.

THE SHIM IS DRIVEN IN A SUBPROCESS PER COMMAND UNDER A SCRATCH HOME (the pattern of
test_root_verbs, ticket b41b0c0fff0e): the instance root is read from HOME at import, so
nothing here touches the live instance; the scratch carries a LIVE liveness record so no
shim spawns a ground loop. Cold queries wake nothing, so no bus and no store are reached;
tooth 3's registration of the live roster wakes each device in-process with no bus and
asks its declarations directly — the same call ``_ensure_device`` makes.

A hollow build could not pass: tooth 1 reads the table and its rendering; tooth 3's
refusal is the registration seat itself, reverted it wakes the colliding device and
answers.
"""
from __future__ import annotations

import importlib
import inspect
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cairn.tools.base.device import BaseDevice  # noqa: E402
from cairn.tools.base.shim import BaseShim, cli_main  # noqa: E402

PROVES = {"15d6a0ef9c11": {
    "1": "test_the_vocabulary_is_one_table_and_list_carries_it",
    "2": "test_every_roster_device_inherits_the_root_verbs",
    "3": "test_a_colliding_registration_is_refused",
    "4": "test_get_status_is_uniform_across_the_roster",
}}

_RULED = ("list", "show", "get", "stop", "start", "settings")
_GET_SHAPE = ["device", "view", "cached", "timestamp", "data"]


# --- fixtures for tooth 3 ---------------------------------------------------------------

class _Fixture(BaseDevice):
    def __init__(self, device_id: str) -> None:
        super().__init__()
        self._device_id = device_id

    @property
    def device_id(self) -> str:
        return self._device_id

    def intention(self) -> dict:
        return {"what": f"fixture {self._device_id}", "why": "proof 15d6a0ef9c11"}

    def state(self) -> dict:
        return {"awake": True}

    def settings(self) -> dict:
        return {}


class ViewCollider(_Fixture):
    def declared_views(self) -> dict:
        return {"Settings": lambda: {"mine": True}}   # folds onto the root view (ruled 2026-09-07)


class VerbCollider(_Fixture):
    def _my_get(self, envelope: dict) -> dict:
        return {"rebound": True}

    def declared_verbs(self) -> dict:
        return {**super().declared_verbs(), "get": self._my_get}


class Extender(_Fixture):
    def _frob(self, envelope: dict) -> dict:
        return {"frobbed": True}

    def declared_verbs(self) -> dict:
        return {**super().declared_verbs(), "frob": self._frob}


class _FixtureShim(BaseShim):
    KIND: type = _Fixture

    @property
    def device_id(self) -> str:
        return f"15d6-{self.KIND.__name__.lower()}"

    def _start_device(self):
        return self.KIND(self.device_id)


class ViewColliderShim(_FixtureShim):
    KIND = ViewCollider


class VerbColliderShim(_FixtureShim):
    KIND = VerbCollider


class ExtenderShim(_FixtureShim):
    KIND = Extender


FIXTURES = {"view": ViewColliderShim, "verb": VerbColliderShim, "extender": ExtenderShim}


# --- the harness ------------------------------------------------------------------------

def _roster() -> list[str]:
    return sorted(p.parent.name for p in (ROOT / "cairn" / "devices").glob("*/shim.py"))


def _shim_class(name: str) -> type:
    mod = importlib.import_module(f"cairn.devices.{name}.shim")
    classes = [c for _, c in sorted(vars(mod).items())
               if inspect.isclass(c) and issubclass(c, BaseShim) and c is not BaseShim
               and c.__module__ == mod.__name__]
    assert classes, f"cairn/devices/{name}/shim.py declares no BaseShim subclass"
    return classes[0]


def _scratch() -> Path:
    home = Path(tempfile.mkdtemp(prefix="15d6-home-"))
    from cairn.devices.cairn.machines.ground_loop.liveness import write_liveness
    lh = home / ".cairn" / "devices" / "cairn" / "0" / "machines" / "ground_loop"
    lh.mkdir(parents=True)
    write_liveness(datetime.now(timezone.utc).astimezone(), {"beats": 1, "subscribers": []},
                   os.getpid(), lh)
    return home


def _run(home: Path, which: str, *argv: str) -> subprocess.CompletedProcess:
    env = dict(os.environ, HOME=str(home), PYTHONPATH=str(ROOT))
    return subprocess.run([sys.executable, __file__, "--drive", which, *argv], env=env,
                          capture_output=True, text=True, timeout=120, cwd=str(ROOT))


def _snapshots(home: Path) -> list[str]:
    return sorted(str(p.relative_to(home)) for p in home.rglob("last_known.json"))


@pytest.fixture(scope="module")
def home():
    h = _scratch()
    try:
        yield h
    finally:
        shutil.rmtree(h, ignore_errors=True)


# --- the teeth --------------------------------------------------------------------------

def test_the_vocabulary_is_one_table_and_list_carries_it(home: Path) -> None:
    from cairn.tools.base import shim
    table = getattr(shim, "ROOT_VERB_SEMANTICS", None)
    assert isinstance(table, dict), "the root shim declares no ROOT_VERB_SEMANTICS table — the vocabulary is prose"
    assert tuple(table) == _RULED, (tuple(table), _RULED)
    for verb, meaning in table.items():
        assert isinstance(meaning, str) and len(meaning.split()) >= 4, (verb, meaning)
    assert shim.ROOT_VERBS == tuple(table), "ROOT_VERBS is not derived from the table — two mouths"
    r = _run(home, "extender", "list")
    assert r.returncode == 0, r.stderr
    lines = [ln.strip() for ln in r.stdout.splitlines()]
    assert "semantics:" in lines, r.stdout
    for verb, meaning in table.items():
        assert f"{verb}: {meaning}" in lines, (verb, r.stdout)
    assert not _snapshots(home), "a cold list woke the device"
    print("ok test_the_vocabulary_is_one_table_and_list_carries_it")


def test_every_roster_device_inherits_the_root_verbs(home: Path) -> None:
    roster = _roster()
    assert len(roster) >= 5, roster
    for name in roster:
        cls = _shim_class(name)
        for attr in ("resolve", "_resolve"):
            assert getattr(cls, attr) is getattr(BaseShim, attr), \
                f"{name}'s shim overrides {attr} — a device opted in to its own vocabulary"
        r = _run(home, name, "list")
        assert r.returncode == 0, (name, r.stderr)
        lines = [ln.strip() for ln in r.stdout.splitlines()]
        for verb in _RULED:
            assert verb in lines, (name, verb, r.stdout)
    assert not _snapshots(home), "a cold list on the roster woke a device"
    print(f"ok test_every_roster_device_inherits_the_root_verbs ({len(roster)}: {' '.join(roster)})")


def test_a_colliding_registration_is_refused(home: Path) -> None:
    from cairn.tools.base import shim
    assert getattr(shim, "RootVerbCollision", None) is not None, "no RootVerbCollision — registration refuses nothing"
    # a view named after a root view: start is refused, the shim never reads ONLINE, no snapshot
    r = _run(home, "view", "start")
    assert r.returncode == 2 and r.stdout == "", (r.returncode, r.stdout, r.stderr)
    assert "device view 'settings' collides with the root view" in r.stderr, r.stderr
    # a bus verb named after a root verb, bound to the device's own handler
    r = _run(home, "verb", "show", "status", "hot")
    assert r.returncode == 2 and r.stdout == "", (r.returncode, r.stdout, r.stderr)
    assert "device verb 'get' collides with the root verb" in r.stderr, r.stderr
    assert not _snapshots(home), f"a refused registration still stamped a snapshot: {_snapshots(home)}"
    # the presence stays below ONLINE across the refusal, in one process
    r = _run(home, "verb", "--presence", "start")
    assert r.returncode == 2, (r.stdout, r.stderr)
    assert r.stdout.strip() == shim.NEVER_BOOTED, r.stdout
    # extending with **super() keeps the root meaning and wakes
    r = _run(home, "extender", "start")
    assert r.returncode == 0 and r.stdout.strip() == "started 15d6-extender", (r.stdout, r.stderr)
    assert _snapshots(home) == [".cairn/devices/15d6-extender/0/last_known.json"], _snapshots(home)
    # every live roster device registers clean — the same call _ensure_device makes, no bus
    for name in _roster():
        r = _run(home, name, "--register")
        assert r.returncode == 0, (name, r.stdout, r.stderr)
        assert r.stdout.strip().startswith(f"registered {name}"), (name, r.stdout)
    print("ok test_a_colliding_registration_is_refused")


def test_get_status_is_uniform_across_the_roster(home: Path) -> None:
    for name in _roster():
        r = _run(home, name, "get", "status")
        assert r.returncode == 0, (name, r.stderr)
        assert r.stdout.count("\n") == 1, (name, r.stdout)
        payload = json.loads(r.stdout)
        assert list(payload) == _GET_SHAPE, (name, list(payload))
        assert payload["device"] == name and payload["view"] == "status", (name, payload)
        assert payload["cached"] is True, (name, payload)
    print("ok test_get_status_is_uniform_across_the_roster")


# --- the driver: what the subprocess runs ---------------------------------------------------

def _drive(argv: list[str]) -> int:
    which, rest = argv[0], argv[1:]
    cls = FIXTURES[which] if which in FIXTURES else _shim_class(which)
    if rest and rest[0] == "--register":
        s = cls()
        dev = s._start_device()
        BaseShim._register(dev)
        print(f"registered {which}")
        return 0
    if rest and rest[0] == "--presence":
        s = cls()
        result = s.resolve(rest[1:])
        print(s.presence)
        return result["exit"]
    return cli_main(cls, rest)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--drive":
        sys.exit(_drive(sys.argv[2:]))
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
