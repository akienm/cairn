"""gate — everything always proved, and listing what it proved.

AKIEN, 2026-08-13, and it is the whole specification:

    "NO GATES MAY CONSULT ORACLES EVER PERIOD. A GATE ONLY OPENS WHEN A FINDINGS REPORT
     MATCHES WHAT IT ALLOWS. ITS AN == compare. Must be identical. NO ORACLE."

    "The build inspector must list EVERY TEST THAT HAS PASSED. {EXPECTED: value, ACTUAL:
     value} ... NO EMPTY ANYWHERE."

    "EVERYTHING ALWAYS PROVED AND LISTING WHAT IT PROVED. SAME PATTERN EVERYWHERE."

SO A GATE DOES NOT HOLD AN EXEMPTION LIST. It holds a PROOF RECORD: one entry per check
that ran, each carrying what was EXPECTED and what was ACTUAL. The gate opens when every
entry's expected equals its actual — an == compare, per entry, no oracle anywhere near it.

WHY THAT IS NOT THE SAME AS "NO FINDINGS", which is the shape this module shipped with
first and which is wrong in a way that reads as strict. A findings report lists only what
went WRONG, so an empty one is ambiguous at exactly the moment it matters: it means "every
check passed" and "no check ran" and "the walk crashed early" and "the subject wasn't
found", and nothing downstream can tell those apart. Passing that to a gate makes the
gate's green a green about SILENCE. A proof record cannot be silent — it names every check
by name and states its expected and actual side by side, so a check that stopped running
disappears from the list and is visible as a shorter list, not as a cleaner one.

NO EMPTY ANYWHERE. An empty record raises. A gate that proved nothing has not proved
everything; it is the vacuous green (Law 8), and it is refused rather than reported. An
entry missing ``expected`` or ``actual`` raises too — those are the compare's own
preconditions, and a gate that quietly skips an unusable entry is a gate that opens on
fewer checks than it claims.

THE RECORD SHAPE IS THE SEED, AND THE SEED IS ALREADY IN THIS CORPUS — Akien settled it in
2007 and it lives at ``cairn/machines/diagnostic_inspector/inspector.py`` as ``SEED``:
identity, location, code, expected, actual, fatality, source, plus every value at every
transition and boundary that bears on the fault. ``proved()`` below builds an entry in that
shape so every gate in the system emits the SAME PATTERN. This module deliberately does not
re-derive completeness checking over it: measuring whether a record carries its seed is
diagnostic_inspector's job and it already does it. What lives here is the compare.

    from cairn.tools.gate import gate
    record = [gate.proved(identity="charter_on_disk", location="devices/bus",
                          code="inspector.py:charter_on_disk", expected=1.0, actual=1.0,
                          source="build_inspector")]
    v = gate.verdict(record)
    v["opens"], v["proved"], v["failed"]      # and v["mismatches"] says exactly which

THE AUTHORING HAZARD, MEASURED n=4 IN ONE DAY (2026-08-13, the sweep that converted the
corpus onto this shape). Writing a lane, the natural sentence is "expected: one of A or B,
actual: A" — and that lane can never open, so it reds on every HEALTHY subject. Four of
them shipped in one day (a ruling packet's verbatim check, skill_block's exit vocabulary,
and two of the extraction judge's). BOTH SIDES MUST READ THE SAME SENTENCE WHEN THE LANE
PASSES; the offending value rides in ``values``, where a reader still sees it. Populations
are the exception that shows the rule — ``expected=[every candidate]``, ``actual=[the ones
that qualified]`` — because those two ARE equal when the lane passes.

Nothing here enforces it: an entry that fails while carrying an empty refusal payload is
internally inconsistent, but the payload's key is the caller's word (lacks, findings,
complaints, reds, failures, missing) and this tool does not know it. What caught all four
was the component's own tooth asserting that a healthy fixture produces an all-passing
record. That tooth is the physics until something better exists — an IOU, not a resting
state (Law 4). · *ticket owed*

A TOOL HAS USERS, NOT AN OWNER (Law 6). Not because a tool cannot remember — it can, and
ruling 2026-08-14-tools-and-machines-remember-under-their-holder says so: ongoing state
berths under the HOLDER, at ``~/.cairn/devices/<device>/<instance>/tools/<tool class>/
<tool instance>/``, so it is the holder's to own and gate and the tool has nothing OF ITS
OWN to gate. What is true of THIS build, and is a fact about this build rather than about
tools: the record arrives as an argument and nothing is remembered between calls.
"""

from __future__ import annotations

import json

OPEN = "OPEN"
CLOSED = "CLOSED"

# The record shape, named here so every gate emits the same one. It is diagnostic_inspector's
# SEED — Akien's 2007 list — and it is NOT re-derived here: this is the vocabulary, that is
# the instrument that measures whether a record honours it.
SEED = ("identity", "location", "code", "expected", "actual", "fatality", "source")

# The compare's own preconditions. Everything else in the seed is completeness, which is a
# different question with a different owner.
REQUIRED = ("identity", "expected", "actual")


class NoProof(Exception):
    """A gate was asked for a verdict over a record that cannot support one.

    Empty, or an entry that does not carry what the compare needs. Loud and terminal: a
    gate that proved nothing has not proved everything, and one that skips an unusable
    entry opens on fewer checks than it says it did.
    """


def canonical(value) -> str:
    """One value as one canonical string — sorted keys, no whitespace slack.

    So that ``expected`` and ``actual`` compare on CONTENT: two dicts built in a different
    key order are the same value, and a gate that said otherwise would be measuring how
    its caller happened to construct a literal. ``default=str`` so a Path or a datetime
    renders rather than raising, because a gate that crashes on an odd value fails open
    inside any caller that wraps it.
    """
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def proved(*, identity, expected, actual, location="", code="", fatality="", source="",
           **values) -> dict:
    """One entry in a proof record — a check, what it expected, what it got.

    SAME PATTERN EVERYWHERE (Akien, 2026-08-13). Every gate builds its entries through
    here, so a reader who has read one proof record has read all of them, and so a new
    gate cannot invent its own field names for the same three ideas. Extra keyword
    arguments land in ``values`` — the seed's every-value-that-bears-on-the-fault clause.
    """
    entry = {"identity": identity, "location": location, "code": code,
             "expected": expected, "actual": actual,
             "fatality": fatality or ("closes the gate" if canonical(expected) != canonical(actual)
                                      else "none"),
             "source": source}
    if values:
        entry["values"] = values
    return entry


def passed(entry) -> bool:
    """One entry's == compare. This is the entire decision procedure of every gate."""
    return canonical(entry["expected"]) == canonical(entry["actual"])


def _checked(record) -> list:
    """The record, refused if it cannot carry a verdict. NO EMPTY ANYWHERE."""
    entries = list(record)
    if not entries:
        raise NoProof(
            "empty proof record — a gate that proved nothing has not proved everything. "
            "A gate lists EVERY test that ran with its expected and actual; an empty list "
            "is the vacuous green (Law 8), not a clean one.")
    for i, e in enumerate(entries):
        missing = [k for k in REQUIRED if k not in e]
        if missing:
            raise NoProof(
                f"proof record entry {i} is missing {missing} — every entry names the check "
                f"and states expected beside actual. Build entries with gate.proved(). Got: {e}")
    return entries


def opens(record) -> bool:
    """Akien's sentence, executable: every check proved, or the gate stays shut."""
    return all(passed(e) for e in _checked(record))


def verdict(record) -> dict:
    """The gate's whole answer in one read.

    ``proved`` is the list of what it PROVED, by name — the point of the record, and the
    half a findings report throws away. ``mismatches`` carries the failures whole, so a
    closed gate never sends the next mind back to re-run it for the detail
    (I-complete-diagnostic-on-first-pass).
    """
    entries = _checked(record)
    ok = [e for e in entries if passed(e)]
    bad = [e for e in entries if not passed(e)]
    return {
        "verdict": OPEN if not bad else CLOSED,
        "opens": not bad,
        "checks": len(entries),
        "passed": len(ok),
        "failed": len(bad),
        "proved": [e["identity"] if not e.get("location") else f"{e['identity']} @ {e['location']}"
                   for e in ok],
        "mismatches": bad,
        "why": (
            f"all {len(entries)} checks proved — expected == actual for every one"
            if not bad else
            f"{len(bad)} of {len(entries)} checks did not match — a gate opens only when "
            "every expected equals its actual"
        ),
    }
