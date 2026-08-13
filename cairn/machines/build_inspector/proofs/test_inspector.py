"""Proofs for build_inspector — sieves judge measurements, findings are complete,
and the gate cannot silently inspect nothing.

Hermetic: a synthetic tree pins each sieve's fire-and-stay-quiet behavior; the real
tree is asserted by invariant only (shape and floors, never a snapshot of findings —
the sweep's real findings are work items, not constants; memory:
proof-over-live-data-assert-invariants).
"""

from __future__ import annotations

import json
import pathlib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.machines.build_inspector.inspector import SIEVES, inspect  # noqa: E402
from cairn.tools.charter import projector  # noqa: E402
from cairn.tools.orient.orient import ScanRefused  # noqa: E402
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402

# "score" joined 2026-08-06 (the-questions-are-the-sieve): a finding carries the DATUM
# (evidence, under the name it has always had) AND the score — the datum read against
# the requirement, which the datum alone cannot say. Pinned here so a sieve cannot emit
# a bare judgement again.
_FINDING_SHAPE = {"sieve", "component", "finding", "evidence", "score", "why_it_matters"}


def _refuses(fn, because):
    try:
        fn()
    except ScanRefused:
        return
    except Exception as e:  # noqa: BLE001
        raise AssertionError(
            f"THE GATE DID NOT REFUSE — {because}. Instead: {type(e).__name__}: {e}."
        ) from None
    raise AssertionError(f"NO REFUSAL AT ALL — {because}.")


def _component(root: Path, name: str, *, charter=True, proof=True, device=True, emits=True):
    d = root / name
    (d / "proofs").mkdir(parents=True)
    if charter:
        (d / "intention+why.json").write_text('{"component": "%s"}' % name)
    if proof:
        (d / "proofs" / "test_x.py").write_text("assert True\n")
    body = "from base import BaseDevice\n\n\nclass D(BaseDevice):\n    def work(self):\n"
    body += "        self.emit('gate')\n" if emits else "        return 1\n"
    (d / "dev.py").write_text(body if device else "def helper():\n    return 1\n")
    return d


def main() -> None:
    tmp = scratch_dir("inspector-proof-")
    root = tmp / "cairn"

    # A healthy component and one broken per sieve.
    _component(root, "healthy")
    _component(root, "no_charter", charter=False)
    _component(root, "no_proofs", proof=False)
    _component(root, "silent", emits=False)
    _component(root, "plain_lib", device=False, emits=False)  # not a device: silence is fine

    # 1 — a healthy component is CLEAN: a gate that always fires is a smoke alarm
    #     nobody wires in (and 'plain_lib' shows silent_device scopes to devices only).
    r = inspect(root=root, component="healthy")
    assert r["clean"] and r["findings"] == [], r["findings"]
    assert inspect(root=root, component="plain_lib")["clean"]

    # 2 — each seeded failure fires exactly its sieve, nothing else.
    for comp, expected in [("no_charter", "charter_on_disk"),
                           ("no_proofs", "proofs_exist"),
                           ("silent", "silent_device")]:
        f = inspect(root=root, component=comp)["findings"]
        assert [x["sieve"] for x in f] == [expected], (comp, f)

    # 3 — state_is_projection: a voyage written THROUGH THE DOOR is clean...
    h, s = root / "healthy" / "history.json", root / "healthy" / "state.json"
    projector.append_entry(str(h), str(s), {"standing": "BUILDME", "note": "born"})
    assert inspect(root=root, component="healthy")["clean"]

    # 4 — ...and a HAND-EDIT to state.json is caught as drift, with the diverging keys.
    edited = json.loads(s.read_text())
    edited["cursor"] = {"gate": "PROVED"}  # the lie: promotion without a crossing
    s.write_text(json.dumps(edited))
    f = inspect(root=root, component="healthy")["findings"]
    assert [x["sieve"] for x in f] == ["state_is_projection"], f
    assert "cursor" in f[0]["evidence"]["diverging_keys"], f[0]

    # 5 — repair goes through the door (append), never an edit — and the gate agrees.
    projector.append_entry(str(h), str(s), {"standing": "BUILDME", "note": "re-projected"})
    assert inspect(root=root, component="healthy")["clean"]

    # 6 — an orphan half of the pair is a finding (state without history).
    orphan = _component(root, "orphan")
    (orphan / "state.json").write_text("{}")
    f = inspect(root=root, component="orphan")["findings"]
    assert [x["sieve"] for x in f] == ["state_is_projection"] and "without" in f[0]["finding"]

    # 7 — the gate cannot silently inspect nothing: unknown component refuses, and
    #     names what the census actually sees (complete on first pass).
    _refuses(lambda: inspect(root=root, component="ghost"),
             "inspecting a nonexistent component must refuse — a gate that inspects "
             "nothing passes everything")

    # 8 — a bad root refuses (inherited from the census, verified at THIS surface).
    _refuses(lambda: inspect(root=tmp / "nowhere"),
             "a sweep of nowhere must refuse, not report a clean empty world")

    # 9 — every finding is complete on first pass: full shape, non-empty why.
    sweep = inspect(root=root)
    assert not sweep["clean"]
    for x in sweep["findings"]:
        assert set(x) == _FINDING_SHAPE and len(x["why_it_matters"]) > 40, x

    # 10 — THE LEARNING-DEVICE SHAPE: every sieve's docstring carries a provenance
    #      naming its seeding failure (dated or IOU-named) — a sieve nobody was
    #      taught by is refused here, same tooth as orient's scans.
    for name, judge in SIEVES.items():
        doc = judge.__doc__ or ""
        assert "Provenance:" in doc, f"{name}: no provenance — a check nobody was taught by"

    # 11 — REAL TREE, invariants only: the sweep runs, sees the tree, exits gate-ably.
    real = inspect()
    assert real["components_inspected"] >= 10, "the sweep barely saw the tree"
    assert real["sieves_run"] == sorted(SIEVES)
    for x in real["findings"]:
        assert set(x) == _FINDING_SHAPE, x
    assert real["clean"] == (not real["findings"])

    # 12 — the inspector is inference-free BY IMPORT: no deepen, no inference_domain,
    #      no outbound-capable module in inspector.py.
    import ast as _ast
    src = (_REPO_ROOT / "cairn" / "machines" / "build_inspector" / "inspector.py").read_text()
    tree = _ast.parse(src)
    imported = {
        n.name.split(".")[0]
        for node in _ast.walk(tree) if isinstance(node, _ast.Import) for n in node.names
    } | {
        node.module.split(".")[0]
        for node in _ast.walk(tree)
        if isinstance(node, _ast.ImportFrom) and node.module
    }
    forbidden = {"urllib", "http", "requests", "httpx", "aiohttp", "socket"}
    assert not (imported & forbidden), f"outbound-capable import: {imported & forbidden}"
    assert "deepen" not in src.split('"""', 2)[2], (
        "the inspector consults no oracle — a gate that asks Hex is not a gate"
    )

    # 13 — PACKET JURISDICTION (packet-inspector-wire, 2026-07-28): the gate finds a
    #      build's charted packets via history -> ticket -> berth and judges the
    #      charted refs at promotion. Fire-and-stay-quiet, berths on a synthetic root.
    import cairn.machines.build_inspector.inspector as _insp
    berths = tmp / "berths"
    (berths / "0" / "packets").mkdir(parents=True)
    saved_berths = _insp._CHART_BERTHS
    _insp._CHART_BERTHS = berths
    try:
        charted = _component(root, "charted")
        h2, s2 = charted / "history.json", charted / "state.json"
        projector.append_entry(str(h2), str(s2),
                               {"standing": "BUILDME", "note": "born", "ticket": "wire-proof"})
        p = berths / "0" / "packets"
        # A berth claiming ANOTHER ticket is outside this build's jurisdiction: quiet.
        (p / "orient-20260728T000000-aaaa.json").write_text(
            json.dumps({"ticket": "someone-else", "refs": ["no/such/ref.py"]}))
        assert inspect(root=root, component="charted")["clean"]
        # A berth claiming THIS ticket whose charted ref no longer resolves: fires,
        # and the finding separates missing from still-resolving (complete first pass).
        (p / "orient-20260728T000001-bbbb.json").write_text(
            json.dumps({"ticket": "wire-proof", "refs": ["chart", "no/such/ref.py"]}))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["charted_refs_resolve"], f
        assert f[0]["evidence"]["missing"] == ["no/such/ref.py"], f[0]
        # The world matching the chart again: quiet again.
        (p / "orient-20260728T000001-bbbb.json").write_text(
            json.dumps({"ticket": "wire-proof", "refs": ["chart"]}))
        assert inspect(root=root, component="charted")["clean"]

        # 14 — an UNREADABLE berth is a named finding on the berth owner (chart)
        #      exactly once — never on every component's crossing, never skipped.
        _component(root, "chart")
        (p / "orient-20260728T000002-cccc.json").write_text("{not json")
        assert inspect(root=root, component="charted")["clean"], \
            "an unreadable berth must not fire on other components' crossings"
        f = inspect(root=root, component="chart")["findings"]
        assert [x["sieve"] for x in f] == ["charted_refs_resolve"], f
        assert "unreadable" in f[0]["finding"], f[0]
        # 15 — THE JUDGES BEFORE THE JUDGED (constrain-filters): a charted constrain
        #      packet with an unresolvable source fires constraint_traces; an empty
        #      bounds.out fires constraint_bounds_complete; a whole packet is quiet.
        #      (Installed before the constrain module exists — the fixtures here ARE
        #      the module's acceptance contract.)
        whole = {"ticket": "wire-proof",
                 "constraints": [{"text": "stay off the network", "source": "chart",
                                  "kind": "charter"}],
                 "bounds": {"in": ["the gate only"], "out": ["everything else"]}}
        cpath = p / "constrain-20260728T000003-dddd.json"
        cpath.write_text(json.dumps(whole))
        assert inspect(root=root, component="charted")["clean"]
        minted = dict(whole, constraints=[{"text": "obey the minted rule",
                                           "source": "no/such/charter.json",
                                           "kind": "charter"}])
        cpath.write_text(json.dumps(minted))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["constraint_traces"], f
        assert f[0]["evidence"]["source"] == "no/such/charter.json", f[0]
        unbounded = dict(whole, bounds={"in": ["the gate only"], "out": []})
        cpath.write_text(json.dumps(unbounded))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["constraint_bounds_complete"], f
        assert f[0]["evidence"]["side"] == "out", f[0]

        # 16 — ONE IMPLEMENTATION, TWO MOUTHS: the registry sieves report exactly
        #      what the pure judge reports — no drift between door and gate is
        #      possible because there is nothing to drift between.
        from cairn.machines.build_inspector.inspector import judge_constrain
        assert judge_constrain(whole) == []
        assert [x["judge"] for x in judge_constrain(minted)] == ["constraint_traces"]
        assert [x["judge"] for x in judge_constrain(unbounded)] == ["constraint_bounds_complete"]
        cpath.unlink()

        # 17 — THE JUDGES BEFORE THE JUDGED, SECOND INSTANCE (survey-filters): a
        #      charted survey packet with an unresolvable holding fires
        #      survey_holdings_resolve; an empty sought or a measureless absence
        #      fires survey_coverage_complete; a whole packet is quiet. (Installed
        #      before the survey module exists — these fixtures ARE its acceptance
        #      contract, the pattern constrain-filters filed at edge (b).)
        held = {"ticket": "wire-proof",
                "sought": ["a settled measurer of the territory"],
                "holdings": [{"what": "the chart component", "address": "chart"}],
                "absences": [{"what": "a survey module",
                              "measure": "device_census rows, no such component"}]}
        spath = p / "survey-20260728T000004-eeee.json"
        spath.write_text(json.dumps(held))
        assert inspect(root=root, component="charted")["clean"]
        phantom = dict(held, holdings=[{"what": "a phantom holding",
                                        "address": "no/such/thing.py"}])
        spath.write_text(json.dumps(phantom))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["survey_holdings_resolve"], f
        assert f[0]["evidence"]["address"] == "no/such/thing.py", f[0]
        unswept = dict(held, sought=[])
        spath.write_text(json.dumps(unswept))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["survey_coverage_complete"], f
        unmeasured = dict(held, absences=[{"what": "a survey module"}])
        spath.write_text(json.dumps(unmeasured))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["survey_coverage_complete"], f
        assert "measure" in f[0]["finding"], f[0]

        # 18 — one implementation, two mouths, for the survey judge too.
        from cairn.machines.build_inspector.inspector import judge_survey
        assert judge_survey(held) == []
        assert [x["judge"] for x in judge_survey(phantom)] == ["survey_holdings_resolve"]
        assert [x["judge"] for x in judge_survey(unswept)] == ["survey_coverage_complete"]
        assert [x["judge"] for x in judge_survey(unmeasured)] == ["survey_coverage_complete"]
        spath.unlink()

        # 19 — THE JUDGES BEFORE THE JUDGED, THIRD APPLICATION (decompose-filters):
        #      a compose piece using an address the survey berth does not hold fires
        #      decompose_composes_holdings; a build piece filling an unmeasured
        #      absence fires decompose_builds_absences; a broken survey_ref is a
        #      loud finding; a derived split is quiet. (Installed before the
        #      decompose module exists — these fixtures ARE its acceptance contract.)
        sb = tmp / "survey_berth_fixture.json"
        sb.write_text(json.dumps({
            "holdings": [{"what": "the chart component", "address": "chart"}],
            "absences": [{"what": "a decompose module",
                          "measure": "path check, absent"}]}))
        derived = {"ticket": "wire-proof", "survey_ref": str(sb),
                   "sub_problems": [
                       {"what": "compose the chart door", "why": "it is held",
                        "kind": "compose", "uses": ["chart"]},
                       {"what": "build the module", "why": "measured absent",
                        "kind": "build", "fills": "a decompose module"}]}
        dpath = p / "decompose-20260728T000005-ffff.json"
        dpath.write_text(json.dumps(derived))
        assert inspect(root=root, component="charted")["clean"]
        rebuilt = dict(derived, sub_problems=[
            {"what": "compose a phantom", "why": "it is not held",
             "kind": "compose", "uses": ["no/such/thing.py"]}])
        dpath.write_text(json.dumps(rebuilt))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["decompose_composes_holdings"], f
        assert f[0]["evidence"]["uses"] == "no/such/thing.py", f[0]
        invented = dict(derived, sub_problems=[
            {"what": "build a whim", "why": "nobody measured it",
             "kind": "build", "fills": "a thing never sought"}])
        dpath.write_text(json.dumps(invented))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["decompose_builds_absences"], f
        assert f[0]["evidence"]["fills"] == "a thing never sought", f[0]
        broken = dict(derived, survey_ref=str(tmp / "gone.json"))
        dpath.write_text(json.dumps(broken))
        f = inspect(root=root, component="charted")["findings"]
        assert "decompose_composes_holdings" in [x["sieve"] for x in f], f
        assert any("survey berth" in x["finding"] for x in f), f
        dpath.unlink()

        # 20 — one implementation, two mouths, for the decompose judge too.
        from cairn.machines.build_inspector.inspector import judge_decompose
        assert judge_decompose(derived) == []
        assert [x["judge"] for x in judge_decompose(rebuilt)] == ["decompose_composes_holdings"]
        assert [x["judge"] for x in judge_decompose(invented)] == ["decompose_builds_absences"]
        assert [x["judge"] for x in judge_decompose(broken)] and \
            judge_decompose(broken)[0]["judge"] == "decompose_composes_holdings"

        # 21 — THE JUDGES BEFORE THE JUDGED, FOURTH APPLICATION (triage-filters):
        #      an order dropping a split piece fires triage_covers_the_split
        #      naming the dropped piece; an invented or double-ordered piece fires
        #      the same judge; a why_now-less entry fires triage_reasons_the_order;
        #      a broken decompose_ref is a loud finding; a complete reasoned order
        #      is quiet. (Installed before the triage module exists — these
        #      fixtures ARE its acceptance contract.)
        db = tmp / "decompose_berth_fixture.json"
        db.write_text(json.dumps({
            "survey_ref": str(sb),
            "sub_problems": [
                {"what": "compose the chart door", "why": "it is held",
                 "kind": "compose", "uses": ["chart"]},
                {"what": "build the module", "why": "measured absent",
                 "kind": "build", "fills": "a decompose module"}]}))
        ranked = {"ticket": "wire-proof", "decompose_ref": str(db),
                  "order": [
                      {"what": "build the module",
                       "why_now": "the layer below solidifies first"},
                      {"what": "compose the chart door",
                       "why_now": "rides on the module once it stands"}]}
        tpath = p / "triage-20260728T000006-abab.json"
        tpath.write_text(json.dumps(ranked))
        assert inspect(root=root, component="charted")["clean"]
        dropped = dict(ranked, order=ranked["order"][:1])
        tpath.write_text(json.dumps(dropped))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["triage_covers_the_split"], f
        assert f[0]["evidence"]["dropped"] == ["compose the chart door"], f[0]
        invented_rank = dict(ranked, order=ranked["order"] + [
            {"what": "polish a whim", "why_now": "it would be nice"}])
        tpath.write_text(json.dumps(invented_rank))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["triage_covers_the_split"], f
        assert f[0]["evidence"]["what"] == "polish a whim", f[0]
        unreasoned = dict(ranked, order=[
            dict(ranked["order"][0], why_now=""), ranked["order"][1]])
        tpath.write_text(json.dumps(unreasoned))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["triage_reasons_the_order"], f
        assert f[0]["evidence"]["what"] == "build the module", f[0]
        chainless = dict(ranked, decompose_ref=str(tmp / "gone.json"))
        tpath.write_text(json.dumps(chainless))
        f = inspect(root=root, component="charted")["findings"]
        assert "triage_covers_the_split" in [x["sieve"] for x in f], f
        assert any("decompose berth" in x["finding"] for x in f), f
        tpath.unlink()

        # 22 — one implementation, two mouths, for the triage judge too; and the
        #      double-order fires with its counts in evidence.
        from cairn.machines.build_inspector.inspector import judge_triage
        assert judge_triage(ranked) == []
        assert [x["judge"] for x in judge_triage(dropped)] == ["triage_covers_the_split"]
        assert [x["judge"] for x in judge_triage(unreasoned)] == ["triage_reasons_the_order"]
        doubled = dict(ranked, order=ranked["order"] + [ranked["order"][0]])
        frs = judge_triage(doubled)
        assert [x["judge"] for x in frs] == ["triage_covers_the_split"] and \
            frs[0]["evidence"] == {"what": "build the module", "ordered": 2, "split": 1}, frs
        assert judge_triage(chainless) and \
            judge_triage(chainless)[0]["judge"] == "triage_covers_the_split"

        # 23 — THE JUDGES BEFORE THE JUDGED, FIFTH APPLICATION
        #      (hypothesize-filters): a ranked piece with no hypothesis fires
        #      hypothesize_covers_the_ranked naming every uncovered piece; a
        #      hypothesis on an invented piece fires the same judge; a claim
        #      missing falsifier/instrument fires hypothesize_falsifiable_measured
        #      naming ALL missing fields at once; a broken triage_ref is loud; a
        #      full measured covering is quiet. (Installed before the hypothesize
        #      module exists — these fixtures ARE its acceptance contract.)
        tb = tmp / "triage_berth_fixture.json"
        tb.write_text(json.dumps({
            "decompose_ref": str(db),
            "order": [
                {"what": "build the module",
                 "why_now": "the layer below solidifies first"},
                {"what": "compose the chart door",
                 "why_now": "rides on the module once it stands"}]}))
        expected = {"ticket": "wire-proof", "triage_ref": str(tb),
                    "hypotheses": [
                        {"piece": "build the module",
                         "expect": "the module's teeth pass twice",
                         "falsifier": "any tooth red on either run",
                         "instrument": "python3 proofs/test_module.py, twice"},
                        {"piece": "compose the chart door",
                         "expect": "the door refuses a phantom ref",
                         "falsifier": "a phantom ref berths",
                         "instrument": "the door's own gate, fixture ref"}]}
        hpath = p / "hypothesize-20260728T000007-cdcd.json"
        hpath.write_text(json.dumps(expected))
        assert inspect(root=root, component="charted")["clean"]
        uncovered = dict(expected, hypotheses=expected["hypotheses"][:1])
        hpath.write_text(json.dumps(uncovered))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["hypothesize_covers_the_ranked"], f
        assert f[0]["evidence"]["uncovered"] == ["compose the chart door"], f[0]
        invented_h = dict(expected, hypotheses=expected["hypotheses"] + [
            {"piece": "polish a whim", "expect": "it gleams",
             "falsifier": "it does not", "instrument": "a glance"}])
        hpath.write_text(json.dumps(invented_h))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["hypothesize_covers_the_ranked"], f
        assert f[0]["evidence"]["piece"] == "polish a whim", f[0]
        unmeasured_h = dict(expected, hypotheses=[
            dict(expected["hypotheses"][0], falsifier="", instrument="  "),
            expected["hypotheses"][1]])
        hpath.write_text(json.dumps(unmeasured_h))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["hypothesize_falsifiable_measured"], f
        assert f[0]["evidence"]["lacking"] == ["falsifier", "instrument"], f[0]
        chainless_h = dict(expected, triage_ref=str(tmp / "gone.json"))
        hpath.write_text(json.dumps(chainless_h))
        f = inspect(root=root, component="charted")["findings"]
        assert "hypothesize_covers_the_ranked" in [x["sieve"] for x in f], f
        assert any("triage berth" in x["finding"] for x in f), f
        hpath.unlink()

        # 24 — one implementation, two mouths, for the hypothesize judge too.
        from cairn.machines.build_inspector.inspector import judge_hypothesize
        assert judge_hypothesize(expected) == []
        assert [x["judge"] for x in judge_hypothesize(uncovered)] == \
            ["hypothesize_covers_the_ranked"]
        assert [x["judge"] for x in judge_hypothesize(unmeasured_h)] == \
            ["hypothesize_falsifiable_measured"]
        assert judge_hypothesize(chainless_h) and \
            judge_hypothesize(chainless_h)[0]["judge"] == "hypothesize_covers_the_ranked"

        # 25 — THE JUDGES BEFORE THE JUDGED, SIXTH APPLICATION
        #      (validate-filters): a criterion without its instrument fires
        #      validate_measures_done naming all missing fields; a covers entry
        #      on an unclaimed piece fires validate_covers_the_build; a claimed
        #      piece no criterion covers fires the same judge naming every
        #      uncovered piece; a broken hypothesize_ref is loud; a complete
        #      measured criteria set is quiet. (Installed before the validate
        #      module exists — these fixtures ARE its acceptance contract.)
        hb = tmp / "hypothesize_berth_fixture.json"
        hb.write_text(json.dumps({
            "triage_ref": str(tb),
            "hypotheses": [
                {"piece": "build the module",
                 "expect": "the module's teeth pass twice",
                 "falsifier": "any tooth red on either run",
                 "instrument": "python3 proofs/test_module.py, twice"},
                {"piece": "compose the chart door",
                 "expect": "the door refuses a phantom ref",
                 "falsifier": "a phantom ref berths",
                 "instrument": "the door's own gate, fixture ref"}]}))
        done_set = {"ticket": "wire-proof", "hypothesize_ref": str(hb),
                    "criteria": [
                        {"claim": "the whole build is green under seal",
                         "instrument": "the tester's netns seal, both proofs",
                         "covers": ["build the module"]},
                        {"claim": "the composed door holds at promotion",
                         "instrument": "inspect(component=...), clean",
                         "covers": ["compose the chart door"]}]}
        vpath = p / "validate-20260728T000008-efef.json"
        vpath.write_text(json.dumps(done_set))
        assert inspect(root=root, component="charted")["clean"]
        unmeasured_c = dict(done_set, criteria=[
            dict(done_set["criteria"][0], instrument=" "),
            done_set["criteria"][1]])
        vpath.write_text(json.dumps(unmeasured_c))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["validate_measures_done"], f
        assert f[0]["evidence"]["lacking"] == ["instrument"], f[0]
        unclaimed = dict(done_set, criteria=done_set["criteria"] + [
            {"claim": "a whim gleams", "instrument": "a glance",
             "covers": ["polish a whim"]}])
        vpath.write_text(json.dumps(unclaimed))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["validate_covers_the_build"], f
        assert f[0]["evidence"]["covers"] == "polish a whim", f[0]
        partial = dict(done_set, criteria=done_set["criteria"][:1])
        vpath.write_text(json.dumps(partial))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["sieve"] for x in f] == ["validate_covers_the_build"], f
        assert f[0]["evidence"]["uncovered"] == ["compose the chart door"], f[0]
        chainless_v = dict(done_set, hypothesize_ref=str(tmp / "gone.json"))
        vpath.write_text(json.dumps(chainless_v))
        f = inspect(root=root, component="charted")["findings"]
        assert "validate_covers_the_build" in [x["sieve"] for x in f], f
        assert any("hypothesize berth" in x["finding"] for x in f), f
        vpath.unlink()

        # 26 — one implementation, two mouths, for the validate judge too.
        from cairn.machines.build_inspector.inspector import judge_validate
        assert judge_validate(done_set) == []
        assert [x["judge"] for x in judge_validate(unmeasured_c)] == \
            ["validate_measures_done"]
        assert [x["judge"] for x in judge_validate(partial)] == \
            ["validate_covers_the_build"]
        assert judge_validate(chainless_v) and \
            judge_validate(chainless_v)[0]["judge"] == "validate_covers_the_build"

        # 26b — THE FORWARDING ORDER (watchme-emits-a-probe, 2026-07-30). A charted
        #       address stops resolving two ways: the world DRIFTED (the 2026-07-24
        #       failure these ref sieves were built for), or the build's own charted
        #       plan MOVED it. Measured in anger: that ticket's decompose piece (f)
        #       was 'the CALLBACK -> PROBE rename, run FIRST', and running it first
        #       falsified the chart's own orient ref and four survey holdings. The
        #       disposition is a named successor on the ticket — and it is checked at
        #       BOTH ends, so it can never become a way to launder a missing address.
        fwd_tickets = tmp / "CairnCommons" / "tickets"
        fwd_tickets.mkdir(parents=True)
        saved_troot = _insp._TICKETS_ROOT
        _insp._TICKETS_ROOT = str(root)          # ticket_path reads root/../CairnCommons
        tfile = fwd_tickets / "fwd-proof.json"

        def _order(order):
            tfile.write_text(json.dumps({"id": "fwd-proof", "forwarding": order}))

        moved = _component(root, "moved")
        h3, s3 = moved / "history.json", moved / "state.json"
        projector.append_entry(str(h3), str(s3),
                               {"standing": "BUILDME", "note": "born", "ticket": "fwd-proof"})
        mp = berths / "0" / "packets"
        (mp / "orient-20260730T000000-1111.json").write_text(
            json.dumps({"ticket": "fwd-proof", "refs": ["chart", "gone/away.py"]}))
        (mp / "survey-20260730T000001-2222.json").write_text(json.dumps(
            {"ticket": "fwd-proof", "sought": ["the moved thing"],
             "holdings": [{"what": "the thing that moved", "address": "gone/away.py"}],
             "absences": [{"what": "nothing", "measure": "census rows"}]}))

        # (i) NO ORDER: both mouths red. The tolerance is opt-in, never the default.
        names = lambda comp: sorted(x["sieve"] for x in           # noqa: E731
                                    inspect(root=root, component=comp)["findings"])
        assert names("moved") == ["charted_refs_resolve", "survey_holdings_resolve"], \
            "a missing charted address with no forwarding order must still red"

        # (ii) A WHOLE ORDER: both disposed, and nothing else is loosened.
        _order({"gone/away.py": {"to": "chart", "why": "renamed by piece (f)"}})
        assert names("moved") == [], inspect(root=root, component="moved")["findings"]

        # (iii) FORWARDING TO NOTHING: the order reds by its own name AND disposes
        #       nothing — the missing-ref findings stand. Two loud records, never one
        #       silent pass; a successor the world does not hold is the same hollow
        #       claim as the ref it was offered to dispose, one indirection later.
        _order({"gone/away.py": {"to": "also/gone.py", "why": "renamed by piece (f)"}})
        assert names("moved") == ["charted_refs_resolve", "forwarding_order_resolves",
                                  "survey_holdings_resolve"], names("moved")

        # (iv) FORWARDING A LIVE ADDRESS: reds. A forwarding order is for what MOVED;
        #      re-aiming a resolving address would let a chart's claim be pointed at a
        #      different thing while the original sits there untouched.
        _order({"chart": {"to": "base", "why": "not a move at all"}})
        assert "forwarding_order_resolves" in names("moved"), names("moved")
        assert "still resolves" in [x["finding"] for x in
                                    inspect(root=root, component="moved")["findings"]
                                    if x["sieve"] == "forwarding_order_resolves"][0]

        # (v) THE WHY IS FORCED STRUCTURALLY (CP3), and so is the shape.
        for broken in ({"gone/away.py": {"to": "chart"}},
                       {"gone/away.py": {"why": "no successor named"}},
                       {"gone/away.py": "chart"},
                       {"gone/away.py": {"to": "chart", "why": "   "}}):
            _order(broken)
            assert "forwarding_order_resolves" in names("moved"), (broken, names("moved"))
            assert "charted_refs_resolve" in names("moved"), \
                ("a broken order must grant no tolerance at all", broken)
        tfile.write_text(json.dumps({"id": "fwd-proof", "forwarding": ["not", "a", "map"]}))
        assert "forwarding_order_resolves" in names("moved"), names("moved")
        tfile.write_text("{not json")
        assert "forwarding_order_resolves" in names("moved"), \
            "an unreadable record of truth is a named finding, never a silent skip"

        # (vi) THE BERTH DOOR DOES NOT INHERIT THE TOLERANCE. judge_survey is the
        #      door's mouth too, and at berth time every holding resolves by
        #      definition — a successor is meaningless there, and teaching the pure
        #      judge about one would let a packet be berthed naming an address that
        #      was already gone. Asserted against a WHOLE order, the case where the
        #      promotion side is quiet: only the promotion side may dispose.
        _order({"gone/away.py": {"to": "chart", "why": "renamed by piece (f)"}})
        assert names("moved") == [], "the promotion side disposes a whole order"
        berthed = json.loads((mp / "survey-20260730T000001-2222.json").read_text())
        assert [x["judge"] for x in judge_survey(berthed)] == ["survey_holdings_resolve"], \
            "the berth door must still refuse a holding the world does not hold"

        # (vii) A TICKET THAT MOVES NOTHING is the normal case and says nothing.
        tfile.write_text(json.dumps({"id": "fwd-proof"}))
        assert names("moved") == ["charted_refs_resolve", "survey_holdings_resolve"]
        (mp / "orient-20260730T000000-1111.json").unlink()
        (mp / "survey-20260730T000001-2222.json").unlink()
        tfile.unlink()
        _insp._TICKETS_ROOT = saved_troot

        # 27 — THE ENTRY GATE (buildme-rides-the-chart, 2026-07-29): green iff a
        #      READABLE VALIDATE berth claims the ticket; red is ONE finding carrying
        #      ticket + searched root + the /chart disposition, complete first pass.
        #      Crossing-jurisdiction, deliberately NOT in SIEVES — a promotion sweep
        #      would retro-red every pre-chain component (the tooth-1 failure).
        from cairn.machines.build_inspector.inspector import SIEVES as _SIEVES
        from cairn.machines.build_inspector.inspector import buildme_rides_the_chart
        eroot = tmp / "entry-berths"
        ep = eroot / "0" / "packets"
        ep.mkdir(parents=True)
        ef = buildme_rides_the_chart("lonely", berths_root=eroot)
        assert [x["sieve"] for x in ef] == ["buildme_rides_the_chart"], ef
        assert ef[0]["evidence"]["ticket"] == "lonely" and \
            ef[0]["evidence"]["searched"] == str(eroot) and \
            "/chart" in ef[0]["why_it_matters"], ef[0]
        # a claim on ANOTHER ticket, an unreadable berth, a non-validate stage: still red
        (ep / "validate-20260729T000000-aaaa.json").write_text(
            json.dumps({"ticket": "someone-else"}))
        (ep / "validate-20260729T000001-bbbb.json").write_text("{not json")
        (ep / "hypothesize-20260729T000002-cccc.json").write_text(
            json.dumps({"ticket": "lonely"}))
        assert buildme_rides_the_chart("lonely", berths_root=eroot), \
            "only a READABLE VALIDATE berth claiming the ticket is a charted course"
        # the real claim lands: green, empty findings
        (ep / "validate-20260729T000003-dddd.json").write_text(
            json.dumps({"ticket": "lonely"}))
        assert buildme_rides_the_chart("lonely", berths_root=eroot) == []
        # a nonexistent root reds, never crashes; and the check stays OUT of SIEVES
        assert buildme_rides_the_chart("lonely", berths_root=eroot / "nope")
        assert "buildme_rides_the_chart" not in _SIEVES, \
            "crossing-jurisdiction: the promotion sweep must not run the entry check"

        # 28 — THE EXIT GATE (proved-answers-the-chart, 2026-07-29): the loop's
        #      other hand. UNCLAIMED is GREEN (the inversion of tooth 27: entry
        #      demands a chart exists, exit only judges the chart that claims);
        #      claimed-and-unanswered is red naming each unanswered item; only a
        #      complete, passing verdict artifact answering the CLAIMING berth
        #      greens. Same crossing-jurisdiction, same NOT-in-SIEVES reason.
        from cairn.machines.build_inspector.inspector import proved_answers_the_chart
        xroot = tmp / "exit-berths"
        xp = xroot / "0" / "packets"
        xp.mkdir(parents=True)
        # unclaimed ticket: green, even on an empty (or nonexistent) root
        assert proved_answers_the_chart("sworn", berths_root=xroot) == []
        assert proved_answers_the_chart("sworn", berths_root=xroot / "nope") == []
        # the claiming chain: hypothesize berth <- validate berth claiming 'sworn'
        hyp = xp / "hypothesize-20260729T000000-aaaa.json"
        hyp.write_text(json.dumps({"hypotheses": [
            {"piece": "p1", "expect": "e1", "falsifier": "f", "instrument": "i"}]}))
        val = xp / "validate-20260729T000001-bbbb.json"
        val.write_text(json.dumps({"ticket": "sworn", "hypothesize_ref": str(hyp),
                                   "criteria": [{"claim": "c1", "instrument": "cmd",
                                                 "covers": ["p1"]}]}))
        # claimed, no verdict artifact: ONE red naming the missing answer + disposition
        xf = proved_answers_the_chart("sworn", berths_root=xroot)
        assert [x["sieve"] for x in xf] == ["proved_answers_the_chart"], xf
        assert "no verdict artifact" in xf[0]["finding"] and \
            str(val) in xf[0]["evidence"]["claiming"] and \
            "write_verdict" in xf[0]["why_it_matters"], xf[0]
        # a verdict answering someone ELSE's chart: red, not an answer here
        stray = xp / "verdict-20260729T000002-cccc.json"
        stray.write_text(json.dumps(
            {"ticket": "sworn", "validate_ref": str(xp / "elsewhere.json"),
             "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "pass",
                           "evidence": "seen"}],
             "dispositions": [{"piece": "p1", "expect": "e1",
                               "disposition": "confirmed", "by": "obs"}]}))
        xf = proved_answers_the_chart("sworn", berths_root=xroot)
        assert xf and "does not claim this ticket" in xf[0]["finding"], xf
        # narration (empty evidence) is malformed, loudly — done may not live there
        stray.unlink()
        bad = xp / "verdict-20260729T000003-dddd.json"
        bad.write_text(json.dumps(
            {"ticket": "sworn", "validate_ref": str(val),
             "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "pass",
                           "evidence": ""}],
             "dispositions": []}))
        xf = proved_answers_the_chart("sworn", berths_root=xroot)
        assert xf and "malformed" in xf[0]["finding"] and \
            "narration" in xf[0]["finding"], xf
        # answered-and-FAILED + undispositioned: one complete finding EACH, first pass
        bad.unlink()
        half = xp / "verdict-20260729T000004-eeee.json"
        half.write_text(json.dumps(
            {"ticket": "sworn", "validate_ref": str(val),
             "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "fail",
                           "evidence": "it broke"}],
             "dispositions": []}))
        xf = proved_answers_the_chart("sworn", berths_root=xroot)
        assert len(xf) == 2, xf
        assert "FAILED" in xf[0]["finding"] and "kick-back" in xf[0]["finding"], xf[0]
        assert "undispositioned" in xf[1]["finding"] and "p1" in xf[1]["finding"], xf[1]
        # the complete answer stands: LATEST artifact wins, green, empty findings
        (xp / "verdict-20260729T000005-ffff.json").write_text(json.dumps(
            {"ticket": "sworn", "validate_ref": str(val),
             "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "pass",
                           "evidence": "seen: exit 0 twice"}],
             "dispositions": [{"piece": "p1", "expect": "e1",
                               "disposition": "killed", "by": "the second run"}]}))
        assert proved_answers_the_chart("sworn", berths_root=xroot) == []
        # and the check stays OUT of SIEVES (crossing-jurisdiction, tooth-1 reason)
        assert "proved_answers_the_chart" not in _SIEVES, \
            "crossing-jurisdiction: the promotion sweep must not run the exit check"
    finally:
        _insp._CHART_BERTHS = saved_berths

    # ── the sole path (2026-08-08, ruling the-inference-proxy-is-a-rules-stack,
    #    item 1: "THAT NEEDS TO BE IN THE BUILD INSPECTION") ─────────────────
    #
    # DEFECT-FIRST: a component that grows a second door to the inference host. The
    # healthy tree above already proved the sieve stays quiet (section 1 ran with it
    # in the roster); without THIS tooth, that quiet is indistinguishable from a
    # sieve made of solid sheet metal — the leak-scan-coin-toss-red lesson.
    rogue = _component(root, "rogue")
    (rogue / "dialer.py").write_text("import urllib.request\n")
    f = inspect(root=root, component="rogue")["findings"]
    assert [x["sieve"] for x in f] == ["sole_path_holds"], \
        f"the planted dialer must red exactly sole_path_holds: {f}"
    assert "dialer.py" in f[0]["finding"] and "SECOND door" in f[0]["finding"], f[0]
    # the rogue's door reds the ROGUE's row alone — healthy keeps its clean.
    assert inspect(root=root, component="healthy")["clean"], \
        "another component's door must never red a clean component's row"
    # and the mesh's own exemption: the same import INSIDE inference_domain is the
    # sole path itself, not a second door.
    dom = _component(root, "inference_domain")
    (dom / "host.py").write_text("import urllib.request\n")
    assert inspect(root=root, component="inference_domain")["clean"], \
        "inference_domain IS the door — the mesh's 'only' must spare it"

    # ── the nest (2026-08-06, ticket the-questions-are-the-sieve) ────────────
    #
    # DEFECT-FIRST, and the defect is the one the derivation exists to prevent: a band
    # that was authored would sit still while the sieve it labels started reaching
    # further. So the tooth EDITS a sieve's body and demands the band MOVE, with no
    # other change and nothing hand-set anywhere.
    nest = _insp.the_nest()
    banded = {name: b for b, names in nest for name in names}
    assert banded["charter_on_disk"] == 0, banded          # answer is in the census row
    assert banded["state_is_projection"] >= 1, banded      # has to open history.json
    assert [b for b, _ in nest] == sorted(b for b, _ in nest), \
        "the nest is shaken coarse band first — that ordering IS the nest"

    src = pathlib.Path(_insp.__file__).read_text()
    reaches = _insp.import_sieve.reach_of(src)
    assert reaches["charter_on_disk"] == 0, reaches["charter_on_disk"]
    # now make that same sieve reach off-box, changing NOTHING else
    mutant = src.replace(
        "def charter_on_disk(row: dict, comp_dir: Path) -> list[dict]:",
        "def charter_on_disk(row: dict, comp_dir: Path) -> list[dict]:\n"
        "    import cairn.devices.db_domain as _d; _d.connect()", 1)
    assert mutant != src, "the mutation did not apply — the tooth would be vacuous"
    moved = _insp.import_sieve.reach_of(mutant)
    assert moved["charter_on_disk"] == 3, (
        "a sieve that started reaching off the box kept its band — the band is being "
        "authored somewhere instead of derived, which is this ticket's first falsifier: "
        f"{moved['charter_on_disk']}")

    # ...and no band is written down. A literal band beside a sieve is the hand-set
    # constant this derivation replaced; if one appears, the derivation is decoration.
    assert '"band"' not in src.split("def the_nest")[0], \
        "a band literal appears in sieve code — bands are derived, never authored"

    # THE GRADATION: a score per sieve that RAN, and the vector Akien drew.
    rep = _insp.inspect()
    for comp, scores in rep["gradation"].items():
        assert set(scores) == set(_SIEVES), \
            f"{comp}: the gradation must score every sieve the nest shook, not a subset"
        assert set(scores.values()) <= {0.0, 1.0}, \
            f"{comp}: sieves are binary today, as floats — a third value is not the design"
        assert rep["component_scores"][comp] == min(scores.values()), (
            "the roll-up is min() — one zero sinks the component, and a pile of passes "
            "may not buy past a real catch")
    caught = {f["sieve"] for f in rep["findings"]}
    for f in rep["findings"]:
        assert f["score"] == 0.0, f
        assert rep["gradation"][f["component"]][f["sieve"]] == 0.0, f
    for comp, scores in rep["gradation"].items():
        for name, s in scores.items():
            if s == 1.0:
                assert not any(f["sieve"] == name and f["component"] == comp
                               for f in rep["findings"]), \
                    ("a sieve scored 1.0 while emitting a finding — the score and "
                     "the finding are two faces of one judgement and cannot disagree")
    assert caught <= set(_SIEVES)

    # ABSENCE, NOT A THIRD VALUE: a sieve the nest did not shake is missing from the
    # gradation rather than scored zero. Akien refused a tri-value, so this is the only
    # place 'not applicable' can live, and it must be structurally reachable.
    partial = dict(list(_SIEVES.items())[:2])
    saved_sieves = _insp.SIEVES
    saved_cache = _insp._NEST_CACHE
    try:
        _insp.SIEVES, _insp._NEST_CACHE = partial, None
        thin = _insp.inspect()
        for comp, scores in thin["gradation"].items():
            assert set(scores) == set(partial), scores
            missing = set(saved_sieves) - set(partial)
            assert not (missing & set(scores)), (
                "a sieve that never ran appeared in the gradation — absent is how "
                "not-applicable is carried, and a 0.0 there would be a false catch")
    finally:
        _insp.SIEVES, _insp._NEST_CACHE = saved_sieves, saved_cache

    print("build_inspector proofs: all teeth green")


if __name__ == "__main__":
    main()
