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

    python3 cairn/devices/ground_loop/proofs/test_discovery.py     # exit 0 = green
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.ground_loop.discovery import ProbeCache, discover, device_folders  # noqa: E402
from cairn.devices.ground_loop.loop import (  # noqa: E402
    SELF_TROUBLE, TROUBLE_PREFIX, GroundLoopDevice)
from cairn.devices.trouble.trouble import TroubleDevice  # noqa: E402

NOW = datetime(2026, 8, 11, 12, 0, tzinfo=timezone.utc)

_GOOD = '''
from cairn.tools.base.probe import Probe
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


class _RecordingBus:
    """The consumer end. The falsifier does not say 'the probe is loadable' — it says the
    watch REACHES ITS CONSUMER after the staleness is detected, and with no bus every fire
    records ``unwired`` and delivers to nobody. So the tooth needs somewhere for the poke to
    actually land, or it proves the weaker claim and reads as if it proved the stronger."""

    def __init__(self) -> None:
        self.posted: list[dict] = []

    def post(self, sender, to, channel, **kw):
        # ``id`` is what the shim reads back off the envelope to record the delivery; a fake
        # bus that omits it makes every fire read ``refused`` and the tooth passes for the
        # wrong reason in the other direction.
        envelope = {"id": f"env-{len(self.posted)}", "sender": sender, "to": to,
                    "channel": channel, **kw}
        self.posted.append(envelope)
        return envelope


def _loop(root: Path, trouble_root: Path, staleness=None, bus=None):
    """A loop wired to a temp tree and a temp trouble lane — the same injection the resident
    runner does with the real world, with the folder read counted so the bench can be measured
    at the IMPORT rather than at the pulse.

    ``staleness`` is injected for the same reason ``discover`` is: the predicate's own teeth
    live in ``test_staleness.py`` and construct real drift in a real interpreter, so what the
    benching teeth need here is the ANSWER, not a second reproduction of the condition. A
    proof that had to move a file out from under this process to test the bench would be
    testing two things and proving neither."""
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
    return (GroundLoopDevice(discover=discoverer, trouble=trouble, staleness=staleness,
                             bus=bus),
            trouble, calls)


def _stale(*modules):
    """A staleness answer in the shape ``module_drift`` returns. Named generically on
    purpose: the ticket's falsifier clause (3) refuses a fix that recognises this outage by
    the symbols that happened to move in it (``Probe``, ``common_shape_record``), because the
    next rename would produce a third face and the loop would blame a device again."""
    return lambda: [{"module": m, "evidence": "VANISHED", "file": f"/gone/{m}.py",
                     "detail": "fixture drift"} for m in modules]


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


# --- THE PAIR THAT MUST PROVE APART ----------------------------------------
#
# Ticket the-loop-names-its-own-staleness-instead-of-benching-a-device. The SAME broken
# folder meets the loop twice; the only difference is whether the process holds code that
# has drifted out from under it. If both teeth cannot be green at once, the predicate is not
# what decides the bench — and a build where staleness is detected but the device is benched
# anyway is this ticket's third hollow pass: the record gets prettier and the outage is
# exactly where it was.

def test_a_stale_process_does_not_bench_the_device_and_its_healthy_probe_still_fires():
    """THE TOOTH THAT ENDS THE OUTAGE, and note WHICH probe it is about.

    Benching is per-DEVICE while failures are per-FILE, so one unloadable probe took its
    whole folder down with it — that is how twenty-two probes went dark behind fifteen
    devices. Under staleness the device stays on the roster and the probe that loads fine
    still fires, which is the falsifier's requirement that a watch reach its consumer AFTER
    the staleness is detected."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "mixed", {"broke.py": _BROKEN_IMPORT,
                                "works.py": _GOOD.format(why="still armed", fires="True")})
        bus = _RecordingBus()
        loop, trouble, _ = _loop(root, root / "_troubles",
                                 staleness=_stale("some.module.that.moved"), bus=bus)
        record = loop.beat(NOW)

        assert record["pulsed"] == ["mixed"], record["pulsed"]
        assert not [t for t in trouble.live()
                    if t["id"] == TROUBLE_PREFIX + "mixed"], trouble.live()
        pulse = record["pulses"][0]
        assert pulse["fired_count"] == 1, pulse          # ``ok``, not merely attempted
        assert [p["to"] for p in bus.posted] == ["harbor_master"], bus.posted


def test_the_same_broken_folder_is_benched_when_the_process_is_not_stale():
    """THE PARTNER. Identical fixture, staleness absent — and the bench must still bite.

    A fix that stopped benching outright would pass the tooth above and leave the loop unable
    to hold out a genuinely broken device, which is Akien's 2026-08-11 ruling. The predicate
    has to be the thing that decides, and the only way to show that is to change nothing else
    and watch the verdict flip."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "mixed", {"broke.py": _BROKEN_IMPORT,
                                "works.py": _GOOD.format(why="still armed", fires="True")})
        loop, trouble, _ = _loop(root, root / "_troubles", staleness=lambda: [])
        record = loop.beat(NOW)

        assert record["pulsed"] == [], record["pulsed"]
        assert [t["id"] for t in trouble.live()] == [TROUBLE_PREFIX + "mixed"], trouble.live()


def test_the_real_predicate_is_what_the_loop_actually_asks():
    """THE THIRD LEG OF THE PAIR, added 2026-08-18 (ticket staleness-is-about-this-process-
    not-about-disk), and it exists because the two teeth above CANNOT catch a broken
    predicate — by design.

    Both of them inject the ANSWER (``_stale(...)`` / ``lambda: []``), which is right for
    what they measure: the loop's branch, held apart from the reproduction of real drift. But
    that isolation is also a seam, and the seam is where this ticket's defect lived — the
    predicate went blind on 2026-08-18 while every tooth in this file stayed green, because
    no tooth here ever asked the real one anything. Injection proves the branch; only the
    default proves the WIRING, and the diagnostic for 'armed by hand or actually wired' is
    always to CALL IT.

    So: no ``staleness=`` argument at all, a healthy process, a genuinely broken device. The
    real predicate must answer 'nothing drifted' and the bench must bite. A predicate that
    over-detects — the cheapest wrong implementation, and the direction a content comparison
    could plausibly fail — would unblame everybody forever and this tooth would red."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "mixed", {"broke.py": _BROKEN_IMPORT,
                                "works.py": _GOOD.format(why="still armed", fires="True")})
        loop, trouble, _ = _loop(root, root / "_troubles")     # THE DEFAULT PREDICATE
        record = loop.beat(NOW)

        assert record["pulsed"] == [], record["pulsed"]
        assert [t["id"] for t in trouble.live()] == [TROUBLE_PREFIX + "mixed"], trouble.live()


def test_a_stale_loop_raises_its_trouble_against_ITSELF():
    """The loop is the one party it may make claims about (Law 6). For 29 hours it made a
    claim about fifteen devices instead, and every human reader — me, twice — believed it."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "mixed", {"broke.py": _BROKEN_IMPORT})
        loop, trouble, _ = _loop(root, root / "_troubles",
                                 staleness=_stale("some.module.that.moved"))
        loop.beat(NOW)
        live = trouble.live()
        assert [t["id"] for t in live] == [SELF_TROUBLE], live
        detail = live[0]["occurrences"][0]
        assert detail["drifted"][0]["module"] == "some.module.that.moved", detail


def test_the_self_trouble_does_not_bench_a_phantom_device():
    """THE TRAP IN THE EXISTING CODE, and it is one identifier wide. ``_refresh_bench`` turns
    every live ticket whose id starts with ``TROUBLE_PREFIX`` into a benched device by
    STRIPPING the prefix — so a self-trouble named ``ground-loop-device-ground_loop`` would
    hold out a device that does not exist, forever, and the loop would have benched itself
    while reporting that it had not."""
    assert not SELF_TROUBLE.startswith(TROUBLE_PREFIX), SELF_TROUBLE
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "mixed", {"broke.py": _BROKEN_IMPORT,
                                "works.py": _GOOD.format(why="armed", fires="True")})
        loop, _, _ = _loop(root, root / "_troubles",
                           staleness=_stale("some.module.that.moved"))
        loop.beat(NOW)
        loop.beat(NOW)                       # the second beat re-reads the bench from the lane
        assert loop._benched == {}, loop._benched
        assert loop.beat(NOW)["pulsed"] == ["mixed"]


def test_staleness_does_not_silence_the_failures_it_declines_to_bench_on():
    """Law 7 — loud at diagnostic surfaces. Declining to blame the device must not lose the
    import errors themselves: they are the evidence, and a reader who cannot see them is back
    to guessing. They ride the loop's own trouble, where they belong."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "mixed", {"broke.py": _BROKEN_IMPORT})
        loop, trouble, _ = _loop(root, root / "_troubles",
                                 staleness=_stale("some.module.that.moved"))
        loop.beat(NOW)
        detail = trouble.live()[0]["occurrences"][0]
        blob = str(detail)
        assert "ModuleNotFoundError" in blob, detail
        assert "mixed" in blob, detail


def test_fifty_stale_beats_raise_one_self_trouble():
    """The damper again, on the new lane. A staleness that persists is one condition, not
    fifty — and a loop that reports it every second is a firehose wearing a lane's clothes."""
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        _device(root, "mixed", {"broke.py": _BROKEN_IMPORT})
        loop, trouble, _ = _loop(root, root / "_troubles",
                                 staleness=_stale("some.module.that.moved"))
        for _ in range(50):
            loop.beat(NOW)
        live = trouble.live()
        assert len(live) == 1 and live[0]["id"] == SELF_TROUBLE, live


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
