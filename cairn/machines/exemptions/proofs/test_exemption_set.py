"""Proofs for the exemption sieve (every_exemption_cites_a_ruling_or_an_impossibility).

Each tooth is aimed at a clause of the ticket's falsifier, and each is written
against a DELIBERATELY BROKEN set so the instrument is shown capable of failing
before it is trusted on the real one (Law 8 — a hollow green is worse than a red,
because a red is distrusted by construction and a false green gets leaned on).

A hollow implementation that always returned [] would fail teeth 1 through 7.
A set that had been narrowed would fail tooth 4. A set that certified itself
against code that had moved underneath would fail tooth 7.

Provenance: ticket 892a0f9cd925-an-exemption-cites-a-ruling-or-an-impossibility,
discharging ruling 2026-09-10-exemption-reasons-are-not-rulings.
"""

import json
from pathlib import Path

from cairn.devices.tester.scratch import scratch_dir
from cairn.machines.build_inspector.inspector import (
    SIEVES, the_nest, every_exemption_cites_a_ruling_or_an_impossibility as SIEVE)
from cairn.machines.exemptions.justification import justification_lack, LEGAL_KINDS

PASS = 0
FAIL = 0

REPO = Path(__file__).resolve().parents[4]
REAL_SET = REPO / "cairn" / "machines" / "exemptions" / "exemption_set.json"

PROVES = {
    "892a0f9cd925": {
        "the set exists and is read": "test_AN_ABSENT_SET_REDS",
        "the set is readable": "test_AN_UNREADABLE_SET_REDS",
        "the set is non-empty": "test_AN_EMPTY_SET_REDS",
        "narrowing fires the check on itself": "test_A_SET_THAT_DROPPED_ITS_OWN_ENTRY_REDS",
        "a ruling kind's decision id must resolve": "test_A_RULING_THAT_DOES_NOT_RESOLVE_REDS",
        "a no-other-way kind must state something": "test_AN_EMPTY_IMPOSSIBILITY_REDS",
        "the reason is anchored in the code": "test_A_SYMBOL_THAT_MOVED_REDS",
        "the live set carries every measured site": "test_THE_LIVE_SET_CARRIES_THE_SEVEN_MEASURED_SITES",
        "the sieve is registered and fires": "test_THE_SIEVE_IS_REGISTERED_AND_IN_THE_NEST",
        "nothing here reaches an inference host": "test_NOTHING_IN_THE_CLOSURE_REACHES_AN_LLM",
        "the watch probe is armed and can fire": "test_THE_WATCH_PROBE_IS_ARMED_AND_CAN_FIRE",
    }
}


def _check(name, ok, detail=""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print("  ok   %s" % name)
    else:
        FAIL += 1
        print("  FAIL %s  %s" % (name, detail))


def _lacks(out):
    """The `lack` strings a sieve run produced.

    A finding carries its detail under `values`, not at the top level — reading
    it at the top level is how a tooth quietly stops discriminating, because
    `f.get("lack")` is None for EVERY finding and the `any(...)` is then False
    whether the sieve redded correctly or not at all.
    """
    return [str((f.get("values") or {}).get("lack", "")) for f in out]


def _component(exemptions, *, write=True, raw=None):
    """A temporary repo-like tree holding an exemptions component."""
    root = scratch_dir("exemptions_")
    (root / ".git").mkdir(exist_ok=True)
    comp = root / "cairn" / "machines" / "exemptions"
    comp.mkdir(parents=True, exist_ok=True)
    if raw is not None:
        (comp / "exemption_set.json").write_text(raw, encoding="utf-8")
    elif write:
        (comp / "exemption_set.json").write_text(
            json.dumps({"schema_version": "exemption-set-v1",
                        "exemptions": exemptions}, indent=1), encoding="utf-8")
    return root, comp


def _self_entry(comp_rel="cairn/machines/exemptions/exemption_set.json"):
    return {"id": "self", "path": comp_rel, "description": "the set itself",
            "kind": "set", "justification_kind": "no-other-way",
            "evidence": "nothing discovers an exemption nobody entered",
            "symbol": "exemptions"}


ROW = {"component": "exemptions"}


def test_AN_ABSENT_SET_REDS():
    _root, comp = _component(None, write=False)
    out = SIEVE(ROW, comp)
    _check("an absent set reds", len(out) == 1, out)


def test_AN_UNREADABLE_SET_REDS():
    _root, comp = _component(None, raw="{not json at all")
    out = SIEVE(ROW, comp)
    _check("an unreadable set reds", len(out) == 1, out)


def test_AN_EMPTY_SET_REDS():
    _root, comp = _component([])
    out = SIEVE(ROW, comp)
    _check("an empty set reds", len(out) == 1, out)


def test_A_SET_THAT_DROPPED_ITS_OWN_ENTRY_REDS():
    entry = {"id": "somewhere-else", "path": "cairn/tools/base/transitions.py",
             "description": "x", "kind": "roster",
             "justification_kind": "no-other-way", "evidence": "because",
             "symbol": "_EXEMPT_ROSTER"}
    root, comp = _component([entry])
    (root / "cairn" / "tools" / "base").mkdir(parents=True, exist_ok=True)
    (root / "cairn" / "tools" / "base" / "transitions.py").write_text(
        "_EXEMPT_ROSTER = frozenset()\n", encoding="utf-8")
    out = SIEVE(ROW, comp)
    _check("a set that dropped its own entry reds",
           any("self-membership" in n for n in _lacks(out)), out)


def test_A_RULING_THAT_DOES_NOT_RESOLVE_REDS():
    entry = {"id": "cites-a-ghost", "path": "cairn/machines/exemptions/exemption_set.json",
             "description": "x", "kind": "sieve-scope",
             "justification_kind": "ruling",
             "evidence": "2099-01-01-a-ruling-that-was-never-made",
             "symbol": "exemptions"}
    _root, comp = _component([entry])
    out = SIEVE(ROW, comp)
    _check("a ruling kind naming an unresolvable decision reds",
           any("does not resolve" in n for n in _lacks(out)), out)
    lack = justification_lack(entry)
    _check("and the resolver says why, not just no",
           "no decision file" in lack, lack)


def test_AN_EMPTY_IMPOSSIBILITY_REDS():
    for bad in ("", "   ", None):
        entry = {"id": "says-nothing", "path": "cairn/machines/exemptions/exemption_set.json",
                 "description": "x", "kind": "sieve-scope",
                 "justification_kind": "no-other-way", "evidence": bad,
                 "symbol": "exemptions"}
        _root, comp = _component([entry])
        out = SIEVE(ROW, comp)
        _check("an empty impossibility (%r) reds" % bad,
               any("evidence is missing or empty" in n for n in _lacks(out)), out)
    entry = {"id": "no-kind", "path": "cairn/machines/exemptions/exemption_set.json",
             "description": "x", "kind": "sieve-scope",
             "justification_kind": "because I said so", "evidence": "words",
             "symbol": "exemptions"}
    _root, comp = _component([entry])
    out = SIEVE(ROW, comp)
    _check("an illegal justification_kind reds",
           any("must be one of" in n for n in _lacks(out)), out)
    _check("and the two legal kinds are the declared pair",
           set(LEGAL_KINDS) == {"ruling", "no-other-way"}, LEGAL_KINDS)


def test_A_SYMBOL_THAT_MOVED_REDS():
    """THE ANCHOR TOOTH — the one that stops the set certifying itself.

    A set an author wrote and a sieve the same author wrote will agree with each
    other forever. The symbol is what makes them both answerable to the code:
    rename the exempting construct, leave the reason untouched, and the entry
    must red.
    """
    entry = {"id": "anchored", "path": "cairn/tools/base/transitions.py",
             "description": "x", "kind": "roster",
             "justification_kind": "no-other-way", "evidence": "because",
             "symbol": "_EXEMPT_ROSTER: frozenset[str]"}
    root, comp = _component([entry, _self_entry()])
    base = root / "cairn" / "tools" / "base"
    base.mkdir(parents=True, exist_ok=True)
    target = base / "transitions.py"

    target.write_text("_EXEMPT_ROSTER: frozenset[str] = frozenset()\n", encoding="utf-8")
    _check("an anchored entry passes while the symbol is there", SIEVE(ROW, comp) == [],
           SIEVE(ROW, comp))

    target.write_text("_TICKET_WAIVER: frozenset[str] = frozenset()\n", encoding="utf-8")
    out = SIEVE(ROW, comp)
    _check("and reds the moment the construct is renamed",
           any("declared symbol does not appear" in n for n in _lacks(out)), out)

    target.unlink()
    out = SIEVE(ROW, comp)
    _check("and reds when the site is gone entirely",
           any("no longer resolves" in n for n in _lacks(out)), out)


def test_THE_LIVE_SET_CARRIES_THE_SEVEN_MEASURED_SITES():
    """THE CONTENT TOOTH — aimed at the set itself, not only at the sieve.

    exemption_set.json is data, and a proof that only exercised the sieve's logic
    would let the set be reverted with every tooth still green. That is the
    measured hollow shape from ticket 4c022c44de53, and this tooth is what keeps
    it off this build.
    """
    _check("the live set exists", REAL_SET.is_file(), REAL_SET)
    if not REAL_SET.is_file():
        return
    s = json.loads(REAL_SET.read_text(encoding="utf-8"))
    ex = s.get("exemptions") or []
    _check("the live set carries 8 entries — 7 measured sites plus itself",
           len(ex) == 8, len(ex))
    want = {
        "cairn/machines/exemptions/exemption_set.json",
        "cairn/machines/build_inspector/inspector.py",
        "cairn/tools/base/address_rule.py",
        "cairn/tools/base/transitions.py",
        "cairn/tools/base/watchme_spec.py",
        "cairn/tools/bus_client/probes/a_client_reaches_and_never_beats.py",
        "cairn/devices/tester/hollow.py",
    }
    got = {e.get("path") for e in ex}
    _check("every measured site is in the set", want <= got, sorted(want - got))
    _check("every entry declares a legal justification_kind",
           all(e.get("justification_kind") in LEGAL_KINDS for e in ex),
           [e.get("id") for e in ex if e.get("justification_kind") not in LEGAL_KINDS])
    _check("every entry's declared justification resolves against the live corpus",
           all(justification_lack(e) == "" for e in ex),
           [(e.get("id"), justification_lack(e)) for e in ex if justification_lack(e)])
    _check("the live set reads green through the sieve",
           SIEVE(ROW, REAL_SET.parent) == [], SIEVE(ROW, REAL_SET.parent))


def test_THE_SIEVE_IS_REGISTERED_AND_IN_THE_NEST():
    name = "every_exemption_cites_a_ruling_or_an_impossibility"
    _check("the sieve is in SIEVES", name in SIEVES, sorted(SIEVES)[:3])
    in_nest = any(name in names for _phase, names in the_nest())
    _check("the sieve is assembled into the nest", in_nest, the_nest())
    _check("it fires only for the exemptions component",
           SIEVE({"component": "corrosion"}, REAL_SET.parent) == [])


def test_NOTHING_IN_THE_CLOSURE_REACHES_AN_LLM():
    """Akien's standing rule: nothing in an inspector or a gate may be an LLM."""
    import cairn.machines.exemptions.justification as J
    banned = ("inference_domain", "anthropic", "openai", "hex.local", "claude")
    for mod in (J,):
        text = Path(mod.__file__).read_text(encoding="utf-8")
        # the word 'claude' appears in prose nowhere here; an IMPORT is what matters
        hits = [b for b in banned
                if ("import %s" % b) in text or ("from %s" % b) in text]
        _check("%s imports no inference path" % Path(mod.__file__).name,
               not hits, hits)
    sieve_src = Path(SIEVES["every_exemption_cites_a_ruling_or_an_impossibility"]
                     .__code__.co_filename)
    _check("the sieve lives in the inspector, not in a device",
           "machines/build_inspector" in str(sieve_src), sieve_src)


def test_THE_WATCH_PROBE_IS_ARMED_AND_CAN_FIRE():
    """A probe that has never been shown to fire is a green light with no bulb.

    The trigger is exercised against a corpus that HAS an untriaged site, so the
    'no untriaged sites' reading this probe gives today is a measurement rather
    than a property of a predicate that cannot say anything else.
    """
    from cairn.tools.base.probe import Probe
    import cairn.machines.exemptions.probes.\
        every_exemption_cites_a_ruling_or_an_impossibility as W

    _check("PROBE is a frozen Probe", isinstance(W.PROBE, Probe), type(W.PROBE))
    _check("it carries a carry and an enough",
           callable(W.PROBE.carry) and callable(W.PROBE.enough))
    _check("and a why that says what silence would mean",
           len(W.PROBE.why or "") > 40, W.PROBE.why)

    ctx = {}
    quiet = W._trigger(None, ctx)
    _check("it is quiet over today's corpus", quiet is False, ctx.get("untriaged"))
    _check("because every swept site is declared or acknowledged",
           ctx["swept_sites"] > 0 and ctx["declared_sites"] > 0, ctx)
    _check("and its quiet carry still reports both counts",
           W._carry(ctx)["declared_sites"] == ctx["declared_sites"])

    # THE FIRING TOOTH — an exemption-shaped construct nobody entered.
    real_ack = W._ACKNOWLEDGED
    try:
        W._ACKNOWLEDGED = {}          # the acknowledged non-site becomes untriaged
        loud = {}
        _check("it fires the moment a site is neither declared nor acknowledged",
               W._trigger(None, loud) is True, loud.get("untriaged"))
        body = W._carry(loud)
        _check("and names the offending path in what it carries",
               any("clearance_actually_gates" in u for u in body["untriaged"]),
               body["untriaged"])
        _check("and its finding says which of the two things went wrong",
               "fallen behind" in body["finding"], body["finding"])
    finally:
        W._ACKNOWLEDGED = real_ack

    _check("and it is quiet again once the acknowledgement is restored",
           W._trigger(None, {}) is False)
    _check("enough never clears — the corpus never stops growing sites",
           W._enough({}) is False)


def main():
    for fn in (test_AN_ABSENT_SET_REDS,
               test_AN_UNREADABLE_SET_REDS,
               test_AN_EMPTY_SET_REDS,
               test_A_SET_THAT_DROPPED_ITS_OWN_ENTRY_REDS,
               test_A_RULING_THAT_DOES_NOT_RESOLVE_REDS,
               test_AN_EMPTY_IMPOSSIBILITY_REDS,
               test_A_SYMBOL_THAT_MOVED_REDS,
               test_THE_LIVE_SET_CARRIES_THE_SEVEN_MEASURED_SITES,
               test_THE_SIEVE_IS_REGISTERED_AND_IN_THE_NEST,
               test_NOTHING_IN_THE_CLOSURE_REACHES_AN_LLM,
               test_THE_WATCH_PROBE_IS_ARMED_AND_CAN_FIRE):
        print(fn.__name__)
        fn()
    print("\n%d passed, %d failed" % (PASS, FAIL))
    return 1 if FAIL else 0


if __name__ == "__main__":
    raise SystemExit(main())
