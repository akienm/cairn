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

THE DERIVATION GATE IOU IS DISCHARGED, and this docstring carried the opposite claim
until 2026-09-11. `cairn cairnmap --gate` has been built and runnable since 2026-08-13;
the ninth tooth below says so in its own docstring and has been reading it for weeks.
Two sentences in one file disagreeing about whether a thing exists is the drift Law 5
is made of, and the tooth is the half with an instrument behind it.

TWO KINDS OF TOOTH LIVE HERE, and the difference is which tree they can read. The
HERMETIC ones (clause_1 .. clause_4, added 2026-09-11 under ticket c691e19d5464) call
``cairnmap.inspect(repo=REPO)`` with REPO derived from ``__file__``, so they read the
tree they are standing in. The HOST-WIDE one shells out to ``bin/cairn cairnmap --gate``
and reads whatever the host resolves. That is not a style choice: ``cairnmap.repo_root()``
is NAME-based (``roots_parent() / "cairn"``), so inside a git worktree — which is where
``cairn test --hollow`` measures — the CLI lands outside the worktree and reports 0
charters, and every lane passes vacuously. Measured 2026-09-11 in a real worktree: 15
findings, 6 checks proved, 0 charters. So only the hermetic four are DECLARED to hollow;
the host-wide one stays because the live fire against the real host is worth having, and
is deliberately undeclared because it cannot answer a reversion question.
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
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

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
# ['1','2','3','4'] off the DONE-when head). Only the hermetic teeth are here: the
# host-wide subprocess tooth below cannot run where hollow measures, and declaring a
# tooth that reds at HEAD in a worktree makes every reversion unreadable.
PROVES = {
    "c691e19d5464": {
        "1": "test_clause_1_the_command_lane_carries_no_reds",
        "2": "test_clause_2_the_five_are_named_with_real_usage",
        "3": "test_clause_3_ruled_is_installed_as_a_symlink_and_names_its_cli_face",
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


def test_the_skill_class_derivation_gate_is_green():
    """THE IOU IS DISCHARGED, and this tooth is how that was found out. It was first
    written as 'cairnmap is unbuilt, so this debt stands' — and it RED immediately,
    because cairnmap has been built since. PROOF.md had been carrying a stale IOU: the
    gate the ticket names as this node's prove_gate was runnable the whole time.

    Its first real run then caught a live defect — cairn/machines/skill_block/ had no charter,
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



# ── ticket c691e19d5464: the command lane, read hermetically ─────────────────
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
    "ruled": "skills/ruled/intention+why.json",
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

    The lane accepts either (cairnmap.units() yields the charter itself plus any
    top-level dict carrying both `what` and `invoke`), and for these six the owner is
    the component itself. Reading only the top-level string is what makes the tooth
    stricter than the lane it checks, which is the point of a clause (2) at all.
    """
    charter = json.loads((REPO / rel).read_text(encoding="utf-8"))
    return charter.get("invoke") or ""


def test_clause_1_the_command_lane_carries_no_reds():
    """Falsifier clause (1), read against THIS tree rather than against the host.

    `cairnmap.inspect(repo=REPO)` runs the same predicate the CLI gate runs — for each
    executable in bin/cmd, a `\bcairn <name>\b` search across every charter'd unit's
    invoke — but over the repo this file is standing in. That is what lets the tooth run
    inside `cairn test --hollow`'s worktree, where the CLI reads a repo that isn't there.

    Only the command lane is read. The commons-reading lanes beside it legitimately red
    in a worktree (commons_root() is name-based too), and collapsing 'this lane is
    clean' into 'the gate is green' would make the tooth unreadable exactly where it is
    needed most (Law 7 — a diagnostic surface may not collapse an error).
    """
    from cairn.tools.cairnmap import cairnmap
    entry = [e for e in cairnmap.inspect(repo=REPO)
             if e["identity"] == "every_command_is_named_by_a_charter"]
    assert len(entry) == 1, f"the command lane did not run at all: {entry}"
    reds = entry[0]["values"]["reds"]
    assert reds == [], "commands no charter's invoke names:\n  " + "\n  ".join(reds)
    # NON-VACUITY, and it is the whole reason this tooth can be trusted inside a
    # worktree. A lane that found no commands reds nothing and looks identical to a lane
    # that found twenty-five and owned them all. The CLI's worktree run failed exactly
    # this way: 0 charters, command lane 'pass'.
    expected = entry[0]["expected"]
    assert len(expected) >= 20, (
        f"the lane walked {len(expected)} command(s) — it found no corpus, so its green "
        f"says nothing: {expected}")
    assert set(COMMAND_OWNERS) <= set(expected), (
        f"the six this ticket is about are not among the commands walked: {expected}")


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


def test_clause_3_ruled_is_installed_as_a_symlink_and_names_its_cli_face():
    """Falsifier clause (3)'s two halves, and the WRONG INTENT clause that rides it.

    The gate's sixth red is not a command-lane red at all — /ruled carries a charter and
    has no entry in ~/.claude/skills — but the host-wide tooth below reads the WHOLE
    gate, so it cannot go green until this clears. A COPY would clear the gate and fork
    the source; the ticket names that as WRONG INTENT, and all 14 pre-existing entries
    are symlinks, so the install pattern is not in question.

    The install half is host state and survives a repo reversion by construction; the
    charter half does not, which is what gives this tooth something to say about the
    build.
    """
    from cairn.tools.cairnmap import cairnmap
    installed = cairnmap.installed_skills()
    assert "ruled" in installed, (
        f"/ruled is chartered and not installed — the derivation gate's sixth finding. "
        f"Installed: {sorted(installed)}")
    link = Path.home() / ".claude" / "skills" / "ruled"
    assert link.is_symlink(), (
        f"{link} exists but is not a symlink — a copied skill forks its own source, and "
        f"every one of the other {len(installed) - 1} entries is a link")
    target = installed["ruled"]
    assert target is not None and (target / "SKILL.md").is_file(), (
        f"the /ruled link resolves to {target}, which carries no SKILL.md")
    # The repo half: the charter must record the CLI face beside the slash face. Both
    # are real — bin/cmd/ruled execs skills.ruled.door directly — and a charter naming
    # only one of a component's two faces is a charter a reader cannot run from.
    invoke = _invoke_of(COMMAND_OWNERS["ruled"])
    assert "/ruled" in invoke and re.search(r"\bcairn ruled\b", invoke), (
        f"the /ruled charter records only one of its two faces: {invoke!r}")


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
