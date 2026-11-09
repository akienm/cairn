"""Proof for skill:/intent — the first skill wired onto the Learning Block anatomy
(ticket intent-becomes-a-learning-block, 2026-08-01).

WHAT THIS PROOF IS FOR, and what it deliberately is not. The seam's own teeth live in
``cairn/machines/skill_block/proofs/test_skill_block.py`` — they prove the door refuses, traces,
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

THE DERIVATION GATE IS RETIRED with the tool that ran it (ticket d547b4859f9a, outline 19.6:
the help surface is `cairn help`, 2.4.2). Its host-wide tooth and c691e19d5464's clause (1),
which read the gate's command lane, went with it; clauses (2) and (4) read the charters over
the tree this file stands in. Clause (3) (the /ruled skill installed) retired with the
ruling intake's code (ticket 640a7a48e1c5, outline Q#43).
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

from cairn.machines.learning_block.learning_block import DoorRefused  # noqa: E402
from cairn.machines.skill_block import skill_block as sb  # noqa: E402
from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

SKILL_MD = (SKILL_DIR / "SKILL.md").read_text(encoding="utf-8")
CHARTER = json.loads((SKILL_DIR / "intention+why.json").read_text(encoding="utf-8"))
CONTRACT = CHARTER["input_contract"]

# The five nexus questions, in the order SKILL.md fires them, mapped to the contract
# field each one lands in. This mapping is the drift detector: it is written down once,
# here, and both sides are checked against it.
# `Origin` is question 0, not a sixth: it is PROVENANCE asked before the five birth
# questions, and the five stay five so that "the adversarial pass over the five birth
# answers" keeps meaning what it says. It is here rather than in the exempt set because
# the executor must go and ANSWER it — the exempt three are routing (`exit`), the finding
# (`bullets`) and a separate step (`challenge`), none of which is a question at all.
# `TICKET or TASK` is question 1b — a sub-question like Origin, answered from the WHAT
# alone. It belongs here because the executor must go and ANSWER it.
QUESTIONS = {"Origin": "from_idea",
             "WHAT": "what", "TICKET or TASK": "task_or_ticket",
             "HOW": "how", "Trace": "traces_to",
             "Shape": "shape", "Falsifier": "falsifier"}

GOOD = {
    # from_idea joined the contract 2026-08-04 with skill:/idea. The named exemption, with a
    # referent the judge can open — a proof packet is born of no captured idea.
    "from_idea": "none, because this packet is a proof fixture exercising the /intent wire, "
                 "not an intention — see skills/intent/proofs/test_intent_skill.py",
    "task_or_ticket": "ticket",
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



# ── ticket c691e19d5464 — the five commands the map cannot render ────────────
# One tooth per MARKED clause of the falsifier (proof_coverage.clauses() reads
# ['1','2','3','4'] off the DONE-when head). Clause (1) read the derivation gate's
# command lane and retired with it (ticket d547b4859f9a); clause (3) retired with the
# ruling intake (ticket 640a7a48e1c5).
PROVES = {
    "c691e19d5464": {
        "2": "test_clause_2_the_five_are_named_with_real_usage",
        "4": "test_clause_4_no_charter_was_minted_under_bin_cmd",
    },
}

def world():
    return scratch_dir("intent-proof-")


def test_the_two_entrances_cannot_differ_in_strictness():
    """THE MEASURED DEFECT, head on (2026-08-05). One packet carrying a `from_idea`
    shaped like an id and resolving to nothing: `python3 -m cairn.machines.skill_block fire intent`
    ACCEPTED it (rc=0, berthed) while `python3 skills/intent/door.py` REFUSED it (rc=2).
    The semantic judge lived only behind the skill's own file, so the generic entrance —
    the one anyone can reach, and the one this proof used to advertise — skipped every
    semantic judge in the system. A gate whose strictness depends on which command was
    typed is policy, not physics (Law 4).
    """
    import importlib.util
    spec = importlib.util.spec_from_file_location("_intent_door_probe", SKILL_DIR / "door.py")
    door = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(door)

    packet = dict(GOOD, from_idea="2026-08-04-an-idea-that-was-never-captured")

    def lacks_from(fire):
        try:
            fire(packet, berths=world(), trace_root=world())
        except DoorRefused as exc:
            return [(lack.get("field"), lack.get("why")) for lack in exc.lacks]
        return []

    seam = lacks_from(lambda p, **kw: sb.fire("intent", p, **kw))
    own = lacks_from(door.fire)
    assert seam == own, (
        "the two entrances disagree about one packet — seam said "
        f"{[f for f, _ in seam]}, the skill's door said {[f for f, _ in own]}")
    # NON-VACUITY: agreeing on nothing is not agreement. This packet must actually bite,
    # or the tooth would stay green with every judge deleted.
    assert [f for f, _ in seam] == ["from_idea"], (
        f"the unresolvable origin no longer refuses at all: {seam}")


def test_the_anatomy_is_a_CALL_not_a_paragraph_about_one():
    """Ticket falsifier (3), head on. A skill executed by an LLM reading markdown fires
    a door only if the text tells it to run the command — anything softer is discipline
    in prose, which is the thing this migration exists to stop being."""
    assert re.search(r"python3 -m cairn\.machines\.skill_block fire intent\b", SKILL_MD), \
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


# ── ticket c691e19d5464: the commands' owners, read hermetically ─────────────
# THE FIVE, and where each is owned. The owner is the charter of the component the
# dispatcher in bin/cmd actually execs — never a charter minted under bin/cmd, which is
# the ticket's WRONG INTENT clause. Measured 2026-09-11 across 22 existing ownership
# sites: 17 are a component's own top-level `invoke`, 5 are facility blocks on bin's
# charter, and ZERO live under bin/cmd.
COMMAND_OWNERS = {
    "groundloop": "cairn/devices/cairn/machines/ground_loop/intention+why.json",
    "mailcheck": "cairn/devices/cc/intention+why.json",
    "operator": "cairn/tools/operator_inbox/intention+why.json",
    "operator_inbox": "cairn/tools/operator_inbox/intention+why.json",
    "review": "cairn/machines/skill_block/intention+why.json",
}

# WHAT COUNTS AS REAL USAGE, and why it is a shape rather than a word list. The gate's
# own lane is satisfied by the bare string `cairn operator_inbox` — which is how that
# charter passed for weeks while telling a reader nothing about how to run the thing.
# The falsifier's clause (2) closes that: the mention must carry usage the dispatcher
# ACTUALLY accepts. Three shapes qualify, and each is checkable without knowing the
# command: an angle-bracket placeholder (`<id>`), a pipe-separated alternation of
# subcommands (`status|stop`), or — for a dispatcher that genuinely takes no arguments,
# which bin/cmd/mailcheck does — the explicit words "no arguments". The third is not a
# loophole: mailcheck's real usage IS the bare form, and a charter that says so is
# saying something a bare word cannot. (Written into the ticket 2026-09-11: the clause
# as first cast said "at minimum one subcommand or argument", which mailcheck cannot
# satisfy and which would have been a bar no honest charter could clear.)
_USAGE_WINDOW = 80
_USAGE_SHAPE = re.compile(r"<[^>\n]+>|\w+\|\w+|no arguments")


def _invoke_of(rel: str) -> str:
    """The component's OWN top-level invoke — not a facility block's.

    For these six the owner is the component itself, so only the top-level string is
    read: a facility block naming the command would not tell a reader where to go.
    """
    charter = json.loads((REPO / rel).read_text(encoding="utf-8"))
    return charter.get("invoke") or ""


def test_clause_2_the_five_are_named_with_real_usage():
    """Falsifier clause (2): named by the RIGHT charter, and with usage a bare word
    cannot fake.

    Clause (1) only asks whether SOME charter mentions the command — a charter anywhere
    in the corpus could claim `cairn review` and the lane would go green. This tooth
    pins the mention to the charter of the component the dispatcher execs, and to that
    charter's OWN top-level invoke rather than a facility block, so 'owned' means the
    thing a reader would go and read.
    """
    for name, rel in sorted(COMMAND_OWNERS.items()):
        invoke = _invoke_of(rel)
        assert invoke, f"{rel} carries no top-level `invoke` at all, so it names nothing"
        hits = [m for m in re.finditer(rf"\bcairn {re.escape(name)}\b", invoke)]
        assert hits, (
            f"`cairn {name}` is not named by its own component's invoke ({rel}) — the "
            f"lane may still be green off some other charter, which is the substitution "
            f"this clause exists to catch")
        # At least ONE mention must carry usage in its window. `cairn review` appears
        # twice in skill_block's invoke — the bare listing form and the marking form —
        # and only the second carries an argument; either satisfying is correct.
        assert any(_USAGE_SHAPE.search(invoke[m.end():m.end() + _USAGE_WINDOW])
                   for m in hits), (
            f"`cairn {name}` is named in {rel} with no real usage within "
            f"{_USAGE_WINDOW} chars — no <placeholder>, no sub|command alternation, and "
            f"no explicit 'no arguments'. A bare mention satisfies the gate's lane and "
            f"tells a reader nothing, which is the measured state of `cairn "
            f"operator_inbox` before this ticket.")


def test_clause_4_no_charter_was_minted_under_bin_cmd():
    """The ticket's WRONG INTENT clause, head on: five charters appearing under bin/cmd
    would clear the gate by manufacturing five components that are not components.

    A dispatcher is a two-line exec into a component that already has a charter; giving
    it one of its own would make the complexity axis say there are five more things in
    the system than there are. This tooth contributes no reversion signal (nothing this
    build writes can make it red) and is declared anyway, because the clause is a bound
    on the SHAPE of the fix and an unwatched bound is the one a later hand crosses.
    """
    minted = sorted(str(p.relative_to(REPO)) for p in (REPO / "bin" / "cmd").rglob("intention+why.json"))
    assert minted == [], f"charters minted under bin/cmd: {minted}"




def _main() -> int:
    # COLLECTED HERE, NOT AT MODULE LEVEL. A `TEETH = [...]` comprehension sitting
    # above the last def collects only what is above it, and the runner then prints a
    # confident count over teeth that never ran. Measured corpus-wide 2026-09-09: 189
    # of 211 proofs carry the module-level shape. Collecting at call time makes the
    # count equal the file.
    TEETH = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
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
