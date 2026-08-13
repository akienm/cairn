"""Proof: the WATCHME spec is MANDATORY TO SATISFY ONCE CARRIED — and retro-reds nobody.

Ticket ``watchme-emits-a-probe`` (2026-07-30), triage position 5, piece (c-ii). Akien's rule
has two halves and the second is the one that usually goes missing: optional to carry,
MANDATORY TO SATISFY once carried, with "none, because X" as the only other legal answer.
Silence is not an answer — that is the whole difference between an author who considered
efficacy and one who skipped the question.

THE FALSIFIER THIS PROOF IS BUILT AROUND, verbatim from the ticket: *the check RETRO-REDS
pre-existing cast tickets — i.e. it fires on tickets written before the rule existed. That is
the promotion-filter jurisdiction failure the entry-gate stone already paid for once, and it
would make every open boat un-crossable.* So the instrument is not a fixture: it is
``sweep()`` over the REAL ``CairnCommons/tickets/``, and the ticket's own stated instrument
adds the teeth that matter — *a pass must be by a STATED rule, not incidental*.

IT ALREADY FIRED ONCE, and the record stands: the first sweep RED three tickets
(cc-learning-store, learning-as-a-pattern, default-superclaude-to-200k — 2026-07-15/16, whose
``state`` is a bare word like 'building' because they predate workflow strings). That is the
falsifier landing on the first run. The fix was jurisdictional, not a grandfather list: a
state that names no version claims none, so the obligation cannot attach — and deciding
malformedness at all was a second opinion about a question the parser owns (Law 6).

HOW THE PASS IS SHOWN TO BE NON-INCIDENTAL — ``test_the_clean_sweep_is_not_a_vacuous_check``.
Fifty-seven green could mean the rule holds, or it could mean the rule never fires. The row
takes the REAL tickets, retags each to v2 (the one thing the stated exemption turns on), and
demands the sweep go RED — so the clean sweep is caused by the version rule and by nothing
else. A check that passes everything is not a check.

    python3 cairn/tools/base/proofs/test_watchme_spec.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import watchme_spec as ws

_V1 = "code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"
_V2_BARE = "code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> PROVED"
_V2_WATCH = ("code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> "
             "WATCHME(does-the-emission-gate-fire-in-anger) -> PROVED")
_V2_TWO = ("code-seam@v2: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> "
           "WATCHME(does-the-gate-fire) -> WATCHME(does-anyone-read-the-verdict) -> PROVED")


def _spec(obj, **over):
    s = {"object": obj,
         "trigger": "a forward crossing out of WATCHME is attempted",
         "enough": "three journaled crossings, or the ticket's horizon passes",
         "carrier": "a verdict artifact against the ticket's falsifier",
         "nexus": "hypothesize",
         "consumer": "the owner, who back-edges on a failed verdict",
         "probe": "cairn/tools/base/probes/does_the_emission_gate_fire.py"}
    s.update(over)
    return s


def test_a_v1_ticket_is_exempt_by_the_version_rule():
    assert ws.watchme_spec_error({"state": _V1}) is None, \
        "v1's vocabulary has no WATCHME, so the obligation cannot attach — this is the rule " \
        "that keeps every open boat crossable"


def test_a_pre_workflow_string_ticket_is_exempt_too():
    """The three that RED on the first real sweep. A bare word claims no version at all."""
    for state in ("building", "validated", ""):
        assert ws.watchme_spec_error({"state": state}) is None, state
    assert ws.watchme_spec_error({}) is None, "a ticket with no state field is not this " \
        "module's verdict to give either"


def test_a_v2_ticket_that_carries_no_watch_must_say_none_because():
    err = ws.watchme_spec_error({"state": _V2_BARE})
    assert err and "none, because" in err, err
    assert ws.watchme_spec_error(
        {"state": _V2_BARE, "watchme": "none, because this seam has no efficacy question a "
                                       "probe could answer — its proof IS the measure"}) is None
    assert ws.watchme_spec_error({"state": _V2_BARE, "watchme": "none"}), \
        "'none' without a because is the silence the rule exists to refuse"


def test_a_carried_watch_with_a_complete_spec_passes():
    t = {"state": _V2_WATCH,
         "watchme": [_spec("does-the-emission-gate-fire-in-anger")]}
    assert ws.watchme_spec_error(t) is None, ws.watchme_spec_error(t)


def test_a_carried_watch_with_no_spec_is_refused():
    err = ws.watchme_spec_error({"state": _V2_WATCH})
    assert "mandatory to satisfy once carried" in err, err
    assert "does-the-emission-gate-fire-in-anger" in err, \
        "the refusal names WHICH watch is unspecified — a refusal you must go looking for is " \
        "half a refusal (Law 7)"


def test_a_missing_field_is_named_and_so_is_every_other_one():
    """Complete diagnostic on the FIRST pass — never re-run the check to find the next fault."""
    bad = _spec("does-the-emission-gate-fire-in-anger", nexus="", consumer=None)
    del bad["enough"]
    err = ws.watchme_spec_error({"state": _V2_WATCH, "watchme": [bad]})
    for field in ("enough", "nexus", "consumer"):
        assert field in err, f"{field} missing from {err!r}"
    assert "trigger" not in err.split("the five are")[0], \
        "a field that IS filled must not be reported as missing"


def test_a_spec_with_no_berth_cannot_be_gated():
    bad = _spec("does-the-emission-gate-fire-in-anger")
    del bad["probe"]
    err = ws.watchme_spec_error({"state": _V2_WATCH, "watchme": [bad]})
    assert "probe" in err and "path" in err, err


def test_two_watches_need_two_specs_joined_by_object():
    one = {"state": _V2_TWO, "watchme": [_spec("does-the-gate-fire")]}
    err = ws.watchme_spec_error(one)
    assert "does-anyone-read-the-verdict" in err and "does-the-gate-fire" not in err, err
    both = {"state": _V2_TWO,
            "watchme": [_spec("does-the-gate-fire"), _spec("does-anyone-read-the-verdict")]}
    assert ws.watchme_spec_error(both) is None, ws.watchme_spec_error(both)


def test_a_spec_cannot_drift_onto_a_watch_the_node_does_not_carry():
    """The other direction. Checking only one side lets the pair rot in the unchecked half."""
    t = {"state": _V2_WATCH,
         "watchme": [_spec("does-the-emission-gate-fire-in-anger"),
                     _spec("something-nobody-is-watching")]}
    err = ws.watchme_spec_error(t)
    assert "something-nobody-is-watching" in err and "drift" in err, err


def test_a_spec_that_names_no_object_describes_nothing():
    nameless = _spec("x")
    del nameless["object"]
    err = ws.watchme_spec_error({"state": _V2_WATCH, "watchme": [nameless]})
    assert "join key" in err, err
    dupes = {"state": _V2_WATCH,
             "watchme": [_spec("does-the-emission-gate-fire-in-anger"),
                         _spec("does-the-emission-gate-fire-in-anger", nexus="triage")]}
    assert "exactly one spec" in ws.watchme_spec_error(dupes)


def test_a_lone_dict_is_read_as_one_spec():
    t = {"state": _V2_WATCH, "watchme": _spec("does-the-emission-gate-fire-in-anger")}
    assert ws.watchme_spec_error(t) is None, \
        "the single-watch case is the common one — it must not require list ceremony"


def test_the_real_ticket_corpus_is_not_retro_redded():
    """THE FALSIFIER'S OWN INSTRUMENT — the real CairnCommons/tickets/, not a fixture."""
    rows = ws.sweep()
    assert len(rows) > 40, f"the sweep found only {len(rows)} tickets — it is not reading the " \
                           "real corpus"
    red = [r for r in rows if r["error"]]
    assert not red, "retro-red on pre-existing cast tickets: " + \
                    "; ".join(f"{r['ticket']}: {r['error']}" for r in red)


def test_the_clean_sweep_is_not_a_vacuous_check():
    """A clean sweep proves the rule holds OR that it never fires. This row separates them by
    REMOVING the exemption from real ticket bodies and demanding the same sweep go loudly RED.

    THE MECHANISM CHANGED 2026-08-03 BECAUSE ITS FIXTURE DID. This row used to retag the real
    ``@v1`` tickets to v2 — which worked only while v1 tickets existed on disk. Akien's scrub
    sweep migrated the last of them, so the old row retagged NOTHING and went red announcing
    "the rule bit only 0 tickets": a non-vacuity check that had itself gone vacuous.

    What it turns on now is what the exemption turns on now: a v2 claim the ticketer COMPOSED
    versus one a sweep APPLIED. So take the real v2 bodies, strip ``migrated_from`` (present
    them as authored), drop any ``watchme`` answer, and the rule must bite. Same claim as
    before — the clean sweep is caused by the stated exemptions and by nothing else — read
    against the corpus as it actually is."""
    import json

    bit, exempt = 0, 0
    for p in sorted(ws._TICKETS.glob("*.json")):
        if p.name.startswith("_"):
            continue
        t = json.loads(p.read_text(encoding="utf-8"))
        state = t.get("state")
        if not (isinstance(state, str) and "@v2:" in state) or "WATCHME" in state:
            exempt += 1
            continue
        t.pop("migrated_from", None)      # present it as an AUTHORED v2 claim
        t.pop("watchme", None)            # and as one whose author answered nothing
        if ws.watchme_spec_error(t):
            bit += 1
    assert bit > 20, f"stripped to an authored v2 claim the rule bit only {bit} tickets — a " \
                     f"check that passes everything is not a check ({exempt} carried no " \
                     f"parseable v2 claim, or carried a watch)"


def test_a_swept_version_claim_is_exempt_but_an_authored_one_is_not():
    """THE NEW EXEMPTION, both directions, on one body. A ticket whose v2 claim was applied by
    a sweep (``migrated_from``) owes nothing: nobody asked its author. The SAME ticket without
    that field owes the answer. One field is the whole difference, which is what makes this a
    stated rule rather than a grandfather list."""
    swept = {"state": _V2_BARE, "migrated_from": "code-seam@v1 — swept 2026-08-03"}
    assert ws.watchme_spec_error(swept) is None, \
        "a swept version claim retro-imposed a ticketing-time obligation on an absent author"

    authored = {"state": _V2_BARE}
    err = ws.watchme_spec_error(authored)
    assert err and "none, because" in err, \
        f"an AUTHORED v2 claim with no answer must still be refused — the exemption widened " \
        f"past its stated rule (got: {err!r})"


TESTS = [
    test_a_v1_ticket_is_exempt_by_the_version_rule,
    test_a_pre_workflow_string_ticket_is_exempt_too,
    test_a_v2_ticket_that_carries_no_watch_must_say_none_because,
    test_a_carried_watch_with_a_complete_spec_passes,
    test_a_carried_watch_with_no_spec_is_refused,
    test_a_missing_field_is_named_and_so_is_every_other_one,
    test_a_spec_with_no_berth_cannot_be_gated,
    test_two_watches_need_two_specs_joined_by_object,
    test_a_spec_cannot_drift_onto_a_watch_the_node_does_not_carry,
    test_a_spec_that_names_no_object_describes_nothing,
    test_a_lone_dict_is_read_as_one_spec,
    test_the_real_ticket_corpus_is_not_retro_redded,
    test_the_clean_sweep_is_not_a_vacuous_check,
    test_a_swept_version_claim_is_exempt_but_an_authored_one_is_not,
]

if __name__ == "__main__":
    failures = 0
    for t in TESTS:
        try:
            t()
            print(f"  ok   {t.__name__}")
        except AssertionError as e:
            failures += 1
            print(f"  FAIL {t.__name__}: {e}")
    print(f"\n{len(TESTS) - failures}/{len(TESTS)} green")
    sys.exit(1 if failures else 0)
