"""Proof: a chart note attaches to a real leg, and the two animals cannot share a name again.

The finding this grips (2026-07-30, measured while closing the suite's one red): ``stage_needs``
held 33 chart-keyed PROSE entries across 12 tickets and 7 workflow-keyed LEDGER entries across 6.
One field, two animals. The needs door refused the prose correctly, and because its live scan
raised on the FIRST offender the whole thing read as one stale ticket named 'orient'.

So there are three halves and a hollow build fails all three:
  - MECHANISM, on synthetic nodes: every refusal actually refuses, and each clause is load-bearing.
  - NO DRIFT: the leg list here and the dial's registry are the same seven, in the same order —
    otherwise "written down once" is a claim, not a fact.
  - IN SITU, by SCANNING the live tickets: whatever is on disk conforms, at least one node really
    carries notes (a green over zero carriers is a hollow pass, Law 8), and NO ticket still keys a
    workflow-stage need by a chart leg — the migration is proved by the corpus, not by memory.

Invariants only on the live half. Notes get added and legs get answered; a proof that pinned "12
tickets, 33 notes" would red on the next honest day, which is noise rather than a finding (Law 1).

Deliberately dependency-light on the gate path: ``chain`` imports nothing. The drift tooth imports
``dial`` (which pulls the whole chain) and is the only heavy thing here.

    python3 cairn/tools/chain/proofs/test_chart_notes.py     # exit 0 = green
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.devices.tester.scratch import scratch_dir  # noqa: E402
from cairn.tools.chain import chain
from cairn.tools.chain.chain import ChartNoteRefused

_TICKETS = _REPO_ROOT.parent / "CairnCommons" / "tickets"

_GOOD = "settle a3 first, because it can shrink the stone before anything is built"
_NODE = {"id": "synthetic-for-proof", "chart_notes": {"constrain": _GOOD}}


def _refuses(fn, because: str):
    """Assert the gate REFUSES, and report a hollow build as a hollow build. The second except
    clause is the lesson test_needs.py learned and this inherits: a gutted gate that dies further
    downstream with a KeyError is still a red, but it points the reader at the wrong thing."""
    try:
        fn()
    except ChartNoteRefused:
        return
    except Exception as e:                       # noqa: BLE001 — the diagnostic IS the point
        raise AssertionError(
            f"THE GATE DID NOT REFUSE — {because}. Instead the malformed record got far enough in "
            f"to break something else: {type(e).__name__}: {e}. The refusal was removed or "
            "weakened; the downstream crash is the symptom, not the cause."
        ) from None
    raise AssertionError(f"NOT REFUSED — {because}")


# ── mechanism: a note attaches to a leg that exists ──────────────────────────


def test_a_note_on_a_leg_that_does_not_exist_is_refused():
    """The tooth that closes the original collision from the other side: a WORKFLOW stage name is
    not a chart leg, so the same content cannot simply be moved back under the new field."""
    for bogus in ("BUILDME", "PROVEME", "findings", "Orient", "orientation", "", "chart"):
        _refuses(lambda b=bogus: chain.validate_chart_notes({**_NODE, "chart_notes": {b: _GOOD}}),
                 f"a note on leg {bogus!r} was admitted")


def test_every_real_leg_is_admitted():
    """The other side of the same tooth — a gate that refuses everything is not a gate. Runs the
    whole vocabulary, so a leg silently dropped from STAGES turns this red."""
    for leg in chain.STAGES:
        chain.validate_chart_notes({**_NODE, "chart_notes": {leg: _GOOD}})
    assert len(chain.STAGES) == 7, f"the chain is not seven legs: {chain.STAGES}"


def test_a_misshapen_block_is_refused_but_absent_is_fine():
    node_without = {k: v for k, v in _NODE.items() if k != "chart_notes"}
    chain.validate_chart_notes(node_without)     # most nodes never chart; not a defect
    chain.validate_chart_notes({**_NODE, "chart_notes": {}})   # charted, left no notes
    for bad in ([], "a bare string", 7, ["constrain", _GOOD]):
        _refuses(lambda b=bad: chain.validate_chart_notes({**_NODE, "chart_notes": b}),
                 f"chart_notes={bad!r} was admitted")


def test_a_note_must_be_prose_and_not_a_needs_entry_in_disguise():
    """The shape IS the distinction. A list of {need, marks} under a leg would be the collision
    re-forming under the new name — the field would grow marks, and a note would start pretending
    to be measured."""
    for bad in ([{"need": "the bus device", "marks": []}], {"need": "x"}, 12, None, True):
        _refuses(lambda b=bad: chain.validate_chart_notes({**_NODE, "chart_notes": {"survey": b}}),
                 f"a {type(bad).__name__} note was admitted")


def test_an_empty_note_is_refused_and_the_floor_is_load_bearing():
    for bad in ("", "   ", "tbd", "see above", "x" * (chain._MIN_NOTE - 1)):
        _refuses(lambda b=bad: chain.validate_chart_notes({**_NODE, "chart_notes": {"triage": b}}),
                 f"note {bad!r} was admitted under the {chain._MIN_NOTE}-char floor")
    chain.validate_chart_notes({**_NODE, "chart_notes": {"triage": "x" * chain._MIN_NOTE}})


def test_the_refusal_names_the_other_field():
    """Complete diagnostic on the FIRST pass: someone who lands here is one field-rename away from
    being right, and the message has to say which way to go — in both directions."""
    def _message_of(fn, exc):
        """The message, or a red. A bare try/except whose body never runs is a VACUOUS pass —
        every assertion inside it is skipped and the tooth reports green for the wrong reason
        (memory: leak-scan-coin-toss-red). So the absence of a refusal is itself the failure."""
        try:
            fn()
        except exc as e:
            return str(e)
        raise AssertionError("nothing was refused, so the message under test was never produced")

    msg = _message_of(lambda: chain.validate_chart_notes({**_NODE,
                                                          "chart_notes": {"BUILDME": _GOOD}}),
                      ChartNoteRefused)
    assert "stage_needs" in msg, f"the refusal does not point at the other field: {msg}"
    assert all(leg in msg for leg in chain.STAGES), f"the refusal hides the legs: {msg}"

    from cairn.tools.base import needs
    msg = _message_of(
        lambda: needs.validate_needs(
            {"id": "n", "workflow_and_state": "code-seam@v1: THINKME -> [BUILDME] -> PROVED",
             "stage_needs": {"survey": "prose addressed to a chart leg here"}}),
        needs.NeedRefused)
    assert "chart_notes" in msg, \
        f"the needs door refuses the prose without naming where it belongs: {msg}"


# ── no drift: one list, two readers ──────────────────────────────────────────


def test_the_dial_registry_and_the_chain_are_the_same_seven_in_the_same_order():
    """``chain.STAGES`` claims to be the written-down chain. ``dial.STAGE_FIELDS`` is the other
    place the seven appear, and it was there first. If they can disagree, the claim is false and
    the gate is validating against a private opinion (Law 1 — the settled answer lives once)."""
    from skills.chart import dial
    assert tuple(dial.STAGE_FIELDS) == chain.STAGES, (
        f"the two lists have drifted — dial says {tuple(dial.STAGE_FIELDS)}, "
        f"chain says {chain.STAGES}. Until dial CONSTRUCTS its registry from chain.STAGES "
        "(the IOU in chain.py), this tooth is the only thing holding them together."
    )


# ── the scan reports everything, which is the defect it was born from ────────


def test_the_scan_reports_EVERY_offender_not_the_first():
    """The repair, proved. The needs live-scan raised on the first bad ticket and eleven more sat
    invisible behind alphabetical order. Three offenders in, three findings out — a scan that
    reported one would pass a `len(findings) > 0` assertion and still hide two."""
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        for name in ("aaa", "mmm", "zzz"):
            (d / f"{name}.json").write_text(json.dumps(
                {"id": name, "chart_notes": {"BUILDME": _GOOD}}))
        (d / "fine.json").write_text(json.dumps({"id": "fine", "chart_notes": {"survey": _GOOD}}))
        (d / "_ignored.json").write_text(json.dumps({"id": "x", "chart_notes": {"nope": _GOOD}}))
        (d / "notes.md").write_text("not a ticket")
        (d / "broken.json").write_text("{not json")
        found = chain.scan(str(d))
    names = sorted(f["ticket"] for f in found)
    assert names == ["aaa.json", "broken.json", "mmm.json", "zzz.json"], \
        f"the scan did not report every offender exactly once: {names}"
    assert all(f["why"] for f in found), "a finding carried no reason"
    assert chain.scan(str(scratch_dir("no-such-chain-") / "definitely-not-here-9f3a")) == [], \
        "an absent directory is reported as a finding — a missing store is not a defect"


# ── IN SITU: the live tickets ────────────────────────────────────────────────


def _live_nodes():
    out = []
    for f in sorted(_TICKETS.glob("*.json")):
        if f.name.startswith("_"):
            continue
        try:
            out.append((f.name, json.loads(f.read_text())))
        except ValueError:
            continue
    return out


def test_every_chart_notes_block_on_disk_conforms():
    findings = chain.scan(str(_TICKETS))
    assert not findings, ("live chart_notes blocks do not conform:\n"
                          + "\n".join(f"  {f['ticket']}: {f['why']}" for f in findings))


def test_a_real_case_carries_real_notes():
    """The non-hollow floor (Law 8). Somewhere in the live fleet a ticket really speaks to the
    chart — otherwise the field exists and nothing uses it, and every refusal above is theatre.
    Invariants only: which ticket, which leg, and how many are all free to change."""
    carriers = [(name, node["chart_notes"]) for name, node in _live_nodes()
                if node.get("chart_notes")]
    assert carriers, ("NO live ticket carries chart_notes — the shape exists but nothing uses it, "
                      "which is a hollow pass: the field was migrated FROM 33 real entries")
    assert any(len(b) >= 4 for _, b in carriers), \
        "no live ticket notes four or more legs — a whole charted preamble should leave a trail"
    for name, block in carriers:
        for leg, note in block.items():
            assert leg in chain.STAGES and isinstance(note, str), f"{name}/{leg}"


def test_no_ticket_still_keys_a_workflow_NEED_by_a_chart_leg():
    """The migration proved by the corpus rather than by memory. Every surviving ``stage_needs``
    key must be a workflow stage and every value a list; a chart leg or a bare string there means
    the collision has re-formed. This is the tooth that would have caught it on day one."""
    from cairn.tools.base import needs
    offenders = []
    for name, node in _live_nodes():
        block = node.get("stage_needs")
        if not block:
            continue
        for stage, entry in block.items():
            if stage in chain.STAGES or isinstance(entry, str):
                offenders.append(f"  {name}: stage_needs[{stage!r}] is a "
                                 f"{type(entry).__name__} — chart prose in the needs field")
        try:
            needs.validate_needs(node)
        except (needs.NeedRefused, ValueError) as e:
            offenders.append(f"  {name}: {e}")
    assert not offenders, "the two animals share a field again:\n" + "\n".join(offenders)


def _main() -> int:
    checks = [f for f in globals().values()
              if callable(f) and getattr(f, "__name__", "").startswith("test_")]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — chart_notes: a note attaches to a real leg, prose and needs cannot share a "
          "field, the leg list has one home, the scan reports every offender on its first pass, "
          "and the live fleet carries real notes with no needs block still holding chart prose")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
