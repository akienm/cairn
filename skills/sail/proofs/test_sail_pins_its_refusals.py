"""Proof — /sail's prose contract carries its refusal conditions, step order, and gate names.

The skill is prose-as-implementation: what SKILL.md says IS what a delegated builder does.
This proof pins the three structural properties that, if they drift, silently teach the
wrong liturgy:

  (a) REFUSAL CONTRACT: the prose names the conditions under which the build refuses to
      proceed — no cast ticket and no berthed chart chain. A SKILL.md that drops these
      conditions is a SKILL.md that lets a builder start without a charted course.

  (b) STEP ORDER: certain steps MUST precede others because the gate physics demands it.
      A SKILL.md that reorders them is teaching a builder to trip the gates.

  (c) GATE NAME RESOLUTION: every gate exception class the prose mentions by name must
      resolve to a real class in cairn.tools.base.transitions. A name that no longer
      imports is a reference a builder cannot follow.

READS THE REAL FILE — skills/sail/SKILL.md, not a fixture. The proof pins STRUCTURE
(step numbers, ordering, importable names) not PHRASING — an honest rewording must not
red this; a structural break must.
"""

from __future__ import annotations

import importlib
import re
from pathlib import Path

import pytest

_SKILL_PATH = Path(__file__).resolve().parent.parent / "SKILL.md"


def _read_skill() -> str:
    assert _SKILL_PATH.is_file(), f"SKILL.md not found at {_SKILL_PATH}"
    return _SKILL_PATH.read_text(encoding="utf-8")


def _extract_steps(text: str) -> list[tuple[str, str, str]]:
    """Return (step_id, title, body) for each ## header that starts with a step number.

    step_id is the raw number/letter (e.g. "0", "0b", "1", "11").
    title is the rest of the header line.
    body is everything until the next ## header.
    """
    pattern = re.compile(r"^## (\d+\w?)\.\s+(.+?)$", re.MULTILINE)
    matches = list(pattern.finditer(text))
    steps = []
    for i, m in enumerate(matches):
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        body = text[m.end():end]
        steps.append((m.group(1), m.group(2), body))
    return steps


def _step_index(steps: list[tuple[str, str, str]], step_id: str) -> int:
    for i, (sid, _, _) in enumerate(steps):
        if sid == step_id:
            return i
    raise ValueError(f"step {step_id!r} not found in SKILL.md")


def _gate_names_in_prose(text: str) -> set[str]:
    """Extract every ``FooGateRed`` or ``FooEmissionRed`` class name backtick-quoted in the prose."""
    return set(re.findall(r"`(\w+(?:GateRed|EmissionRed))`", text))


# ---------------------------------------------------------------------------
# (a) REFUSAL CONTRACT — the prose names the refusal conditions
# ---------------------------------------------------------------------------


class TestRefusalContract:
    """The prose must name the two conditions under which the build refuses."""

    def test_refuses_without_cast_ticket(self):
        text = _read_skill()
        steps = _extract_steps(text)
        preamble_steps = [s for s in steps if s[0] in ("0", "0b")]
        assert preamble_steps, "SKILL.md has no step 0 or 0b — the preamble is gone"
        preamble_text = " ".join(body for _, _, body in preamble_steps)
        assert re.search(r"cast\s+ticket", preamble_text, re.IGNORECASE), (
            "step 0/0b does not mention a cast ticket — the refusal condition is gone"
        )

    def test_refuses_without_chart_chain(self):
        text = _read_skill()
        steps = _extract_steps(text)
        preamble_steps = [s for s in steps if s[0] in ("0", "0b")]
        preamble_text = " ".join(body for _, _, body in preamble_steps)
        assert re.search(r"chart|chain", preamble_text, re.IGNORECASE), (
            "step 0/0b does not mention the chart or chain — the refusal condition is gone"
        )

    def test_refusal_is_imperative(self):
        """The prose names REFUSING, not just describing — it uses refuse/red/error language."""
        text = _read_skill()
        steps = _extract_steps(text)
        preamble_steps = [s for s in steps if s[0] in ("0", "0b")]
        preamble_text = " ".join(body for _, _, body in preamble_steps)
        assert re.search(r"refus|red\b|error|throw", preamble_text, re.IGNORECASE), (
            "step 0/0b describes the conditions but never says the build REFUSES — "
            "the contract became advisory"
        )


# ---------------------------------------------------------------------------
# (b) STEP ORDER — the physics demands these orderings
# ---------------------------------------------------------------------------


class TestStepOrder:
    """Steps must appear in the order the gate physics requires."""

    def _steps(self):
        return _extract_steps(_read_skill())

    def test_buildme_before_build(self):
        """BUILDME journal (step 1) must precede the build (step 2)."""
        steps = self._steps()
        assert _step_index(steps, "1") < _step_index(steps, "2")

    def test_proveme_before_answer_the_chart(self):
        """PROVEME/seal (step 4) must precede answer-the-chart (step 6)."""
        steps = self._steps()
        assert _step_index(steps, "4") < _step_index(steps, "6")

    def test_answer_the_chart_before_proved(self):
        """Answer-the-chart (step 6) must precede PROVED crossing (step 8)."""
        steps = self._steps()
        assert _step_index(steps, "6") < _step_index(steps, "8")

    def test_prove_before_seal(self):
        """Prove (step 3) must precede PROVEME/seal (step 4)."""
        steps = self._steps()
        assert _step_index(steps, "3") < _step_index(steps, "4")

    def test_chart_before_everything(self):
        """Step 0 (chart it) must be the first step."""
        steps = self._steps()
        assert steps[0][0] == "0", (
            f"first step is {steps[0][0]!r}, not '0' — the chart is no longer step 0"
        )

    def test_step_numbers_are_monotonic(self):
        """The numeric part of step ids must be non-decreasing — no reorderings."""
        steps = self._steps()
        nums = []
        for sid, _, _ in steps:
            n = int(re.match(r"\d+", sid).group())
            nums.append(n)
        for i in range(1, len(nums)):
            assert nums[i] >= nums[i - 1], (
                f"step ordering broken: step {steps[i][0]} (num {nums[i]}) "
                f"follows step {steps[i-1][0]} (num {nums[i-1]})"
            )


# ---------------------------------------------------------------------------
# (c) GATE NAME RESOLUTION — every named gate class must be importable
# ---------------------------------------------------------------------------


class TestGateNameResolution:
    """Every gate exception class named in the prose must resolve to real code."""

    def test_at_least_one_gate_named(self):
        """The prose must name at least one gate class — a SKILL.md with no gate
        references is a SKILL.md that no longer teaches what throws."""
        names = _gate_names_in_prose(_read_skill())
        assert names, "SKILL.md names zero gate classes — the references are gone"

    def test_every_named_gate_imports(self):
        """Every backtick-quoted gate/emission class in the prose must be importable
        from cairn.tools.base.transitions."""
        mod = importlib.import_module("cairn.tools.base.transitions")
        names = _gate_names_in_prose(_read_skill())
        for name in sorted(names):
            cls = getattr(mod, name, None)
            assert cls is not None, (
                f"SKILL.md references `{name}` but cairn.tools.base.transitions "
                f"has no such class — the gate was renamed or removed"
            )

    def test_named_gates_are_exceptions(self):
        """Each resolved gate class must be an exception (a throwable refusal)."""
        mod = importlib.import_module("cairn.tools.base.transitions")
        names = _gate_names_in_prose(_read_skill())
        for name in sorted(names):
            cls = getattr(mod, name, None)
            if cls is None:
                pytest.skip(f"{name} not found — covered by test_every_named_gate_imports")
            assert issubclass(cls, Exception), (
                f"`{name}` exists but is not an Exception subclass — "
                f"the prose calls it a gate refusal but it can't be thrown"
            )

    def test_known_gates_present(self):
        """The three gate classes the ticket names must appear in the prose:
        EntryGateRed, ExitGateRed, WatchmeEmissionRed."""
        names = _gate_names_in_prose(_read_skill())
        expected = {"EntryGateRed", "ExitGateRed", "WatchmeEmissionRed"}
        missing = expected - names
        assert not missing, (
            f"SKILL.md no longer references {missing} — "
            f"a builder will not know what throws at that crossing"
        )


# ---------------------------------------------------------------------------
# Mutation teeth — structural breaks that this proof MUST catch
# ---------------------------------------------------------------------------


class TestMutationTeeth:
    """Verify the proof has teeth by testing that structural mutations would red."""

    def test_reorder_would_red(self):
        """If step 6 appeared after step 8, the ordering tests would catch it."""
        steps = _extract_steps(_read_skill())
        idx_6 = _step_index(steps, "6")
        idx_8 = _step_index(steps, "8")
        assert idx_6 < idx_8, "this is the live check — a reorder IS a red"

    def test_missing_gate_would_red(self):
        """If we looked for a nonexistent gate class, the import test would catch it."""
        mod = importlib.import_module("cairn.tools.base.transitions")
        assert not hasattr(mod, "PhantomGateRed"), (
            "PhantomGateRed exists — remove this canary if it's real"
        )

    def test_empty_skill_would_red(self):
        """An empty SKILL.md has no steps — the step extraction returns nothing."""
        assert _extract_steps("") == []
        assert _extract_steps("# Just a title\nSome text.") == []
