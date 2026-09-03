"""feedback — the edge a finding travels along, and the physics that it exists.

AKIEN, 2026-08-14, drawing the segment as one repeating unit:

    machine -> inspector -1-> findings -> gate -> output -2-> feedback to
    [thing this thing feeds back to, might be the machine, might be anything else]

THE CORPUS WAS BUILT UP TO THE GATE AND STOPPED THERE. Measured the day this tool was
written: every one of the eight builder stages carries ``inspect_<stage>`` (machine ->
inspector), a proof record (-> findings), ``validate_<stage>`` as the == compare
(findings -> gate), and ``write_<stage>`` (-> output). Edge -2- existed NOWHERE. A grep
across the builder, build_inspector and tools/base for any routing declaration returned
nothing. Failing findings refused loudly at their gate and stopped; they never travelled,
so nothing they could have improved ever heard about them.

    "that findings problem IS THIS WHOLE CONVERSATION. That's what we're fixing now.
     because these have to be as bullet proof as possible. these are the foundation for
     everything else." (Akien, 2026-08-14)

WHY THE ROUTE IS DECLARED AND NOT COMPUTED. A finding knows who MADE it — ``source`` and
``location`` ride in every entry. It cannot know where it should GO, because that is a
design fact about the segment, not a property of the failure. The conversation that bore
this tool spent three exchanges trying to derive the destination from the evidence and
failed every time: askscan's five measured gaps all named ``verdict`` as the stage that
ran last, and not one of them was verdict's to fix — three were ambiguities in the
REQUEST and belonged above the whole chain. A destination inferred from the failure is a
guess wearing a measurement's clothes. So the segment DECLARES it, once, in the charter.

AND WHAT IT DECLARES IS A TARGET, NOT A DISTANCE. Akien's first statement of the rule ended
"in some cases it skips levels", and the first cast of the 17 routes read that as a hop
count — mid-chain stages one link back, orient some number of links further. He corrected
it the same day: "really it shouldn't be 'number of steps' it should be 'to the feedback
target' which is likely to be the previous step." The previous step is the COMMON CASE, not
the definition. So orient — whose upstream artifact is the ticket, not another stage — is
an ordinary answer rather than an exception owing an excuse, and nothing in this module
counts anything.

WHY THE CHARTER AND NOT AN ARGUMENT. If ``proved()`` took the route as a free keyword,
the charter would say one thing and 66 call sites would each say their own, and the two
could disagree — which is the identical defect (two mouths on one question) that the
proof record was built to close for refusal sentences. DERIVED, NEVER PARALLEL. The
charter is the one mouth; ``route()`` reads it; the finding carries what it read.

WHAT THE POPULATION IS, and why it is not ``def inspect_``. The rule Akien named is "an
inspector that can fail with nowhere to send it". The capability that makes that possible
is CONSTRUCTING A FINDING, not being named like an inspector — so the population is every
component whose shipped code calls ``gate.proved`` or the chain's ``inspected``. Reading
for a ``def inspect_`` would be the structural proxy this corpus keeps catching in its own
instruments: a component could route findings through a helper named anything at all, and
a component could carry a ``def inspect_thing`` that never builds an entry.

DEFERRED IS THE DEFAULT, AND THAT IS A BOUND, NOT AN OMISSION (Akien, 2026-08-14):
"since we're trying to compile to the lowest possible level, why: so we can maximize
determinism, we want to push toward 'the feedback is processed later to improve the
generator and the inspector' in most cases. we will have cases with more immediacy as
well, like 'don't start a new process if each of these costs 10% of cpu and we're already
at 80%'. but while we're leaving room for those, we're not building or ticketing those
now." So a route is an ADDRESS and nothing else. There is no urgency field, no mode, no
"immediate" enum — leaving room means the shape does not preclude one, and adding a
placeholder now would be building the thing he just said not to build.

BOTH ENDS GET IMPROVED. "processed later to improve the generator AND the inspector" —
the machine that made the bad output, and the inspector that either missed it or asked
the wrong question. That is the processing act, which is deliberately not in this tool:
this tool makes the edge exist and makes a routeless finding impossible. What happens at
the far end grows against real findings, of which the corpus currently has none.

    from cairn.tools.feedback import feedback
    feedback.route("cairn/devices/codemonkey/machines/orient")   # -> the declared address
    feedback.corpus_record()                                  # the proof record, all producers

A TOOL HAS USERS, NOT AN OWNER (Law 6) — AND A TOOL MAY STILL REMEMBER. Ruling
2026-08-14-tools-and-machines-remember-under-their-holder, correcting this file's first
line on the subject: "If a starting state is needed, it's in the code. ongoing state is in
the runtime folder.
``~/.cairn/devices/<device class>/<device name/num>/tools/<tool class>/<tool name/num>/``
… So even completely no LLM can have instance or class level memories" — "right because
each instance of the tool or machine can have it's own data". The definition and the
defaults berth here in class-space; anything ongoing berths under the HOLDER that
assembled the tool. Law 6 survives intact because that state is the holder's to own and
gate — the tool has nothing OF ITS OWN to gate — which is a different claim from "a tool
holds no state", the property-of-toolhood sentence this docstring shipped with and which
is simply wrong. TODAY this module persists nothing: charters are read on demand. That is
a fact about this build, not about tools, and it changes the moment a finding travels —
the berth for findings in flight is the address above.

AND THE CLASS SEGMENT OF THAT PATH IS A FOLDER. ``tools/<tool class>/`` holds every
instance of that class within one holder, so it can hold files SHARED by them. Akien
called this out explicitly so it could not become ambiguous later, and bounded it in the
same breath: "i don't have a use for it in my head. but that use is not excluded." It is
an affordance of the shape — permitted, deliberately unbuilt, and not ticketed. Written
down here so a later reader finds it already allowed instead of re-deriving it, and so
nobody builds a mechanism for a use nobody has named. It is HOLDER-SCOPED: that folder
sits under one device instance, and there is no cross-device drawer for a tool class.
"""
from __future__ import annotations

import ast
import json
import os
from pathlib import Path

from cairn.tools.gate import gate

CAIRN_ROOT = os.environ.get("CAIRN_ROOT") or str(Path(__file__).resolve().parents[3])

CHARTER = "intention+why.json"

# The declaration's own shape. ``to`` is the address; ``why`` is forced by the schema
# rather than left to a fillable field, because a route nobody justified is a route
# nobody will re-examine when it turns out to be wrong (I-force-the-why-structurally).
FIELD = "feedback"
REQUIRED_KEYS = ("to", "why")
PROBE_REQUIRED_KEYS = ("to", "why")
VALID_CONSUMERS = ("active", "passive")

# The two ways this corpus constructs a finding. A component that calls either can produce
# a failure, and that is the whole population that owes a route.
CONSTRUCTORS = ("proved", "inspected")


class NoRoute(Exception):
    """A finding could be built with nowhere to send it.

    Loud and terminal. Akien's whole sentence for this tool is that these have to be as
    bulletproof as possible because everything else rests on them — so a missing route is
    refused where it is discovered, never defaulted to somewhere plausible. A default
    destination is how feedback silently piles up against the wrong door.
    """


def _charter(component: str, root: str = CAIRN_ROOT) -> dict:
    """One component's charter as data. Missing or unparseable is a refusal, not a {}."""
    path = Path(root) / component / CHARTER
    if not path.is_file():
        raise NoRoute(
            f"{component} has no charter at {component}/{CHARTER} — a component without an "
            "intention does not run, and one that cannot say where its findings go cannot "
            "be allowed to make any")
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise NoRoute(f"{component}/{CHARTER} does not parse: {e}") from e


def declared(component: str, root: str = CAIRN_ROOT) -> dict | None:
    """The component's feedback block, or None if it declares none."""
    block = _charter(component, root).get(FIELD)
    return block if isinstance(block, dict) else None


def _normalize_probes(block: dict, component: str) -> list[dict]:
    """Normalize a feedback block into a list of probe dicts.

    Accepts either the shorthand ``{to, why}`` or the explicit ``{probes: [{to, why, consumer?}, ...]}``
    shape. Every returned probe carries ``to``, ``why``, and ``consumer`` (defaulting to ``'active'``).
    """
    raw = block.get("probes")
    if raw is not None:
        if not isinstance(raw, list) or not raw:
            raise NoRoute(
                f"{component}'s {FIELD} block carries 'probes' but it is not a non-empty list")
        entries = raw
    else:
        entries = [block]

    normalized = []
    for i, entry in enumerate(entries):
        if not isinstance(entry, dict):
            raise NoRoute(
                f"{component}'s {FIELD} probe [{i}] is not a dict")
        missing = [k for k in PROBE_REQUIRED_KEYS if not str(entry.get(k, "")).strip()]
        if missing:
            raise NoRoute(
                f"{component}'s {FIELD} probe [{i}] is missing {missing} — 'to' is the address "
                "and 'why' is why THAT address and not another")
        consumer = entry.get("consumer", "active")
        if consumer not in VALID_CONSUMERS:
            raise NoRoute(
                f"{component}'s {FIELD} probe [{i}] has consumer={consumer!r} — "
                f"must be one of {VALID_CONSUMERS}")
        normalized.append({"to": entry["to"], "why": entry["why"], "consumer": consumer})
    return normalized


def probes(component: str, root: str = CAIRN_ROOT) -> list[dict]:
    """The component's declared probes, normalized. Raises NoRoute if it cannot say.

    Every recipient has their own probe (Akien ruling 2026-09-01). A segment that reports
    to multiple targets declares a probes array; the single-probe shorthand (feedback.to)
    is sugar for a one-element probes array.
    """
    block = declared(component, root)
    if block is None:
        raise NoRoute(
            f"{component} constructs findings but its charter declares no {FIELD!r} — an "
            "inspector that can fail with nowhere to send it is the defect this tool "
            "exists to make impossible. Declare "
            f'{FIELD}: {{"to": "<address>", "why": "<why there>"}}')
    result = _normalize_probes(block, component)
    for probe in result:
        if not resolves(probe["to"], root):
            raise NoRoute(
                f"{component} routes its findings to {probe['to']!r}, which does not resolve. "
                "A destination that is not on disk is indistinguishable from no destination "
                "the moment anyone tries to deliver to it")
    return result


def resolves(address: str, root: str = CAIRN_ROOT) -> bool:
    """Does this route point at something that EXISTS?

    The physics that keeps the field from decaying into prose. A route is checked the same
    way orient checks a ref — the thing is on disk or it is not — because a destination
    that does not resolve is indistinguishable from no destination at all the moment
    anyone tries to deliver to it. Addresses are repo-relative and may name either root:
    a component directory here, or a commons folder (tickets, intentions) over there.
    """
    if not isinstance(address, str) or not address.strip():
        return False
    here = Path(root) / address
    if here.exists():
        return True
    # The commons is a sibling root, and a route to ticketing or to an intention is one
    # of the two destinations Akien named by hand ("might go back to ticketing. it might
    # even go back to intention").
    commons = Path(root).parent / "CairnCommons"
    return (commons / address).exists() or (
        address.startswith("CairnCommons/") and (Path(root).parent / address).exists())


def route(component: str, root: str = CAIRN_ROOT) -> str:
    """Where this component's failing findings go — the FIRST probe's address.

    Backward-compatible: returns one address. For multi-probe components, use probes()
    to see all targets. This function is the single mouth every finding-constructor calls;
    the charter declares the destination, no call site gets to spell it.
    """
    return probes(component, root)[0]["to"]


def _constructs_findings(py: Path) -> bool:
    """Does this module actually BUILD a finding? Parsed, not grepped.

    ``ast`` rather than a substring scan so a mention in a docstring or a comment does not
    count as a call — the use-vs-mention tax this corpus has paid twice already.
    """
    try:
        tree = ast.parse(py.read_text(encoding="utf-8"))
    except (OSError, SyntaxError):
        return False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        fn = node.func
        name = fn.attr if isinstance(fn, ast.Attribute) else getattr(fn, "id", None)
        if name in CONSTRUCTORS:
            return True
    return False


def producers(root: str = CAIRN_ROOT) -> list[str]:
    """Every component whose SHIPPED code can construct a finding.

    Proofs are excluded on purpose: a proof builds fixture findings to test a door, and it
    is not a segment with an output anyone consumes. The unit is the COMPONENT — the
    directory carrying the charter — because that is the address a route is declared at.
    """
    found = set()
    for py in Path(root, "cairn").rglob("*.py"):
        parts = py.relative_to(root).parts
        if "proofs" in parts or "__pycache__" in parts:
            continue
        if not _constructs_findings(py):
            continue
        # Walk up to the nearest directory that carries a charter: that is the component.
        d = py.parent
        while d != Path(root):
            if (d / CHARTER).is_file():
                found.add(str(d.relative_to(root)))
                break
            d = d.parent
    return sorted(found)


def corpus_record(root: str = CAIRN_ROOT) -> list[dict]:
    """THE PROOF RECORD: one entry per finding-producer, routed or not, passes included.

    EVERYTHING ALWAYS PROVED AND LISTING WHAT IT PROVED (Akien, 2026-08-13). A component
    that starts constructing findings and declares no route makes this record LONGER by
    one failing entry; a component that stops constructing them makes it SHORTER, which is
    visible as a shorter list rather than a cleaner one.

    This record is built by hand rather than through ``route()`` alone so that a passing
    entry states the address it proved — a reader sees WHERE each segment sends its
    feedback, which is the half a complaint list throws away.

    THE ROUTE IS NOT A FIELD ON THE ENTRY, AND THAT IS DELIBERATE. The first cast of this
    tool made ``gate.proved`` require it, which would have put the destination at all 66
    finding-construction sites in the corpus — 66 chances to spell by hand what the
    charter already says, which is the two-mouths defect the proof record itself was built
    to close for refusal sentences. The charter says it once; a deliverer asks ``route()``
    at delivery time and therefore cannot be reading a stale copy.
    """
    record = []
    for component in producers(root):
        try:
            p = probes(component, root)
        except NoRoute as e:
            record.append(gate.proved(
                identity="constructs_findings_and_declares_where_they_go",
                location=component, code="feedback.py:probes",
                expected="a resolvable feedback route", actual="none",
                source="feedback", lack=str(e)))
        else:
            record.append(gate.proved(
                identity="constructs_findings_and_declares_where_they_go",
                location=component, code="feedback.py:probes",
                expected="a resolvable feedback route", actual="a resolvable feedback route",
                source="feedback", routes_to=p[0]["to"],
                probes_to=[{"to": e["to"], "consumer": e["consumer"]} for e in p]))
    return record


def _main(argv=None) -> int:
    """The census: who constructs findings, and where each one sends them.

    ATTENDANCE, NOT ONLY OBJECTIONS. Routed producers are printed too, each with its
    destination, because the half a complaint list throws away is exactly the half a
    reader needs to see the edge at all.
    """
    import sys
    argv = list(sys.argv[1:] if argv is None else argv)
    record = corpus_record()
    v = gate.verdict(record) if record else {"verdict": "CLOSED", "opens": False,
                                             "checks": 0, "passed": 0, "failed": 0,
                                             "why": "no finding-producers found at all — "
                                                    "the census walked and saw nothing, "
                                                    "which is a broken walk, not a clean corpus"}
    if "--json" in argv:
        print(json.dumps({"verdict": v, "record": record}, indent=2))
        return 0 if v["opens"] else 1

    print(f"{v['checks']} finding-producing component(s) — "
          f"{v['passed']} routed, {v['failed']} with nowhere to send a failure\n")
    for e in record:
        if gate.passed(e):
            probes_to = e["values"].get("probes_to", [])
            if len(probes_to) <= 1:
                print(f"  routed   {e['location']}  ->  {e['values']['routes_to']}")
            else:
                print(f"  routed   {e['location']}")
                for p in probes_to:
                    print(f"             -> {p['to']}  ({p['consumer']})")
    for e in record:
        if not gate.passed(e):
            print(f"  NO ROUTE {e['location']}")
    if not v["opens"]:
        print(f"\n{v['why']}")
        print("A segment is machine -> inspector -> findings -> gate -> output -2-> feedback.\n"
              "Every component above with NO ROUTE can construct a finding that has nowhere\n"
              "to go, so nothing it could improve will ever hear about it. Declare in its\n"
              'charter:  "feedback": {"to": "<address>", "why": "<why there>"}')
    return 0 if v["opens"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
