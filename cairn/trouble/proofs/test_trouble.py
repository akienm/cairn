"""THE TROUBLE TICKET IS THE DAMPER — raise once, count after, never re-demand attention.

Akien 2026-07-25: "a system alarm is raised. it's not raised again and again, it's count can
increment... but demanding more attention when there is none to give is not productive... we
do need to be able to make a change and clear the current trouble ticket and start fresh. but
once a notifier-ee gets one, it stays live until they clear it. and for now, you get them all."

WHAT THIS PROVES:
  - FIFTY OCCURRENCES, ONE DEMAND FOR ATTENTION. The first raise notifies; every recurrence
    increments and notifies NOBODY. This is the chatter answer, with no width to guess.
  - TRUTH IS NOT DAMPED, ONLY NOTIFICATION (Law 7 both halves). The count is exact, the
    timestamps move, and a bounded tail keeps the SHAPE of the recurrence.
  - ONLY THE RECIPIENT CLEARS. No timeout, no quiet period, no later passing run.
  - A CLEAR MUST NAME A CHANGE. "it stopped happening" is refused.
  - CLEARING IS APPEND, NOT ERASURE. The cleared ticket keeps its whole history.
  - AND THEN IT STARTS FRESH. A recurrence after a clear is a NEW ticket at count 1, carrying
    the fix that did not hold — a failed fix must be visibly a failed fix.
  - NORMAL OPERATING STATE IS ZERO. live() empty is the system working.
  - THE LANE DOES NOT GO DARK ON ITS OWN FAULT. A malformed trouble file surfaces as a live
    trouble, not as silence in the one place built to end silence.

    python3 cairn/trouble/proofs/test_trouble.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cairn.trouble.trouble import CLEARED, LIVE, OCCURRENCE_TAIL, TroubleDevice, TroubleError

IDENT = "append-door-has-no-schema-gate"
WHY = "the single write-door accepts a record no reader can read"


def _dev(tmp):
    return TroubleDevice(root=tmp)


def test_the_first_raise_notifies():
    with tempfile.TemporaryDirectory() as tmp:
        out = _dev(tmp).raise_trouble(IDENT, why=WHY)
    assert out == {"outcome": "raised", "id": IDENT, "count": 1, "notified": ["cc"]}, out


def test_fifty_occurrences_are_one_demand_for_attention():
    """The chatter answer: the count rises, the attention is spent exactly once."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        outs = [d.raise_trouble(IDENT, why=WHY, detail={"n": i}) for i in range(50)]
        notified = [o for o in outs if o["notified"]]
        assert len(notified) == 1 and notified[0]["outcome"] == "raised", \
            f"one ticket, one notification — {len(notified)} notifications"
        assert all(o["outcome"] == "incremented" for o in outs[1:])
        live = d.live()
        assert len(live) == 1, "fifty flaps do not make fifty tickets"
        assert live[0]["count"] == 50, "the count is EXACT — truth is not damped, only noise"


def test_the_recurrence_keeps_its_shape_but_stays_bounded():
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        for i in range(50):
            d.raise_trouble(IDENT, why=WHY, detail={"n": i})
        t = d.live()[0]
    assert len(t["occurrences"]) == OCCURRENCE_TAIL, "a bounded tail — the ticket cannot bloat"
    assert [o["n"] for o in t["occurrences"]] == list(range(40, 50)), "the MOST RECENT ones"
    assert t["first_seen"] <= t["last_seen"], "the span of the recurrence is readable"


def test_normal_operating_state_is_zero():
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        assert d.live() == [] and d.state()["at_normal_operating_state"] is True, \
            "no troubles is the system WORKING, and the device says so in its own state"
        d.raise_trouble(IDENT, why=WHY)
        assert d.state()["at_normal_operating_state"] is False


def test_only_the_recipient_clears_it():
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        d.raise_trouble(IDENT, why=WHY)
        for _ in range(5):
            d.raise_trouble(IDENT, why=WHY)      # time passing, faults recurring
        assert d.live(), "nothing but a recipient's clear takes it off the live list"
        out = d.clear(IDENT, by="cc", what_changed="added a schema gate to append_entry")
        assert out["standing"] == CLEARED
        assert d.live() == [], "and now the lane is quiet again"


def test_a_clear_must_name_what_changed():
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        d.raise_trouble(IDENT, why=WHY)
        try:
            d.clear(IDENT, by="cc", what_changed="")
        except TroubleError as e:
            assert "what_changed" in str(e)
        else:
            raise AssertionError("'it stopped happening' is not a fix and must be refused")
        assert d.live(), "the refused clear left the ticket LIVE — no half-clear"


def test_clearing_something_never_raised_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _dev(tmp).clear("never-happened", by="cc", what_changed="nothing")
        except TroubleError as e:
            assert "never raised" in str(e)
        else:
            raise AssertionError("a clear must not manufacture an all-clear out of nothing")


def test_clearing_is_append_not_erasure():
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        for i in range(3):
            d.raise_trouble(IDENT, why=WHY, detail={"n": i})
        d.clear(IDENT, by="cc", what_changed="added a schema gate")
        t = [x for x in d.all() if x["id"] == IDENT][0]
    assert t["standing"] == CLEARED
    assert t["count"] == 3 and len(t["occurrences"]) == 3, "the whole history survives the clear"
    assert t["resolution"]["what_changed"] == "added a schema gate"
    assert t["resolution"]["at_count"] == 3, "and WHEN it was cleared is on the record"


def test_a_recurrence_after_a_clear_starts_fresh_and_names_the_failed_fix():
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        d.raise_trouble(IDENT, why=WHY)
        d.raise_trouble(IDENT, why=WHY)
        d.clear(IDENT, by="cc", what_changed="a gate I thought was enough")
        out = d.raise_trouble(IDENT, why=WHY)     # it came back
        t = d.live()[0]
    assert out["outcome"] == "raised" and out["notified"] == ["cc"], \
        "a fault after a fix is NEW attention — the fix is the thing now in question"
    assert t["count"] == 1, "start fresh: the count is evidence about THIS attempted fix"
    assert t["recurred_after_clear"]["what_changed"] == "a gate I thought was enough", \
        "a fix that did not hold must be visibly a fix that did not hold"
    assert t["prior_attempts"] == 1


def test_a_trouble_without_a_why_or_an_identity_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        for bad, field in ((dict(identity=IDENT, why=""), "why"),
                           (dict(identity="   ", why=WHY), "identity")):
            try:
                d.raise_trouble(bad["identity"], why=bad["why"])
            except TroubleError as e:
                assert field in str(e), e
            else:
                raise AssertionError(f"a trouble with no {field} must be refused at n=1")


def test_the_lane_does_not_go_dark_on_its_own_malformed_file():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "half-written.json").write_text("{ this is not json", encoding="utf-8")
        live = _dev(tmp).live()
    assert len(live) == 1 and live[0]["unreadable"] is True, \
        "silence about a broken trouble file, in the lane built to end silence, is the worst case"


def test_an_off_template_record_is_never_reported_as_having_no_why():
    """MEASURED 2026-08-12 at session open: the banner printed ``<no why recorded>`` beside
    ``the-runtime-spine-has-never-run`` — the record carrying the FULLEST why in the store
    (opened_by, the_claim_under_test, verdict, method, findings, the_map), all of it under
    names the reader did not know. A presentation surface may collapse an error into a
    coherent shape; it may never MANUFACTURE one, and "nobody wrote a why" is a claim about
    the author, not about the reader's vocabulary (Law 7)."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "spine.json").write_text(json.dumps(
            {"id": "spine", "verdict": "FALSIFIED, and not by a break", "method": "census"}),
            encoding="utf-8")
        got = _dev(tmp).live()
    assert len(got) == 1 and got[0].get("off_template") is True, \
        f"an off-template record must still reach the reader, flagged as one — got {got}"
    why = got[0]["why"]
    assert "OFF-TEMPLATE" in why and "verdict" in why and "method" in why and "spine.json" in why, \
        ("the synthesized why must name the shape, what the record DOES carry, and where to "
         f"read it — an unactionable placeholder is the defect restated — got {why!r}")
    assert "no why" not in why.lower(), \
        "the one thing it must never say is that the why was not recorded"


def test_every_live_trouble_in_the_REAL_store_carries_a_why():
    """LIVE, and stated as an INVARIANT rather than a census: whatever is in the inbox today,
    the lane never hands its reader a trouble it cannot say anything about. Goes red only if
    the reader regresses — not when the inbox changes, and not when it empties."""
    store = Path(__file__).resolve().parents[3].parent / "CairnCommons" / "troubles"
    if not store.exists():                       # commons absent (packaged/foreign box) is not a red
        return
    for t in TroubleDevice(root=store).live():
        why = (t.get("why") or "").strip()
        assert why, f"live trouble {t.get('id')!r} reached the reader with nothing to say"
        assert "no why recorded" not in why.lower(), \
            f"live trouble {t.get('id')!r} renders as an absence claim about its own author"


def test_only_an_explicit_cleared_takes_a_ticket_off_the_live_list():
    """Found on this device's FIRST contact with a real file. The hand-written trouble said
    ``"OPEN — reported complete, awaiting Akien's ratify"``; an equality test on LIVE reported
    ZERO troubles with an open one on disk — the silent failure the lane exists to end."""
    with tempfile.TemporaryDirectory() as tmp:
        for name, standing in (("prose", "OPEN — awaiting ratify"), ("typo", "open"),
                               ("absent", None), ("gone", CLEARED)):
            t = {"id": name, "count": 1, "why": "x"}
            if standing is not None:
                t["standing"] = standing
            (Path(tmp) / f"{name}.json").write_text(json.dumps(t), encoding="utf-8")
        live = {t["id"] for t in _dev(tmp).live()}
    assert live == {"prose", "typo", "absent"}, \
        f"only an explicit CLEARED is quiet; everything else demands attention — got {live}"


def test_a_near_miss_standing_increments_rather_than_being_overwritten():
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / f"{IDENT}.json").write_text(json.dumps(
            {"id": IDENT, "standing": "OPEN — awaiting ratify", "count": 4, "why": WHY}),
            encoding="utf-8")
        out = _dev(tmp).raise_trouble(IDENT, why=WHY)
    assert out == {"outcome": "incremented", "id": IDENT, "count": 5, "notified": []}, \
        "a near-miss standing must not silently reset a real ticket's history to count 1"


def test_two_recipients_hold_it_live_until_both_clear():
    """The shape already admits the help Akien expects later — a second name, not a redesign."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        d.raise_trouble(IDENT, why=WHY, recipients=["cc", "akien"])
        first = d.clear(IDENT, by="cc", what_changed="patched it")
        assert first["outcome"] == "partially_cleared" and first["outstanding"] == ["akien"]
        assert d.live(), "it stays live for whoever has not cleared it"
        assert d.clear(IDENT, by="akien", what_changed="reviewed and agreed")["standing"] == CLEARED
        assert d.live() == []


def test_the_ticket_on_disk_is_plain_readable_json():
    with tempfile.TemporaryDirectory() as tmp:
        _dev(tmp).raise_trouble(IDENT, why=WHY, detail={"location": "projector.py:112"})
        raw = json.loads((Path(tmp) / f"{IDENT}.json").read_text())
    assert raw["standing"] == LIVE and raw["why"] == WHY
    assert raw["occurrences"][0]["location"] == "projector.py:112", \
        "the occurrence's own detail rides on the ticket — complete on the first pass"


def test_the_crossings_are_no_longer_silent():
    """The silent_device disposition (troubles/silent-devices-2026-07-27.json): the lane's
    crossings are its three door-acts — raise, increment, clear — each a durable write.
    The damper rations NOTIFICATION; a held breadcrumb is a record, not a demand for
    attention, so increments breadcrumb too (Law 7, both halves). Reads emit nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        assert d.held_diagnostics() == [], "construction is not a crossing"
        d.raise_trouble(IDENT, why=WHY)
        d.raise_trouble(IDENT, why=WHY)          # the damped occurrence STILL breadcrumbs
        d.live(), d.all(), d.state()             # reads are not crossings
        d.clear(IDENT, by="cc", what_changed="fixed it")
        held = d.held_diagnostics()
        assert [h["gate"] for h in held] == ["raise_trouble", "raise_trouble", "clear"], (
            f"three door-acts, three breadcrumbs, got {[h['gate'] for h in held]} — "
            "reads must add none"
        )
        assert held[0]["values"] == {"outcome": "raised", "count": 1}
        assert held[1]["values"] == {"outcome": "incremented", "count": 2}, \
            "the increment is damped as a NOTIFICATION, not as a record — it still breadcrumbs"
        assert held[2]["values"] == {"outcome": "cleared", "standing": CLEARED}
        assert all(h["pointer"] == IDENT for h in held), \
            "every breadcrumb points at the ticket — the record of truth on disk"
        assert all(h["home"] == "held" for h in held), \
            "with no receiver wired the records HOLD (Law 7) — never silently dropped"


# DERIVED, NOT TYPED OUT (2026-08-12). This was a hand-written roster of sixteen names, and
# it caught its author the same hour: two new teeth were added above, the file printed
# "16/16 green", and NEITHER NEW TOOTH HAD RUN. A hand roster beside the thing it lists is a
# proxy for "every test in this module" that goes stale silently and in the safe-looking
# direction — the proof gets greener, never redder. Same shape as the inspector's import
# allowlist one directory over: a property typed out longhand. Ten other proof files in the
# corpus still carry one; that is a corpus-wide finding, not ten quiet edits, and it is owed.
TESTS = [fn for name, fn in sorted(globals().items())
         if name.startswith("test_") and callable(fn)]

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
