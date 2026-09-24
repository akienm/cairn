"""Proof for ticket cf80bdb57205 — the cheapest reader rehearses a ticket before BUILDME.

Every tooth runs over a SCRATCH world handed to the artifact door (``set_diagnostic_roots``
and, for the CLI subprocess, ``CAIRN_ARTIFACT_ROOTS``): a fixture commons with one ticket,
its own journal, its own rehearsals/ and questions/. No tooth reads the live commons and no
tooth calls the live reader (D15) — the reader is a stub replaying recorded trees, so the
proof pins the MACHINE (render, schema, diff, loop, records, lane, probe) and the live fire
is the measurement of the reader.

The teeth, each against the charter's falsifier:

  1. a deliberately underspecified fixture returns gaps naming the underspecified step in
     all three reads, and the gap list is byte-identical over the same trees twice (D6);
     steps are decision ids (D<n>) or 'unlisted: <text>' (D6 as amended, open-d71a52522428),
     an unlisted step is a gap of its own kind, and step names fold through
     cairn.tools.system_word;
  2. a read that fails the schema is re-read (D5) and every attempt is recorded; a reader
     that never satisfies it refuses the pass and writes NO record;
  3. with the gap answered as a decision line (``decide``, journaled ``cast``) the next pass
     returns zero gaps and writes a CLEAN record (journaled ``rehearse``) the ticket points
     at, whose ticket_sha256 equals the live bytes (D8 as amended);
  4. the sieve ``buildme_rides_the_rehearsal`` reds a ticket without a rehearsal, reds a
     ticket edited after its rehearsal — by name — and reads a clean current one green; the
     entry gate lists five lanes, the fifth ``the_ticket_rehearses_clean``;
  5. the sixth pass opens ONE question naming the standing gaps and reads nothing (D11);
  6. the prompt asserts the reader's job is the tree and that cannot_proceed is a legal
     answer; schema.json and ``validate`` agree over the schema's own vocabulary;
  7. the WATCHME probe is armed (carry + enough) and measures a scratch commons: enough at
     eight empty divergences of ten, WRONG-INTENT trigger at seven;
  8. after PROVED, ``record_divergence`` writes the diff both ways onto the clean record;
  9. ``cairn rehearse --help`` exits 0 and ``--standing`` speaks JSON through the subprocess
     seam;
 10. the entry gate's five lanes (folded into 4 above) and the CLI's ``--decide`` step form;
 11. the live fire's recorded reads (fixtures/live_fire_pass1.json, 46 gaps over 12/16/12
     free-text steps; live_fire_pass4.json, 0 gaps over 36/36/36 decision ids) replay through
     ``gaps`` and ``validate`` to the recorded numbers — clause 6's evidence without the
     reader (D15);
 12. the package init exists and skills/sail/SKILL.md sends the builder to `cairn rehearse`
     before the BUILDME crossing, naming the lane and both dispositions of a gap.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))



class _CallTime:
    """The machine under proof, bound at CALL time, never at import. A hollow reading reverts
    rehearsal.py to before the build and runs this file; a module-level import would then die
    before the first tooth printed, and the instrument would read every reverted file as
    UNREADABLE instead of the teeth that red without the machine (measured 2026-09-15 on the
    first reading of cf80bdb57205: 5 of 12 files unread). ``R.gaps`` still reads as it did."""

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module("cairn.machines.rehearsal.rehearsal"), name)


R = _CallTime()
from cairn.tools.artifact import artifact as door             # noqa: E402

REPO = Path(__file__).resolve().parents[4]

# The falsifier's clauses, each with the tooth that reds on a hollow build (read by
# ``clearance.hollow_lacks`` through ``cairn test --hollow``; plain literals, ast-parsed).
# Clause 6 is the live fire itself; its tooth replays the fire's recorded reads (D15).
PROVES = {
    "cf80bdb57205": {
        "1": "test_an_underspecified_ticket_returns_gaps_naming_the_step_in_every_read",
        "2": "test_a_decision_line_answers_the_gap_and_the_next_pass_writes_a_clean_record_over_the_live_bytes",
        "3": "test_the_sieve_reds_no_rehearsal_and_a_stale_hash_by_name_and_reads_a_clean_one_green",
        "4": "test_the_prompt_says_the_job_is_the_tree_and_cannot_proceed_is_legal_and_the_schema_mirrors_validate",
        "5": "test_after_proved_the_divergence_is_written_onto_the_clean_record_both_ways",
        "6": "test_the_live_fires_recorded_reads_replay_through_the_diff_gappy_first_and_clean_fourth",
        # the rest of the teeth, under the name of what each pins — the hollow reading counts
        # DECLARED teeth only, so an undeclared tooth is one a reverted file can never red
        "reread": "test_a_schema_failure_is_re_read_and_a_reader_that_never_satisfies_it_writes_nothing",
        "lanes": "test_the_entry_gate_lists_five_lanes_and_the_fifth_is_the_rehearsal",
        "cap": "test_the_sixth_pass_opens_one_question_naming_the_standing_gaps_and_reads_nothing",
        "probe": "test_the_probe_is_armed_and_measures_enough_at_eight_of_ten_and_fires_at_seven",
        "cli": "test_the_cli_answers_help_and_speaks_standing_as_json_through_the_subprocess_seam",
        "skill": "test_the_machine_is_a_package_and_the_sail_skill_sends_the_builder_to_rehearse_before_buildme",
    },
}
TID = "0badc0ffee01"
STEM = f"{TID}-a-fixture-ticket-that-leaves-one-step-unsaid"
TICKET = {
    "id": TID, "title": "a fixture ticket that leaves one step unsaid",
    "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED",
    "decisions": [{"n": 1, "text": "write the widget", "by": "the proof"},
                  {"n": 2, "text": "prove the widget", "by": "the proof"}],
    "questions": [],
}


def _node(step, state="builds_as_written", assumption="", would_settle="", confidence=0.9):
    return {"step": step, "state": state, "assumption": assumption,
            "would_settle": would_settle, "confidence": confidence}


# D6 as amended (open-d71a52522428): a step is a decision id, or 'unlisted: <text>' when the
# ticket carries no decision for it. The fixture ticket carries D1 and D2; the wiring step is
# the one it leaves unsaid.
WIRE = "unlisted: wire the widget"
CLEAN_TREE = {"nodes": [_node("D1"), _node("D2")]}
CLEAN_TREE_WIRED = {"nodes": [_node("D1"), _node("D2"), _node("D3")]}   # after decide() adds D3
# every carried decision is in every tree (a reading that skips one is handed back);
# what the three readings disagree on is the wiring step nobody decided, and read 3
# alone also sees a lint step — that is the one step_absent left to a reader.
LINT = "unlisted: lint the widget"
GAPPY_TREES = [
    {"nodes": [_node("D1"),
               _node("unlisted: Wire The Widget", "builds_under_assumption", "it hangs off the rack",
                     "say where the widget is wired"),
               _node("D2")]},
    {"nodes": [_node("D1"),
               _node(WIRE, "cannot_proceed", "", "say where the widget is wired"),
               _node("D2")]},
    {"nodes": [_node("D1"),
               _node(WIRE, "builds_under_assumption", "it hangs off the shim",
                     "say where the widget is wired"),
               _node("D2"), _node(LINT)]},
]


class Stub:
    """A reader replaying recorded trees, counting its calls. ``script`` is a list of what
    each call returns (a tree, or None for 'the reader returned nothing'); it cycles."""

    def __init__(self, script):
        self.script, self.calls = list(script), 0

    def __call__(self, text, schema_doc):
        out = self.script[self.calls % len(self.script)]
        self.calls += 1
        self.last_text = text
        self.texts = getattr(self, "texts", []) + [text]
        return (json.loads(json.dumps(out)) if out is not None else None,
                {"model": "stub", "cost_usd": 0.001, "duration_ms": 1})


class World:
    def __init__(self):
        self.dir = Path(tempfile.mkdtemp(prefix="rehearsal-proof-"))
        self.commons = self.dir / "CairnCommons"
        self.cairn = self.dir / "cairn"
        for d in ("tickets", "rehearsals", "questions"):
            (self.commons / d).mkdir(parents=True)
        self.cairn.mkdir()
        self.ticket = self.commons / "tickets" / f"{STEM}.json"
        self.ticket.write_text(json.dumps(TICKET, indent=2) + "\n")
        door.set_diagnostic_roots({"cairn": self.cairn, "CairnCommons": self.commons})

    def close(self):
        door.set_diagnostic_roots(None)
        shutil.rmtree(self.dir, ignore_errors=True)

    def journal(self):
        return door.read_journal(self.commons)

    def env(self):
        return {**os.environ, "PYTHONPATH": str(REPO),
                "CAIRN_ARTIFACT_ROOTS": json.dumps({"cairn": str(self.cairn), "CairnCommons": str(self.commons)})}


def _kw(w):
    return dict(root=w.commons, berths_root=w.dir / "no-berths", repo=w.dir / "no-repo")


# 1 ------------------------------------------------------------------------

def test_an_underspecified_ticket_returns_gaps_naming_the_step_in_every_read():
    w = World()
    try:
        stub = Stub(GAPPY_TREES)
        rec = R.rehearse(TID, reader=stub, **_kw(w))
        assert stub.calls == 3, stub.calls
        assert not rec["clean"] and rec["pass"] == 1, rec
        kinds = {(g["kind"], g["step"].lower()) for g in rec["gaps"]}
        assert ("assumes", WIRE) in kinds and ("cannot_proceed", WIRE) in kinds, kinds
        # an unlisted step is a gap of its own kind in every read that names it (D6 as amended)
        assert ("unlisted", WIRE) in kinds, kinds
        wire = [g for g in rec["gaps"] if g["step"].lower() == WIRE and g["kind"] != "step_absent"]
        assert sorted(set(sum((g["reads"] for g in wire), []))) == [1, 2, 3], wire
        # the fold: 'unlisted: Wire The Widget' and 'unlisted: wire the widget' are ONE step, never a step_absent
        assert not any(g["kind"] == "step_absent" and g["step"].lower() == WIRE for g in rec["gaps"]), rec["gaps"]
        # the lint step is in read 3 only — step_absent in reads 1 and 2; an id can never be
        # step_absent, because a reading missing one is handed back before it counts
        absent = [g for g in rec["gaps"] if g["kind"] == "step_absent"]
        assert absent and absent[0]["step"] == LINT and absent[0]["reads"] == [1, 2], absent
        assert all(g["step"].startswith("unlisted: ") for g in absent), absent
        # D1 and D2 build as written in all three reads under the same id: no gap names them
        assert not any(g["step"] in ("D1", "D2") for g in rec["gaps"]), rec["gaps"]
        # the would_settle line rides the gap
        assert any("say where the widget is wired" in (g.get("would_settle") or []) for g in rec["gaps"])
        # deterministic: the same trees twice → the same list
        reads = [dict(t, read=i + 1) for i, t in enumerate(GAPPY_TREES)]
        assert R.gaps(reads) == R.gaps(reads) == rec["gaps"]
        # the record is on disk, through the door, verb rehearse; the ticket is untouched
        assert Path(rec["path"]).is_file() and rec["record"].startswith("rehearsals/" + TID)
        j = w.journal()
        assert [e["verb"] for e in j] == ["rehearse"], [e["verb"] for e in j]
        assert json.loads(w.ticket.read_text()).get("rehearsal") is None
        # the reader saw the prompt and the ticket, nothing from any repo
        assert "cannot_proceed" in stub.last_text and TID in stub.last_text and "no-repo" not in stub.last_text
    finally:
        w.close()


# 2 ------------------------------------------------------------------------

def test_a_schema_failure_is_re_read_and_a_reader_that_never_satisfies_it_writes_nothing():
    w = World()
    try:
        bad = {"nodes": [{"step": "x", "state": "maybe", "assumption": "", "would_settle": "", "confidence": 2}]}
        stub = Stub([bad, None, CLEAN_TREE])   # each read: bad, nothing, then good
        rec = R.rehearse(TID, reader=stub, **_kw(w))
        assert rec["clean"] and stub.calls == 9, (rec["clean"], stub.calls)
        attempts = rec["meta"]["attempts"]
        assert len(attempts) == 9 and [a["attempt"] for a in attempts[:3]] == [1, 2, 3], attempts
        assert attempts[0]["schema_lacks"] and "state" in " ".join(attempts[0]["schema_lacks"]), attempts[0]
        assert any("neither D<n>" in l for l in attempts[0]["schema_lacks"]), "a free-text step fails the shape"
        assert attempts[1]["schema_lacks"] == ["reader returned nothing"], attempts[1]
        assert attempts[2]["schema_lacks"] == [], attempts[2]
    finally:
        w.close()
    w = World()
    try:
        # a decision id the ticket does not carry is a lack the pattern cannot see — the machine re-reads
        stub = Stub([{"nodes": [_node("D1"), _node("D2"), _node("D9")]},
                     {"nodes": [_node("D1")]},
                     CLEAN_TREE])
        rec = R.rehearse(TID, reader=stub, **_kw(w))
        att = [a["schema_lacks"] for a in rec["meta"]["attempts"]]
        assert len(att[0]) == 1 and "'D9' names a decision the ticket does not carry" in att[0][0], att[0]
        assert att[1] == ["nodes: every decision gets one node; missing ['D2']"], att[1]
        assert rec["clean"] and stub.calls == 9, (rec["clean"], stub.calls)
        # a re-read is told what it lacked — and only its own lack; the first attempt of
        # every read is the bare text (cold to the other reads, D1)
        t = stub.texts
        assert "HANDED BACK" not in t[0] and "HANDED BACK" not in t[3] and "HANDED BACK" not in t[6], "first attempts are cold"
        assert t[1].startswith(t[0]) and "'D9' names a decision the ticket does not carry" in t[1], t[1][-400:]
        assert t[2].startswith(t[0]) and "missing ['D2']" in t[2] and "D9" not in t[2][len(t[0]):], "each re-read carries its own lack, not the history"
        # identity is stamped from truth, never trusted from the reader
        assert rec["reads"][0]["ticket"] == TID and rec["reads"][2]["read"] == 3
    finally:
        w.close()
    w = World()
    try:
        stub = Stub([bad])
        try:
            R.rehearse(TID, reader=stub, **_kw(w))
        except R.ReaderFailed as exc:
            assert "read 1" in str(exc) and stub.calls == R.RETRIES_PER_READ + 1, (exc, stub.calls)
        else:
            raise AssertionError("a reader that never passes the schema must refuse the pass")
        assert not list((w.commons / "rehearsals").iterdir()) and w.journal() == [], "no record on an instrument failure"
    finally:
        w.close()


# 3 ------------------------------------------------------------------------

def test_a_decision_line_answers_the_gap_and_the_next_pass_writes_a_clean_record_over_the_live_bytes():
    w = World()
    try:
        R.rehearse(TID, reader=Stub(GAPPY_TREES), **_kw(w))
        entry = R.decide(TID, WIRE, "the widget is wired off the rack shim", by="Akien verbatim", root=w.commons)
        doc = json.loads(w.ticket.read_text())
        assert doc["decisions"][-1] == entry and entry["n"] == 3 and entry["source"] == "rehearsal", doc["decisions"]
        assert [e["verb"] for e in w.journal()] == ["rehearse", "cast"]
        # the next read names the step by the decision it now has — the loop converges on ids
        rec = R.rehearse(TID, reader=Stub([CLEAN_TREE_WIRED]), **_kw(w))
        # the decide reset the count (open-8b95d8bb20c5, "Reset it fully."), so this is pass 1
        assert rec["clean"] and rec["gaps"] == [] and rec["pass"] == 1, rec
        doc = json.loads(w.ticket.read_text())
        assert doc["rehearsal"] == rec["record"], doc.get("rehearsal")
        live = R._sha(w.ticket.read_bytes())
        assert rec["ticket_sha256"] == live, "the record hashes the bytes the lane will see"
        assert rec["ticket_sha256_at_read"] != live, "the pointer changed the bytes after the read — both hashes kept"
        assert [e["verb"] for e in w.journal()] == ["rehearse", "cast", "cast", "rehearse"]
        st = R.standing(TID, w.commons)
        assert st["ok"] and st["record"] == rec["record"], st
        assert R.passes_since_clean(TID, w.commons) == 0
    finally:
        w.close()


# 4 ------------------------------------------------------------------------

def test_the_sieve_reds_no_rehearsal_and_a_stale_hash_by_name_and_reads_a_clean_one_green():
    from cairn.machines.build_inspector.inspector import buildme_rides_the_rehearsal as sieve
    w = World()
    try:
        f = sieve(TID, root=w.commons)
        assert len(f) == 1 and f[0]["method"] == "buildme_rides_the_rehearsal", f
        v = f[0]["values"]
        assert "no rehearsal pointer" in v["lack"] and f"cairn rehearse {TID}" == v["rehearse_with"], f[0]
        R.rehearse(TID, reader=Stub(GAPPY_TREES), **_kw(w))
        f = sieve(TID, root=w.commons)
        assert len(f) == 1 and "no rehearsal pointer" in f[0]["values"]["lack"], "an unclean pass points nothing"
        R.rehearse(TID, reader=Stub([CLEAN_TREE]), **_kw(w))
        assert sieve(TID, root=w.commons) == [], "a clean current record is green"
        # edited after its rehearsal — through the door, as an edit would be
        doc = json.loads(w.ticket.read_text())
        doc["decisions"].append({"n": 9, "text": "one more thing", "by": "the proof"})
        door.write(str(w.ticket), json.dumps(doc, indent=2) + "\n", verb="cast", why="the proof edits the ticket")
        f = sieve(TID, root=w.commons)
        assert len(f) == 1 and "edited after its rehearsal" in f[0]["values"]["lack"], f
        assert f[0]["values"]["ticket_sha256"] != f[0]["values"]["live_sha256"]
        # the pointer at an unclean record is red too
        doc = json.loads(w.ticket.read_text())
        unclean = [p for p, d in R.records_for(TID, w.commons) if not d.get("clean")]
        assert len(unclean) == 1, "one gappy record stands beside the clean one — same second, two files"
        doc["rehearsal"] = "rehearsals/" + unclean[0].name
        door.write(str(w.ticket), json.dumps(doc, indent=2) + "\n", verb="cast", why="the proof repoints the ticket")
        f = sieve(TID, root=w.commons)
        assert len(f) == 1 and "is not clean" in f[0]["values"]["lack"], f
        # a ticket that is not on file is the chokepoint's refusal, not this sieve's
        assert sieve("ffffffffffff", root=w.commons) == []
    finally:
        w.close()


def test_the_entry_gate_lists_five_lanes_and_the_fifth_is_the_rehearsal():
    from cairn.tools.base import transitions
    import cairn.machines.build_inspector.inspector as I
    w = World()
    try:
        tickets = w.dir / "gate-tickets"
        tickets.mkdir()
        (tickets / "widget.json").write_text("{}")
        berths = w.dir / "gate-berths"
        (berths / "0" / "packets").mkdir(parents=True)
        saved = transitions._TICKETS, I._CHART_BERTHS
        transitions._TICKETS, I._CHART_BERTHS = tickets, berths
        try:
            record = transitions.inspect_entry("widget")
        finally:
            transitions._TICKETS, I._CHART_BERTHS = saved
        names = [e["identity"] for e in record]
        assert len(names) == 5 and names[-1] == "the_ticket_rehearses_clean", names
        src = (REPO / "cairn/tools/base/transitions.py").read_text()
        assert src.count('_sieve_lane("the_ticket_rehearses_clean"') == 1
    finally:
        w.close()


# 5 ------------------------------------------------------------------------

def test_the_sixth_pass_opens_one_question_naming_the_standing_gaps_and_reads_nothing():
    from cairn.tools.question import question as Q
    w = World()
    try:
        stub = Stub(GAPPY_TREES)
        for i in range(R.PASS_CAP):
            rec = R.rehearse(TID, reader=stub, **_kw(w))
            assert rec["pass"] == i + 1 and not rec["clean"]
        assert stub.calls == 3 * R.PASS_CAP
        out = R.rehearse(TID, reader=stub, **_kw(w))
        assert stub.calls == 3 * R.PASS_CAP, "the sixth pass reads nothing"
        assert out.get("question", "").startswith("open-") and out["passes"] == R.PASS_CAP, out
        qs = Q.open_for(TID, root=w.commons / "questions")
        assert len(qs) == 1 and qs[0]["id"] == out["question"] and qs[0]["source"] == "rehearsal", qs
        assert "wire the widget" in qs[0]["question"] and qs[0]["question"].endswith("?"), qs[0]["question"]
        assert "say where the widget is wired" in qs[0]["question"]
        assert out["question"] in json.loads(w.ticket.read_text())["questions"], "both ends of the link"
        assert len(list((w.commons / "rehearsals").iterdir())) == R.PASS_CAP, "no sixth record"
        # a seventh call opens nothing new — the one question stands
        out2 = R.rehearse(TID, reader=stub, **_kw(w))
        assert out2["question"] == out["question"] and out2.get("already_open"), out2
        assert len(Q.open_for(TID, root=w.commons / "questions")) == 1, "ONE question, not one per call"
        # his answer is the new input: the loop starts over — the next call READS again and
        # writes pass 1, and opens no second question (measured red 2026-09-17 on a705346aa75c)
        Q.answer(out["question"], "the widget is wired in bin/widget.sh", spawned=[],
                 root=w.commons / "questions")
        assert R.passes_since_clean(TID, w.commons) == 0, "an answered question resets the cap"
        rec = R.rehearse(TID, reader=stub, **_kw(w))
        assert stub.calls == 3 * (R.PASS_CAP + 1), "after the answer the reader reads again"
        assert rec.get("pass") == 1 and "question" not in rec, rec
        assert len(Q.open_for(TID, root=w.commons / "questions")) == 0, "no second question"
        # a gap disposed with --decide is new input too, and resets FULLY (open-8b95d8bb20c5,
        # Akien 2026-09-23: "Reset it fully.") — else the CLI's own "dispose each: --decide,
        # then rehearse again" is unreachable at the cap. Run to the cap once more, decide.
        time.sleep(1.1)   # the answer reset is stamped to the second; step past it
        while R.passes_since_clean(TID, w.commons) < R.PASS_CAP:
            R.rehearse(TID, reader=stub, **_kw(w))
        time.sleep(1.1)
        entry = R.decide(TID, WIRE, "the widget is wired in bin/widget.sh", by="the proof", root=w.commons)
        assert entry.get("at"), "a decide line carries when it was made, or it can reset nothing"
        assert R.passes_since_clean(TID, w.commons) == 0, "a --decide resets the cap fully"
        wired = Stub([{"nodes": t["nodes"] + [_node("D3")]} for t in GAPPY_TREES])
        rec = R.rehearse(TID, reader=wired, **_kw(w))
        assert wired.calls == 3 and rec.get("pass") == 1 and "question" not in rec, rec
        assert len(Q.open_for(TID, root=w.commons / "questions")) == 0, "a decide opens no question"
    finally:
        w.close()


# 6 ------------------------------------------------------------------------

def test_the_prompt_says_the_job_is_the_tree_and_cannot_proceed_is_legal_and_the_schema_mirrors_validate():
    text = R.prompt()
    assert "Your job is the TREE, not the code" in text, "the prompt must say the job is the tree"
    assert "cannot_proceed" in text and "correct answer, not a failure" in text, "cannot_proceed must be a legal answer"
    assert "no repository" in text.lower() or "no repository, no shell" in text
    s = R.schema()
    node = s["properties"]["nodes"]["items"]
    assert tuple(node["properties"]["state"]["enum"]) == R.STATES
    assert sorted(node["required"]) == sorted(["step", "state", "assumption", "would_settle", "confidence"])
    assert s["properties"]["read"]["maximum"] == R.READS
    assert R.validate({"nodes": [_node("unlisted: x", st) for st in R.STATES]}) == []
    assert R.validate({"nodes": [_node("D1"), _node("D12")]}) == [], "any D<n> passes the shape alone"
    assert R.validate({"nodes": [_node("D1"), _node("D12")]}, {1}) == ["nodes[1].step: 'D12' names a decision the ticket does not carry (it has [1])"]
    assert R.validate({"nodes": [_node("D1")]}, {1, 2}) == ["nodes: every decision gets one node; missing ['D2']"]
    assert R.validate({"nodes": [_node("D1"), _node("D2"), _node("D2")]}, {1, 2}) == ["nodes: every decision gets one node; doubled ['D2']"]
    assert R.validate({"nodes": [_node("D1"), _node("D2"), _node("unlisted: x")]}, {1, 2}) == []
    assert R.validate({"nodes": []}) and R.validate({"nodes": [{"step": "x"}]}) and R.validate([])
    assert R.validate({"nodes": [_node("x")]}) and R.validate({"nodes": [_node("D0")]}) and R.validate({"nodes": [_node("unlisted:")]})
    assert R.validate({"nodes": [dict(_node("unlisted: x"), extra=1)]}), "additionalProperties: false"
    import re as _re
    pat = _re.compile(node["properties"]["step"]["pattern"])
    for good in ("D1", "D42", "unlisted: wire it"):
        assert pat.match(good) and R.STEP_RE.match(good), good
    for bad in ("x", "D0", "d1", "unlisted:", "unlisted: "):
        assert not pat.match(bad) and not R.STEP_RE.match(bad), bad
    assert "D<n>" in text and "unlisted:" in text, "the prompt teaches the step vocabulary"
    assert "exactly\n  one node" in text or "exactly one node" in text.replace("\n  ", " "), "one node per decision, always"
    assert "unlisted" in R.GAP_KINDS
    # open-a57cdd7cf3c1 (Akien 2026-09-23): the reader judges each decision against the whole
    # list — a piece another decision settles is settled, and a later decision governs
    assert "against the WHOLE list" in text and "the later one governs" in text, "the whole-list rule"


# 7 ------------------------------------------------------------------------

def test_the_probe_is_armed_and_measures_enough_at_eight_of_ten_and_fires_at_seven():
    import importlib
    m = importlib.import_module("cairn.machines.rehearsal.probes.the_rehearsal_predicts_the_build")
    p = m.PROBE
    assert p.carry is not None and p.enough is not None and p.to == "harbor_master", p
    w = World()
    try:
        def seed(n_total, n_empty):
            for f in (w.commons / "rehearsals").glob("*.json"):
                f.unlink()
            for i in range(n_total):
                empty = i < n_empty
                (w.commons / "rehearsals" / f"{i:012x}-20260915T00000{i}.json").write_text(json.dumps({
                    "ticket": f"{i:012x}", "clean": True,
                    "divergence": {"steps_unproved": [] if empty else ["a step"], "teeth_unforeseen": [], "matched": []}}))
        seed(10, 8)
        ctx = {}
        assert not p.trigger(None, ctx) and p.enough(ctx) and p.carry(ctx)["empty_divergence"] == 8, ctx
        seed(10, 7)
        ctx = {}
        assert p.trigger(None, ctx) and not p.enough(ctx) and "WRONG-INTENT" in p.carry(ctx)["finding"], ctx
        seed(9, 9)
        ctx = {}
        assert not p.trigger(None, ctx) and not p.enough(ctx), "nine is not ten"
    finally:
        w.close()


# 8 ------------------------------------------------------------------------

def test_after_proved_the_divergence_is_written_onto_the_clean_record_both_ways():
    w = World()
    try:
        R.rehearse(TID, reader=Stub([CLEAN_TREE]), **_kw(w))
        proof = w.dir / "test_widget.py"
        proof.write_text("def test_write_the_widget_lands():\n    pass\n\n"
                         "def test_the_rack_hums():\n    pass\n")
        d = R.record_divergence(TID, [proof], root=w.commons)
        assert d["steps_unproved"] == ["prove the widget"], d
        assert d["teeth_unforeseen"] == ["test_the_rack_hums"], d
        assert d["matched"] == [["write the widget", "test_write_the_widget_lands"]], d
        assert R.step_text("unlisted: wire the widget", {}) == "wire the widget" and R.step_text("D7", {}) == "D7"
        rec = json.loads((w.commons / json.loads(w.ticket.read_text())["rehearsal"]).read_text())
        assert rec["divergence"]["steps_unproved"] == ["prove the widget"] and rec["divergence"]["proofs"] == [str(proof)]
        assert w.journal()[-1]["verb"] == "rehearse" and "divergence" in w.journal()[-1]["why"]
        assert R.divergence(["a", "b"], []) == {"steps_unproved": ["a", "b"], "teeth_unforeseen": [], "matched": []}
    finally:
        w.close()


# 9 ------------------------------------------------------------------------

def test_the_cli_answers_help_and_speaks_standing_as_json_through_the_subprocess_seam():
    w = World()
    try:
        cli = [str(REPO / "bin" / "cairn"), "rehearse"]
        r = subprocess.run(cli + ["--help"], capture_output=True, text=True, env=w.env(), timeout=120)
        assert r.returncode == 0 and "--decide" in r.stdout and "--proved" in r.stdout, r.stdout[-300:] + r.stderr[-300:]
        r = subprocess.run(cli + [TID, "--standing"], capture_output=True, text=True, env=w.env(), timeout=120)
        assert r.returncode == 0, r.stderr[-400:]
        st = json.loads(r.stdout)
        assert st["ok"] is False and "no rehearsal pointer" in st["lack"], st
        r = subprocess.run(cli + [TID, "--DECIDE", WIRE, "off the shim"],
                           capture_output=True, text=True, env=w.env(), timeout=120)
        assert r.returncode == 2 and "--by" in r.stderr, (r.returncode, r.stderr[-200:])
        r = subprocess.run(cli + [TID, "--decide", WIRE, "off the shim", "--by", "the proof"],
                           capture_output=True, text=True, env=w.env(), timeout=120)
        assert r.returncode == 0 and "decided D3" in r.stdout, r.stdout + r.stderr[-300:]
        assert json.loads(w.ticket.read_text())["decisions"][-1]["text"] == "off the shim"
    finally:
        w.close()


# 11 -----------------------------------------------------------------------

def test_the_live_fires_recorded_reads_replay_through_the_diff_gappy_first_and_clean_fourth():
    """Clause 6 of the falsifier is the live fire, and a live Haiku call is never a proof
    tooth (D15). What the proof CAN pin is the live fire's evidence: the three real reads of
    pass 1 (12/16/12 free-text steps, 46 gaps) and pass 4 (36/36/36 decision-id nodes, 0
    gaps) are berthed under fixtures/ and replayed through the same ``gaps`` and ``validate``
    the live run used. A hollow build with the diff reverted cannot reproduce either number."""
    fx = Path(__file__).resolve().parent / "fixtures"
    one = json.loads((fx / "live_fire_pass1.json").read_text())
    four = json.loads((fx / "live_fire_pass4.json").read_text())
    assert one["pass"] == 1 and not one["clean"] and four["pass"] == 4 and four["clean"], (one["pass"], four["pass"])
    # pass 1: three cold reads over the un-amended ticket — every read names a gap, the
    # recorded count is reproduced, and the same trees twice give the same list (D6)
    g1 = R.gaps(one["reads"])
    assert len(g1) == one["gaps_recorded"] == 46, (len(g1), one["gaps_recorded"])
    assert sorted(set(sum((g["reads"] for g in g1), []))) == [1, 2, 3], "a read that named no gap"
    assert {g["kind"] for g in g1} >= {"assumes", "step_absent"}, {g["kind"] for g in g1}
    assert R.gaps(one["reads"]) == g1
    # pass 4: three reads that each carry every one of the 36 decisions once, and agree
    ids = set(range(1, 37))
    for t in four["reads"]:
        assert R.validate(t, ids) == [], R.validate(t, ids)
        assert sorted(n["step"] for n in t["nodes"]) == sorted(f"D{i}" for i in ids)
    assert R.gaps(four["reads"]) == [] and four["gaps_recorded"] == 0
    # the reads are the live reader's, not a stub's: three distinct sha-stamped reads per pass
    for rec in (one, four):
        assert [t["read"] for t in rec["reads"]] == [1, 2, 3] and len({t["ticket_sha256"] for t in rec["reads"]}) == 1
        assert rec["cost_usd"] > 0.5, rec["cost_usd"]
    assert one["reads"][0]["ticket_sha256"] != four["reads"][0]["ticket_sha256"]


# 12 -----------------------------------------------------------------------

def test_the_machine_is_a_package_and_the_sail_skill_sends_the_builder_to_rehearse_before_buildme():
    """The build's two non-code writes: the package init that makes ``cairn.machines.rehearsal``
    importable as a machine (not a namespace accident), and the /sail step that is the only
    mouth telling a builder the lane exists. Both were hollow on the first reading (2026-09-15)."""
    assert (REPO / "cairn" / "machines" / "rehearsal" / "__init__.py").is_file()
    skill = (REPO / "skills" / "sail" / "SKILL.md").read_text(encoding="utf-8")
    assert "cairn rehearse <ticket-id>" in skill, "the skill never tells the builder to rehearse"
    assert "the_ticket_rehearses_clean" in skill, "the skill never names the lane that holds the crossing"
    assert "--decide" in skill and "cairn question open" in skill, "the skill never says how a gap is disposed"
    assert skill.index("cairn rehearse <ticket-id>") < skill.index("## 1. Journal BUILDME"), \
        "the rehearsal step must come before the BUILDME crossing"


def main() -> int:
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    assert len(teeth) >= 12, len(teeth)
    failed = []
    for tooth in teeth:
        # every tooth runs, whatever the one before it did: a run that stops at the first red
        # prints no teeth, and a hollow reading cannot tell that from a proof that never ran
        try:
            tooth()
        except Exception as e:                       # noqa: BLE001 — the reason is the record
            failed.append(tooth.__name__)
            print(f"  FAIL  {tooth.__name__}: {type(e).__name__}: {str(e)[:300]}")
            continue
        print(f"  PASS  {tooth.__name__}")
    if failed:
        print(f"red — {len(failed)} of {len(teeth)} teeth: {', '.join(failed)}")
        return 1
    print(f"green — {len(teeth)} teeth: the rehearsal machine renders, reads through an injectable "
          "reader, re-reads a schema failure, diffs three trees into deterministic gaps, disposes a gap "
          "as a decision line, writes clean and unclean records through the door, holds the fifth "
          "BUILDME lane on a missing or stale rehearsal, opens one question at the pass cap, arms the "
          "WATCHME probe, writes the post-PROVED divergence, and replays the live fire's recorded "
          "reads to the recorded numbers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
