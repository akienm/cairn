"""Proof for tree/questions.py — the question registry and embeddings generator.

Teeth a hollow build could not pass:

  - REGISTRY HOLDS TUPLES: add and remove work; two tuples with the same
    question but different owners coexist (no dedup).
  - CONSTANTS ARE STRINGS: each established question is a non-empty string;
    a misspelled name raises AttributeError.
  - GENERATOR ROUTES THROUGH RENDER_METHOD: accepts a single question or a list;
    returns embeddings for each via the embed callable.
  - TEMPORARY LIFECYCLE: add, present, remove, absent, re-read still absent.
  - META-QUESTION TIER: a meta-question is a (question, owner) tuple held
    without special-casing; the generator produces embeddings for it.

    python3 cairn/tools/tree/proofs/test_questions.py     # exit 0 = green
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.tree.questions import (
    ESTABLISHED_QUESTIONS,
    QuestionRefused,
    add,
    generate_embeddings,
    registry,
    remove,
    _REGISTRY,
)


def _fake_embed(text: str) -> list[float]:
    return [float(len(text)), 0.1, 0.2]


def _reset():
    _REGISTRY.clear()


def test_registry_holds_tuples_add_remove():
    _reset()
    e1 = add("how does X work", "device_a")
    e2 = add("how does X work", "device_b")
    assert e1 == ("how does X work", "device_a")
    assert e2 == ("how does X work", "device_b")
    reg = registry()
    assert len(reg) == 2, f"two entries expected, got {len(reg)}"
    assert e1 in reg and e2 in reg
    remove("how does X work", "device_a")
    reg = registry()
    assert len(reg) == 1
    assert ("how does X work", "device_b") in reg
    assert ("how does X work", "device_a") not in reg


def test_no_dedup_same_question_different_owners():
    _reset()
    add("what is the failure mode", "device_a")
    add("what is the failure mode", "device_b")
    add("what is the failure mode", "device_c")
    reg = registry()
    matching = [e for e in reg if e[0] == "what is the failure mode"]
    assert len(matching) == 3, f"three entries expected (no dedup), got {len(matching)}"
    owners = {e[1] for e in matching}
    assert owners == {"device_a", "device_b", "device_c"}


def test_established_questions_are_importable_strings():
    assert isinstance(ESTABLISHED_QUESTIONS, list)
    assert len(ESTABLISHED_QUESTIONS) > 0, "at least one established question"
    for q in ESTABLISHED_QUESTIONS:
        assert isinstance(q, str), f"each question must be a string, got {type(q)}"
        assert q.strip(), "each question must be non-empty"


def test_misspelled_constant_raises():
    try:
        from cairn.tools.tree import questions
        _ = questions.NONEXISTENT_QUESTION_CONSTANT
        raise AssertionError("a misspelled name must raise AttributeError")
    except AttributeError:
        pass


def test_generator_single_question():
    results = generate_embeddings("how does X work", _fake_embed)
    assert len(results) == 1
    assert results[0]["question"] == "how does X work"
    assert isinstance(results[0]["vector"], list)
    assert len(results[0]["vector"]) > 0


def test_generator_list_of_questions():
    results = generate_embeddings(
        ["how does X work", "what depends on Y"], _fake_embed)
    assert len(results) == 2
    assert results[0]["question"] == "how does X work"
    assert results[1]["question"] == "what depends on Y"
    for r in results:
        assert isinstance(r["vector"], list)


def test_generator_routes_through_embed():
    calls = []
    def tracking_embed(text):
        calls.append(text)
        return [1.0, 2.0, 3.0]
    generate_embeddings(["q1", "q2"], tracking_embed)
    assert calls == ["q1", "q2"], f"embed must be called for each question, got {calls}"


def test_temporary_question_lifecycle():
    _reset()
    add("research: what patterns appear in error logs", "experiment_42")
    reg = registry()
    assert ("research: what patterns appear in error logs", "experiment_42") in reg
    remove("research: what patterns appear in error logs", "experiment_42")
    reg = registry()
    assert ("research: what patterns appear in error logs", "experiment_42") not in reg
    reg2 = registry()
    assert ("research: what patterns appear in error logs", "experiment_42") not in reg2


def test_remove_absent_raises():
    _reset()
    try:
        remove("never added", "nobody")
        raise AssertionError("removing an absent tuple must raise QuestionRefused")
    except QuestionRefused:
        pass


def test_meta_question_held_without_special_casing():
    _reset()
    add("what question should I ask about this component", "meta_device")
    add("how does this component work", "regular_device")
    reg = registry()
    meta = ("what question should I ask about this component", "meta_device")
    regular = ("how does this component work", "regular_device")
    assert meta in reg and regular in reg
    assert type(reg[0]) == type(reg[1]), "same tuple type — no special-casing"


def test_meta_question_generator_same_shape():
    results_meta = generate_embeddings(
        "what question should I ask about this component", _fake_embed)
    results_regular = generate_embeddings(
        "how does this component work", _fake_embed)
    assert set(results_meta[0].keys()) == set(results_regular[0].keys()), \
        "meta-question output must have the same shape as regular"


def test_add_refuses_empty():
    for bad in ("", "  ", None):
        try:
            add(bad, "owner")
            raise AssertionError(f"add({bad!r}) must refuse")
        except (QuestionRefused, TypeError):
            pass
    for bad in ("", "  ", None):
        try:
            add("valid question", bad)
            raise AssertionError(f"add(q, {bad!r}) must refuse")
        except (QuestionRefused, TypeError):
            pass


def test_generate_refuses_empty():
    try:
        generate_embeddings([], _fake_embed)
        raise AssertionError("generate_embeddings([]) must refuse")
    except QuestionRefused:
        pass
    try:
        generate_embeddings("", _fake_embed)
        raise AssertionError("generate_embeddings('') must refuse")
    except QuestionRefused:
        pass


def _main() -> int:
    checks = [
        test_registry_holds_tuples_add_remove,
        test_no_dedup_same_question_different_owners,
        test_established_questions_are_importable_strings,
        test_misspelled_constant_raises,
        test_generator_single_question,
        test_generator_list_of_questions,
        test_generator_routes_through_embed,
        test_temporary_question_lifecycle,
        test_remove_absent_raises,
        test_meta_question_held_without_special_casing,
        test_meta_question_generator_same_shape,
        test_add_refuses_empty,
        test_generate_refuses_empty,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — tree/questions: registry holds tuples with add/remove, no dedup, "
          "constants importable, generator routes through embed, temporary lifecycle, "
          "meta-questions same shape")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
