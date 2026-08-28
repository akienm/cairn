"""learning_block — the shared gate machinery every Learning Block imports.

The five organs, built once (the single-door move — skills declare contracts,
they do not build refusal):

  DOOR     check_input / fire_door — refuses insufficient shape with EVERY lack
           named on the first pass; the refusal itself is traced.
  TRACE    write_trace / read_trace — every firing recorded, green included,
           consumer-typed at write; debug records expire at 30 days, swept by
           the NEXT WRITE (the write is the event; no clock, nothing resident).
  FINDING  emit_finding — the exit-time bullet list, every bullet stratum-tagged
           code|tree|hex; hex bullets exist ONLY via an injected callable (the
           seam toward inference_domain — provenance cannot be invented).
  VERDICT  record_verdict — Akien's approve/disprove/question captured as a
           gate-record CONFORMING to CairnCommons/learning/'s v0 format; the
           sole write path into that store from this component. Approvals are
           recorded with the same fidelity as disprovals — the denominator.
  DIAL     dial — a pure projection over trace + verdict records: firings,
           send-backs, approvals, disproves, questions, match rate. Computed on
           read, stores nothing, mutates nothing.

Roots are injectable for proofs: CAIRN_LB_TRACE_ROOT (traces; default
~/.cairn/devices/learning_block/0/traces — instance-space, never git) and
CAIRN_ROOTS_PARENT (commons discovery; verdicts land in
<parent>/CairnCommons/learning/records — knowledge, git).
"""

from __future__ import annotations

import json
import os
import uuid
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

from cairn.tools.gate import gate
from cairn.tools.base.address import instance_path

CONSUMERS = ("debug", "training", "tree-primary")
STRATA = ("code", "tree", "hex")
DEBUG_TTL_DAYS = 30

SIGNALS = {
    # signal -> (evidence per the learning store's v0 vocabulary, confidence_move).
    # Asymmetric BY THE STORE'S OWN GUARDRAIL: counter-evidence lowers faster than
    # confirmation raises.
    "approve":  ("confirmation", "+ slow (confirmed prediction; the denominator grows)"),
    "disprove": ("correction",   "- fast (surprise — counter-evidence lowers faster than confirmation raises)"),
    "question": ("weak",         "0 (a question is not yet evidence; silence is never approval)"),
}


class DoorRefused(ValueError):
    """Insufficient input at a block's door. Carries EVERY lack, named — and the
    message renders each as ``field: why`` so a caller that only prints ``str(exc)``
    hands the executor the remedy, not a list of names to go look up (ticket
    chart-doors-refuse-in-one-pass, folding opus-pass rank 7: the whys used to ride
    only ``.lacks`` and were dropped by exactly the callers who needed them most)."""

    def __init__(self, block: str, lacks: list[dict]):
        self.block, self.lacks = block, lacks
        rendered = "; ".join(f"{l['field']}: {l['why']}" for l in lacks)
        super().__init__(f"door refused for block {block!r} — {len(lacks)} lack(s), "
                         f"all named on this first pass: {rendered}")


class TraceRefused(ValueError):
    """A trace write with no honest consumer. No consumer named, no trace written."""


class FindingRefused(ValueError):
    """A bullet without provenance. An untagged adjudication cannot be delegated."""


class VerdictRefused(ValueError):
    """A verdict that would not conform to the learning store's v0 record format."""


# ── roots ────────────────────────────────────────────────────────────────────

def trace_root() -> Path:
    env = os.environ.get("CAIRN_LB_TRACE_ROOT")
    if env:
        return Path(env)
    return instance_path("learning_block", 0) / "traces"


def learning_records_dir() -> Path:
    env = os.environ.get("CAIRN_ROOTS_PARENT")
    parent = Path(env) if env else Path(__file__).resolve().parents[3].parent
    return parent / "CairnCommons" / "learning" / "records"


def _now(now: datetime | None) -> datetime:
    return now if now is not None else datetime.now(timezone.utc)


# ── TRACE — the substrate every organ records through ────────────────────────

def write_trace(block: str, event: str, consumer: str, data: dict, *,
                now: datetime | None = None, root: Path | None = None) -> dict:
    """One firing -> one durable record. Green or red, same fidelity.

    Refuses a missing/unknown consumer (no consumer named, no trace written).
    After appending, sweeps expired DEBUG records from this block's file —
    write-fired, amortized on the path that was already open; never a clock.
    """
    if not block or not str(block).strip():
        raise TraceRefused("trace refused — a record must name its block")
    if not event or not str(event).strip():
        raise TraceRefused("trace refused — a record must name its event")
    if consumer not in CONSUMERS:
        raise TraceRefused(
            f"trace refused — consumer {consumer!r} is not one of {CONSUMERS}: "
            "who reads this trace, and why? No consumer named, no trace written.")
    when = _now(now)
    record = {
        "id": uuid.uuid4().hex[:12],
        "when": when.isoformat(),
        "block": block,
        "event": event,
        "consumer": consumer,
        "data": data,
    }
    base = root if root is not None else trace_root()
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{block}.jsonl"
    kept: list[str] = []
    cutoff = when - timedelta(days=DEBUG_TTL_DAYS)
    if path.exists():
        for line in path.read_text().splitlines():
            if not line.strip():
                continue
            old = json.loads(line)
            if old.get("consumer") == "debug" and datetime.fromisoformat(old["when"]) < cutoff:
                continue                      # expired into nothingness, at the write
            kept.append(line)
    kept.append(json.dumps(record, sort_keys=True))
    tmp = path.with_suffix(".tmp")
    tmp.write_text("\n".join(kept) + "\n")
    os.replace(tmp, path)
    return record


@contextmanager
def traced(block: str, op: str, *, consumer: str = "training",
           now: datetime | None = None, root: Path | None = None):
    """THE TRACE WIRE — one line retrofits an existing door (deploy pass, approved
    2026-08-01): wrap the door's work; a clean exit traces ``door_pass``, an
    exception traces ``send_back`` with the refusal named as the lack, then
    re-raises untouched. The dial counts both as firings.

    Consumer defaults to ``training`` deliberately: greens are the denominator
    (the Leah rule) and must not expire the way debug records do — a decaying
    denominator would silently bend every rate the dial reports.
    """
    try:
        yield
    except BaseException as exc:
        write_trace(block, "send_back", consumer,
                    {"op": op, "lacks": [f"{type(exc).__name__}: {exc}"]},
                    now=now, root=root)
        raise
    write_trace(block, "door_pass", consumer, {"op": op}, now=now, root=root)


def read_trace(block: str, *, root: Path | None = None) -> list[dict]:
    """Pure read; never mutates (no touch-marks — the dial must not disturb what it counts)."""
    base = root if root is not None else trace_root()
    path = base / f"{block}.jsonl"
    if not path.exists():
        return []
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


# ── DOOR — send-back at all steps ────────────────────────────────────────────

def declare_contract(block: str, requires: dict[str, str]) -> dict:
    """A block's input contract: field -> why it is required. The why is forced
    (a lack that cannot say why it matters cannot be conformed to)."""
    if not block or not block.strip():
        raise DoorRefused("?", [{"field": "block", "why": "a contract must name its block"}])
    hollow = [f for f, why in requires.items() if not str(why).strip()]
    if hollow:
        raise DoorRefused(block, [{"field": f, "why": "a required field must say WHY it is required"}
                                  for f in hollow])
    return {"block": block, "requires": dict(requires)}


def inspect_input(contract: dict, payload: dict,
                  extra_lacks: list[dict] | None = None,
                  extra_record: list[dict] | None = None) -> list[dict]:
    """THE PROOF RECORD this door opens on: one entry per REQUIRED FIELD the contract
    declares, EXPECTED beside ACTUAL, passes included (Akien, 2026-08-13: "EVERYTHING
    ALWAYS PROVED AND LISTING WHAT IT PROVED ... SAME PATTERN EVERYWHERE").

    Why the record and not the lack list: an empty lack list was the same bytes whether
    every declared field arrived, or the contract declared nothing, or ``requires`` was
    quietly emptied upstream. The record's LENGTH is the contract's size, so a field that
    stops being required makes it SHORTER — visible — rather than cleaner.

    AN EMPTY COLLECTION IS A LACK (added 2026-08-01, ticket intent-becomes-a-learning-block).
    ``bullets: []`` is not a bullet list — it is the *absence* of one wearing the field's
    name, and without this it sailed through the door as "present". Found while wiring the
    first skill onto the primitive: the alternative was a second check beside ``fire_door``,
    which would have made the door two doors (Law 6). Fixing the organ keeps it one.

    THE JUDGE ENTRY IS GUARDED, AND THE GUARD IS THE POINT. ``extra_lacks=None`` means no
    semantic judge ran, so no entry is appended — a check that did not run is ABSENT, not
    passed. ``extra_lacks=[]`` means a judge RAN and found nothing, which is a different
    fact and gets an entry that says so. That distinction is unavailable to the judges in
    cairn/machines/build_inspector (ticket a-judge-declares-its-attendance); here the
    caller hands it over for free, so it is recorded.
    """
    record = []
    for field, why in contract["requires"].items():
        value = payload.get(field)
        empty = (
            value is None
            or (isinstance(value, str) and not value.strip())
            or (isinstance(value, (list, tuple, dict, set)) and not value)
        )
        record.append(gate.proved(
            identity="required_field_arrived:%s" % field,
            location="%s.requires.%s" % (contract.get("block", "?"), field),
            code="learning_block.py:inspect_input",
            source="learning_block.door",
            expected="present and non-empty",
            actual="absent or empty" if empty else "present and non-empty",
            lacks=[{"field": field, "why": why}] if empty else [],
            why=why))

    if extra_record is not None:
        # THE CALLER ALREADY PROVED ITS OWN LANES, so they ride the ONE record verbatim
        # rather than being flattened into the aggregate below. A caller with two lanes
        # (skill_block: the semantic judge AND the exit vocabulary) collapsed into one
        # entry could not say which of them ran — and its exit lane is GUARDED, so
        # "collapsed" and "skipped" were the same bytes. Entries in, entries out: the
        # refusal's lacks are still derived from this one record, never a second walk.
        assert extra_lacks is None, (
            "extra_record and extra_lacks are two mouths for one question — hand entries "
            "or hand lacks, and the lacks are read back out of the entries")
        record.extend(extra_record)
    elif extra_lacks is not None:
        extra = list(extra_lacks)
        record.append(gate.proved(
            identity="the_callers_judge_finds_nothing",
            location=contract.get("block", "?"),
            code="learning_block.py:inspect_input",
            source="learning_block.door",
            expected=[], actual=[l.get("field", "?") for l in extra],
            lacks=extra))
    return record


def check_input(contract: dict, payload: dict) -> list[dict]:
    """Every lack, in one pass. A dribbled refusal costs the sender a round-trip per field.

    A VIEW OVER ``inspect_input``, DERIVED AND NEVER PARALLEL — two mouths for one
    question is how a door and the refusal it raises come to disagree about what was
    missing.
    """
    return [lack for entry in inspect_input(contract, payload)
            if not gate.passed(entry) for lack in entry["values"]["lacks"]]


def fire_door(contract: dict, payload: dict, *,
              now: datetime | None = None, root: Path | None = None,
              extra_lacks: list[dict] | None = None,
              extra_record: list[dict] | None = None,
              judge: str | None = None) -> dict:
    """The gate at the input. Conforming -> traced pass. Insufficient -> the
    send-back is TRACED (with every lack) and then raised. Both paths leave a
    record — the refusal rate is measurable or the gate is vacuous.

    ``extra_lacks`` are lacks the caller's own SEMANTIC judge already found. They ride
    the same refusal rather than a second one, because two doors raising separately
    about one firing is two doors — the caller would then have to remember to call
    both, which is precisely the strictness-depends-on-the-entrance defect. Flat lacks
    come first: absence is the contract's finding, and a judge only speaks about fields
    that are present.

    ``extra_record`` is the same seam one rung up: a caller that already PROVED its own
    lanes hands the entries over and they ride this record whole, so a lane it guarded
    stays visibly absent instead of collapsing into one aggregate.
    """
    block = contract["block"]
    record = inspect_input(contract, payload, extra_lacks, extra_record)
    lacks = [lack for entry in record if not gate.passed(entry)
             for lack in entry["values"]["lacks"]]
    # THE RECORD RIDES BOTH TRACES, and the pass side is the half that was missing. A
    # door_pass used to say only which fields ARRIVED; it could not say which checks
    # RAN, so a contract quietly emptied upstream wrote the same triumphant line as a
    # contract fully satisfied. The trace is a record of truth (Law 7) and now carries
    # what was proved, not only that nothing complained.
    data = {"record": record, "checks_proved": len(record),
            "payload_fields": sorted(payload.keys())}
    if judge:
        # WHICH judge stood at this door. A record that cannot name its judge cannot be
        # read back as evidence about that judge — and the judges are the thing that
        # learns. It rides BOTH ways now: naming the judge only when it objected made
        # the trace corpus a record of failures wearing a record of firings' clothes.
        data["judge"] = judge
    if lacks:
        write_trace(block, "send_back", "training", dict(data, lacks=lacks),
                    now=now, root=root)
        raise DoorRefused(block, lacks)
    return write_trace(block, "door_pass", "training", data, now=now, root=root)


# ── FINDING — the bullet list the gate reads ─────────────────────────────────

def emit_finding(block: str, bullets: list[dict], *,
                 hex_source=None, subject: str | None = None,
                 now: datetime | None = None,
                 root: Path | None = None) -> dict:
    """The exit-time finding. Caller bullets carry stratum code|tree only; hex
    bullets are MINTED HERE from the injected callable (the seam toward
    inference_domain) — a hand-authored 'hex' would be invented provenance."""
    checked: list[dict] = []
    for i, b in enumerate(bullets):
        text = b.get("text", "")
        stratum = b.get("stratum")
        if not str(text).strip():
            raise FindingRefused(f"finding refused — bullet {i} has no text")
        if stratum not in STRATA:
            raise FindingRefused(
                f"finding refused — bullet {i} ({text[:40]!r}) carries stratum {stratum!r}, "
                f"not one of {STRATA}: provenance is what makes delegation adjudicable")
        if stratum == "hex":
            raise FindingRefused(
                f"finding refused — bullet {i} ({text[:40]!r}) claims stratum 'hex' by hand; "
                "hex bullets exist only via the injected hex_source (invented provenance)")
        checked.append({"text": str(text), "stratum": stratum})
    if hex_source is not None:
        for text in hex_source():
            checked.append({"text": str(text), "stratum": "hex"})
    data: dict = {"bullets": checked}
    if subject and str(subject).strip():
        data["subject"] = str(subject).strip()
    return write_trace(block, "finding", "training", data,
                       now=now, root=root)


# ── VERDICT — Akien's gate act becomes a training pair ───────────────────────

def record_verdict(gate: str, finding_record: dict, signal: str, verbatim: str, *,
                   session: str, note: str = "",
                   now: datetime | None = None,
                   records_dir: Path | None = None,
                   trace_dir: Path | None = None) -> Path:
    """One gate act -> one v0 gate-record in CairnCommons/learning/ (the store's
    ratified shape: {session, note, records:[...]} with the v0 fields) — and one
    trace record so the dial can count without opening the commons.

    THE SOLE WRITE PATH into learning/ from this component. An approve is
    recorded with the same fidelity as a disprove: greens are the denominator.
    """
    if signal not in SIGNALS:
        raise VerdictRefused(f"verdict refused — signal {signal!r} is not one of "
                             f"{tuple(SIGNALS)} (approve / disprove / question)")
    bullets = (finding_record or {}).get("data", {}).get("bullets")
    if not bullets:
        raise VerdictRefused(
            "verdict refused — no finding context: an unlabeled training pair teaches "
            "nothing (the verdict must carry the bullet list it judged)")
    if not str(verbatim).strip():
        raise VerdictRefused("verdict refused — the signal carries Akien's words or it is "
                             "CC's keystroke wearing his act (the ruling-gate lesson)")
    when = _now(now)
    evidence, confidence_move = SIGNALS[signal]
    record = {
        "id": f"lb-{when.strftime('%Y%m%d')}-{uuid.uuid4().hex[:8]}",
        "date": when.date().isoformat(),
        "session": session,
        "gate": gate,
        "decision": {"finding_id": finding_record.get("id"), "bullets": bullets},
        "signal": {"kind": signal, "verbatim": verbatim},
        "evidence": evidence,
        "ceiling": False,
        "confidence_move": confidence_move,
        "note": note or f"learning_block gate act on {gate}",
        "provenance": f"learning_block.record_verdict, finding {finding_record.get('id')}",
    }
    base = records_dir if records_dir is not None else learning_records_dir()
    base.mkdir(parents=True, exist_ok=True)
    path = base / f"{when.date().isoformat()}-learning-block.json"
    if path.exists():
        doc = json.loads(path.read_text())
    else:
        doc = {"session": session,
               "note": "gate-records written by cairn/machines/learning_block (the sole writer here)",
               "records": []}
    doc["records"].append(record)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(doc, indent=2, ensure_ascii=False) + "\n")
    os.replace(tmp, path)
    write_trace(gate, "verdict", "training",
                {"signal": signal, "finding_id": finding_record.get("id"),
                 "record_id": record["id"]},
                now=now, root=trace_dir)
    return path


# ── DIAL — the numbers Akien reads to delegate ───────────────────────────────

def dial(block: str, *, root: Path | None = None) -> dict:
    """A pure projection from the trace: counts + match rate. No stored state,
    no cache, no write — re-derived on every read so it cannot drift from the
    record it summarizes. match_rate is approvals/(approvals+disproves): how
    often the finding survived Akien's gate — None until a verdict exists."""
    counts = {"firings": 0, "send_backs": 0, "door_passes": 0, "findings": 0,
              "approvals": 0, "disproves": 0, "questions": 0}
    for rec in read_trace(block, root=root):
        event = rec.get("event")
        if event in ("door_pass", "send_back"):
            counts["firings"] += 1
            counts["send_backs" if event == "send_back" else "door_passes"] += 1
        elif event == "finding":
            counts["findings"] += 1
        elif event == "verdict":
            kind = rec.get("data", {}).get("signal")
            if kind == "approve":
                counts["approvals"] += 1
            elif kind == "disprove":
                counts["disproves"] += 1
            elif kind == "question":
                counts["questions"] += 1
    judged = counts["approvals"] + counts["disproves"]
    counts["match_rate"] = (counts["approvals"] / judged) if judged else None
    return counts


# ── THE GATE QUEUE — what stands awaiting a verdict ──────────────────────────

def pending_findings(gate: str | None = None, *, root: Path | None = None) -> list[dict]:
    """Every finding no approve/disprove has answered, oldest first.

    The pendingness rule (settled at the 2026-08-01 recordverdict chart): a
    QUESTION does not clear a finding — a question is the gate owner asking,
    not disposing, so the finding stays at the gate until an approve or
    disprove names its id. Pure read, the dial's own law: no write, no sweep,
    no mutation — session open and the bare command may call this freely.
    """
    base = root if root is not None else trace_root()
    if not base.is_dir():
        return []
    findings: list[dict] = []
    answered: set[str] = set()
    for path in sorted(base.glob("*.jsonl")):
        for rec in read_trace(path.stem, root=base):
            event = rec.get("event")
            if event == "finding":
                findings.append(rec)
            elif event == "verdict":
                data = rec.get("data") or {}
                if data.get("signal") in ("approve", "disprove") and data.get("finding_id"):
                    answered.add(data["finding_id"])
    pend = [f for f in findings if f.get("id") not in answered]
    if gate is not None:
        pend = [f for f in pend if f.get("block") == gate]
    pend.sort(key=lambda r: str(r.get("when", "")))
    return pend


def answered_finding_ids(*, root: Path | None = None) -> set[str]:
    """Every finding ID that has an approve or disprove verdict — the set
    pending_findings subtracts from. Extracted so the berth sweep can ask
    'is this finding settled?' without re-deriving the full pending list."""
    base = root if root is not None else trace_root()
    if not base.is_dir():
        return set()
    answered: set[str] = set()
    for path in sorted(base.glob("*.jsonl")):
        for rec in read_trace(path.stem, root=base):
            if rec.get("event") == "verdict":
                data = rec.get("data") or {}
                if data.get("signal") in ("approve", "disprove") and data.get("finding_id"):
                    answered.add(data["finding_id"])
    return answered
