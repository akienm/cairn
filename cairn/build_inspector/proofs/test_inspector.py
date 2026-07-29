"""Proofs for build_inspector — filters judge measurements, findings are complete,
and the gate cannot silently inspect nothing.

Hermetic: a synthetic tree pins each filter's fire-and-stay-quiet behavior; the real
tree is asserted by invariant only (shape and floors, never a snapshot of findings —
the sweep's real findings are work items, not constants; memory:
proof-over-live-data-assert-invariants).
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from cairn.build_inspector.inspector import FILTERS, inspect  # noqa: E402
from cairn.charter import projector  # noqa: E402
from cairn.orient.orient import ScanRefused  # noqa: E402

_FINDING_SHAPE = {"filter", "component", "finding", "evidence", "why_it_matters"}


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
    tmp = Path(tempfile.mkdtemp(prefix="inspector-proof-"))
    root = tmp / "cairn"

    # A healthy component and one broken per filter.
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

    # 2 — each seeded failure fires exactly its filter, nothing else.
    for comp, expected in [("no_charter", "charter_on_disk"),
                           ("no_proofs", "proofs_exist"),
                           ("silent", "silent_device")]:
        f = inspect(root=root, component=comp)["findings"]
        assert [x["filter"] for x in f] == [expected], (comp, f)

    # 3 — state_is_projection: a voyage written THROUGH THE DOOR is clean...
    h, s = root / "healthy" / "history.json", root / "healthy" / "state.json"
    projector.append_entry(str(h), str(s), {"standing": "BUILDME", "note": "born"})
    assert inspect(root=root, component="healthy")["clean"]

    # 4 — ...and a HAND-EDIT to state.json is caught as drift, with the diverging keys.
    edited = json.loads(s.read_text())
    edited["cursor"] = {"gate": "PROVED"}  # the lie: promotion without a crossing
    s.write_text(json.dumps(edited))
    f = inspect(root=root, component="healthy")["findings"]
    assert [x["filter"] for x in f] == ["state_is_projection"], f
    assert "cursor" in f[0]["evidence"]["diverging_keys"], f[0]

    # 5 — repair goes through the door (append), never an edit — and the gate agrees.
    projector.append_entry(str(h), str(s), {"standing": "BUILDME", "note": "re-projected"})
    assert inspect(root=root, component="healthy")["clean"]

    # 6 — an orphan half of the pair is a finding (state without history).
    orphan = _component(root, "orphan")
    (orphan / "state.json").write_text("{}")
    f = inspect(root=root, component="orphan")["findings"]
    assert [x["filter"] for x in f] == ["state_is_projection"] and "without" in f[0]["finding"]

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

    # 10 — THE LEARNING-DEVICE SHAPE: every filter's docstring carries a provenance
    #      naming its seeding failure (dated or IOU-named) — a filter nobody was
    #      taught by is refused here, same tooth as orient's scans.
    for name, judge in FILTERS.items():
        doc = judge.__doc__ or ""
        assert "Provenance:" in doc, f"{name}: no provenance — a check nobody was taught by"

    # 11 — REAL TREE, invariants only: the sweep runs, sees the tree, exits gate-ably.
    real = inspect()
    assert real["components_inspected"] >= 10, "the sweep barely saw the tree"
    assert real["filters_run"] == sorted(FILTERS)
    for x in real["findings"]:
        assert set(x) == _FINDING_SHAPE, x
    assert real["clean"] == (not real["findings"])

    # 12 — the inspector is inference-free BY IMPORT: no deepen, no inference_domain,
    #      no outbound-capable module in inspector.py.
    import ast as _ast
    src = (_REPO_ROOT / "cairn" / "build_inspector" / "inspector.py").read_text()
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
    import cairn.build_inspector.inspector as _insp
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
        assert [x["filter"] for x in f] == ["charted_refs_resolve"], f
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
        assert [x["filter"] for x in f] == ["charted_refs_resolve"], f
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
        assert [x["filter"] for x in f] == ["constraint_traces"], f
        assert f[0]["evidence"]["source"] == "no/such/charter.json", f[0]
        unbounded = dict(whole, bounds={"in": ["the gate only"], "out": []})
        cpath.write_text(json.dumps(unbounded))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["filter"] for x in f] == ["constraint_bounds_complete"], f
        assert f[0]["evidence"]["side"] == "out", f[0]

        # 16 — ONE IMPLEMENTATION, TWO MOUTHS: the registry filters report exactly
        #      what the pure judge reports — no drift between door and gate is
        #      possible because there is nothing to drift between.
        from cairn.build_inspector.inspector import judge_constrain
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
        assert [x["filter"] for x in f] == ["survey_holdings_resolve"], f
        assert f[0]["evidence"]["address"] == "no/such/thing.py", f[0]
        unswept = dict(held, sought=[])
        spath.write_text(json.dumps(unswept))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["filter"] for x in f] == ["survey_coverage_complete"], f
        unmeasured = dict(held, absences=[{"what": "a survey module"}])
        spath.write_text(json.dumps(unmeasured))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["filter"] for x in f] == ["survey_coverage_complete"], f
        assert "measure" in f[0]["finding"], f[0]

        # 18 — one implementation, two mouths, for the survey judge too.
        from cairn.build_inspector.inspector import judge_survey
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
        assert [x["filter"] for x in f] == ["decompose_composes_holdings"], f
        assert f[0]["evidence"]["uses"] == "no/such/thing.py", f[0]
        invented = dict(derived, sub_problems=[
            {"what": "build a whim", "why": "nobody measured it",
             "kind": "build", "fills": "a thing never sought"}])
        dpath.write_text(json.dumps(invented))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["filter"] for x in f] == ["decompose_builds_absences"], f
        assert f[0]["evidence"]["fills"] == "a thing never sought", f[0]
        broken = dict(derived, survey_ref=str(tmp / "gone.json"))
        dpath.write_text(json.dumps(broken))
        f = inspect(root=root, component="charted")["findings"]
        assert "decompose_composes_holdings" in [x["filter"] for x in f], f
        assert any("survey berth" in x["finding"] for x in f), f
        dpath.unlink()

        # 20 — one implementation, two mouths, for the decompose judge too.
        from cairn.build_inspector.inspector import judge_decompose
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
        assert [x["filter"] for x in f] == ["triage_covers_the_split"], f
        assert f[0]["evidence"]["dropped"] == ["compose the chart door"], f[0]
        invented_rank = dict(ranked, order=ranked["order"] + [
            {"what": "polish a whim", "why_now": "it would be nice"}])
        tpath.write_text(json.dumps(invented_rank))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["filter"] for x in f] == ["triage_covers_the_split"], f
        assert f[0]["evidence"]["what"] == "polish a whim", f[0]
        unreasoned = dict(ranked, order=[
            dict(ranked["order"][0], why_now=""), ranked["order"][1]])
        tpath.write_text(json.dumps(unreasoned))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["filter"] for x in f] == ["triage_reasons_the_order"], f
        assert f[0]["evidence"]["what"] == "build the module", f[0]
        chainless = dict(ranked, decompose_ref=str(tmp / "gone.json"))
        tpath.write_text(json.dumps(chainless))
        f = inspect(root=root, component="charted")["findings"]
        assert "triage_covers_the_split" in [x["filter"] for x in f], f
        assert any("decompose berth" in x["finding"] for x in f), f
        tpath.unlink()

        # 22 — one implementation, two mouths, for the triage judge too; and the
        #      double-order fires with its counts in evidence.
        from cairn.build_inspector.inspector import judge_triage
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
        assert [x["filter"] for x in f] == ["hypothesize_covers_the_ranked"], f
        assert f[0]["evidence"]["uncovered"] == ["compose the chart door"], f[0]
        invented_h = dict(expected, hypotheses=expected["hypotheses"] + [
            {"piece": "polish a whim", "expect": "it gleams",
             "falsifier": "it does not", "instrument": "a glance"}])
        hpath.write_text(json.dumps(invented_h))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["filter"] for x in f] == ["hypothesize_covers_the_ranked"], f
        assert f[0]["evidence"]["piece"] == "polish a whim", f[0]
        unmeasured_h = dict(expected, hypotheses=[
            dict(expected["hypotheses"][0], falsifier="", instrument="  "),
            expected["hypotheses"][1]])
        hpath.write_text(json.dumps(unmeasured_h))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["filter"] for x in f] == ["hypothesize_falsifiable_measured"], f
        assert f[0]["evidence"]["lacking"] == ["falsifier", "instrument"], f[0]
        chainless_h = dict(expected, triage_ref=str(tmp / "gone.json"))
        hpath.write_text(json.dumps(chainless_h))
        f = inspect(root=root, component="charted")["findings"]
        assert "hypothesize_covers_the_ranked" in [x["filter"] for x in f], f
        assert any("triage berth" in x["finding"] for x in f), f
        hpath.unlink()

        # 24 — one implementation, two mouths, for the hypothesize judge too.
        from cairn.build_inspector.inspector import judge_hypothesize
        assert judge_hypothesize(expected) == []
        assert [x["judge"] for x in judge_hypothesize(uncovered)] == \
            ["hypothesize_covers_the_ranked"]
        assert [x["judge"] for x in judge_hypothesize(unmeasured_h)] == \
            ["hypothesize_falsifiable_measured"]
        assert judge_hypothesize(chainless_h) and \
            judge_hypothesize(chainless_h)[0]["judge"] == "hypothesize_covers_the_ranked"
    finally:
        _insp._CHART_BERTHS = saved_berths

    print("build_inspector proofs: all teeth green")


if __name__ == "__main__":
    main()
