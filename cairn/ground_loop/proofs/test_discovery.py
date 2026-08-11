"""PROOF — the pulse roster is read from DISK, and a broken device is benched, not retried.

Akien's ruling, 2026-08-11, is the contract these teeth bite on:

  "ON EACH PASS THE GROUND LOOP POLLS A FOLDER FOR EACH DEVICE AND IF THERE IS CODE THERE
   THE GROUND LOOP RUNS IT... EACH CALL HAS TO BE WRAPPED IN TRY/CATCH SO THE GROUND LOOP
   CANNOT FAIL. FAILS AT THE DEVICE LEVEL ISSUE A TROUBLE TICKET, WHICH CAN COUNT FAILS,
   BUT A FAILING ONE WONT BE RETRIED UNTIL ITS TROUBLE TICKET IS CLEARED."

WHAT A HOLLOW BUILD WOULD PASS AND THIS MUST NOT (Law 8). A discovery that ran once at
construction would pass "it finds the folders" and fail every tooth below that writes a file
mid-run. A bench that merely stopped *pulsing* a broken device — while still importing it
every second — would pass "it does not fire" and fail ``test_a_benched_device_is_not_even_
imported``, which counts import attempts. And a loop that raised one ticket per beat would
pass "a ticket exists" and fail the count tooth, which is the whole damper.

Every tooth runs on a TEMP tree with a TEMP trouble root: nothing here reads the real repo or
writes the real commons. The loop is built with no ``liveness_home``, so it is the anonymous
in-process heartbeat and touches no device space (the same discipline the sibling proofs use).

    python3 cairn/ground_loop/proofs/test_discovery.py     # exit 0 = green
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cairn.ground_loop.discovery import ProbeCache, discover, device_folders  # noqa: E402
from cairn.ground_loop.loop import TROUBLE_PREFIX, GroundLoopDevice  # noqa: E402
from cairn.trouble.trouble import TroubleDevice  # noqa: E402

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)

_GOOD = '''
from cairn.base.probe import Probe
FIRED = []
PROBE = Probe(why="{why}", trigger=lambda now, ctx: {fires}, to="harbor_master",
              body={{"k": "v"}})
'''

_BROKEN_IMPORT = "import a_module_that_does_not_exist_anywhere\nPROBE = None\n"
_NO_PROBE = "X = 1\n"
_NOT_A_PROBE = "PROBE = 'this is a string, not a Probe'\n"


def _device(root: Path, name: str, files: dict[str, str]) -> Path:
    folder = root / name / "probes"
    folder.mkdir(parents=True, exist_ok=True)
    for filename, body in files.items():
        (folder / filename).write_text(body, encoding="utf-8")
    return folder


def _loop(root: Path, trouble_root: Path):
    """A loop wired to a temp tree and a temp trouble lane — the same injection the resident
    runner does with the real world, with the folder read counted so the bench can be measured
    at the IMPORT rather than at the pulse."""
    trouble = TroubleDevice(root=trouble_root)
    calls = {"imports": 0}

    class CountingCache(ProbeCache):
        def probes_for(self, folder):
            calls["imports"] += 1
            return super().probes_for(folder)

    cache = CountingCache()

    def discoverer(cache=None, skip=None):   # noqa: ARG001 — the loop's cache, ours is the tree's
        return discover(root=root, cache=_held[0], skip=skip)

    _held = [cache]
    return GroundLoopDevice(discover=discoverer, trouble=trouble), trouble, calls


# --- teeth ------------------------------------------------------------------

def test_a_folder_on_disk_is_the_registration():
    """No subscribe call: a device with a probes/ folder is pulsed because it EXISTS."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "alpha", {"w.py": _GOOD.format(why="alpha watch", fires="False")})
        loop, _, _ = _loop(root, root / "_troubles")
        record = loop.beat(NOW)
        assert record["pulsed"] == ["alpha"], record["pulsed"]
        assert loop.subscribers == ["alpha"]


def test_a_probe_written_mid_run_is_fired_by_the_next_beat():
    """'If there is code there the ground loop runs it' — including code that appeared one
    beat ago. A discovery that ran once at construction dies here."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "alpha", {"w.py": _GOOD.format(why="alpha watch", fires="False")})
        loop, _, _ = _loop(root, root / "_troubles")
        loop.beat(NOW)
        assert loop.subscribers == ["alpha"]
        _device(root, "beta", {"w.py": _GOOD.format(why="beta watch", fires="False")})
        record = loop.beat(NOW)
        assert sorted(record["pulsed"]) == ["alpha", "beta"], record["pulsed"]


def test_a_probe_deleted_mid_run_leaves_the_roster():
    """The stale-list failure, inverted: disk shrank, so the roster shrank. No maintenance."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        folder = _device(root, "alpha", {"w.py": _GOOD.format(why="a", fires="False")})
        _device(root, "beta", {"w.py": _GOOD.format(why="b", fires="False")})
        loop, _, _ = _loop(root, root / "_troubles")
        loop.beat(NOW)
        assert sorted(loop.subscribers) == ["alpha", "beta"]
        shutil.rmtree(folder)   # rmtree, not rmdir: importing a probe leaves a __pycache__
        record = loop.beat(NOW)
        assert record["pulsed"] == ["beta"], record["pulsed"]


def test_an_edited_probe_is_reimported_not_served_from_cache():
    """A watch re-armed with a new trigger fires on the new trigger. A cache keyed by path
    alone (not mtime) passes every other tooth and fails this one."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        folder = _device(root, "alpha", {"w.py": _GOOD.format(why="a", fires="False")})
        loop, _, _ = _loop(root, root / "_troubles")
        rec = loop.beat(NOW)
        assert rec["pulses"][0]["fired_count"] == 0
        # A different mtime is what invalidates; write it far enough forward to be unambiguous.
        (folder / "w.py").write_text(_GOOD.format(why="a", fires="True"), encoding="utf-8")
        import os
        os.utime(folder / "w.py", (0, 10_000_000))
        rec = loop.beat(NOW)
        assert len(rec["pulses"][0]["fired"]) == 1, rec["pulses"][0]


def test_a_device_that_will_not_import_is_benched_with_a_ticket():
    """The device-level failure: a bad file cannot reach the beat, and it names itself."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "broken", {"w.py": _BROKEN_IMPORT})
        _device(root, "fine", {"w.py": _GOOD.format(why="fine", fires="False")})
        loop, trouble, _ = _loop(root, root / "_troubles")
        record = loop.beat(NOW)
        assert record["pulsed"] == ["fine"], record["pulsed"]
        live = trouble.live()
        assert len(live) == 1, live
        assert live[0]["id"] == TROUBLE_PREFIX + "broken"
        detail = live[0]["occurrences"][0]
        assert "ModuleNotFoundError" in str(detail["failures"]), detail
        assert detail["failures"][0]["file"].endswith("w.py")


def test_the_heartbeat_survives_every_shape_of_bad_device():
    """CP2: the loop cannot be taken down by a device. Three different lacks, one beat, and
    the healthy device still gets pulsed."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "raises", {"w.py": _BROKEN_IMPORT})
        _device(root, "silent", {"w.py": _NO_PROBE})
        _device(root, "liar", {"w.py": _NOT_A_PROBE})
        _device(root, "fine", {"w.py": _GOOD.format(why="fine", fires="False")})
        loop, trouble, _ = _loop(root, root / "_troubles")
        record = loop.beat(NOW)
        assert record["pulsed"] == ["fine"], record["pulsed"]
        assert {t["id"] for t in trouble.live()} == {
            TROUBLE_PREFIX + n for n in ("raises", "silent", "liar")}


def test_a_benched_device_is_not_even_imported_again():
    """'A failing one wont be retried until its trouble ticket is cleared.' Counted at the
    IMPORT, not at the pulse: a loop that re-imports a known-broken module every second is
    retrying it, whatever it does with the result."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "broken", {"w.py": _BROKEN_IMPORT})
        loop, trouble, calls = _loop(root, root / "_troubles")
        loop.beat(NOW)
        after_first = calls["imports"]
        for _ in range(5):
            loop.beat(NOW)
        assert calls["imports"] == after_first, (
            f"benched device was re-imported {calls['imports'] - after_first} more times")


def test_fifty_beats_over_a_broken_device_raise_one_ticket():
    """The damper (trouble.py): attention is spent once. A ticket per beat — or a count
    climbing with the clock — would be a firehose wearing a lane's clothes."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "broken", {"w.py": _BROKEN_IMPORT})
        loop, trouble, _ = _loop(root, root / "_troubles")
        for _ in range(50):
            loop.beat(NOW)
        live = trouble.live()
        assert len(live) == 1, live
        # Benched after the first failure, so the count does NOT climb with the beats — the
        # bench is what rations the retry, and the ticket records the one real occurrence.
        assert live[0]["count"] == 1, live[0]["count"]


def test_only_a_clear_puts_a_benched_device_back_on_the_beat():
    """The loop never un-benches itself — not on a timeout, not because a later pass would
    have succeeded. Clearing is the recipient's act alone (trouble.py)."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        folder = _device(root, "broken", {"w.py": _BROKEN_IMPORT})
        loop, trouble, _ = _loop(root, root / "_troubles")
        loop.beat(NOW)
        assert loop.subscribers == []
        # The fix lands, but the ticket still stands: the device stays off the beat.
        (folder / "w.py").write_text(_GOOD.format(why="fixed", fires="False"), encoding="utf-8")
        loop.beat(NOW)
        assert loop.subscribers == [], "a fix without a clear must not un-bench"
        trouble.clear(TROUBLE_PREFIX + "broken", by="cc",
                      what_changed="the import was fixed")
        loop.beat(NOW)
        assert loop.subscribers == ["broken"], loop.subscribers


def test_a_clear_is_seen_even_though_it_never_touches_the_directory():
    """THE TOOTH THAT KILLED THE FIRST BENCH GATE, kept sharp by asserting the hard case.

    ``trouble.py`` clears a ticket by rewriting its file in place — no temp file, no rename
    — so the trouble DIRECTORY's mtime does not move. A refresh gated on that mtime is blind
    to the one event it exists to catch, and a benched device stays benched forever while
    every surface reports a healthy beat. This tooth measures the directory's mtime across
    the clear and REQUIRES it to be unchanged, so the gate cannot pass here by accident on
    some future filesystem that happens to bump it."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "broken", {"w.py": _BROKEN_IMPORT})
        troubles = root / "_troubles"
        loop, trouble, _ = _loop(root, troubles)
        loop.beat(NOW)
        loop.beat(NOW)
        assert trouble.live()[0]["count"] == 1
        before = troubles.stat().st_mtime
        # ``cc`` is the notified recipient (trouble.DEFAULT_RECIPIENTS) — and only a notified
        # recipient's clear takes a ticket off live(). Clearing as anyone else leaves it
        # partially_cleared and still LIVE, which is the lane working as designed.
        trouble.clear(TROUBLE_PREFIX + "broken", by="cc", what_changed="fixed the import")
        assert troubles.stat().st_mtime == before, (
            "the premise no longer holds: this clear DID move the directory's mtime, so this "
            "tooth is no longer measuring the hard case — re-derive the gate")
        # The probe file is STILL broken, so the proof of 'the clear was seen' is that the
        # device got RETRIED and failed again. The lane records a post-clear recurrence as a
        # FRESH ticket carrying ``recurred_after_clear`` — deliberately not a bumped count,
        # so 'this fix did not hold' cannot hide inside a running total (trouble.py). A gate
        # blind to the clear never retries, so that field is never set.
        loop.beat(NOW)
        back = trouble.live()[0]
        assert back["recurred_after_clear"] is not None, back
        assert back["recurred_after_clear"]["what_changed"] == "fixed the import", back
        assert back["prior_attempts"] == 1, back


def test_a_hand_subscribed_shim_is_not_double_pulsed_by_discovery():
    """One device, one shim. A real shim (the web server registers two) must not be shadowed
    by a discovered one, or every probe fires twice per beat."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "alpha", {"w.py": _GOOD.format(why="a", fires="False")})
        loop, _, _ = _loop(root, root / "_troubles")

        class HandShim:
            device_id = "alpha"
            pulses = 0

            def on_pulse(self, now, ctx):
                HandShim.pulses += 1
                return {"device": "alpha", "fired": [], "fired_count": 0, "held": []}

        loop.subscribe(HandShim())
        record = loop.beat(NOW)
        assert record["pulsed"] == ["alpha"], record["pulsed"]
        assert HandShim.pulses == 1


def test_the_real_tree_discovers_its_devices():
    """Not a fixture: the actual repo. A discovery that only works on a synthetic tree is a
    discovery that has never met the system it is for."""
    found = device_folders()
    ids = {d for d, _ in found}
    assert {"librarian", "harbor_master", "base"} <= ids, sorted(ids)


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
    print("green — the roster is disk, the bench holds, and only a clear releases it")
