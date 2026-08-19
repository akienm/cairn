"""harbor_master/clearance.py — the CLEARANCE gate: the AUTHORITY rung of a transition.

harbor_master owns the harbor through which workflows voyage. Child a (register.py) is the
TRUTH rung as an aggregate — the fleet register. This is child b: the AUTHORITY rung — the
gate that decides WHO may move a boat's cursor, and refuses every move that is not cleared.

A workflow-transition factors into THREE rungs (the emit-chokepoint trichotomy, resolved
2026-07-21):

  - RULES (Law 4) — IS this move legal for the class? Base-class physics, inherited,
    un-delegable. Lives in cairn/tools/base/transitions.py; this gate does NOT re-implement it —
    it WRAPS it. Authority never overrides the rules: even a boat's owner cannot clear an
    illegal move, because ``emit`` validates legality before it writes.
  - AUTHORITY (Law 6) — WHO may invoke it? THIS FILE. Exactly one owner gates writes to a
    boat; delegated access happens only through the owner's gate, per-operation, never
    ambiently. An actor who is neither the owner nor the holder of a matching per-operation
    grant is refused — this is what stops devices from advancing workflows AROUND the harbor.
  - TRUTH (Law 7) — record it. Delegated to ``emit``'s journal door: the crossing appends to
    the boat's own history (carrying WHO cleared it), and the fleet register (child a) reads
    that history on demand — so the movement is recorded in both vantages with no rival copy.

And Law 8 binds here too: a cleared move summons a peer who ACTS, and the code that acts
must already be in proven-space. The caller names that code by its PROOF's address, and the
gate reads the seal beside it. It only READS the seal (confirms the code is proven) — it
never CALLS anything: the harbor clears the move, the crew sails it. A harbor that executed
would be the ground_loop-executor goof the ticket warns of.

NO REGISTRY (Akien, 2026-08-05: "methodregistry is a registry. generally we frown on
registries. why do we need one here?" — and we did not). Until today this rung asked an
in-memory ``MethodRegistry``, re-instated from the ground_loop driver-executor, which had
DISPATCHED and so genuinely needed a name -> callable map. That executor role was stripped as
a goof; the registry came back with its map intact and its consumer changed, and this gate
threw the callable away on the line it received it — it only ever wanted a yes or no. Law 1
forbids re-deriving a settled answer; it does not license carrying one forward when the
question moved. Three things the removal buys, none of them tidiness:

  - NO SECOND COPY. "This passed under the tester" already lives beside the proof, at an
    address DERIVED from the proof's own path (73 trails on disk). There was nothing to look
    up; the registry held a rival record of a fact that attaches at its own endpoint (Law 6).
  - THE HORIZON IS ENFORCED. A registry entry cached a bool with no expiry and kept answering
    green after the code moved. The seal carries a source fingerprint, so a stale green is a
    REFUSAL now (Law 3 — a VALIDATION expires).
  - NOTHING TO POPULATE. The registry admitted a method by RE-RUNNING its proof at wiring
    time; a restart lost the lot. Reading a seal costs a file read and survives everything.

So the gate binds FOUR refusals before a cursor moves — unauthorized (Law 6), unproven
(Law 8), illegal (Law 4, via the wrapped chokepoint), and unresourced — and only then does
the truth get written (Law 7). Cooperative, not policed: there is no enforcer here, only a
gate the one owner holds (the db_domain pattern — no other door). Forgery is not the threat
model on a single-owner cooperative box; AMBIENT authority is — an actor moving a boat with
no grant, or reusing one grant across operations. That is exactly what a per-operation grant
refuses.

THE FOURTH REFUSAL — UNRESOURCED (ratified by Akien 2026-08-04). A move that summons a
builder onto a host with no room for it fails as surely as an illegal one, just louder and
later. Measured from experience: past ~6 concurrent builders this box crawls, past 8 it heads
for a hard crash. The gate that already holds up the license to advance is where that is
answered — "it's not asking the system anymore, it's asking the harbormaster, because that's
the entity that would hold up the license to advance."

Three things this is NOT, each load-bearing:
  - NOT A COUNT. Nothing here or anywhere counts live builders — that would be a manager, and
    a manager is what this system does not have. Admission is decided from PRESSURE, which is
    directly observable, not from POPULATION, which would need a census someone owns. The
    fleet register (child a) is never consulted to gate a build; it reports, it does not
    manage.
  - NOT A READING. system_rackmount answers a VERDICT — "your line is crossed" — never a
    number. The harbor owns the LINE; the system device owns the METRIC. Either can change
    without the other knowing (Law 6).
  - NOT A SCHEDULER. The gate answers when asked. It never dispatches, never assigns, never
    starts anything. Initiative stays with the boat: each device owns its own task of checking
    whether it can start, and this is the door it checks at.

    python3 cairn/devices/harbor_master/proofs/test_clearance.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field

from cairn.tools.base.transitions import emit, parse_workflow, resolve_target
from cairn.machines.learning_block.learning_block import trace_root, write_trace
from cairn.devices.tester.validation_store import standing

# THE TWO ROOTS THE OWNER-READ WALKS, derived from this file's own address rather than
# taken from a caller. That is not fussiness: the whole point of ticket
# boat-owner-is-read-not-stated is that the caller must not be able to choose what the
# gate reads, and a ``tickets_dir=`` parameter on ``clear`` would hand the hole straight
# back under a new name (the ticket's own falsifier clause (1)). ``boat_owner_of`` below
# accepts roots so a PROOF can point it at a fixture; ``clear`` never passes them.
CAIRN_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
COMMONS_ROOT = os.path.join(os.path.dirname(CAIRN_ROOT), "CairnCommons")
TICKETS_DIR = os.path.join(COMMONS_ROOT, "tickets")

# THE KEY A CHARTER CARRIES WHEN IT HAS STOPPED BEING THE DESIGN. Named for the verb the
# corpus already uses at its one existing retirement door — cairn/machines/ruling/ruling.py
# calls itself "THE RETIREMENT DOOR" and derives a ``retired_ids`` set — so a reader meets
# one word for one act in both places. ``superseded_by`` is the FIELD inside it rather than
# the key, because a retirement with no successor is a real state and a key spelled
# "superseded_by" could not say it (build-to-the-tool naming: the term has to be derivable
# from its native use, and nobody memorises a mapping).
_RETIREMENT_KEY = "retired"

# How long a minted grant stays spendable. RULED BY AKIEN AT 10 SECONDS, 2026-08-04: "the thing
# asks for it, and has 10 seconds to take it to the build gate."
#
# The floor on this number is how long a launch takes to become VISIBLE to the resource owner:
# a grant that lapses before the thing it cleared shows up in the reading leaves the next asker
# blind for the gap. MEASURED: system_rackmount's runnable-count reading reflects a new load in
# under a second, so 10s clears that floor with room to spare. It would NOT have cleared it
# against the decaying load average that device served until today (~60s to reflect the same
# event) — the TTL and the metric swap are one decision, not two.
GRANT_TTL_SECONDS = 10.0

# The harbor's OWN lines — the values it holds up against system_rackmount's verdicts. The
# harbor owns these; the system device owns how they are measured, and neither needs the other's
# half. cpu: 6 of 8 cores runnable is 75%, the top of the range Akien measured as still workable.
# memory: a HYPOTHESIS, not a measurement (Law 3) — no one has yet measured what a builder needs
# to not thrash, so this is a placeholder holding the seam open, labelled as one.
HARBOR_LINES: dict[str, float] = {"cpu_threshold": 75.0, "memory_floor": 1024.0}

# THE WITNESS FIELDS — what this gate stamps on a crossing's record, and therefore what a
# caller may never hand in through ``journal_extra``. These are the evidence the chokepoint's
# clearance check reads back (ticket emit-refuses-an-uncleared-crossing, 2026-08-10): if a
# caller could supply them, an uncleared crossing could dress itself as a cleared one and the
# gate downstream would have no way to tell. The set is the exact spread ``clear`` writes at
# its ``emit`` call — kept beside the writing so the two cannot drift apart.
_GATE_WITNESS_FIELDS = frozenset({"cleared_by", "proven_by", "proven_seal_date", "delegated"})

# THE FIELDS A CALLER MAY NOT STATE BECAUSE THE GATE READS THEM (ticket
# boat-owner-is-read-not-stated, 2026-08-10). Distinct from the witness set above and the
# distinction is the whole ticket: a witness field is one the gate WRITES, so a caller
# supplying it forges evidence; ``boat_owner`` is one the gate READS off the boat, so a
# caller supplying it chooses the answer to the question being asked of it.
#
# Removing the parameter is NOT enough on its own, and this is the non-obvious half:
# ``**journal_extra`` would happily swallow a stray ``boat_owner=`` and ride it into the
# record as an extra field — the argument would look accepted, the gate would ignore it,
# and a record of truth would carry a claim about ownership that nothing checked. Law 7
# forbids exactly that collapse at exactly this surface, so it is refused LOUDLY.
_UNSTATABLE_FIELDS = frozenset({"boat_owner", "owning_intention", "gated_by"})

# ── THE GATE'S QUEUE (ticket clearance-leaves-a-trace, 2026-08-10) ───────────────────────
# Until today this gate remembered only what it PERMITTED. A refusal raised and the attempt
# vanished with the stack frame, so "the gate was asked, and said no" survived nowhere — and
# by Law 1 that guarantees the next mind walks into the same wall and re-derives the same
# refusal. The IOU is voyage.py's, filed 2026-07-26 and standing since.
#
# WHY THIS IS NOT A NEW STORE. ``write_trace`` already is this ticket's shape — one firing,
# one durable record, "green or red, same fidelity", append-only JSONL, instance-space,
# root injectable for proofs. Building a second record surface beside it would be the
# stone-1 parallel-roster failure with the answer sitting in the tree. So the queue is a
# BLOCK in that store, not a mechanism of its own.
#
# WHY THE BLOCK LIVES UNDER learning_block's ROOT WITHOUT BREAKING LAW 6. The root is a
# shared primitive surface keyed by block name, not learning_block's private state —
# measured: web_server, logger_for_bash, intentions_model_compiler and superclaude already
# keep blocks there and none of them is a learning block. The OWNED thing is the file
# ``harbor_master:clearance.jsonl``, and it is written from inside this module — the owner's
# own gate — never by a caller.
QUEUE_BLOCK = "harbor_master:clearance"

# CONSUMER: 'training', and 'debug' is DISQUALIFIED BY MEASUREMENT rather than by taste.
# ``write_trace`` sweeps expired debug records out of a block on every subsequent write
# (learning_block.py, cutoff = when - DEBUG_TTL_DAYS, "expired into nothingness, at the
# write"). A record of truth that evaporates after 30 days is not one, and Law 7 governs
# this store precisely because a refusal is an error-class outcome. 'tree-primary' would
# claim the tree is the reader, which it is not — the reader is the probe beside this code.
QUEUE_CONSUMER = "training"

# THE TWO EVENTS. The distinction the ticket demands is IN the record as a field, never
# inferred by a reader's arithmetic: a refusal is not "a grant that is absent from the
# journal", it is a record that says ``clearance_refused``. Same shape as ``fire_door``'s
# door_pass/send_back pair, which states this ticket's own falsifier in other words: both
# paths leave a record, or the refusal rate is unmeasurable and the gate is vacuous.
GRANTED = "clearance_granted"
REFUSED = "clearance_refused"


def _trace_attempt(event: str, *, workflow_str: str, target: str, actor: str, boat_id: str,
                   exc: BaseException | None = None) -> None:
    """Record ONE clearance attempt in the gate's queue — the four fields the ticket names
    by hand (who asked, for what transition, when, and on a refusal the reason), plus the
    reason's TYPE so the store is queryable by refusal class rather than by string-matching
    prose. ``when`` is stamped by ``write_trace`` itself, so it cannot be forged here.

    THE REASON IS TYPE **AND** MESSAGE, and neither alone would do. The type is the
    structured category a reader groups by (five of them today); the message carries the
    particulars this gate already writes well — which actor, which boat, which line was
    crossed, which proof was not sealed. Recording only the type would satisfy the ticket's
    words while landing on its second pre-named hollow pass ("a refusal with no reason":
    loud without being useful); recording only the message would leave every reader parsing
    prose to count anything.

    A FAILING TRACE IS NEVER SWALLOWED. If the write raises, it propagates — chained onto
    the refusal it was recording, so both are visible. Law 7 forbids collapsing an error
    into a coherent shape at exactly this surface, and a queue that quietly drops records
    when the disk is unhappy is a queue whose emptiness means nothing."""
    data = {
        "actor": actor,                 # who asked
        "boat": boat_id,                # which voyage was being moved
        "target": target,               # for what transition
        "workflow": workflow_str,       # ...from where — the cursor at the moment of asking
    }
    if exc is not None:
        data["reason_type"] = type(exc).__name__
        data["reason"] = str(exc)
    write_trace(QUEUE_BLOCK, event, QUEUE_CONSUMER, data)


def read_attempts() -> dict:
    """THE READ FACE OF THE QUEUE — "that record must be readable afterwards" is half the
    ticket, and a write with no reader is the ceremonial half of this build.

    Returns ``{queue, attempts, unreadable_lines}``: every recorded attempt oldest first, each
    flattened to what a consumer actually asks of it — ``{at, event, actor, boat, target,
    workflow}`` plus ``reason_type``/``reason`` on a refusal. Nothing is aggregated here; the
    counting belongs to whoever is counting.

    THE UNREADABLE LINES ARE REPORTED, NOT JUST SKIPPED. Dropping them silently would make a
    corrupted queue read exactly like an empty one, and the number this store exists to
    produce is "has the gate ever said no" — where a confident zero from an unreadable file
    is the worst available answer (Law 7: loud at a diagnostic surface). The ``queue`` path
    rides back for the same reason: a consumer reporting a count should be able to say what
    it read it from.

    IT LIVES AT THE OWNER'S ADDRESS, not in a consumer. There are two readers already
    (harbor_master's own probe, which filed the IOU for this store, and the traffic image's
    filed ``[X] refused`` marker), and a component that reads its own queue twice by hand is
    the parallel-roster failure inside one directory: two copies of the block name and the
    event names, either of which can quietly stop matching the writer and report a confident
    zero. Contrast the two trace readers elsewhere in the corpus, which re-implement the
    filter because they read DIFFERENT components' blocks — there is no owner there to put it
    at. No query surface is added to the trace store itself for the same reason in reverse:
    learning_block owns the substrate, not this block's meaning.

    Filters on event AND consumer TOGETHER, the corpus idiom. Either alone is a wrong count
    waiting to happen: a block that later carries a second consumer's records would inflate
    every number, and an event matched without its consumer would count a record the reaper
    is entitled to delete. An unparseable line is SKIPPED — counting it as a refusal invents
    a no the gate never said, and counting it as an attempt inflates the denominator."""
    path = trace_root() / f"{QUEUE_BLOCK}.jsonl"
    attempts: list[dict] = []
    unreadable = 0
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                unreadable += 1
                continue
            if rec.get("consumer") != QUEUE_CONSUMER or rec.get("event") not in (GRANTED, REFUSED):
                continue
            data = rec.get("data") or {}
            row = {"at": rec.get("when"), "event": rec.get("event"), "actor": data.get("actor"),
                   "boat": data.get("boat"), "target": data.get("target"),
                   "workflow": data.get("workflow")}
            if rec.get("event") == REFUSED:
                row["reason_type"] = data.get("reason_type") or "<unnamed>"
                row["reason"] = data.get("reason")
            attempts.append(row)
    return {"queue": str(path), "attempts": attempts, "unreadable_lines": unreadable}


class Unauthorized(Exception):
    """The actor may not move this boat: not its owner, and holds no matching grant (Law 6).

    Loud, never silent (Law 7) — an ambient advance that slips through unrecorded is the
    failure this gate exists to make impossible."""


class GrantExpired(Unauthorized):
    """The grant was real and named exactly this operation — and it lapsed before it was spent.

    A subclass of ``Unauthorized`` on purpose: an expired grant authorizes nothing, so every
    guarantee that holds for "no grant" must hold identically here, including that the refused
    move leaves NO record. The distinct name exists so a caller can tell "you were never
    allowed" from "you waited too long" — those want different responses from the asker."""


class Unproven(Exception):
    """The code this move would summon is not in proven-space RIGHT NOW (Law 8).

    Replaces ``registry.UnprovenMethod``, and the rename is the design change: there is no
    METHOD name any more, only the address of a proof and the seal beside it. Four ways to
    earn this refusal, and the reader (``validation_store.standing``) says which in one pass —
    never sealed, newest seal red, sealed green but carrying no fingerprint, or sealed green
    with the horizon closed because the code moved underneath it."""


class Unresourced(Exception):
    """The host has no room for what this move would summon — the fourth refusal.

    Not an authority failure and not a rules failure: the actor was entitled, the move was
    legal, and the answer is still no. It carries no reading, because the gate never received
    one — only which line was crossed (Law 6)."""


class OwnerUnresolvable(Exception):
    """The gate cannot tell WHOSE boat this is — so it refuses, and it never guesses.

    Deliberately NOT a subclass of ``Unauthorized``, because the two want opposite
    responses from the asker. ``Unauthorized`` means *you have no standing here* and the
    fix is a grant. This means *the boat does not say who owns it* and the fix is one line
    in a file — so the refusal always names the file it opened and the line to add. A
    reader that could not tell them apart would go looking for permission when what is
    missing is a fact.

    The alternative — falling back to some default owner when a hop does not resolve — is
    the ticket's own falsifier clause (1) wearing a coat: the owner would once again be
    something other than what the boat says, and the gate would be checking a value it
    invented."""


class IntentionRetired(Exception):
    """The boat is riding an intention that has been RETIRED — so the gate refuses a
    forward crossing and names what replaced it.

    Not an authority failure: the actor may be a perfectly admitted hand, and the move may
    be perfectly legal. It is a failure of the thing the work is FOR. An intention is the
    design a boat is a translation of (Law 9), so a boat still sailing under a retired one
    is building toward a picture nobody holds any more — and the whole point of this
    refusal is that the state cannot be passed SILENTLY while boats still ride it.

    THE BACK-EDGE IS EXEMPT, and that is not a softening. A retreat is how a boat that has
    lost its intention gets DEALT WITH — sent back to design, re-parented, ended. Refusing
    the retreat too would leave such a boat with no legal move at all, which is a gate that
    has stopped being a gate and started being a wall.

    AND THE GATE DECIDES NOTHING BEYOND THE REFUSAL. What happens to a boat found riding a
    retired intention — ended, re-parented, sailed on under a ruling — is the owner's act
    (Law 6). A gate that resolved it automatically would have taken the owner's gate."""


class RetirementUnreadable(Exception):
    """A charter carries the retirement key and the gate cannot read it — so it refuses.

    Deliberately NOT collapsed into "not retired". A malformed retirement is exactly the
    shape that would let the state pass silently: the key is there, somebody meant
    something by it, and treating it as absence is a record of truth being smoothed into a
    coherent shape (Law 7). Every lack is named in one pass, the way ``ruling.supersede``
    names all six of its refusals at once — a caller fixing one field at a time learns the
    schema one refusal at a time, which is the door teaching badly."""


@dataclass(frozen=True)
class Retirement:
    """A charter's retirement, as the gate reads it off the charter.

    ``superseded_by`` IS NULLABLE ON PURPOSE, and that nullability is the whole reason this
    state lives on the RETIRED charter rather than on its successor. ``ruling.supersede``
    (cairn/machines/ruling/ruling.py) does it the other way — the successor appends to its
    own ``supersedes`` list and the retired packet is never touched — because what it
    retires is a packet carrying Akien's signature, and rewriting a signed record is the
    thing that door exists to prevent.

    A charter is not that. It is an authored design record that has always grown by
    ADDITION, and three measurements say the inversion does not transfer:

      - A deprecation with NO successor would be inexpressible. An intention can simply
        stop being the design without another one taking its place, and a scheme that can
        only say "X replaced Y" cannot say that at all.
      - Reading it would cost a scan of every charter in the corpus (59 of them, measured
        2026-08-18) inside EVERY crossing, for a state that is almost always absent.
      - The one seat that needs the answer — ``boat_owner_of`` — already has the retired
        charter's dict in hand, because it opened that file to read ``gated_by``. On this
        side the read is one ``.get``; on the other it is a corpus walk.

    WHAT DOES TRANSFER FROM THE RULING DOOR, and it is the part that matters: evidence is
    REQUIRED (a retirement with no stated why is a design change nobody can argue with),
    and the shape is normalised on READ, never by rewriting what is on disk."""

    superseded_by: str | None
    when: str
    evidence: str


def retirement_of(charter: dict, *, at: str = "<charter>") -> Retirement | None:
    """Read a charter's retirement — one ``.get`` on a dict the caller already holds.

    Returns ``None`` when the charter carries no retirement key at all, which is the
    ordinary case for every charter in the corpus today. Raises ``RetirementUnreadable``
    when the key is PRESENT and malformed — the distinction the caller must not be allowed
    to collapse.

    The shape::

        "retired": {"superseded_by": "<address>" | null,   # null = retired, nothing replaced it
                    "when":          "<date>",
                    "evidence":      "<why this stopped being the design>"}

    Normalises on read and never by rewrite: a bare string under the key is taken as the
    successor address with the rest unstated, because that is the shape a hand reaches for
    first and refusing it would teach nothing a default cannot. ``ruling.py`` pays the same
    price for the same reason — its ``_supersessions`` normalises two on-disk shapes on
    READ, and the measured lesson recorded there is that normalising by rewrite costs the
    record while normalising on read costs one function.
    """
    raw = charter.get(_RETIREMENT_KEY)
    if raw is None:
        return None
    if isinstance(raw, str):
        raw = {"superseded_by": raw.strip() or None}
    if not isinstance(raw, dict):
        raise RetirementUnreadable(
            f"{at} carries a {_RETIREMENT_KEY!r} key of type {type(raw).__name__}, which "
            f"is neither an object nor an address string. It is NOT read as 'not retired' "
            f"— a key somebody meant something by, treated as absence, is exactly how this "
            f"state passes silently. Shape: {{\"superseded_by\": <address or null>, "
            f"\"when\": <date>, \"evidence\": <why>}}."
        )

    lacks = []
    succ = raw.get("superseded_by")
    if succ is not None and (not isinstance(succ, str) or not succ.strip()):
        lacks.append("'superseded_by' must be an address string, or null for a retirement "
                     "with nothing replacing it — an empty string is neither")
    when = raw.get("when")
    if not isinstance(when, str) or not when.strip():
        lacks.append("'when' must be a non-empty date string — a retirement with no date "
                     "cannot be told apart from one recorded years ago")
    evidence = raw.get("evidence")
    if not isinstance(evidence, str) or not evidence.strip():
        lacks.append("'evidence' must be a non-empty string saying WHY this stopped being "
                     "the design — required for the same reason ruling.supersede requires "
                     "it: a retirement nobody can argue with is a design change nobody can "
                     "argue with")
    if lacks:
        raise RetirementUnreadable(
            f"{at} carries a malformed {_RETIREMENT_KEY!r}, {len(lacks)} lack(s), all named "
            "in one pass:\n  - " + "\n  - ".join(lacks)
        )
    return Retirement(superseded_by=(succ.strip() if isinstance(succ, str) else None),
                      when=when.strip(), evidence=evidence.strip())


@dataclass(frozen=True)
class BoatOwner:
    """Who owns a boat, as the gate reads it off the boat — TWO facts, kept apart.

    ``intention`` is the OWNER (ruled 2026-08-10: intentions own their tickets, a ticket
    owns its workflow, and the workflow IS the boat). ``hands`` are the movers that
    intention's owner-gate admits. They are different namespaces on purpose and the
    original defect was collapsing them: the gate used to compare a mover against a mover
    and call the result ownership. An intention cannot act, so a hand is never *equal* to
    the owner — it is *admitted by* it, which is Law 6's second clause (delegated access
    happens through the owner's gate, never ambiently) rather than its first."""

    intention: str
    hands: tuple[str, ...]
    # THE THIRD READ FACT, and it costs nothing to carry: the charter this owner was read
    # from was already open and parsed to reach ``gated_by``, so the retirement is one more
    # ``.get`` on a dict in hand rather than a lookup. ``None`` for every charter in the
    # corpus today. Defaulted so that every existing constructor call — proofs included —
    # keeps working unchanged; a boat whose owner was built without this simply reads as
    # riding a living intention, which is what it was already asserting.
    retired: "Retirement | None" = None


def boat_owner_of(boat_id: str, *, tickets_dir: str = TICKETS_DIR,
                  cairn_root: str = CAIRN_ROOT,
                  commons_root: str = COMMONS_ROOT) -> BoatOwner:
    """Read a boat's owner OFF THE BOAT. Files only — two of them, opened directly.

    The resolution the ruling settles, hop by hop:

        boat_id  ->  CairnCommons/tickets/<boat_id>.json   (the boat IS its ticket)
                 ->  that ticket's ``owning_intention``     (an address)
                 ->  that intention's charter               (beside code, or homeless)
                 ->  its ``gated_by``                       (the hands it admits)

    NO DAEMON, NO REGISTRY, NO NETWORK — gate (iii) of the ticket's PROVEME set, and it is
    a hard bound rather than an aesthetic: this runs inside a crossing, and a crossing that
    can only complete when something else is up is a crossing that stops working for
    reasons unrelated to itself.

    Every hop that does not resolve raises ``OwnerUnresolvable`` naming the address that
    was opened and the one line that would fix it. The roots are parameters ONLY so a proof
    can point this at a fixture; ``clear`` calls it with none of them.
    """
    if not isinstance(boat_id, str) or not boat_id.strip():
        raise OwnerUnresolvable(
            f"boat_id {boat_id!r} is not a ticket id, so there is no boat to read an owner "
            "off. A boat IS its ticket (ruled 2026-08-10) — the id is the filename under "
            "CairnCommons/tickets/."
        )

    ticket_path = os.path.join(tickets_dir, f"{boat_id}.json")
    if not os.path.isfile(ticket_path):
        raise OwnerUnresolvable(
            f"boat {boat_id!r} has no ticket at {ticket_path} — nothing on disk says who "
            "owns this voyage, so the gate refuses rather than assuming. If the boat is "
            "real, /sorted casts it; if the id is wrong, the crossing is naming a boat "
            "that does not exist."
        )
    try:
        ticket = json.loads(open(ticket_path, encoding="utf-8").read())
    except (ValueError, OSError) as exc:
        raise OwnerUnresolvable(
            f"boat {boat_id!r}'s ticket at {ticket_path} could not be read: {exc}"
        ) from exc

    addr = ticket.get("owning_intention")
    if not isinstance(addr, str) or not addr.strip():
        raise OwnerUnresolvable(
            f"boat {boat_id!r}'s ticket at {ticket_path} names no owning intention. FIX, "
            'one line: add "owning_intention": "<path to the intention+why.json that owns '
            'this ticket>". The field is declared in CairnCommons/tickets/_charter+why.json '
            "and it is deliberately NOT back-filled across the corpus — a value nobody "
            "checked is a guess with somebody's confidence attached, so it is filled when a "
            "real crossing needs it, which is now."
        )

    for root in (cairn_root, commons_root):
        charter_path = os.path.join(root, addr)
        if os.path.isfile(charter_path):
            break
    else:
        raise OwnerUnresolvable(
            f"boat {boat_id!r} names owning intention {addr!r}, which resolves under "
            f"neither {cairn_root} nor {commons_root}. An owning intention is an ADDRESS: "
            "a path to a beside-code intention+why.json, or to a file under "
            "intentions-not-beside-code/ for a homeless one."
        )
    try:
        charter = json.loads(open(charter_path, encoding="utf-8").read())
    except (ValueError, OSError) as exc:
        raise OwnerUnresolvable(
            f"boat {boat_id!r}'s owning intention at {charter_path} could not be read: {exc}"
        ) from exc

    hands = charter.get("gated_by")
    if (not isinstance(hands, list) or not hands
            or any(not isinstance(h, str) or not h.strip() for h in hands)):
        raise OwnerUnresolvable(
            f"boat {boat_id!r} is owned by {addr}, and that intention does not declare "
            f"which hands its owner-gate admits (read {charter_path}). FIX, one line: add "
            '"gated_by": ["<actor>", ...] to that charter — a list of actor names, compared '
            "by exact membership. It is prose in `owner` today and prose cannot gate: "
            "measured 2026-08-10, 22 of 24 beside-code charters carry an `owner` over 60 "
            "characters and 2 carry an empty one, so matching an actor against it would be "
            "a substring scan that goes green for the wrong reason."
        )
    # AND THE RETIREMENT, OFF THE SAME DICT. No second file, no second parse: this charter
    # was opened above to reach ``gated_by`` and is still in hand. A malformed key RAISES
    # rather than reading as absence — see ``retirement_of`` — and it raises as
    # ``RetirementUnreadable``, not ``OwnerUnresolvable``, because the owner IS resolvable
    # and telling a caller otherwise would send them to fix the wrong line.
    return BoatOwner(intention=addr, hands=tuple(hands),
                     retired=retirement_of(charter, at=charter_path))


@dataclass(frozen=True)
class Riders:
    """Who is riding one intention right now — and, inseparably, what the read COULD NOT SEE.

    The four blind fields are not diagnostics hung off the side of the answer; they are half
    of the answer. A scan that reports only what it found is a green earned by not looking,
    and this read has a specific, measured way to earn one: on 2026-08-18 THIS FUNCTION
    measured the live corpus at 69 boats in flight, of which 40 named no owning intention at
    all, 7 named one that resolves under neither root, and 3 carried a state it could not
    judge — 22 attributable out of 69. (The hand sweep that cast the ticket said 28 of 72,
    because it neither filtered to in-flight nor parsed the workflow string; the instrument's
    numbers are the ones that stand.) A string-matched reverse read over that corpus would
    have reported a clean "nobody is riding this" for almost any address — the exact hollow
    the ticket that built this names as its wrong-shape.

    THE THIRD CLASS WAS NOT IN THE TICKET, AND IT IS THE WORST OF THEM. ``unresolvable``
    boats DO carry an ``owning_intention``, so a naive read counts them as attributed — to
    an intention that does not exist. They vanish from the real owner's list AND inflate the
    attributed total, which is invisible in the direction that matters. One of the eight was
    written by this hand on the day this was built, hours after reading the resolution rule.

    ``unreadable`` covers a ticket the read could not judge at all — bad JSON, or a ``state``
    the chokepoint's own parser cannot make a workflow of. THREE today, and it was predicted
    to be zero: the ticket's hypothesis named two blind classes and the corpus has three, so
    this one is reported as its own rather than folded into "not riding". It is reported even
    at zero, because a class that only appears when it is non-zero is a class a reader learns
    to assume away.
    """

    intention: str
    riding: tuple[str, ...]
    in_flight: int
    # COUNTED IN THE WALK, NOT DERIVED — and the difference was measured rather than
    # reasoned. This started as ``in_flight - len(unattributed) - len(unresolvable)``, which
    # made the partition identity below TRUE BY ARITHMETIC: dropping a blind class from the
    # report raised ``attributable`` by exactly as much and every check stayed green. The
    # mutation tooth in test_clearance.py caught it on its first run — a report whose
    # blindness cannot be removed without something going red is the whole claim here, and
    # for one commit it was a claim about subtraction.
    attributable: int
    unattributed: tuple[str, ...]
    unresolvable: tuple[tuple[str, str], ...]
    unreadable: tuple[tuple[str, str], ...]

    @property
    def blind(self) -> dict:
        """The three blind classes as counts — always all three, even at zero."""
        return {"unattributed": len(self.unattributed),
                "unresolvable": len(self.unresolvable),
                "unreadable": len(self.unreadable)}


def _in_flight(state: str):
    """Is this boat still sailing? Returns True/False, or raises for a state it cannot judge.

    Settled ONCE, here, and derived rather than listed: a boat is in flight when its cursor
    is not the last state of its own workflow path. There is deliberately no set of terminal
    state names in this file — a second list of states is a second place for the workflow
    grammar to live, and the chokepoint's parser already knows where a path ends.

    A prose state (no bracket, no arrows) is not judgeable and says so by raising; the caller
    counts it in ``unreadable`` rather than guessing a boat into or out of the fleet.
    """
    wf = parse_workflow(state)          # MalformedWorkflow for anything it cannot read
    return wf.cursor < len(wf.path) - 1


def riders_of(intention: str, *, tickets_dir: str = TICKETS_DIR,
              cairn_root: str = CAIRN_ROOT,
              commons_root: str = COMMONS_ROOT) -> Riders:
    """THE REVERSE OF ``boat_owner_of``: given an intention address, which in-flight boats
    name it — and how many the read could not attribute at all.

    Files only, exactly like the forward hop it inverts, and for the same hard reason: this
    is read at a moment when somebody is deciding whether to retire an intention, and an
    answer that depends on something else being up is an answer that stops working for
    reasons unrelated to itself.

    NOT AN INDEX AND NOT A CACHE. It is a walk of the ticket corpus, computed on read, the
    way the fleet register is (Law 7 — an aggregate that is stored is an aggregate that can
    drift from the boats). At corpus scale that is 72 small file reads; when it turns hot,
    the event-fired cache the register already names is the grow-against-need step, never a
    poll.

    The match is by RESOLVED PATH, not by string. Two tickets can spell the same charter two
    ways (an address relative to either root), and a string match would file them under two
    different owners while reporting neither as blind.
    """
    want = _resolved_charter(intention, cairn_root=cairn_root, commons_root=commons_root)
    riding, unattributed, unresolvable, unreadable = [], [], [], []
    in_flight = attributable = 0

    for name in sorted(os.listdir(tickets_dir) if os.path.isdir(tickets_dir) else []):
        if not name.endswith(".json"):
            continue
        path = os.path.join(tickets_dir, name)
        try:
            ticket = json.loads(open(path, encoding="utf-8").read())
        except (ValueError, OSError) as exc:
            unreadable.append((name, f"unreadable ticket: {exc}"))
            continue
        boat_id, state = ticket.get("id"), ticket.get("state")
        if not boat_id or not isinstance(state, str):
            continue                    # not a boat (the folder's own schema doc) — the
                                        # register's rule for what a boat IS, composed
        try:
            if not _in_flight(state):
                continue                # berthed: it is not riding anything any more
        except Exception as exc:        # noqa: BLE001 — any parse failure is the same fact
            unreadable.append((boat_id, f"state not judgeable: {exc}"))
            continue

        in_flight += 1
        addr = ticket.get("owning_intention")
        if not isinstance(addr, str) or not addr.strip():
            unattributed.append(boat_id)
            continue
        got = _resolved_charter(addr, cairn_root=cairn_root, commons_root=commons_root)
        if got is None:
            unresolvable.append((boat_id, addr))
            continue
        attributable += 1
        if want is not None and got == want:
            riding.append(boat_id)

    return Riders(intention=intention, riding=tuple(riding), in_flight=in_flight,
                  attributable=attributable, unattributed=tuple(unattributed),
                  unresolvable=tuple(unresolvable), unreadable=tuple(unreadable))


def _resolved_charter(addr: str, *, cairn_root: str, commons_root: str) -> str | None:
    """An intention address -> the real file it names, or None. The same two-root rule
    ``boat_owner_of`` walks, spelled once and shared, so the forward hop and its inverse can
    never disagree about what an address means."""
    if not isinstance(addr, str) or not addr.strip():
        return None
    for root in (cairn_root, commons_root):
        candidate = os.path.join(root, addr)
        if os.path.isfile(candidate):
            return os.path.realpath(candidate)
    return None


@dataclass(frozen=True)
class Grant:
    """A per-operation delegation: the owner authorizes ONE actor to make ONE transition on
    ONE boat, WITHIN A WINDOW. Frozen and specific by construction — it cannot be widened after
    minting, and it authorizes nothing but the exact (boat, target, actor) it names, for as long
    as it names. Non-ambient physics: authority is a thing you hold FOR an operation, not a
    standing capability you keep — and the expiry is what stops "for an operation" from quietly
    becoming "forever" whenever an operation is slow to happen.

    The window is also what makes a lagging instrument safe. A resource verdict is true when it
    is given and decays from there; a grant that never expired would let a builder bank a yes
    from a quiet moment and spend it into a loaded box. Ten seconds is the leash on that."""

    boat_id: str
    target: str
    to_actor: str
    by_owner: str
    issued_at: float = field(default_factory=time.monotonic)
    ttl_seconds: float = GRANT_TTL_SECONDS

    def authorizes(self, *, boat_id: str, target: str, actor: str, owner: str) -> bool:
        """True only for the exact operation this grant names, issued by this boat's owner.

        ``owner`` IS NOW THE READ OWNER — the intention address ``boat_owner_of`` resolved,
        not a string the caller chose (ticket boat-owner-is-read-not-stated). Before
        2026-08-10 both sides of this comparison came from the same caller in the same
        call, so a caller who could state ``boat_owner`` could mint itself a grant from
        that same fictional owner and this check would pass. Fixing the direct branch alone
        would have moved the hole one door along rather than closing it.

        IDENTITY ONLY — it deliberately does not consider the clock. "This grant was never for
        you" and "this grant lapsed" are different answers to the asker, so the gate asks them
        separately and refuses with different names."""
        return (
            self.by_owner == owner
            and self.boat_id == boat_id
            and self.target == target
            and self.to_actor == actor
        )

    def expired(self, now: float | None = None) -> bool:
        """Has the window closed? ``now`` is injectable so the expiry is provable without a
        sleep — a proof that waits on a wall clock is a flake with a schedule."""
        if now is None:
            now = time.monotonic()
        return (now - self.issued_at) >= self.ttl_seconds


def mint_grant(*, minted_by: str, boat_id: str, to_actor: str, target: str,
               now: float | None = None, ttl_seconds: float = GRANT_TTL_SECONDS,
               **read_roots) -> Grant:
    """The owner delegates ONE operation — the only door delegation passes through (Law 6).

    THE OWNER IS READ, NOT DECLARED (ticket boat-owner-is-read-not-stated, 2026-08-10).
    The old signature took ``owner`` as a bare string, which meant minting was a promise
    the minter made about itself: the parameter that had to be true was supplied by the
    party it was true *about*. Now the boat is read, and ``minted_by`` — the HAND doing
    the minting — must be one the owning intention's gate admits, or nothing is minted.

    So the two questions have been separated, and the separation is the fix. WHO is
    delegating is read off the boat (``by_owner`` carries the owning intention's address).
    WHETHER this hand may delegate on that intention's behalf is checked against the
    intention's own ``gated_by``. A hand with no standing on a boat can no longer manufacture
    standing for anybody, itself included.

    WHAT THIS STILL DOES NOT SETTLE, named rather than implied: any admitted hand may mint
    for any other. On a box with one hand that is not observable, and the fuller question —
    who may mint on an intention's behalf, as against merely act for it — is filed as ticket
    an-intention-declares-its-gated-hands rather than answered here.

    The mint stamps the clock. There is no way to mint an unexpiring grant — the window is a
    property of the capability, not an option a caller can decline.
    """
    owner = boat_owner_of(boat_id, **read_roots)
    if minted_by not in owner.hands:
        raise Unauthorized(
            f"{minted_by!r} may not mint a grant on boat {boat_id!r}: that boat is owned by "
            f"{owner.intention}, whose gate admits {list(owner.hands)!r}. Delegated access "
            "happens through the OWNER's gate, never ambiently (Law 6) — a hand that cannot "
            "move a boat cannot authorize somebody else to move it either."
        )
    return Grant(
        boat_id=boat_id, target=target, to_actor=to_actor, by_owner=owner.intention,
        issued_at=time.monotonic() if now is None else now,
        ttl_seconds=ttl_seconds,
    )


def _decide(
    workflow_str: str,
    target: str,
    *,
    actor: str,
    boat_id: str,
    proven_by: str,
    grant: Grant | None = None,
    history_path: str | None = None,
    state_path: str | None = None,
    node_class_root=None,
    resources=None,
    lines: dict | None = None,
    now: float | None = None,
    **journal_extra,
) -> str:
    """Clear a transition, or refuse it — the authority rung wrapping the rules+truth chokepoint.

    WHAT A CC-MADE CROSSING NAMES (settled 2026-08-10, ticket
    emit-refuses-an-uncleared-crossing). The four arguments below are not free text, and
    until this settlement they had never been supplied by anything but a proof. The door
    may not mint them — a door-minted value can never disagree with the door, which is the
    same two-witness argument that killed auto-inherit for chart claims — so they are
    stated here, at the owner's address, and the caller supplies them:

      - ``actor`` — WHO MOVED THE BOAT. For a crossing CC makes, the string is ``"CC"``.
        Measured before settling: 16 records already carried an ``actor`` and already
        carried TWO spellings for one mover — ``"CC"`` x12 and ``"claude"`` x4 — because
        nothing had ever gated the field. The majority spelling wins on the ordinary
        ground that it is what Akien calls this hand. The 4 dissenting records are NOT
        repaired: they are a record of truth and they were never improper (Law 7).
      - ``boat_id`` — THE TICKET, and since 2026-08-10 also the only thing the gate needs
        in order to know whose boat it is. It is already on every gated crossing, so it
        adds no vocabulary; it names WHICH voyage is moving, and the owner is READ from it.
        The gate now also refuses a call whose ``boat_id`` and ``journal_extra["ticket"]``
        disagree — the docstring has asserted they are the same thing since this function
        was written, and until that check existed a caller could hand a real ticket to the
        three chokepoint gates and an unrelated boat_id to this one, so the owner would be
        read off a different boat than the one being recorded.

      THERE IS NO ``boat_owner`` ARGUMENT, and the two superseded answers to what one
      would have held are kept here because the sequence is the instruction (ticket
      boat-owner-is-read-not-stated, ruling 2026-08-10-the-ticket-owns-the-refusal):

        SUPERSEDED (1), the component reading: "THE COMPONENT WHOSE HISTORY IS BEING
        APPENDED TO — for a crossing journaled at cairn/tools/base/history.json that is 'base'".
        Killed by the first live fire on 2026-08-10: the gate compared ``actor`` against
        ``boat_owner`` for identity, so a component name put the two in different
        namespaces and every CC crossing refused as ``Unauthorized``. The component owns
        its history FILE; that is a different ownership that happened to share a word.

        SUPERSEDED (2), the mover reading that replaced it: "WHO OWNS THE VOYAGE, in the
        same namespace as ``actor`` — for a voyage CC sails on Akien's box that is 'CC', so
        ``actor == boat_owner``". Not killed by an error but by the hole it left, which
        this file named at the time: the caller stated BOTH sides of the identity the gate
        checked, so a caller could always make them equal and the Law 6 refusal bound an
        honest caller and nothing else. It also claimed, factually, that "the ticket's
        ``owner`` field is prose about components". IT IS NOT: measured across the 91 filed
        tickets that carry the field, only 5 distinct values name a component and 56 run
        past 120 characters — it is prose about people and agents far more often, which is
        why it could not simply be re-read under the ruling.

        RULED, and what the code now does: an INTENTION owns its TICKET, a ticket owns its
        WORKFLOW, and the workflow IS the boat — one object from two vantages, which is why
        ``boat_id`` has always been the ticket id. So the owner is not in the same namespace
        as the actor at all, and the check is not an identity test any more: ``boat_owner_of``
        resolves boat_id -> ticket -> ``owning_intention`` -> that charter -> ``gated_by``,
        and the gate asks whether ``actor`` is a hand that intention's owner-gate ADMITS. A
        hand is never equal to an intention; it is admitted by one, which is Law 6's second
        clause rather than its first. NO DEVICE SITS ABOVE A BOAT: this device operates the
        gate, and the refusal it raises is the boat's own.

        WHAT IS STILL RED, and it cannot be built away on this box: the ticket's falsifier
        clause (3) — every boat's owner resolving to the same string — is ALREADY TRUE at
        n=2, because both cleared crossings in the corpus were made by one hand. No amount
        of building distinguishes a working owner-read from a constant while only one hand
        exists, so the claim is carried forward by an instrument instead of an argument:
        probes/boat_owner_comes_from_the_boat.py, whose ``enough`` is deliberately NOT
        satisfiable by volume.
      - ``proven_by`` — THE PROOF THIS MOVE IS CLEARED ONTO, sealed and still describing
        the code as it stands. For a voyage this is the proof its own PROVEME step just
        sealed, which is what makes clearance affordable at all: proven-space is a FRESH
        state that decays (measured 2026-08-10: only 4 of 78 proofs in the corpus were
        standing, and they were the four most recently sealed), so the honest moment to
        lean on a seal is the moment after it is cut.

    ``**journal_extra`` rides through to ``emit`` untouched, and it is not a convenience:
    WITHOUT IT THIS FUNCTION WAS UNCALLABLE FOR EVERY CROSSING THAT MATTERS. Three gates
    at the chokepoint read ``journal_extra["ticket"]`` — the entry gate at BUILDME, the
    exit gate at PROVED, the emission gate at a carried WATCHME — and each refuses a
    crossing that names no cast ticket. Before 2026-08-10 ``clear`` accepted no such
    argument, so a caller who did everything right was still refused at the door with
    ``TicketRequiredRed``. That is the measured reason the authority rung went a year with
    no production caller: not discipline, but physics pointing the wrong way — the ticket
    gate that landed 2026-07-29 made the clearance gate structurally unreachable, and
    nothing said so because nobody was calling it to find out.

    Binds four refusals before the cursor may move, then records the crossing:
      1. AUTHORITY (Law 6): the boat's owner is READ (``boat_owner_of``, two files, no
         network), and ``actor`` must be a hand that owning intention's gate admits — or
         hold a ``grant`` that authorizes exactly this (boat_id, target, actor) and was
         minted by that same read owner, and has not lapsed. Otherwise → ``Unauthorized``
         (or ``GrantExpired``, its subclass, when the grant named the right operation but
         its window closed). A boat that does not say who owns it → ``OwnerUnresolvable``,
         which is a MISSING FACT and not a denied permission; the gate never guesses a
         default, because a guessed owner is the same hole under a new name. Checked first:
         an actor with no standing here is turned away before anything else is inspected.
      2. PROVEN-SPACE (Law 8): ``proven_by`` is the ADDRESS OF A PROOF — the code this move
         summons is the component that proof lives in. The seal beside it must be green AND
         still describe the code as it stands (the source fingerprint the tester recorded).
         Otherwise → ``Unproven``. The seal is read, nothing is called — the harbor clears the
         move, it does not sail it. There is no registry to populate: the proof's address IS
         the key, and a stale green refuses (Law 3).
      3. RESOURCES: if this harbor was wired to a resource owner, every line in ``lines`` is
         put to it and a crossed line refuses the move → ``Unresourced``. ``resources`` is
         anything with ``ask(name, value) -> bool`` (system_rackmount's may-I door). The
         harbor holds the LINES; the resource owner holds the METRICS and answers only a
         verdict, so neither half can drift into the other (Law 6). Left un-wired
         (``resources=None``) this gate does not run, and the harbor is honestly a harbor with
         no view of the host — not a harbor that decided there was room.
      4. RULES + TRUTH (Law 4/7): ``emit`` validates legality against the class's versioned
         table and, only if legal, journals the crossing through the projector's write-door
         (append-only, carrying ``cleared_by`` and whether it was delegated). An illegal
         move → ``IllegalTransition`` and NOTHING is written — authority never buys an
         illegal transition.

    Returns the new workflow string (cursor moved to ``target``). Every refusal raises before
    ``emit`` is reached, so a refused move leaves no CROSSING record — unauthorised OR unproven
    OR unresourced OR illegal means the boat did not move and no history was appended to.

    THIS IS THE DECISION HALF ONLY, AND IT IS NOT THE PUBLIC DOOR. ``clear`` wraps it and
    records the ATTEMPT either way (ticket clearance-leaves-a-trace, 2026-08-10) — so
    "a refused move leaves no partial record" is still true of the crossing journal, and no
    longer true of the world: a refusal now leaves a trace in the gate's own queue, which is
    a different store precisely because a refusal is not a crossing. Call ``clear``; this
    function is private so that a caller cannot reach the decision while stepping around the
    record, which is Law 6 on the gate's own queue (the write happens inside the gate, never
    at the caller's discretion).
    """
    # 0. THE WITNESS IS THE GATE'S TO WRITE. A caller may enrich the record through
    #    ``journal_extra``, but it may not hand in the very fields this gate exists to
    #    stamp — a self-declared ``cleared_by`` is exactly the door-minted value the
    #    ticket's falsifier clause (3) names, and letting one through silently would make
    #    the authority check vacuous at the one door that reads it. Refused LOUDLY rather
    #    than dropped: a quietly discarded field is a record of truth collapsing an error
    #    into a coherent shape, which Law 7 forbids at exactly this surface.
    _witness = _GATE_WITNESS_FIELDS & journal_extra.keys()
    if _witness:
        raise Unauthorized(
            f"a caller may not hand this gate its own witness: {sorted(_witness)} "
            f"{'is' if len(_witness) == 1 else 'are'} written BY the clearance gate, never "
            "to it. A self-declared clearance can never disagree with the door, which is "
            "the whole reason the door is worth passing through (Law 6). Drop the field "
            "and let the gate stamp it."
        )

    # 0b. AND THE GATE'S READ IS THE GATE'S TO MAKE. Removing ``boat_owner`` from the
    #     signature is not sufficient on its own: ``**journal_extra`` would swallow a
    #     stray ``boat_owner=`` and journal it, so the caller would still be stating an
    #     ownership claim — one that no longer even gets checked, which is worse than the
    #     hole it replaced. Refused by name, with the fix, rather than dropped.
    _stated = _UNSTATABLE_FIELDS & journal_extra.keys()
    if _stated:
        raise Unauthorized(
            f"a caller may not tell this gate who owns the boat: {sorted(_stated)} "
            f"{'is' if len(_stated) == 1 else 'are'} READ off the boat, never handed to "
            "the gate (ticket boat-owner-is-read-not-stated, ruled 2026-08-10). A caller "
            "that states both sides of the identity check can always make them equal, "
            "which is the Law 6 refusal binding an honest caller and nothing else. Drop "
            f"the field: {boat_id!r} is enough, because a boat IS its ticket."
        )

    # 0c. THE BOAT AND THE RECORD MUST NAME THE SAME VOYAGE. They arrive by different
    #     routes — ``boat_id`` a named parameter, ``ticket`` inside ``journal_extra`` — and
    #     the chokepoint's three gates read the second while this rung reads the first. The
    #     docstring has called them the same thing since this function was written; now the
    #     door does. Refused BEFORE emit, so a mismatched call leaves no partial record.
    _ticket = journal_extra.get("ticket")
    if _ticket is not None and _ticket != boat_id:
        raise Unauthorized(
            f"this crossing names two different voyages: boat_id={boat_id!r} but "
            f"ticket={_ticket!r}. A boat IS its ticket (ruled 2026-08-10), so the owner "
            "would be read off one boat while the record was written about another. Pass "
            "the same id to both, or fix whichever one is wrong."
        )

    # 1. AUTHORITY (Law 6) — the owner is READ off the boat; the actor is a hand that
    #    owning intention's gate admits, or one holding a grant that intention minted.
    owner = boat_owner_of(boat_id)
    delegated = actor not in owner.hands
    if delegated:
        if grant is None or not grant.authorizes(
            boat_id=boat_id, target=target, actor=actor, owner=owner.intention
        ):
            raise Unauthorized(
                f"{actor!r} may not move boat {boat_id!r} to {target!r}: that boat is owned "
                f"by {owner.intention}, whose gate admits {list(owner.hands)!r}, and "
                f"{actor!r} holds no grant for THIS operation — authority is per-operation "
                f"and non-ambient (Law 6)"
            )
        if grant.expired(now):
            raise GrantExpired(
                f"{actor!r} holds a grant for boat {boat_id!r} -> {target!r} that LAPSED: "
                f"minted with a {grant.ttl_seconds}s window and spent after it closed. Ask "
                f"again — a stale yes is not a yes, because what it was true about has moved"
            )

    # 1b. THE INTENTION MUST STILL BE THE DESIGN (Law 9). The charter was already opened and
    #     parsed in step 1 to reach ``gated_by``, so this costs one ``.get`` on a dict in
    #     hand — no second file, no lookup, no scan. It sits AFTER authority deliberately:
    #     an actor with no standing here is turned away before anything about the boat is
    #     inspected, which is the ladder's existing rule and not a new one.
    #
    #     FORWARD ONLY. A retreat is how a boat that has lost its intention gets dealt with;
    #     refusing that too would leave it with no legal move at all. The direction is read
    #     through the chokepoint's own grammar rather than a second rule of this file's —
    #     ``resolve_target`` is what decides which POSITION naming a target means, so asking
    #     it is asking the same authority ``emit`` will ask a few lines below.
    if owner.retired is not None:
        try:
            _forward = resolve_target(parse_workflow(workflow_str), target) > \
                parse_workflow(workflow_str).cursor
        except Exception:               # noqa: BLE001 — an unparseable string is emit's red
            _forward = True             # to raise, not this gate's to swallow; treat the
                                        # crossing as forward so the retirement is never
                                        # skipped by a malformed workflow
        if _forward:
            _succ = owner.retired.superseded_by
            raise IntentionRetired(
                f"boat {boat_id!r} may not move forward to {target!r}: the intention it "
                f"sails under, {owner.intention}, was RETIRED on {owner.retired.when} — "
                + (f"superseded by {_succ}. " if _succ else
                   "with nothing replacing it (retired outright, no successor). ")
                + f"Why: {owner.retired.evidence} "
                "The boat is not ended and not re-parented by this refusal — that is the "
                "owner's act (Law 6). Retreating is still legal; this gate refuses only "
                "forward motion, so a boat that has lost its design cannot quietly build "
                "toward it."
            )

    # 2. PROVEN-SPACE (Law 8) — the code the move summons must be proven, and still be the code
    #    that was proven. One file read at a derived address; no registry, nothing to populate.
    proven = standing(proven_by)
    if not proven["proven"]:
        raise Unproven(
            f"{actor!r} may not move boat {boat_id!r} to {target!r} onto code that is not in "
            f"proven-space: {proven['why']}. The harbor clears only onto proven code (Law 8)"
        )

    # 3. RESOURCES — the fourth refusal. The harbor asks the resource owner about ITS OWN lines
    #    and receives a verdict, never a reading. Nothing here counts anything: a line is about
    #    PRESSURE on the host, and pressure is observable without a census of who is causing it.
    if resources is not None:
        for name, value in (HARBOR_LINES if lines is None else lines).items():
            if resources.ask(name, value):
                raise Unresourced(
                    f"the host has no room to move boat {boat_id!r} to {target!r}: the harbor's "
                    f"{name} line ({value}) is crossed. The move is authorized, proven and legal "
                    f"— and still refused. Ask again when the box is quieter"
                )

    # 4. RULES + TRUTH (Law 4/7) — wrap the chokepoint: it refuses the illegal, journals the legal.
    emit_kwargs = {}
    if node_class_root is not None:
        emit_kwargs["node_class_root"] = node_class_root
    return emit(
        workflow_str,
        target,
        history_path=history_path,
        state_path=state_path,
        cleared_by=actor,
        # AND THE ORDINARY FIELD TOO, not only the gate's witness. ``actor`` is the record
        # vocabulary every existing reader uses for "who moved the boat" — the corpus census
        # in troubles/every-crossing-goes-around-the-clearance-gate, the probes at
        # cairn/*/probes/, the state window. ``cleared_by`` is a different claim: that the
        # authority rung RAN, and who it cleared. On a cleared crossing the two carry the
        # same string by construction, and that is not redundancy to trim — dropping
        # ``actor`` would make the first cleared crossings in the system's life invisible to
        # every census already written, which is the failure of keeping a word and replacing
        # what fills it. Stamped here rather than accepted from ``journal_extra`` because
        # ``actor`` is a named parameter of this function: a caller cannot supply it twice.
        actor=actor,
        # The record of truth names the PROOF the clearance leaned on and the seal's date, so a
        # reader a year out can go and look at the same evidence the gate looked at rather than
        # taking "it was proven" on the record's word (Law 5 — the proof shares the address).
        proven_by=proven_by,
        proven_seal_date=proven["seal"]["date"],
        # WAS ``actor != boat_owner``; now "a per-operation grant was spent". The word is
        # kept and the distinction it draws is kept — direct standing vs a capability
        # minted for this one move — which is exactly what transitions.py renders as
        # "(delegated)" on the crossing's standing line. THE OTHER READING WAS CONSIDERED
        # AND MEASURED OUT: under the ruling a hand is never the owner (an intention
        # cannot act), so "delegated" could be argued to be universally true — but that
        # would make it a flag that never varies, render every crossing "(delegated)", and
        # tell a reader nothing. Recording the standing-vs-grant distinction under a
        # second name would be the honest third option; it is a change to what base
        # journals, which this voyage's bounds put out, so it is named and not taken.
        delegated=delegated,
        # The caller's own fields ride through untouched — ``ticket`` above all, which the
        # entry/exit/emission gates each demand and which this rung had no way to carry
        # until 2026-08-10. Spread LAST so a caller can enrich ``standing`` the same way a
        # bare ``emit`` caller can. It may NOT carry a witness field — see the refusal above.
        **journal_extra,
        **emit_kwargs,
    )


def clear(
    workflow_str: str,
    target: str,
    *,
    actor: str,
    boat_id: str,
    proven_by: str,
    grant: Grant | None = None,
    history_path: str | None = None,
    state_path: str | None = None,
    node_class_root=None,
    resources=None,
    lines: dict | None = None,
    now: float | None = None,
    **journal_extra,
) -> str:
    """The clearance gate — decide, and REMEMBER BEING ASKED. This is the public door.

    Everything about what is decided lives in ``_decide`` above; this rung adds exactly one
    thing, and it is the ticket clearance-leaves-a-trace: an attempt leaves a durable record
    whether it was granted or refused.

    WHY THE WRITER IS AT THE FRAME AND NOT AT THE RAISE SITES. Measured before building:
    fourteen refusal paths reach a caller of this door, and only SEVEN of them raise inside
    ``_decide``'s own text. The other seven are ``OwnerUnresolvable``, raised inside
    ``boat_owner_of`` — a function ``_decide`` calls, and one that is also called directly by
    readers who are not asking for clearance at all. A writer placed at each raise site would
    therefore have had to be threaded into a shared helper (recording clearance attempts that
    nobody made) or would have missed half the refusal surface while LOOKING complete — the
    hollow pass the ticket pre-names, wearing a plausible shape. Wrapping the frame makes the
    record's completeness structural: anything that leaves this function by raising is traced,
    including refusals nobody has thought of yet, and including ``IllegalTransition`` from the
    chokepoint, which the docstring above has always counted among the refusals.

    A MALFORMED CALL IS TRACED TOO, deliberately. If ``_decide`` raises ``TypeError`` because
    a required argument was never supplied, that is still a hand that asked this gate to move
    a boat and did not get it moved. Filtering exception types here would mean this gate
    deciding which failures are worth remembering — the collapse Law 7 forbids at a record of
    truth. The type rides in the record; a reader can filter, the writer may not.

    A GRANT IS RECORDED AS ITS OWN EVENT, not inferred from the absence of a refusal. The
    ticket's falsifier asks that "a grant must be distinguishable from a refusal in the
    record", and a store holding only refusals satisfies that only by arithmetic over a
    denominator it does not carry.

    THE SIGNATURE IS SPELLED OUT RATHER THAN FORWARDED AS ``**kwargs``, and the first
    version of this wrapper got that wrong. A ``**kwargs`` door still behaves correctly —
    ``_decide`` names ``proven_by``, so it can never fall through into ``journal_extra`` —
    but it makes the property INVISIBLE, and the proof's own witness tooth reads this
    signature to assert that ``proven_by`` is unsmugglable BY STRUCTURE. Hiding the contract
    behind a splat turned a structural guarantee into one you had to trace two frames to
    see; the tooth caught it on the first run. The two signatures are kept in step by a
    tooth of their own, not by care.
    """
    try:
        outcome = _decide(
            workflow_str, target,
            actor=actor, boat_id=boat_id, proven_by=proven_by, grant=grant,
            history_path=history_path, state_path=state_path,
            node_class_root=node_class_root, resources=resources, lines=lines, now=now,
            **journal_extra,
        )
    except BaseException as exc:
        # THE TRACE WRITE IS NOT SWALLOWED. If the queue cannot be written, that failure
        # propagates — chained onto the refusal it was recording, so a reader sees both the
        # answer the gate gave and the fact that it could not remember giving it. Swallowing
        # here would produce the one state this ticket exists to end: a refusal that happened
        # and left nothing, now with code that claims otherwise.
        _trace_attempt(REFUSED, workflow_str=workflow_str, target=target,
                       actor=actor, boat_id=boat_id, exc=exc)
        raise
    _trace_attempt(GRANTED, workflow_str=workflow_str, target=target,
                   actor=actor, boat_id=boat_id)
    return outcome
