"""Teeth: every gate-bearing skill markdown carries an operator review step.

The step's shape is the review QUEUE (commit e72418ee, 2026-08-28): the artifact is queued,
the operator reviews it with `cairn review <id> "words"`, and the skill does NOT block waiting.
Until 2026-09-16 these teeth still asserted the earlier present-and-wait shape and were red under
a green seal that named no teeth (77f15efd5a96)."""

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
    "queued for operator review",
    "cairn review <id>",
    "Do not block waiting",
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


def test_review_instructs_the_queue(skill_markdown):
    name, text = skill_markdown
    marker = REVIEW_HEADING_MARKERS[name]
    idx = text.index(marker)
    section = text[idx:]
    for phrase in REQUIRED_PHRASES:
        assert phrase in section, (
            f"{name}/SKILL.md review section missing '{phrase}'"
        )


def test_review_never_waits_on_the_operator(skill_markdown):
    name, text = skill_markdown
    marker = REVIEW_HEADING_MARKERS[name]
    idx = text.index(marker)
    section = text[idx:]
    for stale in ["Wait for the operator", "Sign-off", "Rejection"]:
        assert stale not in section, (
            f"{name}/SKILL.md review section still carries the pre-e72418ee '{stale}' step"
        )

if __name__ == "__main__":
    from cairn.tools.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
