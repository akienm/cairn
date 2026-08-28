"""Teeth: every gate-bearing skill markdown carries an operator review step."""

import pathlib
import pytest

SKILLS_ROOT = pathlib.Path(__file__).resolve().parents[4] / "skills"

REVIEW_SKILLS = ["idea", "intent", "sorted"]

REVIEW_HEADING_MARKERS = {
    "idea": "## Operator reviews the record",
    "intent": "## Operator reviews the intention",
    "sorted": "### 5b. Operator reviews the ticket",
}

REQUIRED_PHRASES = [
    "present",
    "operator",
    "Wait for the operator",
]


@pytest.fixture(params=REVIEW_SKILLS)
def skill_markdown(request):
    path = SKILLS_ROOT / request.param / "SKILL.md"
    assert path.exists(), f"{path} missing"
    return request.param, path.read_text()


def test_review_heading_exists(skill_markdown):
    name, text = skill_markdown
    marker = REVIEW_HEADING_MARKERS[name]
    assert marker in text, (
        f"{name}/SKILL.md has no '{marker}' heading"
    )


def test_review_instructs_presentation(skill_markdown):
    name, text = skill_markdown
    marker = REVIEW_HEADING_MARKERS[name]
    idx = text.index(marker)
    section = text[idx:]
    for phrase in REQUIRED_PHRASES:
        assert phrase in section, (
            f"{name}/SKILL.md review section missing '{phrase}'"
        )


def test_review_names_three_outcomes(skill_markdown):
    name, text = skill_markdown
    marker = REVIEW_HEADING_MARKERS[name]
    idx = text.index(marker)
    section = text[idx:]
    for outcome in ["Sign-off", "Correction", "Rejection"]:
        assert outcome in section, (
            f"{name}/SKILL.md review section missing outcome '{outcome}'"
        )
