"""PROOF — /sail's post-build reflection reaches codemother as a record (ticket 68f563403c8f).

Five teeth, one per proves_red clause of post-build-reflection-feeds-codemother, over the
three pieces the chain split it into: ``skills/sail/reflection.py`` (the shape and its
door), the ``feedback`` verb on codemother's shim (the receiver), and
``ingest.ingest_reflections`` (the compose with the pattern vocabulary). Every tooth binds
its subject at call time so a hollow reading that takes the module away reds the tooth
by name instead of crashing the import.

The fixture world is a scratch instance root (``_address.ROOTS["instance"]`` swapped per
tooth, the shape ``test_charter_held.py`` set) and a fake bus that records one post; the
live backpack under ``~/.cairn`` is never written.

    PYTHONPATH=. python3 cairn/devices/codemother/proofs/test_feedback_verb.py
"""
from __future__ import annotations

import contextlib
import json
import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

PROVES = {
    "68f563403c8f": {
        "1": "test_silence_is_refused_and_at_par_true_is_a_complete_answer",
        "2": "test_a_reflection_carries_no_code_and_fires_once",
        "3": "test_the_verb_lands_one_record_in_codemothers_held_backpack",
        "4": "test_the_skill_step_is_one_short_section_naming_the_door",
        "5": "test_praise_and_at_par_ingest_as_positive_types",
    },
}

_TICKET = "68f563403c8f"


def _good(**over) -> dict:
    p = {"ticket": _TICKET, "at_par": True, "findings": [], "cost_estimate": "nothing extra",
         "stratum": "code"}
    p.update(over)
    return p


def _flag(text="decompose said ingest.py:23-55 reads a recorder record; it reads .md frontmatter") -> dict:
    return {"artifact": "chart", "field": "decompose.sub_problems", "kind": "flag", "text": text,
            "would_change": "the compose piece names the function it composes with"}


class _FakeBus:
    def __init__(self):
        self.posts: list[dict] = []

    def request(self, **envelope):
        self.posts.append(envelope)
        return {"accepted": True, "echo": envelope.get("verb")}


@contextlib.contextmanager
def _scratch_instance():
    from cairn.devices.tester.scratch import scratch_dir
    from cairn.tools.base import address as _address
    live = _address.ROOTS["instance"]
    d = scratch_dir("cairn_feedback_verb_")
    _address.ROOTS["instance"] = d
    try:
        yield d
    finally:
        _address.ROOTS["instance"] = live


# --- teeth -----------------------------------------------------------------------------------

def test_silence_is_refused_and_at_par_true_is_a_complete_answer():
    """Clause (1) + (5): a packet with no at_par is refused naming at_par; a non-bool at_par is
    refused; at_par true with no findings passes — 'was fine' is an answer, not a skip."""
    from skills.sail.reflection import check
    lacks = check({})
    assert any(l.startswith("at_par:") for l in lacks), lacks
    lacks = check({k: v for k, v in _good().items() if k != "at_par"})
    assert lacks and all(l.startswith("at_par:") for l in lacks), lacks
    lacks = check(_good(at_par="yes"))
    assert lacks == ["at_par: must be true or false, explicitly — silence is not an answer"], lacks
    assert check(_good()) == []
    # below par has to name what was wrong
    lacks = check(_good(at_par=False))
    assert lacks == ["at_par: false with no flag finding — below par names what was wrong"], lacks
    assert check(_good(at_par=False, findings=[_flag()])) == []
    print("ok test_silence_is_refused_and_at_par_true_is_a_complete_answer")


def test_a_reflection_carries_no_code_and_fires_once():
    """Clause (2): a patch/diff/files key is refused by name — the shape has no field for code;
    fire() over a bus posts exactly one request and returns its reply, and sends nothing when
    the packet is refused."""
    from skills.sail import reflection
    for key in ("patch", "diff", "files"):
        lacks = reflection.check(_good(**{key: "x"}))
        assert len(lacks) == 1 and lacks[0].startswith(f"{key}: not a field of a reflection"), lacks
    bus = _FakeBus()
    reply = reflection.fire(_good(at_par=False, findings=[_flag()]), bus=bus)
    assert reply == {"accepted": True, "echo": "feedback"}, reply
    assert len(bus.posts) == 1
    post = bus.posts[0]
    assert post["to"] == "codemother" and post["verb"] == "feedback" and post["sender"] == "sail"
    assert post["body"]["reflection"]["ticket"] == _TICKET
    assert "below par" in post["why"]
    try:
        reflection.fire(_good(patch="x"), bus=bus)
    except ValueError as exc:
        assert "patch" in str(exc)
    else:
        raise AssertionError("a packet carrying a patch was fired")
    assert len(bus.posts) == 1, "a refused packet was sent"
    print("ok test_a_reflection_carries_no_code_and_fires_once")


def test_the_verb_lands_one_record_in_codemothers_held_backpack():
    """Clause (3): the receiver is codemother — her shim declares 'feedback', one call appends
    one record to the held charter backpack under metadata.type feedback, and a silent
    packet is refused at the receiver too."""
    from cairn.devices.codemother import shim as cm
    from cairn.tools.instanceizer.instanceizer import load
    with _scratch_instance() as root:
        dev = cm.CodeMotherDevice(bus=None)
        assert "feedback" in dev.declared_verbs()
        packet = _good(at_par=False, findings=[_flag()])
        out = dev._handle_feedback({"sender": "sail", "verb": "feedback", "body": {"reflection": packet}})
        assert out["accepted"] is True and out["records"] == 1, out
        held = cm.charter_instance()
        assert str(held).startswith(str(root)), (held, root)
        records = load(held).read()
        assert len(records) == 1
        rec = records[0]
        assert rec["metadata"] == {"type": "feedback"}
        assert rec["reflection"] == packet
        assert rec["probe_source"] == "sail"
        assert rec["finding"] == f"{_TICKET}: below par (1 flag(s))"
        bad = dev._handle_feedback({"sender": "sail", "verb": "feedback",
                                    "body": {"reflection": {"ticket": _TICKET}}})
        assert bad["accepted"] is False and "at_par" in bad["why"], bad
        assert len(load(held).read()) == 1, "a silent packet landed"
    print("ok test_the_verb_lands_one_record_in_codemothers_held_backpack")


def test_the_skill_step_is_one_short_section_naming_the_door():
    """Clause (4), the firehose: the prompt is ONE numbered section under 40 lines, between §3
    and §4, naming reflection.py and the at-par answer as positive — not a wall."""
    text = (_REPO_ROOT / "skills/sail/SKILL.md").read_text(encoding="utf-8")
    m = re.search(r"^## 3b\. Reflect on the packet.*?(?=^## 4\.)", text, re.S | re.M)
    assert m, "no '## 3b. Reflect on the packet' section before '## 4.'"
    section = m.group(0)
    assert text.index("## 3. Prove") < m.start() < text.index("## 4. Journal PROVEME")
    lines = section.strip().splitlines()
    assert len(lines) < 40, f"the reflection step is {len(lines)} lines — a firehose"
    assert "skills/sail/reflection.py" in section and "python3 -m skills.sail.reflection" in section
    assert "POSITIVE" in section and "praise" in section
    assert "codemother" in section
    print("ok test_the_skill_step_is_one_short_section_naming_the_door")


def test_praise_and_at_par_ingest_as_positive_types():
    """Clause (5): praise passes the door, and the compose with ingest keeps the polarity —
    an at-par reflection is a POSITIVE type, a below-par one a NEGATIVE type tagged
    cc-feedback; records without the feedback metadata are skipped."""
    from skills.sail.reflection import check
    from cairn.devices.codemother.ingest import ingest_reflections
    from cairn.devices.codemother.types import TypePolarity
    praise = {"artifact": "ticket", "field": "how", "kind": "praise", "text": "D1-D6 named every step"}
    assert check(_good(findings=[praise])) == []
    lacks = check(_good(findings=[{**praise, "would_change": "nothing"}]))
    assert lacks == ["findings[0].would_change: praise changes nothing — drop the key"], lacks
    records = [
        {"metadata": {"type": "feedback"}, "reflection": _good(findings=[praise])},
        {"metadata": {"type": "feedback"}, "reflection": _good(ticket="aaaaaaaaaaaa", at_par=False,
                                                                 findings=[_flag()])},
        {"finding": "not a reflection", "probe_source": "x"},
    ]
    types = ingest_reflections(records)
    assert [t.polarity for t in types] == [TypePolarity.POSITIVE, TypePolarity.NEGATIVE], types
    pos, neg = types
    assert pos.name == f"reflection:{_TICKET}" and "at par" in pos.why and "ticket.how" in pos.why
    assert "cc-feedback" in pos.tags and "at-par" in pos.tags
    assert neg.name == "reflection:aaaaaaaaaaaa" and "would change" in neg.why
    assert "cc-feedback" in neg.tags and len(neg.signals) == 1
    print("ok test_praise_and_at_par_ingest_as_positive_types")


# --- the run ---------------------------------------------------------------------------------

def _run_all() -> int:
    rc = 0
    for k in sorted(PROVES[_TICKET]):
        t = globals()[PROVES[_TICKET][k]]
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except Exception as exc:  # noqa: BLE001
            rc = 1
            print(f"  FAIL  {t.__name__}: {type(exc).__name__}: {exc}")
    print("green — the reflection reaches codemother" if rc == 0 else "RED")
    return rc


if __name__ == "__main__":
    sys.exit(_run_all())
