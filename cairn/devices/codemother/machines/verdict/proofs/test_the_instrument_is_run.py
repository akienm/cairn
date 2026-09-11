"""THE DOOR RUNS THE INSTRUMENT IT IS HANDED — ticket 8e5db5f3edb2.

WHAT WAS WRONG. ``write_verdict`` is the last gate before a forward crossing into
PROVED, and every check it gated on read the artifact's SHAPE: is the instrument
field present, is the outcome word legal, does every hypothesis carry a
disposition, does every criterion carry a discriminating observation. Not one of
them touched the world the instrument describes. So a criterion could report
``pass`` while its instrument, run right now, said otherwise, and nothing anywhere
would know — the door that closes proven-space asked the builder whether the build
worked. Law 8 names that shape as worse than a red: a red is distrusted by
construction, and a false green gets leaned on by a peer without re-checking.

WHAT THESE TEETH SETTLE, clause by clause against the ticket's falsifier. The
extraction declines rather than guesses (2); a non-zero success exit is READ from
the declaration rather than assumed (1); a contradicted outcome is refused in both
directions (3); a bound overrun is refused as a TIMEOUT by that name (4); and what
the door observed lands in the artifact it berths (5).

WHAT THEY CANNOT SETTLE, which is why the ticket carries a WATCHME. Every tooth
here runs against fixtures this file wrote, so all of them say the physics is
right TODAY. The ticket's WRONG INTENT clause is about the CORPUS: instruments
could collapse into trivially-green commands — ``true``, a bare ``ls``, an
``echo`` — so every re-run agrees by construction and the door has moved the
silence rather than removed it. No fixture can see that. The probe at
``probes/the_instrument_is_re_run_not_reported.py`` reads the shape of the
instruments actually arriving, which is the only place that question is answerable.

NO FORK IN THE CHEAP TEETH. ``observe_instruments`` takes its runner as an
argument, so the reasoning is watched against a substitute and the subprocess is
paid for exactly where a subprocess is the thing under test (the timeout tooth,
which needs a real clock, and the berth tooth, which needs a real exit).
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.codemother.machines.verdict.verdict import (  # noqa: E402
    VerdictRefused, extract_command, inspect_verdict, observe_instruments,
    run_instrument, validate_verdict, write_verdict)
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

PROVES = {
    "8e5db5f3edb2": {
        "1": "test_a_non_zero_success_exit_is_read_from_the_declaration",
        "2": "test_extraction_declines_rather_than_guesses",
        "3": "test_a_contradicted_outcome_is_refused",
        "4": "test_a_timeout_is_refused_by_its_own_name",
        "5": "test_the_observed_run_lands_in_the_berthed_artifact",
        "the watch probe is armed and can be made to fire":
            "test_the_probe_is_armed_and_can_be_made_to_fire",
    },
}


# ── the fixture world ────────────────────────────────────────────────────────

def make_root():
    """A filed ticket, a claiming chain, and two scripts the door can actually run.

    ``exits.sh`` returns whatever it is handed, which is the whole fixture: it
    lets one tooth declare a success as 7 and another declare it as 0 without any
    of them depending on what a particular command happens to do."""
    tmp = str(scratch_dir("instrument_is_run_"))
    root = os.path.join(tmp, "repo")
    os.makedirs(os.path.join(root, "cairn"))
    os.makedirs(os.path.join(root, "proofs"))
    with open(os.path.join(root, "proofs", "exits.sh"), "w") as fh:
        fh.write('echo "ran with ${1:-0}"\nexit "${1:-0}"\n')
    with open(os.path.join(root, "proofs", "hangs.sh"), "w") as fh:
        fh.write("sleep 30\n")
    tickets = os.path.join(tmp, "CairnCommons", "tickets")
    os.makedirs(tickets)
    with open(os.path.join(tickets, "sworn.json"), "w") as fh:
        fh.write("{}")
    packets = os.path.join(tmp, "berths", "0", "packets")
    os.makedirs(packets)
    hyp = os.path.join(packets, "hypothesize-20260911T000000-feedfeedfeed.json")
    with open(hyp, "w") as fh:
        json.dump({"hypotheses": [{"piece": "run the instrument",
                                   "expect": "the exit agrees with the declaration",
                                   "falsifier": "a reported pass the run contradicts",
                                   "instrument": "bash proofs/exits.sh"}]}, fh)
    val = os.path.join(packets, "validate-20260911T000001-cafecafecafe.json")
    with open(val, "w") as fh:
        json.dump({"ticket": "sworn", "hypothesize_ref": hyp,
                   "criteria": [{"claim": "the grep finds nothing",
                                 "instrument": "bash proofs/exits.sh 7",
                                 "expect_exit": 7,
                                 "covers": ["run the instrument"]}]}, fh)
    return root, val


@pytest.fixture
def world():
    return make_root()


def artifact(val, **entry):
    """One criterion, answered — the smallest artifact the coverage check passes."""
    return {
        "ticket": "sworn",
        "validate_ref": val,
        "verdicts": [dict({"claim": "the grep finds nothing",
                           "instrument": "bash proofs/exits.sh 7",
                           "outcome": "pass",
                           "evidence": "exit 7, no hits",
                           "discriminating_observation":
                               "seeded a hit; the same instrument exits 0"}, **entry)],
        "dispositions": [{"piece": "run the instrument",
                          "expect": "the exit agrees with the declaration",
                          "disposition": "confirmed", "by": "exit 7 as declared"}],
    }


def refusal(fn, needle):
    try:
        fn()
    except VerdictRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return str(err)
    raise AssertionError("expected VerdictRefused mentioning %r, got none" % needle)


def _fake_runner(exit_code=0, tail="", timed_out=False):
    def run(command, *, timeout_s=600, cwd=None):
        return {"command": command, "exit": None if timed_out else exit_code,
                "timed_out": timed_out, "timeout_s": timeout_s,
                "seconds": 0.0, "tail": tail}
    return run


# ── clause (2): the extraction declines rather than guesses ──────────────────

def test_extraction_declines_rather_than_guesses(world):
    """ZERO CANDIDATES OR TWO IS A REFUSAL. Choosing between two backticked spans
    is a judgement, and this door makes none — a door that guesses which half of a
    sentence the builder meant is an oracle wearing a regex."""
    root, val = world
    assert extract_command("bash proofs/exits.sh 7", root) == "bash proofs/exits.sh 7"
    assert extract_command("the teeth, twice: `bash proofs/exits.sh`", root) \
        == "bash proofs/exits.sh"
    assert extract_command("PYTHONPATH=. python3 -c 'print(1)'", root) is not None, \
        "a leading VAR=value assignment is stepped over, not read as a program name"
    for prose in ("the probe's survey of the ticket corpus",
                  "a reading taken against the live store",
                  "run `this` or maybe `that`",
                  "",
                  None,
                  "   "):
        assert extract_command(prose, root) is None, prose

    # AND THE REFUSAL NAMES THE CRITERION AND QUOTES THE PROSE, which is the half
    # that makes it actionable: a builder told only "refused" has to go looking for
    # which of eight criteria the door could not read.
    a = artifact(val, instrument="the probe's survey of the ticket corpus")
    err = refusal(lambda: write_verdict(a, instance_dir=os.path.join(root, "b1"),
                                        root=root), "no command could be run")
    assert "the grep finds nothing" in err and "survey of the ticket corpus" in err

    # A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED: an artifact carrying no stamp
    # reaches the new entries with nothing to inspect, and they are missing from the
    # record rather than green. That is what leaves the corpus berthed before this
    # shipped legal where it lies (Law 7 — a berthed verdict is a record of truth).
    names = [e["identity"] for e in inspect_verdict(a, root=root)]
    assert "every_instrument_carries_a_runnable_command" not in names, names
    assert "every_falsifier_clause_is_answered" in names, names


# ── clause (1): the declaration is read, not assumed ─────────────────────────

def test_a_non_zero_success_exit_is_read_from_the_declaration(world):
    """EXIT STATUS IS THE INSTRUMENT'S ANSWER, NOT THE CRITERION'S. ``grep -c x f``
    exits 1 when the count is zero, and zero is exactly what some criteria claim.
    So what a pass looks like is DECLARED — and the chart's declaration, authored
    before the build and unable to have been tuned to the run that happened, beats
    the builder's own."""
    root, val = world
    a = artifact(val)
    obs = observe_instruments(a, root, runner=_fake_runner(7))
    assert obs[0]["expect_exit"] == 7, \
        "the validate berth declared 7; a door that assumed 0 would refuse a true claim"
    assert validate_verdict(a, root=root, observations=obs) is a

    record = inspect_verdict(a, root=root, observations=obs)
    by_name = {e["identity"]: e for e in record}
    entry = by_name["every_criterion_instrument_was_run_and_agreed"]
    assert entry["expected"] == entry["actual"] == ["the grep finds nothing"], entry
    assert entry["values"]["runs"][0]["exit"] == 7 and entry["values"]["runs"][0]["expect_exit"] == 7

    # THE VERDICT ENTRY DECLARES ONLY WHERE THE CHART DID NOT. With a berth in
    # hand the chart wins outright, so a builder cannot widen a criterion after
    # the fact by declaring a friendlier exit on their own answer.
    tuned = artifact(val, expect_exit=0)
    assert observe_instruments(tuned, root, runner=_fake_runner(7))[0]["expect_exit"] == 7
    # With no berth to read — the falsifier form a probe writes — it is all there is.
    loose = dict(tuned, validate_ref="falsifier@sworn")
    assert observe_instruments(loose, root, runner=_fake_runner(0))[0]["expect_exit"] == 0


# ── clause (3): a contradicted outcome is refused, both ways ─────────────────

def test_a_contradicted_outcome_is_refused(world):
    """BOTH DIRECTIONS, because a claimed failure that cannot be reproduced is the
    same hollow shape wearing the other sign."""
    root, val = world
    a = artifact(val)

    err = refusal(lambda: validate_verdict(
        a, root=root, observations=observe_instruments(
            a, root, runner=_fake_runner(1, tail="3 hits, not 0"))),
        "reports pass")
    assert "the grep finds nothing" in err
    assert "3 hits, not 0" in err, \
        "the output tail rides the refusal, or the builder has a verdict and no evidence"

    failed = artifact(val, outcome="fail", evidence="3 hits")
    refusal(lambda: validate_verdict(
        failed, root=root, observations=observe_instruments(
            failed, root, runner=_fake_runner(7))),
        "reports fail")

    # ...the honestly-passing one passes the whole door.
    assert validate_verdict(a, root=root, observations=observe_instruments(
        a, root, runner=_fake_runner(7))) is a

    # AND THE HONESTLY-FAILING ONE IS STILL REFUSED — BY THE OTHER SENTENCE. A
    # reported `fail` never reaches PROVED whatever its re-run says: the coverage
    # check kicks it back because PROVED asserts done. The whole point of clause
    # (3) is that the builder can tell WHICH refusal they got, because the two send
    # them to opposite work — "go fix the build" versus "your report of a failure
    # cannot be reproduced and the build may be fine". That distinction is what buys
    # the run entries their place ahead of the coverage check in `inspect_verdict`.
    honest = refusal(lambda: validate_verdict(
        failed, root=root, observations=observe_instruments(
            failed, root, runner=_fake_runner(1))),
        "FAILED")
    assert "the re-run disagrees" not in honest, \
        "a failure the re-run reproduces is a kick-back, never a contradiction"


# ── clause (4): a timeout is refused by its own name ─────────────────────────

def test_a_timeout_is_refused_by_its_own_name(world):
    """NEVER FOLDED INTO DISAGREEMENT. The two send a builder to different work —
    one to a slow or hanging instrument, the other to a claim that is not true —
    and collapsing them is what Law 7 forbids at a diagnostic surface.

    THIS TOOTH PAYS FOR A REAL FORK, deliberately: a timeout is a fact about a
    clock, and a substitute runner asserting `timed_out: True` would prove only
    that the dict key is spelled correctly."""
    root, val = world
    real = run_instrument("bash proofs/hangs.sh", timeout_s=1, cwd=root)
    assert real["timed_out"] is True and real["exit"] is None, real

    a = artifact(val, instrument="bash proofs/hangs.sh", timeout_s=1)
    err = refusal(lambda: write_verdict(a, instance_dir=os.path.join(root, "b2"),
                                        root=root), "TIMEOUT")
    assert "did not finish" in err and "the grep finds nothing" in err
    assert "reports pass" not in err, \
        "a timeout must not be reported as a disagreement — different work, different word"


# ── clause (5): what was observed lands in the record ────────────────────────

def test_the_observed_run_lands_in_the_berthed_artifact(world):
    """LAW 7 AT THE CLOSE: the measurement lands in the record of truth, not only
    its verdict. And the STAMP LANDS BEFORE THE DIGEST — the filename carries a
    hash of the content, so an observation added afterwards would berth under a
    name describing a different artifact."""
    root, val = world
    berth_dir = os.path.join(root, "berthed")
    a = artifact(val)
    path = write_verdict(a, instance_dir=berth_dir, root=root)
    with open(path) as fh:
        berthed = json.load(fh)

    stamp = berthed["observed_runs"]
    assert [o["run"]["command"] for o in stamp] == ["bash proofs/exits.sh 7"]
    assert stamp[0]["run"]["exit"] == 7 and stamp[0]["expect_exit"] == 7
    assert "ran with 7" in stamp[0]["run"]["tail"]
    assert "observed_runs" not in a, "the caller's dict is not mutated"

    import hashlib
    digest = hashlib.sha256(
        json.dumps(berthed, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    assert os.path.basename(path).endswith(digest + ".json"), \
        "the berthed content hashes to the name it berthed under — the stamp is inside it"

    # AND A REFUSED ARTIFACT LEAVES NOTHING BEHIND THE DOOR.
    refusal(lambda: write_verdict(artifact(val, outcome="fail", evidence="3 hits"),
                                  instance_dir=berth_dir, root=root), "reports fail")
    assert len(os.listdir(berth_dir)) == 1


# ── the watch ────────────────────────────────────────────────────────────────

def test_the_probe_is_armed_and_can_be_made_to_fire(world):
    """A PROBE THAT CANNOT BE MADE TO FIRE IS A PROBE NOBODY HAS MEASURED. The
    reading is handed a corpus, so this tooth can hand it one that should fire and
    one that should not, without touching the live berth."""
    from cairn.devices.codemother.machines.verdict.probes import (
        the_instrument_is_re_run_not_reported as probe)

    assert probe.PROBE.carry is not None and probe.PROBE.enough is not None

    quiet = probe.instrument_shape([
        {"instrument": "bash proofs/exits.sh 7", "runnable": True},
        {"instrument": "PYTHONPATH=. python3 -m pytest -q proofs/test_x.py",
         "runnable": True}])
    assert quiet["fires"] is False, quiet

    # THE WRONG-INTENT SHAPE THE TICKET NAMES: instruments collapsed into
    # trivially-green commands, so every re-run agrees by construction.
    loud = probe.instrument_shape([
        {"instrument": "true", "runnable": True},
        {"instrument": "echo ok", "runnable": True},
        {"instrument": "ls", "runnable": True}])
    assert loud["fires"] is True, loud
    assert "trivially" in loud["what"], loud["what"]


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
