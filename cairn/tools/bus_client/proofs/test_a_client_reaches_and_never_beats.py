"""A CLIENT REACHES AND A RUNNER BEATS — ticket ``fc93d8cd5961`` (2026-09-09).

MEASURED: ``connect_bus()`` 23.5s (a full ``GroundLoopDevice.beat``), ``reach()`` 0.23s.
Five clients paid the beat to ask for one embedding. This proof pins that they no longer do,
and that the watch which keeps it so can actually see a client.

WHAT THIS PROVES, and why a hollow build could not pass it:
  (i)   BEAT STUBBED TO RAISE, every client helper still hands back a working bus. Revert
        any of the five client files and this tooth raises at that client — the stub is the
        beat, and a client that beats hits it.
  (ii)  THE WALK BITES. A fixture tree with one planted client caller, one roster file, one
        proofs/ file and one docstring-only mention comes back as exactly the planted caller,
        file and line. A walk that matched nothing would return [] over the live tree too,
        which is why (iii) alone is worthless.
  (iii) THE LIVE WALK IS EMPTY over class-space.
  (iv)  THE PROBE IS ARMED: a frozen PROBE with carry and enough, and enough is False while
        a caller stands.
  (v)   THE DOCSTRING NO LONGER TEACHES THE DEFECT: ``connect_bus`` stops calling
        ``beat=False`` a test-fixture case and names ``reach`` as the client's face.
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

from cairn.tools import bus_client

# THE PROBE IS IMPORTED INSIDE THE TEETH THAT CHECK IT, NEVER AT MODULE LEVEL. The hollow
# check reverts the build file by file and asks which teeth red; a module-level import of the
# probe would make its removal break the whole proof (no teeth printed — "unreadable") instead
# of redding (ii), (iii), (iv). Measured 2026-09-09 on this very file, first hollow run.
_PROBE_MOD = "cairn.tools.bus_client.probes.a_client_reaches_and_never_beats"


def _probe():
    import importlib
    return importlib.import_module(_PROBE_MOD)

_REPO_ROOT = Path(__file__).resolve().parents[4]

# WHICH CLAUSE OF THE TICKET'S FALSIFIER EACH TOOTH PROVES — read by proof_coverage and by
# the hollow check, which reverts the build file by file and asks which of THESE go red.
PROVES = {
    "fc93d8cd5961": {
        # (1) counsel under 1s: the mechanism is that no client beats — stub the beat, call
        #     every client; and the docstring that taught the beat as the client face is gone.
        "1": "test_i_every_client_helper_reaches_without_beating",
        "1b": "test_v_connect_bus_no_longer_calls_beat_false_a_test_fixture_case",
        # (2) the tooth reds on a reintroduced caller — the fixture tree, and the probe that
        #     carries the walk into the beat.
        "2": "test_ii_the_walk_names_a_planted_client_and_nothing_else",
        "2b": "test_iv_the_probe_is_armed_and_enough_is_false_while_a_caller_stands",
        # (3) the walk finds zero client callers over live class-space.
        "3": "test_iii_the_live_walk_over_class_space_is_empty",
    }
}


class _BeatRaised(RuntimeError):
    pass


def _stub_beat():
    from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice
    original = GroundLoopDevice.beat

    def raising(self, now, context=None):
        raise _BeatRaised("a client fired the heartbeat")

    GroundLoopDevice.beat = raising
    return lambda: setattr(GroundLoopDevice, "beat", original)


def test_i_every_client_helper_reaches_without_beating():
    restore = _stub_beat()
    try:
        import skills.chart.live as chart_live
        import cairn.devices.codemother.watch as cm_watch
        from cairn.devices.librarian import live as lib_live
        from cairn.devices.intention_extractor import live as ie_live
        from cairn.devices.codemother import seed_trees
        chart_live._BUS = None
        cm_watch._BUS = None
        clients = {
            "skills/chart/live.py": chart_live._bus,
            "cairn/devices/codemother/watch.py": cm_watch._bus,
            "cairn/devices/librarian/live.py": lib_live._wire_bus,
            "cairn/devices/intention_extractor/live.py": ie_live._wire_bus,
        }
        for name, helper in clients.items():
            try:
                bus = helper()
            except _BeatRaised as e:
                raise AssertionError(f"{name} BEATS to ask one question: {e}") from None
            assert hasattr(bus, "request"), f"{name} returned no bus: {bus!r}"
        try:
            embed = seed_trees._embed_fn()
        except _BeatRaised as e:
            raise AssertionError(f"cairn/devices/codemother/seed_trees.py BEATS: {e}") from None
        assert callable(embed)
    finally:
        restore()
        import skills.chart.live as chart_live
        import cairn.devices.codemother.watch as cm_watch
        chart_live._BUS = None
        cm_watch._BUS = None


def test_ii_the_walk_names_a_planted_client_and_nothing_else():
    _m = _probe(); RUNNER_ROSTER, walk_client_callers = _m.RUNNER_ROSTER, _m.walk_client_callers
    with tempfile.TemporaryDirectory(prefix="a-client-reaches-fixture-") as d:
        root = Path(d)
        (root / "pkg").mkdir()
        (root / "pkg" / "client.py").write_text(
            '"""a docstring that says connect_bus and connect_system is not a caller."""\n'
            "from cairn.tools.bus_client import connect_bus\n"
            "\n"
            "def wire():\n"
            "    # a comment naming connect_bus() is not a caller either\n"
            "    return connect_bus(devices=['inference_domain'])\n", encoding="utf-8")
        (root / "pkg" / "mention_only.py").write_text(
            '"""connect_bus(devices=[]) in prose only."""\nX = "connect_system("\n',
            encoding="utf-8")
        (root / "pkg" / "proofs").mkdir()
        (root / "pkg" / "proofs" / "test_beat_cost.py").write_text(
            "from cairn.tools.bus_client import connect_bus\nbus = connect_bus()\n",
            encoding="utf-8")
        for rel in RUNNER_ROSTER:
            p = root / rel
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text("import cairn.tools.bus_client as bc\nbus, loop = bc.connect_system()\n",
                         encoding="utf-8")
        (root / "pkg" / "broken.py").write_text("def (:\n", encoding="utf-8")
        found = walk_client_callers(root)
        assert found == [{"file": "pkg/client.py", "line": 6, "callee": "connect_bus"}], found
        (root / "pkg" / "attr.py").write_text(
            "import cairn.tools.bus_client as bc\nb = bc.connect_system(beat=True)\n",
            encoding="utf-8")
        found = walk_client_callers(root)
        assert [f["file"] for f in found] == ["pkg/attr.py", "pkg/client.py"], found
        assert found[0]["callee"] == "connect_system"


def test_iii_the_live_walk_over_class_space_is_empty():
    _m = _probe(); RUNNER_ROSTER, walk_client_callers = _m.RUNNER_ROSTER, _m.walk_client_callers
    found = walk_client_callers(_REPO_ROOT)
    assert found == [], f"a client in class-space beats: {found}"
    for rel in RUNNER_ROSTER:
        assert (_REPO_ROOT / rel).is_file(), f"roster names a file that is not there: {rel}"


def test_iv_the_probe_is_armed_and_enough_is_false_while_a_caller_stands():
    _m = _probe(); PROBE = _m.PROBE
    assert PROBE.carry is not None and PROBE.enough is not None
    try:
        PROBE.why = "x"
        raise AssertionError("PROBE is not frozen")
    except (AttributeError, TypeError):
        pass
    standing = {"clients": {"client_callers": [{"file": "x.py", "line": 1, "callee": "connect_bus"}],
                            "count": 1},
                "tooth": {"proven": True, "why": "fixture"}}
    assert PROBE.trigger(None, standing) is True
    assert PROBE.enough(standing) is False
    carried = PROBE.carry(standing)
    assert carried["count"] == 1 and carried["client_callers"][0]["file"] == "x.py"
    assert PROBE.enough({"clients": {"client_callers": [], "count": 0},
                         "tooth": {"proven": False, "why": "never sealed"}}) is False
    assert PROBE.enough({"clients": {"client_callers": [], "count": 0},
                         "tooth": {"proven": True, "why": "sealed green"}}) is True
    assert PROBE.to == "harbor_master"


def test_v_connect_bus_no_longer_calls_beat_false_a_test_fixture_case():
    doc = bus_client.connect_bus.__doc__ or ""
    assert "Almost always True" not in doc, "connect_bus still teaches the defect"
    assert "reach" in doc, "connect_bus's docstring does not point a client at reach()"
    assert "beat" in (bus_client.reach.__doc__ or "")


TESTS = [
    test_i_every_client_helper_reaches_without_beating,
    test_ii_the_walk_names_a_planted_client_and_nothing_else,
    test_iii_the_live_walk_over_class_space_is_empty,
    test_iv_the_probe_is_armed_and_enough_is_false_while_a_caller_stands,
    test_v_connect_bus_no_longer_calls_beat_false_a_test_fixture_case,
]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
