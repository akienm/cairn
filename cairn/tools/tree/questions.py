"""tree/questions.py — the question registry and embeddings generator.

A global list of (question, owner) tuples. Each device or domain registers its
own questions; two devices asking the same question coexist without deduplication
(each gets its own spin). Established questions are string constants that prevent
misspelling. Temporary questions are added for a research run and removed when it
completes. Meta-questions (questions about what questions to ask) are regular
tuples — no special-casing.

The generator accepts a single question or a list and returns embeddings for each
via the render_method pipeline the tree already supports. Vectors arrive as DATA
(the embed call is the caller's, through inference_domain) — this module never
touches the network.
"""
from __future__ import annotations


class QuestionRefused(RuntimeError):
    """A question-registry ask this module cannot honestly serve."""


ESTABLISHED_QUESTIONS = [
    "how does this component work",
    "what does this component depend on",
    "what is the failure mode of this component",
    "what question should I ask about this component",
]

_REGISTRY: list[tuple[str, str]] = []


def registry() -> list[tuple[str, str]]:
    """The current (question, owner) tuples — a snapshot, not the live list."""
    return list(_REGISTRY)


def add(question: str, owner: str) -> tuple[str, str]:
    """Register a (question, owner) tuple. No dedup — the same question from two
    owners is two entries, each gets its own spin."""
    if not isinstance(question, str) or not question.strip():
        raise QuestionRefused("add: question must be a non-empty string")
    if not isinstance(owner, str) or not owner.strip():
        raise QuestionRefused("add: owner must be a non-empty string")
    entry = (question, owner)
    _REGISTRY.append(entry)
    return entry


def remove(question: str, owner: str) -> tuple[str, str]:
    """Remove a (question, owner) tuple by identity (both fields match). Raises
    QuestionRefused if the tuple is not in the registry."""
    entry = (question, owner)
    try:
        _REGISTRY.remove(entry)
    except ValueError:
        raise QuestionRefused(
            f"remove: ({question!r}, {owner!r}) is not in the registry")
    return entry


def generate_embeddings(questions, embed):
    """Accept a single question string or a list of question strings and return
    embeddings for each via the caller's embed function (the render_method pipeline).

    ``embed`` is the caller's seam — e.g. ``embed_via_domain()`` from
    ``cairn.devices.librarian.live``. This module never imports inference_domain;
    vectors arrive as DATA (the charter's composition rule).

    Returns a list of ``{"question": str, "vector": list[float]}`` dicts, one per
    input question. A single string returns a one-element list."""
    if isinstance(questions, str):
        questions = [questions]
    if not isinstance(questions, list) or not questions:
        raise QuestionRefused(
            "generate_embeddings: questions must be a non-empty string or list of strings")
    results = []
    for q in questions:
        if not isinstance(q, str) or not q.strip():
            raise QuestionRefused(
                f"generate_embeddings: each question must be a non-empty string, got {q!r}")
        results.append({"question": q, "vector": embed(q)})
    return results
