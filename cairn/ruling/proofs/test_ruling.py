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
  - A CONFIRMATION CARRIES ITS OWN SOURCE. ``confirm`` refuses an empty evidence string and
    records his words verbatim beside the flag. Found the first time the verb was used for
    real: Akien typed the confirm command into the session rather than a shell, so the act
    was his and the keystroke was mine, and a bare ``confirmed: true`` could not tell those
    apart — this gate's own defect, one layer up.
  - THE OLDER NARRATIVE DECISIONS ARE NOT EATEN. ``kind: "decision"`` records in the same
    store are skipped, not migrated and not verified. A scanner that assumed the store was
    all its own trips this.
  - NON-VACUITY: a correct packet over a correct world is GREEN. Without this every tooth
    above could be passing because the gate reds unconditionally.
  - THE RESIDUE MEASUREMENT STILL RUNS. Filed edge (b)'s falsifier is re-runnable, so the
    28.5% cited in CLAUDE.md cannot decay into folklore. It asserts the INSTRUMENT, never
    the value — the corpus grows, and pinning a legitimately-moving number turns a normal
    day into a spurious red.
  - THE HOOK NEVER WEDGES A TURN and names what is open. Exit 0 with a systemMessage
    carrying the ruling's id; silent when nothing is red.
  - RETIREMENT NEVER TOUCHES THE RETIRED (grown 2026-08-02 against the first
    superseded ruling, as filed edge (d) predicted): ``supersede`` stamps the
    confirmed successor and leaves the misfiled packet byte-identical; the retired
    packet leaves the hook but stays on disk and stays red under ``verify``; an
    unsourced, unconfirmed, doubled, or retired-by-the-retired supersession is
    refused with every reason at once; an unrelated red is not silenced.

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


def _git_world(d: str) -> str:
    """``_world`` with the code root under real git, one commit deep. The instrument
    ``as_of`` uses is git itself, so the proof uses git itself — a stub would be proving
    the stub."""
    _world(d)
    code = os.path.join(d, "cairn")
    for cmd in (["init", "-q"], ["config", "user.email", "p@proof"],
                ["config", "user.name", "proof"], ["add", "-A"],
                ["commit", "-qm", "before the ruling"]):
        subprocess.run(["git", "-C", code, *cmd], check=True, capture_output=True)
    return subprocess.run(["git", "-C", code, "rev-parse", "HEAD"],
                          capture_output=True, text=True, check=True).stdout.strip()


def test_a_ruling_recorded_after_its_own_work_can_still_go_green():
    """THE 2026-08-06 FINDING. Akien rules, the work lands, the packet gets written later
    — and the gate had no green path for that, because the baseline was the FILING DATE.
    With as_of the baseline is the commit he ruled against, so the same disk that read
    UNTOUCHED reads conformed."""
    with tempfile.TemporaryDirectory() as d:
        before = _git_world(d)
        conformer = "cairn/cairn/compiler_thing/compiler.py"
        Path(d, conformer).write_text("# conformed, hours before the packet was written\n")

        ruling.open_ruling(_packet(id="2026-08-01-no-as-of", date="2026-08-01",
                                   what_dies=[], what_conforms=[conformer]), d)
        no_as_of = ruling.verify([r for r in ruling.load_all(d)
                                  if r["id"] == "2026-08-01-no-as-of"][0], d)
        assert any("UNTOUCHED" in f for f in no_as_of["failures"]), (
            "PRECONDITION: measured against intake, already-done work reads UNTOUCHED "
            "forever — the defect this field exists to fix")

        ruling.open_ruling(_packet(id="2026-08-02-with-as-of", date="2026-08-02",
                                   what_dies=[], what_conforms=[conformer],
                                   as_of={"cairn": before}), d)
        record = [r for r in ruling.load_all(d) if r["id"] == "2026-08-02-with-as-of"][0]
        assert record["conforms_fingerprint"][conformer] != ruling.fingerprint(
            os.path.join(d, conformer)), (
            "the baseline is the file AS HE RULED, measured by git — not the disk now")
        ruling.confirm("2026-08-02-with-as-of", "yes, that is what i said", d)
        assert ruling.verify(record | {"confirmed": True}, d)["green"], (
            "work done BEFORE the paperwork is still work done; the gate must be able "
            "to say so")


def test_as_of_cannot_conform_a_file_that_did_not_exist_then():
    with tempfile.TemporaryDirectory() as d:
        before = _git_world(d)
        newborn = "cairn/cairn/compiler_thing/brand_new.py"
        Path(d, newborn).write_text("# written after the ruling\n")
        try:
            ruling.open_ruling(_packet(what_dies=[], what_conforms=[newborn],
                                       as_of={"cairn": before}), d)
        except ValueError as exc:
            assert "does not resolve" in str(exc), exc
        else:
            raise AssertionError("a file that did not exist when he ruled is a new "
                                 "build, not a conformance — and an unresolvable "
                                 "baseline would fingerprint nothing and pass")


def test_a_conformer_with_no_baseline_is_red_not_green():
    """The weakest check must not wear the strongest verdict. A hand-edit that moves a
    path into what_conforms leaves it with no fingerprint, and `prints.get(rel) == …`
    used to make that MISSING baseline read as a passed check."""
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        ruling.open_ruling(_packet(), d)
        ruling.confirm("2026-07-31-model-json-is-retired", "yes", d)
        os.remove(os.path.join(d, "CairnCommons/intentions-congruency-lab/_model.json"))
        record = ruling.load_all(d)[0]
        record["what_conforms"] = record["what_conforms"] + ["cairn/CLAUDE.md"]
        Path(d, "cairn", "CLAUDE.md").write_text("# smuggled in by hand\n")

        verdict = ruling.verify(record, d)
        assert any("UNMEASURED" in f and "CLAUDE.md" in f for f in verdict["failures"]), (
            f"never measured is not green; got {verdict['failures']}")


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
        ruling.confirm("2026-07-31-model-json-is-retired", "yes, do that", d)

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


def test_a_confirmation_carries_its_own_source():
    """The defect found the first time the verb was used for real, 2026-07-31.

    Akien typed `cairn ruling confirm <id>` into the session rather than into a shell, so
    the act was genuinely his and the hand on the keyboard was mine — and a bare
    ``confirmed: true`` could not tell those apart. That is this component's own defect
    one layer up: a confirmation with no written source, reconstructible only from whoever
    ran the command.
    """
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        ruling.open_ruling(_packet(), d)

        for empty in ("", "   ", None):
            try:
                ruling.confirm("2026-07-31-model-json-is-retired", empty, d)
            except ValueError as exc:
                assert "EVIDENCE" in str(exc), exc
            else:
                raise AssertionError(
                    f"confirm({empty!r}) must RAISE — an unsourced confirmation is the "
                    "defect this gate exists to fix, wearing the gate's own clothes")

        ruling.confirm("2026-07-31-model-json-is-retired", "  yes, do that  ", d)
        record = ruling.load_all(d)[0]
        assert record["confirmed"] is True
        assert record["confirmation_verbatim"] == "yes, do that", record
        assert record["confirmed_by"] == "Akien", (
            "who confirmed and what they said are SEPARATE facts — the ruler's name comes "
            f"from the packet, the words from the act; got {record}")


def test_an_untouched_conformer_is_red():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        ruling.open_ruling(_packet(), d)
        ruling.confirm("2026-07-31-model-json-is-retired", "yes, do that", d)
        os.remove(os.path.join(d, "CairnCommons/intentions-congruency-lab/_model.json"))

        verdict = ruling.verify(ruling.load_all(d)[0], d)
        assert any("UNTOUCHED" in f for f in verdict["failures"]), (
            "the thing that was supposed to change is byte-identical to intake — the "
            f"ruling was half-obeyed and that is not green; got {verdict}")


def test_a_conformer_deleted_by_mistake_is_red():
    with tempfile.TemporaryDirectory() as d:
        _world(d)
        ruling.open_ruling(_packet(), d)
        ruling.confirm("2026-07-31-model-json-is-retired", "yes, do that", d)
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


def test_the_residue_measurement_still_runs():
    """Filed edge (b)'s falsifier is re-runnable, so its number cannot become folklore.

    A rate cited in CLAUDE.md whose script was deleted is a measurement that has to be
    re-derived to be trusted — a Law 1 defect, and exactly how a loose number gets loose.
    This does not assert the 28.5%: the corpus grows, so pinning the value would be
    pinning a legitimately-moving number. It asserts the instrument still works.
    """
    from cairn.ruling import corpus

    with tempfile.TemporaryDirectory() as d:
        rows = [
            {"type": "user", "message": {"content": "no, that's wrong"}},        # negate
            {"type": "user", "message": {"content": "what does the compiler do?"}},
            {"type": "user", "message": {"content": "<system-reminder>x</system-reminder>"}},
            {"type": "assistant", "message": {"content": [{"type": "text", "text": "stop"}]}},
        ]
        Path(d, "t.jsonl").write_text("\n".join(json.dumps(r) for r in rows))
        r = corpus.measure(os.path.join(d, "*.jsonl"))

        assert r["prompts"] == 2, (
            f"harness lines are not Akien talking, and counting them would inflate the "
            f"denominator in the direction that flatters the hook; got {r}")
        assert r["any"] == 1 and r["by_tier"]["negate"] == 1, r
        assert r["rate"] == 0.5, r


def _misfile_world(d: str) -> tuple[str, str]:
    """The 2026-08-02 scenario, replayed: a confirmed packet that misfiled a living
    file under ``what_dies`` (red forever, hand-edit forbidden), and its confirmed,
    conforming successor. Returns (misfiled_id, successor_id)."""
    _world(d)
    ruling.open_ruling(_packet(), d)
    ruling.confirm("2026-07-31-model-json-is-retired", "i confirm all that", d)
    # the misfiled packet is now RED: _model.json was "ruled dead" and is on disk.
    ruling.open_ruling(_packet(
        id="2026-08-01-the-refile", date="2026-08-01", what_dies=[],
        what_conforms=["cairn/cairn/compiler_thing/compiler.py"]), d)
    Path(d, "cairn/cairn/compiler_thing/compiler.py").write_text("# conformed\n")
    ruling.confirm("2026-08-01-the-refile", "i confirm the refile", d)
    return "2026-07-31-model-json-is-retired", "2026-08-01-the-refile"


def test_supersede_refuses_with_every_reason():
    with tempfile.TemporaryDirectory() as d:
        old, new = _misfile_world(d)

        for empty in ("", "   ", None):
            try:
                ruling.supersede(old, new, empty, d)
            except ValueError as exc:
                assert "EVIDENCE" in str(exc), exc
            else:
                raise AssertionError("an unsourced retirement is the confirm defect "
                                     "one layer up and must RAISE")

        try:
            ruling.supersede("2026-01-01-nope", "2026-01-01-nope", "words", d)
        except ValueError as exc:
            msg = str(exc)
            assert "no such ruling to retire" in msg and "cannot supersede itself" in msg, (
                f"EVERY refusal on the first pass, not twenty questions; got {msg}")
        else:
            raise AssertionError("unknown ids and self-supersession must refuse")

        # an unconfirmed successor cannot retire a confirmed act
        ruling.open_ruling(_packet(
            id="2026-08-01-my-guess", date="2026-08-01", what_dies=[],
            what_conforms=["cairn/cairn/compiler_thing/compiler.py"]), d)
        try:
            ruling.supersede(old, "2026-08-01-my-guess", "trust me", d)
        except ValueError as exc:
            assert "UNCONFIRMED" in str(exc), exc
        else:
            raise AssertionError("my unconfirmed guess outvoted his signature")


def test_supersede_writes_only_to_the_superseding_record():
    """The ticket's falsifier, clause (a): retiring must not edit the confirmed record."""
    with tempfile.TemporaryDirectory() as d:
        old, new = _misfile_world(d)
        old_path = os.path.join(ruling.store_dir(d), f"{old}.json")
        before = Path(old_path).read_bytes()

        ruling.supersede(old, new, "  he said the file was never meant to die  ", d)

        assert Path(old_path).read_bytes() == before, (
            "the retired packet must stay BYTE-IDENTICAL — an in-place edit of a "
            "confirmed record erases his act, which is the thing Law 7 forbids")
        successor = [r for r in ruling.load_all(d) if r["id"] == new][0]
        assert successor["supersedes"] == [
            {"id": old, "evidence": "he said the file was never meant to die"}], (
            "the act lands on the SUCCESSOR, with its evidence, verbatim and stripped")


def test_a_superseded_ruling_leaves_the_hook_but_not_the_disk():
    """The ticket's falsifier, clause (b): the hook stops naming it — while verify,
    the record-local verdict, stays honestly red and the file stays on disk."""
    with tempfile.TemporaryDirectory() as d:
        old, new = _misfile_world(d)
        assert [v["id"] for v in ruling.open_rulings(d)] == [old], (
            "PRECONDITION: before the act, the misfiled packet is the one open red")

        ruling.supersede(old, new, "misfiled what_dies; the successor carries it", d)

        assert ruling.open_rulings(d) == [], (
            "a retired packet is no longer anyone's to act on — this red printing "
            "every turn forever is exactly the noise the ticket names")
        old_record = [r for r in ruling.load_all(d) if r["id"] == old][0]
        assert not ruling.verify(old_record, d)["green"], (
            "verify stays record-local and honestly red — supersession changes who "
            "must ACT, never what the record says")
        assert os.path.exists(os.path.join(ruling.store_dir(d), f"{old}.json")), (
            "retired is not deleted; the record of truth is permanent")


def test_one_successor_retires_many_without_erasing_the_first_act():
    """THE 2026-08-06 MEASUREMENT, frozen as a tooth. ``supersedes`` was one slot, so
    retiring a second packet by the same successor overwrote the first — old-a quietly
    came back onto the open board and its evidence was gone, with no error raised.

    The scenario is not contrived: a successor must be CONFIRMED to retire anything, so
    a packet rescoped before Akien signs the original leaves BOTH open, and one corrected
    reading is the only thing that can answer for the pair. That is the exact position
    the two file-path rulings were in when this was found."""
    with tempfile.TemporaryDirectory() as d:
        old_a, new = _misfile_world(d)
        ruling.open_ruling(_packet(id="2026-07-31-the-rescope", date="2026-07-31"), d)
        ruling.confirm("2026-07-31-the-rescope", "i confirm the rescope too", d)
        old_b = "2026-07-31-the-rescope"

        ruling.supersede(old_a, new, "the original misfiled what_dies", d)
        ruling.supersede(old_b, new, "the rescope carried the same misreading", d)

        retired = ruling.retired_ids(ruling.load_all(d))
        assert retired == {old_a, old_b}, (
            f"a second supersession must not un-retire the first; retired={retired}")
        assert ruling.open_rulings(d) == [], (
            "both misfiled packets are answered for — neither is anyone's to act on")
        successor = [r for r in ruling.load_all(d) if r["id"] == new][0]
        assert successor["supersedes"] == [
            {"id": old_a, "evidence": "the original misfiled what_dies"},
            {"id": old_b, "evidence": "the rescope carried the same misreading"}], (
            "BOTH acts survive, in the order they happened — a retirement whose evidence "
            "is silently dropped is a record of truth losing an act (Law 7)")


def test_the_single_slot_shape_still_retires():
    """Two CONFIRMED records on disk predate the list and are deliberately NOT rewritten
    — an in-place edit of a confirmed record is the act this module refuses. So the
    normaliser, not a migration, is what keeps them retiring what they retired."""
    with tempfile.TemporaryDirectory() as d:
        old, new = _misfile_world(d)
        path = os.path.join(ruling.store_dir(d), f"{new}.json")
        record = json.loads(Path(path).read_text())
        record["supersedes"] = {"id": old, "evidence": "written the old way"}
        Path(path).write_text(json.dumps(record, indent=2))

        assert ruling.retired_ids(ruling.load_all(d)) == {old}, (
            "a legacy single-slot supersession must still retire its packet — a reader "
            "that only knows the new shape resurrects every already-answered red")
        assert ruling._supersessions({"supersedes": "nonsense"}) == [], (
            "an unrecognisable field reads as NO supersession — a malformed value must "
            "never silently retire a live packet")


def test_a_retired_ruling_answers_for_nothing():
    with tempfile.TemporaryDirectory() as d:
        old, new = _misfile_world(d)
        ruling.supersede(old, new, "misfiled; successor carries it", d)

        try:
            ruling.supersede(old, new, "again, differently", d)
        except ValueError as exc:
            assert "already retired" in str(exc), exc
        else:
            raise AssertionError("a second supersession would silently overwrite the "
                                 "first act's evidence")

        ruling.open_ruling(_packet(
            id="2026-08-01-a-third", date="2026-08-01", what_dies=[],
            what_conforms=["cairn/cairn/compiler_thing/compiler.py"]), d)
        ruling.confirm("2026-08-01-a-third", "yes", d)
        try:
            ruling.supersede("2026-08-01-a-third", old, "retire by the retired", d)
        except ValueError as exc:
            assert "itself retired" in str(exc), exc
        else:
            raise AssertionError("a retired ruling cannot retire another — that is "
                                 "the two-act mutual-silencing hole")


def test_supersession_does_not_silence_an_unrelated_red():
    with tempfile.TemporaryDirectory() as d:
        old, new = _misfile_world(d)
        ruling.open_ruling(_packet(
            id="2026-08-01-still-unconfirmed", date="2026-08-01", what_dies=[],
            what_conforms=["cairn/cairn/compiler_thing/compiler.py"]), d)

        ruling.supersede(old, new, "misfiled; successor carries it", d)

        assert [v["id"] for v in ruling.open_rulings(d)] == ["2026-08-01-still-unconfirmed"], (
            "retirement is one packet's, not a mute button — the unrelated red stays")


def test_the_hook_goes_quiet_after_a_cli_supersession():
    """Clause (b) at the real surface: the verb through the CLI, then --hook silent."""
    with tempfile.TemporaryDirectory() as d:
        old, new = _misfile_world(d)
        env = {**os.environ, "CAIRN_ROOTS_PARENT": d, "PYTHONPATH": str(_REPO_ROOT)}
        run = lambda *args: subprocess.run(
            [sys.executable, "-m", "cairn.ruling.cli", *args], input="{}",
            capture_output=True, text=True, cwd=str(_REPO_ROOT), env=env)

        loud = run("--hook")
        assert old in loud.stdout, f"PRECONDITION: the hook names the misfiled red; {loud.stdout!r}"

        act = run("supersede", old, new, "misfiled", "what_dies;", "successor", "carries", "it")
        assert act.returncode == 0, act.stderr

        quiet = run("--hook")
        assert quiet.returncode == 0 and quiet.stdout.strip() == "", (
            f"the retired packet must leave the hook; got {quiet.stdout!r}")


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
        test_a_ruling_recorded_after_its_own_work_can_still_go_green,
        test_as_of_cannot_conform_a_file_that_did_not_exist_then,
        test_a_conformer_with_no_baseline_is_red_not_green,
        test_unconfirmed_is_red_over_a_perfect_tree,
        test_the_day_this_was_built,
        test_a_confirmation_carries_its_own_source,
        test_an_untouched_conformer_is_red,
        test_a_conformer_deleted_by_mistake_is_red,
        test_the_older_narrative_decisions_are_not_eaten,
        test_absolute_paths_are_refused,
        test_the_residue_measurement_still_runs,
        test_supersede_refuses_with_every_reason,
        test_supersede_writes_only_to_the_superseding_record,
        test_a_superseded_ruling_leaves_the_hook_but_not_the_disk,
        test_one_successor_retires_many_without_erasing_the_first_act,
        test_the_single_slot_shape_still_retires,
        test_a_retired_ruling_answers_for_nothing,
        test_supersession_does_not_silence_an_unrelated_red,
        test_the_hook_goes_quiet_after_a_cli_supersession,
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
