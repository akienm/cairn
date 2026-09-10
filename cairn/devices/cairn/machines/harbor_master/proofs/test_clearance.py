"""Proof: the CLEARANCE gate (harbor_master child b) — the AUTHORITY rung of a transition.

The stone's claim: no boat's cursor moves without CLEARANCE — the owner's, or a delegate's
under a per-operation grant — and every refusal (unauthorized, unproven, illegal) leaves no
record, while every cleared move is recorded in the boat's own history. Teeth a hollow build
could not pass (mapped to the parent falsifier, tickets/harbor-master.json):

  - CLEARANCE IS REQUIRED (Law 6): the owner may move the boat; an actor who is neither the
    owner nor a grant-holder is REFUSED — and nothing is journaled. An ambient-advance build
    (anyone may move any boat) dies here.
  - CLEARANCE IS DELEGABLE, PER-OPERATION (Law 6): the owner mints a grant for ONE igor to
    make ONE move; the igor clears it. THE HOLLOW-KILLER: that same grant does NOT authorize
    a different target, a different boat, or a different actor — an ambient "the igor may
    advance anything" model passes the happy path and dies on this tooth.
  - AUTHORITY NEVER BUYS AN ILLEGAL MOVE (Law 4): even the OWNER, with a proven method,
    cannot clear a rules-illegal transition (a skip past a gate summons) — the wrapped
    chokepoint refuses it and nothing is written. Authority and rules are separate gates.
  - THE CODE THE MOVE SUMMONS MUST BE PROVEN, AND STILL BE THE CODE THAT WAS PROVEN (Law 8 +
    Law 3). The caller names a PROOF's address and the gate reads the seal beside it — there
    is no registry to populate (ripped out 2026-08-05). Three refusals: never sealed, sealed
    red, and THE HOLLOW-KILLER — sealed GREEN and then the component's code changed, so the
    VALIDATION's own horizon ('valid until the proof file or the code it proves changes') has
    closed. That last tooth is exactly what the in-memory registry could not do: it cached a
    bool with no description of what it was about, so it answered yes forever. A build that
    reads the verdict and skips the fingerprint dies there.
  - A GRANT LAPSES (Law 6): a grant that names the right operation and was minted by the right
    owner is STILL refused once its window closes. A build that treated the grant as a standing
    capability passes every operation-identity tooth above and dies here.
  - THE HOST CAN REFUSE (the fourth refusal): a move that is authorized, proven and legal is
    still refused when the harbor's resource line is crossed. THE HOLLOW-KILLERS: the gate
    receives a VERDICT and never a reading (a fake that raises on any door but ``ask`` proves
    it), and NOTHING COUNTS BUILDERS anywhere in the chain — the fake also raises on every
    census-shaped door, so a build that decided admission from a population dies here.

Runs bare. The proven-space fixtures are REAL: scratch component trees whose validation
trails are written by the real tester through the real single write-door, so a build that
faked a seal or a verdict dies before the teeth even start.
    python3 cairn/devices/cairn/machines/harbor_master/proofs/test_clearance.py     # exit 0 = green
"""

from __future__ import annotations

import contextlib
import io
import json
import os
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[6]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

# THE HARBOR'S END OF ``1accdc1781aa`` — clause (3), and only clause (3). The seam runs
# through three components and ``proven_by`` is read as one-or-many so the crossing can
# name all of them: the tester's end (clauses 1 and 4) is
# cairn/devices/tester/proofs/test_the_seal_announces_itself.py; codemother's end
# (clauses 2 and 5) is cairn/devices/codemother/proofs/test_codemother.py.
#
# ONE TOOTH IS NAMED, NOT SIX, because the coverage rung reads one tooth per clause and
# the clause has one load-bearing demand: that every lack is named IN ONE PASS. The tooth
# below is the one that measures that. Its five siblings measure the individual refusals
# the clause enumerates and stand beside it:
#   test_a_seal_whose_FINGERPRINT_HAS_MOVED_is_refused_at_PROVED
#   test_a_CODE_SEAM_WITH_NO_HOLLOW_READING_is_refused_the_same_as_an_absent_seal
#   test_a_HOLLOW_FILE_in_the_reading_is_refused_and_the_refusal_NAMES_THE_FILE
#   test_an_UNREADABLE_file_is_REFUSED_and_is_never_folded_into_hollow
#   test_a_CONCEPT_PIECE_is_never_asked_for_a_hollow_reading
#   test_a_REFUSAL_RAISES_A_TROUBLE_naming_the_boat_and_the_finding
PROVES = {
    "1accdc1781aa": {
        "3": "test_an_UNCOVERED_boat_is_REFUSED_at_PROVED_and_every_lack_is_named_in_one_pass",
    },
}

from cairn.tools.base.transitions import IllegalTransition
from cairn.tools.charter import projector
from cairn.devices.cairn.machines.harbor_master.clearance import (
    GRANT_TTL_SECONDS,
    HARBOR_LINES,
    GrantExpired,
    IntentionRetired,
    OwnerUnresolvable,
    Retirement,
    RetirementUnreadable,
    Riders,
    Unauthorized,
    Unproven,
    Unresourced,
    GRANTED,
    QUEUE_BLOCK,
    QUEUE_CONSUMER,
    REFUSED,
    boat_owner_of,
    clear,
    mint_grant,
    retirement_of,
    riders_of,
)


# ══════════════════════════════════════════════════════════════════════════════════════
# THE NAMES THIS BUILD ADDED ARE RESOLVED AT CALL TIME, NOT AT IMPORT TIME.
# ══════════════════════════════════════════════════════════════════════════════════════
# ``Uncovered`` and ``hollow_lacks`` did not exist in clearance before ticket 1accdc1781aa,
# and they were imported at module level like everything above. That is fine until the one
# instrument that must revert this build runs: ``cairn test --hollow`` checks out the
# pre-build clearance.py under a scratch worktree and re-runs these teeth, and a module-level
# import of a name the reverted file does not define kills the WHOLE MODULE before a single
# tooth prints. Measured 2026-09-09: the hollow run reported
#
#   UNRAN cairn/.../clearance.py [1 proof(s) printed no teeth at all: the import broke]
#   unreadable: ... the reversion broke the proof rather than failing a tooth, so nothing
#   here says whether a tooth checks this file
#
# — the reading this proof exists to make, unmade, on the file this proof is ABOUT. Resolving
# late turns that into a real reading: the reverted file still imports, the teeth still run,
# and the two that lean on the new names fail LOUDLY and specifically, which is precisely the
# signal the instrument is asking for. A proof that must survive its subject being taken away
# cannot bind its subject's newest names at import time.
def _built(name):
    """A name ticket 1accdc1781aa added to clearance, fetched now rather than at import."""
    from cairn.devices.cairn.machines.harbor_master import clearance as _c
    try:
        return getattr(_c, name)
    except AttributeError as exc:  # the hollow instrument's reversion, or a real regression
        raise AssertionError(
            f"clearance does not define {name!r} — under `cairn test --hollow` this IS the "
            f"reading (the reverted file lacks it, so this tooth is evidence about it); "
            f"at HEAD it is a regression: {exc}") from exc

from cairn.devices.cairn.machines.harbor_master import clearance as _clearance
from cairn.devices.cairn.machines.harbor_master import register as _register
from cairn.machines.learning_block.learning_block import trace_root, write_trace
from cairn.devices.tester.device import TesterDevice
from cairn.devices.tester.scratch import scratch_dir
from cairn.devices.tester.validation_store import persist_validation, record_hollow


# ══════════════════════════════════════════════════════════════════════════════════════
# THE CORPUS IS WHERE GIT SAYS IT IS — not where THIS CHECKOUT's parent happens to be.
# ══════════════════════════════════════════════════════════════════════════════════════
# ``clearance.COMMONS_ROOT`` and ``transitions._NODE_CLASSES`` both spell the commons as
# "the sibling of the checkout I am imported from". That is right in the live tree and
# wrong in every WORKTREE of it — and a worktree is exactly where ``cairn test --hollow``
# does all of its reverting, so the expression is wrong precisely where this proof most
# needs to run.
#
# MEASURED 2026-09-09, and it was worse than a red tooth: this module DIED AT IMPORT.
# ``_OWNER = boat_owner_of(_BOAT)`` runs at module level, found no
# /tmp/CairnCommons/tickets/boat-owner-is-read-not-stated.json, and raised
# OwnerUnresolvable before a single tooth ran. To the hollow verb that reads as "the
# declared tooth test_an_UNCOVERED_boat_is_REFUSED_at_PROVED_... is not green at HEAD",
# which refuses the WHOLE measurement of ticket 1accdc1781aa with HollowUnmeasurable — one
# unportable path hiding every reversion reading the ticket has.
#
# THE SAME CLASS the trouble proofs took on 2026-09-09 and the codemother proofs took the
# same day: ``git rev-parse --git-common-dir`` is the shared ``.git`` of the repo AND of
# every worktree of it, so its parent is the MAIN working tree from wherever this runs.
#     -> ticket a-proof-that-reaches-a-sibling-repo-by-relative-path-cannot-be-reproven-elsewhere
#
# THE CORRECTION IS CONDITIONAL AND ADDRESS-ONLY. In the live tree the default resolves and
# NOTHING is patched — so the ordinary run is byte-for-byte the run it always was, and this
# block cannot quietly become the thing the teeth are measuring. When it does fire it
# substitutes an ADDRESS and never a behaviour: the real ``boat_owner_of`` walks the real
# hops over the operator's real tickets and real charters, and the real ``load_class_def``
# reads the real code-seam definition. A stub of either would make these teeth pass by
# lowering the bar they exist to hold.
#
# IT MUST BE A WRAPPER, not a constant assignment: both roots are DEFAULT ARGUMENTS bound
# at def time (``boat_owner_of(..., commons_root=COMMONS_ROOT)``,
# ``load_class_def(..., root=_NODE_CLASSES)``), so rebinding the module constants would do
# nothing at all. And the predicate is "does the given root exist", not "did the caller
# pass one" — ``emit`` always passes its own default, which IS the broken expression.

def _main_tree() -> Path:
    """This repo's MAIN working tree, named the same from itself and from any worktree."""
    import subprocess
    common = subprocess.run(
        ["git", "-C", str(Path(__file__).resolve().parent),
         "rev-parse", "--path-format=absolute", "--git-common-dir"],
        capture_output=True, text=True)
    if common.returncode == 0 and common.stdout.strip():
        return Path(common.stdout.strip()).parent
    # NOT A SILENT FALLBACK: outside a git checkout there is no main tree to name, so the
    # checkout itself is the honest best effort and the caller below fails LOUDLY naming
    # the path it looked in — the behaviour that surfaced this bug in the first place.
    return _REPO_ROOT


def _correct_the_corpus_roots_if_this_is_a_worktree() -> None:
    from cairn.devices.cairn.machines.harbor_master import clearance as _c
    from cairn.tools.base import transitions as _t

    # THE PREDICATE IS "AM I THE MAIN TREE", NOT "DOES THE DEFAULT DIRECTORY EXIST", and
    # the difference is a measurement rather than a preference. The existence spelling was
    # written first and did not fire: a proof had leaked fixture tickets into
    # /tmp/CairnCommons/tickets on 2026-09-08, so from a worktree at /tmp/hw the derived
    # default WAS a directory — holding two fixture tickets and none of the operator's. The
    # correction stood down and the module died at import exactly as before, now pointing at
    # a folder that existed. Asking git which tree this is cannot be fooled that way, and it
    # is the same question the resolution itself is built on.
    if _REPO_ROOT.resolve() == _main_tree().resolve():
        return                                    # the live tree: change nothing
    tree = _main_tree()
    commons = tree.parent / "CairnCommons"
    real_owner, real_load = _c.boat_owner_of, _t.load_class_def

    def _rooted_owner_of(boat_id, **kw):
        kw.setdefault("tickets_dir", str(commons / "tickets"))
        kw.setdefault("cairn_root", str(tree))
        kw.setdefault("commons_root", str(commons))
        return real_owner(boat_id, **kw)

    def _rooted_load(node_class, *, root=None):
        if root is None or not Path(root).is_dir():
            root = commons / "node_classes"
        return real_load(node_class, root=root)

    _c.boat_owner_of = _rooted_owner_of
    _t.load_class_def = _rooted_load
    # AND THE CHOKEPOINT'S OWN CAST-TICKET ROOT, which is a THIRD spelling of the same
    # sibling expression (``transitions._TICKETS``). This one is read at call time rather
    # than bound as a default, so the constant IS the seam — no wrapper needed. Found the
    # way the other two were: the crossing got past the owner rung and then refused
    # "named ticket 'an-intention-declares-its-gated-hands' is not cast — no file ... in
    # /tmp/CairnCommons/tickets". Three readers, three spellings, one wrong assumption.
    _t._TICKETS = commons / "tickets"
    # AND THIS MODULE'S OWN BINDING, which is a SEPARATE NAME and was the half that bit.
    # ``from ...clearance import boat_owner_of`` at the top copied the function object into
    # these globals, so patching the clearance module alone leaves ``_OWNER =
    # boat_owner_of(_BOAT)`` forty lines below still calling the unrooted original — and
    # that line is the one that died at import. ``clear()`` resolves its own call through
    # the clearance module, so BOTH bindings are needed and neither is redundant.
    globals()["boat_owner_of"] = _rooted_owner_of


_correct_the_corpus_roots_if_this_is_a_worktree()


# ══════════════════════════════════════════════════════════════════════════════════════
# THE FIXTURE BOATS RAISE THEIR TROUBLES INTO A SANDBOX, NOT INTO THE OPERATOR'S INBOX.
# ══════════════════════════════════════════════════════════════════════════════════════
# ``_raise_uncovered_trouble`` takes a ``device`` and, when nobody hands it one, builds
# ``ModuleRaiser("harbor_master")`` against the LIVE world. Two teeth below inject their
# own device and assert against it; every OTHER tooth that walks a refusal path leaves the
# default in place, so its emission landed in the real ~/.cairn/logs/harbor_master trail and
# the trouble device's next beat folded it into CairnCommons/troubles/.
#
# MEASURED 2026-09-09, after running this proof six times in one afternoon: EIGHT new files
# in the operator's live trouble store, named for boats that exist only in this file —
# ``boat-crossed-to-proved-uncovered-hollowf0000a``, ``-nohollow000a``, ``-lowercase00a``,
# ``-moved00000a``, ``-uncover0000a`` — one of them with ``count: 6``, one occurrence per
# run, each pointing at a ``/tmp/clearance-proven-space-*`` that no longer exists. Those sit
# in the session-open banner as LIVE TROUBLE alongside real ones. Law 7 cuts BOTH ways: a
# record of truth may never collapse an error, and it may never be fed a manufactured one.
#
# ``set_diagnostic_roots`` is the seam built for exactly this (its own docstring: "a proof
# that only wants isolation should reach for this — it leaves the mechanism under test
# intact"). NOTHING IS SILENCED: the raiser still runs, still writes its emission, still
# returns its record — it writes into a temp world the drain never reads. A tooth that wants
# to ASSERT on a raise still injects its own device and is untouched by this.
import cairn.tools.base.diagnostic as _diagnostic

# THROUGH THE DOOR — scratch_dir registers its own removal, which is why this reaches for it
# rather than for mkdtemp+atexit (what stood here until 2026-09-09 and was caught by
# test_scratch.py's corpus tooth; ticket dd8ad9702b49 fixed it in passing). Line 320 in this
# same file was already going through the door: two temp worlds, one of them hand-rolled.
_TROUBLE_SANDBOX = scratch_dir("clearance-proof-trouble-world-")
_LIVE_MODULE_RAISER = _diagnostic.ModuleRaiser


class _SandboxedModuleRaiser(_LIVE_MODULE_RAISER):
    """A ModuleRaiser whose default world is this proof's temp tree, not the operator's."""

    def __init__(self, component, instance=0, *, roots=None):
        super().__init__(component, instance, roots=roots or {
            "repo": _TROUBLE_SANDBOX,
            "commons": _TROUBLE_SANDBOX,
            "instance": _TROUBLE_SANDBOX,
        })


_diagnostic.ModuleRaiser = _SandboxedModuleRaiser

# The real code-seam@v1 string, cursor at BUILDME. Legal forward from here: PROVEME (the next
# summons). Illegal: LEARNME (a skip PAST the PROVEME gate). Validated against the REAL
# node-class table (CairnCommons/node_classes/code-seam.json) — non-hollow, like transitions.
_WF = "code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME -> LEARNME -> PROVED"

# THE BOATS ARE REAL NOW, and they have to be. Since 2026-08-10 (ticket
# boat-owner-is-read-not-stated) the gate READS a boat's owner off disk rather than taking
# it as an argument, and it accepts no root injection — a ``tickets_dir=`` parameter would
# hand the caller back the choice of what the gate reads, which is the ticket's own
# falsifier clause (1) wearing a coat. So a proof that wants a cleared crossing must name a
# boat that exists.
#
# WHAT IS ASSERTED ABOUT THEM IS AN INVARIANT, NEVER A SNAPSHOT. ``_OWNER`` is not the
# string 'CC' written down here; it is whatever hand these boats' owning intention admits,
# read the same way the gate reads it. If that list changes tomorrow these teeth still
# mean what they say — where a hard-coded 'CC' would go green for the wrong reason on the
# day somebody edits the charter.
_BOAT = "boat-owner-is-read-not-stated"
_OTHER_BOAT = "an-intention-declares-its-gated-hands"
_OWNER = boat_owner_of(_BOAT).hands[0]
_IGOR = "igor_7"
assert _IGOR not in boat_owner_of(_BOAT).hands, \
    "the unauthorized actor these teeth use must actually be unauthorized"

_FIXTURES = _REPO_ROOT / "cairn" / "devices" / "tester" / "proofs" / "fixtures"
_GREEN_FIXTURE = _FIXTURES / "green_proof.py"
_RED_FIXTURE = _FIXTURES / "red_proof.py"

# Scratch components for the proven-space teeth. NOT hand-written seals: each is a real
# component tree whose validation trail is produced by the REAL tester and landed through the
# REAL single write-door, so a build that faked either dies here. Swept at process exit by
# cairn.devices.tester.scratch — the corpus's own door for this, and test_scratch.py enforces its use.
_SCRATCH = scratch_dir("clearance-proven-space-")


def _component(name: str, fixture: Path) -> str:
    """Build a component tree ``<scratch>/<name>/proofs/test_<name>.py`` and return the proof."""
    proofs = Path(_SCRATCH) / name / "proofs"
    proofs.mkdir(parents=True, exist_ok=True)
    proof = proofs / f"test_{name}.py"
    proof.write_text(fixture.read_text(), encoding="utf-8")
    return str(proof)


def _seal(proof: str) -> dict:
    """Run it under the real tester and append the verdict through the real store's write-door."""
    validation = TesterDevice().run_proof(proof, sink="none")
    persist_validation(validation, proof_path=proof)
    return validation


# Sealed GREEN, fingerprint current — the code a move may be cleared onto.
_PROVEN = _component("proven", _GREEN_FIXTURE)
_seal(_PROVEN)

# Never sealed at all: a component with a proof and no trail beside it.
_UNSEALED = _component("unsealed", _GREEN_FIXTURE)

# Sealed, and the tester said RED. It was measured, and it failed.
_REDDED = _component("redded", _RED_FIXTURE)
_seal(_REDDED)


def _paths(tmp: str):
    return str(Path(tmp) / "history.json"), str(Path(tmp) / "state.json")


# ── the gate's queue (ticket clearance-leaves-a-trace) ───────────────────────────────────
#
# THE LIVE STORE IS NEVER TOUCHED BY THIS PROOF, and that is not tidiness — it is the
# difference between the queue being evidence and being noise. harbor_master's own probe
# (probes/clearance_actually_gates.py) reads this store to answer "has the gate ever
# actually refused a real crossing?", and its header states the rule this block enforces:
# "A COUNTED FIXTURE REFUSAL WOULD BE A LIE... a refusal manufactured by its own proof is
# not evidence that the gate ever stood in a real crossing's way." Every tooth below
# manufactures refusals by the dozen. So the root is redirected for the whole process at
# import — BEFORE any test can call ``clear()`` — and the last tooth asserts the live file
# came out of the run byte-identical. Same discipline, and the same pairing of injection
# with a byte-identity tooth, as skills/sorted/proofs/test_sorted_door.py.
_TRACE_ENV = "CAIRN_LB_TRACE_ROOT"
_LIVE_QUEUE = trace_root() / f"{QUEUE_BLOCK}.jsonl"
_LIVE_BEFORE = _LIVE_QUEUE.read_bytes() if _LIVE_QUEUE.exists() else None
os.environ[_TRACE_ENV] = str(Path(_SCRATCH) / "traces")


@contextlib.contextmanager
def _queue(tmp: str):
    """Point the trace root at a fresh directory for the duration, and yield the queue file
    this gate writes to. Per-tooth isolation so a count means what it says: a shared file
    would let one tooth pass on another tooth's records, which is the check going green for
    the wrong reason."""
    root = Path(tmp) / "traces"
    prior = os.environ[_TRACE_ENV]
    os.environ[_TRACE_ENV] = str(root)
    try:
        yield root / f"{QUEUE_BLOCK}.jsonl"
    finally:
        os.environ[_TRACE_ENV] = prior


def _records(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _attempt(**overrides):
    """Ask the gate for the standard legal move, with any argument overridden. Returns the
    exception it refused with, or None if it cleared."""
    kw = dict(actor=_OWNER, boat_id=_BOAT, proven_by=_PROVEN)
    kw.update(overrides)
    target = kw.pop("target_state", "PROVEME")
    try:
        clear(_WF, target, **kw)
    except Exception as exc:  # noqa: BLE001 — the refusal IS the measurement here
        return exc
    return None


def test_a_refused_attempt_leaves_a_durable_record_carrying_its_reason():
    """THE TICKET'S SUBJECT, and its FIRST pre-named hollow pass: "a hollow build passes by
    logging only grants (the present behaviour)". Before this voyage a refusal raised bare
    and the attempt vanished with the stack frame."""
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        with _queue(tmp) as q:
            exc = _attempt(actor=_IGOR, history_path=hp, state_path=sp)
        assert isinstance(exc, Unauthorized), "the setup must actually be refused"
        recs = _records(q)
        assert len(recs) == 1, f"one attempt, one record — got {len(recs)}"
        rec = recs[0]
        assert rec["event"] == REFUSED, "the record must say it was a refusal"
        assert rec["block"] == QUEUE_BLOCK and rec["consumer"] == QUEUE_CONSUMER
        # WHEN — stamped by the store, not by the gate, so it cannot be forged upstream.
        datetime.fromisoformat(rec["when"])
        d = rec["data"]
        assert d["actor"] == _IGOR, "who asked"
        assert d["boat"] == _BOAT, "which voyage"
        assert d["target"] == "PROVEME", "for what transition"
        assert d["workflow"] == _WF, "...and from where"
        # THE SECOND PRE-NAMED HOLLOW PASS: "writing a refusal with no reason, which is loud
        # without being useful". A reason that is merely the exception's class name repeated
        # is that failure wearing a longer coat, so the message must carry particulars.
        assert "reason_type" in d and "reason" in d, \
            f"a refusal with no reason is loud without being useful — the record carries {sorted(d)}"
        assert d["reason_type"] == "Unauthorized", "the reason's CLASS, so refusals group"
        assert _IGOR in d["reason"] and len(d["reason"]) > 40, \
            "the reason must name the particulars, not restate the class"
        # And the refusal is still not a CROSSING: nothing was journaled.
        assert not Path(hp).exists(), "a refused move must still leave no crossing record"


def test_a_grant_and_a_refusal_are_one_field_apart_in_one_store():
    """"A grant must be distinguishable from a refusal IN the record." A store holding only
    refusals satisfies that only by a reader's arithmetic over a denominator it does not
    carry — which is the reading the falsifier rules out, and which would also make the
    refusal RATE unmeasurable forever."""
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        with _queue(tmp) as q:
            assert _attempt(history_path=hp, state_path=sp) is None, "the owner's move clears"
            assert _attempt(actor=_IGOR, history_path=hp, state_path=sp) is not None
        recs = _records(q)
        assert len(recs) == 2, "both halves of the gate's answer are recorded, in ONE store"
        assert [r["event"] for r in recs] == [GRANTED, REFUSED], \
            "the distinction is a FIELD, in order of asking — never inferred from absence"
        granted, refused = recs
        assert "reason" not in granted["data"] and "reason_type" not in granted["data"], \
            "a grant has nothing to explain; a reason on it would make the field meaningless"
        assert granted["data"]["actor"] == _OWNER and refused["data"]["actor"] == _IGOR


def test_every_refusal_CLASS_reaches_the_queue_including_the_ones_raised_outside_the_gate():
    """THE TOOTH A PER-RAISE-SITE BUILD FAILS. Half this door's refusal paths do not raise
    in the decision function's own text: every ``OwnerUnresolvable`` comes out of
    ``boat_owner_of``, a shared helper the gate CALLS. A writer sprinkled at the raise sites
    inside the gate would look complete and silently miss them — so the record's coverage is
    asserted over the whole refusal vocabulary, including the class raised elsewhere and the
    one raised by the chokepoint underneath."""
    lapsed = mint_grant(minted_by=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME",
                        now=1000.0)
    cases = {
        "Unauthorized": dict(actor=_IGOR),                         # raised in the gate
        "OwnerUnresolvable": dict(boat_id="no-such-boat-exists"),  # raised in boat_owner_of
        "Unproven": dict(proven_by=_UNSEALED),                     # raised in the gate
        "GrantExpired": dict(actor=_IGOR, grant=lapsed,            # the subclass, distinct
                             now=1000.0 + GRANT_TTL_SECONDS + 0.1),
        "Unresourced": dict(resources=_ResourceOwner(crossed=True)),   # raised in the gate
        "IllegalTransition": dict(target_state="LEARNME"),         # raised UNDER the gate, in emit
    }
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        with _queue(tmp) as q:
            for name, kw in cases.items():
                exc = _attempt(history_path=hp, state_path=sp, **kw)
                assert exc is not None and type(exc).__name__ == name, \
                    f"the {name} setup refused with {type(exc).__name__} instead"
        recs = _records(q)
        assert all(r["event"] == REFUSED for r in recs), "every one of these was a refusal"
        assert {r["data"]["reason_type"] for r in recs} == set(cases), \
            "every refusal class must reach the queue — a missing one is a blind spot"
        assert all(r["data"].get("reason") for r in recs), "and every one carries its reason"


def test_the_record_outlives_the_reaper_that_would_have_eaten_a_debug_one():
    """THE CONSUMER CHOICE, MEASURED RATHER THAN ARGUED. ``write_trace`` sweeps expired
    ``debug`` records out of a block on every subsequent write. A Law 7 record of truth may
    not evaporate at 30 days, so the queue is written as ``training`` — and this tooth proves
    the choice bites by aging the store past the TTL and watching a debug record die in the
    same file the clearance record survives in. A build that had chosen ``debug`` for the
    queue would pass every other tooth here and fail this one."""
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        with _queue(tmp) as q:
            _attempt(actor=_IGOR, history_path=hp, state_path=sp)
            write_trace(QUEUE_BLOCK, "control", "debug", {"note": "should not survive"})
            assert len(_records(q)) == 2, "both records are in the file to begin with"
            # A LATER WRITE IS THE REAPER'S ONLY CLOCK — never a daemon. Fire one from far
            # enough in the future that anything with a TTL has expired.
            write_trace(QUEUE_BLOCK, "control", "training", {"note": "the sweeping write"},
                        now=datetime.now(timezone.utc) + timedelta(days=400))
        events = [r["event"] for r in _records(q)]
        assert events.count("control") == 1, "the debug record must have been swept — else " \
                                             "this tooth cannot tell training from debug"
        assert REFUSED in events, "the clearance record must still be there, 400 days on"


def test_the_public_door_and_the_decision_it_wraps_have_one_signature():
    """The gate is now two functions — ``clear`` records the attempt, ``_decide`` makes it —
    and the door's signature is the component's contract: the witness tooth above reads it
    to assert that ``proven_by`` is unsmugglable by structure, and callers read it to know
    what may be passed. A parameter added to the decision and forgotten on the door would be
    a TypeError at some caller months from now; a parameter added to the door and dropped in
    the forward would be silently ignored, which is worse. Asserted rather than remembered —
    the first cut of the wrapper took ``**kwargs`` and quietly lost the whole named set."""
    import inspect as _inspect
    from cairn.devices.cairn.machines.harbor_master.clearance import _decide

    door = _inspect.signature(clear).parameters
    decision = _inspect.signature(_decide).parameters
    assert list(door) == list(decision), \
        f"the door and the decision have drifted apart: {set(door) ^ set(decision)}"
    for name, p in decision.items():
        assert door[name].kind is p.kind and door[name].default is p.default, \
            f"parameter {name!r} differs between the door and the decision"


def test_the_refusals_are_readable_afterwards_by_the_probe_that_asked_for_them():
    """"THAT RECORD MUST BE READABLE AFTERWARDS" — the ticket's own wording, and the half
    that keeps this build from being ceremony. The reader is not a fresh one written to
    satisfy this tooth: it is ``clearance_actually_gates.survey_the_refusals``, the probe
    that filed the IOU for this store and hard-coded ``refusals_recorded: 0`` beside a note
    naming this ticket as the build that would make the number real. So the tooth measures
    the thing that asked for it — which also means a writer whose event names or consumer
    ever drift away from the reader's dies here rather than reporting a quiet zero."""
    from cairn.devices.cairn.machines.harbor_master.probes.clearance_actually_gates import survey_the_refusals

    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        with _queue(tmp) as q:
            _attempt(history_path=hp, state_path=sp)                    # one grant
            _attempt(actor=_IGOR, history_path=hp, state_path=sp)       # two refusals,
            _attempt(boat_id="no-such-boat-exists", history_path=hp, state_path=sp)  # two classes
            q.write_text(q.read_text(encoding="utf-8") + "{not json\n", encoding="utf-8")
            s = survey_the_refusals()
    assert s["asked"] == 3 and s["granted"] == 1 and s["refused"] == 2, \
        f"the reader must count what the gate answered — got {s}"
    assert s["by_reason"] == {"Unauthorized": 1, "OwnerUnresolvable": 1}, \
        "and group refusals by class, which is what makes the store worth querying"
    # A LINE THE READER CANNOT PARSE IS NOT EVIDENCE IN EITHER DIRECTION. Counting it as a
    # refusal invents a no the gate never said; counting it as an attempt inflates the
    # denominator the probe's vacuity clause reads.
    assert s["unreadable_lines"] == 1 and s["asked"] == 3, "a bad line is skipped, not counted"
    assert s["recent_refusals"][0]["reason"], "the refusals ride back verbatim, reasons and all"


def test_this_proof_never_wrote_to_the_live_queue():
    """The injection above is only worth as much as this assertion. harbor_master's probe
    counts REAL refusals off the live store; a fixture refusal landing there would not be a
    messy file, it would be manufactured evidence that the gate once stood in a real
    crossing's way."""
    now = _LIVE_QUEUE.read_bytes() if _LIVE_QUEUE.exists() else None
    assert now == _LIVE_BEFORE, \
        f"{_LIVE_QUEUE} changed during this proof run — fixture refusals reached the live queue"


def test_the_owner_may_clear_a_legal_move_and_it_is_recorded():
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_OWNER, boat_id=_BOAT,
            proven_by=_PROVEN, history_path=hp, state_path=sp,
        )
        assert "[PROVEME:waiting]" in new, "the cursor must have moved to PROVEME"
        history = projector.read_history(hp)
        assert len(history) == 1, "exactly one crossing recorded"
        rec = history[0]
        assert rec["from"] == "BUILDME" and rec["to"] == "PROVEME"
        assert rec["cleared_by"] == _OWNER, "the record must name WHO cleared it (Law 7)"
        assert rec["delegated"] is False, "the owner acting directly is not a delegation"


def test_an_unauthorized_actor_is_refused_and_nothing_is_written():
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_IGOR, boat_id=_BOAT, # igor, no grant
                proven_by=_PROVEN, history_path=hp, state_path=sp,
            )
        except Unauthorized:
            assert not Path(hp).exists(), "a refused move must leave NO record (no ambient advance)"
            return
        raise AssertionError("an ungranted non-owner must be refused — ambient advance is the failure")


def test_clearance_is_delegable_per_operation():
    grant = mint_grant(minted_by=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME")
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_IGOR, boat_id=_BOAT,
            proven_by=_PROVEN, grant=grant, history_path=hp, state_path=sp,
        )
        assert "[PROVEME:waiting]" in new
        rec = projector.read_history(hp)[0]
        assert rec["cleared_by"] == _IGOR and rec["delegated"] is True, "a delegated crossing is recorded as such"


def test_a_grant_is_non_ambient_it_does_not_authorize_other_operations():
    # THE HOLLOW-KILLER. A grant for (this boat, PROVEME, this igor) must NOT authorize a
    # different target, a different boat, or a different actor. An ambient authority model
    # (a grant that lets the igor do anything) passes every happy path and dies right here.
    grant = mint_grant(minted_by=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME")
    other_actor = "igor_9"

    def _refused(**overrides):
        kw = dict(actor=_IGOR, boat_id=_BOAT, proven_by=_PROVEN, grant=grant)
        kw.update(overrides)
        try:
            clear(_WF, kw.pop("target_state", "PROVEME"), **kw)
        except Unauthorized:
            return True
        return False

    # wrong target: the grant names PROVEME, try to clear a back-edge to TICKETME under it
    assert _refused(target_state="TICKETME"), "a grant for PROVEME must not authorize a different target"
    # wrong boat: same grant, a different boat_id
    # A REAL other boat, because the gate now reads one: an id with no ticket behind it
    # would raise OwnerUnresolvable and this tooth would be passing on the wrong refusal.
    assert _refused(boat_id=_OTHER_BOAT), "a grant for one boat must not authorize another"
    # wrong actor: the grant names igor_7, igor_9 tries to use it
    assert _refused(actor=other_actor), "a grant to one actor must not authorize another"


def test_even_the_owner_cannot_clear_an_illegal_move():
    # Authority never overrides the base-class rules (Law 4). LEARNME is a skip PAST the
    # PROVEME gate — illegal — and the owner's authority does not buy it.
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "LEARNME",
                actor=_OWNER, boat_id=_BOAT,
                proven_by=_PROVEN, history_path=hp, state_path=sp,
            )
        except IllegalTransition:
            assert not Path(hp).exists(), "an illegal move, even by the owner, writes no record"
            return
        raise AssertionError("a rules-illegal move must be refused regardless of authority (Law 4)")


def _refused_for_proven_space(proven_by: str) -> str:
    """Clear an otherwise-perfect move onto ``proven_by``; return the refusal text. Asserts the
    refusal wrote nothing — a move turned away at Law 8 leaves no more record than one turned
    away at Law 6."""
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id=_BOAT,
                proven_by=proven_by, history_path=hp, state_path=sp,
            )
        except Unproven as exc:
            assert not Path(hp).exists(), "a move refused for want of proven-space writes no record"
            return str(exc)
        raise AssertionError(
            f"clearing onto {proven_by} must be refused — the harbor clears only onto proven "
            f"code (Law 8)")


def test_clearing_onto_code_that_was_never_sealed_is_refused():
    # Law 8, the plainest way in: nobody ever ran this proof, so proven-space has not spoken
    # about this code. Silence is not a pass.
    why = _refused_for_proven_space(_UNSEALED)
    assert "no VALIDATION has ever sealed" in why, f"the refusal must say WHICH lack it is: {why}"


def test_clearing_onto_code_whose_proof_went_red_is_refused():
    # Proven-space is the TESTER's, not a label anyone can claim: this component's proof was
    # actually run and it actually failed, and the seal beside it says so.
    why = _refused_for_proven_space(_REDDED)
    assert "did not pass" in why, f"the refusal must name the red verdict it read: {why}"


def test_a_green_seal_whose_code_has_moved_underneath_it_is_refused():
    # THE HOLLOW-KILLER FOR THIS STONE, and the whole reason the registry went (2026-08-05).
    # Every VALIDATION promises a horizon — "valid until the proof file or the code it proves
    # changes" — and until today nothing checked it. An in-memory registry CANNOT: it cached a
    # bool at wiring time with no description of what it was about, so it kept answering yes
    # forever. Here the seal is real, green, and freshly written by the real tester; the only
    # thing that happens is that the component's code changes afterwards. A build that reads
    # the verdict and skips the fingerprint passes every other tooth in this file and dies here.
    drifting = _component("drifting", _GREEN_FIXTURE)
    _seal(drifting)

    # Sanity: before anything moves, this same code clears. Without this the tooth below could
    # pass because `drifting` was never clearable in the first place.
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        assert "[PROVEME:waiting]" in clear(
            _WF, "PROVEME",
            actor=_OWNER, boat_id=_BOAT,
            proven_by=drifting, history_path=hp, state_path=sp,
        ), "a freshly-sealed green component must clear before its code moves"

    # Now the code moves. Not the proof — a sibling module, which is the likelier drift by far
    # and the one a proof-only hash would miss entirely.
    (Path(drifting).parent.parent / "worker.py").write_text(
        "# the code the proof proves, edited after the seal\n", encoding="utf-8")

    why = _refused_for_proven_space(drifting)
    assert "HORIZON HAS CLOSED" in why, f"the refusal must name the expiry, not a vaguer lack: {why}"
    assert "fingerprint" in why, f"and must say what moved: {why}"


def test_the_record_names_the_proof_the_clearance_leaned_on():
    # Law 5: the crossing and its evidence share an address. A record that said only "proven"
    # would make a reader take the gate's word for it a year later; this one hands over the
    # proof path and the seal's date, so the same evidence can be re-read.
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        clear(
            _WF, "PROVEME",
            actor=_OWNER, boat_id=_BOAT,
            proven_by=_PROVEN, history_path=hp, state_path=sp,
        )
        rec = projector.read_history(hp)[0]
        assert rec["proven_by"] == _PROVEN, "the record must name the proof that backed the clearance"
        assert rec["proven_seal_date"], "and the date of the seal it read, so the trail entry is findable"


class _ResourceOwner:
    """A stand-in for system_rackmount's may-I door, built to catch a gate reaching for more
    than a verdict. It answers ``ask`` with a fixed verdict and RAISES on every other shape a
    hollow build might reach for — the raw reading, and any census of who is running. Those
    raises are the teeth: they are the two designs this one is not."""

    def __init__(self, crossed: bool) -> None:
        self._crossed = crossed
        self.asked: list[tuple] = []

    def ask(self, name: str, value) -> bool:
        self.asked.append((name, value))
        return self._crossed

    def _forbidden(self, *_a, **_k):
        raise AssertionError(
            "the gate reached past the verdict — it must never pull a reading, and it must "
            "never count builders (admission is decided from pressure, not population)"
        )

    reading = _reading = state = _forbidden          # the raw number: not this gate's business
    builders = count = active_builders = _forbidden  # the census that would make this a manager


def test_a_lapsed_grant_is_refused_and_nothing_is_written():
    # The window is part of the capability. This grant names exactly the right operation and was
    # minted by the right owner — the only thing wrong with it is that it is old.
    grant = mint_grant(minted_by=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME", now=1000.0)
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_IGOR, boat_id=_BOAT,
                proven_by=_PROVEN, grant=grant,
                now=1000.0 + GRANT_TTL_SECONDS + 0.1,   # spent just past the window
                history_path=hp, state_path=sp,
            )
        except GrantExpired:
            assert not Path(hp).exists(), "a lapsed grant writes no record — it authorizes nothing"
            return
        raise AssertionError("a grant spent after its window must be refused (Law 6)")


def test_the_same_grant_inside_its_window_still_clears():
    # The other half of the tooth above: the expiry must refuse the STALE, not the DELEGATED.
    # A build that broke delegation outright would pass the lapse test and die right here.
    grant = mint_grant(minted_by=_OWNER, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME", now=1000.0)
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_IGOR, boat_id=_BOAT,
            proven_by=_PROVEN, grant=grant,
            now=1000.0 + GRANT_TTL_SECONDS - 0.1,       # spent just inside it
            history_path=hp, state_path=sp,
        )
        assert "[PROVEME:waiting]" in new, "a grant inside its window must still clear the move"


def test_a_crossed_resource_line_refuses_an_otherwise_perfect_move():
    # THE FOURTH REFUSAL. Owner acting directly, proven method, legal target — every other gate
    # is wide open, and the host still says no.
    host = _ResourceOwner(crossed=True)
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id=_BOAT,
                proven_by=_PROVEN, resources=host,
                history_path=hp, state_path=sp,
            )
        except Unresourced:
            assert not Path(hp).exists(), "a move refused for want of room writes no record"
            assert host.asked, "the gate must actually ask the resource owner, not assume"
            assert host.asked[0][0] in HARBOR_LINES, "it asks by ADVERTISED MENU NAME, not method"
            return
        raise AssertionError("a crossed resource line must refuse the move — the fourth refusal")


def test_the_gate_asks_for_a_verdict_and_never_counts_anything():
    # THE HOLLOW-KILLER for this stone. _ResourceOwner raises on every door but `ask` — on the
    # raw reading (which would export the metric's semantics into the harbor, Law 6) and on
    # every census shape (which would make this a manager). A build that reached for either
    # dies here even though the happy path below is identical.
    host = _ResourceOwner(crossed=False)
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        new = clear(
            _WF, "PROVEME",
            actor=_OWNER, boat_id=_BOAT,
            proven_by=_PROVEN, resources=host,
            history_path=hp, state_path=sp,
        )
        assert "[PROVEME:waiting]" in new, "room on the host → the move clears"
        assert host.asked == [(name, value) for name, value in HARBOR_LINES.items()], (
            "every line the harbor holds must be put to the resource owner — one unasked line "
            "is a gate that does not gate"
        )
        for name, value in host.asked:
            assert isinstance(value, (int, float)), "the harbor sends its LINE, a number it owns"
        assert projector.read_history(hp)[0]["to"] == "PROVEME"


# ---- THE GATE BECOMES CALLABLE, AND STAYS THE ONLY HAND THAT STAMPS ----------------
# Ticket ``emit-refuses-an-uncleared-crossing`` (2026-08-10). The build's decisive finding
# was not a discipline failure: ``clear`` had been STRUCTURALLY UNCALLABLE for every gated
# crossing since 2026-07-29, when ``a-voyage-names-its-ticket`` landed the ticket demand.
# Three gates inside ``emit`` read ``journal_extra["ticket"]``; ``clear`` accepted no
# ``**journal_extra``, so a caller doing everything right was still refused with
# ``TicketRequiredRed``. A year of ambient crossings had physics pointing the wrong way,
# and nothing said so because nobody was calling it to find out.
#
# The pass-through is what makes the gate reachable. The refusal below is what keeps it
# worth passing through: the four witness fields are written BY this gate, never TO it.


def test_a_gated_crossing_can_actually_be_cleared_and_the_ticket_rides():
    """THE REACHABILITY TOOTH — this is the row that was impossible before this stone.
    A crossing whose downstream gate demands a ticket now clears, because ``clear``
    forwards ``**journal_extra`` to ``emit``. Revert the pass-through and this refuses
    with ``TicketRequiredRed``, which is exactly the state the corpus was in: every
    gated crossing routed around the harbor because going through it could not work."""
    # THE FIXTURE TICKETS DIR IS GONE, and its removal is part of the same settlement:
    # this test used to fabricate a ``widget.json`` and monkeypatch ``_t._TICKETS`` at it,
    # which was safe only while nothing read the ticket's CONTENTS. The gate does now, so
    # the boat is real and the two halves of the crossing name the same voyage — which is
    # what the binding tooth below refuses to let drift apart.
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        at_learn = ("code-seam@v1: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
                    "[LEARNME] -> PROVED")
        # ``_OTHER_BOAT`` RATHER THAN ``_BOAT``, and the reason is worth a line because it
        # bit on the first run: this crossing goes into PROVED, so it meets the exit gate,
        # which refuses a ticket whose chart claim has no verdict yet. Pointing it at the
        # voyage that is running this very proof makes a circle — the proof cannot pass
        # until the verdict is written, and the verdict cannot be written until the proof
        # passes. The gate was right and the fixture was wrong.
        #
        # ISOLATED BERTHS: skeleton chart chains (the prebuild's delegation markers) now
        # claim every BUILDME ticket in live instance-space, so the exit gate would see a
        # chart claim with no verdict. The test is about the clearance mechanism, not the
        # chart gate — an empty berths root lets it pass without fabricating a verdict.
        #
        # AND THE COVERAGE RUNG IS SATISFIED RATHER THAN ROUTED AROUND (2026-09-09, ticket
        # 1accdc1781aa). This crossing goes into PROVED, so it now also meets the rung that
        # asks whether the named proof COVERS this boat — and `_PROVEN` is a bare green
        # fixture that declares nothing about anything. The honest fix is to give this
        # crossing real coverage, not to point the tooth at a lesser target: the claim here
        # is that a gated crossing can ACTUALLY be cleared, and a crossing that dodges one
        # of the gates is not the thing being claimed. The owner read is substituted the
        # same way the retirement teeth substitute it, because the gate takes no root
        # injection and the boat's real ticket carries no crossings.
        _covering = _covering_proof("gated-crossing-rides", _OTHER_BOAT)
        _seal(_covering)
        assert record_hollow(_covering, _OTHER_BOAT, {"thing.py": [_COVERED_TOOTH]}) is True
        import cairn.machines.build_inspector.inspector as _insp
        _saved = _insp._CHART_BERTHS
        _insp._CHART_BERTHS = Path(tmp) / "no-chart-berths"
        try:
            # AND THE CROSSING RECORD IS STOOD UP TOO (2026-09-10). The coverage rung used to
            # read this boat's proofs off the substituted ticket dict; since the crossings
            # migration it derives them from the journals, and this boat is REAL — its live
            # journal names the real ``test_clearance.py``, whose fingerprint moves every time
            # this file is edited. Reading the live record here would make the tooth red on
            # its own author. The fixture world is the same substitution ``_owner_is`` already
            # makes, one read further down.
            with _owner_is(_covered_owner(_OTHER_BOAT, _covering)), _fixture_journals():
                new = clear(
                    at_learn, "PROVED",
                    actor=_OWNER, boat_id=_OTHER_BOAT,
                    proven_by=_covering, history_path=hp, state_path=sp,
                    ticket=_OTHER_BOAT,
                )
            assert "[PROVED]" in new, new
            rec = projector.read_history(hp)[0]
            assert rec["ticket"] == _OTHER_BOAT, \
                f"the ticket must ride through to the record the gates read: {rec}"
            assert rec["cleared_by"] == _OWNER and rec["proven_by"] == _covering, rec
            assert "re-read at the door" in rec.get("clearance_gate", ""), (
                "and the chokepoint's own sixth seat must have re-read the seal — a crossing "
                f"through this gate satisfies that gate rather than being waived past it: {rec}")
        finally:
            _insp._CHART_BERTHS = _saved


def test_a_caller_may_not_hand_this_gate_its_own_witness():
    """THE VACUITY KILL. ``cleared_by``, ``proven_by``, ``proven_seal_date`` and
    ``delegated`` are stamped BY this gate. If a caller could pass them in, a
    self-declared clearance could never disagree with the door — which is the whole
    reason the door is worth passing through (Law 6). Each of the four is refused by
    name, before anything is written, and the refusal says which."""
    import inspect as _inspect
    named = _inspect.signature(clear).parameters
    # ``proven_by`` is on the roster too, but it can never REACH journal_extra: it is a
    # named parameter, so a caller who passes it passes it to the gate's own argument and
    # a second one is a TypeError at the call. Structure, not a check — and asserted here
    # rather than assumed, because the day it stops being named is the day the roster
    # entry stops being decorative and starts being the only thing standing there.
    assert named["proven_by"].kind is _inspect.Parameter.KEYWORD_ONLY, \
        "proven_by must stay a named parameter — that is what makes it unsmugglable"
    reachable = [f for f in ("cleared_by", "proven_seal_date", "delegated") if f not in named]
    assert len(reachable) == 3, f"all three must be reachable through journal_extra: {reachable}"
    for field in reachable:
        with tempfile.TemporaryDirectory() as tmp:
            hp, sp = _paths(tmp)
            try:
                clear(
                    _WF, "PROVEME",
                    actor=_OWNER, boat_id=_BOAT,
                    proven_by=_PROVEN, history_path=hp, state_path=sp,
                    **{field: "forged"},
                )
            except Unauthorized as e:
                assert field in str(e), f"the refusal must name the field it refused: {e}"
                assert "written BY the clearance gate" in str(e), e
            else:
                raise AssertionError(f"a caller-supplied {field!r} was accepted")
            assert not Path(hp).exists(), \
                "a refused clearance writes no record of truth — not even an empty one"


# ── THE OWNER IS READ, NOT STATED (ticket boat-owner-is-read-not-stated, 2026-08-10) ──
#
# THE NON-HOLLOW METHOD FOR THIS SET IS TWO-SIDED, AND THE SIGN IS WRITTEN DOWN HERE
# because the ticket's own wording about it is ambiguous and would let a later reader
# check the wrong one. Unambiguously: the exploit call — an actor naming ITSELF the owner
# of a boat it does not own — SUCCEEDS on the reverted code and is REFUSED on the built
# code. On the reverted code the tooth below cannot even be written the same way, because
# ``boat_owner`` was a parameter; that is the point. Revert cycle run by hand at build
# time, both directions recorded in the verdict artifact.


def test_the_owner_cannot_be_stated_by_any_route():
    """THE CENTRAL TOOTH. Four routes, because one closed door is not a closed room.

    (1) the parameter is gone; (2) the keyword does not ride ``**journal_extra`` into the
    record — this is the non-obvious one, since removing a parameter alone leaves the
    caller able to journal an unchecked ownership claim; (3) a grant cannot be minted from
    an owner the minter invented; (4) the two ids naming the voyage must agree."""
    import inspect as _inspect
    assert "boat_owner" not in _inspect.signature(clear).parameters, \
        "the owner must not be statable as an argument — that IS the ticket"

    # (2) the keyword must RAISE, not be swallowed. A signature check alone would pass
    #     while the value rode through into a record of truth.
    for smuggled in ("boat_owner", "owning_intention", "gated_by"):
        with tempfile.TemporaryDirectory() as tmp:
            hp, sp = _paths(tmp)
            try:
                clear(
                    _WF, "PROVEME",
                    actor=_OWNER, boat_id=_BOAT,
                    proven_by=_PROVEN, history_path=hp, state_path=sp,
                    **{smuggled: "fiction"},
                )
            except Unauthorized as e:
                assert smuggled in str(e) and "READ off the boat" in str(e), e
            else:
                raise AssertionError(f"a caller-supplied {smuggled!r} was accepted")
            assert not Path(hp).exists(), "a refused clearance writes no record"


def test_a_grant_minted_from_an_owner_the_minter_invented_authorizes_nothing():
    """THE HOLE THE PARENT TICKET NAMED AS EXAMINED: fixing the direct branch alone moves
    the hole one door along, because a caller who could state the owner could mint itself
    a grant from that same fictional owner and ``authorizes`` would compare the fiction to
    itself. Minting now reads the boat and refuses a minter with no standing on it."""
    try:
        mint_grant(minted_by=_IGOR, boat_id=_BOAT, to_actor=_IGOR, target="PROVEME")
    except Unauthorized as e:
        assert "may not mint" in str(e) and _BOAT in str(e), e
    else:
        raise AssertionError("an unadmitted hand minted itself standing on a boat")


def test_an_actor_merely_similar_to_an_admitted_one_is_refused():
    """THE GREEN-FOR-THE-WRONG-REASON KILL. The comparison replaced a substring scan over
    charter prose, and a substring scan is exactly what it must not become: an actor that
    is a prefix of an admitted one, or an admitted one with something appended, must be
    refused. Derived from the read rather than hard-coded, so the tooth still means this
    if the charter's list changes."""
    admitted = boat_owner_of(_BOAT).hands[0]
    for near in (admitted[:1], admitted + "_extra", admitted.lower(), " " + admitted):
        if near in boat_owner_of(_BOAT).hands:
            continue
        with tempfile.TemporaryDirectory() as tmp:
            hp, sp = _paths(tmp)
            try:
                clear(
                    _WF, "PROVEME",
                    actor=near, boat_id=_BOAT,
                    proven_by=_PROVEN, history_path=hp, state_path=sp,
                )
            except Unauthorized:
                assert not Path(hp).exists(), "a refused clearance writes no record"
            else:
                raise AssertionError(
                    f"{near!r} cleared a boat whose gate admits only "
                    f"{list(boat_owner_of(_BOAT).hands)!r} — the check is scanning, not matching"
                )


def test_a_crossing_that_names_two_voyages_is_refused_before_anything_is_written():
    """``boat_id`` and ``ticket`` arrive by different routes and the docstring has called
    them the same thing since this function was written. Until this check they could
    disagree, so the owner would be read off one boat while the record was written about
    another."""
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id=_BOAT,
                proven_by=_PROVEN, history_path=hp, state_path=sp,
                ticket=_OTHER_BOAT,
            )
        except Unauthorized as e:
            assert "two different voyages" in str(e), e
            assert not Path(hp).exists(), "a mismatched crossing leaves the record untouched"
        else:
            raise AssertionError("a crossing named two voyages and was cleared")


def test_an_unresolvable_hop_refuses_by_name_and_never_defaults():
    """A default here IS the ticket's falsifier clause (1): the owner would once again be
    something other than what the boat says. Each hop is broken in a fixture and the
    refusal must name the address it opened. ``OwnerUnresolvable`` is deliberately not an
    ``Unauthorized`` — 'nobody says who owns this' and 'you have no standing' want
    different responses, and a reader that conflated them would go looking for a grant
    when what is missing is one line in a file."""
    with tempfile.TemporaryDirectory() as tmp:
        tickets = Path(tmp) / "tickets"
        tickets.mkdir()
        charters = Path(tmp) / "charters"
        (charters / "thing").mkdir(parents=True)

        (tickets / "no-field.json").write_text("{}", encoding="utf-8")
        (tickets / "bad-address.json").write_text(
            '{"owning_intention": "nowhere/at/all/intention+why.json"}', encoding="utf-8")
        (tickets / "no-hands.json").write_text(
            '{"owning_intention": "thing/intention+why.json"}', encoding="utf-8")
        (charters / "thing" / "intention+why.json").write_text(
            '{"owner": "a paragraph of prose that no gate can stand on"}', encoding="utf-8")

        def _why(boat):
            try:
                boat_owner_of(boat, tickets_dir=str(tickets),
                              cairn_root=str(charters), commons_root=str(charters))
            except OwnerUnresolvable as e:
                return str(e)
            raise AssertionError(f"{boat!r} resolved an owner it has no business resolving")

        assert str(tickets / "missing.json") in _why("missing"), "name the file you opened"
        assert "owning_intention" in _why("no-field")
        assert "nowhere/at/all" in _why("bad-address")
        assert "gated_by" in _why("no-hands") and "substring scan" in _why("no-hands")

    # And through the gate itself, against the REAL corpus — no injection, because ``clear``
    # accepts none. An id with no ticket behind it is the honest live case.
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        try:
            clear(
                _WF, "PROVEME",
                actor=_OWNER, boat_id="no-such-boat-has-ever-been-cast",
                proven_by=_PROVEN, history_path=hp, state_path=sp,
            )
        except OwnerUnresolvable as e:
            assert "has no ticket at" in str(e), e
            assert not Path(hp).exists(), "an unresolvable owner writes no record"
        else:
            raise AssertionError("the gate cleared a boat it could not find an owner for")


def test_the_read_reaches_nothing_outward():
    """GATE (iii) OF THE TICKET'S OWN PROVEME SET, and falsifier clause (2): the read must
    not make the gate reach outward at a crossing. Asserted structurally over the module's
    transitive imports rather than by trusting the source to look innocent — and the whole
    proof also runs under the tester with ``isolation='netns'``, where a network reach
    fails by construction rather than by an assertion somebody remembered to write."""
    import ast

    # THE SCOPE OF THIS TOOTH IS THE READ, and getting the scope right took two wrong
    # versions worth recording, because both were the same mistake in opposite directions.
    #
    # TOO NARROW: walk ``vars(module)`` for things whose ``__module__`` starts with
    # 'cairn.'. That set contains only cairn names by construction, so 'socket',
    # 'subprocess', 'urllib' and 'http' in the forbidden list below could never match and
    # sat there as decoration reading as coverage. Measured: 5 names, all 'cairn.*'.
    #
    # TOO WIDE: parse the whole transitive static import graph from this module. That
    # reaches ``cairn.tools.base.transitions``, and through it the tester, the build inspector and
    # the chart verdict — 17 modules, three of which import ``subprocess`` because running a
    # proof under netns isolation is *supposed* to shell out. It went red on its first run
    # and the red was about somebody else's correct behaviour. A tooth that fires on normal
    # motion is the pinned-cursor defect; it would have been silenced, and silencing is how
    # a real signal gets trained away.
    #
    # THE CLAIM IS ABOUT THIS FUNCTION: ``boat_owner_of`` must not make a crossing depend on
    # anything being up. So the check is this module's own imports, plus every call the
    # resolution makes, against a whitelist. Anything not on it is a finding — which is the
    # sign that matters, since a NEW reach is exactly what this would have to catch.
    src = _REPO_ROOT / "cairn" / "devices" / "cairn" / "machines" / "harbor_master" / "clearance.py"
    tree = ast.parse(src.read_text(encoding="utf-8"))

    imported = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
            imported.add(node.module.split(".")[0])
    assert imported, "the import scan found nothing — it is measuring itself"
    forbidden = ("socket", "requests", "urllib", "subprocess", "http", "psycopg",
                 "asyncio", "db_domain", "inference_domain")
    assert not (imported & set(forbidden)), \
        f"clearance imports {sorted(imported & set(forbidden))} — falsifier clause (2)"

    # The whitelist is FILE READS AND PURE BUILTINS — nothing that can wait on a socket, a
    # port, a process or a clock. It is enumerated rather than grown by adding whatever the
    # assertion last complained about, which would turn it into a rubber stamp that ratifies
    # the code instead of judging it.
    #
    # AND ADMITTING A HELPER COSTS PROVING THE HELPER. When ``boat_owner_of`` grew a call to
    # ``retirement_of`` (2026-08-18) this tooth went red, correctly: a name on the whitelist
    # is a promise about everything behind it. So the sieve runs over the whole reachable
    # set rather than one function, and a helper is admitted by being CHECKED, never by
    # being named. That is the difference between a whitelist and a rubber stamp.
    allowed = {"open", "isinstance", "json.loads", "os.path.join", "os.path.isfile",
               "os.path.realpath", "os.path.isdir", "os.listdir", "_glob.glob",
               "OwnerUnresolvable", "BoatOwner", "tuple", "str", "read", "strip",
               "get", "encode", "list", "sorted", "len", "repr", "any", "all",
               # the retirement read (ticket a-superseded-intention-is-never-silent) —
               # a pure dict read over a dict the caller already holds, checked below
               "retirement_of", "Retirement", "RetirementUnreadable", "type", "append",
               # the reverse read, bound by the same rule for the same reason: it is what
               # a hand consults while deciding to retire an intention
               "_resolved_charter", "_in_flight", "Riders", "parse_workflow", "endswith",
               "int", "join"}

    def _calls(name):
        fn = next(n for n in ast.walk(tree)
                  if isinstance(n, ast.FunctionDef) and n.name == name)
        out = set()
        for node in ast.walk(fn):
            if isinstance(node, ast.Call):
                f, parts = node.func, []
                while isinstance(f, ast.Attribute):
                    parts.append(f.attr)
                    f = f.value
                if isinstance(f, ast.Name):
                    parts.append(f.id)
                out.add(".".join(reversed(parts)) if parts else "<computed>")
        return out

    # boat_owner_of and everything it reaches; riders_of and everything IT reaches.
    for name in ("boat_owner_of", "retirement_of", "riders_of", "_resolved_charter", "_in_flight"):
        called = _calls(name)
        stray = {c for c in called if c not in allowed and c.split(".")[-1] not in allowed}
        assert not stray, (
            f"{name} calls {sorted(stray)}, which is outside the files-only whitelist — a "
            f"crossing must not depend on anything being up (falsifier clause 2)"
        )
    assert "open" in _calls("boat_owner_of"), \
        "the resolution opens no file — it is not reading the boat at all"
    assert "open" in _calls("riders_of"), "the reverse read opens no file"




# ── A RETIRED INTENTION IS NEVER SILENT (ticket a-superseded-intention-is-never-silent) ──
#
# THE FIXTURE SPLIT, STATED ONCE SO IT IS NOT MISTAKEN FOR CONVENIENCE. The READ half is
# proved against real files on disk, because ``boat_owner_of`` takes root parameters exactly
# so a proof can point it at a fixture. The GATE half cannot be: ``clear`` accepts no root
# injection — deliberately, since a ``tickets_dir=`` parameter would hand the caller back
# the choice of what the gate reads — and there is no retired intention in the live corpus
# to sail a real boat under. So the refusal is proved by substituting the READ (the seam the
# gate calls), which proves the ladder's position, the forward/back asymmetry, and that
# nothing is written. What it does NOT prove is that the gate reads a real charter; the tooth
# above proves that, on real files, and the two together cover the seam end to end.


def _retired_fixture(tmp, *, retired):
    """A real ticket + a real charter on disk, the charter carrying (or not) a retirement."""
    tickets, charters = Path(tmp) / "tickets", Path(tmp) / "charters"
    tickets.mkdir()
    (charters / "thing").mkdir(parents=True)
    (tickets / "a-boat.json").write_text(
        json.dumps({"id": "a-boat", "owning_intention": "thing/intention+why.json",
                    "state": "code-seam@v1: THINKME -> TICKETME -> [BUILDME] -> PROVEME "
                             "-> LEARNME -> PROVED"}), encoding="utf-8")
    charter = {"gated_by": ["CC"]}
    if retired is not None:
        charter["retired"] = retired
    (charters / "thing" / "intention+why.json").write_text(json.dumps(charter), encoding="utf-8")
    return str(tickets), str(charters)


def test_a_retirement_is_read_off_the_charter_THE_OWNER_READ_ALREADY_OPENED():
    """The state costs one ``.get`` on a dict already in hand — asserted by COUNTING FILE
    OPENS, not by reading the code and agreeing with it. A retired charter and a living one
    must cost the gate exactly the same number of opens; the moment the retirement needs a
    lookup of its own, this goes red."""
    import builtins

    def _opens(retired):
        with tempfile.TemporaryDirectory() as tmp:
            t, c = _retired_fixture(tmp, retired=retired)
            real, seen = builtins.open, []

            def counting(f, *a, **k):
                seen.append(str(f))
                return real(f, *a, **k)

            builtins.open = counting
            try:
                owner = boat_owner_of("a-boat", tickets_dir=t, cairn_root=c, commons_root=c)
            finally:
                builtins.open = real
            return owner, len(seen)

    living, n_living = _opens(None)
    dead, n_dead = _opens({"superseded_by": "other/intention+why.json",
                           "when": "2026-08-18", "evidence": "the design moved"})
    assert living.retired is None, "a charter with no retirement key is not retired"
    assert isinstance(dead.retired, Retirement), dead.retired
    assert dead.retired.superseded_by == "other/intention+why.json"
    assert dead.retired.when == "2026-08-18" and dead.retired.evidence == "the design moved"
    assert n_dead == n_living == 2, \
        f"reading a retirement must cost NO extra file open: {n_dead} vs {n_living} (want 2)"


def test_a_malformed_retirement_REFUSES_and_never_reads_as_not_retired():
    """The silent-pass shape, killed. A key somebody meant something by, treated as absence,
    is exactly how this state slips through — so a malformed one raises, and it names every
    lack in one pass the way ``ruling.supersede`` does rather than teaching the schema one
    refusal at a time."""
    with tempfile.TemporaryDirectory() as tmp:
        t, c = _retired_fixture(tmp, retired={"superseded_by": "x/intention+why.json"})
        try:
            boat_owner_of("a-boat", tickets_dir=t, cairn_root=c, commons_root=c)
        except RetirementUnreadable as e:
            msg = str(e)
        else:
            raise AssertionError("a retirement missing when AND evidence read as readable")
        assert "2 lack(s)" in msg, msg
        assert "'when'" in msg and "'evidence'" in msg, "every lack, one pass: " + msg

    # A retirement key of the wrong TYPE is refused too — and never as 'not retired'.
    for bad in (7, [], True):
        try:
            retirement_of({"retired": bad}, at="<fixture>")
        except RetirementUnreadable:
            pass
        else:
            raise AssertionError(f"retired={bad!r} read as a retirement or as absence")

    # Evidence is REQUIRED — the discipline that transfers from the ruling door whole.
    try:
        retirement_of({"retired": {"superseded_by": None, "when": "2026-08-18"}})
    except RetirementUnreadable as e:
        assert "evidence" in str(e)
    else:
        raise AssertionError("a retirement with no stated why was accepted")

    # And the shape a hand reaches for first is normalised ON READ, never by rewrite.
    bare = {"retired": "other/intention+why.json"}
    try:
        retirement_of(bare)
    except RetirementUnreadable:
        pass
    assert bare == {"retired": "other/intention+why.json"}, "the reader rewrote the record"


def _riding_a_retired(retired):
    """Substitute the READ the gate makes — see the note above this section for why."""
    owner = _clearance.BoatOwner(intention="thing/intention+why.json", hands=("CC",),
                                 retired=retired)
    return contextlib.ExitStack(), owner


@contextlib.contextmanager
def _owner_is(owner):
    real = _clearance.boat_owner_of
    _clearance.boat_owner_of = lambda *a, **k: owner
    try:
        yield
    finally:
        _clearance.boat_owner_of = real


def test_a_boat_riding_a_retired_intention_MAY_NOT_MOVE_FORWARD():
    """Clause (a) of the ticket's falsifier: the next forward crossing refuses, naming the
    retirement and the successor. And it refuses BEFORE ``emit`` — no history file appears,
    so a refused crossing leaves no partial record, exactly like the four refusals beside it."""
    _, owner = _riding_a_retired(Retirement(superseded_by="new/intention+why.json",
                                            when="2026-08-18",
                                            evidence="the design moved to the new seam"))
    with tempfile.TemporaryDirectory() as tmp, _owner_is(owner):
        hp, sp = _paths(tmp)
        try:
            clear(_WF, "PROVEME", actor="CC", boat_id=_BOAT, proven_by=_PROVEN,
                  history_path=hp, state_path=sp)
        except IntentionRetired as e:
            msg = str(e)
        else:
            raise AssertionError("a boat sailed forward under a retired intention")
        assert "thing/intention+why.json" in msg, "name the retired intention: " + msg
        assert "new/intention+why.json" in msg, "name the successor: " + msg
        assert "2026-08-18" in msg and "the design moved to the new seam" in msg, msg
        assert not Path(hp).exists(), "a refused crossing wrote a history record"
        assert not Path(sp).exists(), "a refused crossing wrote a state record"


def test_but_it_may_still_RETREAT_because_a_wall_is_not_a_gate():
    """The back-edge is exempt and that is load-bearing: a retreat is how a boat that has
    lost its intention gets dealt with. Refusing it too would leave such a boat with no
    legal move at all — a gate that has stopped being a gate."""
    _, owner = _riding_a_retired(Retirement(superseded_by=None, when="2026-08-18",
                                            evidence="retired outright"))
    with tempfile.TemporaryDirectory() as tmp, _owner_is(owner):
        hp, sp = _paths(tmp)
        after = clear(_WF, "TICKETME", actor="CC", boat_id=_BOAT, proven_by=_PROVEN,
                      history_path=hp, state_path=sp, ticket=_BOAT)
        assert "[TICKETME" in after, after   # the retreat landed (cursor carries a phase)
        assert Path(hp).exists(), "the retreat was cleared but nothing was journaled"


def test_a_retirement_with_NO_SUCCESSOR_still_refuses_and_says_so():
    """The state the ruling door's shape could not express at all, and the reason this key
    lives on the retired charter rather than on a successor that may not exist."""
    _, owner = _riding_a_retired(Retirement(superseded_by=None, when="2026-08-18",
                                            evidence="the problem it solved stopped existing"))
    with tempfile.TemporaryDirectory() as tmp, _owner_is(owner):
        hp, sp = _paths(tmp)
        try:
            clear(_WF, "PROVEME", actor="CC", boat_id=_BOAT, proven_by=_PROVEN,
                  history_path=hp, state_path=sp)
        except IntentionRetired as e:
            assert "nothing replacing it" in str(e), str(e)
            assert "the problem it solved stopped existing" in str(e)
        else:
            raise AssertionError("a successorless retirement was silent")


def test_the_reverse_read_PARTITIONS_the_fleet_and_agrees_with_the_register():
    """Clause (b), asserted as INVARIANTS over the LIVE corpus — never a snapshot count,
    because a number written here goes red on the day somebody casts a ticket.

    Two invariants: the four buckets partition the in-flight population exactly, and every
    boat the reverse read returns is one the fleet register also calls open. If the two
    disagree about what a boat IS, that disagreement is the finding."""
    r = riders_of("cairn/devices/cairn/machines/harbor_master/intention+why.json")
    assert isinstance(r, Riders)
    assert r.attributable + len(r.unattributed) + len(r.unresolvable) == r.in_flight, \
        f"the buckets do not partition the fleet: {r.blind} over {r.in_flight}"
    assert set(r.blind) == {"unattributed", "unresolvable", "unreadable"}, \
        "all three blind classes are reported, at zero as well as non-zero"
    open_ids = {b["id"] for b in _register.register()["open"]}
    assert set(r.riding) <= open_ids, \
        f"the reverse read returned boats the register does not call open: " \
        f"{set(r.riding) - open_ids}"
    assert set(u for u in r.unattributed) <= open_ids


def test_THE_BLIND_COUNT_CANNOT_BE_REMOVED_WITHOUT_THIS_PROOF_GOING_RED():
    """The non-hollow floor for a scan: removing the measurement must turn the check red.
    A report that names only what it found is a green earned by not looking, and the ONLY
    way to know a tooth actually bites on that is to break it and watch.

    Each blind class is removed in turn from a FIXTURE ``Riders`` with known non-zero
    blind counts, and the partition assertion is re-run; a class whose removal changes
    nothing is a class nobody is checking. Uses a fixture rather than the live corpus so
    the tooth proves the algorithm regardless of whether the fleet currently has work."""
    fixture = _clearance.Riders(
        intention="fixture",
        riding=("ticket-a", "ticket-b"),
        in_flight=4,
        attributable=2,
        unattributed=("ticket-c",),
        unresolvable=(("ticket-d", "gone/intention+why.json"),),
        unreadable=(("ticket-e", "bad json"),),
    )

    def partitions(r):
        return r.attributable + len(r.unattributed) + len(r.unresolvable) == r.in_flight

    assert partitions(fixture), "the fixture itself must partition"
    for field in ("unattributed", "unresolvable"):
        hollowed = _clearance.Riders(**{**fixture.__dict__, field: ()})
        assert not partitions(hollowed), \
            f"dropping {field!r} from the report left every check green — the count is decorative"
    assert "unreadable" in fixture.blind and isinstance(fixture.unreadable, tuple)


def test_the_read_face_prints_only_numbers_the_library_returned():
    """A presentation surface may arrange; it may not compute a second version of the truth
    (Law 7). Every integer the report prints is checked against the one the library returned
    on the same corpus — so the printed answer and the programmatic answer cannot drift."""
    addr = "cairn/devices/cairn/machines/harbor_master/intention+why.json"
    r = riders_of(addr)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = _register._retirement_report(addr)
    out = buf.getvalue()
    assert rc == 0
    for label, n in r.blind.items():
        assert f"{label:12}  {n:4}" in out, f"{label}={n} not printed as the library reports it"
    assert f"over {r.in_flight} in-flight boats, {r.attributable} were attributable" in out
    for boat in r.riding:
        assert boat in out, f"a found boat was not printed: {boat}"
    for boat, _addr in r.unresolvable:
        assert boat in out, f"an unresolvable boat was not named: {boat}"


def test_this_build_added_no_tracing_of_its_own():
    """``clear``'s frame-level ``try/except BaseException`` already records every refusal
    that leaves the function — "including refusals nobody has thought of yet", as its
    docstring says. This build leaned on that and wrote none of its own; the census is what
    keeps that true tomorrow. A second write site is a second record of the same fact, which
    is the rival-record shape Law 7 and Law 6 both refuse."""
    import ast as _ast

    tree = _ast.parse(Path(_clearance.__file__).read_text(encoding="utf-8"))
    sites = {}          # function name -> how many times it calls the trace writer
    for fn in _ast.walk(tree):
        if not isinstance(fn, _ast.FunctionDef):
            continue
        for node in _ast.walk(fn):
            if isinstance(node, _ast.Call) and getattr(node.func, "id", None) == "write_trace":
                sites[fn.name] = sites.get(fn.name, 0) + 1
    assert sites == {"_trace_attempt": 1}, \
        f"the trace store is written from {sites} — it has exactly one writer, by design"

    callers = {fn.name for fn in _ast.walk(tree) if isinstance(fn, _ast.FunctionDef)
               for n in _ast.walk(fn)
               if isinstance(n, _ast.Call) and getattr(n.func, "id", None) == "_trace_attempt"}
    assert callers == {"clear"}, \
        (f"the gate's queue is written from {sorted(callers)} — the frame-level tracer in "
         "clear() covers every refusal that leaves the function, 'including refusals nobody "
         "has thought of yet'. A refusal that wrote its own trace would be a second record "
         "of the same fact, and the retirement refusal added in 2026-08-18 deliberately "
         "wrote none.")


# ── THE PROOF MUST COVER THE BOAT (ticket 1accdc1781aa) ─────────────────────────────────
#
# THE SIXTH REFUSAL, and it is a different question from the fifth. Rule 2 asks *is the
# named code in proven-space?* — about the PROOF. This asks *does that proof say anything
# about THIS boat?* — about the JOIN. A green, current seal on a proof that declares not one
# tooth for this ticket's clauses is the shape measured on four of twelve tickets on
# 2026-09-07: a green standing in for a proof nobody wrote.
#
# THE FIXTURES ARE REAL ALL THE WAY DOWN and nothing here hand-writes a seal. The proof is a
# real file, run by the REAL tester, sealed through the REAL single write-door, and its
# hollow reading is landed by the REAL ``record_hollow``. A build that faked any of the three
# dies here. What IS substituted is the boat's owner — the same ``_owner_is`` precedent the
# retirement teeth use, and for the same stated reason: the gate takes no root injection,
# because a ``tickets_dir=`` parameter would hand the caller back the choice of what the gate
# reads. Naming the proof by ABSOLUTE path is what lets a fixture ticket point at scratch
# without any door into the gate at all.
#
# AND SINCE 2026-09-10 A SECOND READ IS SUBSTITUTED, for the same reason and by the same
# means. The ticket's record of crossings is now DERIVED from history.json in two roots
# (ruling crossings-are-derived-never-written) rather than stored on the ticket, so an
# absolute proof path is no longer everything a fixture needs — the record itself lives on
# disk. ``_crossing_roots`` is the module-level read the gate asks, taking no arguments so
# no caller can pass one, and ``_journalled`` stands a scratch world behind it. THE JOURNAL
# IS REAL TOO: the same ``{"entries": [...]}`` shape ``emit`` writes, read by the same
# derivation the live gate reads, in a scratch root — never a manufactured entry in a record
# of truth (Law 7).


def _journal_world() -> Path:
    world = Path(_SCRATCH) / "journal-world"
    (world / "cairn").mkdir(parents=True, exist_ok=True)
    return world


def _journalled(tid: str, proof: str, *, to: str = "PROVEME") -> None:
    """Record a crossing for ``tid`` in the fixture world's journal — append, never replace,
    so a tooth that records twice gets latest-wins the way the live derivation orders by ``at``."""
    path = _journal_world() / "cairn" / "history.json"
    doc = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"entries": []}
    n = len(doc["entries"])
    doc["entries"].append({"ticket": tid, "to": to, "direction": "forward", "actor": _OWNER,
                           "at": f"2026-09-10T00:{n // 60:02d}:{n % 60:02d}",
                           "proven_by": proof})
    path.write_text(json.dumps(doc, indent=2), encoding="utf-8")


@contextlib.contextmanager
def _fixture_journals():
    """Stand the fixture world behind the gate's crossing-record read — the ``_owner_is``
    precedent, applied to the second read the coverage rung makes."""
    world = _journal_world()
    real = _clearance._crossing_roots
    _clearance._crossing_roots = lambda: {"repo": world, "commons": world / "commons",
                                          "instance": world / "instance"}
    try:
        yield
    finally:
        _clearance._crossing_roots = real

_COVERED_TOOTH = "test_the_thing_the_build_added"


def _covering_proof(name: str, tid: str, *, declares: bool = True) -> str:
    """A real proof that PRINTS a green tooth and DECLARES it for ``tid``. Sealed by caller."""
    proofs = Path(_SCRATCH) / name / "proofs"
    proofs.mkdir(parents=True, exist_ok=True)
    proof = proofs / f"test_{name}.py"
    body = f'''"""A covering proof fixture for the clearance coverage rung."""
'''
    if declares:
        body += f'PROVES = {{{tid!r}: {{"1": {_COVERED_TOOTH!r}}}}}\n'
    body += f'print("  ok   {_COVERED_TOOTH}")\nraise SystemExit(0)\n'
    proof.write_text(body, encoding="utf-8")
    return str(proof)


def _fixture_ticket(tid: str, proof: str, *, node_class: str = "code-seam") -> dict:
    """A boat whose falsifier names exactly one clause.

    NO ``crossings`` KEY, because no ticket in the corpus carries one since 2026-09-10
    (ruling crossings-are-derived-never-written) and a fixture shaped like the old world
    would go green over a reader that no longer exists. The proof this boat leans on reaches
    the coverage rung the way the real crossing carries it — as ``clear``'s ``proven_by``
    argument, which the rung passes through as ``named``.
    """
    _journalled(tid, proof)
    return {
        "id": tid,
        "node_class": node_class,
        "falsifier": "DONE when (1) the thing the build added is actually there.",
    }


def _covered_owner(tid: str, proof: str, **kw) -> "_clearance.BoatOwner":
    return _clearance.BoatOwner(intention="thing/intention+why.json", hands=(_OWNER,),
                                ticket=_fixture_ticket(tid, proof, **kw))


# THE FIXTURE TICKETS DIR IS BACK, and the comment two hundred lines up that says it is gone
# is still right about WHY it went: it was safe only while nothing read the ticket's CONTENTS.
# What changed on 2026-09-09 is where the contents come from. The coverage rung reads them off
# ``BoatOwner.ticket`` — the owner read, which these teeth substitute through the established
# ``_owner_is`` precedent — and the chokepoint's own named-ticket gate reads the DIRECTORY for
# EXISTENCE ONLY (``_require_named_ticket`` -> ``_find_ticket``, a glob that returns a path or
# None and never opens it). Two different questions, two different sources, and only the
# existence half needs a file on disk. So the fixture dir is a cast-registry stub, not a
# ticket store: it holds the emptiest legal file that makes ``_find_ticket`` say yes.
#
# WHY NOT USE A REAL CAST TICKET, as ``test_a_gated_crossing_can_actually_be_cleared`` does?
# Because these teeth cross the SAME boat with coverage deliberately broken in six different
# ways, and a real ticket would put six fabricated states onto a live voyage's name. The
# reachability tooth there is about the crossing; these are about the rung, and the rung's
# input is the ticket dict, which is substituted either way.
_FIXTURE_TICKETS = Path(_SCRATCH) / "cast-registry"


def _cast(tid: str) -> None:
    """Make ``tid`` resolve for the chokepoint's existence-only named-ticket gate."""
    _FIXTURE_TICKETS.mkdir(parents=True, exist_ok=True)
    (_FIXTURE_TICKETS / f"{tid}.json").write_text(
        json.dumps({"id": tid, "cursor": "code-seam@v1: ... [PROVEME]"}), encoding="utf-8")


def _cross_to_proved(owner, tmp: str, *, boat: str, proven_by: str, **kw):
    """Ask the gate for the PROVED crossing this rung guards. Returns the refusal, or None."""
    import cairn.machines.build_inspector.inspector as _insp
    import cairn.tools.base.transitions as _t
    hp, sp = _paths(tmp)
    at_learn = ("code-seam@v1: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
                "[LEARNME] -> PROVED")
    _cast(boat)
    _saved = _insp._CHART_BERTHS
    _saved_tickets = _t._TICKETS
    _insp._CHART_BERTHS = Path(tmp) / "no-chart-berths"
    _t._TICKETS = _FIXTURE_TICKETS
    try:
        with _owner_is(owner), _fixture_journals():
            clear(at_learn, "PROVED", actor=_OWNER, boat_id=boat, proven_by=proven_by,
                  history_path=hp, state_path=sp, ticket=boat, **kw)
    except Exception as exc:  # noqa: BLE001 — the refusal IS the measurement here
        return exc
    finally:
        _insp._CHART_BERTHS = _saved
        _t._TICKETS = _saved_tickets
    return None


# Built once: the covered boat every admission tooth below leans on.
_COVERED_TID = "cover000000a"
_COVERED_PROOF = _covering_proof("covered", _COVERED_TID)
_seal(_COVERED_PROOF)
assert record_hollow(_COVERED_PROOF, _COVERED_TID,
                     {"thing.py": [_COVERED_TOOTH]}) is True, \
    "the hollow reading must land through the real door, or the admission tooth is hollow itself"


class _Raises:
    """A trouble device that only remembers — the injection ``persist_validation`` established."""

    def __init__(self):
        self.raised = []

    def raise_trouble(self, identity, *, why, detail=None, now=None):
        self.raised.append({"identity": identity, "why": why, "detail": detail or {}})
        return {"poke": "held for the beat — fixture"}


def test_a_COVERED_boat_crosses_to_PROVED_and_the_rung_is_reachable():
    """THE ADMISSION. Before asserting the rung refuses anything, prove it can be SATISFIED —
    a gate nothing can pass is a wall, and a refusal tooth beside a wall goes green for the
    wrong reason. Every ingredient is real: the tester ran the proof, the store sealed it,
    ``record_hollow`` landed the reading, and the ticket's one clause has a declared tooth
    that printed green."""
    with tempfile.TemporaryDirectory() as tmp:
        owner = _covered_owner(_COVERED_TID, _COVERED_PROOF)
        exc = _cross_to_proved(owner, tmp, boat=_COVERED_TID, proven_by=_COVERED_PROOF)
        assert exc is None, f"a fully covered boat must cross: {type(exc).__name__}: {exc}"
        hp, _ = _paths(tmp)
        rec = projector.read_history(hp)[0]
        assert rec["proven_by"] == _COVERED_PROOF, rec


def test_the_rung_fires_ONLY_at_PROVED_so_a_boat_under_construction_still_moves():
    """THE SCOPE, and it is load-bearing. Demanding full coverage at BUILDME would refuse the
    very act that goes and gets it. The SAME boat that crosses to PROVED above, stripped of
    every scrap of coverage, still crosses to PROVEME — so the rung is bounded by the target
    and not by luck."""
    # NO ``ticket=`` ON THE CROSSING, and that is the file's standing precedent rather than a
    # dodge: ``_WF``'s cursor sits AT BUILDME, so a forward crossing off it meets the
    # chokepoint's ENTRY gate whenever a ticket is named — a gate about the chart chain, not
    # about coverage. Every PROVEME tooth above crosses the same way for the same reason. The
    # COVERAGE state is what this tooth varies, and the rung reads that off the substituted
    # owner: no crossings, no proof, no seal, no hollow reading. Utterly uncovered, and it moves.
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        owner = _clearance.BoatOwner(intention="thing/intention+why.json", hands=(_OWNER,),
                                     ticket={"id": "nocover0000a", "node_class": "code-seam",
                                             "falsifier": "DONE when (1) x."})
        with _owner_is(owner):
            out = clear(_WF, "PROVEME", actor=_OWNER, boat_id="nocover0000a",
                        proven_by=_PROVEN, history_path=hp, state_path=sp)
        assert "[PROVEME" in out, out


def test_an_UNCOVERED_boat_is_REFUSED_at_PROVED_and_every_lack_is_named_in_one_pass():
    """Clause (3), first third: the coverage finding is non-empty and the door refuses. EVERY
    lack in one pass — a caller who fixes what he is told and hits a second refusal learns to
    distrust the report, which is the reasoning ``proof_coverage.lacks`` was built on and the
    reason this rung composes it instead of asking its own first-failure question."""
    tid = "uncover0000a"
    proof = _covering_proof("uncovered", tid, declares=False)
    _seal(proof)
    with tempfile.TemporaryDirectory() as tmp:
        exc = _cross_to_proved(_covered_owner(tid, proof), tmp, boat=tid, proven_by=proof)
        assert isinstance(exc, _built("Uncovered")), f"an uncovered boat crossed to PROVED: {exc!r}"
        msg = str(exc)
        for want in ("proof_declares_the_ticket", "clause_declared", "hollow_evidence_absent"):
            assert want in msg, f"the refusal must name the {want} lack in the same pass: {msg}"
        hp, _ = _paths(tmp)
        assert not Path(hp).exists(), \
            "a refused crossing leaves no partial record — like the five refusals beside it"


def test_a_seal_whose_FINGERPRINT_HAS_MOVED_is_refused_at_PROVED():
    """Clause (3), second third. Not a second instrument: "is this seal still about this
    code?" is exactly what ``lacks`` already asks of every named proof, so the rung asks it
    once rather than adding a fingerprint check beside the sieve that has one.

    AND THE TWO SETS OF PROOFS ARE NOT THE SAME SET — which is the whole reason this rung
    still earns its keep after rule 2. Rule 2 asks whether the proofs THIS CROSSING NAMES
    stand; the rung asks whether the proofs THE TICKET'S RECORD NAMES cover the ticket. At a
    PROVED crossing the ticket's latest recorded crossing is the PROVEME one, so the second
    set is the older set, and a fresh ``proven_by=`` walks a stale record straight past rule
    2. Measured while writing this: pointing both at one stale proof never reaches the rung
    at all — rule 2 refuses first with ``Unproven`` — so a tooth built that way would have
    gone green on a gate that is not the one under test. The fixture below splits them."""
    tid = "moved00000a"
    stale = _covering_proof("fingerprint-moved", tid)
    _seal(stale)
    assert record_hollow(stale, tid, {"thing.py": [_COVERED_TOOTH]}) is True
    Path(stale).write_text(Path(stale).read_text(encoding="utf-8")
                           + "\n# the code moved under the seal\n", encoding="utf-8")
    fresh = _covering_proof("fingerprint-fresh", tid)
    _seal(fresh)
    assert record_hollow(fresh, tid, {"thing.py": [_COVERED_TOOTH]}) is True
    with tempfile.TemporaryDirectory() as tmp:
        # The owner's ticket records the STALE proof; the crossing names the FRESH one.
        exc = _cross_to_proved(_covered_owner(tid, stale), tmp, boat=tid, proven_by=fresh)
        assert isinstance(exc, _built("Uncovered")), f"a stale-fingerprint seal cleared PROVED: {exc!r}"
        assert "seal_fingerprint_current" in str(exc), str(exc)


def test_a_CODE_SEAM_WITH_NO_HOLLOW_READING_is_refused_the_same_as_an_absent_seal():
    """Clause (3), final third, and it is the rung's whole point. This proof is perfectly
    sealed, perfectly current, and declares a green tooth for the ticket's one clause — the
    coverage sieve alone reads it CLEAN. It is refused anyway, because nothing has ever
    distinguished its green from the green a build with the work reverted would also print
    (Law 8: a proof a hollow build couldn't pass)."""
    tid = "nohollow000a"
    proof = _covering_proof("no-hollow", tid)
    _seal(proof)
    ticket = _fixture_ticket(tid, proof)
    with _fixture_journals():
        clean = _clearance.coverage_lacks(ticket, repo_root=Path(_REPO_ROOT),
                                          roots=_clearance._crossing_roots())
    assert clean == [], \
        "the setup must be CLEAN to the coverage sieve, or this tooth proves nothing new"
    with tempfile.TemporaryDirectory() as tmp:
        exc = _cross_to_proved(_covered_owner(tid, proof), tmp, boat=tid, proven_by=proof)
        assert isinstance(exc, _built("Uncovered")), f"a code-seam with no hollow reading crossed: {exc!r}"
        assert "hollow_evidence_absent" in str(exc), str(exc)


def test_a_HOLLOW_FILE_in_the_reading_is_refused_and_the_refusal_NAMES_THE_FILE():
    """A reading that was taken and came back bad. ``{file: []}`` means reverting that file
    redded no declared tooth — the proof is green whether that code is there or not. The file
    name rides the refusal because it is the one thing the builder has to go and fix."""
    tid = "hollowf0000a"
    proof = _covering_proof("hollow-file", tid)
    _seal(proof)
    assert record_hollow(proof, tid, {"real.py": [_COVERED_TOOTH], "decorative.py": []}) is True
    with tempfile.TemporaryDirectory() as tmp:
        exc = _cross_to_proved(_covered_owner(tid, proof), tmp, boat=tid, proven_by=proof)
        assert isinstance(exc, _built("Uncovered")), f"a hollow file crossed to PROVED: {exc!r}"
        assert "hollow_file" in str(exc) and "decorative.py" in str(exc), str(exc)
        assert "real.py" not in str(exc), \
            "only the HOLLOW files are named — listing the sound ones buries the finding"


def test_an_UNREADABLE_file_is_REFUSED_and_is_never_folded_into_hollow():
    """The third value a reading can carry, and the one the seal used to throw away.

    ``cairn test --hollow`` reverts a file and re-runs the ticket's teeth. Usually a tooth
    reds (covered) or none does (hollow). The third outcome is that the reversion breaks the
    proof's IMPORT, so it prints no teeth at all — and then whatever tooth list survives says
    nothing whatever about that file. ``hollow.measure`` already refuses to call that covered
    or hollow and reds the run; until 2026-09-09 the SEAL dropped the distinction, so this
    rung read a leftover non-empty list and called the file covered. Two files on this very
    ticket's reading came through that hole. It is its own refusal and its own fix text: a
    hollow file needs a tooth written, an unreadable one needs the proof to stop binding the
    build's new names at import time — sending the builder at the other problem costs a
    round trip."""
    tid = "unreadabl0a"
    proof = _covering_proof("unreadable", tid)
    _seal(proof)
    assert record_hollow(proof, tid, {"real.py": [_COVERED_TOOTH],
                                      "broke.py": {"unreadable": ["proofs/test_broke.py"]}}) is True
    lacks = _built("hollow_lacks")(_fixture_ticket(tid, proof), [proof],
                                   repo_root=Path(_REPO_ROOT))
    kinds = [one["kind"] for one in lacks]
    assert kinds == ["hollow_unreadable"], \
        f"an unreadable reading must red ONCE, as itself, not as a hollow file: {kinds}"
    assert lacks[0]["values"]["files"] == ["broke.py"], lacks[0]
    assert "real.py" not in json.dumps(lacks[0]), \
        "only the UNREADABLE files are named — listing the sound ones buries the finding"
    with tempfile.TemporaryDirectory() as tmp:
        exc = _cross_to_proved(_covered_owner(tid, proof), tmp, boat=tid, proven_by=proof)
        assert isinstance(exc, _built("Uncovered")), f"an unreadable reading crossed: {exc!r}"
        assert "hollow_unreadable" in str(exc) and "broke.py" in str(exc), str(exc)


def test_a_CONCEPT_PIECE_is_never_asked_for_a_hollow_reading():
    """The fork that keeps this rung honest rather than merely strict. A concept-piece is
    proved by PEOPLE READING IT — there is no build to hollow out and no file to revert, so
    demanding the reading would be demanding evidence that cannot exist. ``proof_coverage``
    already forks concept-pieces to their own coverage question; this takes the same fork."""
    tid = "concept0000a"
    proof = _covering_proof("concept", tid)
    _seal(proof)
    ticket = _fixture_ticket(tid, proof, node_class="concept-piece")
    assert _built("hollow_lacks")(ticket, [proof], repo_root=Path(_REPO_ROOT)) == [], \
        "a concept-piece was asked for a hollow reading it cannot have"
    # And the fold is the system's, not a string compare: he may type it in any case.
    assert _built("hollow_lacks")({**ticket, "node_class": "Concept-Piece"}, [proof],
                        repo_root=Path(_REPO_ROOT)) == [], \
        "the node class is a system word and folds case (ruled 2026-09-07)"
    assert _built("hollow_lacks")(_fixture_ticket(tid, proof), [proof],
                        repo_root=Path(_REPO_ROOT)) != [], \
        "and the fork must be the CLASS — a code-seam with the same seal is still asked"


def test_a_REFUSAL_RAISES_A_TROUBLE_naming_the_boat_and_the_finding():
    """The half of the rule that is not the refusal. A gate that only refuses teaches the one
    caller standing at it; the boat then sits at PROVEME looking exactly like a boat nobody
    has got to yet. The trouble is what makes the reason outlive the call — one identity per
    BOAT, so five refusals fold to one trouble with a count of five."""
    tid = "trouble0000a"
    proof = _covering_proof("trouble", tid, declares=False)
    _seal(proof)
    dev = _Raises()
    with tempfile.TemporaryDirectory() as tmp:
        exc = _cross_to_proved(_covered_owner(tid, proof), tmp, boat=tid, proven_by=proof,
                               trouble_device=dev)
    assert isinstance(exc, _built("Uncovered"))
    assert len(dev.raised) == 1, f"exactly one trouble per refusal: {dev.raised}"
    one = dev.raised[0]
    assert tid in one["identity"], one["identity"]
    assert one["detail"]["boat"] == tid and one["detail"]["lacks"], one["detail"]
    assert {l["kind"] for l in one["detail"]["lacks"]} <= set(one["why"] .split()) | \
        {k for k in ("proof_declares_the_ticket", "clause_declared", "hollow_evidence_absent")}, \
        "the why must name the kinds a reader would grep for"


def test_a_TROUBLE_STORE_THAT_IS_DOWN_never_turns_a_clean_refusal_into_a_stack_trace():
    """Law 7 at a diagnostic surface, pointed the safe way. The refusal is the record of
    truth and it is already on its way up; a diagnostics failure must not make the gate MORE
    dangerous. Measured by handing it a device that throws."""
    class _Broken:
        def raise_trouble(self, *a, **k):
            raise RuntimeError("the trouble store is down")

    tid = "broken00000a"
    proof = _covering_proof("broken-trouble", tid, declares=False)
    _seal(proof)
    with tempfile.TemporaryDirectory() as tmp:
        exc = _cross_to_proved(_covered_owner(tid, proof), tmp, boat=tid, proven_by=proof,
                               trouble_device=_Broken())
    assert isinstance(exc, _built("Uncovered")), \
        f"a broken trouble store replaced the refusal with its own failure: {exc!r}"


def test_the_rung_reads_the_TARGET_as_a_system_word_so_lower_case_proved_cannot_walk_past():
    """Ruled 2026-09-07: a stage token is a system word and compares folded. A bare string
    compare against "PROVED" would let ``proved`` through the one rung that guards the
    terminal — the check going green for the wrong reason, on the cheapest possible input."""
    tid = "lowercase00a"
    proof = _covering_proof("lowercase", tid, declares=False)
    _seal(proof)
    with tempfile.TemporaryDirectory() as tmp:
        import cairn.machines.build_inspector.inspector as _insp
        hp, sp = _paths(tmp)
        at_learn = ("code-seam@v1: THINKME -> TICKETME -> BUILDME -> PROVEME -> "
                    "[LEARNME] -> PROVED")
        _saved = _insp._CHART_BERTHS
        _insp._CHART_BERTHS = Path(tmp) / "no-chart-berths"
        try:
            with _owner_is(_covered_owner(tid, proof)):
                clear(at_learn, "proved", actor=_OWNER, boat_id=tid, proven_by=proof,
                      history_path=hp, state_path=sp, ticket=tid)
        except _built("Uncovered"):
            pass
        else:
            raise AssertionError("a lower-case 'proved' walked past the coverage rung")
        finally:
            _insp._CHART_BERTHS = _saved


def test_proven_by_IS_READ_AS_ONE_OR_MANY_because_a_seam_has_more_than_one_end():
    """The live trouble clearance-gate-checks-one-proof-while-the-record-names-many —
    THE HARBOR'S HALF. ``proof_coverage`` has read a crossing's ``proven_by`` as one-or-many
    since 2026-09-07; this rung called ``standing()`` on the value whole, so a list was a
    TypeError at the door — and where it did not throw, the gate verified ONE proof while the
    sieve judged all of them. EVERY named proof must stand: a seam is not proven because one
    of its ends is.

    AND IT IS ONLY HALF, measured 2026-09-09 rather than assumed. This tooth crosses to
    PROVEME, and PROVEME ``is_summons`` — so the IDENTICAL rung inside the chokepoint
    (``transitions.inspect_clearance``, which fires only on a crossing into a REST) never ran
    here, and stayed unfixed while this tooth read green. Ticket 1accdc1781aa found it the
    expensive way: the harbor cleared a two-ended seam and the chokepoint then raised
    ``expected str, bytes or os.PathLike object, not list``. Base's half is proved at base's
    own address — ``cairn/tools/base/proofs/test_transitions.py``,
    ``test_the_clearance_lane_reads_proven_by_AS_ONE_OR_MANY_and_every_end_must_stand`` — and
    the seam end-to-end by ``test_a_TWO_ENDED_SEAM_crosses_carrying_BOTH_ends_not_just_the_one_that_sealed``
    in codemother's proof. A rung that exists twice must be proved twice."""
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        # Two proofs, both standing — the list must clear, not throw. Unticketed for the same
        # reason as the scope tooth above: the entry gate is in the path off ``_WF``.
        with _owner_is(_covered_owner("manyends000a", _PROVEN)):
            out = clear(_WF, "PROVEME", actor=_OWNER, boat_id="manyends000a",
                        proven_by=[_PROVEN, _COVERED_PROOF], history_path=hp, state_path=sp)
        assert "[PROVEME" in out, out
    with tempfile.TemporaryDirectory() as tmp:
        hp, sp = _paths(tmp)
        # One end unsealed — the whole seam is unproven, and the refusal says WHICH end.
        try:
            with _owner_is(_covered_owner("oneend0000a", _PROVEN)):
                clear(_WF, "PROVEME", actor=_OWNER, boat_id="oneend0000a",
                      proven_by=[_PROVEN, _UNSEALED], history_path=hp, state_path=sp)
        except Unproven as exc:
            assert _UNSEALED in str(exc) and "one of its ends" in str(exc), str(exc)
        else:
            raise AssertionError("a seam with an unproven end cleared")
        assert not Path(hp).exists(), "and nothing was written"


def test_A_HOLLOW_READING_SURVIVES_A_RESEAL_OF_THE_SAME_CODE_AND_ONLY_THAT():
    """THE DEFECT THIS VOYAGE UNCOVERED, and the rung above is unbuildable without the fix.
    ``persist_validation`` REPLACES, so ``evidence.hollow`` had a lifetime of one commit:
    measured 2026-09-09, the fc93d8cd5961 run reported "hollow evidence landed on 1 of 1
    standing validation(s)" and a corpus-wide read found ZERO records anywhere carrying the
    key, because the pre-commit reseal ladder runs on every commit and each reseal dropped
    it. The carry is FINGERPRINT-BOUND, which is the whole point: a reading about a tree that
    no longer exists must expire (Law 3)."""
    tid = "survive0000a"
    proof = _covering_proof("survives-reseal", tid)
    _seal(proof)
    assert record_hollow(proof, tid, {"thing.py": [_COVERED_TOOTH]}) is True

    def _hollow_now():
        from cairn.tools.base.validation import latest_seal
        return ((latest_seal(proof, artifact=False).get("evidence") or {}).get("hollow") or {})

    assert tid in _hollow_now(), "the setup must land the reading"
    _seal(proof)                       # a re-seal of UNCHANGED code
    assert tid in _hollow_now(), \
        "a re-seal of the same code dropped the hollow reading — the one-commit lifetime is back"
    Path(proof).write_text(Path(proof).read_text(encoding="utf-8") + "\n# moved\n",
                           encoding="utf-8")
    _seal(proof)                       # a re-seal AFTER the code moved
    assert tid not in _hollow_now(), \
        ("a hollow reading outlived the tree it was taken on — it must expire with the "
         "fingerprint (Law 3), or the gate leans on a measurement about code that is gone")


def _main() -> int:
    checks = [
        test_the_owner_may_clear_a_legal_move_and_it_is_recorded,
        test_an_unauthorized_actor_is_refused_and_nothing_is_written,
        test_clearance_is_delegable_per_operation,
        test_a_grant_is_non_ambient_it_does_not_authorize_other_operations,
        test_even_the_owner_cannot_clear_an_illegal_move,
        test_clearing_onto_code_that_was_never_sealed_is_refused,
        test_clearing_onto_code_whose_proof_went_red_is_refused,
        test_a_green_seal_whose_code_has_moved_underneath_it_is_refused,
        test_the_record_names_the_proof_the_clearance_leaned_on,
        test_a_lapsed_grant_is_refused_and_nothing_is_written,
        test_the_same_grant_inside_its_window_still_clears,
        test_a_crossed_resource_line_refuses_an_otherwise_perfect_move,
        test_the_gate_asks_for_a_verdict_and_never_counts_anything,
        test_a_gated_crossing_can_actually_be_cleared_and_the_ticket_rides,
        test_a_caller_may_not_hand_this_gate_its_own_witness,
        test_the_owner_cannot_be_stated_by_any_route,
        test_a_grant_minted_from_an_owner_the_minter_invented_authorizes_nothing,
        test_an_actor_merely_similar_to_an_admitted_one_is_refused,
        test_a_crossing_that_names_two_voyages_is_refused_before_anything_is_written,
        test_an_unresolvable_hop_refuses_by_name_and_never_defaults,
        test_the_read_reaches_nothing_outward,
        # THE GATE'S QUEUE (ticket clearance-leaves-a-trace). The live-store tooth runs
        # LAST on purpose: it is the one that can only judge the run once the run is over.
        test_a_refused_attempt_leaves_a_durable_record_carrying_its_reason,
        test_a_grant_and_a_refusal_are_one_field_apart_in_one_store,
        test_every_refusal_CLASS_reaches_the_queue_including_the_ones_raised_outside_the_gate,
        test_the_record_outlives_the_reaper_that_would_have_eaten_a_debug_one,
        test_the_public_door_and_the_decision_it_wraps_have_one_signature,
        test_the_refusals_are_readable_afterwards_by_the_probe_that_asked_for_them,
        test_this_proof_never_wrote_to_the_live_queue,
        # A RETIRED INTENTION IS NEVER SILENT (ticket a-superseded-intention-is-never-silent).
        test_a_retirement_is_read_off_the_charter_THE_OWNER_READ_ALREADY_OPENED,
        test_a_malformed_retirement_REFUSES_and_never_reads_as_not_retired,
        test_a_boat_riding_a_retired_intention_MAY_NOT_MOVE_FORWARD,
        test_but_it_may_still_RETREAT_because_a_wall_is_not_a_gate,
        test_a_retirement_with_NO_SUCCESSOR_still_refuses_and_says_so,
        test_the_reverse_read_PARTITIONS_the_fleet_and_agrees_with_the_register,
        test_THE_BLIND_COUNT_CANNOT_BE_REMOVED_WITHOUT_THIS_PROOF_GOING_RED,
        test_the_read_face_prints_only_numbers_the_library_returned,
        test_this_build_added_no_tracing_of_its_own,
        # THE PROOF MUST COVER THE BOAT (ticket 1accdc1781aa). Admission first, then the
        # three refusals, then the fork, then the two Law 7 teeth, then the seam read and
        # the store fix the rung stands on.
        test_a_COVERED_boat_crosses_to_PROVED_and_the_rung_is_reachable,
        test_the_rung_fires_ONLY_at_PROVED_so_a_boat_under_construction_still_moves,
        test_an_UNCOVERED_boat_is_REFUSED_at_PROVED_and_every_lack_is_named_in_one_pass,
        test_a_seal_whose_FINGERPRINT_HAS_MOVED_is_refused_at_PROVED,
        test_a_CODE_SEAM_WITH_NO_HOLLOW_READING_is_refused_the_same_as_an_absent_seal,
        test_a_HOLLOW_FILE_in_the_reading_is_refused_and_the_refusal_NAMES_THE_FILE,
        test_an_UNREADABLE_file_is_REFUSED_and_is_never_folded_into_hollow,
        test_a_CONCEPT_PIECE_is_never_asked_for_a_hollow_reading,
        test_a_REFUSAL_RAISES_A_TROUBLE_naming_the_boat_and_the_finding,
        test_a_TROUBLE_STORE_THAT_IS_DOWN_never_turns_a_clean_refusal_into_a_stack_trace,
        test_the_rung_reads_the_TARGET_as_a_system_word_so_lower_case_proved_cannot_walk_past,
        test_proven_by_IS_READ_AS_ONE_OR_MANY_because_a_seam_has_more_than_one_end,
        test_A_HOLLOW_READING_SURVIVES_A_RESEAL_OF_THE_SAME_CODE_AND_ONLY_THAT,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — the clearance gate binds authority (Law 6), proven-space (Law 8), resources, "
          "and the wrapped rules (Law 4) before a cursor moves, and records the crossing "
          "(Law 7) — the harbor clears the move, it never sails it, and it never counts a fleet")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
