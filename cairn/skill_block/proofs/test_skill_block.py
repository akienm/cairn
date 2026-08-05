"""Proof for cairn/skill_block — teeth a hollow seam could not pass.

Every call runs against injected roots (a temp skills tree, a temp berth root, a temp
trace root); the live berths, the real skills/ charters and the real trace directory are
never read or written. NON-VACUITY is structural: each refusal tooth is paired with the
green path it must NOT refuse, so a seam that refuses everything fails the green half and
one that passes everything fails the refusal half.

    python3 cairn/skill_block/proofs/test_skill_block.py     # exit 0 = green
"""

from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO))

from cairn.learning_block import learning_block as lb  # noqa: E402
from cairn.skill_block import skill_block as sb  # noqa: E402
from cairn.tester.scratch import scratch_dir  # noqa: E402

NOW = datetime(2026, 8, 1, 12, 0, 0, tzinfo=timezone.utc)

CONTRACT = {"what": "why what matters", "exit": "why exit matters",
            "bullets": "why bullets matter"}

GOOD = {
    "what": "a thing",
    "exit": "routed_forward",
    "bullets": [{"text": "a bullet", "stratum": "code"}],
}


def world():
    return scratch_dir("sb-proof-")


def skills_tree(*names, contract=None):
    """A temp skills/ tree with a charter per name. The seam must read the CHARTER —
    that is the template claim's whole mechanism."""
    root = world()
    for name in names:
        d = root / name
        d.mkdir(parents=True)
        (d / "intention+why.json").write_text(json.dumps({
            "component": f"skill:/{name}",
            "input_contract": dict(CONTRACT if contract is None else contract),
        }))
    return root


# ── the seam: contract comes from the charter ────────────────────────────────

def test_contract_is_read_from_the_charter():
    root = skills_tree("alpha")
    c = sb.load_contract("alpha", skills_root=root)
    assert c["block"] == "skill:alpha", f"block namespaced by skill: {c}"
    assert set(c["requires"]) == set(CONTRACT), f"charter fields are the contract: {c}"


def test_a_skill_with_no_charter_is_refused():
    root = skills_tree("alpha")
    try:
        sb.load_contract("ghost", skills_root=root)
    except sb.SkillBlockRefused as exc:
        assert "no charter" in str(exc), exc
        return
    raise AssertionError("a skill with no charter must not fire as a block")


def test_a_charter_with_no_contract_is_refused():
    root = world()
    (root / "bare").mkdir(parents=True)
    (root / "bare" / "intention+why.json").write_text(json.dumps({"component": "x"}))
    try:
        sb.load_contract("bare", skills_root=root)
    except sb.SkillBlockRefused as exc:
        assert "input_contract" in str(exc), exc
        return
    raise AssertionError(
        "an absent contract must not read as an empty one — that door passes everything")


def test_an_empty_contract_is_refused():
    root = skills_tree("hollow", contract={})
    try:
        sb.load_contract("hollow", skills_root=root)
    except sb.SkillBlockRefused:
        return
    raise AssertionError("an empty input_contract is the vacuous gate, not a lenient one")


# ── THE TEMPLATE CLAIM (ticket falsifier 5), tested now, not at skill #2 ──────

def test_a_second_skill_needs_no_code_change():
    """Two skills fire through the SAME call with no argument but the name, and the
    seam's own source is not touched between them. If this tooth ever needs a code
    edit to pass, child b produced a one-off and not the template brick."""
    root = skills_tree("alpha", "beta")
    berths, traces = world(), world()
    before = (Path(sb.__file__)).read_text()
    a = sb.fire("alpha", dict(GOOD), now=NOW, skills_root=root, berths=berths,
                trace_root=traces)
    b = sb.fire("beta", dict(GOOD), now=NOW, skills_root=root, berths=berths,
                trace_root=traces)
    after = (Path(sb.__file__)).read_text()
    assert before == after, "the seam's source must not change between two tenants"
    assert a["berth"] != b["berth"], "two skills berth separately"
    assert a["block"] == "skill:alpha" and b["block"] == "skill:beta"
    assert Path(a["berth"]).is_file() and Path(b["berth"]).is_file()


# ── the DOOR: every lack, first pass, and the refusal COUNTS ─────────────────

def test_door_names_every_lack_in_one_pass():
    root = skills_tree("alpha")
    berths, traces = world(), world()
    try:
        sb.fire("alpha", {"what": "only this"}, now=NOW, skills_root=root,
                berths=berths, trace_root=traces)
    except lb.DoorRefused as exc:
        fields = {l["field"] for l in exc.lacks}
        assert fields == {"exit", "bullets"}, (
            f"a dribbled refusal costs a round-trip per field; got {fields}")
        return
    raise AssertionError("an insufficient firing must be refused")


def test_a_refusal_is_traced_so_the_denominator_survives():
    root = skills_tree("alpha")
    berths, traces = world(), world()
    try:
        sb.fire("alpha", {"what": "only this"}, now=NOW, skills_root=root,
                berths=berths, trace_root=traces)
    except lb.DoorRefused:
        pass
    recs = lb.read_trace("skill:alpha", root=traces)
    assert [r["event"] for r in recs] == ["send_back"], (
        f"a refused firing that leaves no record destroys the refusal rate: {recs}")
    assert lb.dial("skill:alpha", root=traces)["send_backs"] == 1


def test_an_empty_bullet_list_is_a_lack_not_a_value():
    """`bullets: []` is the ABSENCE of a bullet list wearing the field's name. Before
    2026-08-01 it sailed through check_input as 'present'."""
    root = skills_tree("alpha")
    berths, traces = world(), world()
    try:
        sb.fire("alpha", dict(GOOD, bullets=[]), now=NOW, skills_root=root,
                berths=berths, trace_root=traces)
    except lb.DoorRefused as exc:
        assert {l["field"] for l in exc.lacks} == {"bullets"}, exc.lacks
        return
    raise AssertionError("an empty collection must be read as a lack")


def test_a_conforming_firing_passes_and_is_traced_green():
    root = skills_tree("alpha")
    berths, traces = world(), world()
    out = sb.fire("alpha", dict(GOOD), now=NOW, skills_root=root, berths=berths,
                  trace_root=traces)
    events = [r["event"] for r in lb.read_trace("skill:alpha", root=traces)]
    assert events == ["door_pass", "finding"], f"greens are the denominator: {events}"
    assert out["exit"] == "routed_forward"


# ── the FINDING: BOTH exits, and the kill has nothing to hang on ─────────────

def test_the_ticketless_kill_exit_reaches_the_gate():
    """The routed_out firing — a node killed because nothing traced to the Telos — has
    no ticket, no downstream artifact, nothing. It is the most valuable firing in the
    system and the only one that vanishes into conversation today. If the finding path
    required a subject to attach to, THIS is the case that could not be recorded."""
    root = skills_tree("alpha")
    berths, traces = world(), world()
    out = sb.fire("alpha", dict(GOOD, exit="routed_out",
                                bullets=[{"text": "nothing traces to the Telos",
                                          "stratum": "code"}]),
                  now=NOW, skills_root=root, berths=berths, trace_root=traces)
    assert out["exit"] == "routed_out"
    pend = lb.pending_findings("skill:alpha", root=traces)
    assert len(pend) == 1 and pend[0]["id"] == out["finding_id"], (
        f"the kill must stand at Akien's gate like any other finding: {pend}")
    berth = json.loads(Path(out["berth"]).read_text())
    assert berth["exit"] == "routed_out" and berth["bullets"], berth


def test_an_unknown_exit_is_refused():
    root = skills_tree("alpha")
    berths, traces = world(), world()
    try:
        sb.fire("alpha", dict(GOOD, exit="sideways"), now=NOW, skills_root=root,
                berths=berths, trace_root=traces)
    except sb.SkillBlockRefused as exc:
        assert "sideways" in str(exc), exc
        return
    raise AssertionError("the two exits are counted separately; a third is a typo")


def test_a_hand_claimed_hex_bullet_is_refused():
    root = skills_tree("alpha")
    berths, traces = world(), world()
    try:
        sb.fire("alpha", dict(GOOD, bullets=[{"text": "x", "stratum": "hex"}]),
                now=NOW, skills_root=root, berths=berths, trace_root=traces)
    except lb.FindingRefused as exc:
        assert "hex" in str(exc), exc
        return
    raise AssertionError("a hand-authored hex bullet is invented provenance")


# ── the BERTH: what the gate downstream will read ────────────────────────────

def test_the_berth_carries_what_the_gate_needs():
    root = skills_tree("alpha")
    berths, traces = world(), world()
    out = sb.fire("alpha", dict(GOOD), now=NOW, skills_root=root, berths=berths,
                  trace_root=traces)
    doc = sb.read_berth(out["berth"])
    assert doc["skill"] == "alpha", "the gate reads which skill actually fired"
    assert doc["trace_id"] == out["trace_id"] and doc["finding_id"] == out["finding_id"]
    assert doc["answers"]["what"] == "a thing" and "bullets" not in doc["answers"]


def test_read_berth_returns_none_rather_than_raising():
    assert sb.read_berth("/nonexistent/berth.json") is None
    junk = world() / "junk.json"
    junk.write_text("{not json")
    assert sb.read_berth(junk) is None, (
        "a gate turns this into a finding WITH THE ADDRESS; an exception says nothing")


# ── the shell reach — the door and the finding, from where a skill lives ─────

def _cli(*args, cwd=REPO):
    """The shell reach, run against INJECTED roots. The first draft of this tooth wrote
    a send_back into /intent's LIVE trace — a proof-run refusal landing in the exact
    counter the intent-door-refusals watch measures. A proof that pollutes the
    denominator it will later be read against is a proof that breaks its own measure."""
    return subprocess.run([sys.executable, "-m", "cairn.skill_block", *args],
                          capture_output=True, text=True, cwd=cwd,
                          env={"PYTHONPATH": str(REPO), "PATH": "/usr/bin:/bin",
                               "HOME": str(Path.home()),
                               "CAIRN_LB_TRACE_ROOT": str(_CLI_TRACES),
                               "CAIRN_SKILL_BERTHS": str(_CLI_BERTHS)})


# Fires against the REAL skills/intent charter on purpose — this is the tooth that says
# /intent itself is wired, not that the seam works in a fixture world.
_CLI_TRACES, _CLI_BERTHS = world(), world()
LIVE_GOOD = {
    # from_idea joined the LIVE contract 2026-08-04 with skill:/idea; this fixture fires
    # against that contract, so it takes the named exemption with a referent the judge can
    # actually open (build_inspector.reason_has_referent) — a proof packet has no idea behind it.
    "from_idea": "none, because this packet is a proof fixture exercising the wire, not an "
                 "intention — see cairn/skill_block/proofs/test_skill_block.py",
    "what": "a test firing against the real contract",
    "how": "run the CLI",
    "traces_to": "Law 8 — the proof is the entry",
    "shape": "aside",
    "falsifier": "the CLI exits non-zero",
    "exit": "routed_forward",
    "bullets": [{"text": "the wire is reachable from bash", "stratum": "code"}],
    # The real contract requires the challenge pass (ticket challenge-fires-at-intent);
    # a live-wire tooth without it would red for the packet, not the wire.
    "challenge": {"better_approach": "none — a CLI reach test has one shape",
                  "prior_art": "this proof file", "hidden_assumption": "none load-bearing",
                  "real_collision": "none", "back_up": "proceed"},
}


def test_cli_fires_and_refuses_with_honest_exit_codes():
    packet = world() / "p.json"
    packet.write_text(json.dumps(LIVE_GOOD))
    r = _cli("fire", "intent", str(packet))
    assert r.returncode == 0, f"a conforming firing exits 0: {r.stderr}"
    out = json.loads(r.stdout)
    assert out["block"] == "skill:intent" and Path(out["berth"]).is_file()

    bad = world() / "bad.json"
    bad.write_text(json.dumps({"what": "missing the rest"}))
    r = _cli("fire", "intent", str(bad))
    assert r.returncode == 2, f"a refusal exits 2: {r.returncode}"
    for field in ("exit", "bullets", "falsifier", "how", "traces_to", "shape"):
        assert field in r.stderr, f"every lack named on the first pass: {r.stderr}"


def test_the_proof_never_touches_the_live_trace():
    """Non-vacuity for the tooth above: assert the injection actually took."""
    live = Path.home() / ".cairn/devices/learning_block/0/traces/skill:intent.jsonl"
    before = live.read_text() if live.exists() else None
    packet = world() / "p.json"
    packet.write_text(json.dumps(LIVE_GOOD))
    assert _cli("fire", "intent", str(packet)).returncode == 0
    after = live.read_text() if live.exists() else None
    assert before == after, (
        "the proof wrote into /intent's live denominator — the watch reads that counter")


def test_the_wire_is_not_fatal_when_the_ROOTS_are_unwritable():
    """Measured at this build's live fire: an unwritable berth root wedged /intent with a
    raw PermissionError traceback. The recording must never stop the work — /intent is the
    cheapest gate in the system only if firing it costs nothing. Exits 0, prints NO berth,
    and says out loud that nothing was recorded; the downstream BUILDME gate is what turns
    that missing berth into a refusal later, so the loss surfaces at a door rather than
    never. Distinct from a DoorRefused, which is the packet being wrong and stays fatal."""
    locked = world()
    (locked / "sub").mkdir()
    (locked / "sub").chmod(0o500)
    try:
        packet = world() / "p.json"
        packet.write_text(json.dumps(LIVE_GOOD))
        r = subprocess.run(
            [sys.executable, "-m", "cairn.skill_block", "fire", "intent", str(packet)],
            capture_output=True, text=True, cwd=REPO,
            env={"PYTHONPATH": str(REPO), "PATH": "/usr/bin:/bin", "HOME": str(Path.home()),
                 "CAIRN_LB_TRACE_ROOT": str(locked / "sub" / "traces"),
                 "CAIRN_SKILL_BERTHS": str(locked / "sub" / "berths")})
        assert r.returncode == 0, f"the wire must not wedge the skill: {r.stderr}"
        assert json.loads(r.stdout)["berth"] is None, \
            "a firing that was not recorded must not print a berth path"
        assert "NO BERTH EXISTS" in r.stderr, \
            f"the loss must be loud at the diagnostic surface: {r.stderr}"
        assert "Traceback" not in r.stderr, f"a raw traceback is not a diagnostic: {r.stderr}"
    finally:
        (locked / "sub").chmod(0o700)


def test_cli_refuses_an_unreadable_packet_by_name():
    r = _cli("fire", "intent", "/nonexistent/packet.json")
    assert r.returncode == 2 and "unreadable" in r.stderr, r.stderr


# ── challenge fires at intent (ticket challenge-fires-at-intent) ─────────────
# Falsifier clause 1 as teeth: /challenge is a REQUIRED step of /intent, and an
# edit softening it back to optional goes RED here. The first two read the REAL
# charter and the REAL skill text — membership/absence invariants, never sentence
# snapshots, so a legitimate rewording survives and only a softening reds.

def test_challenge_is_required_at_the_real_intent_door():
    """The door reads the contract from the live charter at fire time, so THIS
    membership assert is the required-ness: drop the field and the door goes cold."""
    c = sb.load_contract("intent")
    assert "challenge" in c["requires"], (
        "skills/intent/intention+why.json input_contract no longer requires "
        "'challenge' — the softening edit falsifier clause 1 exists to catch")


def test_door_refuses_an_unchallenged_firing_naming_the_lack():
    """The mechanism, in a fixture world: a contract carrying challenge refuses a
    firing without it, the lack NAMED in the one-pass list."""
    root = skills_tree("alpha", contract=dict(CONTRACT, challenge="why the pass is forced"))
    berths, traces = world(), world()
    try:
        sb.fire("alpha", dict(GOOD), now=NOW, skills_root=root,
                berths=berths, trace_root=traces)
    except lb.DoorRefused as exc:
        assert {l["field"] for l in exc.lacks} == {"challenge"}, exc.lacks
    else:
        raise AssertionError("an unchallenged firing must be refused")
    # NON-VACUITY: the same fixture passes once the answers ride along.
    out = sb.fire("alpha", dict(GOOD, challenge={"prior_art": "none found, consulted x"}),
                  now=NOW, skills_root=root, berths=berths, trace_root=traces)
    assert Path(out["berth"]).is_file()


def test_the_live_text_carries_challenge_as_required():
    """The executor is an LLM reading markdown — the step must stand in the text the
    door will point at. Invariants: the optional-route phrasing is GONE, and some line
    names /challenge together with required-ness. The charter's routing must not call
    it optional either."""
    text = (REPO / "skills" / "intent" / "SKILL.md").read_text()
    assert "if the design wants" not in text, (
        "the optional-route phrasing is back in skills/intent/SKILL.md")
    assert any("challenge" in ln.lower() and "required" in ln.lower()
               for ln in text.splitlines()), (
        "no line in skills/intent/SKILL.md states the challenge step as required")
    charter = json.loads((REPO / "skills" / "intent" / "intention+why.json").read_text())
    routes = json.dumps(charter.get("nexus", {}))
    assert "optional adversarial pass" not in routes, (
        "the charter's routing still calls /challenge optional")


# ── the intent gate at the chokepoint (ticket falsifier 6) ───────────────────

def _tickets(**fields):
    """A fixture world shaped the way ticket_path() reads one: the root handed to the
    gate is the CAIRN_ROOT analogue, and the tickets live in its SIBLING CairnCommons —
    the two roots, not one folder. The first draft handed over the parent instead, so
    every ticket read as unfiled and four gate teeth passed VACUOUSLY on the silent
    path. Composing ticket_path rather than joining the path here is what keeps this
    fixture honest against the real reader."""
    parent = world()
    (parent / "CairnCommons" / "tickets").mkdir(parents=True)
    for name, doc in fields.items():
        (parent / "CairnCommons" / "tickets" / f"{name}.json").write_text(json.dumps(doc))
    root = parent / "cairn"
    root.mkdir()
    return root


def test_gate_reds_a_ticket_that_names_no_intent_firing():
    from cairn.build_inspector.inspector import buildme_rides_the_intent as gate
    root = _tickets(t={"id": "t"})
    found = gate("t", tickets_root=root)
    assert len(found) == 1, f"one finding, complete on the first pass: {found}"
    assert found[0]["filter"] == "buildme_rides_the_intent"
    assert "intent_berth" in found[0]["finding"], found[0]


def test_gate_greens_a_ticket_naming_a_real_intent_berth():
    from cairn.build_inspector.inspector import buildme_rides_the_intent as gate
    skills, berths, traces = skills_tree("intent"), world(), world()
    out = sb.fire("intent", dict(GOOD), now=NOW, skills_root=skills, berths=berths,
                  trace_root=traces)
    root = _tickets(t={"id": "t", "intent_berth": out["berth"]})
    assert gate("t", tickets_root=root) == [], "a real berth opens the door"


def test_gate_reds_a_berth_that_does_not_resolve():
    from cairn.build_inspector.inspector import buildme_rides_the_intent as gate
    root = _tickets(t={"id": "t", "intent_berth": "/nowhere/intent-000.json"})
    found = gate("t", tickets_root=root)
    assert len(found) == 1 and "does not read" in found[0]["finding"], found


def test_gate_reds_a_berth_for_the_wrong_skill():
    """Otherwise ANY berth satisfies a field named intent_berth."""
    from cairn.build_inspector.inspector import buildme_rides_the_intent as gate
    skills, berths, traces = skills_tree("alpha"), world(), world()
    out = sb.fire("alpha", dict(GOOD), now=NOW, skills_root=skills, berths=berths,
                  trace_root=traces)
    root = _tickets(t={"id": "t", "intent_berth": out["berth"]})
    found = gate("t", tickets_root=root)
    assert len(found) == 1 and "not 'intent'" in found[0]["finding"], found


def test_gate_accepts_a_NAMED_exemption_and_refuses_a_blank_one():
    """25 of 70 filed tickets predate this door. Silence reds; an honest, judgeable
    exemption passes — the shape /sorted already uses for watchme."""
    from cairn.build_inspector.inspector import buildme_rides_the_intent as gate
    root = _tickets(
        good={"id": "good", "intent_berth": "none, because cast before the door existed"},
        blank={"id": "blank", "intent_berth": "none, because "},
    )
    assert gate("good", tickets_root=root) == [], "a named exemption is legal"
    found = gate("blank", tickets_root=root)
    assert len(found) == 1 and "no reason" in found[0]["finding"], (
        f"an exemption with a blank reason is silence with a prefix on it: {found}")
    # The blank case is exactly where a .strip() before the prefix test hides: it eats
    # the trailing space and the value falls through to the path branch, redding for a
    # reason that would send the reader to fix a berth path that was never one.
    assert "does not read" not in found[0]["finding"], (
        f"redded as a bad path instead of a blank exemption: {found[0]['finding']}")


def test_gate_stays_silent_on_an_unfiled_ticket():
    """Two filters reporting one fault is noise; the chokepoint already refuses a
    named-but-uncast ticket by name."""
    from cairn.build_inspector.inspector import buildme_rides_the_intent as gate
    root = _tickets(real={"id": "real"})
    assert gate("ghost", tickets_root=root) == []
    # NON-VACUITY: the same root reds a ticket that IS on file, so the silence above
    # is the unfiled rule and not a fixture the gate simply cannot see.
    assert gate("real", tickets_root=root), "the fixture must be readable at all"


# ── runner ───────────────────────────────────────────────────────────────────

TEETH = [v for k, v in sorted(globals().items()) if k.startswith("test_")]

if __name__ == "__main__":
    failed = 0
    for tooth in TEETH:
        try:
            tooth()
            print(f"  green  {tooth.__name__}")
        except Exception as exc:
            failed += 1
            print(f"  RED    {tooth.__name__}: {exc}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    sys.exit(1 if failed else 0)
