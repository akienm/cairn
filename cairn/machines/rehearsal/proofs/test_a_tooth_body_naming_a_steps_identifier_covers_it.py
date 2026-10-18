"""A voyage step is covered by the tooth whose BODY uses the code identifier the step names.

Ticket 870d26e0da47 (trouble divergence-matcher-misses-a-step-a-tooth-covers). Measured
2026-10-14 on d6eb399ab6ad: the divergence after PROVED listed the step "deleted _ensure_loop
... from the librarian launcher" as unproved, though test_check_lives_in_the_base_only names
"_ensure_loop" in its body and reds on the old launcher. The matcher read only tooth NAMES.
Measured 2026-10-18 by CC over the 153 clean records carrying a divergence: matching body
tokens as a bag over-matches (0539e85f8b2d went 16 -> 0 on 'akien', 'cairn', 'py'); matching a
shared snake_case identifier, minus the ones most steps or most teeth carry, covers both
d6eb _ensure_loop steps and leaves its five bookkeeping steps unproved (857 -> 808 overall).

Also measured that day: teeth_of read 'def test_' lines inside fixture strings as teeth (8
phantom teeth in the census). A tooth is a top-level function.

Run:  cd ~/dev/src/cairn && bin/cairn test cairn/machines/rehearsal/proofs/test_a_tooth_body_naming_a_steps_identifier_covers_it.py
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO))

from cairn.machines.rehearsal import rehearsal as R          # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir           # noqa: E402

PROVES = {"870d26e0da47": {
    "1": "test_a_step_naming_an_identifier_a_tooth_body_uses_is_covered",
    "2": "test_an_identifier_most_steps_carry_covers_nothing",
    "3": "test_a_def_inside_a_fixture_string_is_not_a_tooth",
    "4": "test_a_proof_that_does_not_parse_still_gives_its_teeth_by_name",
}}

LAUNCHER_PROOF = '''\
def test_dead_to_live_one_shim():
    assert "shim" in "the shim starts the loop"

def test_check_lives_in_the_base_only():
    starts = ("-m cairn.devices.ground_loop", "_ensure_loop")
    assert all(s for s in starts)
'''

STEPS = [
    "DONE: cairn 65d7bbe6 deleted _ensure_loop, LOOP_UNIT and the call from the librarian launcher",
    "WATCH: none new; the cast watchme stands as written",
    "A build step: cross BUILDME forward from FIXME naming the proof as proven_by",
]


def _proof(text: str) -> tuple[Path, Path]:
    d = scratch_dir("rehearsal-divergence-testing-")
    p = d / "test_widget.py"
    p.write_text(text)
    return d, p


def test_a_step_naming_an_identifier_a_tooth_body_uses_is_covered():
    d, p = _proof(LAUNCHER_PROOF)
    try:
        div = R.proof_divergence(STEPS, [p])
        assert div["matched"] == [[STEPS[0], "test_check_lives_in_the_base_only"]], div
        assert div["steps_unproved"] == STEPS[1:], div
        assert div["teeth_unforeseen"] == ["test_dead_to_live_one_shim"], div
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_an_identifier_most_steps_carry_covers_nothing():
    """The component's own name rides most steps and most teeth; it says which component,
    not which step, so it links nothing."""
    steps = ["counting_block learns whose hand cleared it",
             "counting_block passes an ask to pulse",
             "COMPONENT is counting_block's module constant"]
    d, p = _proof("def test_1():\n    assert 'counting_block'\n\n"
                  "def test_2():\n    assert 'counting_block'\n\n"
                  "def test_3():\n    assert 'counting_block' and 'clears_error'\n")
    try:
        div = R.proof_divergence(steps, [p])
        assert div["matched"] == [] and div["steps_unproved"] == steps, div
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_a_def_inside_a_fixture_string_is_not_a_tooth():
    d, p = _proof("FIXTURE = '''\ndef test_phantom():\n    pass\n'''\n\n"
                  "def test_real():\n    assert FIXTURE\n")
    try:
        assert R.teeth_of(p) == ["test_real"], R.teeth_of(p)
        assert list(R.teeth_bodies(p)) == ["test_real"], R.teeth_bodies(p)
    finally:
        shutil.rmtree(d, ignore_errors=True)


def test_a_proof_that_does_not_parse_still_gives_its_teeth_by_name():
    d, p = _proof("def test_one():\n    pass\n\ndef test_two(:\n")
    try:
        assert R.teeth_of(p) == ["test_one", "test_two"], R.teeth_of(p)
        assert R.teeth_bodies(p) == {"test_one": "", "test_two": ""}, R.teeth_bodies(p)
    finally:
        shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    fails = 0
    for name in [t for k in PROVES.values() for t in k.values()]:
        try:
            globals()[name]()
            print(f"PASS {name}")
        except Exception as e:  # noqa: BLE001 — every tooth prints, red or green
            fails += 1
            print(f"FAIL {name}: {type(e).__name__}: {e}")
    raise SystemExit(1 if fails else 0)
