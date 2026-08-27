"""Proof: operator inbox reads live state and matches independent reads."""

import json
from pathlib import Path

from cairn.tools.operator_inbox.inbox import (
    gather_all,
    format_inbox,
    read_troubles,
    read_adjudications,
    read_questions,
    read_tickets,
    read_ideas,
    read_intentions,
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
    from cairn.machines.learning_block.learning_block import pending_findings
    independent = pending_findings()
    result = read_adjudications()
    assert result["count"] == len(independent)
    independent_ids = {f.get("id") for f in independent}
    result_ids = {f.get("id") for f in result["findings"]}
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
            cursor = _cursor(t.get("state", ""))
            if cursor in TERMINAL_STATES:
                continue
            independent_count += 1
    assert result["total_not_done"] == independent_count


def test_ideas_match_independent_read():
    result = read_ideas()
    if IDEAS_DIR.exists():
        independent = [p for p in IDEAS_DIR.glob("*.json")
                       if not p.stem.startswith("_")]
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
    assert "ADJUDICATIONS" in output or "adjudication" in output.lower()
    assert "TROUBLES" in output or "troubles" in output.lower()
    assert len(output) > 100


def test_section_order_is_ruled():
    assert SECTION_ORDER == [
        "troubles", "email", "adjudications", "questions",
        "design", "tickets", "intentions", "ideas",
    ]


def test_no_akien_in_headers():
    data = gather_all()
    output = format_inbox(data)
    for line in output.split("\n"):
        if line.strip().startswith("--") or "INBOX" in line:
            assert "AKIEN" not in line.upper() or "AKIEN" in line, \
                f"Header uses 'Akien' instead of 'Operator': {line}"


def test_format_uses_operator_not_akien():
    data = gather_all()
    output = format_inbox(data)
    for line in output.split("\n"):
        upper = line.strip().upper()
        if upper.startswith("--") or upper.startswith("==") or "INBOX" in upper:
            assert "AKIEN" not in upper, \
                f"Structural line uses 'Akien' instead of 'Operator': {line}"
