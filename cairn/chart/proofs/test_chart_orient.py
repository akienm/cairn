"""Proof: the orient nexus v0 — the floor reports only what EXISTS, the schema gate
refuses what a hollow build would emit, provenance travels per-field, and the packet
berths gated in instance-space.

Hermetic where it mutates (a fabricated temp root — no live snapshot values are
pinned); the two live-root teeth assert MEMBERSHIP invariants only. Exit 0 = green.
"""
import ast
import json
import os
import shutil
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from cairn.chart.orient import (AUTHORED_FIELDS, OrientRefused, component_roster,
                                floor_facts, ref_exists, validate_orient, write_packet)

ORIENT_PY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "orient.py"))
ALLOWED_IMPORTS = {"__future__", "hashlib", "json", "os", "re", "time", "pathlib",
                   "cairn.orient.orient"}


def make_root():
    root = tempfile.mkdtemp(prefix="chart_orient_proof_")
    # gamma carries code but NO charter — the census sees it, the roster must not
    for comp in ("alpha", "beta", "gamma"):
        os.makedirs(os.path.join(root, "cairn", comp))
        with open(os.path.join(root, "cairn", comp, comp + ".py"), "w") as fh:
            fh.write("x = 1\n")
        if comp != "gamma":
            with open(os.path.join(root, "cairn", comp, "intention+why.json"), "w") as fh:
                fh.write("{}\n")
    os.makedirs(os.path.join(root, "skills", "chart"))
    return root


def good_packet():
    return {
        "intent": "close alpha's gate against hollow input",
        "domain": "alpha",
        "scope": "the gate only, not beta's consumption of it",
        "refs": ["alpha", "cairn/alpha/intention+why.json"],
        "unknowns": ["whether beta consumes the gated output"],
        "confidence": 0.8,
        "provenance": {"intent": "claude", "domain": "floor", "scope": "claude",
                       "refs": "floor", "unknowns": "claude"},
    }


def expect_refusal(fn, needle):
    try:
        fn()
    except OrientRefused as err:
        assert needle in str(err), "refusal lacks %r: %s" % (needle, err)
        return
    raise AssertionError("expected OrientRefused mentioning %r, got none" % needle)


def test_empty_request_refuses(root):
    expect_refusal(lambda: floor_facts("   ", root=root), "empty")


def test_floor_reports_only_what_exists(root):
    facts = floor_facts(
        "fix alpha using cairn/alpha/intention+why.json and bogus/nowhere.py", root=root)
    assert facts["stratum"] == "floor"
    assert facts["components_mentioned"] == ["alpha"]
    assert "cairn/alpha/intention+why.json" in facts["paths_found"]
    assert "bogus/nowhere.py" in facts["paths_missing"]
    assert not set(facts["paths_found"]) & set(facts["paths_missing"]), \
        "found and missing must stay separate, never merged"


def test_floor_slash_verb_is_a_skill_not_a_path(root):
    facts = floor_facts("run /chart on beta", root=root)
    assert facts["skills_mentioned"] == ["chart"]
    assert "/chart" not in facts["paths_missing"], \
        "a known slash-verb is a skill mention, not a missing-path claim"
    assert facts["components_mentioned"] == ["beta"]


def test_schema_gate_refuses_missing_fields(root):
    packet = good_packet()
    del packet["scope"]
    expect_refusal(lambda: validate_orient(packet, root=root), "scope")


def test_schema_gate_refuses_bad_confidence(root):
    over = dict(good_packet(), confidence=1.5)
    expect_refusal(lambda: validate_orient(over, root=root), "confidence")
    boolean = dict(good_packet(), confidence=True)
    expect_refusal(lambda: validate_orient(boolean, root=root), "confidence")


def test_invented_ref_refuses(root):
    packet = good_packet()
    packet["refs"] = list(packet["refs"]) + ["minted/place.py"]
    expect_refusal(lambda: validate_orient(packet, root=root), "minted/place.py")


def test_provenance_must_cover_authored_fields(root):
    uncovered = good_packet()
    del uncovered["provenance"]["refs"]
    expect_refusal(lambda: validate_orient(uncovered, root=root), "refs")
    vibes = good_packet()
    vibes["provenance"]["scope"] = "vibes"
    expect_refusal(lambda: validate_orient(vibes, root=root), "vibes")


def test_good_packet_validates_and_berths(root):
    berth = os.path.join(root, "instance", "packets")
    packet = good_packet()
    assert validate_orient(packet, root=root) is packet
    path = write_packet(packet, instance_dir=berth, root=root)
    assert os.path.basename(path).startswith("orient-")
    with open(path) as fh:
        assert json.load(fh) == packet, "the berthed packet must round-trip whole"


def test_write_door_is_gated(root):
    berth = os.path.join(root, "instance", "gated")
    hollow = dict(good_packet(), intent="   ")
    expect_refusal(lambda: write_packet(hollow, instance_dir=berth, root=root), "intent")
    assert not os.path.isdir(berth) or not os.listdir(berth), \
        "a refused packet must leave nothing behind the door"


def test_live_roster_carries_chart(root):
    live = component_roster()
    assert "chart" in live and "librarian" in live, \
        "membership invariant: components with charters ride the roster"
    assert set(AUTHORED_FIELDS) == {"intent", "domain", "scope", "refs", "unknowns"}


def test_floor_composes_the_orient_instrument(root):
    """The roster comes from the orient instrument's census, filtered to
    charter-on-disk — never a parallel territory scan. gamma has code but no
    charter: the census sees it, the roster must not (a component without an
    intention doesn't run). Provenance of this tooth: the nexus's first live
    fire, 2026-07-28 — the floor's own parallel roster caught its builder
    having never surveyed cairn/orient."""
    assert component_roster(root) == ["alpha", "beta"]


def test_ticket_claim_is_gated(root):
    """A packet may claim its ticket only if the ticket is ON FILE in
    CairnCommons/tickets/ (packet-inspector-wire, 2026-07-28) — a packet claiming
    an unfiled ticket is fabricated attribution (the 2026-07-26 class). The
    synthetic root has no commons beside it, so any claim there refuses; the
    live-root pass is a membership invariant against a committed ticket."""
    minted = dict(good_packet(), ticket="no-such-ticket")
    expect_refusal(lambda: validate_orient(minted, root=root), "no-such-ticket")
    hollow = dict(good_packet(), ticket="")
    expect_refusal(lambda: validate_orient(hollow, root=root), "ticket")
    live = dict(good_packet(), refs=["chart"], ticket="moreabout")
    assert validate_orient(live) is live, \
        "a claim naming a filed ticket passes (moreabout.json is committed)"
    assert ref_exists("chart") and not ref_exists("minted/nowhere.py"), \
        "the public ref semantics are the gate's own (one implementation, two mouths)"


def test_import_allowlist(root):
    """Stdlib plus EXACTLY ONE door into the house: cairn.orient.orient (the
    settled measurer). Any other cairn import is a second door or a re-derivation."""
    tree = ast.parse(open(ORIENT_PY).read())
    seen = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            seen.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            seen.add(module if module.startswith("cairn") else module.split(".")[0])
    stray = seen - ALLOWED_IMPORTS
    assert not stray, "orient.py imports outside its allowlist: %s" % sorted(stray)


def main():
    root = make_root()
    teeth = [fn for name, fn in sorted(globals().items()) if name.startswith("test_")]
    try:
        for tooth in teeth:
            tooth(root)
            print("PASS %s" % tooth.__name__)
    finally:
        shutil.rmtree(root, ignore_errors=True)
    print("green: %d teeth" % len(teeth))


if __name__ == "__main__":
    main()
