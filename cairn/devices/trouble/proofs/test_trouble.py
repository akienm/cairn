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

    python3 cairn/devices/trouble/proofs/test_trouble.py     # exit 0 = green
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

from cairn.devices.trouble.trouble import CLEARED, LIVE, OCCURRENCE_TAIL, TroubleDevice, TroubleError

# WHICH TICKET CLAUSES THESE TEETH COVER (read by cairn/tools/proof_coverage, ticket
# feeb4c786b14). A pointer INTO the falsifier, never a second copy of it: the clause text
# lives on the ticket, and duplicating it here would give a reader two versions to reconcile.
# Clauses (3) and (5) are served in other proofs — see the ticket's crossing, which names
# all of them, because this ticket's subject is a SEAM and a seam has ends in more than one
# component.
PROVES = {
    "9579a6f9cec6": {
        "1": "test_the_isolation_sieve_reports_nothing_over_the_live_tree",
        "2": "test_no_device_reaches_this_one_by_import",
        # CLAUSE (2) HAS TWO TEETH because the clause has two halves the same string-grep
        # cannot hold: the direct path, and the one-hop re-export the ticket DELETED and
        # nothing guarded. The suffixed key is how one clause names both — the reader maps
        # key -> ONE tooth, and collapsing them would drop whichever came second.
        "2b": "test_the_holding_class_is_not_re_exported_from_anywhere_outside_this_device",
        "4": "test_two_processes_raising_ONE_identity_fold_to_ONE_ticket",
        "6": "test_the_inspector_troubles_were_cleared_through_the_door",
    }
}

IDENT = "append-door-has-no-schema-gate"
WHY = "the single write-door accepts a record no reader can read"


def _dev(tmp):
    dev = TroubleDevice(root=tmp)
    # SILENCED (ticket a-device-logs-without-being-wired, 2026-08-18): an un-wired device now
    # writes its trail to ~/.cairn/logs/trouble/0/ instead of holding. ``tmp`` here is the
    # TROUBLE STORE's root, not the roots table — it redirects the store and not the trail — so
    # silencing is what keeps this proof out of the live logs tree, and what keeps the held list
    # its breadcrumb tooth reads from going empty.
    dev.set_diagnostic_receiver(None)
    return dev


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


def test_an_off_template_record_can_still_leave_through_the_door():
    """MEASURED 2026-08-15: clear() read ``ticket["count"]`` and a pre-template record carries
    no count — so the one record live() was explicitly built to keep visible was a record its
    own door could never release. The lane's tolerance must be two-sided: reachable by the
    reader AND clearable by the recipient. ``at_count`` on such a clear is honestly null
    (unknown), never 0 (a measurement nobody took)."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "spine.json").write_text(json.dumps(
            {"id": "spine", "verdict": "FALSIFIED", "method": "census"}), encoding="utf-8")
        dev = _dev(tmp)
        got = dev.clear("spine", by="cc", what_changed="the claim under test is now false")
        assert got["outcome"] == "cleared" and got["standing"] == CLEARED, \
            f"an off-template record with nobody notified must clear whole — got {got}"
        on_disk = json.loads((Path(tmp) / "spine.json").read_text(encoding="utf-8"))
    assert on_disk["standing"] == CLEARED and on_disk["cleared_by"][0]["at_count"] is None, \
        f"the clear must land on disk with at_count null, not a manufactured count — got {on_disk}"
    assert on_disk["verdict"] == "FALSIFIED", "clearing is append — the record's own fields survive"


def test_every_live_trouble_in_the_REAL_store_carries_a_why():
    """LIVE, and stated as an INVARIANT rather than a census: whatever is in the inbox today,
    the lane never hands its reader a trouble it cannot say anything about. Goes red only if
    the reader regresses — not when the inbox changes, and not when it empties."""
    store = Path(__file__).resolve().parents[4].parent / "CairnCommons" / "troubles"
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


def test_an_amendment_appends_a_correction_beside_the_false_statement():
    """Law 7: the false statement stays permanent; the correction stands beside it so a reader
    of the original sees both. NOT a second clear — standing is untouched."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        d.raise_trouble(IDENT, why=WHY)
        d.clear(IDENT, by="cc", what_changed="patched the gate — or so I thought")
        out = d.amend(IDENT, by="cc",
                      correction="the gate was already patched since 2026-08-16; "
                                 "the clear's claim of NOT DONE is false")
        assert out["outcome"] == "amended"
        assert out["standing"] == CLEARED, "an amendment does NOT change standing"
        on_disk = json.loads((Path(tmp) / f"{IDENT}.json").read_text(encoding="utf-8"))
        assert len(on_disk["cleared_by"]) == 2, "the original clear + the amendment"
        original = on_disk["cleared_by"][0]
        amendment = on_disk["cleared_by"][1]
        assert "amendment" not in original, "the original clear is untouched"
        assert amendment["amendment"] is True
        assert amendment["correction"].startswith("the gate was already patched")
        assert amendment["by"] == "cc"
        assert "at" in amendment


def test_an_amendment_on_a_nonexistent_ticket_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        try:
            _dev(tmp).amend("ghost", by="cc", correction="fixing nothing")
        except TroubleError as e:
            assert "no trouble" in str(e)
        else:
            raise AssertionError("amending a nonexistent ticket must be refused")


def test_an_amendment_without_a_cleared_by_entry_is_refused():
    """Amending a record that was never cleared is amending nothing."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        d.raise_trouble(IDENT, why=WHY)
        try:
            d.amend(IDENT, by="cc", correction="correcting a clear that never happened")
        except TroubleError as e:
            assert "no cleared_by" in str(e)
        else:
            raise AssertionError("a correction without an original is not an amendment")


def test_an_empty_correction_is_refused():
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        d.raise_trouble(IDENT, why=WHY)
        d.clear(IDENT, by="cc", what_changed="something")
        try:
            d.amend(IDENT, by="cc", correction="")
        except TroubleError as e:
            assert "empty correction" in str(e)
        else:
            raise AssertionError("a change that says nothing changed is not an amendment")


def test_an_amendment_does_not_change_standing():
    """The amendment is append-only context, not a state transition."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        d.raise_trouble(IDENT, why=WHY)
        d.clear(IDENT, by="cc", what_changed="fixed")
        assert d.live() == [], "cleared"
        d.amend(IDENT, by="cc", correction="the fix claim was wrong")
        assert d.live() == [], "still cleared — an amendment is NOT a re-open"
        on_disk = json.loads((Path(tmp) / f"{IDENT}.json").read_text(encoding="utf-8"))
        assert on_disk["standing"] == CLEARED


def test_an_amendment_emits_a_breadcrumb():
    """The amendment is a door-act and a durable write — it breadcrumbs (Law 7)."""
    with tempfile.TemporaryDirectory() as tmp:
        d = _dev(tmp)
        d.raise_trouble(IDENT, why=WHY)
        d.clear(IDENT, by="cc", what_changed="fixed")
        d.amend(IDENT, by="cc", correction="that clear was wrong")
        held = d.held_diagnostics()
        amend_crumbs = [h for h in held if h["gate"] == "amend"]
        assert len(amend_crumbs) == 1
        assert amend_crumbs[0]["values"]["outcome"] == "amended"
        assert amend_crumbs[0]["pointer"] == IDENT


# ── the drain: raises from processes that never held this device ────────────────────────

def _raise_in_a_separate_process(world: Path, component: str, identity: str, why: str) -> None:
    """Fire one raise from a process that has never imported ``cairn.devices``.

    A SEPARATE PROCESS IS THE POINT, not test hygiene. The whole claim of ticket
    9579a6f9cec6 is that a raiser needs no running lane and no shared object — so a fold
    proved by two calls on one in-memory device would be proving the wrong thing entirely.
    Two processes that exit before the drain ever starts is the real shape: nothing is
    passed between them but files on disk."""
    script = f'''
import sys; sys.path.insert(0, {str(Path(__file__).resolve().parents[4])!r})
from pathlib import Path
from cairn.tools.base.diagnostic import ModuleRaiser
ModuleRaiser({component!r}, roots={{k: Path({str(world)!r}) for k in ("repo","commons","instance")}}
             ).raise_trouble({identity!r}, why={why!r})
'''
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                         timeout=120)
    assert out.returncode == 0, out.stderr


def test_two_processes_raising_ONE_identity_fold_to_ONE_ticket():
    """THE END-TO-END TOOTH (ticket 9579a6f9cec6, falsifier 4). Two components, two
    processes, neither holding this device — and what the operator meets is ONE ticket
    counting two, not two tickets of one.

    This is the damping proved across the seam rather than inside it. The in-process
    version above (``test_fifty_occurrences_are_one_demand_for_attention``) proves the
    device folds what it is handed; this proves the DRAIN hands it the right thing —
    that a breadcrumb written by a stranger arrives at ``raise_trouble`` with its identity
    intact. An identity mangled anywhere along that path turns fifty flaps into fifty
    tickets, which is the failure the whole lane exists to prevent, and it would be
    invisible to every tooth on either side of the drain alone."""
    from cairn.devices.trouble.shim import TroubleShim

    with tempfile.TemporaryDirectory() as tmp:
        world = Path(tmp) / "world"
        store = Path(tmp) / "store"
        _raise_in_a_separate_process(world, "build_inspector", IDENT, WHY)
        _raise_in_a_separate_process(world, "tester", IDENT, WHY)

        roots = {k: world for k in ("repo", "commons", "instance")}
        drained = TroubleShim(roots=roots, root=str(store)).drain()
        assert drained["outcome"] == "ok", drained
        assert drained.get("refused", []) == [], drained
        assert len(drained["folded"]) == 2, drained

        live = _dev_at(store).live()
        assert len(live) == 1, [t["id"] for t in live]
        assert live[0]["id"] == IDENT
        assert live[0]["count"] == 2, live[0]


def test_a_SECOND_drain_does_not_re_fold_what_it_already_folded():
    """The watermark, from the operator's side. Without it every beat would re-read every
    breadcrumb a device ever wrote and the count would climb forever with nothing wrong —
    a number that grows on its own is worse than no number, because it looks like evidence."""
    from cairn.devices.trouble.shim import TroubleShim

    with tempfile.TemporaryDirectory() as tmp:
        world = Path(tmp) / "world"
        store = Path(tmp) / "store"
        _raise_in_a_separate_process(world, "build_inspector", IDENT, WHY)

        roots = {k: world for k in ("repo", "commons", "instance")}
        shim = TroubleShim(roots=roots, root=str(store))
        shim.drain()
        second = shim.drain()

        assert _dev_at(store).live()[0]["count"] == 1, "the drain re-folded a breadcrumb"
        assert second["folded"] == [], second


def test_the_isolation_sieve_reports_nothing_over_the_live_tree():
    """CLAUSE (1) OF 9579a6f9cec6, and it is a live-corpus tooth on purpose. The claim is
    not that the sieve works — the inspector's own proofs own that — it is that the tree it
    reads over is CLEAN, which is a fact about this repo today and can only be measured
    here. The tooth is the invariant, not a count: zero findings, whatever the census size.

    IT ASKS THE SIEVE, NOT THE WHOLE NEST — and the difference was 35 SECONDS, measured
    2026-09-09. This tooth used to call ``inspect()``, which shakes EVERY sieve over EVERY
    census row, and then threw away everything whose method did not contain "isolation".
    That is Law 1 at its plainest: ~20 settled answers re-derived to read one. Timed over
    the live tree on this box: the full shake 44.40s, the census plus this one sieve 9.45s
    (0.71s + 8.69s), 54 rows and 0 findings BOTH ways. 44.40s of a 45.41s proof file — the
    other 36 teeth cost 1.0s between them — so this single call WAS test_trouble.py's cost.
    It was also, transitively, the cost of ``cairn test --hollow``: that verb re-runs each
    named proof once per reverted file, and on ticket 9579a6f9cec6 nine passes over this
    file put the run at 364-417s against d0f2b03952e3's own five-minute WRONG INTENT bound.
    Its falsifier guessed the loop was to blame and prescribed one shared worktree and one
    shared instance swap; the verb already did both, and the measurement named this line
    instead. So the bound fired correctly and pointed somewhere its author did not expect.

    THE ANSWER IS THE SAME ANSWER, not a cheaper approximation, and that is checkable
    rather than asserted: ``inspect()`` reaches the sieve through ``SIEVES[name](row,
    root / row["dir"])`` over exactly ``device_census(root=root)["measured"]["components"]``,
    which is what the loop below is. ``device_isolation_holds`` is the only member of the
    nest whose name carries "isolation", so the old filter selected precisely this sieve's
    findings and nothing else. The one behavioural difference is in the honest direction: a
    sieve that RAISES is wrapped by the nest into an "unreadable" finding, and here it
    propagates — a measurement that could not be taken stops being reported as clean (Law 7).

    NOT FIXED BY GIVING ``inspect()`` A ``sieves=`` ARGUMENT, though that is the shape the
    beat's own tail wants (trouble beat-tail-re-walks-corpora-no-sieve-counts). A partial
    shake returns a partial GRADATION, and what a score of "min() over the sieves we felt
    like running" means is a real question about the nest's contract, owned by
    build_inspector and not settleable from inside a consumer's proof. A caller that wants
    one sieve's findings can compose the sieve; that needs no new contract.
        -> trouble beat-tail-re-walks-corpora-no-sieve-counts
    """
    from cairn.machines.build_inspector.inspector import (
        device_census, device_isolation_holds, _REPO_ROOT)

    root = _REPO_ROOT / "cairn"
    findings = []
    for row in device_census(root=root)["measured"]["components"]:
        for f in device_isolation_holds(row, root / row["dir"]):
            f["at"] = row["dir"]
            findings.append(f)
    assert findings == [], (
        "a device imports another device — the seam this ticket closed has re-opened: "
        + "; ".join(f"{f.get('component')}: {f.get('about')}" for f in findings[:5]))


def test_no_device_reaches_this_one_by_import():
    """CLAUSE (2). The sieve above is the physics; this is the same question asked of the
    text, because the two can disagree — a sieve with an allowlist reports clean about
    exactly the imports its allowlist forgives, and reading the tree independently is what
    makes that forgiveness visible instead of invisible.

    THE ALLOWED HOMES ARE THREE SHAPES, and each is a different reason:
      - under cairn/devices/trouble/ — the device itself;
      - a TOOL (cairn/tools/...) — operator_inbox reads the store; tools may import devices,
        devices may not import each other, and that asymmetry is the isolation rule;
      - a PROOF or PROBE — an instrument reads what it measures, and an instrument that
        had to go through the bus to observe the bus would be measuring its own transport.
    Any other importer is the defect, and it is named rather than counted."""
    root = Path(__file__).resolve().parents[4] / "cairn"
    offenders = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root.parent).as_posix()
        if rel.startswith("cairn/devices/trouble/"):
            continue
        if "cairn.devices.trouble" not in path.read_text(encoding="utf-8", errors="replace"):
            continue
        if rel.startswith("cairn/tools/") or "/proofs/" in rel or "/probes/" in rel:
            continue
        offenders.append(rel)
    assert offenders == [], (
        "these reach the trouble device by import instead of over the bus: " + str(offenders))


def test_the_holding_class_is_not_re_exported_from_anywhere_outside_this_device():
    """CLAUSE (2) AGAIN, ONE HOP OUT — and the tooth exists because the hollow verb found the
    hole on 2026-09-09, not because anyone reasoned their way to it.

    THE SIBLING TOOTH ABOVE READS FOR THE STRING ``cairn.devices.trouble``, so it goes quiet
    the moment somebody reaches the same class by a DIFFERENT name. That is not hypothetical:
    ``cairn/tools/trouble.py`` was exactly that module, its whole body re-exported
    ``TroubleDevice``, and 9579a6f9cec6 DELETED it for the stated reason that it "moved the
    import one hop and satisfied grep rather than physics (Law 4)". The deletion shipped; the
    tooth guarding it did not. So the seam was one re-export away from re-opening with every
    check in the system still green — which is Law 8's hollow shape, in the ticket that was
    supposed to close it.

    HOW IT SURFACED, and it is the point worth keeping: ``cairn test --hollow 9579a6f9cec6``
    reverted ``cairn/devices/tester/validation_store.py`` — whose change under that ticket was
    precisely swapping ``from cairn.tools.trouble import TroubleDevice`` for a ``ModuleRaiser``
    and a bus request — and NO declared tooth redded. HOLLOW, measured, on an instrument built
    to ask that question. The file's contribution to that ticket was unproven for two days.

    IT READS IMPORTS, NOT TEXT. ``TroubleDevice`` appears in a dozen comments and docstrings
    across the corpus (this device's history is written down beside the code that changed), and
    a grep tooth would either drown in those or be tuned until it stopped biting. The AST sees
    only what actually BINDS the name, which is the only thing that can reach the store.

    THE ALLOWED HOMES ARE THE SAME THREE SHAPES as the sibling tooth, for the same three
    reasons — the device itself, a TOOL, or an instrument (proof/probe). Any other binder is
    the defect, by whatever path it spelled it.
    """
    import ast

    root = Path(__file__).resolve().parents[4] / "cairn"
    offenders = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root.parent).as_posix()
        if rel.startswith("cairn/devices/trouble/"):
            continue
        if rel.startswith("cairn/tools/") or "/proofs/" in rel or "/probes/" in rel:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        if "TroubleDevice" not in text and "trouble" not in text:
            continue
        try:
            tree = ast.parse(text)
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = [a.name for a in node.names]
                if "TroubleDevice" in names or (node.module or "").endswith(".trouble"):
                    offenders.append(f"{rel}:{node.lineno} from {node.module} import "
                                     f"{', '.join(names)}")
            elif isinstance(node, ast.Import):
                for a in node.names:
                    if a.name.endswith(".trouble") or a.name.split(".")[-1] == "trouble":
                        offenders.append(f"{rel}:{node.lineno} import {a.name}")
    assert offenders == [], (
        "these BIND the trouble-holding class outside the device that owns it — by whatever "
        "name they spelled it, which is the hole a string-grep leaves open: " + str(offenders))


def _live_commons() -> Path:
    """The operator's CairnCommons — resolved so this proof is WORKTREE-PORTABLE.

    MEASURED 2026-09-09 (ticket d0f2b03952e3, the hollow verb's first live fire): this proof
    read 37/37 green in the live tree and 36/37 inside a scratch worktree, the one red being
    ``test_the_inspector_troubles_were_cleared_through_the_door``. The cause was
    ``parents[4].parent / "CairnCommons"`` — the repo root's SIBLING. A worktree is a checkout
    of this repo at another path, so from ``/tmp/cairn-hollow-xxx/worktree`` that expression
    names ``/tmp/cairn-hollow-xxx/CairnCommons``, which does not exist. The tooth then read
    "the inspector isolation troubles are gone" and failed, and because a declared tooth that
    is not green at HEAD makes every reversion reading unattributable, the whole hollow
    measurement of ticket 9579a6f9cec6 refused with ``HollowUnmeasurable``. FOUR of that
    ticket's FIVE declared teeth live in this file, so one unportable path was hiding 80% of
    the only coverage evidence 9579 has.

    WHY GIT'S COMMON DIR AND NOT AN ENV VAR OR ``cairnmap.commons_root()``. What this tooth
    reads is a HISTORICAL RECORD in the operator's real commons — the evidence that two
    troubles were cleared through the door, which is not a function of which checkout is
    running. So the resolution must name the MAIN working tree from wherever it stands, and
    git already knows: ``--git-common-dir`` is the shared ``.git`` of the repo and every
    worktree of it, so its parent is the real repo root from both. Measured: identical
    absolute answer from the live tree and from a detached worktree.
    ``cairnmap.commons_root()`` would NOT have fixed this — it derives from ``__file__`` the
    same way and carries the same bug; that is a shared tool with its own proofs and its own
    ticket, and widening it from here is the shape Law 8 refuses.
        -> ticket the-canonical-roots-resolver-is-not-worktree-portable
    """
    common = subprocess.run(
        ["git", "-C", str(Path(__file__).resolve().parent),
         "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True)
    if common.returncode == 0 and common.stdout.strip():
        return Path(common.stdout.strip()).parent.parent / "CairnCommons"
    # NOT A SILENT FALLBACK: outside a git checkout there is no main tree to name, and the
    # sibling guess is the honest best effort — the assertion below then fails LOUDLY naming
    # the path it looked in, which is the behaviour that surfaced this bug in the first place.
    return Path(__file__).resolve().parents[4].parent / "CairnCommons"


def test_the_inspector_troubles_were_cleared_through_the_door():
    """CLAUSE (6): cleared by reconcile through ``clear``, NOT BY HAND — and the difference
    is readable on disk, which is the only reason this is a tooth rather than a promise. A
    hand edit sets standing to CLEARED and stops there. The door cannot: it writes a
    ``cleared_by`` entry carrying who, when, WHAT CHANGED — a clear that names no change is
    refused, which is a tooth of its own above — and ``at_count``, the occurrence count at
    the moment of clearing. ``at_count`` is the tell that cannot be faked casually: it is a
    number only the door is holding when it writes, and a hand editor setting a field would
    have to go read the count and copy it deliberately. And ``what_changed`` names RECONCILE
    specifically, which is the clause's other half."""
    troubles = _live_commons() / "troubles"
    seen = sorted(troubles.glob("*device-isolation*.json"))
    assert seen, f"the inspector isolation troubles are gone from {troubles} — the record " \
                 f"of the clearing is the evidence, and it may not be deleted (Law 7)"
    for path in seen:
        rec = json.loads(path.read_text(encoding="utf-8"))
        assert rec.get("standing") == CLEARED, f"{path.name} still stands {rec.get('standing')}"
        marks = rec.get("cleared_by") or []
        assert marks, (f"{path.name} reads CLEARED with no cleared_by — the mark of a hand "
                       f"edit, because the door writes the clearer in the same act")
        last = marks[-1]
        assert last.get("by") and last.get("at"), f"{path.name}: {last}"
        assert isinstance(last.get("at_count"), int), (
            f"{path.name} was cleared with no at_count — the door records the occurrence "
            f"count it was holding; its absence is the shape of a hand-set field: {last}")
    # THE TWO THE CLAUSE NAMES, and only those two. A third isolation trouble
    # (devices/codemother) was cleared later by an actual fix, its what_changed naming the
    # import that went away — a clear through the same door by a different route, and
    # demanding "reconcile" of it would red a correct act. The door's signature above is
    # what proves "not by hand" for all of them; reconcile is what proves it for these two.
    by_name = {p.name: json.loads(p.read_text(encoding="utf-8")) for p in seen}
    for want in ("inspector-new-finding-device-isolation-holds-devices-cairn.json",
                 "inspector-new-finding-device-isolation-holds-devices-web-server.json"):
        rec = by_name.get(want)
        assert rec, f"{want} is missing — it is one of the two the ticket cleared"
        said = str((rec["cleared_by"][-1]).get("what_changed", "")).lower()
        assert "reconcile" in said, (
            f"{want} was cleared, but not BY RECONCILE — what_changed says {said!r}")


def _emit_in_a_separate_process(world: Path, component: str, call: str) -> None:
    """Fire one trouble emission from a process that holds nothing and then exits.

    Same reasoning as ``_raise_in_a_separate_process`` above and the same shape, widened to
    the other two lanes: what crosses between the sender and the holder is a file on disk
    and nothing else. A helper that ran the call in THIS process would prove the fold and
    silently assume the transport."""
    root = str(Path(__file__).resolve().parents[4])
    script = (
        f"import sys; sys.path.insert(0, {root!r})\n"
        f"from pathlib import Path\n"
        f"from cairn.tools.base.diagnostic import ModuleRaiser\n"
        f"r = ModuleRaiser({component!r}, roots={{k: Path({str(world)!r}) "
        f'for k in ("repo","commons","instance")}})\n'
        f"r.{call}\n")
    out = subprocess.run([sys.executable, "-c", script], capture_output=True, text=True,
                         timeout=120)
    assert out.returncode == 0, out.stderr


def test_a_clear_CROSSES_THE_SEAM_and_the_HOLDER_writes_the_resolution():
    """THE SEND HALF OF A CLEAR IS AN EMISSION (ticket 9579a6f9cec6, completed 2026-09-08).

    Two processes again, neither holding this device: one raises, one says the fault is
    fixed, and what lands on disk is a ticket cleared THROUGH THE DOOR — carrying who,
    what changed, and the count at the moment of clearing. The sender wrote none of that
    and could not have: it never opened the store.

    THIS IS THE TOOTH THAT WOULD HAVE CAUGHT THE ORIGINAL SHAPE, which passed every test it
    had. Clearing shipped as a bus request on correct reasoning — a clear is a
    read-modify-write, so it belongs to the one hand that owns the store — with the wrong
    conclusion drawn from it: the ASKING moved to the bus along with the writing, and
    dialing the bus statically reaches ``inference_domain`` and ``db_domain``. The build
    inspector, which must reach neither, was a clearer. Its own ``fire_path_unreachable``
    sieve measured 4 findings and its gate refused a PROVED crossing on them."""
    from cairn.devices.trouble.shim import TroubleShim

    with tempfile.TemporaryDirectory() as tmp:
        world, store = Path(tmp) / "world", Path(tmp) / "store"
        roots = {k: world for k in ("repo", "commons", "instance")}
        shim = TroubleShim(roots=roots, root=str(store))

        _raise_in_a_separate_process(world, "build_inspector", IDENT, WHY)
        shim.drain()
        assert [t["id"] for t in _dev_at(store).live()] == [IDENT]

        _emit_in_a_separate_process(
            world, "tester",
            f"clear_trouble({IDENT!r}, by='cc', what_changed='the door grew a schema gate')")
        drained = shim.drain()
        assert drained.get("refused", []) == [], drained
        assert len(drained["folded"]) == 1, drained

        assert _dev_at(store).live() == [], "the clear crossed the seam but nothing cleared"
        ticket = json.loads(next((store).glob("*.json")).read_text(encoding="utf-8"))
        mark = ticket["cleared_by"][-1]
        assert mark["what_changed"] == "the door grew a schema gate", mark
        assert mark["at_count"] == 1, mark
        assert "at" in mark and mark["by"] == "cc", mark


def test_a_clear_for_a_trouble_that_is_NOT_LIVE_is_DECLINED_and_does_not_WEDGE_the_lane():
    """DECLINING IS THE HOLDER'S RIGHT, AND THE WATERMARK MUST STILL ADVANCE.

    ``TroubleDevice.clear`` REFUSES an unknown or already-cleared identity, and it is right
    to: at that door a clear is an assertion, and manufacturing an all-clear for a ticket
    nobody raised is the silent failure the lane exists to end. But an EMISSION is not an
    assertion, it is a report — the sender says what it observed and the owner judges
    (Law 6). So the drain declines it instead of propagating the refusal.

    THE SECOND HALF IS THE ONE WITH TEETH. The drain holds its watermark on a refusal, on
    purpose: a fault that cannot be folded must not be skipped past. Let a decline take that
    path and one stale clear wedges the lane FOREVER — every later emission from that
    component, raises included, sits behind it unread. This proves the wedge does not
    happen: a real raise arriving after the declined clear still lands."""
    from cairn.devices.trouble.shim import TroubleShim

    with tempfile.TemporaryDirectory() as tmp:
        world, store = Path(tmp) / "world", Path(tmp) / "store"
        roots = {k: world for k in ("repo", "commons", "instance")}
        shim = TroubleShim(roots=roots, root=str(store))

        _emit_in_a_separate_process(
            world, "tester",
            "clear_trouble('never-was-raised', by='cc', what_changed='wishful thinking')")
        first = shim.drain()
        assert first.get("refused", []) == [], (
            "a clear the holder declines came back as a REFUSAL — the watermark is now "
            f"stuck behind it: {first}")
        assert first["folded"][0]["outcome"] == "declined", first

        _raise_in_a_separate_process(world, "tester", IDENT, WHY)
        second = shim.drain()
        assert [t["id"] for t in _dev_at(store).live()] == [IDENT], (
            "the raise behind the declined clear never folded — the lane is wedged: "
            f"{second}")


def test_a_reconcile_clears_the_stale_spares_the_standing_and_CANNOT_REACH_OUTSIDE_ITS_SCOPE():
    """THE RECONCILE LANE: the reporter states what it still observes, the owner clears the rest.

    Why this exists beside ``clear_trouble``: a reconciler cannot know what is stale without
    READING the store, and both routes to that read are shut — over the bus (the fire path
    this change closes) or by importing the trouble device (the isolation red the ticket was
    cast against). So it reads nothing and reports everything, and the difference is computed
    in the hand that already holds the store.

    THE THIRD ASSERTION IS THE REAL TOOTH. A reconcile is the most powerful thing in this
    lane — it can clear tickets it never names — so its authority has to STOP at its scope.
    A trouble outside the scope prefix is not in ``still`` either, and an implementation that
    diffed against the whole live list instead of the scoped subset would clear it while
    passing both of the first two assertions."""
    from cairn.devices.trouble.shim import TroubleShim

    mine_kept = "inspector-new-finding-alpha"
    mine_gone = "inspector-new-finding-beta"
    not_mine = "validation-verdict-changed-test-thing"

    with tempfile.TemporaryDirectory() as tmp:
        world, store = Path(tmp) / "world", Path(tmp) / "store"
        roots = {k: world for k in ("repo", "commons", "instance")}
        shim = TroubleShim(roots=roots, root=str(store))

        for ident in (mine_kept, mine_gone, not_mine):
            _raise_in_a_separate_process(world, "build_inspector", ident, WHY)
        shim.drain()
        assert len(_dev_at(store).live()) == 3

        _emit_in_a_separate_process(
            world, "build_inspector",
            f"reconcile_troubles('inspector-new-finding-', [{mine_kept!r}], by='cc', "
            f"what_changed='the raising condition is gone from the current findings')")
        drained = shim.drain()
        assert drained.get("refused", []) == [], drained

        live = sorted(t["id"] for t in _dev_at(store).live())
        assert mine_kept in live, f"a finding still standing was cleared: {live}"
        assert mine_gone not in live, f"a stale finding was not cleared: {live}"
        assert not_mine in live, (
            "the reconcile reached OUTSIDE its scope and cleared another reporter's "
            f"trouble: {live}")


def test_BOTH_CLEARING_LANES_COMPARE_THROUGH_THE_STORES_OWN_ADDRESSING_RULE():
    """A SENDER NAMES A DEFECT; THE STORE HOLDS A SLUG. The drain has to bridge the two.

    Every door on ``TroubleDevice`` slugs what it is handed — lowercase, non-alphanumerics
    folded to "-" — so what is on disk is always the slug. Both clearing lanes, though,
    COMPARE a sender's identity against those stored ids before they decide anything, and
    until 2026-09-08 both compared the raw pointer. The two failures are opposite and both
    bad, which is why one test covers both lanes:

      clear     — declines forever. Measured live the day the lane shipped: 5 of 5 tester
                  clears folded to "declined — not live", because the tester names a trouble
                  after its proof file (``test_inspector_nexus``) and the store holds
                  ``test-inspector-nexus``. The trouble stayed in the operator inbox with
                  its proof standing green.
      reconcile — clears what is STILL STANDING. ``still`` is the complete current picture;
                  an unslugged entry matches nothing, so the trouble it names reads as stale
                  and is cleared. That is the quiet-and-wrong direction Law 7 forbids, and
                  no assertion in the lane's other tests can see it, because they all speak
                  in slugs already.

    THE FIXTURE SPEAKS IN UNDERSCORES ON PURPOSE. A hollow implementation that slugs one
    lane and not the other fails exactly one half of this test."""
    from cairn.devices.trouble.shim import TroubleShim

    # What the tester actually sends: an identity built from a proof FILENAME.
    unslugged_kept = "validation-verdict-changed-test_still_red"
    unslugged_gone = "validation-verdict-changed-test_went_green"
    slug_kept = "validation-verdict-changed-test-still-red"
    slug_gone = "validation-verdict-changed-test-went-green"

    with tempfile.TemporaryDirectory() as tmp:
        world, store = Path(tmp) / "world", Path(tmp) / "store"
        roots = {k: world for k in ("repo", "commons", "instance")}
        shim = TroubleShim(roots=roots, root=str(store))

        # --- the CLEAR lane: an unslugged clear must reach the trouble it names
        _raise_in_a_separate_process(world, "tester", unslugged_gone, WHY)
        shim.drain()
        assert [t["id"] for t in _dev_at(store).live()] == [slug_gone], (
            "the raise did not land under the slug — the fixture's premise is wrong")

        _emit_in_a_separate_process(
            world, "tester",
            f"clear_trouble({unslugged_gone!r}, by='cc', "
            f"what_changed='re-seal round-trip: red -> green')")
        drained = shim.drain()
        folds = [f for f in drained.get("folded", []) if "clear_trouble" in f["emission"]]
        assert folds and folds[0].get("outcome") != "declined", (
            "an unslugged clear was declined as 'not live' while the trouble it names is "
            f"standing — the lane compares the raw pointer against slugged ids: {folds}")
        assert _dev_at(store).live() == [], (
            f"the clear folded but the trouble is still standing: {_dev_at(store).live()}")

        # --- the RECONCILE lane: an unslugged `still` entry must SPARE its trouble
        for ident in (unslugged_kept, unslugged_gone):
            _raise_in_a_separate_process(world, "tester", ident, WHY)
        shim.drain()
        assert sorted(t["id"] for t in _dev_at(store).live()) == sorted((slug_kept, slug_gone))

        _emit_in_a_separate_process(
            world, "tester",
            f"reconcile_troubles('validation-verdict-changed-', [{unslugged_kept!r}], "
            f"by='cc', what_changed='the current picture after the sweep')")
        drained = shim.drain()
        assert drained.get("refused", []) == [], drained
        live = sorted(t["id"] for t in _dev_at(store).live())
        assert slug_kept in live, (
            "a trouble the reporter said is STILL STANDING was cleared — its `still` entry "
            f"was unslugged and matched nothing: {live}")
        assert slug_gone not in live, f"a stale trouble was not cleared: {live}"


def test_a_RECONCILE_SCOPE_KEEPS_ITS_TRAILING_SEPARATOR():
    """SLUGGING A PREFIX IS HALF-RIGHT: the fold is wanted, the end-trim is not.

    ``identity_of`` strips leading and trailing separators, which is correct for an identity
    and wrong for a scope: it turns the prefix ``"inspector-new-finding-"`` into
    ``"inspector-new-finding"``, which still matches everything it should AND everything
    under any longer word starting the same way. A reconcile is the most powerful act in
    this lane, so widening its reach by one character is a real defect even though every
    id in today's corpus survives it. Proved with a neighbour that only the un-trimmed
    prefix excludes."""
    from cairn.devices.trouble.shim import TroubleShim

    inside = "inspector-new-finding-alpha"
    neighbour = "inspector-new-findings-rollup"   # differs only after the separator

    with tempfile.TemporaryDirectory() as tmp:
        world, store = Path(tmp) / "world", Path(tmp) / "store"
        roots = {k: world for k in ("repo", "commons", "instance")}
        shim = TroubleShim(roots=roots, root=str(store))

        for ident in (inside, neighbour):
            _raise_in_a_separate_process(world, "build_inspector", ident, WHY)
        shim.drain()
        assert len(_dev_at(store).live()) == 2

        # An EMPTY current picture under the scope: everything in scope is stale.
        _emit_in_a_separate_process(
            world, "build_inspector",
            "reconcile_troubles('inspector-new-finding-', [], by='cc', "
            "what_changed='no findings at all in the current run')")
        drained = shim.drain()
        assert drained.get("refused", []) == [], drained

        live = [t["id"] for t in _dev_at(store).live()]
        assert inside not in live, f"the in-scope stale trouble was not cleared: {live}"
        assert neighbour in live, (
            "the reconcile cleared a trouble OUTSIDE its scope — the trailing separator was "
            f"trimmed off the prefix, widening the reach: {live}")


def test_the_THREE_LANES_keep_INDEPENDENT_watermarks():
    """A SHARED WATERMARK SILENTLY DROPS EMISSIONS, and the drop is invisible in the result.

    The watermark is a filename high-water mark and filenames are timestamps, so three gates
    sharing one mark looks fine right up until two emissions carry the SAME stamp. Then the
    lexical order of the gate suffix decides: ``.clear_trouble.json`` sorts before
    ``.raise_trouble.json``, the raise folds first and advances the mark past the clear, and
    the clear is skipped forever — reported as neither folded nor refused.

    Same stamp is exactly what a caller that raises and clears in one breath produces, which
    is why this is a tooth and not a hypothetical. Both lanes must fold."""
    from cairn.devices.trouble.shim import TroubleShim

    other = "some-other-defect"
    with tempfile.TemporaryDirectory() as tmp:
        world, store = Path(tmp) / "world", Path(tmp) / "store"
        roots = {k: world for k in ("repo", "commons", "instance")}
        shim = TroubleShim(roots=roots, root=str(store))

        _raise_in_a_separate_process(world, "tester", other, WHY)
        shim.drain()
        assert [t["id"] for t in _dev_at(store).live()] == [other]

        import datetime as _dt
        stamp = ("__import__('datetime').datetime(2031, 1, 1, 12, 0, 0, "
                 "tzinfo=__import__('datetime').timezone.utc)")
        _emit_in_a_separate_process(
            world, "tester",
            f"clear_trouble({other!r}, by='cc', what_changed='fixed', now={stamp})")
        _emit_in_a_separate_process(
            world, "tester",
            f"raise_trouble({IDENT!r}, why={WHY!r}, now={stamp})")

        drained = shim.drain()
        assert drained.get("refused", []) == [], drained
        live = sorted(t["id"] for t in _dev_at(store).live())
        assert live == [IDENT], (
            "one of two same-stamped emissions was silently skipped — the lanes are "
            f"sharing a watermark. live={live}, drained={drained}")


def test_SENDING_to_the_trouble_lane_NEVER_DIALS_THE_BUS():
    """CLAUSE (2)'S OTHER FACE, and the one the original build got wrong.

    ``test_no_device_reaches_this_one_by_import`` asks whether anyone reaches trouble by
    IMPORT. Nobody did — and the lane was still reached by dialing the bus, which pulls in
    ``bus_client`` and through it ``inference_domain`` and ``db_domain``. So a component
    could satisfy every isolation tooth in this file and still statically reach a database,
    which is what the build inspector's ``fire_path_unreachable`` sieve caught after the
    fact.

    THE LINE IS SEND VS READ, NOT BUS VS NOT-BUS, and drawing it anywhere else makes this
    tooth wrong rather than strict. Its first draft banned every trouble bus verb and
    promptly reported ``cairn/device.py`` and ``web_server/listener.py`` — the two
    presentation surfaces that ask ``live`` for the operator's panel, which is exactly the
    shape this ticket CHARTED for them (they are the panel; asking the owner for its list
    is what a reader is supposed to do). A tooth that reds the design it was written to
    protect is measuring the wrong property.

    So: reading ``live`` over the bus stays legal for anyone. SENDING — clear, and now
    reconcile — may not ride the bus from anywhere, because a sender is often a component
    with a fire-path rule and the send has an emission lane that costs it nothing."""
    root = Path(__file__).resolve().parents[4] / "cairn"
    offenders = []
    for path in root.rglob("*.py"):
        rel = path.relative_to(root.parent).as_posix()
        if rel.startswith("cairn/devices/trouble/") or "/proofs/" in rel or "/probes/" in rel:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for verb in ("clear", "reconcile"):
            if f'verb="{verb}"' in text or f"verb='{verb}'" in text:
                offenders.append(f"{rel} (verb={verb})")
    assert offenders == [], (
        "these SEND to the trouble lane over the bus — which imports inference_domain and "
        "db_domain, so every one of them statically reaches a database. The send lanes are "
        f"emissions (DiagnosticBase.clear_trouble / reconcile_troubles): {offenders}")


def _dev_at(store) -> TroubleDevice:
    dev = TroubleDevice(root=str(store))
    dev.set_diagnostic_receiver(None)
    return dev


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
