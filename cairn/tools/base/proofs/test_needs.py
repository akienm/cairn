"""Proof: a stage's needs are real, and an UNMEASURED mark cannot be written.

The falsifier this proof grips (tickets/stage-needs.json child a): "A mark lacking WHEN or HOW
MEASURED must be REFUSED at the write door — a bare [DONE] cannot be written. Staleness must be
QUERYABLE. And the shape must carry a REAL case end-to-end."

So there are two halves and the second is the one a hollow build fails:
  - MECHANISM, on synthetic records: every refusal actually refuses.
  - IN SITU, by SCANNING the live tickets: whatever is on disk conforms, and at least one node
    really declares needs with a really-measured mark. A green over zero declaring nodes would be a
    hollow pass (Law 8), so an empty scan is itself a red.

The live half asserts INVARIANTS ONLY — never a snapshot value. Marks get added, needs get met, the
cursor moves; a proof that pinned "3 needs, 1 DONE" would go red on the next honest day, which is
noise, not a finding (Law 1 — re-deriving a settled answer is the defect; a proof that cries wolf
makes the suite re-derive its own trustworthiness). Age is checked against an INJECTED today for the
same reason: reaching for the clock and asserting 0 would pass only on the day it was written.

Deliberately dependency-light: pure file reads + the needs core. Runs bare.

    python3 cairn/tools/base/proofs/test_needs.py     # exit 0 = green
"""

from __future__ import annotations

import json
import shutil
import sys
import tempfile
from datetime import date
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.base import needs
from cairn.tools.base.needs import NeedRefused

_TICKETS = _REPO_ROOT.parent / "CairnCommons" / "tickets"

# A synthetic node carrying the canonical code-seam@v1 vocabulary. Synthetic on purpose: the
# mechanism teeth must not depend on what any live ticket happens to say today.
_NODE = {
    "id": "synthetic-for-proof",
    "state": "code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED",
    "stage_needs": {"BUILDME": [{"need": "the bus device", "marks": []}]},
}

_GOOD_MARK = {
    "need": "the bus device",
    "status": "DONE",
    "when": "2026-07-26",
    "how_measured": "imported cairn.devices.bus and read its state.json cursor: gate=proven",
}


def _refuses(fn, because: str):
    """Assert the gate REFUSES, and report a hollow build as a hollow build.

    The second except clause is the lesson, not decoration: gutting the gate made this proof die
    with a bare ``KeyError: 'when'`` — a red (so Law 8 held) whose message pointed at a missing dict
    key rather than at the missing GATE. That is a complete-diagnostic failure at the proof's own
    surface: the reader would go hunting the wrong thing. Now a hollow build names itself.
    """
    try:
        fn()
    except NeedRefused:
        return
    except Exception as e:                       # noqa: BLE001 — the diagnostic IS the point
        raise AssertionError(
            f"THE GATE DID NOT REFUSE — {because}. Instead the malformed record got far enough in "
            f"to break something else: {type(e).__name__}: {e}. That means the refusal was removed "
            "or weakened; the downstream crash is the symptom, not the cause."
        ) from None
    raise AssertionError(f"NOT REFUSED — {because}")


# ── the falsifier: a bare [DONE] cannot be written ───────────────────────────


def test_a_mark_missing_when_or_how_measured_is_refused():
    """THE point of the node. Akien's sketch writes '[DONE] BUS DEVICE'; a bare DONE goes stale
    invisibly, so the door refuses it. He agreed at n=1: 'bare done goes stale. agreed.'"""
    for drop in ("when", "how_measured", "status", "need"):
        partial = {k: v for k, v in _GOOD_MARK.items() if k != drop}
        _refuses(lambda p=partial: needs.validate_mark(p), f"a mark with no {drop!r} was admitted")
    # And the empty string is the same defect wearing the field name.
    for blank in ("when", "how_measured"):
        _refuses(lambda b=blank: needs.validate_mark({**_GOOD_MARK, b: "   "}),
                 f"a mark with a blank {blank!r} was admitted")


def test_a_token_how_measured_is_refused_but_a_rerunnable_one_passes():
    """'checked' is a bare DONE with extra words. The floor is a length, not a grammar — no regex
    can decide 'could a reader re-run this' — but the useless cases are refused outright."""
    for token in ("ok", "checked", "yes", "done"):
        _refuses(lambda t=token: needs.validate_mark({**_GOOD_MARK, "how_measured": t}),
                 f"how_measured={token!r} was admitted")
    needs.validate_mark(_GOOD_MARK)      # the re-runnable one passes


def test_a_when_that_cannot_be_AGED_is_refused():
    """The age IS the product. A date only a human can read cannot be turned red by a staleness
    query, so it is not a valid observation."""
    for bad in ("yesterday", "last week", "26/07/2026", "recently", "2026-13-01"):
        _refuses(lambda b=bad: needs.validate_mark({**_GOOD_MARK, "when": b}),
                 f"when={bad!r} was admitted")
    needs.validate_mark({**_GOOD_MARK, "when": "2026-07-26T14:03:00"})    # timestamps are fine


def test_never_looked_at_is_not_a_writable_status():
    """The third condition is the ABSENCE of a mark, not a status. Two ways to say one thing is how
    they drift apart — and 'nobody measured this' is not an observation."""
    for bogus in ("UNKNOWN", "NEVER", "TODO", "", "done", "Done"):
        _refuses(lambda b=bogus: needs.validate_mark({**_GOOD_MARK, "status": b}),
                 f"status={bogus!r} was admitted")
    assert set(needs.STATUSES) == {"DONE", "MISSING"}, "the writable status set changed silently"


# ── the shape: a need attaches to a stage the node actually has ──────────────


def test_a_need_on_a_stage_the_node_does_not_have_is_refused():
    """Validated against the node's OWN parsed vocabulary, so the stages it can declare needs for
    are exactly the stages it has. This is the tooth that could not be built while the cursor was
    prose (troubles/workflow-cursor-unreadable-by-the-chokepoint.json)."""
    for bogus in ("BUILD", "SHIPME", "buildme", "PROVED_MAYBE"):
        node = {**_NODE, "stage_needs": {bogus: [{"need": "x y z", "marks": []}]}}
        _refuses(lambda n=node: needs.validate_needs(n), f"a need on stage {bogus!r} was admitted")


def test_a_misshapen_needs_block_is_refused_but_absent_is_fine():
    node_without = {k: v for k, v in _NODE.items() if k != "stage_needs"}
    needs.validate_needs(node_without)          # most nodes need nothing external; not a defect
    for bad in ([], "the bus device", {"BUILDME": []}, {"BUILDME": ["the bus device"]},
                {"BUILDME": [{"marks": []}]}, {"BUILDME": [{"need": "  ", "marks": []}]},
                {"BUILDME": [{"need": "the bus device", "marks": "none"}]}):
        _refuses(lambda b=bad: needs.validate_needs({**_NODE, "stage_needs": b}),
                 f"stage_needs={bad!r} was admitted")


# ── append-only, and the projection that makes staleness queryable ───────────


def test_marks_are_append_only_and_prior_marks_are_never_touched():
    first = needs.append_mark([], _GOOD_MARK, at="2026-07-26T10:00:00")
    second = needs.append_mark(first, {**_GOOD_MARK, "status": "MISSING"}, at="2026-07-26T11:00:00")
    assert len(first) == 1 and len(second) == 2, "append_mark did not append"
    assert first[0] == second[0], "a prior mark was mutated — history is append-only (Law 7)"
    assert [m["seq"] for m in second] == [0, 1], f"seq is not monotonic from 0: {second}"
    _refuses(lambda: needs.append_mark([], {**_GOOD_MARK, "how_measured": ""}),
             "append_mark validated nothing")
    assert needs.append_mark([], _GOOD_MARK)[0]["how_measured"] == _GOOD_MARK["how_measured"], \
        "the observation was altered on the way in (Law 7 — a record of truth is carried, not edited)"


def test_staleness_is_QUERYABLE_and_the_age_comes_from_an_injected_today():
    node = {**_NODE, "stage_needs": {"BUILDME": [
        {"need": "the bus device", "marks": [{**_GOOD_MARK, "when": "2026-07-05"}]},
        {"need": "an unlooked-at thing", "marks": []},
    ]}}
    view = needs.project_needs(node, today=date(2026, 7, 26))["BUILDME"]
    aged = {row["need"]: row for row in view}
    assert aged["the bus device"]["age_days"] == 21, \
        f"21 days is not reported as 21: {aged['the bus device']['age_days']}"
    assert aged["an unlooked-at thing"]["status"] is None, "an unmarked need invented a status"
    assert aged["an unlooked-at thing"]["age_days"] is None, "an unmarked need invented an age"
    # The projection is a PURE FUNCTION of the marks + the day, so it cannot drift from them.
    assert needs.project_needs(node, today=date(2026, 7, 26)) == \
        needs.project_needs(node, today=date(2026, 7, 26)), "the projection is not deterministic"
    # Later day, older mark — the direction that makes 'this DONE is 21 days old' sayable at all.
    later = needs.project_needs(node, today=date(2026, 8, 26))["BUILDME"][0]["age_days"]
    assert later > 21, f"age did not grow with the day: {later}"


def test_the_latest_observation_wins_and_the_earlier_one_survives():
    """A need can go DONE then MISSING (a host goes down). The view shows the latest; the record
    keeps both, which is what makes 'when did this break' answerable later."""
    marks = needs.append_mark([], _GOOD_MARK, at="2026-07-26T10:00:00")
    marks = needs.append_mark(marks, {**_GOOD_MARK, "status": "MISSING", "when": "2026-07-27",
                                      "how_measured": "curl :11434 refused, connection reset"},
                              at="2026-07-27T10:00:00")
    node = {**_NODE, "stage_needs": {"BUILDME": [{"need": "the bus device", "marks": marks}]}}
    row = needs.project_needs(node, today=date(2026, 7, 27))["BUILDME"][0]
    assert row["status"] == "MISSING", f"the latest observation did not win: {row['status']}"
    assert row["observations"] == 2, "the earlier observation was lost"


# ── the door, on a real file ─────────────────────────────────────────────────


def test_the_door_refuses_an_undeclared_stage_or_need_and_writes_nothing():
    """A mark must land ON a declared need — an observation with nothing to attach to is lost. And a
    refused write must leave the file byte-identical, since the refusal happens before the write."""
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "node.json"
        p.write_text(json.dumps(_NODE, indent=2))
        before = p.read_bytes()
        _refuses(lambda: needs.mark(str(p), "PROVEME", "the bus device", status="DONE",
                                    when="2026-07-26", how_measured=_GOOD_MARK["how_measured"]),
                 "a mark on a stage with no declared needs was admitted")
        _refuses(lambda: needs.mark(str(p), "BUILDME", "a need nobody declared", status="DONE",
                                    when="2026-07-26", how_measured=_GOOD_MARK["how_measured"]),
                 "a mark on an undeclared need was admitted")
        _refuses(lambda: needs.mark(str(p), "BUILDME", "the bus device", status="DONE",
                                    when="2026-07-26", how_measured="ok"),
                 "a bare DONE went through the door")
        assert p.read_bytes() == before, "a REFUSED write still touched the file"
        out = needs.mark(str(p), "BUILDME", "the bus device", status="DONE", when="2026-07-26",
                         how_measured=_GOOD_MARK["how_measured"])
        assert out["stage_needs"]["BUILDME"][0]["marks"][0]["status"] == "DONE", "the mark did not land"
        assert json.loads(p.read_text())["stage_needs"]["BUILDME"][0]["marks"][0]["seq"] == 0, \
            "the mark did not persist to disk"
        assert json.loads(p.read_text())["id"] == _NODE["id"], "the door damaged the rest of the record"


# ── IN SITU: the live tickets, invariants only ───────────────────────────────


def _live_nodes() -> list[tuple[str, dict]]:
    out = []
    for f in sorted(_TICKETS.glob("*.json")):
        if f.name.startswith("_"):
            continue
        try:
            out.append((f.name, json.loads(f.read_text())))
        except ValueError:
            continue
    return out


def test_every_needs_block_on_disk_conforms():
    """Scans, so it covers each node that adopts the shape without being edited. A hand-authored
    need on a stage that does not exist, or a mark someone typed without a measurement, turns red.

    REPORTS EVERY NONCONFORMANCE, NOT THE FIRST — and that is a repair, not a flourish. This tooth
    raised on ``a-node-holds-one-claim.json`` and stopped, so eleven more tickets in exactly the
    same condition sat invisible behind alphabetical order and the finding read as one stale ticket
    for a day. The real finding was structural: 33 chart-keyed PROSE entries had been written into
    the field this door owns (they live in ``chart_notes`` now, gated at
    ``cairn/machines/chart/chain.py``). A diagnostic surface delivers ALL the data on its INITIAL pass;
    re-running to gather the rest is the re-derivation Law 1 refuses
    (I-complete-diagnostic-on-first-pass)."""
    checked = 0
    bad = []
    for name, node in _live_nodes():
        if not node.get("stage_needs"):
            continue
        try:
            needs.validate_needs(node)
        except (NeedRefused, ValueError) as e:
            bad.append(f"  {name}: {e}")
        checked += 1
    if bad:
        raise AssertionError(
            f"{len(bad)} of {checked} live needs blocks do not conform:\n" + "\n".join(bad)
        )
    assert checked, ("NO live node declares stage_needs — the shape exists but nothing uses it, "
                     "which is a hollow pass (Law 8): the falsifier demands a REAL case end to end")


def test_a_real_case_carries_a_real_measurement():
    """The non-hollow floor. Somewhere in the live fleet there is a need marked DONE by an
    observation that names HOW — and its age is a number a reader can judge. Invariants, not values:
    which node, which need, and how old are all free to change."""
    today = date.today()
    dones = []
    for name, node in _live_nodes():
        if not node.get("stage_needs"):
            continue
        for stage, rows in needs.project_needs(node, today=today).items():
            for row in rows:
                assert row["age_days"] is None or isinstance(row["age_days"], int), \
                    f"{name}/{stage}: age is not a number, so staleness is not queryable"
                assert row["age_days"] is None or row["age_days"] >= 0, \
                    f"{name}/{stage}/{row['need']}: age is negative — a mark measured in the future"
                if row["status"] == "DONE":
                    dones.append((name, stage, row))
    assert dones, ("no live need is marked DONE by a real observation — the shape has never been "
                   "used to record a measurement, so nothing proves the door admits a good mark")
    for name, stage, row in dones:
        assert len(row["how_measured"]) >= needs._MIN_HOW_MEASURED, \
            f"{name}/{stage}: a DONE on disk carries a token how_measured"
        assert row["when"], f"{name}/{stage}: a DONE on disk carries no when"


def test_the_render_shows_all_three_conditions_it_can_show():
    """Akien's sketch IS the spec of the surface, so it is proved, not just described. Rendered from
    a synthetic node — the live fleet's mix is free to change without reddening this."""
    node = {**_NODE, "stage_needs": {"BUILDME": [
        {"need": "a met thing", "marks": [needs.append_mark([], _GOOD_MARK, at="x")[0]]},
        {"need": "a looked-for thing that is not there",
         "marks": [needs.append_mark([], {**_GOOD_MARK, "status": "MISSING",
                                          "need": "a looked-for thing that is not there"}, at="x")[0]]},
        {"need": "a thing nobody looked for", "marks": []},
    ]}}
    text = needs.render_needs(node, today=date(2026, 7, 26))
    assert "[ ] BUILDME — Needs:" in text, f"the stage header is not Akien's shape:\n{text}"
    assert "[DONE]" in text and "[MISSING]" in text, f"a status is not rendered:\n{text}"
    assert "never looked" in text, f"the unmeasured condition is invisible in the render:\n{text}"
    assert "(0d ago)" in text, f"the age is not on the surface:\n{text}"
    # Workflow order, not dict order: a stage the node has but declares nothing for is not invented.
    assert "PROVEME" not in text, f"the render invented a stage with no needs:\n{text}"


def _main() -> int:
    checks = [
        test_a_mark_missing_when_or_how_measured_is_refused,
        test_a_token_how_measured_is_refused_but_a_rerunnable_one_passes,
        test_a_when_that_cannot_be_AGED_is_refused,
        test_never_looked_at_is_not_a_writable_status,
        test_a_need_on_a_stage_the_node_does_not_have_is_refused,
        test_a_misshapen_needs_block_is_refused_but_absent_is_fine,
        test_marks_are_append_only_and_prior_marks_are_never_touched,
        test_staleness_is_QUERYABLE_and_the_age_comes_from_an_injected_today,
        test_the_latest_observation_wins_and_the_earlier_one_survives,
        test_the_door_refuses_an_undeclared_stage_or_need_and_writes_nothing,
        test_every_needs_block_on_disk_conforms,
        test_a_real_case_carries_a_real_measurement,
        test_the_render_shows_all_three_conditions_it_can_show,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — a stage declares what it needs, and an UNMEASURED mark cannot be written: the "
          "door refuses a bare [DONE], a token how_measured, an unageable when, a status for "
          "'never looked', and a need on a stage the node does not have; marks are append-only; "
          "the current view is a pure projection carrying each mark's AGE (staleness is queryable, "
          "Law 3); and the live fleet carries a real case measured end to end (Law 8)")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
