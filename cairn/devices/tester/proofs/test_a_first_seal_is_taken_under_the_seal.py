"""Proof for ticket 481221f45884 — a proof's FIRST seal is taken under the seal, not beside it.

THE MEASURED FAILURE THIS EXISTS FOR. ``cairn test <path> --seal`` asked each proof's standing
validation what isolation its seal had been taken at and reproduced that (ticket 4431cf2bc625,
2026-09-09). A proof that had never been sealed had nothing to reproduce, so it ran BARE — and
the record that landed carried ``seal: {verdict: "open"}``. In this device's own vocabulary
``open`` is not a weak seal, it is the ABSENCE of a reading: isolation.py says "not asked for;
the route is open by construction, said so". So the single moment a proof entered proven-space
was the one moment nothing measured whether it could reach the network, and the validation
wrote that absence down as though it were a measurement. Measured 2026-09-10 across both roots:
218 validation files, 158 carrying ``sealed``, 54 carrying ``open``, 6 carrying no seal key.

The second half is the surface. The closing line of a sealing run printed one count under the
one word SEALED, so a batch that persisted fifty records of which forty were taken with the
route open reported itself, in the last line on screen, as a sealing run. Law 7: a diagnostic
surface may not state a convenient shape in place of the measurement. Law 8: a false green is
worse here than a red, because a peer leans on it.

THE AXIS IS "NOTHING STANDS", NOT "THE STANDING RECORD IS WEAK". This proof and ticket
4431cf2bc625's sit on opposite ends of one function and must not be collapsed: a STANDING
``open`` still reproduces as ``none`` (tooth 2 below asserts exactly that, and would red if this
build had overrun the guard instead of sitting beneath it). Only the never-sealed case changed.

Teeth a hollow build could not pass:

  1. A FIRST SEAL LANDS `sealed`, NOT `open`. A fixture proof with no standing validation, driven
     through the real CLI with --seal, lands a record whose evidence.seal.verdict is `sealed`,
     and the per-proof isolation reported for the run is `netns`. Before the build this read
     `open` / `none`.
  2. THE GUARD BENEATH IT IS UNTOUCHED. A proof carrying a standing `open` record still re-runs
     at isolation `none`, and isolation_for_seal still maps the four verdicts the way ticket
     4431cf2bc625 fixed them. A stronger default that overran its own guard would be the same
     class of defect one layer up.
  3. A DIAGNOSTIC RUN IS UNCHANGED. Without --seal nothing is persisted and the isolation stays
     `none`, because there is no record of truth to protect and widening the default would change
     what a plain `cairn test` costs.
  4. THE SUMMARY SPLITS SEALED FROM PERSISTED. Over a mixed batch — one proof with a standing
     `open`, one never sealed — the closing lines report the persisted total and the under-seal
     count separately, and the under-seal count equals the number of landed files whose
     evidence.seal.verdict is `sealed`. Asserted as that INVARIANT, never as a literal count, so
     it keeps biting if the fixture batch grows.
  5. THE UNQUALIFIED WORD `SEALED` NEVER STANDS OVER AN OPEN RECORD. In the same mixed batch, no
     output line begins with the bare word SEALED, and the line naming the persisted count is
     still readable by the neighbouring proof's parser (the em-dash is load-bearing).
  6. THE WATCH PROBE IS ARMED AND CAN FIRE. PROBE is a frozen Probe carrying a carry and an
     enough, it is quiet against the live decision, and it fires the moment the decision is
     reverted to the pre-build answer.
  7. A SEAL CUT INSIDE A SEAL IS INHERITED AND STILL MEASURED. A sealing run started inside an
     already-sealed namespace does not re-cut it — it takes the same bare probe in the namespace
     it inherited. Added mid-voyage, because the stronger default made nested sandboxes the
     ordinary case and they did not work: `--cap-add CAP_NET_ADMIN` came across from UU for a
     Router Cairn never built and was the sole reason bwrap refused to start inside a seal.
  8. THE STRONGER DEFAULT CHANGES ISOLATION, NOT VERDICT. One fixture proof read at `none` and at
     `netns` comes back with the same verdict over the same teeth. This is the ticket's own WRONG
     INTENT clause turned into a tooth: a netns run that reds for a reason unrelated to network
     reach means the ticket bought a stronger default and spent it.
  9. THE ROSTER CARRIES EVERY TOOTH. Housekeeping rather than a clause: the count is derived at
     call time, so a tooth deleted reds here instead of shrinking the proof quietly.

THE RUNNER IS `proof_coverage.print_teeth_main`, NOT A HAND-ROLLED LOOP, and the reason is this
voyage's own measurement. The hand-rolled loop ran the teeth in declaration order and stopped at
the first red, so reverting `cli.py` — which reds the FIRST tooth — made it print no tooth names
at all, and the hollow runner could only report `unreadable`. A proof that dies the moment its
subject is taken away cannot say whether it was checking that subject. Under pytest the same
revert reds five teeth by name in 19 seconds.

Self-cleaning: every tooth writes into a throwaway temp component tree, so no real component's
validations/ is touched. The teeth drive the REAL CLI over REAL fixtures rather than reading the
source, because a structural assertion would stay green over a reverted branch.

    python3 cairn/devices/tester/proofs/test_a_first_seal_is_taken_under_the_seal.py   # exit 0 = green
"""

from __future__ import annotations

import io
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections import Counter
from contextlib import redirect_stdout
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester import cli
from cairn.devices.tester import validation_store as vs
from cairn.devices.tester.isolation import BREACHED, INDETERMINATE, OPEN, SEALED

# WHICH TOOTH ANSWERS WHICH DONE-CLAUSE of ticket 481221f45884, read by
# cairn.tools.proof_coverage without importing this module. One tooth per clause, and the
# clause numbers are the ticket's own `(1) (2) (3)`, so a clause that gains a tooth here and
# loses it in the falsifier reds rather than drifting quietly.
PROVES = {
    "481221f45884": {
        "1": "test_a_first_seal_lands_sealed_not_open",
        "2": "test_the_word_sealed_never_stands_over_an_open_record",
        "3": "test_the_stronger_default_changes_isolation_not_verdict",
    },
}

_FIXTURES = _REPO_ROOT / "cairn" / "devices" / "tester" / "proofs" / "fixtures"
_GREEN_FIXTURE = _FIXTURES / "green_proof.py"


def _tree(tmp: str, *stems: str) -> Path:
    """A throwaway component tree at <tmp>/somecomp/proofs/ holding copies of the green fixture."""
    proofs = Path(tmp) / "somecomp" / "proofs"
    proofs.mkdir(parents=True, exist_ok=True)
    body = _GREEN_FIXTURE.read_text(encoding="utf-8")
    for stem in stems:
        (proofs / f"{stem}.py").write_text(body, encoding="utf-8")
    return proofs


def _landed(tmp: str) -> list[Path]:
    return sorted((Path(tmp) / "somecomp" / "validations").glob("*.json"))


def _seal_of(path: Path) -> str | None:
    rec = json.loads(path.read_text(encoding="utf-8"))[-1]
    return ((rec.get("evidence") or {}).get("seal") or {}).get("verdict")


def _force_standing_open(path: Path) -> None:
    """Rewrite a landed record to carry a standing `open` seal, so the next run has a MEASUREMENT
    to reproduce rather than nothing.

    The chmod is not incidental. The store writes its validations read-only on purpose — a record
    of truth is not casually editable — and a tooth that quietly had write access would be testing
    a world the real one does not have. So the permission is lifted deliberately, inside a scratch
    tree, and put back."""
    mode = path.stat().st_mode
    os.chmod(path, mode | stat.S_IWUSR)
    rec = json.loads(path.read_text(encoding="utf-8"))
    rec[-1]["evidence"]["seal"] = {"verdict": OPEN, "detail": "none: no seal requested"}
    path.write_text(json.dumps(rec, indent=2) + "\n", encoding="utf-8")
    os.chmod(path, mode)


def _run(argv: list[str]) -> str:
    out = io.StringIO()
    with redirect_stdout(out):
        cli.main(argv)
    return out.getvalue()


def test_a_first_seal_lands_sealed_not_open() -> None:
    """The whole ticket in one tooth: nothing stands, --seal is asked for, and the record that
    lands carries a MEASUREMENT rather than the absence of one."""
    with tempfile.TemporaryDirectory() as tmp:
        proofs = _tree(tmp, "test_never_sealed")
        text = _run([str(proofs), "--seal"])

        landed = _landed(tmp)
        assert len(landed) == 1, f"the first seal did not land a validation: {landed}\n{text}"
        seal = _seal_of(landed[0])
        assert seal == SEALED, (
            f"a proof with no standing record sealed as {seal!r} — a first seal taken beside the "
            f"seal writes the ABSENCE of a reading into the one record that admits the proof to "
            f"proven-space (Law 8: a false green is worse than a red):\n{text}")

        assert "isolation netns=1" in text, (
            f"the run did not report netns as the isolation it used:\n{text}")


def test_the_standing_open_guard_is_untouched() -> None:
    """Ticket 4431cf2bc625's end of the same function. A stronger default that overran its own
    guard would be this ticket's defect one layer up, so the opposite end is asserted here too."""
    assert vs.isolation_for_seal(None) is None, (
        "nothing standing must stay None at the mapping — the CLI's default is the caller's to "
        "choose, and folding it in here would hide this ticket's change inside the vocabulary")
    assert vs.isolation_for_seal(OPEN) == "none"
    assert vs.isolation_for_seal(SEALED) == "netns"
    assert vs.isolation_for_seal(INDETERMINATE) == "netns"
    assert vs.isolation_for_seal(BREACHED) == "netns"

    with tempfile.TemporaryDirectory() as tmp:
        proofs = _tree(tmp, "test_standing_open")
        _run([str(proofs), "--seal"])          # first seal — now netns
        landed = _landed(tmp)
        assert _seal_of(landed[0]) == SEALED

        # Now force a standing `open` and re-run: the guard must reproduce it bare.
        _force_standing_open(landed[0])

        text = _run([str(proofs), "--seal"])
        assert "isolation none=1" in text, (
            f"a proof whose standing record says `open` was re-run under a seal — the stronger "
            f"default overran the guard instead of sitting beneath it:\n{text}")


def test_a_diagnostic_run_is_unchanged() -> None:
    """Without --seal nothing lands in a record of truth, so there is nothing to protect and the
    cost of a plain `cairn test` must not move."""
    with tempfile.TemporaryDirectory() as tmp:
        proofs = _tree(tmp, "test_diagnostic")
        text = _run([str(proofs)])
        assert not _landed(tmp), "a diagnostic run persisted a validation"
        assert "isolation" not in text, f"a diagnostic run reported an isolation spread:\n{text}"
        assert "NOTHING WAS SEALED" in text, f"the not-sealing stopped saying itself:\n{text}"


def test_the_summary_splits_sealed_from_persisted() -> None:
    """Over a MIXED batch the closing lines must let a reader see how many of the persisted
    records were actually taken under a seal. Asserted as an invariant against the files on disk,
    never as a literal count."""
    with tempfile.TemporaryDirectory() as tmp:
        proofs = _tree(tmp, "test_one", "test_two")
        _run([str(proofs), "--seal"])
        landed = _landed(tmp)
        assert len(landed) == 2, f"the batch did not seal both fixtures: {landed}"

        # Force ONE of them to a standing `open` so the re-run is genuinely mixed.
        _force_standing_open(landed[0])

        text = _run([str(proofs), "--seal"])
        on_disk = Counter(_seal_of(p) for p in _landed(tmp))
        assert on_disk[SEALED] and on_disk[OPEN], (
            f"the batch was not mixed, so this tooth measured nothing: {dict(on_disk)}\n{text}")

        line = [ln for ln in text.splitlines() if "taken UNDER THE SEAL" in ln]
        assert len(line) == 1, f"the summary does not report an under-seal count:\n{text}"
        claimed = int(line[0].split()[0])
        assert claimed == on_disk[SEALED], (
            f"the command says {claimed} record(s) were taken under the seal and {on_disk[SEALED]} "
            f"on disk carry `sealed` — a record-of-truth surface miscounting its own records "
            f"(Law 7):\n{text}")

        total_line = [ln for ln in text.splitlines() if "VALIDATION(s) persisted" in ln]
        assert len(total_line) == 1, f"the persisted count went missing:\n{text}"
        persisted = int(total_line[0].split("—")[1].split()[0])
        assert persisted == sum(on_disk.values()), (
            f"the persisted count {persisted} disagrees with the {sum(on_disk.values())} files on "
            f"disk:\n{text}")
        assert claimed < persisted, (
            f"this tooth needs a batch where the two numbers DIFFER, or it cannot tell a split "
            f"surface from an unsplit one: {claimed} of {persisted}\n{text}")


def test_the_word_sealed_never_stands_over_an_open_record() -> None:
    """The surface half of the ticket. In a mixed batch no line may announce itself with the bare
    word SEALED, because that word over an `open` record says a measurement was taken that was
    not."""
    with tempfile.TemporaryDirectory() as tmp:
        proofs = _tree(tmp, "test_alpha", "test_beta")
        _run([str(proofs), "--seal"])
        _force_standing_open(_landed(tmp)[0])

        text = _run([str(proofs), "--seal"])
        headline = [ln for ln in text.splitlines() if ln.startswith("SEALED")]
        assert not headline, (
            f"a line still opens with the bare word SEALED over a batch containing an `open` "
            f"record — the last line on screen claiming a measurement nobody made:\n{text}")

        # AND THE NEIGHBOURING PROOF CAN STILL READ IT. test_seal_is_never_silently_dropped.py
        # parses the persisted count off the em-dash; breaking that parse would be this voyage
        # quietly reddening another ticket's proof.
        total_line = [ln for ln in text.splitlines() if "VALIDATION(s) persisted" in ln]
        assert len(total_line) == 1 and "—" in total_line[0], (
            f"the persisted line is no longer parseable by ticket 4431cf2bc625's proof:\n{text}")
        int(total_line[0].split("—")[1].split()[0])


def test_the_watch_probe_is_armed_and_can_fire() -> None:
    """The WATCHME object. Armed at the berth the ticket names, quiet against the live decision,
    loud the moment it is reverted."""
    from cairn.tools.base.probe import Probe
    from cairn.devices.tester.probes import a_first_seal_is_taken_under_the_seal as mod

    assert isinstance(mod.PROBE, Probe), "PROBE is not a Probe"
    assert mod.PROBE.carry and mod.PROBE.enough, "a probe needs both a carry and an enough"
    assert mod.PROBE.why, "a probe whose silence means nothing is decoration"

    quiet = mod.decision_reading(lambda standing: "netns" if standing is None else "none")
    assert quiet["fires"] is False, f"the probe is loud against the live decision: {quiet}"
    assert quiet["first_seal_isolation"] == "netns"

    loud = mod.decision_reading(lambda standing: "none")
    assert loud["fires"] is True, (
        f"the probe stayed quiet over the pre-build decision — it cannot see the thing it "
        f"watches: {loud}")
    assert "none" in loud["what"], f"the finding does not name what went wrong: {loud}"

    census = mod.seal_census()
    assert census["validations"] > 0, "the census read no validations at all"
    assert set(census["by_verdict"]), "the census carries no seal verdicts"


# ── tooth 7 — the bug this voyage uncovered, and fixed with it ────────────────────────────

def test_a_seal_cut_inside_a_seal_is_inherited_and_still_measured():
    """THE REGRESSION THIS VOYAGE MADE AND THEN PAID FOR, as a tooth.

    Taking a FIRST seal under the seal means a fixture proof with no standing record now runs
    under netns — including the fixture proofs that three of this device's own proofs drive
    through ``cairn test`` as a subprocess. Those outer proofs are themselves sealed, so the
    inner run tried to cut a namespace inside a namespace, and two separate things broke:

      1. ``--cap-add CAP_NET_ADMIN`` on the outer sandbox made bwrap refuse to start AT ALL
         inside it ("Unexpected capabilities but not setuid"). Measured four ways on
         2026-09-10; the capability was the sole cause and nothing in the corpus used it.
      2. Even with bwrap running, ``check_seal``'s bare positive control has no route to find
         inside an already-dark namespace, so a correctly sealed run read INDETERMINATE.

    Both are fixed at ``isolation.py``, and this tooth is the thing that would say so if
    either came back: it drives the real CLI from inside a real tester sandbox and reads the
    seal verdict off the record that landed. THE ASSERTION IS `sealed`, NOT MERELY `rc == 0`
    — a run that went green while recording the ABSENCE of a network reading is the exact
    false green this whole ticket exists to stop, and it would pass an rc check."""
    from cairn.devices.tester.isolation import NetnsIsolation, SEAL_MARKER, inside_a_seal

    # THE TOOTH RUNS AT WHATEVER DEPTH IT FINDS ITSELF, AND THAT IS THE POINT. Run bare it
    # cuts the outer namespace itself and the inner CLI inherits it; run under the tester's
    # own seal — which is how it runs in every sealed sweep — the outer wrap inherits and the
    # inner CLI is two levels down. Both are the case under test, and the assertion below is
    # identical in both: a `--seal` run started inside a seal records `sealed`. An earlier
    # draft of this tooth REFUSED to run when it found the marker already set, and the tester
    # promptly ran it inside its own seal and redded on that refusal. A tooth that only works
    # in the one world its author happened to be standing in is measuring the author.
    depth = "inherited" if inside_a_seal() else "freshly cut"

    with tempfile.TemporaryDirectory() as tmp:
        comp = Path(tmp) / "somecomp"
        (comp / "proofs").mkdir(parents=True)
        (comp / "intention+why.json").write_text(
            json.dumps({"what": "a throwaway", "why": "a throwaway"}), encoding="utf-8")
        (comp / "proofs" / "test_nested_fixture.py").write_text(
            "def test_one():\n    assert True\n\n"
            "if __name__ == '__main__':\n    test_one(); print('PASS: one')\n",
            encoding="utf-8")

        inner = [sys.executable, "-m", "cairn.devices.tester.cli", str(comp),
                 "--seal", "--timeout", "120"]
        argv = NetnsIsolation().wrap(inner, os.getcwd())
        run = subprocess.run(argv, capture_output=True, text=True, cwd=os.getcwd())

        assert run.returncode == 0, (
            f"a `cairn test --seal` driven from inside a {depth} tester seal did not run "
            f"green (rc={run.returncode}):\n{run.stdout[-2000:]}\n{run.stderr[-2000:]}")

        landed = sorted((comp / "validations").glob("*.json"))
        assert len(landed) == 1, f"expected one landed validation, got {landed}"
        trail = json.loads(landed[0].read_text(encoding="utf-8"))
        seal = ((trail[-1].get("evidence") or {}).get("seal") or {}).get("verdict")
        assert seal == SEALED, (
            f"a run nested inside a {depth} tester seal recorded {seal!r} rather than "
            f"{SEALED!r} — "
            f"an inherited namespace removes the route just as surely as a freshly cut one, "
            f"and a record that cannot say so is the absence-dressed-as-a-reading this "
            f"ticket was cast against")


def test_the_stronger_default_changes_isolation_not_verdict() -> None:
    """CLAUSE 3, and the tooth the nesting bug would have been caught by.

    The ticket's third DONE clause says the six proofs that had no standing seal at cast still
    reproduce under the stronger default — five green sealed, and launchers/proofs/test_bootstrap.py's
    red is its own dependency tooth rather than the seal. That sentence names a POPULATION that no
    longer exists: those six have since been sealed, so re-deriving "the six at cast" from today's
    world is impossible and a tooth that tried would be measuring the calendar.

    So the tooth asserts the INVARIANT the clause is made of, which is the thing that can still be
    false tomorrow: RAISING THE DEFAULT MOVES THE ISOLATION AND NOTHING ELSE. One fixture proof, run
    through the device's own door at `none` and then at `netns`, must come back with the same verdict
    and the same teeth. A netns run that reds for a reason unrelated to network reach is exactly the
    WRONG INTENT this ticket wrote down for itself — the ticket bought a stronger default and spent
    it — and it is not hypothetical: on the day this was built, `--cap-add CAP_NET_ADMIN` made every
    nested sandbox refuse to start, so proofs redded under the seal for a reason that had nothing to
    do with the network. This tooth reds on that world and is quiet on this one.

    `sink="none"` deliberately: the comparison is about the reading, and persisting two records for
    one fixture proof would leave the second standing over the first for no reason.
    """
    from cairn.devices.tester.device import TesterDevice

    dev = TesterDevice()
    with tempfile.TemporaryDirectory() as tmp:
        target = _tree(tmp, "test_reproduces") / "test_reproduces.py"
        bare = dev.run_proof(str(target), sink="none", caller="481221f45884 clause 3",
                             isolation="none", timeout=120)
        under = dev.run_proof(str(target), sink="none", caller="481221f45884 clause 3",
                              isolation="netns", timeout=120)

    assert bare["verdict"] == "green", f"the fixture is not green bare — the tooth measures nothing: {bare}"
    assert under["verdict"] == bare["verdict"], (
        f"the same proof read {bare['verdict']!r} at isolation none and {under['verdict']!r} under "
        f"the seal. The stronger default changed a VERDICT, which is the WRONG INTENT clause of "
        f"ticket 481221f45884 in one line: the ticket bought a stronger default and spent it.\n"
        f"under the seal: {under}")

    bare_teeth = (bare.get("evidence") or {}).get("teeth_green")
    under_teeth = (under.get("evidence") or {}).get("teeth_green")
    assert under_teeth == bare_teeth, (
        f"the seal changed which teeth ran: bare {bare_teeth!r}, under the seal {under_teeth!r}. "
        f"Same verdict over a different set of teeth is a green that means something else.")


def test_the_roster_carries_every_tooth() -> None:
    """THE ROSTER IS DERIVED, AND THIS IS WHAT NOTICES ONE GOING MISSING.

    Until 2026-09-10 this was an assertion inside a hand-rolled ``_main`` that ran the teeth in
    declaration order and stopped at the first red. That shape is the defect the hollow runner
    named on this very voyage: reverting ``cli.py`` reds the FIRST tooth, so the runner raised
    before printing a single name, and hollow read ``printed no teeth at all`` — a proof that
    cannot survive its subject being taken away says nothing about whether it checks that
    subject. Measured the same day: the same revert, run under pytest, reds five teeth in 19s.

    So the runner moved to ``proof_coverage.print_teeth_main``, which runs every tooth and prints
    each by name under a green, red or skip marker — the printer that lives beside the reader of
    those names, so the two cannot drift. What that move cost was the roster-collapse guard, and
    this tooth is it: nine teeth, counted at call time off the module's own globals, so a tooth
    deleted reds here rather than shrinking the proof quietly."""
    roster = sorted(k for k, v in globals().items() if k.startswith("test_") and callable(v))
    assert len(roster) >= 9, (
        f"the derived roster collapsed — the nine teeth of ticket 481221f45884 (eight clauses "
        f"plus this one): {len(roster)} → {roster}")


if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main

    raise SystemExit(print_teeth_main(__file__))
