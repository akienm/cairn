"""Proof for cairn/ruling — the ruling intake gate.

Teeth a hollow gate could not pass:

  - EVERY REFUSAL ON THE FIRST PASS, never the first one found. A validator that returns
    as soon as it finds a problem makes the author play twenty questions with it — the
    incomplete-diagnostic defect wearing a validator's clothes. A short-circuiting build
    trips this.
  - THE VERBATIM FIELD IS NOT OPTIONAL. A packet holding only my READING of the ruling is
    refused. This is the tooth the whole gate is built around: the reading has to sit next
    to his words or there is nothing to check it against, which is the state the system
    was in all of 2026-07-31.
  - AN INVENTED TARGET IS REFUSED. A ``what_dies`` path that is not on disk at intake is
    either already dead or made up, and a ``what_conforms`` path that is not on disk is a
    new build, not a conformance. A gate that took my word for what exists trips this.
  - THE RECORDER CANNOT SELF-CONFIRM. ``confirmed: true`` at intake is refused, and the
    door stamps ``false`` regardless. A gate whose subject can sign its own reading off has
    removed the only reader it exists for.
  - UNCONFIRMED IS RED EVEN OVER A PERFECT TREE. The one tooth that makes confirmation
    load-bearing rather than decorative. A build that verified the disk and shrugged at the
    signature trips this.
  - THE FINGERPRINTS ARE THE DOOR'S, NOT THE AUTHOR'S. An authored ``conforms_fingerprint``
    is overwritten with a measured one, so ``UNTOUCHED`` cannot be talked around.
  - THE 2026-07-31 REGRESSION, REPLAYED (test_the_day_this_was_built): the exact sequence
    that cost two hours — rule a file dead, kill it (green), then regenerate it — must go
    RED. If this test passes on a build that never notices the file came back, the gate is
    ornamental.
  - THE OLDER NARRATIVE DECISIONS ARE NOT EATEN. ``kind: "decision"`` records in the same
    store are skipped, not migrated and not verified. A scanner that assumed the store was
    all its own trips this.
  - NON-VACUITY: a correct packet over a correct world is GREEN. Without this every tooth
    above could be passing because the gate reds unconditionally.
  - THE HOOK NEVER WEDGES A TURN and names what is open. Exit 0 with a systemMessage
    carrying the ruling's id; silent when nothing is red.

Self-contained (a synthetic two-root world in a temp dir) and self-cleaning: the live
CairnCommons store is never read or written.

    python3 cairn/ruling/proofs/test_ruling.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.ruling import ruling


# ── a synthetic world ─────────────────────────────────────────────────────────

def _world(d: str) -> str:
    """Two roots side by side, mirroring ~/dev/src/: a code repo and the commons."""
    os.makedirs(os.path.join(d, "CairnCommons", "decisions"))
    os.makedirs(os.path.join(d, "CairnCommons", "intentions-congruency-lab"))
    os.makedirs(os.path.join(d, "cairn", "cairn", "compiler_thing"))
    Path(d, "CairnCommons", "intentions-congruency-lab", "_model.json").write_text('{"old": 1}')
    Path(d, "cairn", "cairn", "compiler_thing", "compiler.py").write_text("# writes the model\n")
    return d


def _packet(**over) -> dict:
    p = {
        "id": "2026-07-31-model-json-is-retired",
        "kind": "ruling",
        "date": "2026-07-31",
        "ruled_by": "Akien",
        "recorded_by": "CC",
        "the_ruling_verbatim": ["_model.json is retired."],
        "now_the_spec_says": "The lab holds copies of every intention+why; there is no "
                            "aggregate artifact.",
        "what_dies": ["CairnCommons/intentions-congruency-lab/_model.json"],
        "what_conforms": ["cairn/cairn/compiler_thing/compiler.py"],
    }
    p.update(over)
    return p


# ── the teeth ─────────────────────────────────────────────────────────────────

def test_every_refusal_lands_on_the_first_pass():
    bad = ruling.refusals_shape({"kind": "ruling"})
    missing = [r for r in bad if "missing required field" in r]
    assert len(missing) == len(ruling.REQUIRED) - 1, (
        "a gate reports EVERY missing field at once, not the first — otherwise the author "
        f"plays twenty questions with it; got {bad}")


def test_a_packet_without_his_words_is_refused():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        for value in ([], "he said it was retired"):
            bad = ruling.refusals(_packet(the_ruling_verbatim=value), d)
            assert any("the_ruling_verbatim" in r for r in bad), (
                "a packet holding only my READING is the state the system was already in; "
                f"the verbatim field is what the reading is checked against. got {bad}")


def test_a_padded_reading_is_refused():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        multi = ruling.refusals(_packet(now_the_spec_says="line one\nline two"), d)
        assert any("ONE line" in r for r in multi), multi
        long = ruling.refusals(_packet(now_the_spec_says="x" * (ruling.SPEC_MAX + 1)), d)
        assert any("cap is" in r for r in long), long


def test_an_invented_target_is_refused():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        bad = ruling.refusals(_packet(what_dies=["CairnCommons/no/such/file.json"]), d)
        assert any("does not exist at intake" in r for r in bad), (
            f"a path I made up must not survive intake; got {bad}")

        bad = ruling.refusals(_packet(what_conforms=["cairn/cairn/not_built_yet.py"]), d)
        assert any("new build, not a ruling" in r for r in bad), bad


def test_a_ruling_that_moves_nothing_is_refused():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        bad = ruling.refusals(_packet(what_dies=[], what_conforms=[]), d)
        assert any("BOTH empty" in r for r in bad), bad


def test_a_path_cannot_both_die_and_conform():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        p = "cairn/cairn/compiler_thing/compiler.py"
        bad = ruling.refusals(_packet(what_dies=[p], what_conforms=[p]), d)
        assert any("both die and conform" in r for r in bad), bad


def test_the_recorder_cannot_self_confirm():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        bad = ruling.refusals(_packet(confirmed=True), d)
        assert any("confirmed cannot be true at intake" in r for r in bad), bad

        # …and even a packet that sneaks the field past shape validation is stamped down.
        path = ruling.open_ruling(_packet(), d)
        with open(path, encoding="utf-8") as fh:
            assert json.load(fh)["confirmed"] is False


def test_the_fingerprints_are_measured_not_authored():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        lie = {"cairn/cairn/compiler_thing/compiler.py": "deadbeef"}
        path = ruling.open_ruling(_packet(conforms_fingerprint=lie), d)
        with open(path, encoding="utf-8") as fh:
            record = json.load(fh)
        real = ruling.fingerprint(os.path.join(d, "cairn/cairn/compiler_thing/compiler.py"))
        assert record["conforms_fingerprint"]["cairn/cairn/compiler_thing/compiler.py"] == real, (
            "the door measures the fingerprint itself — an authored one would make "
            "UNTOUCHED trivially talk-around-able")


def test_unconfirmed_is_red_over_a_perfect_tree():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        ruling.open_ruling(_packet(), d)
        os.remove(os.path.join(d, "CairnCommons/intentions-congruency-lab/_model.json"))
        Path(d, "cairn/cairn/compiler_thing/compiler.py").write_text("# copies, no model\n")

        verdict = ruling.verify(ruling.load_all(d)[0], d)
        assert not verdict["green"], "the disk is perfect and the signature is missing"
        assert verdict["failures"] == [f for f in verdict["failures"] if "UNCONFIRMED" in f], (
            f"UNCONFIRMED must be the ONLY failure over a clean tree; got {verdict}")


def test_the_day_this_was_built():
    """The 2026-07-31 regression, replayed: ruled dead, killed, then it came BACK."""
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        ruling.open_ruling(_packet(), d)
        ruling.confirm("2026-07-31-model-json-is-retired", d)

        model = os.path.join(d, "CairnCommons/intentions-congruency-lab/_model.json")
        os.remove(model)
        Path(d, "cairn/cairn/compiler_thing/compiler.py").write_text("# copies, no model\n")
        assert ruling.verify(ruling.load_all(d)[0], d)["green"], (
            "NON-VACUITY: a confirmed ruling over a conforming tree is GREEN — without "
            "this, every red below could be the gate reddening unconditionally")

        # …and now the exact two-hour defect: the retired file is regenerated.
        Path(model).write_text('{"old": 1}')
        verdict = ruling.verify(ruling.load_all(d)[0], d)
        assert not verdict["green"], "a file ruled dead came back and the gate shrugged"
        assert any("STILL ALIVE" in f and "_model.json" in f for f in verdict["failures"]), \
            verdict["failures"]


def test_an_untouched_conformer_is_red():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        ruling.open_ruling(_packet(), d)
        ruling.confirm("2026-07-31-model-json-is-retired", d)
        os.remove(os.path.join(d, "CairnCommons/intentions-congruency-lab/_model.json"))

        verdict = ruling.verify(ruling.load_all(d)[0], d)
        assert any("UNTOUCHED" in f for f in verdict["failures"]), (
            "the thing that was supposed to change is byte-identical to intake — the "
            f"ruling was half-obeyed and that is not green; got {verdict}")


def test_a_conformer_deleted_by_mistake_is_red():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        ruling.open_ruling(_packet(), d)
        ruling.confirm("2026-07-31-model-json-is-retired", d)
        os.remove(os.path.join(d, "CairnCommons/intentions-congruency-lab/_model.json"))
        os.remove(os.path.join(d, "cairn/cairn/compiler_thing/compiler.py"))

        verdict = ruling.verify(ruling.load_all(d)[0], d)
        assert any("VANISHED" in f for f in verdict["failures"]), (
            f"over-obeying a ruling is its own failure, not a green; got {verdict}")


def test_the_older_narrative_decisions_are_not_eaten():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        legacy = os.path.join(d, "CairnCommons", "decisions", "2026-07-30-the-old-one.json")
        Path(legacy).write_text(json.dumps({"id": "2026-07-30-the-old-one", "kind": "decision"}))
        ruling.open_ruling(_packet(), d)

        ids = [r["id"] for r in ruling.load_all(d)]
        assert ids == ["2026-07-31-model-json-is-retired"], (
            f"a kind:decision record is a different artifact with a different job; {ids}")
        assert json.loads(Path(legacy).read_text())["kind"] == "decision", "and it is untouched"


def test_absolute_paths_are_refused():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        bad = ruling.refusals(
            _packet(what_dies=[os.path.join(d, "CairnCommons/intentions-congruency-lab/_model.json")]), d)
        assert any("absolute path" in r for r in bad), (
            f"a packet must survive a clone to another machine; got {bad}")


def test_the_hook_names_what_is_open_and_never_wedges_a_turn():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        env = {**os.environ, "CAIRN_ROOTS_PARENT": d, "PYTHONPATH": str(_REPO_ROOT)}
        run = lambda: subprocess.run(
            [sys.executable, "-m", "cairn.ruling.cli", "--hook"], input="{}",
            capture_output=True, text=True, cwd=str(_REPO_ROOT), env=env)

        quiet = run()
        assert quiet.returncode == 0 and quiet.stdout.strip() == "", (
            f"nothing open, nothing said; got {quiet.stdout!r}")

        ruling.open_ruling(_packet(), d)
        loud = run()
        assert loud.returncode == 0, "a gate that can kill the session is worse than silence"
        msg = json.loads(loud.stdout)["systemMessage"]
        assert "2026-07-31-model-json-is-retired" in msg and "UNCONFIRMED" in msg, (
            f"the receipt names the ruling and its failure, not just 'something is open'; {msg}")


def _main() -> int:
    checks = [
        test_every_refusal_lands_on_the_first_pass,
        test_a_packet_without_his_words_is_refused,
        test_a_padded_reading_is_refused,
        test_an_invented_target_is_refused,
        test_a_ruling_that_moves_nothing_is_refused,
        test_a_path_cannot_both_die_and_conform,
        test_the_recorder_cannot_self_confirm,
        test_the_fingerprints_are_measured_not_authored,
        test_unconfirmed_is_red_over_a_perfect_tree,
        test_the_day_this_was_built,
        test_an_untouched_conformer_is_red,
        test_a_conformer_deleted_by_mistake_is_red,
        test_the_older_narrative_decisions_are_not_eaten,
        test_absolute_paths_are_refused,
        test_the_hook_names_what_is_open_and_never_wedges_a_turn,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — cairn/ruling: a ruling is refused unless it carries HIS WORDS beside my "
          "one-line reading and names real paths; the recorder cannot self-confirm; and a "
          "file ruled dead that comes back is RED (the 2026-07-31 regression, replayed).")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
