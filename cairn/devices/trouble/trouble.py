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

WHERE THE RECORDS LIVE — ``store_root()``: ``log_path('cairn', 0)/troubletickets``
(ticket 4ddc9df3369e). Akien 2026-10-11: "trouble tickets are a system alarm, and the ticket
itself is of no use once it's resolved. as such, trouble tickets are logging artifacts ... so
they live in .cairn/logs/cairn/troubletickets and as part of the logging tree, all elemets over
30 days old are deleted as part of the cairn device sleep cycle." The ``0`` is the instance
segment, which is never optional. Until 2026-10-12 the store was ``CairnCommons/troubles/``;
its last committed state is in that repo's history.

A TROUBLE'S LOCATION IS ITS LIVENESS. A file at the top of the store is live; clearing moves it
into ``cleared/``; a recurrence moves it back. No field is read to decide it, because two state
vocabularies once made CC read the wrong one. Each ticket carries the development tickets'
fields under the ``trouble`` node class (``CairnCommons/node_classes/trouble.json``,
OPEN -> CLEARED): born red, green when cleared. The path is injectable so a proof runs on a
temp directory it owns.

    python3 cairn/devices/trouble/proofs/test_trouble.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

from cairn.tools.base.address import log_path
from cairn.tools.base.device import BaseDevice
from cairn.tools.system_word import fold

# The stopgap, written down as one: today CC is told about everything. A second recipient is
# an entry in this list, not a redesign — the notified/cleared sets are already per-recipient.
DEFAULT_RECIPIENTS = ("cc",)
# The operators (ticket 1c1b18bac2eb). Akien 2026-10-11: "tickets announce themselves to the
# operator, and because of how you and i work together, for that statement you and i are both
# operators." A clear whose MEASURED hand is one of these closes the trouble whichever of them
# was notified; the ``by`` word alone never does (D2).
OPERATORS = ("akien", "cc")

# How many recent occurrences ride on the ticket. The COUNT is exact and unbounded; this is the
# tail that shows the SHAPE of a recurrence (is it flapping? accelerating?) without the ticket
# growing without limit. A first guess against real need, like the projector's window — not a law.
OCCURRENCE_TAIL = 10

CLEARED = "CLEARED"

# The development-ticket fields a trouble carries (ticket 4ddc9df3369e): same names, its own
# class. parse_workflow reads both cursors; load_class_def("trouble") loads the class.
NODE_CLASS = "trouble"
SCHEMA_VERSION = "trouble-v1"
WORKFLOW_OPEN = "trouble@v1: [OPEN] -> CLEARED"
WORKFLOW_CLEARED = "trouble@v1: OPEN -> [CLEARED]"


# The store's address, its summary row and its listing live in the tool trouble publishes
# (tools/store/, ticket ee04bb869795), so a reader outside the component reads the files
# without importing this module's fold path — and never asks over the bus. Re-exported here.
from cairn.devices.trouble.tools.store import store as _store  # noqa: E402
from cairn.devices.trouble.tools.store.store import (  # noqa: E402,F401
    CLEARED_DIR, LIVE, LIVE_SUMMARY_KEYS, store_root)

_SLUG = re.compile(r"[^a-z0-9-]+")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class TroubleError(Exception):
    """A refusal by the lane's own gate — the trouble lane failing loudly about itself."""


class TroubleDevice(BaseDevice):
    """THE SINGLE DOOR to the trouble lane (Law 6). Raising, incrementing and clearing all go
    through here; nothing else writes a trouble file. The lane's whole value is that a count is
    trustworthy, and a count is only trustworthy if there is one way to increment it."""

    def __init__(self, root: str | os.PathLike | None = None, *,
                 roots: dict | None = None) -> None:
        super().__init__()
        self._root = Path(root) if root else store_root(roots)
        # WHICH LOG HOMES A READ FOLDS (ticket 3c62020b0d88). The live store folds the live
        # log homes; a store at a scratch root folds only the homes its caller names. A
        # scratch store with no roots folds nothing — folding the live homes into it would
        # advance the LIVE watermark past emissions the live store never received.
        self._roots = roots
        self._folds = root is None or roots is not None

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

    # --- the verbs: how everyone else reaches this lane ---------------------

    def declared_verbs(self) -> dict:
        """No verbs of the lane's own — and both absences are the design.

        There is deliberately NO ``raise`` verb. Raising is inherited from ``DiagnosticBase``
        and needs no addressee, no bus and no running recipient: it is one file in the
        raiser's own log home, which is what lets a fault be reported by a process that
        cannot reach anybody. Putting a raise verb here would give the same act a second path
        — one that fails exactly when the system is unhealthy enough to be worth reporting.

        And since ticket ee04bb869795 (2026-10-18) there is no ``live``, ``clear`` or
        ``clears`` either. Akien: "TROUBLE TICKETS ARE A FILE ARTIFACT IN THE LOGGING TREE" /
        "THERE SHOULD BE NO ROWS FOR TROUBLE TICKETS." Every reply to those verbs stood as a
        bus row (195 ``live`` replies, ~325 KB, and 372 ``clears`` replies, measured that
        day). A reader reads the files through the tool trouble publishes
        (``tools/store/``); a clear is a ``clear_trouble`` emission this lane folds, which is
        what every other clearer already did."""
        return super().declared_verbs()

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

        # Location decides, as in live(): a file at the top of the store is open whatever its
        # standing field says, so its count increments rather than being silently replaced.
        if existing and self._path(ident).exists():
            existing["count"] = (existing.get("count") or 0) + 1
            existing.setdefault("node_class", NODE_CLASS)
            existing.setdefault("schema_version", SCHEMA_VERSION)
            existing["workflow_and_state"] = WORKFLOW_OPEN
            existing["last_seen"] = stamp
            existing["occurrences"] = (existing.get("occurrences", []) + [occurrence])[-OCCURRENCE_TAIL:]
            self._write(ident, existing, verb="raise",
                        why=f"recurrence #{existing['count']} of {ident}")
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
            # A recurrence keeps the clears that did not hold: the fix's record rides back to
            # the top with it, and a hand that taught from it stays on the record.
            "cleared_by": list((existing or {}).get("cleared_by") or []),
            # Set when a prior ticket of the same identity was cleared and the fault came back:
            # the evidence that a specific attempted fix did not hold.
            "recurred_after_clear": (existing or {}).get("resolution") if existing else None,
            "prior_attempts": ((existing or {}).get("prior_attempts", 0) + 1) if existing else 0,
            "node_class": NODE_CLASS,
            "schema_version": SCHEMA_VERSION,
            "workflow_and_state": WORKFLOW_OPEN,
        }
        self._write(ident, ticket, verb="raise", why=f"raised: {why}"[:200])
        if existing:
            self._drop(self._cleared_path(ident), why=f"{ident} recurred after a clear")
        # GATE CONTACT (DiagnosticBase): a NEW ticket landed and attention was spent — the
        # lane's first-class crossing. Emitted after the write lands; thin (the ticket on
        # disk is the record of truth; the breadcrumb points at it).
        self.emit("raise_trouble", pointer=ident,
                  values={"outcome": "raised", "count": 1})
        return {"outcome": "raised", "id": ident, "count": 1, "notified": told}

    def clear(self, identity: str, *, by: str, what_changed: str, hand: dict | None = None) -> dict:
        """The recipient says the change was made. Nothing else may say it — not a timeout, not
        a later passing run. ``what_changed`` is required: a clear with no change behind it is
        the silent failure this lane exists to remove.

        The ticket is not deleted. It keeps its whole occurrence history and gains a resolution,
        so the next recurrence can point at the fix that did not hold (Law 7 — append, never
        erase). Once every notified recipient has cleared, the ticket leaves ``live()`` — or at
        once, when ``hand`` (the clearer's measured hand, c2172127d7a4) is an operator's
        (ticket 1c1b18bac2eb; Akien 2026-10-11: "you and i are both operators")."""
        ident = self._slug(identity)
        ticket = self._read(ident)
        if not ticket:
            raise TroubleError(f"no trouble {ident!r} to clear — clearing a ticket that was "
                               "never raised would quietly manufacture an all-clear")
        if not self._path(ident).exists():          # found only in cleared/ (4ddc9df3369e)
            raise TroubleError(f"trouble {ident!r} is already cleared — a second all-clear "
                               "would overwrite the record of what actually fixed it")
        if not what_changed:
            raise TroubleError("a clear carries what_changed — 'it stopped happening' is not a "
                               "fix, and recording it as one is how a fault comes back unexplained")

        # A pre-template record (the lane's first real files predate the schema) carries no
        # count — live() already leans that way, and a record clear() cannot process is a
        # ticket that can never leave the live list through its own door.
        entry = {"by": by, "at": _now(), "what_changed": what_changed,
                 "at_count": ticket.get("count")}
        if hand is not None:
            entry["hand"] = hand
        ticket.setdefault("cleared_by", []).append(entry)
        # THE RECIPIENT NAME IS A SYSTEM WORD (ruling 2026-09-07,
        # 2026-09-07-system-words-are-case-insensitive-when-akien-types-them). It arrives from
        # ``cairn trouble clear --by <who>`` — a token his fingers produce — and the notified
        # set is written by code, so the two spellings meet here and NOWHERE else. A byte
        # compare made ``--by CC`` against a notified ``cc`` read "partially_cleared, now
        # OPEN": the trouble is fixed, the clear is on the record, and it never leaves the
        # live list — the exact failure the ruling was made of, in the one place where a
        # cleared fault would sit in the inbox forever. Measured 2026-09-09 on
        # clearance-gate-checks-one-proof-while-the-record-names-many.
        _cleared = {fold(c["by"]) for c in ticket["cleared_by"]}
        outstanding = [r for r in ticket.get("notified", [])
                       if fold(r) not in _cleared]
        if isinstance(hand, dict) and fold(hand.get("class") or "") in OPERATORS:
            outstanding = []    # an operator's measured hand closes it (1c1b18bac2eb, D1/D2)
        why_clear = f"cleared by {by}: {what_changed}"[:200]
        if not outstanding:
            ticket["standing"] = CLEARED
            ticket["resolution"] = ticket["cleared_by"][-1]
            ticket.setdefault("node_class", NODE_CLASS)
            ticket.setdefault("schema_version", SCHEMA_VERSION)
            ticket["workflow_and_state"] = WORKFLOW_CLEARED
            # The move IS the clear: written into cleared/, then gone from the top.
            self._write(ident, ticket, verb="clear", why=why_clear,
                        where=self._cleared_path(ident))
            self._drop(self._path(ident), why=why_clear)
        else:
            self._write(ident, ticket, verb="clear", why=why_clear)
        # GATE CONTACT (DiagnosticBase): a recipient said the change was made — the crossing
        # that takes (or moves toward taking) a ticket off the live list. Reads (live/all)
        # emit nothing: no crossing, no state change.
        self.emit("clear", pointer=ident,
                  values={"outcome": "cleared" if not outstanding else "partially_cleared",
                          "standing": ticket["standing"]})
        return {"outcome": "cleared" if not outstanding else "partially_cleared",
                "id": ident, "standing": ticket["standing"], "outstanding": outstanding}

    def amend(self, identity: str, *, by: str, correction: str) -> dict:
        """A CORRECTION appended to a clear that carried a false statement.

        The false statement stays (Law 7 — permanent in the record of truth). The
        correction stands beside it so a reader of the original sees both. This is
        NOT a second clear — it does not change standing, does not re-resolve, and
        does not require the ticket to be live. It requires the ticket to HAVE a
        cleared_by entry, because amending a record that was never cleared is
        amending nothing.

        The shape mirrors validation_store's verdict_change: a changed verdict
        announced before the replace lands. Here the replace is the append."""
        ident = self._slug(identity)
        ticket = self._read(ident)
        if not ticket:
            raise TroubleError(f"no trouble {ident!r} to amend")
        if not ticket.get("cleared_by"):
            raise TroubleError(f"trouble {ident!r} has no cleared_by entry to amend — "
                               "a correction without an original is not an amendment")
        if not correction:
            raise TroubleError("an amendment carries a correction — an empty correction "
                               "is a change that says nothing changed")

        ticket["cleared_by"].append(
            {"amendment": True, "by": by, "at": _now(), "correction": correction})
        where = self._path(ident) if self._path(ident).exists() else self._cleared_path(ident)
        self._write(ident, ticket, verb="clear", why=f"amended by {by}: {correction}"[:200],
                    where=where)
        self.emit("amend", pointer=ident,
                  values={"outcome": "amended", "standing": ticket.get("standing")})
        return {"outcome": "amended", "id": ident, "standing": ticket.get("standing")}

    # --- reading ------------------------------------------------------------

    def live(self) -> list[dict]:
        """The tickets still demanding attention. EMPTY is the normal operating state.

        THE TOP OF THE STORE IS THE LIST, AND NO FIELD IS READ (ticket 4ddc9df3369e). A file
        there is live whatever its standing says; only the clear's move into ``cleared/``
        takes it off. The field test this replaced leaned the safe way for the same reason
        (the first real file said ``"OPEN — reported complete, awaiting Akien's ratify"``);
        location leans that way by construction (Law 7)."""
        self.fold_pending()
        return self._listing(self._root)

    def fold_pending(self) -> dict | None:
        """Fold what is pending before a read answers (ticket 3c62020b0d88).

        A read never fails because a fold did: the fold's fault goes to stderr and the read
        answers from the store as it stands (Law 7 — loud at the diagnostic surface)."""
        if not self._folds:
            return None
        from cairn.devices.trouble.shim import fold_pending
        try:
            return fold_pending(self, self._roots)
        except Exception as exc:  # noqa: BLE001 — the read still answers
            print(f"trouble: fold before read failed: {type(exc).__name__}: {exc}",
                  file=sys.stderr)
            return {"outcome": "failed", "error": f"{type(exc).__name__}: {exc}"}

    def all(self) -> list[dict]:
        """Every trouble in the store: the live ones at the top, then ``cleared/``."""
        self.fold_pending()
        return self._listing(self._root) + self._listing(self._root / CLEARED_DIR)

    def migrate_from(self, old: str | os.PathLike) -> dict:
        """Move an old store whole into this one (ticket 4ddc9df3369e): a file whose standing
        is CLEARED lands in ``cleared/``, every other file (unreadable included) at the top.
        Each move rides the artifact door's ``rename``, so leaving a record of truth is
        journaled. Returns ``{"live": n, "cleared": n}``."""
        from cairn.tools.artifact import artifact as door
        counts = {"live": 0, "cleared": 0}
        for p in sorted(Path(old).glob("*.json")):
            try:
                standing = json.loads(p.read_text(encoding="utf-8")).get("standing")
            except (json.JSONDecodeError, AttributeError):
                standing = None
            kind = "cleared" if standing == CLEARED else "live"
            dest = (self._root / CLEARED_DIR if kind == "cleared" else self._root) / p.name
            dest.parent.mkdir(parents=True, exist_ok=True)
            door.rename(p, dest, why=f"trouble store moved to {self._root} (ticket 4ddc9df3369e)")
            counts[kind] += 1
        return counts

    def _listing(self, folder: Path) -> list[dict]:
        # The reading rule (an unreadable file surfaced, an off-template record said so) lives
        # in the tool, so the owner's reads and every other reader's cannot differ.
        return _store.listing(folder)

    # --- the file layer (thin, and the only writer) -------------------------

    def identity_of(self, identity: str) -> str:
        """The stored form of an identity — PUBLIC because the drain has to ask.

        Every door here (``raise_trouble``, ``clear``, ``amend``) slugs what it is handed,
        so what is ON DISK is always the slug. Anything that wants to COMPARE a caller's
        identity against the live set has to slug it first, and the drain does exactly that
        before it decides whether a clear names a standing trouble. It used to compare the
        raw pointer, and the measured cost was total: on 2026-09-08 five of five tester
        clears folded to ``declined — not live`` because the tester names its troubles after
        a proof file (``test_inspector_nexus``) and the store holds the slug
        (``test-inspector-nexus``). The trouble whose proof had gone green sat in the
        operator inbox anyway.

        Reaching through ``_slug`` from the shim would have worked and would have been a
        lie about the contract: the normalization is not an implementation detail of this
        class, it is the store's addressing rule, and a caller that must obey a rule needs
        a public way to ask what it is."""
        return self._slug(identity)

    def _slug(self, identity: str) -> str:
        s = _SLUG.sub("-", (identity or "").strip().lower()).strip("-")
        if not s:
            raise TroubleError("a trouble carries an identity — the name of the DEFECT, which "
                               "is what makes a second occurrence the same trouble as the first")
        return s

    def _path(self, ident: str) -> Path:
        return self._root / f"{ident}.json"

    def _cleared_path(self, ident: str) -> Path:
        return self._root / CLEARED_DIR / f"{ident}.json"

    def _read(self, ident: str) -> dict | None:
        """The ticket at the top of the store, else the one in ``cleared/``."""
        for p in (self._path(ident), self._cleared_path(ident)):
            if not p.exists():
                continue
            try:
                return json.loads(p.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                return None
        return None

    def _drop(self, path: Path, *, why: str) -> None:
        from cairn.tools.artifact import artifact as door
        if path.exists():
            door.remove(path, why=why)

    def _write(self, ident: str, ticket: dict, *, verb: str, why: str,
               where: Path | None = None) -> None:
        """Every trouble lands through the artifact door (ticket 30531f6e1c5d): the write is
        atomic and the journal names WHO raised, cleared or amended it from the caller's
        cgroup. A store under a scratch root (a proof's world) is outside the door's
        jurisdiction and is written plainly — the door says so rather than pretending."""
        from cairn.tools.artifact import artifact as door
        target = where or self._path(ident)
        target.parent.mkdir(parents=True, exist_ok=True)
        door.write(target, json.dumps(ticket, indent=2, ensure_ascii=False) + "\n",
                   verb=verb, why=why)
