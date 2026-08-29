"""PROOF — the pulse file IS the subscription: presence activates, absence unloads.

Ticket ``the-pulse-file-is-the-subscription``, Akien's design verbatim (2026-08-15):

  "last time i was here, pulse.py did not exist. so inside a try/except i can either run it,
   or i can import it. either way, once i activate it, it's now in my list of things i know
   about.... next pass thru, the file is missing. so i remove it from my list. if i imported
   it, i now unload it. this is true for every device. a groundloop folder can exist at the
   class level or the instance level. nobody has to do anything except put the file there or
   remove it."

WHAT A HOLLOW BUILD WOULD PASS AND THIS MUST NOT (Law 8). A "discovery" that ran once at
construction would pass "it finds the file" and fail the teeth that write and remove files
mid-run. An "unload" that only dropped the roster entry would pass "it stops firing" and
fail ``test_removal_unloads_and_readd_reexecutes``, which asserts the synthetic name leaves
``sys.modules`` AND that a re-added file re-executes its top-level — bookkeeping cannot fake
either. A cache that re-imported every beat would pass "it activates" and fail the
execution-count tooth. And a service fired from the loop's own body instead of the shim
would pass every latency tooth and fail the isolation tooth, where one device's raising
pulse must not stop another's service in the same beat (the 584aa74 goof's headstone).

Every tooth runs on TEMP trees (class root AND instance home both fixtures): nothing here
reads the real repo's groundloop folders or writes the real ``~/.cairn``. Loops are built
with no ``liveness_home`` except the one tooth that measures the durable surface, which
gets a temp home.

    python3 cairn/devices/cairn/machines/ground_loop/proofs/test_pulse_service.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[6]))

from cairn.devices.cairn.machines.ground_loop.discovery import (  # noqa: E402
    GROUNDLOOP_DIR, PULSE_FILE, PulseCache, device_folders, pulse_sites)
from cairn.devices.cairn.machines.ground_loop.loop import GroundLoopDevice  # noqa: E402

NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)

# A pulse whose top-level execution and per-beat hook both leave marks on disk — the marks
# are what the teeth count, so "executed" is measured, never inferred from the roster.
_PULSE = '''
open({imported!r}, "a").write("i")
def on_pulse(now, context):
    open({served!r}, "a").write("p")
'''

_RAISING = "raise RuntimeError('this pulse is broken on purpose')\n"

_HOOK_RAISES = '''
def on_pulse(now, context):
    raise RuntimeError("the hook is broken on purpose")
'''


def _marks(path: Path) -> int:
    try:
        return len(path.read_text())
    except OSError:
        return 0


def _drop(folder: Path, body: str) -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / PULSE_FILE
    path.write_text(body, encoding="utf-8")
    return path


def _bump(path: Path) -> None:
    """Force a distinct mtime — identity is path+mtime, and filesystem stamps are coarse."""
    st = path.stat()
    os.utime(path, (st.st_atime, st.st_mtime + 10))


def _pulse_loop(class_root: Path, instance_home: Path, **kw) -> GroundLoopDevice:
    return GroundLoopDevice(
        pulse_finder=lambda: pulse_sites(class_root=class_root, instance_home=instance_home),
        **kw)


# --- teeth ------------------------------------------------------------------

def test_the_walk_finds_both_levels_and_leaves_probes_alone():
    """The second registration folder rides the SAME walk (same prune, same id-from-parent,
    same sorted stability) and the probes walk does not see it."""
    with tempfile.TemporaryDirectory() as td:
        root, home = Path(td) / "repo", Path(td) / "dot_cairn"
        _drop(root / "devices" / "alpha" / GROUNDLOOP_DIR, "")
        _drop(root / "devices" / "beta" / GROUNDLOOP_DIR, "")
        (root / "devices" / "beta" / "probes").mkdir(parents=True)
        _drop(root / "__pycache__" / "noise" / GROUNDLOOP_DIR, "")          # pruned
        _drop(root / ".hidden" / "noise" / GROUNDLOOP_DIR, "")              # pruned
        (root / "devices" / "gamma" / GROUNDLOOP_DIR).mkdir(parents=True)   # folder, no file
        _drop(home / "alpha" / "0" / GROUNDLOOP_DIR, "")

        sites = pulse_sites(class_root=root, instance_home=home)
        got = [(s["device_id"], s["level"]) for s in sites]
        assert ("alpha", "class") in got and ("beta", "class") in got, got
        assert ("alpha", "instance") in got, got
        assert all(d not in {"noise", "gamma"} for d, _ in got), got
        assert [str(s["path"]) for s in sites] == sorted(str(s["path"]) for s in sites)

        # the probes walk is untouched by the second folder: it sees probes/ only.
        probe_ids = {d for d, _ in device_folders(root)}
        assert probe_ids == {"beta"}, probe_ids


def test_class_and_instance_pair_both_fire():
    """Both present -> BOTH fire: the unit is the FILE (the ruled distinction)."""
    with tempfile.TemporaryDirectory() as td:
        root, home = Path(td) / "repo", Path(td) / "dot_cairn"
        m = Path(td) / "marks"
        m.mkdir()
        _drop(root / "devices" / "alpha" / GROUNDLOOP_DIR,
              _PULSE.format(imported=str(m / "ci"), served=str(m / "cs")))
        _drop(home / "alpha" / "0" / GROUNDLOOP_DIR,
              _PULSE.format(imported=str(m / "ii"), served=str(m / "is")))

        loop = _pulse_loop(root, home)
        loop.beat(NOW)
        assert _marks(m / "ci") == 1 and _marks(m / "ii") == 1, "both levels import"
        assert _marks(m / "cs") == 1 and _marks(m / "is") == 1, "both levels serve"
        live = loop.state()["pulse_services"]
        assert {(e["device"], e["level"]) for e in live} == {("alpha", "class"),
                                                             ("alpha", "instance")}, live


def test_activation_is_once_and_later_beats_are_a_stat():
    """First sight imports and executes top-level exactly ONCE; the hook fires per beat;
    an unchanged file never re-imports."""
    with tempfile.TemporaryDirectory() as td:
        root, home = Path(td) / "repo", Path(td) / "empty"
        m = Path(td) / "marks"
        m.mkdir()
        _drop(root / "devices" / "alpha" / GROUNDLOOP_DIR,
              _PULSE.format(imported=str(m / "i"), served=str(m / "s")))
        loop = _pulse_loop(root, home)
        for _ in range(3):
            loop.beat(NOW)
        assert _marks(m / "i") == 1, f"top-level ran {_marks(m / 'i')}x, not once"
        assert _marks(m / "s") == 3, f"hook served {_marks(m / 's')}x across 3 beats"


def test_a_raising_pulse_is_recorded_once_and_damped():
    """A broken pulse cannot reach the beat, lands as ONE refusal event, and is not
    retried until the file changes — then a fixed file activates."""
    with tempfile.TemporaryDirectory() as td:
        root, home = Path(td) / "repo", Path(td) / "empty"
        m = Path(td) / "marks"
        m.mkdir()
        path = _drop(root / "devices" / "alpha" / GROUNDLOOP_DIR, _RAISING)
        loop = _pulse_loop(root, home)
        loop.beat(NOW)
        loop.beat(NOW)
        events = loop.state()["pulse_events"]
        refused = [e for e in events if e["event"] == "refused"]
        assert len(refused) == 1, f"damping failed: {len(refused)} refusals in 2 beats"
        assert "RuntimeError" in refused[0]["lack"], refused[0]
        assert loop.state()["pulse_refusals"], "the known-bad file is loud on state()"

        path.write_text(_PULSE.format(imported=str(m / "i"), served=str(m / "s")),
                        encoding="utf-8")
        _bump(path)
        loop.beat(NOW)
        assert _marks(m / "i") == 1, "a changed file is retried and activates"
        assert not loop.state()["pulse_refusals"], "the refusal clears with the fix"


def test_removal_unloads_and_readd_reexecutes():
    """The genuinely new half: a vanished file's module leaves ``sys.modules`` in the same
    pass that drops it from the learned list, and a re-added file re-executes fresh —
    which is only possible if the unload was real."""
    with tempfile.TemporaryDirectory() as td:
        root, home = Path(td) / "repo", Path(td) / "empty"
        m = Path(td) / "marks"
        m.mkdir()
        body = _PULSE.format(imported=str(m / "i"), served=str(m / "s"))
        path = _drop(root / "devices" / "alpha" / GROUNDLOOP_DIR, body)
        # DIFF AGAINST A BASELINE, not against empty: a sibling tooth's loop that died
        # without a final beat legitimately leaves its names behind (unload happens at
        # reconcile, and a dead loop reconciles nothing) — this tooth measures ITS file.
        before = {n for n in sys.modules if n.startswith("cairn._pulse.")}
        loop = _pulse_loop(root, home)
        loop.beat(NOW)
        held = [n for n in sys.modules
                if n.startswith("cairn._pulse.") and n not in before]
        assert len(held) == 1, f"activation registers exactly one synthetic name: {held}"
        name = held[0]

        path.unlink()
        loop.beat(NOW)
        assert name not in sys.modules, "deactivation must EVICT, not merely delist"
        assert not loop.state()["pulse_services"], "the learned list dropped it same pass"
        assert [e["event"] for e in loop.state()["pulse_events"]].count("deactivated") == 1

        _drop(path.parent, body)
        _bump(path)
        loop.beat(NOW)
        assert _marks(m / "i") == 2, "a re-added file re-executes its top-level fresh"


def test_an_in_place_edit_is_remove_plus_add_in_one_beat():
    """Identity is path+mtime: the next beat after an edit runs the NEW bytes, and the
    event stream shows deactivated+activated in the same pass."""
    with tempfile.TemporaryDirectory() as td:
        root, home = Path(td) / "repo", Path(td) / "empty"
        m = Path(td) / "marks"
        m.mkdir()
        path = _drop(root / "devices" / "alpha" / GROUNDLOOP_DIR,
                     _PULSE.format(imported=str(m / "old_i"), served=str(m / "old_s")))
        loop = _pulse_loop(root, home)
        loop.beat(NOW)
        path.write_text(_PULSE.format(imported=str(m / "new_i"), served=str(m / "new_s")),
                        encoding="utf-8")
        _bump(path)
        loop.beat(NOW)
        assert _marks(m / "new_i") == 1, "the edit's new bytes ran on the very next beat"
        assert _marks(m / "new_s") == 1, "and the new hook served that same beat"
        beats = {}
        for ev in loop.state()["pulse_events"]:
            beats.setdefault(ev["beat"], []).append(ev["event"])
        assert any(set(evs) >= {"deactivated", "activated"} for evs in beats.values()), \
            f"remove+add must land in ONE beat: {beats}"


def test_one_devices_raising_hook_does_not_stop_anothers_service():
    """Firing lives in the SHIM: each device's pulse is isolated per shim, so a raising
    hook is a loud record entry and the other device still serves the same beat."""
    with tempfile.TemporaryDirectory() as td:
        root, home = Path(td) / "repo", Path(td) / "empty"
        m = Path(td) / "marks"
        m.mkdir()
        _drop(root / "devices" / "broken" / GROUNDLOOP_DIR, _HOOK_RAISES)
        _drop(root / "devices" / "healthy" / GROUNDLOOP_DIR,
              _PULSE.format(imported=str(m / "i"), served=str(m / "s")))
        loop = _pulse_loop(root, home)
        record = loop.beat(NOW)
        assert _marks(m / "s") == 1, "the healthy device served despite the broken one"
        by_device = {p["device"]: p for p in record["pulses"]}
        outcomes = [sv["outcome"] for sv in by_device["broken"].get("services", [])]
        assert outcomes == ["refused"], f"the raising hook is loud, not fatal: {outcomes}"
        assert by_device["healthy"]["services"][0]["outcome"] == "ok"


def test_no_new_durable_record_and_the_face_tracks_add_remove():
    """Constrain's OUT bound, measured: pulse activity writes NOTHING under the loop's
    device space beside liveness.json — the roster rides state() INTO that record — and
    the face tracks add/remove within one reconcile each."""
    with tempfile.TemporaryDirectory() as td:
        root, home = Path(td) / "repo", Path(td) / "empty"
        live_home = Path(td) / "device_space"
        m = Path(td) / "marks"
        m.mkdir()
        path = _drop(root / "devices" / "alpha" / GROUNDLOOP_DIR,
                     _PULSE.format(imported=str(m / "i"), served=str(m / "s")))
        loop = _pulse_loop(root, home, liveness_home=live_home)
        loop.beat(NOW)
        listing = sorted(p.name for p in live_home.iterdir())
        assert listing == ["liveness.json"], f"a new durable record appeared: {listing}"
        written = json.loads((live_home / "liveness.json").read_text())
        assert [e["device"] for e in written["state"]["pulse_services"]] == ["alpha"]
        assert any(e["event"] == "activated" for e in written["state"]["pulse_events"])

        path.unlink()
        loop.beat(NOW)
        listing = sorted(p.name for p in live_home.iterdir())
        assert listing == ["liveness.json"], f"a new durable record appeared: {listing}"
        written = json.loads((live_home / "liveness.json").read_text())
        assert written["state"]["pulse_services"] == [], "the face forgot it within a beat"


def test_a_pulse_only_device_survives_the_probes_reconcile():
    """A device with a groundloop/ and NO probes/ gets a shim and KEEPS it while its pulse
    stands — the gone-computation must not drop what the probes walk cannot see."""
    with tempfile.TemporaryDirectory() as td:
        root, home = Path(td) / "repo", Path(td) / "empty"
        m = Path(td) / "marks"
        m.mkdir()
        path = _drop(root / "devices" / "alpha" / GROUNDLOOP_DIR,
                     _PULSE.format(imported=str(m / "i"), served=str(m / "s")))

        from cairn.devices.cairn.machines.ground_loop.discovery import discover
        loop = GroundLoopDevice(
            discover=lambda cache=None, skip=None: discover(root=root, cache=cache,
                                                            skip=skip),
            pulse_finder=lambda: pulse_sites(class_root=root, instance_home=home))
        loop.beat(NOW)
        loop.beat(NOW)
        assert "alpha" in loop.subscribers, loop.subscribers
        assert _marks(m / "s") == 2, "the pulse served on both beats"
        path.unlink()
        loop.beat(NOW)
        assert "alpha" not in loop.subscribers, "pulse gone + no probes -> off the roster"


def test_the_watchme_probe_is_armed_and_judges_from_fixtures():
    """The carrier probe: a frozen PROBE with carry and enough; trigger FALSE (never a
    raise) on an empty surface; the judge reads within-bound from a record fixture."""
    from cairn.tools.base.probe import Probe
    from cairn.devices.cairn.machines.ground_loop.probes import pulse_service_within_a_beat as psw

    assert isinstance(psw.PROBE, Probe)
    assert psw.PROBE.carry is not None and psw.PROBE.enough is not None

    empty = psw.judge({"verdict": "DEAD", "record": None})
    assert psw._trigger(NOW, {"judged": empty}) is False
    assert psw._enough({"judged": empty}) is False

    record = {"verdict": "LIVE", "record": {"pid": 42, "state": {
        "beats": 10,
        "pulse_services": [],
        "pulse_refusals": [],
        "pulse_events": [
            {"event": "activated", "device": "a", "path": "/x", "mtime": 1000.0,
             "beat": 3, "at": datetime.fromtimestamp(1001.0, timezone.utc).isoformat()},
            {"event": "deactivated", "device": "a", "path": "/x", "beat": 5,
             "at": datetime.fromtimestamp(1003.0, timezone.utc).isoformat()},
        ]}}}
    judged = psw.judge(record)
    assert judged["seconds_per_beat"] == 1.0, judged["seconds_per_beat"]
    assert len(judged["activations_within_bound"]) == 1, judged
    assert judged["measured_within_a_beat"] == 2, judged
    assert psw._trigger(NOW, {"judged": judged}) is True
    assert psw._enough({"judged": judged}) is False, "2 events is not the ticket's 10"

    late = {"verdict": "LIVE", "record": {"pid": 42, "state": {
        "beats": 10, "pulse_services": [], "pulse_refusals": [],
        "pulse_events": [
            {"event": "activated", "device": "a", "path": "/x", "mtime": 1000.0,
             "beat": 3, "at": datetime.fromtimestamp(1500.0, timezone.utc).isoformat()},
        ]}}}
    judged_late = psw.judge(late)
    assert judged_late["activations_late"], "a 500s gap must read LATE, not within-bound"


def test_the_cache_alone_never_raises_and_events_are_complete():
    """The PulseCache's own contract, without a loop: reconcile never raises, and every
    event is a complete dict (device, level, path + the event's own facts)."""
    with tempfile.TemporaryDirectory() as td:
        root, home = Path(td) / "repo", Path(td) / "empty"
        _drop(root / "devices" / "alpha" / GROUNDLOOP_DIR, _RAISING)
        cache = PulseCache()
        events = cache.reconcile(pulse_sites(class_root=root, instance_home=home))
        assert [e["event"] for e in events] == ["refused"], events
        assert {"device", "level", "path", "mtime", "lack"} <= set(events[0]), events[0]
        assert cache.active() == []
        events = cache.reconcile([])
        assert events == [], "a vanished refused file just drops its damper"


if __name__ == "__main__":
    failures = 0
    for name, fn in sorted(globals().items()):
        if not name.startswith("test_") or not callable(fn):
            continue
        try:
            fn()
            print(f"  PASS  {name}")
        except Exception as exc:  # noqa: BLE001 — the proof reports, it does not raise
            failures += 1
            print(f"  FAIL  {name}: {type(exc).__name__}: {exc}")
    if failures:
        print(f"RED — {failures} tooth/teeth bit")
        raise SystemExit(1)
    print("green — presence is the subscription, absence is the unload, and the loop only beats")
