"""Teeth for ticket af394c12b62a — the hollow's 8p question opens when record skips stand beside
the instrument.

MEASURED 2026-10-07 on 41202d4c8d3b (8y): a proofs-only build whose writes_to honestly lists its
own validation record is skipped SKIP_INSTRUMENT + SKIP_RECORD, and the 8p branch required every
skip to be SKIP_INSTRUMENT, so approval() was never called and the hollow redded "measured
nothing" with no way to ask Akien. F19 (the peer's call for Akien, his to overturn): widen the
branch to admit record skips beside the instrument, and pin three edges so the widening cannot
become the escape hatch hollow.py's own comment warns about:

  (1) instrument + record skips, nothing unchanged -> the 8p question opens;
  (2) record skips only, no instrument -> red, never asked;
  (3) any unchanged file or any other skip reason beside them -> red, never asked.

Fixtures are f5bba1daa72a's (test_the_tester_records_an_approved_proofs_only_build.py), loaded the
way it loads test_the_hollow_skips_only_the_instrument.py. The record path need not exist:
``_classify`` skips a record before the existence check. Every tooth imports the tester's modules
INSIDE its body (through the loaded helpers), so a reverted hollow.py reds teeth instead of
breaking this file's import.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(_REPO_ROOT))

PROOF_TIMEOUT_S = 900

from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "af394c12b62a": {
        "1": "test_instrument_and_record_skips_open_the_8p_question",
        "2": "test_record_skips_alone_stay_red_and_ask_nothing",
        "3": "test_an_unchanged_file_or_another_skip_beside_them_stays_red",
    },
}

_HERE = Path(__file__).resolve().parent


def _load(name: str):
    spec = importlib.util.spec_from_file_location(f"tester_8p2_{name}", _HERE / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ap = _load("test_the_tester_records_an_approved_proofs_only_build")
sk = ap.sk
FIXTURE, INSTRUMENT, HELPER, SUBJECT = sk.FIXTURE, sk.INSTRUMENT, sk.HELPER, sk.SUBJECT
RECORD = "validations/test_fixture.json"


def _world(writes_to: list[str]):
    """f5bba's instrument-only build (the instrument and its import touched), with the writes_to
    the tooth names."""
    repo, commons, berths, _ = sk._fixture(
        {INSTRUMENT: sk._PROOF_SRC + "# touched\n", HELPER: sk._HELPER_SRC + "# touched\n"},
        writes_to, subject0=sk._SUBJECT_CLEAN)
    (commons / "questions").mkdir()
    return repo, commons, berths


def _asks_nothing(repo, commons, berths, label):
    rc, sealed, out = ap._run_cli(repo, commons, berths, ["--hollow", FIXTURE, "--seal", "-q"])
    assert rc in (1, 2), (label, rc, out)  # 1 red, 2 unmeasurable; never 0
    asked = [q for q in ap._questions(commons) if q.get("raised_by") == "tester"]
    assert not asked, (label, asked)
    assert not any(isinstance(r, dict) and "approved" in r for r in sealed.values()), (label, sealed)


def test_instrument_and_record_skips_open_the_8p_question():
    """writes_to = the instrument, its import and the build's own validation record. With no
    answer, --seal opens exactly one question raised by the tester naming the instrument; with
    an Akien-answered question naming the instrument the run is green and approved covers every
    skipped file, the record included."""
    from cairn.devices.tester.hollow import SKIP_INSTRUMENT, SKIP_RECORD
    repo, commons, berths = _world([INSTRUMENT, HELPER, RECORD])
    f = ap._measure(repo, commons, berths)
    skips = {s["file"]: s["why"] for s in f["skipped"]}
    assert skips.get(RECORD) == SKIP_RECORD and skips.get(INSTRUMENT) == SKIP_INSTRUMENT, skips
    assert not f["measured"] and not f["unchanged"], (f["measured"], f["unchanged"])
    assert sorted(f.get("approval_wanted") or []) == sorted([INSTRUMENT, HELPER, RECORD]), \
        (f.get("approval_wanted"), f["reasons"])
    rc, sealed, out = ap._run_cli(repo, commons, berths, ["--hollow", FIXTURE, "--seal", "-q"])
    asked = ap._questions(commons)
    assert rc == 1, out
    assert len(asked) == 1, asked
    q = asked[0]
    assert q["ticket"] == FIXTURE and not q["resolved"] and q["raised_by"] == "tester", q
    assert INSTRUMENT in q["question"] and q["question"].endswith("?"), q["question"]

    repo, commons, berths = _world([INSTRUMENT, HELPER, RECORD])
    qid = ap._question(commons, "open-f1x7a99e0801")
    f = ap._measure(repo, commons, berths)
    assert f.get("approved") == {INSTRUMENT: qid, HELPER: qid, RECORD: qid}, (f.get("approved"), f["reasons"])
    assert f["verdict"] == "green", f["reasons"]


def test_record_skips_alone_stay_red_and_ask_nothing():
    """writes_to = the validation record only: verdict red 'measured nothing', nothing approved
    or wanted even with an Akien answer naming the record, and --seal opens no question."""
    from cairn.devices.tester.hollow import SKIP_INSTRUMENT, SKIP_RECORD
    repo, commons, berths = _world([RECORD])
    ap._question(commons, "open-f1x7a99e0802", names=RECORD)
    f = ap._measure(repo, commons, berths)
    assert [s["why"] for s in f["skipped"]] == [SKIP_RECORD], f["skipped"]
    assert not f.get("approved") and not f.get("approval_wanted"), (f.get("approved"), f.get("approval_wanted"))
    assert any("measured nothing" in r for r in f["reasons"]), f["reasons"]
    assert f["verdict"] == "red", f["verdict"]
    repo, commons, berths = _world([RECORD])
    _asks_nothing(repo, commons, berths, "record only")


def test_an_unchanged_file_or_another_skip_beside_them_stays_red():
    """Instrument + record beside an absent gone.py (another skip reason), and separately
    beside a writes_to file the build never touched (unchanged): each red, nothing approved,
    nothing asked, even with an Akien answer naming the instrument.

    The unchanged case has two red shapes, and either holds the edge. MEASURED 2026-10-07: when
    the untouched file is the only eligible one, the anchor refusal fires before the 8p branch
    (HollowUnmeasurable, "every one of the 1 eligible file(s) is byte-identical"; the CLI exits
    2). A finding that does come back must name it unchanged and read red."""
    from cairn.devices.tester.hollow import SKIP_INSTRUMENT, SKIP_RECORD, HollowUnmeasurable
    cases = {"another skip reason": "gone.py", "an unchanged file": SUBJECT}
    for i, (label, extra) in enumerate(cases.items()):
        repo, commons, berths = _world([INSTRUMENT, HELPER, RECORD, extra])
        ap._question(commons, f"open-f1x7a99e081{i}")
        try:
            f = ap._measure(repo, commons, berths)
        except HollowUnmeasurable as why:
            assert extra == SUBJECT and "byte-identical" in str(why), (label, str(why))
            f = None
        if f is None:
            pass
        elif extra == SUBJECT:
            assert SUBJECT in f["unchanged"], (label, f["unchanged"])
        else:
            skips = {s["file"]: s["why"] for s in f["skipped"]}
            assert extra in skips and skips[extra] not in (SKIP_INSTRUMENT, SKIP_RECORD), (label, skips)
        if f is not None:
            assert not f.get("approved") and not f.get("approval_wanted"), (label, f.get("approved"))
            assert f["verdict"] == "red", (label, f["reasons"])
        repo, commons, berths = _world([INSTRUMENT, HELPER, RECORD, extra])
        _asks_nothing(repo, commons, berths, label)


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
