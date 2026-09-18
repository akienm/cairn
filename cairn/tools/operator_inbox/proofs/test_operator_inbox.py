"""Proof: operator inbox reads live state and matches independent reads."""

import json
from pathlib import Path

from cairn.tools.operator_inbox.inbox import (
    gather_all,
    format_inbox,
    format_summary,
    read_troubles,
    read_adjudications,
    read_lap,
    read_questions,
    read_tickets,
    read_ideas,
    read_intentions,
    show_artifact,
    SECTION_ORDER,
    TICKETS_DIR,
    IDEAS_DIR,
    QUESTIONS_DIR,
    INTENTIONS_DIR,
    TERMINAL_STATES,
)

# The reader's own label derivation (cursor_of, status_label, with_derived_phase) is bound
# at CALL time inside the tooth that checks it — 3feb201c84ea added those names, and a
# proof that binds them at import cannot reach its first tooth under a hollow reading.
PROVES = {
    "3feb201c84ea": {"1": "test_tickets_match_independent_read"},
    # 3ed960cc402e — an idea past idea is not an open idea (Akien 2026-09-07)
    "3ed960cc402e": {
        "1": "test_read_ideas_reports_only_the_open_one",
        "2": "test_read_intentions_reports_only_the_one_without_a_ticket",
        "3": "test_ideas_match_independent_read",
        "4": "test_the_dead_from_idea_rule_is_gone",
        "5": "test_inbox_and_dashboard_print_the_same_open_idea_and_intention_counts",
    },
}


def test_troubles_match_independent_read():
    from cairn.devices.trouble.trouble import TroubleDevice
    td = TroubleDevice()
    independent_live = [t for t in td.all() if t.get("standing") != "CLEARED"]
    result = read_troubles()
    assert result["live_count"] == len(independent_live)


def test_adjudications_match_independent_read():
    from cairn.machines.skill_block.skill_block import pending_reviews
    independent = pending_reviews()
    result = read_adjudications()
    assert result["count"] == len(independent)
    independent_ids = {f.get("berth_id") for f in independent}
    result_ids = {f.get("berth_id") for f in result["findings"]}
    assert result_ids == independent_ids


def test_questions_match_independent_read():
    """``resolved`` is the discriminator, not the filename: since ticket 9adc6fddf185
    (2026-09-14) an answered question keeps its ``open-`` name and carries ``resolved``.
    The independent read counts what the lane's contract counts — unresolved, plus
    unreadable (which counts as unresolved, Law 7). Stale form found red 2026-09-15
    (1 open against 7 files) while ticket fb988505c5cb sealed this file."""
    result = read_questions()
    if QUESTIONS_DIR.exists():
        independent = 0
        for p in QUESTIONS_DIR.glob("open-*.json"):
            try:
                doc = json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                independent += 1
                continue
            if not (isinstance(doc, dict) and doc.get("resolved")):
                independent += 1
        assert result["count"] == independent
    else:
        assert result["count"] == 0


def test_tickets_match_independent_read():
    from cairn.tools.operator_inbox.inbox import cursor_of, status_label, with_derived_phase
    result = read_tickets()
    independent_count = 0
    if TICKETS_DIR.exists():
        for p in TICKETS_DIR.glob("*.json"):
            if p.name.startswith("_"):
                continue
            try:
                t = json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if not isinstance(t, dict) or t.get("role") in ("store-charter", "charter"):
                continue
            if not isinstance(t.get("workflow_and_state"), str):
                continue
            label = status_label(cursor_of(t["workflow_and_state"]))
            if label.split(":")[0] in TERMINAL_STATES:
                continue
            independent_count += 1
    assert result["total_not_done"] == independent_count
    # one status: every record's label IS status_label(cursor_of(its own state string)),
    # with the DERIVED in-process phase overlaid (ruling 2026-09-08: in-process is runtime
    # state, never stored, so the file says :waiting while a live sail says :in-process —
    # found red 2026-09-15 with ticket fb988505c5cb's own voyage in flight).
    for r in result["records"]:
        own = json.loads(Path(r["source"]).read_text())["workflow_and_state"]
        assert r["label"] == status_label(with_derived_phase(cursor_of(own), r["id"])), \
            (r["id"], r["label"], own[:80])


# --- moved on (ticket 3ed960cc402e): an artifact past its stage is not reported at it ---

def _fixture_stages(root: Path) -> dict:
    """Four ideas and two intentions with a KNOWN answer: exactly one of each is open.
    A hollow read_ideas (folder census) answers 4; a hollow read_intentions answers 2."""
    ideas = root / "ideas"
    intentions = root / "intentions"
    tickets = root / "tickets"
    firings = root / "skill_block_instance"
    for d in (ideas, intentions, tickets, firings / "berths" / "intent",
              firings / "logs" / "reviewed" / "intent"):
        d.mkdir(parents=True)
    for stem in ("2026-01-01-cited-by-a-ticket", "2026-01-02-named-by-a-firing",
                 "2026-01-03-acted-on", "2026-01-04-still-open"):
        (ideas / f"{stem}.json").write_text(json.dumps({
            "prose": f"idea {stem}", "author": "Akien",
            **({"acted_on": True, "acted_on_note": "hand-set"} if stem.endswith("acted-on") else {}),
        }))
    (ideas / "_store.json").write_text("{}")                    # underscore files are not ideas
    (intentions / "I-with-a-ticket.md").write_text("# with a ticket\n")
    (intentions / "I-no-ticket-yet.md").write_text("# no ticket yet\n")
    (tickets / "aaaaaaaaaaaa-fixture.json").write_text(json.dumps({
        "id": "aaaaaaaaaaaa", "title": "fixture",
        "owning_intention": "intentions-not-beside-code/I-with-a-ticket.md",
        "linked_ideas": ["2026-01-01-cited-by-a-ticket"],
        "workflow_and_state": "code-seam@v2: THINKME -> [TICKETME] -> BUILDME -> PROVED",
    }))
    # one firing per lane shape: a swept (reviewed) one names an idea WITH the .json
    # suffix the way the 2026-08-09 firing did; a fresh berth says "none, because…"
    (firings / "logs" / "reviewed" / "intent" / "intent-1.json").write_text(json.dumps({
        "skill": "intent", "answers": {"from_idea": "2026-01-02-named-by-a-firing.json"}}))
    (firings / "berths" / "intent" / "intent-2.json").write_text(json.dumps({
        "skill": "intent", "answers": {"from_idea": "None, because it came from a chat"}}))
    return {"ideas_dir": ideas, "intentions_dir": intentions,
            "tickets_dir": tickets, "firings_root": firings}


def test_read_ideas_reports_only_the_open_one():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f = _fixture_stages(Path(td))
        result = read_ideas(ideas_dir=f["ideas_dir"], tickets_dir=f["tickets_dir"],
                            firings_root=f["firings_root"])
        assert result["count"] == 1, result
        assert [i["id"] for i in result["items"]] == ["2026-01-04-still-open"]
        assert result["moved_on"] == 3


def test_moved_on_names_each_voice():
    import tempfile
    from cairn.tools.operator_inbox.inbox import moved_on
    with tempfile.TemporaryDirectory() as td:
        f = _fixture_stages(Path(td))
        gone = moved_on(["2026-01-01-cited-by-a-ticket", "2026-01-02-named-by-a-firing",
                         "2026-01-03-acted-on", "2026-01-04-still-open"],
                        tickets_dir=f["tickets_dir"], firings_root=f["firings_root"],
                        acted_on={"2026-01-03-acted-on"})
        assert gone == {
            "2026-01-01-cited-by-a-ticket": ["a ticket cites it"],
            "2026-01-02-named-by-a-firing": ["an /intent firing names it"],
            "2026-01-03-acted-on": ["its record carries acted_on"],
        }, gone


def test_read_intentions_reports_only_the_one_without_a_ticket():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f = _fixture_stages(Path(td))
        result = read_intentions(intentions_dir=f["intentions_dir"],
                                 tickets_dir=f["tickets_dir"])
        assert result["count"] == 1, result
        assert result["items"] == ["I-no-ticket-yet"]
        assert result["moved_on"] == 1


def test_gather_all_threads_the_fixture_roots():
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        f = _fixture_stages(Path(td))
        data = gather_all(**f)
        assert data["ideas"]["count"] == 1
        assert data["intentions"]["count"] == 1
        text = format_inbox(data)
        assert "IDEAS (1 open, not yet at intent; 3 moved on)" in text, text


def test_ideas_match_independent_read():
    """Live commons: the count equals an INDEPENDENT second read that shares no code
    with the reader — a fresh glob of firings, a fresh scan of ticket text."""
    from cairn.machines.skill_block.skill_block import berth_root
    result = read_ideas()
    if not IDEAS_DIR.exists():
        assert result["count"] == 0
        return
    firings_named = set()
    for p in berth_root().parent.glob("**/intent/*.json"):
        try:
            fi = json.loads(p.read_text()).get("answers", {}).get("from_idea")
        except Exception:
            continue
        if isinstance(fi, str) and fi and not fi.lower().startswith("none"):
            firings_named.add(fi.strip().removesuffix(".json"))
    ticket_text = "\n".join(p.read_text() for p in TICKETS_DIR.glob("*.json")
                            if not p.name.startswith("_"))
    open_stems = []
    for p in IDEAS_DIR.glob("*.json"):
        if p.stem.startswith("_"):
            continue
        rec = json.loads(p.read_text())
        if p.stem in firings_named or p.stem in ticket_text or rec.get("acted_on") is True:
            continue
        open_stems.append(p.stem)
    assert result["count"] == len(open_stems), (result["count"], sorted(open_stems))
    assert sorted(i["id"] for i in result["items"]) == sorted(open_stems)

    # the two probes beside the reader run over the same live commons and must agree
    # with it: the WATCHME(idea-past-idea) probe this ticket carries reads the open
    # ideas through the one reader and, with today pushed far ahead, calls every one
    # of them stale with the same two voices answered "no" this walk answered; and the
    # inbox-matches-live-state probe's independent reads (the review lane walked by
    # hand, questions discriminated by `resolved`, not by filename) match every
    # section the script prints. Both are read from disk, so a reverted or removed
    # probe reds here instead of reading hollow.
    from datetime import date
    from cairn.tools.base.probe import Probe
    from cairn.tools.operator_inbox.probes import an_open_idea_that_went_stale as stale_probe
    from cairn.tools.operator_inbox.probes import operator_inbox_matches_live_state as match_probe
    for mod in (stale_probe, match_probe):
        assert isinstance(mod.PROBE, Probe) and mod.PROBE.carry and mod.PROBE.enough, mod.__name__
    assert stale_probe._OWNING_TICKET == "3ed960cc402e"
    far = stale_probe.survey(today=date(2099, 1, 1))
    assert far["open"] == result["count"] and far["moved_on"] == result["moved_on"], far
    assert len(far["stale"]) == far["open"] and far["would_bite"] == bool(far["open"]), far
    assert sorted(s["stem"] for s in far["stale"]) == sorted(open_stems), far["stale"]
    for entry in far["stale"]:
        assert entry["an /intent firing names it"] is False, entry
        assert entry["a ticket cites it"] is False, entry
    checked = match_probe._check_all()
    assert checked["mismatches"] == [], checked["mismatches"]
    assert checked["current_counts"]["ideas"] == result["count"], checked["current_counts"]
    assert checked["current_counts"]["intentions"] == read_intentions()["count"], checked["current_counts"]


def test_intentions_match_independent_read():
    result = read_intentions()
    if not INTENTIONS_DIR.exists():
        assert result["count"] == 0
        return
    ticket_text = "\n".join(p.read_text() for p in TICKETS_DIR.glob("*.json")
                            if not p.name.startswith("_"))
    open_stems = sorted(p.stem for p in INTENTIONS_DIR.glob("I-*.md")
                        if p.stem not in ticket_text)
    assert result["items"] == open_stems


def test_the_dead_from_idea_rule_is_gone():
    """The rule that read 65 ideas as open matched ticket fields no ticket carries.
    It must not survive beside the new reader (Law 1: one reader)."""
    src = (Path(__file__).resolve().parents[1] / "inbox.py").read_text()
    assert "_acted_on_idea_ids" not in src
    assert 'get("provenance"' not in src


def test_inbox_and_dashboard_print_the_same_open_idea_and_intention_counts():
    """3ed960cc402e clause (5): the inbox and the codemother dashboard print the same
    open-idea count and the same open-intention count — one reader, two surfaces. Read
    over the live commons; the invariant is agreement, never a snapshot of the number."""
    import re
    from cairn.devices.codemother.dashboard import format_dashboard
    data = gather_all()
    inbox, dash, summary = format_inbox(data), format_dashboard(data), format_summary(data)

    def one(pattern, text, where):
        hits = re.findall(pattern, text, re.M)
        assert len(hits) == 1, f"{where}: expected one match for {pattern!r}, got {hits}"
        return int(hits[0])

    inbox_ideas = one(r"^-- IDEAS \((\d+) open, not yet at intent; \d+ moved on\)", inbox, "inbox")
    inbox_intents = one(r"^-- INTENTIONS \((\d+) open, no ticket yet; \d+ moved on\)", inbox, "inbox")
    dash_ideas = one(r"^  IDEAS: (\d+) open \(not yet at intent; \d+ moved on\)", dash, "dashboard")
    dash_intents = one(r"^  INTENTIONS: (\d+) open \(no ticket yet; \d+ moved on\)", dash, "dashboard")
    assert inbox_ideas == dash_ideas == data["ideas"]["count"], (inbox_ideas, dash_ideas)
    assert inbox_intents == dash_intents == data["intentions"]["count"], (inbox_intents, dash_intents)
    assert f"{data['intentions']['count']} open intention(s)" in summary, summary
    assert f"{data['ideas']['count']} open idea(s)" in summary, summary
    # the ruled section order carries intentions between tickets and ideas, and the
    # rendered inbox honours it — before this tooth the section was ruled and never printed
    assert 0 < inbox.find("  TICKETS (") < inbox.find("-- INTENTIONS (") < inbox.find("-- IDEAS ("), inbox


def test_format_produces_output():
    data = gather_all()
    output = format_inbox(data)
    assert "OPERATOR INBOX" in output
    assert "ARTIFACT" in output or "artifact" in output.lower() or "review" in output.lower()
    assert "TROUBLES" in output or "troubles" in output.lower()
    assert len(output) > 100


def test_section_order_is_ruled():
    """Troubles moved below the operator's sections 2026-09-15 (ticket fb988505c5cb,
    Akien: "that leaves me ideas and intentions only") — a live trouble is CC's
    deterministic red, rendered so he can see it, after everything that is his."""
    assert SECTION_ORDER == [
        "email", "adjudications", "lap", "questions", "design",
        "troubles", "tickets", "intentions", "ideas",
    ]


def test_troubles_render_under_a_cc_owned_lane_after_the_operators_sections():
    """The lane says who owns it, sits after the review lane and the questions, and the
    live count still rides the summary line at the top (Law 7 loudness kept)."""
    data = gather_all()
    live = [{"id": "trouble-zzzz", "standing": "OPEN", "why": "WHYMARKERZZZZ"}]
    data = dict(data, troubles={"live": live, "live_count": 1, "total_count": 1},
                adjudications={"findings": [{"berth_id": "abc", "skill": "intent",
                                             "title": "t", "when": "", "bullets": []}],
                               "count": 1})
    out = format_inbox(data)
    i_sum = out.find("1 live trouble(s)")
    i_lane = out.find("LIVE TROUBLES (1) — CC owns these")
    i_rev = out.find("ARTIFACTS AWAITING REVIEW")
    i_why = out.find("WHYMARKERZZZZ")
    assert -1 < i_sum < i_rev < i_lane < i_why, (i_sum, i_rev, i_lane, i_why)
    assert "TROUBLES NEEDING OPERATOR ATTENTION" not in out
    zero = format_inbox(dict(data, troubles={"live": [], "live_count": 0, "total_count": 3}))
    assert "TROUBLES: 0 live (3 exist, all CLEARED)" in zero


def test_no_akien_in_headers():
    data = gather_all()
    output = format_inbox(data)
    for line in output.split("\n"):
        if line.strip().startswith("--") or "INBOX" in line:
            assert "AKIEN" not in line.upper() or "AKIEN" in line, \
                f"Header uses 'Akien' instead of 'Operator': {line}"


def test_emit_finding_subject_kwarg():
    from cairn.machines.learning_block.learning_block import emit_finding
    import tempfile
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        rec_with = emit_finding('test:subj', [{'text': 'b', 'stratum': 'code'}],
                                subject='the aim in plain words', root=root)
        assert rec_with['data']['subject'] == 'the aim in plain words'

        rec_without = emit_finding('test:nosubj', [{'text': 'b', 'stratum': 'code'}],
                                   root=root)
        assert 'subject' not in rec_without['data']


def test_adjudication_shows_berth_and_skill():
    finding_a = {
        'berth_id': 'aabbccddee00',
        'skill': 'idea',
        'when': '2026-08-27T12:00:00',
        'bullets': [{'text': 'a note', 'stratum': 'code'}],
    }
    finding_b = {
        'berth_id': 'ff0011223344',
        'skill': 'sorted',
        'when': '2026-08-27T13:00:00',
        'bullets': [{'text': 'sorted note', 'stratum': 'code'}],
    }
    data = gather_all()
    data['adjudications'] = {'findings': [finding_a, finding_b], 'count': 2}
    output = format_inbox(data)
    assert 'aabbccddee00' in output
    assert 'ff0011223344' in output
    assert '[idea]' in output
    assert '[sorted]' in output


def test_format_uses_operator_not_akien():
    data = gather_all()
    output = format_inbox(data)
    for line in output.split("\n"):
        upper = line.strip().upper()
        if upper.startswith("--") or upper.startswith("==") or "INBOX" in upper:
            assert "AKIEN" not in upper, \
                f"Structural line uses 'Akien' instead of 'Operator': {line}"


def test_format_summary_carries_ticket_breakdown():
    data = gather_all()
    summary = format_summary(data)
    assert "ticket" in summary.lower()
    if data["tickets"]["total_not_done"]:
        assert "BUILDME" in summary or "TICKETME" in summary or "PROVEME" in summary


def test_show_artifact_unknown_id():
    result = show_artifact("zzz_nonexistent_prefix")
    assert "no pending artifact" in result


def test_show_artifact_known_prefix():
    result = read_adjudications()
    if result["count"] > 0:
        bid = result["findings"][0]["berth_id"]
        output = show_artifact(bid[:6])
        assert "ARTIFACT" in output
        assert bid[:12] in output


def test_read_lap_empty():
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        result = read_lap(adjudications_dir=Path(td))
        assert result["count"] == 0
        assert result["items"] == []


def test_read_lap_surfaces_unresolved():
    import tempfile
    from pathlib import Path
    with tempfile.TemporaryDirectory() as td:
        d = Path(td)
        (d / "open.json").write_text(json.dumps({
            "id": "test-open", "whose": "akien", "what": "decide this"}))
        (d / "closed.json").write_text(json.dumps({
            "id": "test-closed", "whose": "akien", "what": "done",
            "resolved": {"at": "2026-01-01"}}))
        result = read_lap(adjudications_dir=d)
        assert result["count"] == 1
        assert result["items"][0]["id"] == "test-open"


def test_gather_all_includes_lap():
    data = gather_all()
    assert "lap" in data
    assert "count" in data["lap"]


def test_the_lane_probe_is_armed_and_measures_a_scratch_world():
    """Ticket fb988505c5cb (2026-09-15), falsifier clause (5) + WRONG INTENT: the WATCHME
    probe the_lane_holds_only_his_decisions is armed (module-level PROBE with callable
    trigger/carry/enough) and, handed a scratch world through its pulse context, reads
    the lane as pending_reviews does — a berth named by a [PROVED] ticket drained, one
    named by a [BUILDME] ticket kept, zero terminal-ticket berths left in the lane — and
    reads a LACK the moment a question bound to the ticket is raised by Akien rather than
    by the cc caller class. No read touches the live commons: every root is scratch."""
    from cairn.devices.tester.scratch import scratch_dir
    from cairn.tools.operator_inbox.probes import the_lane_holds_only_his_decisions as probe_mod

    probe = probe_mod.PROBE
    assert callable(probe.trigger) and callable(probe.carry) and callable(probe.enough)
    assert probe.to == "codemother"

    root = scratch_dir("lane-probe-proof-")
    berths, tickets, ideas, questions = (root / "berths", root / "tickets",
                                         root / "ideas", root / "questions")
    for d in (berths / "intent", berths / "sorted", tickets, ideas, questions):
        d.mkdir(parents=True)
    reviewed = root / "reviewed.jsonl"
    reviewed.write_text("")

    def berth(skill, fid):
        p = berths / skill / f"{skill}-20260915T000000-{fid}.json"
        p.write_text(json.dumps({"skill": skill, "finding_id": fid, "title": fid,
                                 "when": "2026-09-15T00:00:00", "exit": "routed_forward",
                                 "bullets": [], "answers": {}}))
        return p

    proved = berth("intent", "proved-intent")
    kept = berth("sorted", "buildme-sorted")
    (tickets / "aaaaaaaaaaaa-scratch.json").write_text(json.dumps({
        "id": "aaaaaaaaaaaa", "intent_berth": str(proved),
        "sorted_berth": "none, because scratch",
        "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]"}))
    (tickets / "bbbbbbbbbbbb-scratch.json").write_text(json.dumps({
        "id": "bbbbbbbbbbbb", "intent_berth": "none, because scratch",
        "sorted_berth": str(kept),
        "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED"}))

    ctx = {"root": str(berths), "reviewed_path": str(reviewed), "tickets": str(tickets),
           "ideas": str(ideas), "questions": str(questions)}
    m = probe_mod._measure(dict(ctx))
    assert m["census"] == 2 and m["lane"] == 1 and m["drained"] == 1, m
    assert m["terminal_in_lane"] == [] and m["re_raised"] == [] and m["clean"], m
    assert probe_mod._trigger(None, dict(ctx)) is False
    carried = probe_mod._carry(dict(ctx))
    assert "zero terminal in lane" in carried["finding"], carried

    # a cc-raised question on the ticket is CC's own work, not a re-raise
    (questions / "open-000000000001.json").write_text(json.dumps({
        "id": "open-000000000001", "ticket": "fb988505c5cb",
        "raised_by": "cc (superclaude-1.scope)", "question": "any terminal?", "resolved": True}))
    assert probe_mod._measure(dict(ctx))["clean"]

    # a question HE raised on the ticket is the WRONG-INTENT clause: a lack, named
    (questions / "open-000000000002.json").write_text(json.dumps({
        "id": "open-000000000002", "ticket": "fb988505c5cb",
        "raised_by": "Akien, in chat", "question": "why did the sorted for X vanish?"}))
    m2 = probe_mod._measure(dict(ctx))
    assert not m2["clean"] and [q["id"] for q in m2["re_raised"]] == ["open-000000000002"], m2
    assert "re-raised" in probe_mod._carry(dict(ctx))["finding"]

if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
