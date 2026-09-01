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
    _cursor,
)


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
    result = read_questions()
    if QUESTIONS_DIR.exists():
        independent = list(QUESTIONS_DIR.glob("open-*.json"))
        assert result["count"] == len(independent)
    else:
        assert result["count"] == 0


def test_tickets_match_independent_read():
    result = read_tickets()
    independent_count = 0
    if TICKETS_DIR.exists():
        for p in TICKETS_DIR.glob("*.json"):
            try:
                t = json.loads(p.read_text())
            except (json.JSONDecodeError, OSError):
                continue
            if t.get("role") in ("store-charter", "charter"):
                continue
            cursor = _cursor(t.get("workflow_and_state", ""))
            if cursor in TERMINAL_STATES:
                continue
            independent_count += 1
    assert result["total_not_done"] == independent_count


def test_ideas_match_independent_read():
    result = read_ideas()
    if IDEAS_DIR.exists():
        from cairn.tools.operator_inbox.inbox import _acted_on_idea_ids
        acted = _acted_on_idea_ids()
        independent = [p for p in IDEAS_DIR.glob("*.json")
                       if not p.stem.startswith("_") and p.stem not in acted]
        assert result["count"] == len(independent)
    else:
        assert result["count"] == 0


def test_intentions_match_independent_read():
    result = read_intentions()
    if INTENTIONS_DIR.exists():
        independent = list(INTENTIONS_DIR.glob("I-*.md"))
        assert result["count"] == len(independent)
    else:
        assert result["count"] == 0


def test_format_produces_output():
    data = gather_all()
    output = format_inbox(data)
    assert "OPERATOR INBOX" in output
    assert "ARTIFACT" in output or "artifact" in output.lower() or "review" in output.lower()
    assert "TROUBLES" in output or "troubles" in output.lower()
    assert len(output) > 100


def test_section_order_is_ruled():
    assert SECTION_ORDER == [
        "troubles", "email", "adjudications", "lap", "questions",
        "design", "tickets", "intentions", "ideas",
    ]


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
