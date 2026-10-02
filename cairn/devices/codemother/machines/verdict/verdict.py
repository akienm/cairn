"""verdict — the answer a voyage owes its chart (ticket proved-answers-the-chart).

The chart chain ends at validate: what DONE means, measured. This module is the
other side of that promise — the v0 VERDICT ARTIFACT a voyage writes after
running those criteria, and the ONE validator both consumers compose:

  - the EXIT GATE (build_inspector.proved_answers_the_chart, called from the emit
    chokepoint's PROVED entry) shape-checks the artifact before a claimed ticket
    may close;
  - the DEPOSIT FACE (skills.chart.live's verdict- branch) re-validates the same
    artifact before its dispositions become the hypothesize tree's memory of
    what killed which.

One implementation, two mouths — a door and a gate that disagreed on a single
artifact would be the two-mouths defect measured on the first crossing.

TREE-FREE BY CONSTRUCTION: like cairn.devices.codemother.machines.orient.orient (the wire's standing
condition, pinned transitively by the inspector-nexus proof), this module
imports no tree machinery — the fire path from the chokepoint through the
inspector into here can never reach the trees or the db. A verdict is always
hardware. The deposit face therefore lives on the tree side (live.py), not here.

The artifact (verdict-<stamp>-<digest>.json, berthed beside the stage packets):

  ticket        — the cast ticket this verdict answers (REQUIRED here, unlike
                  the stages where a claim is optional: an unattributed verdict
                  answers nobody)
  validate_ref  — WHERE THE OBLIGATIONS COME FROM, in one of two forms: the
                  claiming validate berth whose criteria were run, or
                  ``falsifier@<ticket-id>`` — the ticket's own falsifier, clause
                  by clause, for a verdict written long after the chart chain
                  went cold (a WATCHME probe's answer to "did the intention
                  WORK?"). ONE contract either way; see FALSIFIER_REF below
  nexus         — OPTIONAL: which tree this verdict teaches, default
                  ``hypothesize``. Unconstrained to any roster on purpose — a
                  consumer outside this toolchain has no reason to own a tree by
                  one of our names
  verdicts      — [{claim, instrument, outcome: pass|fail, evidence}] — claim
                  verbatim from the berth's criteria; instrument what was RUN;
                  evidence what was OBSERVED (a verdict without both is
                  narration, the exact place done may not live — the 2026-07-24
                  correction as schema at the close). Since 2026-09-11 an entry
                  may also carry ``expect_exit`` (what the instrument returns
                  when the claim HOLDS, default 0) and ``timeout_s`` (default
                  600) — read from the claiming validate berth's criterion first
                  and from the entry only where the chart declared nothing
  observed_runs — STAMPED BY THE DOOR, never authored: one reading per verdict
                  entry, each carrying the command extracted, the exit observed,
                  how long it took and the tail of what it said. This is the
                  measurement the gate closed on, kept beside its verdict so a
                  later reader can re-run the very string the door ran
  dispositions  — [{piece, expect, disposition: confirmed|killed, by}] — piece +
                  expect verbatim from the chain's hypothesize berth; ``by`` is
                  the observation that decided it (a kill nobody can point at is
                  a narrated kill)

THE PENDING LEDGER (2026-07-29, ticket the-deposit-rides-the-read) berths in the chain
tool since 2026-10-02 (cairn/tools/chain/verdict_contract.py, ticket d8e8a2dc1176): the crossing side of the deposit split. The exit gate
shape-checks the artifact on disk, but the DEPOSIT of it into the hypothesize
tree used to be a sail step a builder remembered — and coupling the chokepoint to
the db/embed hosts would break netns sealing (build_inspector edge (l)). So the
crossing writes the cheap durable half (one appended line in a FILE) and the tree
side pays the db cost at its own door, on its own next read.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import shlex
import shutil
import subprocess
import time

from cairn.tools.gate import gate
from cairn.tools.chain.grammar import (CAIRN_ROOT, INSTANCE_DIR, inspected, lacks_of, ticket_claim_error, ticket_path)
from cairn.tools.chain.chain import (
    BERTHS_ROOT, CHAIN_STAGES, DISPOSITIONS, OUTCOMES,
    _DISPOSITION_FIELDS, _VERDICT_FIELDS,
    chain_for_ticket, claiming_packets, latest_claiming_artifact, verdict_error,
)

# THE CONTRACT IS THE CHAIN TOOL'S (ticket d8e8a2dc1176, RULE 1): the coverage reader and the
# verdict-deposit ledger moved down a rung to cairn/tools/chain/verdict_contract.py, and are
# bound here by identity so write_verdict, the live door and every older caller keep working.
from cairn.tools.chain.verdict_contract import (  # noqa: E402
    FALSIFIER_REF, LEDGER_PATH, VerdictRefused, _read_chain, enqueue_verdict,
    falsifier_criteria, mark_deposited, pending, read_ledger, unanswered,
)

DEFAULT_NEXUS = "hypothesize"

def verdict_nexus(artifact: dict) -> str:
    """WHICH TREE THIS VERDICT TEACHES. Named by the artifact, defaulting to
    ``hypothesize`` — the tree a chart-sourced verdict has always taught, so an
    artifact that says nothing lands exactly where it landed before this field
    existed (ticket watchme-emits-a-probe piece (d): "nexus becomes a specified
    parameter rather than the hardwired hypothesize").

    DELIBERATELY UNCONSTRAINED to any roster. The same ticket's falsifier clause
    (8) makes that a RED: a nexus that can only name one of our own devices would
    mean the design works for the toolchain watching itself and nowhere else. The
    value is a name the consumer resolves, and this door does not adjudicate it."""
    named = artifact.get("nexus")
    return named.strip() if isinstance(named, str) and named.strip() else DEFAULT_NEXUS


# ── THE DOOR RUNS THE INSTRUMENT IT IS HANDED (ticket 8e5db5f3edb2) ───────────
#
# Everything above this line reads the artifact's SHAPE: is the field present, is
# the outcome word legal, does every hypothesis carry a disposition. Not one of
# those checks touches the world the instrument describes, so a criterion could
# report ``pass`` while its instrument, run right now, said otherwise, and nothing
# anywhere would know. The last gate before a forward crossing into PROVED was
# made entirely of self-report — the shape Law 8 names as worse than a red,
# because a peer leans on a green without re-checking it.
#
# WHERE THE RUN HAPPENS, AND WHY ONLY THERE. ``write_verdict`` runs the
# instruments ONCE, stamps what it observed into the artifact, and gates on that.
# Every later reader — the exit gate at the PROVED crossing, the deposit face in
# skills/chart/live.py — checks the STAMP rather than re-running: the criteria of
# a real voyage are its proof suites, and re-running them at each of three doors
# would cost minutes per read for an answer that cannot have changed between the
# write and the crossing that follows it. The stamp is not a weaker reading. It
# carries the command, the exit and the output tail, so a reader who doubts it can
# re-run the very string the door ran (Law 7: the measurement lands in the record
# of truth, not only its verdict).
#
# THE BOUND ON THE CORPUS IS DELIBERATE. An artifact carrying no stamp reaches the
# new checks with nothing to inspect, and they are ABSENT from the record rather
# than passing — the same sequencing the shape check has always used. That is what
# makes the 549 prose instruments already berthed legal where they lie: they were
# shape-checked under the contract that stood when they were written, and
# rewriting a berthed record of truth to satisfy a rule invented afterwards is the
# collapse Law 7 forbids. Everything berthed from here on comes through
# ``write_verdict`` and is run.
#
# PURE DETERMINISTIC, AND THAT IS MEASURED RATHER THAN HOPED. The charter's
# falsifier clause (5) forbids this machine reaching an oracle, so the legality of
# forking a shell was checked before it was written: ``determinism.py`` excludes
# ``subprocess`` from the oracle walk by name (cairn/tools/determinism/
# determinism.py:156), and the module header carries Akien's ruling behind that —
# "DETERMINISTIC code can call other scripts. But Pure DETERMINISTIC means no LLM
# calls." A run is a fork. It is never an ask.

_TIMEOUT_DEFAULT = 600
_TAIL_CHARS = 2000
_BACKTICK_RE = re.compile(r"`([^`]+)`")
_ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

# Shell constructs that name no file on disk and that ``shutil.which`` therefore
# cannot find. Short on purpose: this list decides whether a string is a COMMAND,
# and every name added to it is a word that stops reading as prose.
_SHELL_HEADS = frozenset((
    "test", "[", "for", "while", "if", "case", "cd", "echo", "set", "export",
    "true", "false", "read", "eval", "exec", "source", ".", "printf", ":"))


def _tail(text) -> str:
    """The last ``_TAIL_CHARS`` of what the run said. The TAIL and not the head:
    a failing pytest prints its summary last, and that is the part a reader
    arriving at a refusal needs first."""
    if isinstance(text, bytes):
        text = text.decode("utf-8", "replace")
    if not isinstance(text, str):
        return ""
    return text[-_TAIL_CHARS:]


def _first_token_runs(text: str, root: str) -> bool:
    """Does this string OPEN like a command? Deterministic and conservative.

    Leading ``VAR=value`` assignments are stepped over (``PYTHONPATH=. python3 -m
    pytest`` opens with an assignment, not a program), then the head must be a
    shell construct, a path that exists, or a name ``shutil.which`` resolves.

    IT CAN SAY YES TO A SENTENCE, and the honest thing is to name that here rather
    than to claim a classifier this cheap is a parser: prose beginning "python3 is
    used to ..." opens with a resolvable name and reads as runnable. Such a string
    is then RUN and refused for disagreeing with its declared exit instead of for
    carrying no command — the right refusal under the wrong name. The trade is
    deliberate: the other direction, a classifier strict enough never to be fooled,
    refuses real commands, and a door that refuses the honest builder is a door
    that gets worked around."""
    try:
        tokens = shlex.split(text, comments=False)
    except ValueError:
        return False
    while tokens and _ASSIGNMENT_RE.match(tokens[0]):
        tokens.pop(0)
    if not tokens:
        return False
    head = tokens[0]
    if head in _SHELL_HEADS:
        return True
    if "/" in head:
        return (os.path.exists(os.path.join(root, head))
                or os.path.exists(os.path.expanduser(head)))
    return shutil.which(head) is not None


def extract_command(instrument, root: str = CAIRN_ROOT) -> str | None:
    """THE COMMAND INSIDE THE INSTRUMENT, or None when there is not exactly one.

    Two admitted forms, and the second is what the corpus actually looks like:
    the whole string parses as a command outright, or it carries EXACTLY ONE
    backticked span and that span is the command.

    ZERO SPANS OR TWO IS A REFUSAL, not a choice. Picking between two candidate
    commands is a judgement, and this door makes none — a door that guesses which
    half of a sentence the builder meant is an oracle wearing a regex. The
    refusal quotes the prose so the builder can see what could not be run."""
    if not isinstance(instrument, str) or not instrument.strip():
        return None
    text = instrument.strip()
    spans = _BACKTICK_RE.findall(text)
    if len(spans) == 1:
        inner = spans[0].strip()
        return inner or None
    if spans:
        return None
    return text if _first_token_runs(text, root) else None


def run_instrument(command: str, *, timeout_s: int = _TIMEOUT_DEFAULT,
                   cwd: str = CAIRN_ROOT) -> dict:
    """Fork a bounded shell and report what it said. Never raises: a run that
    could not happen is a RECORDED reading, because a door that throws on a
    broken instrument tells the builder less than one that shows them the OSError
    beside the command that caused it (Law 7)."""
    started = time.time()
    try:
        done = subprocess.run(["bash", "-c", command], cwd=cwd,
                              capture_output=True, text=True, timeout=timeout_s)
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "exit": None, "timed_out": True,
                "timeout_s": timeout_s, "seconds": round(time.time() - started, 3),
                "tail": _tail(_tail(exc.stdout) + _tail(exc.stderr))}
    except OSError as exc:
        return {"command": command, "exit": None, "timed_out": False,
                "timeout_s": timeout_s, "seconds": round(time.time() - started, 3),
                "error": "%s: %s" % (type(exc).__name__, exc), "tail": ""}
    return {"command": command, "exit": done.returncode, "timed_out": False,
            "timeout_s": timeout_s, "seconds": round(time.time() - started, 3),
            "tail": _tail(_tail(done.stdout) + _tail(done.stderr))}


def _declared(criterion, entry, field, default):
    """WHAT A PASS LOOKS LIKE, read from the chart first and the verdict second.

    The criterion in the validate berth was authored BEFORE the build and cannot
    have been tuned to the run that happened; the verdict entry is the builder's
    own declaration and stands only where the chart made none (a falsifier-form
    verdict has no berth to read). Earliest honest declaration wins."""
    for source in (criterion, entry):
        if isinstance(source, dict) and isinstance(source.get(field), int) \
                and not isinstance(source.get(field), bool):
            return source[field]
    return default


def observe_instruments(artifact, root: str = CAIRN_ROOT, *,
                        cwd: str | None = None, runner=run_instrument) -> list:
    """RUN WHAT THE ARTIFACT SAYS IT RAN, one reading per reported verdict.

    ``expect_exit`` is a DECLARATION and never an inference, because exit status
    is the INSTRUMENT's answer and not the CRITERION's: ``grep -c x f`` exits 1
    when the count is zero, and zero is exactly what some criteria claim. Absent
    a declaration the default is 0, which is what the overwhelming majority of
    the corpus means and what a builder who never thought about it expects.

    ``runner`` is injectable so a proof can watch this reason without paying for
    a fork — a probe that cannot be made to fire on demand is a probe nobody has
    measured, and the same is true of a door."""
    where = cwd or root
    criteria, _hypotheses, err = _read_chain(artifact, root)
    declared = {}
    if not err:
        for criterion in criteria:
            if isinstance(criterion, dict) and isinstance(criterion.get("claim"), str):
                declared.setdefault(criterion["claim"], criterion)
    observations = []
    for entry in artifact.get("verdicts") or []:
        if not isinstance(entry, dict):
            continue
        criterion = declared.get(entry.get("claim"))
        reading = {
            "claim": entry.get("claim"),
            "instrument": entry.get("instrument"),
            "outcome": entry.get("outcome"),
            "expect_exit": _declared(criterion, entry, "expect_exit", 0),
        }
        command = extract_command(entry.get("instrument"), where)
        if command is None:
            reading["runnable"] = False
            observations.append(reading)
            continue
        reading["runnable"] = True
        reading["run"] = runner(
            command,
            timeout_s=_declared(criterion, entry, "timeout_s", _TIMEOUT_DEFAULT),
            cwd=where)
        observations.append(reading)
    return observations


def _observed_entries(observations) -> list:
    """THE FOUR CHECKS OVER THE READINGS, in the order a builder can act on.

    Each is an ``inspected()`` entry whose expected/actual pair is a LIST, so
    ``validate_verdict``'s existing equality compare closes the gate with no new
    oracle anywhere near it. Each returns early for the same reason the shape
    check does: a criterion whose command could not be found has no exit to
    disagree about, and naming the derived failure beside the real one would send
    a builder to two pieces of work when there is one.

    A TIMEOUT IS ITS OWN CHECK AND NOT A DISAGREEMENT. The two send a builder to
    different work — one to a slow or hanging instrument, the other to a claim
    that is not true — and folding them together is the collapse Law 7 forbids at
    a diagnostic surface."""
    record = []
    unrunnable = [o for o in observations if not o.get("runnable")]
    record.append(inspected(
        "every_instrument_carries_a_runnable_command", stage="verdict",
        expected=[], actual=[o["claim"] for o in unrunnable],
        lack=("verdict artifact refused — no command could be run for: "
              + "; ".join("%r, whose instrument reads %r (a command outright, or "
                          "exactly one backticked span — this door does not choose "
                          "between candidates)" % (o["claim"], o["instrument"])
                          for o in unrunnable)) if unrunnable else ""))
    if unrunnable:
        return record

    timed_out = [o for o in observations if o["run"].get("timed_out")]
    record.append(inspected(
        "every_instrument_finished_inside_its_bound", stage="verdict",
        expected=[], actual=[o["claim"] for o in timed_out],
        lack=("verdict artifact refused — TIMEOUT, not disagreement: "
              + "; ".join("%r ran %r for %ss and did not finish (bound %ss — raise "
                          "timeout_s if the instrument is honestly slow)"
                          % (o["claim"], o["run"]["command"], o["run"]["seconds"],
                             o["run"]["timeout_s"]) for o in timed_out))
             if timed_out else ""))
    if timed_out:
        return record

    contradicted_claims, contradicted_lines = [], []
    for o in observations:
        agrees = o["run"].get("exit") == o["expect_exit"]
        if o["outcome"] == "pass" and not agrees:
            contradicted_claims.append(o["claim"])
            contradicted_lines.append(
                "%r reports pass, but %r exited %r where the claim holding means %r"
                "\n    --- output tail ---\n%s"
                % (o["claim"], o["run"]["command"], o["run"].get("exit"),
                   o["expect_exit"], o["run"].get("tail")))
        elif o["outcome"] == "fail" and agrees:
            contradicted_claims.append(o["claim"])
            contradicted_lines.append(
                "%r reports fail, but %r exited %r — which is exactly what the claim "
                "HOLDING looks like. A claimed failure that cannot be reproduced is the "
                "same hollow shape wearing the other sign"
                % (o["claim"], o["run"]["command"], o["run"].get("exit")))
    record.append(inspected(
        "every_reported_outcome_survives_its_re_run", stage="verdict",
        expected=[], actual=contradicted_claims,
        lack=("verdict artifact refused — the re-run disagrees with the report:\n  "
              + "\n  ".join(contradicted_lines)) if contradicted_lines else ""))
    if contradicted_claims:
        return record

    claims = sorted(str(o["claim"]) for o in observations)
    record.append(inspected(
        "every_criterion_instrument_was_run_and_agreed", stage="verdict",
        expected=claims, actual=claims,
        lack="", runs=[{"claim": o["claim"], "command": o["run"]["command"],
                        "exit": o["run"].get("exit"),
                        "expect_exit": o["expect_exit"]} for o in observations]))
    return record


def inspect_verdict(artifact, root: str = CAIRN_ROOT, *, observations=None) -> list:
    """VERDICT'S OWN INSPECTOR — the proof record for the artifact it berths.

    Every question this stage asks, EXPECTED beside ACTUAL, passes included. Akien,
    2026-08-13, ruling every-machine-carries-its-own-inspector-and-gate: "we can backtrack
    and see exactly where something went awry even if it's not something we're
    specifically looking for yet." Stage 8 hands its artifact to no ninth stage, and the
    ruling still lands here — the reader downstream of a verdict is a HUMAN reading the
    chain later, and an unrecorded pass is exactly as mysterious to them.

    A CHECK THAT DID NOT RUN IS ABSENT, NOT PASSED. The three checks after the shape one
    read fields whose shape is not yet established, so they only run once it holds: on a
    malformed artifact the record is SHORTER and the gate is already closed. That
    sequencing is the door's own, unchanged — what is new is that it is visible in the
    record rather than implied by the order of four raises.
    """
    err = verdict_error(artifact)
    record = [inspected("shape_is_well_formed", stage="verdict",
                        expected="well-formed", actual="well-formed" if not err else "malformed",
                        lack=err or "")]
    if err:
        return record

    hollow = []
    for i, v in enumerate(artifact.get("verdicts") or []):
        if isinstance(v, dict):
            obs = v.get("discriminating_observation")
            if not isinstance(obs, str) or not obs.strip():
                hollow.append("verdicts[%d]" % i)
    record.append(inspected(
        "every_criterion_carries_a_discriminating_observation", stage="verdict",
        expected=[], actual=hollow,
        lack=("verdict artifact refused — %s: discriminating_observation must be "
              "a non-empty string (a criterion whose instrument was never shown "
              "capable of failing is a hollow green — Law 8)"
              % ", ".join(hollow)) if hollow else ""))
    if hollow:
        return record

    claimed = "ticket" in artifact
    record.append(inspected(
        "verdict_claims_its_ticket", stage="verdict",
        expected="claimed", actual="claimed" if claimed else "unattributed",
        lack="verdict artifact refused — a verdict must claim its ticket"))

    claim_error = ticket_claim_error(artifact, root)
    record.append(inspected(
        "ticket_claim_is_consistent", stage="verdict",
        expected="consistent", actual="consistent" if not claim_error else "inconsistent",
        lack="verdict artifact refused — " + (claim_error or "")))

    # THE READINGS, AND WHY THEY COME BEFORE COVERAGE. Everything above is a file
    # read; below is a fork per criterion, so the checks that need no world — shape,
    # the hollow observation, the claim — are settled first and a malformed artifact
    # never reaches a subprocess.
    #
    # COVERAGE, THOUGH, GOES AFTER, AND THAT COSTS SOMETHING ON PURPOSE. ``unanswered``
    # kicks back any criterion reporting ``fail``, so with coverage first the sentence
    # a builder gets for a claimed failure is always "answered and FAILED — a kick-back"
    # and the other half of the ticket's clause (3) could never fire. Those two findings
    # send a builder to opposite work: one says go fix the build, the other says your
    # report of a failure cannot be reproduced and the build may be fine. Naming the
    # second one costs a run on an artifact that was going to be refused anyway, and a
    # wasted fork is cheaper than a builder sent to a bug that is not there (Law 7 — a
    # diagnostic surface may not collapse two errors into one shape).
    readings = observations if observations is not None else artifact.get("observed_runs")
    if isinstance(readings, list):
        observed = _observed_entries(readings)
        record.extend(observed)
        if lacks_of(observed):
            return record

    items = unanswered(artifact, root)
    record.append(inspected(
        "every_falsifier_clause_is_answered", stage="verdict",
        expected=[], actual=items,
        lack="verdict artifact refused — the chart is not yet answered:\n  "
             + "\n  ".join(items)))
    return record


def validate_verdict(artifact, root: str = CAIRN_ROOT, *, observations=None) -> dict:
    """VERDICT'S OWN GATE — an == compare over ``inspect_verdict``'s record.

    The whole door: shape, then the REQUIRED ticket claim (an unattributed verdict answers
    nobody), then coverage. Opens only when every entry's expected equals its actual, per
    entry, no oracle anywhere near it (ruling a-gate-opens-on-an-equality-compare-and-
    never-on-an-oracle). The refusal is the FIRST mismatch's own sentence rather than all
    of them joined, which is this door's long-standing behaviour and is kept deliberately:
    its four checks are sequentially dependent — a malformed artifact cannot be asked
    about its claim, and an artifact with no claim cannot be asked whether the claim is
    consistent — so a joined refusal here would name derived failures as if they were
    independent findings. The record still holds every check that RAN, which is what makes
    the sequencing readable instead of merely obeyed.
    """
    record = inspect_verdict(artifact, root=root, observations=observations)
    if gate.verdict(record)["opens"]:
        return artifact
    raise VerdictRefused(lacks_of(record)[0])


def write_verdict(artifact: dict, *, instance_dir: str = INSTANCE_DIR,
                  root: str = CAIRN_ROOT, cwd: str | None = None,
                  runner=run_instrument) -> str:
    """The berth: RUN the instruments, stamp what was observed, gate on that, then
    land beside the stage packets. Returns the path. The artifact is a NEW record —
    no berthed packet is ever touched, and the caller's dict is not mutated either.

    THE STAMP LANDS BEFORE THE DIGEST, which is not bookkeeping: the filename
    carries a hash of the artifact's content, so an observation added after the
    hash was taken would berth under a name that describes a different artifact.
    The dict that is gated, the dict that is hashed and the dict that is written
    are one object here, deliberately."""
    observations = observe_instruments(artifact, root, cwd=cwd, runner=runner)
    artifact = dict(artifact, observed_runs=observations)
    validate_verdict(artifact, root=root, observations=observations)
    os.makedirs(instance_dir, exist_ok=True)
    digest = hashlib.sha256(
        json.dumps(artifact, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    stamp = time.strftime("%Y%m%dT%H%M%S")
    path = os.path.join(instance_dir, "verdict-%s-%s.json" % (stamp, digest))
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(artifact, fh, indent=2, sort_keys=True)
        fh.write("\n")
    return path


def _criterion_part(v: dict) -> str:
    return "%s -> %s [by %s: %s]" % (v["claim"], v["outcome"],
                                     v["instrument"], v["evidence"])


def _disposition_part(d: dict) -> str:
    return "%s: %s — decided by: %s" % (d["disposition"].upper(), d["piece"], d["by"])


def verdict_node_parts(artifact: dict) -> list[tuple[str, str]]:
    """A NODE HOLDS ONE CLAIM (ticket a-node-holds-one-claim, 2026-07-29): the
    verdict rendered as its PARTS — one entry per criterion run verdict, one per
    hypothesis disposition — so each lands as its own node with its own honest
    vector. Returns ``[(kind, content), ...]`` with kind in criterion|disposition.

    WHY PARTS AND NOT ONE NODE. Measured: an eight-claim verdict rendered whole is
    11283 chars and the embed host refuses it outright (nomic-embed-text carries
    context_length 2048; a binary search over that exact content accepted 7403 and
    refused at 7447), while its largest single part is 2113 — every part clears
    with ~3.5x headroom. But size was the messenger, not the defect: ONE vector
    over eight distinct claims is a centroid pointing nowhere in particular, so
    eight vectors each pointing at one claim is MORE ACCURATE, not merely smaller.

    THE PARTS ARE BARE ON PURPOSE — no ticket, no berth, no framing prose. Two
    reasons, and the second is the load-bearing one. (1) The whole rendering below
    is a pure JOIN over these exact strings, so the two renderings are one function
    and cannot drift into the two-mouths defect. (2) node_id_for is a content hash,
    so attribution baked into content would make every part unique BY
    CONSTRUCTION — which is exactly the property that makes a monolith undedupable
    and is the thing this stone exists to end. A recurring disposition shape must
    be able to land on an existing node and corroborate it. Attribution therefore
    rides the node's PROVENANCE, which is where it belongs and where the deposit
    door already gates it."""
    return ([("criterion", _criterion_part(v)) for v in artifact["verdicts"]]
            + [("disposition", _disposition_part(d)) for d in artifact["dispositions"]])


def verdict_node_content(artifact: dict) -> str:
    """The whole-verdict rendering — what killed which, with the deciding
    observation VERBATIM beside each disposition, so a future counsel hit reads the
    kill and its evidence, not a summary of one.

    DERIVED FROM THE PARTS since 2026-07-29, not built beside them: this is a join
    over verdict_node_parts, so there is exactly one place that formats a criterion
    and one that formats a disposition. Kept because the exit gate and the human
    record still want the whole; it is NOT what the tree stores (nothing anywhere
    reassembles a verdict from tree nodes — measured at this stone's survey, which
    is why the composition half was never built)."""
    parts = verdict_node_parts(artifact)
    ran = "; ".join(c for kind, c in parts if kind == "criterion") or "nothing"
    fates = "; ".join(c for kind, c in parts if kind == "disposition") or "none"
    return ("VERDICT for ticket %s — the chart answered at PROVED. CRITERIA: %s. "
            "HYPOTHESES: %s" % (artifact["ticket"], ran, fates))


# ── WHICH BERTH CLAIMS THIS TICKET — THE ONE LATEST-CLAIMER RULE ─────────────
# Factored to cairn/tools/chain/chain.py (2026-09-02, device isolation): the
# chain reader belongs at the chain level, not inside the builder device.
# claiming_packets, latest_claiming_artifact, chain_for_ticket, CHAIN_STAGES,
# and BERTHS_ROOT are now imported from cairn.tools.chain.chain above.
