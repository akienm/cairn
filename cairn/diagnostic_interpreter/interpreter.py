"""The diagnostic interpreter — assemble the complete first-pass report, and learn.

DiagnosticBase.emit (``cairn/base/diagnostic.py``) sends home a THIN, microsecond-stamped
breadcrumb at each gate contact — a pointer to the ticket travelling through, never the
ticket itself (Law 6). The intelligence was deliberately left OUT of the emission so it
could live HERE, once (Law 1 — the diagnostic surface's inference compiled in one place,
the ``inference_domain`` move). This module is that one place.

Two halves, exactly as Akien scoped (I-complete-diagnostic-on-first-pass):

  THE REPORT — ``assemble(records, pointer)``. Given a pointer, gather that pointer's
  whole transaction from the breadcrumbs, order it by the 6th-decimal stamp, and trim it
  into a coherent slice a resolver can read WITHOUT a second run. Other pointers never
  bleed in. Pure over stdlib; no disk, no clock — it reads records, it does not emit.

  THE LEARNING-LOOP — ``CompletenessRegistry``. The report is self-teaching. When a
  report proves insufficient — a gap forced a second run to resolve some additional
  point — ``record_miss(gate, key)`` folds that datum into what a report for that
  transition-class must carry, so the same gap never costs a second run again. This is
  I-learns-its-gates pointed at the diagnostic surface: it learns what a report must
  CARRY (a distinct endpoint from the decision-autonomy store in ``learning/``, which
  learns whether CC may ACT — kin, not merged).

The falsifier is a SPECIAL CLASS (the load-bearing subtlety). A forced second-run is not
a refutation — it is the loop firing:

  * FIRST miss of a datum → ``record_miss`` returns ``"learned"``: a feed-forward learning
    signal, expected and welcome, how the report grows toward completeness.
  * The SAME learned datum absent from a later report → surfaced by ``assemble`` in
    ``completeness.recurrences`` with ``complete=False``: the terminal falsifier, LOUD
    (Law 7). The surface was told once and failed to consume its own evidence — a Law 1
    defect (re-deriving the settled). ``record_miss`` called again for it returns
    ``"recurred"``, distinguishing the signal from the re-derivation.

``Mailbox`` is a minimal receiver (the contract DiagnosticBase.emit calls,
``receive_diagnostic``) so an emitter → mailbox → interpreter chain runs end to end. In
the running system HOME is CC's shim; here it is whatever a caller wires (the injected
receiver, same stopgap DiagnosticBase names). The 30-day json log tier and the durable
home for learned completeness are filed edges (ticket horizon), not faked here.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path


class Mailbox:
    """A diagnostic receiver: answers ``receive_diagnostic`` (the contract
    ``DiagnosticBase.emit`` calls) and accumulates the breadcrumbs. The v0 stand-in for
    CC's shim mailbox — in-memory, read via ``records()``. The interpreter crawls what
    lands here."""

    def __init__(self) -> None:
        self._records: list[dict] = []

    def receive_diagnostic(self, record: dict) -> None:
        self._records.append(record)

    def records(self) -> list[dict]:
        return list(self._records)


def assemble(records, pointer, *, registry: "CompletenessRegistry | None" = None) -> dict:
    """Trim the breadcrumbs for ``pointer`` into a coherent first-pass report.

    Gathers exactly the records whose ``pointer`` matches (nothing from other pointers
    bleeds in), orders them by the microsecond stamp (``ts`` then ``us`` — the 6th-decimal
    index that guarantees a total order with none lost), and lists the gates crossed.

    With a ``registry``, the report also carries a ``completeness`` verdict: for each gate,
    the value-keys that transition-class has LEARNED it must carry (``required``) vs those
    actually present. Any learned-required key that is absent is a RECURRENCE — a gap the
    surface was already taught — surfaced LOUD in ``recurrences`` with ``complete=False``
    (the terminal falsifier). No records are mutated; the slice carries every emitted value.
    """
    mine = [r for r in records if r.get("pointer") == pointer]
    mine.sort(key=lambda r: (r.get("ts", ""), r.get("us", "")))
    gates = [r.get("gate") for r in mine]
    report = {
        "pointer": pointer,
        "steps": [copy.deepcopy(r) for r in mine],   # a deep copy — the interpreter reads, never mutates its source (nested values included)
        "gates": gates,
    }
    if registry is not None:
        per_gate: dict = {}
        recurrences: list = []
        for gate in dict.fromkeys(gates):    # unique, first-seen order
            present: set = set()
            for r in mine:
                if r.get("gate") == gate:
                    present |= set((r.get("values") or {}).keys())
            required = registry.required(gate)
            missing = required - present
            per_gate[gate] = {
                "required": sorted(required),
                "present": sorted(present),
                "missing": sorted(missing),
            }
            for key in sorted(missing):
                recurrences.append({"gate": gate, "key": key})
        report["completeness"] = {
            "complete": not recurrences,
            "per_gate": per_gate,
            "recurrences": recurrences,   # LOUD — a learned gap that recurred (Law 7)
        }
    return report


class CompletenessRegistry:
    """What each transition-class has LEARNED its report must carry — the learning-loop's
    memory. Keyed by ``gate`` → the set of value-keys a report for that gate must include.

    ``record_miss`` is how a resolver folds in a datum a report lacked (Law 1: the answered
    question becomes structure). It distinguishes the special-class falsifier's two cases:
    a first miss (``"learned"`` — feed-forward signal) from a recurrence of an
    already-learned datum (``"recurred"`` — the report should already have carried it).

    Persistence is injected (a path), proven against a temp here; the durable home — a
    commons git-JSON store vs CC's shim when shims land — is a filed edge (ticket horizon).
    """

    def __init__(self, required: dict | None = None) -> None:
        self._required: dict[str, set] = {
            g: set(keys) for g, keys in (required or {}).items()
        }

    def required(self, gate) -> set:
        """The value-keys ``gate``'s report has learned it must carry (a copy)."""
        return set(self._required.get(gate, set()))

    def record_miss(self, gate, key) -> str:
        """Fold a discovered miss into ``gate``'s required set.

        Returns ``"learned"`` on a first miss (the feed-forward learning signal — this is
        how completeness grows), or ``"recurred"`` if ``gate``/``key`` was already learned
        (the surface was told once; being told again is the terminal-falsifier signal,
        Law 1 — a re-derivation of the settled)."""
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
