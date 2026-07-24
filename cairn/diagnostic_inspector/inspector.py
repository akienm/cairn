"""The diagnostic INSPECTOR — filters a log into FINDINGS, and gets better over time.

THE REMIT (charter, stated by Akien). This inspector's job is to SAVE CC TOKENS exploring an
issue, the same way the prebuild step saves them for coding — the debugging analog of that
pre-processing (Law 1, the cocoon: spend the expensive resolver only on the novel, never on
re-deriving the settled). And to KEEP GETTING BETTER over time: every gap it learns is one
fewer second-exploration forever, so the tokens it saves rise monotonically. Those two
sentences are the whole falsifier — see below.

THREE PARTS OF THE DIAGNOSTIC SURFACE (Akien's factoring):
  - LOGGING — gates emit breadcrumbs (``cairn/base/diagnostic.py``); microsecond-stamped
    records of what crossed. State, so its durable home is instance-space (the ~/.cairn/
    cache-class json log; ``Mailbox`` here is the v0 in-memory stand-in for it — a proof
    fixture, never the runtime home).
  - CALLBACK — when a watched thing happens (a red, a watched gate-contact) a callback FIRES.
    Event, not poll (the shrinking-footprint discipline). It says "inspect now."
  - INSPECTOR — this module. It REACTS to that callback: applies FILTERS to the log and
    produces FINDINGS. It reads; it never emits (Law 6 — that would collapse the
    dumb-breadcrumb / smart-reader split). Filters are selection AT inspection time inside a
    fired run — never a standing scan (that would be the firehose/poll we reject).

FILTERS are just predicates (``predicate(record) -> bool``), conjoined. ``by_pointer`` (the
primary — one item's whole transaction, the complete-first-pass slice) and ``by_gate`` are
built because they have consumers; ``by_time_band`` / ``by_severity`` are filed edges, grown
against need — the abstraction ADMITS them without a query-language built ahead of one.

FINDINGS are the inspector's output, json whose entire audience is CC: the ordered,
isolated transaction slice (every emitted value carried, source never mutated) PLUS the
COMPLETENESS finding — per gate, what this transition-class has LEARNED it must carry vs.
what is present, with any learned-but-absent key surfaced LOUD as a recurrence (Law 7). The
findings are a diagnostic surface (transient, may collapse); the record of truth is the
RESOLUTION CC produces from them, downstream.

GETS BETTER OVER TIME is the ``CompletenessRegistry`` the inspector CARRIES across
inspections (I-learns-its-gates pointed at the diagnostic surface). ``record_miss(gate, key)``
folds a discovered gap into what that class's findings must carry; the next inspection
demands it. A FIRST miss is ``"learned"`` (feed-forward — how completeness grows); an
already-learned key absent again is a ``"recurred"`` — surfaced LOUD in the findings, the
terminal falsifier (the surface failed to save the tokens it had already learned to save).

    python3 cairn/diagnostic_inspector/proofs/test_inspector.py     # exit 0 = green
"""

from __future__ import annotations

import copy
import json
from pathlib import Path


class Mailbox:
    """A diagnostic receiver: answers ``receive_diagnostic`` (the contract
    ``DiagnosticBase.emit`` calls) and accumulates breadcrumbs. The v0 in-memory STAND-IN
    for the instance-space breadcrumb log (~/.cairn/, cache-class) — a proof fixture so an
    emitter → receiver → inspector chain runs end to end, NOT the runtime home (that log is
    a filed edge). The inspector reads the log this exposes via ``records()``."""

    def __init__(self) -> None:
        self._records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self._records.append(record)

    def records(self) -> list[dict]:
        return list(self._records)


class _Filter:
    """A labelled selection predicate over one breadcrumb record. Labelled so the findings
    can echo their own scope (a resolver reads WHAT was filtered without re-deriving it —
    the remit, in miniature). A filter is a thing you compose, not a class to subclass."""

    def __init__(self, label: str, predicate) -> None:
        self.label = label
        self._predicate = predicate

    def __call__(self, record: dict) -> bool:
        return self._predicate(record)

    def __repr__(self) -> str:
        return f"<filter {self.label}>"


def by_pointer(pointer) -> _Filter:
    """THE PRIMARY filter: select one item's whole transaction — the complete-first-pass
    slice. Other pointers never bleed in (Law 6, owned data stays home)."""
    return _Filter(f"pointer={pointer!r}", lambda r: r.get("pointer") == pointer)


def by_gate(gate) -> _Filter:
    """Narrow to contacts at one gate (transition-class) — composes with ``by_pointer`` to
    ask 'this item's contacts at the verify gate'. A real consumer, not built-to-prove."""
    return _Filter(f"gate={gate!r}", lambda r: r.get("gate") == gate)


# Filed edges — the abstraction admits these; build each when a crawl demands it (build-minimal):
#   by_time_band(lo, hi)  — the 6th-decimal stamp is the index; slice a window of the log.
#   by_severity(level)    — once emissions carry severity, triage by it.


class Inspector:
    """Reacts to a callback: applies FILTERS to the log, produces FINDINGS — and carries its
    learned completeness across inspections, so it gets better over time (the remit).

    ``inspect(log, *filters)`` selects the records matching EVERY filter (conjunction),
    orders them by the 6th-decimal stamp (total order, none lost), and returns the findings.
    It deep-copies the slice — the inspector reads, it never mutates its source (Law 6). The
    completeness finding is intrinsic (an inspector always has a registry, even if empty):
    it reports the transaction AND where that transaction falls short of what the class has
    learned it needs.
    """

    def __init__(self, registry: "CompletenessRegistry | None" = None) -> None:
        self._registry = registry if registry is not None else CompletenessRegistry()

    @property
    def registry(self) -> "CompletenessRegistry":
        """The inspector's learned completeness — its memory of what it must carry (the
        'gets better over time' half). Persist it via ``registry.save(path)``."""
        return self._registry

    def inspect(self, log, *filters) -> dict:
        """Filter ``log`` into findings a resolver reads WITHOUT a second exploration."""
        selected = [r for r in log if all(f(r) for f in filters)]
        selected.sort(key=lambda r: (r.get("ts", ""), r.get("us", "")))
        gates = [r.get("gate") for r in selected]
        return {
            "scope": [getattr(f, "label", repr(f)) for f in filters],   # findings self-describe their filter
            "steps": [copy.deepcopy(r) for r in selected],              # deep copy — read, never mutate (Law 6)
            "gates": gates,
            "completeness": self._completeness(selected, gates),
        }

    def _completeness(self, selected, gates) -> dict:
        per_gate: dict = {}
        recurrences: list = []
        for gate in dict.fromkeys(gates):    # unique, first-seen order
            present: set = set()
            for r in selected:
                if r.get("gate") == gate:
                    present |= set((r.get("values") or {}).keys())
            required = self._registry.required(gate)
            missing = required - present
            per_gate[gate] = {
                "required": sorted(required),
                "present": sorted(present),
                "missing": sorted(missing),
            }
            for key in sorted(missing):
                recurrences.append({"gate": gate, "key": key})
        return {
            "complete": not recurrences,
            "per_gate": per_gate,
            "recurrences": recurrences,   # LOUD — a learned gap that recurred (Law 7)
        }

    def record_miss(self, gate, key) -> str:
        """Fold a discovered gap into what this class's findings must carry — how the
        inspector gets better. ``"learned"`` on a first miss (feed-forward), ``"recurred"``
        if it was already learned (the terminal-falsifier signal, Law 1)."""
        return self._registry.record_miss(gate, key)


class CompletenessRegistry:
    """What each transition-class has LEARNED its findings must carry — the inspector's
    memory, keyed by ``gate`` → the set of value-keys a report for that gate must include.

    ``record_miss`` folds in a datum the findings lacked (Law 1: the answered question
    becomes structure). It distinguishes a first miss (``"learned"`` — feed-forward) from a
    recurrence of an already-learned datum (``"recurred"`` — the findings should already have
    carried it). Persistence is injected (a path), proven against a temp; the durable home —
    a commons git-JSON store vs CC's shim when shims land — is a filed edge (ticket horizon).
    """

    def __init__(self, required: dict | None = None) -> None:
        self._required: dict[str, set] = {
            g: set(keys) for g, keys in (required or {}).items()
        }

    def required(self, gate) -> set:
        """The value-keys ``gate``'s findings have learned they must carry (a copy)."""
        return set(self._required.get(gate, set()))

    def record_miss(self, gate, key) -> str:
        """Return ``"learned"`` on a first miss (completeness grows), or ``"recurred"`` if
        ``gate``/``key`` was already learned (told once; being told again is the
        terminal-falsifier signal, Law 1 — a re-derivation of the settled)."""
        cur = self._required.setdefault(gate, set())
        if key in cur:
            return "recurred"
        cur.add(key)
        return "learned"

    def as_dict(self) -> dict:
        """Plain-JSON view (sets → sorted lists) — the on-disk shape."""
        return {g: sorted(keys) for g, keys in sorted(self._required.items())}

    def save(self, path) -> str:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(self.as_dict(), indent=2, sort_keys=True), encoding="utf-8")
        return str(p)

    @classmethod
    def load(cls, path) -> "CompletenessRegistry":
        """Re-read a saved registry; a missing file is an empty registry (nothing learned
        yet), never an error — the loop starts blank and grows."""
        p = Path(path)
        if not p.exists():
            return cls()
        return cls(json.loads(p.read_text(encoding="utf-8")))
