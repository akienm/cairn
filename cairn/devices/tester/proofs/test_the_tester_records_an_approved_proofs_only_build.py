"""Teeth for ticket bf1cd5d79805 — the ticket plan approves a proofs-only build.

MEASURED 2026-10-06 on 45c168cc1ff1: its build wrote only its two proofs, so the hollow skipped
both as the instrument and sealed ``{}``, and clearance refuses hollow_nothing_measured with no
repair of the code able to give it anything to revert. Ruling 8p (f5bba1daa72a) answered that
with a question to Akien; F50 (Akien, 2026-10-09) retires the question: "tester should never ask
me about anything that i don't need to have approved. the plan based tickets are inherently
preapproved."

THE RULE THESE TEETH HOLD. A run that measured nothing because every skip is an instrument (or
record) skip, at least one the instrument, and no file was unwritten, reads green only when the
ticket's plan names EVERY skipped file in its ``writes_to`` list — a field, never prose. The
finding carries ``approved`` {file: "plan"} and --seal seals each such file as
{"approved": "plan"}. Otherwise the run stays red ("measured nothing") and --seal opens NO
question: the red is the record. An Akien-answered question no longer approves. Every other
empty run stays red, plan or not.

The fixture build is test_the_hollow_skips_only_the_instrument.py's (ticket 763379e32e3b), whose
tooth 3 — an instrument-only build whose plan names nothing — must stay red as it is. Every tooth
imports the tester's modules INSIDE its body, so a reverted hollow.py or cli.py reds teeth
instead of breaking this file's import.
"""
from __future__ import annotations

import contextlib
import functools
import importlib.util
import io
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 1800  # tooth 5 runs test_hollow.py (~250s) in a subprocess

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402
from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "bf1cd5d79805": {
        "1": "test_a_plan_naming_every_skipped_file_approves_green_and_seals_plan_asking_nothing",
        "2": "test_a_plan_that_does_not_name_every_skipped_file_stays_red_and_asks_nothing",
        "3": "test_an_empty_run_that_is_not_only_the_instrument_stays_red_with_a_naming_plan",
        "4": "test_the_standing_hollow_proofs_stay_green",
    },
}

_HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"tester_{name}", _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


sk = _load("test_the_hollow_skips_only_the_instrument")
FIXTURE, INSTRUMENT, HELPER = sk.FIXTURE, sk.INSTRUMENT, sk.HELPER
AKIEN = "Akien, recorded by caller class cc"


def _instrument_only(extra_writes: list[str] | None = None):
    """763379's tooth-3 world: the build wrote only the instrument and its import."""
    repo, commons, berths, _ = sk._fixture(
        {INSTRUMENT: sk._PROOF_SRC + "# touched\n", HELPER: sk._HELPER_SRC + "# touched\n"},
        [INSTRUMENT, HELPER] + (extra_writes or []), subject0=sk._SUBJECT_CLEAN)
    (commons / "questions").mkdir()
    return repo, commons, berths


def _question(commons: Path, qid: str, *, ticket: str = FIXTURE, names: str = INSTRUMENT,
              resolved: bool = True, answered_by: str | None = AKIEN) -> str:
    record = {
        "id": qid, "date": "2026-10-06", "ticket": ticket,
        "question": f"May {names} be resealed after this change?",
        "why_it_blocks": "fixture", "raised_by": "fixture", "born_of": None, "source": None,
        "resolved": resolved, "answer": "yes" if resolved else None,
        "answered_by": answered_by if resolved else None,
        "answered_at": "2026-10-06T09:00:00" if resolved else None,
        "spawned": [] if resolved else None,
    }
    (commons / "questions" / f"{qid}.json").write_text(json.dumps(record), encoding="utf-8")
    return qid


def _measure(repo, commons, berths):
    from cairn.devices.tester.hollow import measure
    return measure(FIXTURE, repo_root=repo, commons=commons, berths_root=berths, timeout=60)


def _run_cli(repo, commons, berths, argv):
    """cli.main in-process against the fixture; the seal is captured, never written, and any
    question the run opens lands in the fixture's commons through the artifact door."""
    from cairn.devices.tester import cli, hollow
    from cairn.tools.artifact import artifact as A
    from cairn.tools.question import question as question_mod
    sealed: dict = {}

    def recorder(proof, ticket, reading, **kw):
        sealed.update(reading)
        return False

    saved = (hollow.measure, cli.REPO_ROOT, cli.record_hollow, question_mod.QUESTIONS_DIR)
    hollow.measure = functools.partial(hollow.measure, commons=commons, berths_root=berths)
    cli.REPO_ROOT, cli.record_hollow = repo, recorder
    question_mod.QUESTIONS_DIR = commons / "questions"
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": repo,
                            "parked": commons.parent / "parked"})
    out = io.StringIO()
    try:
        with contextlib.redirect_stdout(out):
            rc = cli.main(argv)
    finally:
        hollow.measure, cli.REPO_ROOT, cli.record_hollow, question_mod.QUESTIONS_DIR = saved
        A.set_diagnostic_roots(None)
    return rc, sealed, out.getvalue()


def _plan(commons: Path, writes_to: list[str]) -> None:
    """The fixture ticket's flat plan, naming ``writes_to`` in the field the tester reads."""
    (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(
        json.dumps({"id": FIXTURE, "how": "fixture", "writes_to": writes_to}), encoding="utf-8")


def _asked(commons: Path) -> list[dict]:
    """Every question in the fixture store the tester raised."""
    return [q for q in (json.loads(p.read_text()) for p in sorted((commons / "questions").glob("*.json")))
            if q.get("raised_by") == "tester"]


def test_a_plan_naming_every_skipped_file_approves_green_and_seals_plan_asking_nothing():
    """45c1's shape under F50: the plan's writes_to names the instrument and its import. The run
    is green, the finding carries "plan" on every skipped file, --seal records each as
    {"approved": "plan"}, and no question is opened."""
    repo, commons, berths = _instrument_only()
    _plan(commons, [INSTRUMENT, HELPER, "elsewhere.py"])
    f = _measure(repo, commons, berths)
    assert not f["measured"], f["measured"]
    assert f.get("approved") == {INSTRUMENT: "plan", HELPER: "plan"}, (f.get("approved"), f["reasons"])
    assert not any("measured nothing" in r for r in f["reasons"]), f["reasons"]
    assert f["verdict"] == "green", f["reasons"]
    rc, sealed, out = _run_cli(repo, commons, berths, ["--hollow", FIXTURE, "--seal", "-q"])
    assert rc == 0, out
    assert sealed == {INSTRUMENT: {"approved": "plan"}, HELPER: {"approved": "plan"}}, sealed
    assert _asked(commons) == [], _asked(commons)


def test_a_plan_that_does_not_name_every_skipped_file_stays_red_and_asks_nothing():
    """A plan naming only some skipped files, none, or naming them only in prose — or an
    Akien-answered question in place of the plan — leaves the run red, and --seal opens no
    question: the red is the record."""
    cases = {
        "names only the instrument": ([INSTRUMENT], False),
        "names nothing": ([], False),
        "named only in prose": (None, False),
        "a question answered by Akien, no plan": ([], True),
    }
    for label, (writes, question) in cases.items():
        repo, commons, berths = _instrument_only()
        if writes is None:
            (commons / "tickets" / f"{FIXTURE}-fixture.json").write_text(json.dumps(
                {"id": FIXTURE, "how": f"write {INSTRUMENT} and {HELPER}"}), encoding="utf-8")
        else:
            _plan(commons, writes)
        if question:
            _question(commons, "open-b71cd5d70001")
        f = _measure(repo, commons, berths)
        assert not f.get("approved"), (label, f.get("approved"))
        assert any("measured nothing" in r for r in f["reasons"]), (label, f["reasons"])
        assert f["verdict"] == "red", (label, f["verdict"])
        rc, sealed, out = _run_cli(repo, commons, berths, ["--hollow", FIXTURE, "--seal", "-q"])
        assert rc == 1, (label, out)
        assert _asked(commons) == [], (label, _asked(commons))
        assert not any(isinstance(r, dict) and "approved" in r for r in sealed.values()), (label, sealed)


def test_an_empty_run_that_is_not_only_the_instrument_stays_red_with_a_naming_plan():
    """A run that measured nothing for any other reason stays red: here one writes_to file is
    absent at HEAD with no successor, so not every skip is an instrument skip — though the plan
    names every file."""
    repo, commons, berths = _instrument_only(extra_writes=["gone.py"])
    _plan(commons, [INSTRUMENT, HELPER, "gone.py"])
    f = _measure(repo, commons, berths)
    skips = {s["file"]: s["why"] for s in f["skipped"]}
    assert "gone.py" in skips and skips["gone.py"] != sk.SKIP_INSTRUMENT, skips
    assert not f.get("approved"), f.get("approved")
    assert any("measured nothing" in r for r in f["reasons"]), f["reasons"]
    assert f["verdict"] == "red", f["verdict"]


def test_the_standing_hollow_proofs_stay_green():
    """763379e32e3b's tooth 3 (a plan naming nothing: still measures nothing), rung 4's teeth,
    and the hollow's own proof hold."""
    sk.test_a_build_of_only_the_instrument_still_measures_nothing()
    for rel in ("cairn/devices/tester/proofs/test_rung_4_lifts_for_an_answered_question.py",
                "cairn/devices/tester/proofs/test_hollow.py"):
        r = subprocess.run([sys.executable, str(_REPO_ROOT / rel)], capture_output=True,
                           text=True, timeout=1500, cwd=_REPO_ROOT)
        assert r.returncode == 0, (rel, r.stdout[-1500:], r.stderr[-1500:])


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
