"""Proof for the extraction judge — teeth a hollow judge could not pass.

Import-pure by construction: this machine's whole outbound surface is the gate tool, so
nothing here needs a temp world, a seam, or a host. That is the property the machine was
carved out to make TRUE rather than merely stated (see the module docstring), and the
last tooth is the one that measures it.

    python3 cairn/devices/intention_extractor/machines/judge/proofs/test_judge.py
"""

from __future__ import annotations

import ast
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[6]
sys.path.insert(0, str(REPO))

from cairn.devices.intention_extractor.machines.judge import judge  # noqa: E402
from cairn.tools.gate import gate  # noqa: E402

_SOURCE = (
    "we need a prebuild type step for you on each thing we design, so that the thing "
    "we'd build from the start as a learning device is not bolted on afterwards"
)


def _good_draft():
    return {
        "what": "a prebuild step runs before each build",
        "why": "so the learning is built in from the start, not bolted on",
        "anchors": ["we need a prebuild type step for you on each thing we design",
                    "we'd build from the start as a learning device"],
        "read": "",
    }


def test_every_check_is_taught_and_pinned():
    """Provenance is read off the INSPECTOR, because that is where the check LIVES — the
    findings function is a view over it. A tooth reading the view would go green over a
    rendering while the rule it names moved."""
    assert sorted(judge.CHECKS) == sorted(judge.INSPECTORS) == [
        "anchors_verbatim", "record_shape"], "registry pinned to the teeth"
    for name, inspector in judge.INSPECTORS.items():
        doc = inspector.__doc__ or ""
        assert "Provenance:" in doc and re.search(r"\d{4}-\d{2}-\d{2}", doc), \
            f"check {name} carries no dated correction — a check nobody was taught by"


def test_a_pass_lists_the_lanes_it_ran_not_only_that_nothing_objected():
    """The findings list was empty both when a draft satisfied every rule and when a rule
    had been quietly dropped. The record's LENGTH is the ruleset's size."""
    draft = _good_draft()
    record = (judge.inspect_record_shape(draft, _SOURCE)
              + judge.inspect_anchors_verbatim(draft, _SOURCE))
    assert all(gate.passed(e) for e in record), [e for e in record if not gate.passed(e)]
    ids = [e["identity"] for e in record]
    assert len(ids) == len(set(ids)) >= 6, ids
    assert "the_field_set_is_exactly_the_four" in ids and "the_why_says_something" in ids
    verbatim = [e for e in record
                if e["identity"] == "every_anchor_appears_verbatim_in_the_source"][0]
    assert verbatim["expected"] == verbatim["actual"] == draft["anchors"], verbatim
    assert judge.findings_of(record) == [], judge.findings_of(record)


def test_the_attribution_lane_is_absent_when_there_are_no_anchors_to_walk():
    """A draft whose ``anchors`` is not a list has nothing to check for fabrication, and
    ``the_draft_is_anchored_at_all`` has already refused it. One fault, one finding — the
    old code said this with a bare ``return findings`` and recorded nothing."""
    draft = dict(_good_draft(), anchors="a string, not a list")
    assert judge.inspect_anchors_verbatim(draft, _SOURCE) == [], "no lane, not a green one"
    shape = [e for e in judge.inspect_record_shape(draft, _SOURCE) if not gate.passed(e)]
    assert [e["identity"] for e in shape] == ["the_draft_is_anchored_at_all"], shape
    # derived, never parallel: the view is the record's mismatches, read back out
    assert judge.record_shape(draft, _SOURCE) == [
        f for e in judge.inspect_record_shape(draft, _SOURCE) if not gate.passed(e)
        for f in e["values"]["findings"]]


def test_a_lane_that_refuses_and_names_nothing_is_louder_than_a_silent_drop():
    """``findings_of`` is not a filter over the findings lists alone. A lane that FAILS
    while carrying no finding is a refusal with no sentence, and flattening the lists
    would have dropped it — the exact silence the record exists to end."""
    mute = gate.proved(identity="a_lane_that_says_nothing", location="x",
                       code="x", source="intention_extractor.record_shape",
                       expected="a", actual="b", findings=[])
    out = judge.findings_of([mute])
    assert len(out) == 1 and "named no finding" in out[0]["finding"], out
    assert out[0]["evidence"] == {"expected": "a", "actual": "b"}, out
    # non-vacuity: a lane that passes contributes nothing
    assert judge.findings_of([gate.proved(
        identity="ok", location="x", code="x", source="s",
        expected="a", actual="a", findings=[])]) == []


def test_the_judge_holds_no_seam_of_its_own():
    """THE WHOLE REASON THIS MACHINE EXISTS. It was carved out of the device because
    bin/cmd/determinism read the device as a gate that could reach an oracle at sleep.
    The carve-out is only worth anything if the judge's import surface stays this narrow,
    so the property is measured here rather than asserted in the docstring."""
    tree = ast.parse(Path(judge.__file__).read_text(encoding="utf-8"))
    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name for a in node.names)
        elif isinstance(node, ast.ImportFrom):
            imported.add(node.module or "")
    assert imported == {"__future__", "cairn.tools.gate"}, sorted(imported)


def _main() -> int:
    checks = [v for k, v in globals().items()
              if k.startswith("test_") and callable(v)]
    assert len(checks) >= 5, f"the derived roster collapsed: {len(checks)}"
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — judge: the checks report what they proved, and reach nothing")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
