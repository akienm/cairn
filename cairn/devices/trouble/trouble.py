"""THE TROUBLE LANE — where a failure that cannot escalate anywhere else goes, and stops.

Akien 2026-07-25, twice, and the second time is the design:

  "a poke into nothing, a message that can't be delivered, these are bugs. nothing should
   fail silently. everything that can't escalate somewhere else should fail to trouble
   tickets until we get no more from the system. it's literally telling you and i how to
   improve it :)"

  "a system alarm is raised. it's not raised again and again, it's count can increment...
   but demanding more attention when there is none to give is not productive. the intention
   for the normal-operating-state is there won't be any active trouble tickets. and it'll be
   a rarity when there is one. but we're a long way from there. we do need to be able to make
   a change and clear the current trouble ticket and start fresh. but once a notifier-ee gets
   one, it stays live until they clear it. and for now, you get them all."

THE TROUBLE TICKET IS THE DAMPER. This is the whole reason the module reads the way it does.
The open question before it was chatter — a predicate flapping across its line raises the
same fault fifty times — and the reflex answer was hysteresis: pick a width, suppress inside
it. That answer needs a NUMBER nobody has measured, and a number set too wide silently eats
real faults. The trouble ticket dissolves the question instead: the second occurrence of a
fault ALREADY KNOWN does not raise anything, it increments a count on the live ticket. There
is no width, because attention — not occurrence — is the scarce thing being rationed, and
attention is already spent the moment the first ticket lands. Fifty flaps become one ticket
that says 50. (Law 1, one level up: the answered question becomes structure.)

WHAT IS DAMPED IS NOTIFICATION, NOT TRUTH (Law 7, both halves). Every occurrence is recorded
— count, first_seen, last_seen, and a bounded tail of the most recent ones, so the resolver
sees the shape of the recurrence. What does NOT repeat is the demand for attention. A record
of truth never collapses; a notification always may.

CLEARING IS THE RECIPIENT'S, AND ONLY THE RECIPIENT'S. "once a notifier-ee gets one, it stays
live until they clear it." Nothing in the system decides on their behalf that a trouble has
gone away — not a timeout, not a quiet period, not a later run that happened to pass. That is
the difference between a trouble lane and a log: a log forgets, a lane holds until a human (or,
later, whatever helps) says the change was made. Clearing is by APPEND — the cleared ticket
keeps its whole occurrence history and gains a resolution; it is never deleted (Law 7).

AND THEN IT STARTS FRESH. "we do need to be able to make a change and clear the current
trouble ticket and start fresh." A fault that recurs AFTER a clear is a NEW ticket at count 1,
not a resurrection of the old one — because the count is the evidence about a specific
attempted fix. A fix that did not hold must be visibly a fix that did not hold; folding the
new occurrences back into the old count would hide exactly that.

WHO IS TOLD — for now, CC gets them all. That is a stopgap and is written down as one:
``DEFAULT_RECIPIENTS``. The notified set is per-recipient because the clear is per-recipient,
so the shape already admits the help Akien expects later ("eventually you'll have help that'll
do that for you") without a redesign — a second recipient is an entry in a list.

THE NORMAL OPERATING STATE IS ZERO. ``live()`` returning empty is the system working, and
that is the horizon this lane is measured against. We are a long way from it, which is the
point: every ticket here is the system telling us how to improve it.

WHERE THE RECORDS LIVE — ``CairnCommons/troubles/``, git-JSON. A trouble is shareable
provenance, and losing it loses knowledge, so it is commons and not a row (the roots table).
The path is injectable so a proof runs on a temp directory it owns.

    python3 cairn/devices/trouble/proofs/test_trouble.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.device import BaseDevice

# The stopgap, written down as one: today CC is told about everything. A second recipient is
# an entry in this list, not a redesign — the notified/cleared sets are already per-recipient.
DEFAULT_RECIPIENTS = ("cc",)

# How many recent occurrences ride on the ticket. The COUNT is exact and unbounded; this is the
# tail that shows the SHAPE of a recurrence (is it flapping? accelerating?) without the ticket
# growing without limit. A first guess against real need, like the projector's window — not a law.
OCCURRENCE_TAIL = 10

LIVE = "OPEN"
CLEARED = "CLEARED"

_SLUG = re.compile(r"[^a-z0-9-]+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TroubleError(Exception):
    """A refusal by the lane's own gate — the trouble lane failing loudly about itself."""


class TroubleDevice(BaseDevice):
    """THE SINGLE DOOR to the trouble lane (Law 6). Raising, incrementing and clearing all go
    through here; nothing else writes a trouble file. The lane's whole value is that a count is
    trustworthy, and a count is only trustworthy if there is one way to increment it."""

    def __init__(self, root: str | os.PathLike | None = None) -> None:
        super().__init__()
        self._root = Path(root) if root else Path.home() / "dev" / "src" / "CairnCommons" / "troubles"

    # --- introspection (Form v0 #2: intention, state, settings) -------------

    @property
    def device_id(self) -> str:
        return "trouble"

    def intention(self) -> dict:
        return {
            "what": "the lane a failure that cannot escalate anywhere else goes to, and stops",
            "why": "nothing fails silently; and demanding attention that has already been "
                   "demanded is not productive — so the ticket counts instead of shouting",
            "normal_operating_state": "live() is EMPTY",
        }

    def state(self) -> dict:
        live = self.live()
        return {
            "live": len(live),
            "at_normal_operating_state": not live,
            "ids": sorted(t["id"] for t in live),
            "root": str(self._root),
        }

    def settings(self) -> dict:
        return {"recipients": list(DEFAULT_RECIPIENTS), "occurrence_tail": OCCURRENCE_TAIL}

    # --- the door -----------------------------------------------------------

    def raise_trouble(self, identity: str, *, why: str, detail: dict | None = None,
                      recipients=None) -> dict:
        """Report a fault. FIRST time: a ticket is written and its recipients are notified.
        EVERY time after, while it is still live: the count increments and NOBODY is notified
        again — the attention was already spent (this is the damping).

        ``identity`` names the DEFECT, not the occurrence — it is what makes the second flap
        the same trouble as the first. ``why`` is required (CP3). ``detail`` is the occurrence's
        own data and rides on the tail; the initial report should carry everything needed to
        resolve it in one pass (I-complete-diagnostic-on-first-pass).

        Returns the outcome, so a caller can tell a raise from an increment without re-reading.
        """
        ident = self._slug(identity)
        if not why:
            raise TroubleError("a trouble carries a why (CP3) — a fault with no reason is not "
                               "a report, it is a shrug")
        existing = self._read(ident)
        stamp = _now()
        occurrence = {"at": stamp, **(detail or {})}

        # Same lean as live(): anything not explicitly CLEARED is still open, so a ticket with a
        # near-miss standing gets its count incremented rather than being silently replaced.
        if existing and existing.get("standing") != CLEARED:
            existing["count"] += 1
            existing["last_seen"] = stamp
            existing["occurrences"] = (existing.get("occurrences", []) + [occurrence])[-OCCURRENCE_TAIL:]
            self._write(ident, existing)
            # NOT notified — deliberately. The record grows; the demand for attention does not.
            # GATE CONTACT (DiagnosticBase): the increment IS still a crossing — a record of
            # truth changed. What the damper rations is NOTIFICATION; a held breadcrumb is a
            # record, not a demand for attention, so it is not damped (Law 7, both halves).
            self.emit("raise_trouble", pointer=ident,
                      values={"outcome": "incremented", "count": existing["count"]})
            return {"outcome": "incremented", "id": ident, "count": existing["count"],
                    "notified": []}

        told = list(recipients if recipients is not None else DEFAULT_RECIPIENTS)
        ticket = {
            "id": ident,
            "standing": LIVE,
            "why": why,
            "count": 1,
            "first_seen": stamp,
            "last_seen": stamp,
            "occurrences": [occurrence],
            # Per-recipient because the CLEAR is per-recipient: it stays live for whoever was
            # told until THEY say the change was made. One name today, more when help arrives.
            "notified": told,
            "cleared_by": [],
            # Set when a prior ticket of the same identity was cleared and the fault came back:
            # the evidence that a specific attempted fix did not hold.
            "recurred_after_clear": (existing or {}).get("resolution") if existing else None,
            "prior_attempts": ((existing or {}).get("prior_attempts", 0) + 1) if existing else 0,
        }
        self._write(ident, ticket)
        # GATE CONTACT (DiagnosticBase): a NEW ticket landed and attention was spent — the
        # lane's first-class crossing. Emitted after the write lands; thin (the ticket on
        # disk is the record of truth; the breadcrumb points at it).
        self.emit("raise_trouble", pointer=ident,
                  values={"outcome": "raised", "count": 1})
        return {"outcome": "raised", "id": ident, "count": 1, "notified": told}

    def clear(self, identity: str, *, by: str, what_changed: str) -> dict:
        """The recipient says the change was made. Nothing else may say it — not a timeout, not
        a later passing run. ``what_changed`` is required: a clear with no change behind it is
        the silent failure this lane exists to remove.

        The ticket is not deleted. It keeps its whole occurrence history and gains a resolution,
        so the next recurrence can point at the fix that did not hold (Law 7 — append, never
        erase). Once every notified recipient has cleared, the ticket leaves ``live()``."""
        ident = self._slug(identity)
        ticket = self._read(ident)
        if not ticket:
            raise TroubleError(f"no trouble {ident!r} to clear — clearing a ticket that was "
                               "never raised would quietly manufacture an all-clear")
        if ticket.get("standing") == CLEARED:
            raise TroubleError(f"trouble {ident!r} is already cleared — a second all-clear "
                               "would overwrite the record of what actually fixed it")
        if not what_changed:
            raise TroubleError("a clear carries what_changed — 'it stopped happening' is not a "
                               "fix, and recording it as one is how a fault comes back unexplained")

        # A pre-template record (the lane's first real files predate the schema) carries no
        # count — live() already leans that way, and a record clear() cannot process is a
        # ticket that can never leave the live list through its own door.
        ticket.setdefault("cleared_by", []).append(
            {"by": by, "at": _now(), "what_changed": what_changed,
             "at_count": ticket.get("count")})
        outstanding = [r for r in ticket.get("notified", [])
                       if r not in {c["by"] for c in ticket["cleared_by"]}]
        if not outstanding:
            ticket["standing"] = CLEARED
            ticket["resolution"] = ticket["cleared_by"][-1]
        self._write(ident, ticket)
        # GATE CONTACT (DiagnosticBase): a recipient said the change was made — the crossing
        # that takes (or moves toward taking) a ticket off the live list. Reads (live/all)
        # emit nothing: no crossing, no state change.
        self.emit("clear", pointer=ident,
                  values={"outcome": "cleared" if not outstanding else "partially_cleared",
                          "standing": ticket["standing"]})
        return {"outcome": "cleared" if not outstanding else "partially_cleared",
                "id": ident, "standing": ticket["standing"], "outstanding": outstanding}

    # --- reading ------------------------------------------------------------

    def live(self) -> list[dict]:
        """The tickets still demanding attention. EMPTY is the normal operating state.

        ONLY AN EXPLICIT ``CLEARED`` TAKES A TICKET OFF THIS LIST. Anything else — a missing
        standing, a typo, prose where a token belongs — counts as LIVE. This is not pedantry:
        the first real file this device ever read said ``"OPEN — reported complete, awaiting
        Akien's ratify"``, and an equality test on ``LIVE`` quietly reported zero troubles with
        an open one on disk. Reading the normal operating state off a near-miss is the silent
        failure this whole lane exists to end, so the default leans the safe way (Law 7)."""
        return [t for t in self.all() if t.get("standing") != CLEARED]

    def all(self) -> list[dict]:
        if not self._root.exists():
            return []
        out = []
        for p in sorted(self._root.glob("*.json")):
            try:
                ticket = json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError as exc:
                # The lane must not go dark because one file is malformed — that would be a
                # silent failure in the very place built to end them.
                out.append({"id": p.stem, "standing": LIVE, "count": 1,
                            "why": f"UNREADABLE TROUBLE FILE: {exc}", "unreadable": True})
                continue
            if isinstance(ticket, dict) and "why" not in ticket:
                # OFF-TEMPLATE, AND SAYING SO IS THE WHOLE POINT (2026-08-12).
                # `the-runtime-spine-has-never-run` carries the fullest why in the store —
                # opened_by, the_claim_under_test, verdict, method, findings, the_map — under
                # none of those names, and the session banner rendered it as
                # "<no why recorded>". That is a reader turning a PRESENT record into an
                # ABSENCE claim: not collapsing an error into a coherent shape (which a
                # presentation surface may do) but MANUFACTURING one (Law 7). The fix belongs
                # here and not in the banner, because what a trouble's why IS belongs to this
                # lane (Law 6) — the banner already refuses to re-derive `live()` for the
                # same reason. Deliberately NOT a fallback key list: guessing which field is
                # really the why would freeze today's two off-template shapes into a schema,
                # and the shapes are the defect, not the vocabulary. The reader is told the
                # record is off-template, what it carries, and where to read it — which is the
                # `notes-store-template-gate-is-prose-not-physics` trouble showing its face at
                # session open instead of hiding behind a manufactured silence.
                ticket = dict(ticket)
                ticket["why"] = (
                    "OFF-TEMPLATE TROUBLE RECORD — the why is almost certainly here, under a "
                    "name this reader does not know, so this line is the READER's limit and "
                    "not the author's silence. It carries: %s. Read it: %s"
                    % (", ".join(k for k in ticket if k != "why"), p))
                ticket["off_template"] = True
            out.append(ticket)
        return out

    # --- the file layer (thin, and the only writer) -------------------------

    def _slug(self, identity: str) -> str:
        s = _SLUG.sub("-", (identity or "").strip().lower()).strip("-")
        if not s:
            raise TroubleError("a trouble carries an identity — the name of the DEFECT, which "
                               "is what makes a second occurrence the same trouble as the first")
        return s

    def _path(self, ident: str) -> Path:
        return self._root / f"{ident}.json"

    def _read(self, ident: str) -> dict | None:
        p = self._path(ident)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return None

    def _write(self, ident: str, ticket: dict) -> None:
        self._root.mkdir(parents=True, exist_ok=True)
        self._path(ident).write_text(
            json.dumps(ticket, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
