"""Teeth for ticket f5bba1daa72a — the tester records an approved proofs-only build.

MEASURED 2026-10-06 on 45c168cc1ff1: its build wrote only its two proofs, so the hollow skipped
both as the instrument and sealed ``{}``, and clearance refuses hollow_nothing_measured with no
repair of the code able to give it anything to revert. Akien had already said yes to that proof
change (open-728473f9b70d). His ruling 8p (2026-10-06): his approval IS the measurement (Law 10)
— "and then i say it's approved and it then is proved. at that point the tester records that
proving. and it's the tester that's asking me for a ruling."

THE RULE THESE TEETH HOLD. A run that measured nothing because every skip is an instrument skip
(and no file was unwritten) reads green only when a question bound to the ticket, answered by
Akien, names one of those files; the finding carries ``approved`` {file: qid} and the --seal
path seals each such file as {"approved": qid}. Without one the run stays red ("measured
nothing") and --seal asks him, once. Every other empty run stays red, approval or not.

The fixture build is test_the_hollow_skips_only_the_instrument.py's (ticket 763379e32e3b), whose
tooth 3 — an instrument-only build with no approval measures nothing — must stay red as it is.
Question records are plain JSON in the fixture's own commons, the shape
``cairn.tools.question.question.answer`` writes (as test_rung_4_lifts_for_an_answered_question.py
does). Every tooth imports the tester's modules INSIDE its body, so a reverted hollow.py or
cli.py reds teeth instead of breaking this file's import.
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
    "f5bba1daa72a": {
        "1": "test_an_akien_approval_naming_the_file_makes_an_instrument_only_build_green_and_sealed",
        "2": "test_an_approval_by_another_hand_or_ticket_or_naming_no_file_stays_red",
        "3": "test_an_empty_run_that_is_not_only_the_instrument_stays_red_with_an_approval",
        "4": "test_the_seal_asks_akien_once",
        "5": "test_the_standing_hollow_proofs_stay_green",
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


def _questions(commons: Path) -> list[dict]:
    return [json.loads(p.read_text()) for p in sorted((commons / "questions").glob("open-*.json"))]


def test_an_akien_approval_naming_the_file_makes_an_instrument_only_build_green_and_sealed():
    """45c1's shape: an Akien-answered question bound to the ticket names the instrument. The
    run is green, the finding carries the approval on every skipped file, and --seal records
    each as {"approved": qid}."""
    repo, commons, berths = _instrument_only()
    qid = _question(commons, "open-f1x7a99e0001")
    f = _measure(repo, commons, berths)
    assert not f["measured"], f["measured"]
    assert f.get("approved") == {INSTRUMENT: qid, HELPER: qid}, (f.get("approved"), f["reasons"])
    assert not any("measured nothing" in r for r in f["reasons"]), f["reasons"]
    assert f["verdict"] == "green", f["reasons"]
    rc, sealed, out = _run_cli(repo, commons, berths, ["--hollow", FIXTURE, "--seal", "-q"])
    assert rc == 0, out
    assert sealed == {INSTRUMENT: {"approved": qid}, HELPER: {"approved": qid}}, sealed
    assert [q["id"] for q in _questions(commons)] == [qid], _questions(commons)


def test_an_approval_by_another_hand_or_ticket_or_naming_no_file_stays_red():
    """Only Akien's answer, on this ticket, about these files, is the measurement."""
    cases = {
        "answered by cc": dict(answered_by="cc"),
        "measured, not his": dict(answered_by="measurement: /tmp/x.json, recorded by caller class cc"),
        "still open": dict(resolved=False),
        "bound to another ticket": dict(ticket="0ther71cket00"),
        "names no skipped file": dict(names="some/other/proofs/test_elsewhere.py"),
    }
    for i, (label, kw) in enumerate(cases.items()):
        repo, commons, berths = _instrument_only()
        _question(commons, f"open-f1x7a99e01{i:02d}", **kw)
        f = _measure(repo, commons, berths)
        assert not f.get("approved"), (label, f.get("approved"))
        assert any("measured nothing" in r for r in f["reasons"]), (label, f["reasons"])
        assert f["verdict"] == "red", (label, f["verdict"])


def test_an_empty_run_that_is_not_only_the_instrument_stays_red_with_an_approval():
    """A run that measured nothing for any other reason stays red: here one writes_to file is
    absent at HEAD with no successor, so not every skip is an instrument skip."""
    repo, commons, berths = _instrument_only(extra_writes=["gone.py"])
    _question(commons, "open-f1x7a99e0201")
    f = _measure(repo, commons, berths)
    skips = {s["file"]: s["why"] for s in f["skipped"]}
    assert "gone.py" in skips and skips["gone.py"] != sk.SKIP_INSTRUMENT, skips
    assert not f.get("approved"), f.get("approved")
    assert any("measured nothing" in r for r in f["reasons"]), f["reasons"]
    assert f["verdict"] == "red", f["verdict"]


def test_the_seal_asks_akien_once():
    """With no answer, --seal opens one question to Akien bound to the ticket and naming the
    files; a second --seal finds it standing and opens none. Nothing is sealed approved."""
    repo, commons, berths = _instrument_only()
    rc, sealed, out = _run_cli(repo, commons, berths, ["--hollow", FIXTURE, "--seal", "-q"])
    asked = _questions(commons)
    assert rc == 1, out
    assert len(asked) == 1, asked
    q = asked[0]
    assert q["ticket"] == FIXTURE and not q["resolved"], q
    assert q["question"].endswith("?") and INSTRUMENT in q["question"], q["question"]
    assert q["raised_by"] == "tester", q["raised_by"]
    assert q["id"] in out, out
    assert not any(isinstance(r, dict) and "approved" in r for r in sealed.values()), sealed
    rc2, _, out2 = _run_cli(repo, commons, berths, ["--hollow", FIXTURE, "--seal", "-q"])
    assert rc2 == 1 and len(_questions(commons)) == 1, (out2, _questions(commons))
    rc3, _, _ = _run_cli(repo, commons, berths, ["--hollow", FIXTURE, "-q"])
    assert len(_questions(commons)) == 1, _questions(commons)


def test_the_standing_hollow_proofs_stay_green():
    """763379e32e3b's tooth 3 (no approval: still measures nothing), rung 4's teeth, and the
    hollow's own proof hold."""
    sk.test_a_build_of_only_the_instrument_still_measures_nothing()
    for rel in ("cairn/devices/tester/proofs/test_rung_4_lifts_for_an_answered_question.py",
                "cairn/devices/tester/proofs/test_hollow.py"):
        r = subprocess.run([sys.executable, str(_REPO_ROOT / rel)], capture_output=True,
                           text=True, timeout=1500, cwd=_REPO_ROOT)
        assert r.returncode == 0, (rel, r.stdout[-1500:], r.stderr[-1500:])


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
