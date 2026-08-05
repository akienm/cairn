"""Proof for skill:/intent — the first skill wired onto the Learning Block anatomy
(ticket intent-becomes-a-learning-block, 2026-08-01).

WHAT THIS PROOF IS FOR, and what it deliberately is not. The seam's own teeth live in
``cairn/skill_block/proofs/test_skill_block.py`` — they prove the door refuses, traces,
berths, and takes a second tenant with no code change. Repeating them here would be
re-deriving the settled. What only THIS component can be asked is whether **/intent
itself is wired**: whether the anatomy is a call or a paragraph about a call, whether
the executed markdown and the authored charter still say the same thing, and whether
the real contract admits a real firing.

The ticket's falsifier (3) is the one this file exists to answer: *the anatomy is prose
in SKILL.md rather than a call into the primitive — discipline wearing physics'
clothes.* A skill's executor is an LLM reading markdown, so the only measurable
difference between "the skill fires the door" and "the skill describes the door" is
whether the text carries the command. That is a grep, and a grep is a proof here.

Falsifier (1) (a firing that leaves no trace) and (2) (an exit with no finding) are
answered by construction — ``skill_block.fire`` writes the trace and the finding in the
same act as the berth — and pinned in the seam's proof; the tooth below re-checks the
composition end to end through /intent's OWN charter, which is the part that could
break without anyone touching the seam.

STANDING IOU, unchanged and NOT discharged here: the skill class's derivation gate
(`cairn cairnmap --gate` renders every skill from its charter, and no charter-less
command renders) is still unbuilt — it lands with the presentation surface. This file
replaces PROOF.md's *behavioral* section, which was hand-run, and leaves the
derivation gate recorded as the debt it is (Law 4).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SKILL_DIR = HERE.parent
REPO = SKILL_DIR.parents[1]
sys.path.insert(0, str(REPO))

from cairn.learning_block.learning_block import DoorRefused  # noqa: E402
from cairn.skill_block import skill_block as sb  # noqa: E402
from cairn.tester.scratch import scratch_dir  # noqa: E402

SKILL_MD = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
CHARTER = json.loads((SKILL_DIR / "intention+why.json").read_text(encoding="utf-8"))
CONTRACT = CHARTER["input_contract"]

# The five nexus questions, in the order SKILL.md fires them, mapped to the contract
# field each one lands in. This mapping is the drift detector: it is written down once,
# here, and both sides are checked against it.
QUESTIONS = {"WHAT": "what", "HOW": "how", "Trace": "traces_to",
             "Shape": "shape", "Falsifier": "falsifier"}

GOOD = {
    # from_idea joined the contract 2026-08-04 with skill:/idea. The named exemption, with a
    # referent the judge can open — a proof packet is born of no captured idea.
    "from_idea": "none, because this packet is a proof fixture exercising the /intent wire, "
                 "not an intention — see skills/intent/proofs/test_intent_skill.py",
    "what": "prove the wire",
    "how": "fire the real contract from a proof",
    "traces_to": "Law 8 — nothing enters proven-space without a proof",
    "shape": "aside",
    "falsifier": "the door refuses this packet",
    # Required since ticket challenge-fires-at-intent (2026-08-03): a birth stands
    # the adversarial pass, and the REAL contract this proof fires against demands it.
    "challenge": {"better_approach": "none — a wire proof has one shape",
                  "prior_art": "the seam's own teeth", "hidden_assumption": "none",
                  "real_collision": "none", "back_up": "proceed"},
    "exit": "routed_forward",
    "bullets": [{"text": "the /intent contract admits a complete firing", "stratum": "code"}],
}


def world():
    return scratch_dir("intent-proof-")


def test_the_anatomy_is_a_CALL_not_a_paragraph_about_one():
    """Ticket falsifier (3), head on. A skill executed by an LLM reading markdown fires
    a door only if the text tells it to run the command — anything softer is discipline
    in prose, which is the thing this migration exists to stop being."""
    assert re.search(r"python3 -m cairn\.skill_block fire intent\b", SKILL_MD), \
        "SKILL.md must carry the literal firing command, not a description of firing"
    assert "PYTHONPATH=" in SKILL_MD, "the command must be runnable as written"


def test_both_exits_are_instructed_including_the_kill():
    """Falsifier (2)'s markdown half: the routed_out exit is the one that vanishes into
    conversation, so the text must say to fire it rather than merely permit it."""
    assert "routed_out" in SKILL_MD and "routed_forward" in SKILL_MD
    assert re.search(r"bullets.{0,400}BOTH exits", SKILL_MD, re.S), \
        "the finding must be demanded at both exits, in the text the executor reads"
    assert "The kill gets fired too" in SKILL_MD, \
        "the kill-exit trap must be named where the executor will read it"


def test_the_markdown_and_the_charter_cannot_drift():
    """The contract is authored in the charter and the questions are authored in
    SKILL.md — two files, one meaning. Nothing but this tooth holds them together, and
    a contract field with no question behind it is a field nobody will ever fill."""
    for question, field in QUESTIONS.items():
        assert re.search(rf"\*\*{question}\*\*", SKILL_MD), \
            f"question {question!r} vanished from SKILL.md"
        assert field in CONTRACT, f"question {question!r} has no contract field {field!r}"
        assert re.search(rf"\*\*{field}\*\*", SKILL_MD), \
            f"contract field {field!r} is never named in the packet section"
    # `challenge` is not one of the five birth questions — it is the adversarial PASS
    # over their answers (ticket challenge-fires-at-intent), with its own step section;
    # the field must still be named where the executor fills the packet.
    extra = set(CONTRACT) - set(QUESTIONS.values()) - {"exit", "bullets", "challenge"}
    assert not extra, f"contract fields with no question behind them: {sorted(extra)}"
    assert re.search(r"\*\*challenge\*\*", SKILL_MD), \
        "contract field 'challenge' is never named in the packet section"


def test_every_contract_field_carries_its_why():
    """A required field whose why is blank is a field a later reader cannot judge —
    and the refusal message QUOTES the why, so a blank one refuses uselessly."""
    for field, why in CONTRACT.items():
        assert isinstance(why, str) and len(why.strip()) > 40, \
            f"contract field {field!r} states no why worth reading: {why!r}"


def test_a_real_firing_against_the_REAL_charter_traces_and_finds():
    """Falsifiers (1) and (2) composed end to end through /intent's own charter: one
    firing, and afterwards the trace carries the green AND a finding stands at the
    gate. Run against injected roots — a proof that wrote here would corrupt the
    denominator the intent-door-refusals watch reads."""
    traces, berths = world(), world()
    out = sb.fire("intent", dict(GOOD), berths=berths, trace_root=traces)
    assert Path(out["berth"]).is_file(), "the firing berths"
    assert out["block"] == "skill:intent"

    events = [json.loads(l) for l in
              (traces / "skill:intent.jsonl").read_text().splitlines() if l.strip()]
    kinds = [e["event"] for e in events]
    assert "door_pass" in kinds, f"the GREEN is traced — that is the denominator: {kinds}"
    assert "finding" in kinds, f"the exit emits a finding: {kinds}"


def test_the_kill_exit_fires_the_same_door():
    """A node that traces to nothing still fires — with the reason in traces_to and the
    exit named. The alternative is what /intent did until today: reason to a kill and
    stop, leaving no record that the question was ever asked."""
    traces, berths = world(), world()
    packet = dict(GOOD, traces_to="nothing — this belongs to another system",
                  exit="routed_out",
                  bullets=[{"text": "killed at the cheapest gate", "stratum": "code"}])
    out = sb.fire("intent", packet, berths=berths, trace_root=traces)
    assert json.loads(Path(out["berth"]).read_text())["exit"] == "routed_out"


def test_an_incomplete_firing_is_refused_by_the_REAL_contract():
    """Non-vacuity for the tooth above: the live charter's contract must actually bite.
    A contract that admits anything is a contract that proves nothing."""
    traces, berths = world(), world()
    try:
        sb.fire("intent", {"what": "only the aim"}, berths=berths, trace_root=traces)
    except DoorRefused as exc:
        named = {lack["field"] for lack in exc.lacks}
        assert named == set(CONTRACT) - {"what"}, \
            f"every lack, on the first pass — got {sorted(named)}"
    else:
        raise AssertionError("the real /intent contract admitted a one-field firing")


def test_the_skill_class_derivation_gate_is_green():
    """THE IOU IS DISCHARGED, and this tooth is how that was found out. It was first
    written as 'cairnmap is unbuilt, so this debt stands' — and it RED immediately,
    because cairnmap has been built since. PROOF.md had been carrying a stale IOU: the
    gate the ticket names as this node's prove_gate was runnable the whole time.

    Its first real run then caught a live defect — cairn/skill_block/ had no charter,
    which by CLAUDE.md means it doesn't run. Fixed at the point of discovery, which is
    why this tooth is worth more than the note it replaced."""
    import subprocess
    run = subprocess.run([str(REPO / "bin" / "cairn"), "cairnmap", "--gate"],
                         capture_output=True, text=True, cwd=REPO)
    assert run.returncode == 0, (
        "the skill class's derivation gate reds — /intent renders from its charter only "
        f"if every component has one:\n{run.stdout}{run.stderr}")
    # Non-vacuity: the gate must have actually walked a corpus, not exited 0 on nothing.
    assert re.search(r"\d+ charters", run.stdout), f"the gate reported no census: {run.stdout}"


TEETH = [v for k, v in sorted(globals().items()) if k.startswith("test_")]


def _main() -> int:
    reds = 0
    for tooth in TEETH:
        try:
            tooth()
            print(f"  green  {tooth.__name__}")
        except AssertionError as exc:
            reds += 1
            print(f"  RED    {tooth.__name__}: {exc}")
    print(f"\n{len(TEETH) - reds}/{len(TEETH)} teeth green")
    if not reds:
        print("skill:/intent is WIRED — the anatomy is a call the markdown fires, the "
              "charter's contract and the executed question set cannot drift apart, a "
              "firing traces its green and emits a finding at either exit, and the "
              "real contract refuses an incomplete packet naming every lack at once")
    return 1 if reds else 0


if __name__ == "__main__":
    raise SystemExit(_main())
