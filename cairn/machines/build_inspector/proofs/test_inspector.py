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

from cairn.machines.build_inspector.inspector import SIEVES, inspect, working_tree_clean  # noqa: E402
from cairn.tools.charter import projector  # noqa: E402
from cairn.tools.orient.orient import ScanRefused  # noqa: E402
from cairn.devices.tester.scratch import scratch_dir  # noqa: E402


def _jfindings(attendance):
    """Extract flat findings from attendance records."""
    return [f for rec in attendance for f in rec["findings"]]

# "score" joined 2026-08-06 (the-questions-are-the-sieve): a finding carries the DATUM
# (evidence, under the name it has always had) AND the score — the datum read against
# the requirement, which the datum alone cannot say. Pinned here so a sieve cannot emit
# a bare judgement again.
#
# "at" joined 2026-08-13 (the builder move): the finding's ADDRESS, alongside its name.
# Two components are called "orient" — the tool and the machine the builder holds — so
# "component" stopped being enough to say which one was caught, and the gradation is now
# keyed by address. "at" is what correlates a finding back to its own row; without it a
# reader (and the tooth below at the gradation) can only guess between two subjects.
_FINDING_SHAPE = {"method", "component", "about", "expected", "actual", "compare", "at"}


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


def _reseal(comp_dir: Path):
    from cairn.machines.build_inspector.inspector import _source_fingerprint
    fp = _source_fingerprint(comp_dir)
    vals = comp_dir / "validations"
    for vf in vals.glob("*.json"):
        records = json.loads(vf.read_text())
        if isinstance(records, list) and records:
            records[-1].setdefault("evidence", {})["source_fingerprint"] = fp
        vf.write_text(json.dumps(records))


def _component(root: Path, name: str, *, charter=True, proof=True, device=True, emits=True):
    d = root / name
    (d / "proofs").mkdir(parents=True)
    if charter:
        (d / "intention+why.json").write_text(json.dumps(
            {"component": name, "runtime_role": "tool",
             "learns": "fixture component — does not learn",
             "claim_provenance": {"role": "cc-read", "what": "cc-read", "why": "cc-read"}}))
    if proof:
        (d / "proofs" / "test_x.py").write_text("assert True\n")
    body = "from base import BaseDevice\n\n\nclass D(BaseDevice):\n    def work(self):\n"
    body += "        self.emit('gate')\n" if emits else "        return 1\n"
    (d / "dev.py").write_text(body if device else "def helper():\n    return 1\n")
    if proof:
        from cairn.machines.build_inspector.inspector import _source_fingerprint
        fp = _source_fingerprint(d)
        (d / "validations").mkdir(exist_ok=True)
        (d / "validations" / "test_x.json").write_text(json.dumps([{
            "claim": "fixture", "caller": "test", "date": "2026-01-01T00:00:00",
            "method": "fixture", "verdict": "green",
            "evidence": {"source_fingerprint": fp},
            "falsifier": "test", "horizon": "test",
        }]))
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
        assert [x["method"] for x in f] == [expected], (comp, f)

    # 3 — state_is_projection: a voyage written THROUGH THE DOOR is clean...
    h, s = root / "healthy" / "history.json", root / "healthy" / "state.json"
    projector.append_entry(str(h), str(s), {"standing": "BUILDME", "note": "born"})
    assert inspect(root=root, component="healthy")["clean"]

    # 4 — ...and a HAND-EDIT to state.json is caught as drift, with the diverging keys.
    edited = json.loads(s.read_text())
    edited["cursor"] = {"gate": "PROVED"}  # the lie: promotion without a crossing
    s.write_text(json.dumps(edited))
    f = inspect(root=root, component="healthy")["findings"]
    assert [x["method"] for x in f] == ["state_is_projection"], f
    assert "cursor" in f[0]["about"], f[0]

    # 5 — repair goes through the door (append), never an edit — and the gate agrees.
    projector.append_entry(str(h), str(s), {"standing": "BUILDME", "note": "re-projected"})
    assert inspect(root=root, component="healthy")["clean"]

    # 6 — an orphan half of the pair is a finding (state without history).
    orphan = _component(root, "orphan")
    (orphan / "state.json").write_text("{}")
    f = inspect(root=root, component="orphan")["findings"]
    assert [x["method"] for x in f] == ["state_is_projection"] and "missing" in f[0]["about"]

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
        assert set(x) - {"values"} == _FINDING_SHAPE and x["about"], x

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
        assert set(x) - {"values"} == _FINDING_SHAPE, x
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
            json.dumps({"ticket": "wire-proof", "refs": ["base", "no/such/ref.py"]}))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["charted_refs_resolve"], f
        assert "no/such/ref.py" in f[0]["about"], f[0]
        # The world matching the chart again: quiet again.
        (p / "orient-20260728T000001-bbbb.json").write_text(
            json.dumps({"ticket": "wire-proof", "refs": ["base"]}))
        assert inspect(root=root, component="charted")["clean"]

        # 14 — an UNREADABLE berth is a named finding on the berth owner (chart)
        #      exactly once — never on every component's crossing, never skipped.
        _component(root, "chart")
        (p / "orient-20260728T000002-cccc.json").write_text("{not json")
        assert inspect(root=root, component="charted")["clean"], \
            "an unreadable berth must not fire on other components' crossings"
        f = inspect(root=root, component="chart")["findings"]
        assert [x["method"] for x in f] == ["charted_refs_resolve"], f
        assert "readable" in f[0]["about"], f[0]
        # 15 — THE JUDGES BEFORE THE JUDGED (constrain-filters): a charted constrain
        #      packet with an unresolvable source fires constraint_traces; an empty
        #      bounds.out fires constraint_bounds_complete; a whole packet is quiet.
        #      (Installed before the constrain module exists — the fixtures here ARE
        #      the module's acceptance contract.)
        whole = {"ticket": "wire-proof",
                 "constraints": [{"text": "stay off the network", "source": "base",
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
        assert [x["method"] for x in f] == ["constraint_traces"], f
        assert f[0]["values"]["source"] == "no/such/charter.json", f[0]
        unbounded = dict(whole, bounds={"in": ["the gate only"], "out": []})
        cpath.write_text(json.dumps(unbounded))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["constraint_bounds_complete"], f
        assert f[0]["values"]["side"] == "out", f[0]

        # 16 — ONE IMPLEMENTATION, TWO MOUTHS: the registry sieves report exactly
        #      what the pure judge reports — no drift between door and gate is
        #      possible because there is nothing to drift between.
        from cairn.machines.build_inspector.inspector import judge_constrain
        assert not _jfindings(judge_constrain(whole))
        assert [x["judge"] for x in _jfindings(judge_constrain(minted))] == ["constraint_traces"]
        assert [x["judge"] for x in _jfindings(judge_constrain(unbounded))] == ["constraint_bounds_complete"]
        cpath.unlink()

        # 17 — THE JUDGES BEFORE THE JUDGED, SECOND INSTANCE (survey-filters): a
        #      charted survey packet with an unresolvable holding fires
        #      survey_holdings_resolve; an empty sought or a measureless absence
        #      fires survey_coverage_complete; a whole packet is quiet. (Installed
        #      before the survey module exists — these fixtures ARE its acceptance
        #      contract, the pattern constrain-filters filed at edge (b).)
        held = {"ticket": "wire-proof",
                "sought": ["a settled measurer of the territory"],
                "holdings": [{"what": "the base tool", "address": "base"}],
                "absences": [{"what": "a survey module",
                              "measure": "device_census rows, no such component"}]}
        spath = p / "survey-20260728T000004-eeee.json"
        spath.write_text(json.dumps(held))
        assert inspect(root=root, component="charted")["clean"]
        phantom = dict(held, holdings=[{"what": "a phantom holding",
                                        "address": "no/such/thing.py"}])
        spath.write_text(json.dumps(phantom))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["survey_holdings_resolve"], f
        assert f[0]["values"]["address"] == "no/such/thing.py", f[0]
        unswept = dict(held, sought=[])
        spath.write_text(json.dumps(unswept))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["survey_coverage_complete"], f
        unmeasured = dict(held, absences=[{"what": "a survey module"}])
        spath.write_text(json.dumps(unmeasured))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["survey_coverage_complete"], f
        assert "measure" in f[0]["about"], f[0]

        # 18 — one implementation, two mouths, for the survey judge too.
        from cairn.machines.build_inspector.inspector import judge_survey
        assert not _jfindings(judge_survey(held))
        assert [x["judge"] for x in _jfindings(judge_survey(phantom))] == ["survey_holdings_resolve"]
        assert [x["judge"] for x in _jfindings(judge_survey(unswept))] == ["survey_coverage_complete"]
        assert [x["judge"] for x in _jfindings(judge_survey(unmeasured))] == ["survey_coverage_complete"]
        spath.unlink()

        # 19 — THE JUDGES BEFORE THE JUDGED, THIRD APPLICATION (decompose-filters):
        #      a compose piece using an address the survey berth does not hold fires
        #      decompose_composes_holdings; a build piece filling an unmeasured
        #      absence fires decompose_builds_absences; a broken survey_ref is a
        #      loud finding; a derived split is quiet. (Installed before the
        #      decompose module exists — these fixtures ARE its acceptance contract.)
        sb = tmp / "survey_berth_fixture.json"
        sb.write_text(json.dumps({
            "holdings": [{"what": "the base tool", "address": "base"}],
            "absences": [{"what": "a decompose module",
                          "measure": "path check, absent"}]}))
        derived = {"ticket": "wire-proof", "survey_ref": str(sb),
                   "sub_problems": [
                       {"what": "compose the base door", "why": "it is held",
                        "kind": "compose", "uses": ["base"]},
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
        assert [x["method"] for x in f] == ["decompose_composes_holdings"], f
        assert f[0]["values"]["uses"] == "no/such/thing.py", f[0]
        invented = dict(derived, sub_problems=[
            {"what": "build a whim", "why": "nobody measured it",
             "kind": "build", "fills": "a thing never sought"}])
        dpath.write_text(json.dumps(invented))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["decompose_builds_absences"], f
        assert f[0]["values"]["fills"] == "a thing never sought", f[0]
        broken = dict(derived, survey_ref=str(tmp / "gone.json"))
        dpath.write_text(json.dumps(broken))
        f = inspect(root=root, component="charted")["findings"]
        assert "decompose_composes_holdings" in [x["method"] for x in f], f
        assert any("survey berth" in x["about"] for x in f), f
        dpath.unlink()

        # 20 — one implementation, two mouths, for the decompose judge too.
        from cairn.machines.build_inspector.inspector import judge_decompose
        assert not _jfindings(judge_decompose(derived))
        assert [x["judge"] for x in _jfindings(judge_decompose(rebuilt))] == ["decompose_composes_holdings"]
        assert [x["judge"] for x in _jfindings(judge_decompose(invented))] == ["decompose_builds_absences"]
        assert _jfindings(judge_decompose(broken)) and \
            _jfindings(judge_decompose(broken))[0]["judge"] == "decompose_composes_holdings"

        # 20b — THE OUTPUT ADDRESS, AND THE SILENCE THAT IS THE POINT (ticket
        #       a-piece-names-where-its-output-lands). This judge is the PROMOTION
        #       mouth: it sweeps the standing corpus, so it judges a `writes_to`
        #       that is PRESENT and says nothing at all about one that is absent.
        #       Lettered rather than renumbered because the charter's falsifier and
        #       this file cite teeth by number — a number is an address.
        addressed = dict(derived, sub_problems=[
            dict(derived["sub_problems"][0], writes_to=["cairn/tools/base/address.py"]),
            # Does NOT exist, and stays quiet: a build piece names the file it is
            # about to create. A judge demanding existence would red exactly the
            # case the field was added to carry.
            dict(derived["sub_problems"][1], writes_to=["cairn/no/such/module.py"])])
        assert not _jfindings(judge_decompose(addressed)), judge_decompose(addressed)
        outside = dict(derived, sub_problems=[
            dict(derived["sub_problems"][0], writes_to=["/etc/passwd"])])
        assert [x["judge"] for x in _jfindings(judge_decompose(outside))] == \
            ["decompose_composes_holdings"], judge_decompose(outside)
        assert "outside the cairn repo" in _jfindings(judge_decompose(outside))[0]["finding"]
        a_dir = dict(derived, sub_problems=[
            dict(derived["sub_problems"][0], writes_to=["cairn/tools"])])
        assert "an existing directory" in _jfindings(judge_decompose(a_dir))[0]["finding"], \
            judge_decompose(a_dir)
        hollow = dict(derived, sub_problems=[
            dict(derived["sub_problems"][0], writes_to=[])])
        assert "not a non-empty list" in _jfindings(judge_decompose(hollow))[0]["finding"]
        # ...and through the registry sieve, not only the pure judge (two mouths).
        dpath.write_text(json.dumps(outside))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["decompose_composes_holdings"], f
        dpath.write_text(json.dumps(addressed))
        assert inspect(root=root, component="charted")["clean"]
        dpath.unlink()

        # NO RETRO-RED, ASSERTED OVER THE REAL STANDING CORPUS AS AN INVARIANT —
        # never as a snapshot count, because _CHART_BERTHS is a live directory that
        # grows every time anyone charts. The berths charted before this field
        # existed never had it asked of them, and reading their silence as a finding
        # would red 51 healthy components against a spec that did not exist when
        # they were written (tooth 1, and Law 9's bound read the other way). The
        # count it actually saw is asserted non-zero: an invariant over zero berths
        # is a hollow green, and this proof's whole exposure is exactly that.
        corpus, silent = 0, 0
        # The same glob _charted_packets sweeps: <instance>/packets/ under the root.
        for real in sorted(Path(saved_berths).glob("*/packets/decompose-*.json")):
            try:
                pkt = json.loads(real.read_text())
            except (OSError, ValueError):
                continue
            pieces = pkt.get("sub_problems")
            if not isinstance(pieces, list) or not pieces:
                continue
            corpus += 1
            if any(isinstance(sp, dict) and "writes_to" in sp for sp in pieces):
                continue
            silent += 1
            said = [x["finding"] for x in _jfindings(judge_decompose(pkt))
                    if "writes_to" in x["finding"]]
            assert not said, (str(real), said)
        assert corpus > 0, (
            "the no-retro-red arm read ZERO standing decompose berths at %s — an "
            "invariant over an empty corpus is a hollow green, and this assertion "
            "is the thing that says so out loud" % saved_berths)
        assert silent > 0, (
            "every standing berth already carries `writes_to`, so the silence this "
            "tooth pins was never exercised — the claim needs a berth that predates "
            "the field, and there is none left at %s" % saved_berths)

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
                {"what": "compose the base door", "why": "it is held",
                 "kind": "compose", "uses": ["base"]},
                {"what": "build the module", "why": "measured absent",
                 "kind": "build", "fills": "a decompose module"}]}))
        ranked = {"ticket": "wire-proof", "decompose_ref": str(db),
                  "order": [
                      {"what": "build the module",
                       "why_now": "the layer below solidifies first"},
                      {"what": "compose the base door",
                       "why_now": "rides on the module once it stands"}]}
        tpath = p / "triage-20260728T000006-abab.json"
        tpath.write_text(json.dumps(ranked))
        assert inspect(root=root, component="charted")["clean"]
        dropped = dict(ranked, order=ranked["order"][:1])
        tpath.write_text(json.dumps(dropped))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["triage_covers_the_split"], f
        assert f[0]["values"]["dropped"] == ["compose the base door"], f[0]
        invented_rank = dict(ranked, order=ranked["order"] + [
            {"what": "polish a whim", "why_now": "it would be nice"}])
        tpath.write_text(json.dumps(invented_rank))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["triage_covers_the_split"], f
        assert f[0]["values"]["what"] == "polish a whim", f[0]
        unreasoned = dict(ranked, order=[
            dict(ranked["order"][0], why_now=""), ranked["order"][1]])
        tpath.write_text(json.dumps(unreasoned))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["triage_reasons_the_order"], f
        assert f[0]["values"]["what"] == "build the module", f[0]
        chainless = dict(ranked, decompose_ref=str(tmp / "gone.json"))
        tpath.write_text(json.dumps(chainless))
        f = inspect(root=root, component="charted")["findings"]
        assert "triage_covers_the_split" in [x["method"] for x in f], f
        assert any("decompose berth" in x["about"] for x in f), f
        tpath.unlink()

        # 22 — one implementation, two mouths, for the triage judge too; and the
        #      double-order fires with its counts in evidence.
        from cairn.machines.build_inspector.inspector import judge_triage
        assert not _jfindings(judge_triage(ranked))
        assert [x["judge"] for x in _jfindings(judge_triage(dropped))] == ["triage_covers_the_split"]
        assert [x["judge"] for x in _jfindings(judge_triage(unreasoned))] == ["triage_reasons_the_order"]
        doubled = dict(ranked, order=ranked["order"] + [ranked["order"][0]])
        frs = _jfindings(judge_triage(doubled))
        assert [x["judge"] for x in frs] == ["triage_covers_the_split"] and \
            frs[0]["evidence"] == {"what": "build the module", "ordered": 2, "split": 1}, frs
        assert _jfindings(judge_triage(chainless)) and \
            _jfindings(judge_triage(chainless))[0]["judge"] == "triage_covers_the_split"

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
                {"what": "compose the base door",
                 "why_now": "rides on the module once it stands"}]}))
        expected = {"ticket": "wire-proof", "triage_ref": str(tb),
                    "hypotheses": [
                        {"piece": "build the module",
                         "expect": "the module's teeth pass twice",
                         "falsifier": "any tooth red on either run",
                         "instrument": "python3 proofs/test_module.py, twice"},
                        {"piece": "compose the base door",
                         "expect": "the door refuses a phantom ref",
                         "falsifier": "a phantom ref berths",
                         "instrument": "the door's own gate, fixture ref"}]}
        hpath = p / "hypothesize-20260728T000007-cdcd.json"
        hpath.write_text(json.dumps(expected))
        assert inspect(root=root, component="charted")["clean"]
        uncovered = dict(expected, hypotheses=expected["hypotheses"][:1])
        hpath.write_text(json.dumps(uncovered))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["hypothesize_covers_the_ranked"], f
        assert f[0]["values"]["uncovered"] == ["compose the base door"], f[0]
        invented_h = dict(expected, hypotheses=expected["hypotheses"] + [
            {"piece": "polish a whim", "expect": "it gleams",
             "falsifier": "it does not", "instrument": "a glance"}])
        hpath.write_text(json.dumps(invented_h))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["hypothesize_covers_the_ranked"], f
        assert f[0]["values"]["piece"] == "polish a whim", f[0]
        unmeasured_h = dict(expected, hypotheses=[
            dict(expected["hypotheses"][0], falsifier="", instrument="  "),
            expected["hypotheses"][1]])
        hpath.write_text(json.dumps(unmeasured_h))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["hypothesize_falsifiable_measured"], f
        assert f[0]["values"]["lacking"] == ["falsifier", "instrument"], f[0]
        chainless_h = dict(expected, triage_ref=str(tmp / "gone.json"))
        hpath.write_text(json.dumps(chainless_h))
        f = inspect(root=root, component="charted")["findings"]
        assert "hypothesize_covers_the_ranked" in [x["method"] for x in f], f
        assert any("triage berth" in x["about"] for x in f), f
        hpath.unlink()

        # 24 — one implementation, two mouths, for the hypothesize judge too.
        from cairn.machines.build_inspector.inspector import judge_hypothesize
        assert not _jfindings(judge_hypothesize(expected))
        assert [x["judge"] for x in _jfindings(judge_hypothesize(uncovered))] == \
            ["hypothesize_covers_the_ranked"]
        assert [x["judge"] for x in _jfindings(judge_hypothesize(unmeasured_h))] == \
            ["hypothesize_falsifiable_measured"]
        assert _jfindings(judge_hypothesize(chainless_h)) and \
            _jfindings(judge_hypothesize(chainless_h))[0]["judge"] == "hypothesize_covers_the_ranked"

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
                {"piece": "compose the base door",
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
                         "covers": ["compose the base door"]}]}
        vpath = p / "validate-20260728T000008-efef.json"
        vpath.write_text(json.dumps(done_set))
        assert inspect(root=root, component="charted")["clean"]
        unmeasured_c = dict(done_set, criteria=[
            dict(done_set["criteria"][0], instrument=" "),
            done_set["criteria"][1]])
        vpath.write_text(json.dumps(unmeasured_c))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["validate_measures_done"], f
        assert f[0]["values"]["lacking"] == ["instrument"], f[0]
        unclaimed = dict(done_set, criteria=done_set["criteria"] + [
            {"claim": "a whim gleams", "instrument": "a glance",
             "covers": ["polish a whim"]}])
        vpath.write_text(json.dumps(unclaimed))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["validate_covers_the_build"], f
        assert f[0]["values"]["covers"] == "polish a whim", f[0]
        partial = dict(done_set, criteria=done_set["criteria"][:1])
        vpath.write_text(json.dumps(partial))
        f = inspect(root=root, component="charted")["findings"]
        assert [x["method"] for x in f] == ["validate_covers_the_build"], f
        assert f[0]["values"]["uncovered"] == ["compose the base door"], f[0]
        chainless_v = dict(done_set, hypothesize_ref=str(tmp / "gone.json"))
        vpath.write_text(json.dumps(chainless_v))
        f = inspect(root=root, component="charted")["findings"]
        assert "validate_covers_the_build" in [x["method"] for x in f], f
        assert any("hypothesize berth" in x["about"] for x in f), f
        vpath.unlink()

        # 26 — one implementation, two mouths, for the validate judge too.
        from cairn.machines.build_inspector.inspector import judge_validate
        assert not _jfindings(judge_validate(done_set))
        assert [x["judge"] for x in _jfindings(judge_validate(unmeasured_c))] == \
            ["validate_measures_done"]
        assert [x["judge"] for x in _jfindings(judge_validate(partial))] == \
            ["validate_covers_the_build"]
        assert _jfindings(judge_validate(chainless_v)) and \
            _jfindings(judge_validate(chainless_v))[0]["judge"] == "validate_covers_the_build"

        # 26a — validate_criterion_is_runnable_before_the_crossing: a criterion
        #       whose instrument reads post-crossing state is refused. Proved by
        #       refiring the two defective criteria from
        #       verdict-20260815T150437-70306f8bfca3's source berth verbatim.
        post_crossing_c = dict(done_set, criteria=[
            {"claim": "the compiler's history carries this ticket's crossings",
             "instrument": "read of the compiler's history.json/state.json "
                           "(three crossings, this ticket, cursor [PROVED])",
             "covers": ["build the module"]},
            {"claim": "cleanup landed after the crossing",
             "instrument": "_cleanup_landed() called live after the PROVED "
                           "crossing",
             "covers": ["compose the base door"]}])
        post_f = _jfindings(judge_validate(post_crossing_c))
        time_f = [f for f in post_f
                  if f["judge"] == "validate_criterion_is_runnable_before_the_crossing"]
        assert len(time_f) == 2, time_f
        assert time_f[0]["evidence"]["index"] == 0
        assert "cursor [PROVED]" in time_f[0]["evidence"]["post_crossing_markers"]
        assert time_f[1]["evidence"]["index"] == 1
        assert "after the crossing" in time_f[1]["evidence"]["post_crossing_markers"]
        pre_crossing_only = dict(done_set, criteria=[
            {"claim": "the module's teeth pass under seal",
             "instrument": "python3 proofs/test_module.py under netns",
             "covers": ["build the module"]},
            {"claim": "the door refuses a phantom ref",
             "instrument": "feed the door a non-existent path, observe refusal",
             "covers": ["compose the base door"]}])
        assert not [f for f in _jfindings(judge_validate(pre_crossing_only))
                    if f["judge"] == "validate_criterion_is_runnable_before_the_crossing"]

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
            json.dumps({"ticket": "fwd-proof", "refs": ["base", "gone/away.py"]}))
        (mp / "survey-20260730T000001-2222.json").write_text(json.dumps(
            {"ticket": "fwd-proof", "sought": ["the moved thing"],
             "holdings": [{"what": "the thing that moved", "address": "gone/away.py"}],
             "absences": [{"what": "nothing", "measure": "census rows"}]}))
        # THE THIRD SIEVE OF THE FAMILY, added 2026-08-14. A constraint's `source` is
        # an address exactly as a holding's `address` is, and a move breaks it
        # identically — but the successor door was fitted on 2026-07-30 to the two
        # sieves whose findings were in that day's refusal, and this one kept the flat
        # rule for fifteen days. Found by measurement, not by reading: ground_loop's
        # PROVEME crossing red 52, a forwarding order disposed 40, and all 12 that
        # stood were constraint sources ALREADY FORWARDED on the same tickets with the
        # successor resolving. Bounds are valid here on purpose, so `constraint_traces`
        # is the only constrain sieve that can speak in this fixture.
        (mp / "constrain-20260730T000002-3333.json").write_text(json.dumps(
            {"ticket": "fwd-proof",
             "constraints": [{"text": "the moved thing bounds this build",
                              "source": "gone/away.py", "kind": "charter"}],
             "bounds": {"in": ["the move"], "out": ["everything else"]}}))

        # (i) NO ORDER: all three mouths red. The tolerance is opt-in, never the default.
        names = lambda comp: sorted(x["method"] for x in           # noqa: E731
                                    inspect(root=root, component=comp)["findings"])
        assert names("moved") == ["charted_refs_resolve", "constraint_traces",
                                  "survey_holdings_resolve"], \
            "a missing charted address with no forwarding order must still red"

        # (ii) A WHOLE ORDER: all three disposed, and nothing else is loosened.
        _order({"gone/away.py": {"to": "base", "why": "renamed by piece (f)"}})
        assert names("moved") == [], inspect(root=root, component="moved")["findings"]

        # (iii) FORWARDING TO NOTHING: the order reds by its own name AND disposes
        #       nothing — the missing-ref findings stand. Two loud records, never one
        #       silent pass; a successor the world does not hold is the same hollow
        #       claim as the ref it was offered to dispose, one indirection later.
        _order({"gone/away.py": {"to": "also/gone.py", "why": "renamed by piece (f)"}})
        assert names("moved") == ["charted_refs_resolve", "constraint_traces",
                                  "forwarding_order_resolves",
                                  "survey_holdings_resolve"], names("moved")

        # (iv) FORWARDING A LIVE ADDRESS: reds. A forwarding order is for what MOVED;
        #      re-aiming a resolving address would let a chart's claim be pointed at a
        #      different thing while the original sits there untouched.
        _order({"librarian": {"to": "base", "why": "not a move at all"}})
        assert "forwarding_order_resolves" in names("moved"), names("moved")
        assert "retired" in [x["about"] for x in
                                    inspect(root=root, component="moved")["findings"]
                                    if x["method"] == "forwarding_order_resolves"][0]

        # (v) THE WHY IS FORCED STRUCTURALLY (CP3), and so is the shape.
        for broken in ({"gone/away.py": {"to": "base"}},
                       {"gone/away.py": {"why": "no successor named"}},
                       {"gone/away.py": "base"},
                       {"gone/away.py": {"to": "base", "why": "   "}}):
            _order(broken)
            assert "forwarding_order_resolves" in names("moved"), (broken, names("moved"))
            assert "charted_refs_resolve" in names("moved"), \
                ("a broken order must grant no tolerance at all", broken)
            assert "constraint_traces" in names("moved"), \
                ("and 'no tolerance at all' reaches the third sieve too — the half "
                 "that went unmeasured for fifteen days", broken)
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
        _order({"gone/away.py": {"to": "base", "why": "renamed by piece (f)"}})
        assert names("moved") == [], "the promotion side disposes a whole order"
        berthed = json.loads((mp / "survey-20260730T000001-2222.json").read_text())
        assert [x["judge"] for x in _jfindings(judge_survey(berthed))] == ["survey_holdings_resolve"], \
            "the berth door must still refuse a holding the world does not hold"
        # and the same for the constrain door, whose promotion side just learned the
        # tolerance: the two mouths of judge_constrain must NOT come to agree. If a
        # berth door inherited this, a packet could be admitted naming an address that
        # was already gone — the tolerance would have become the laundering it exists
        # to stop, one door upstream of where anyone is looking.
        from cairn.machines.build_inspector.inspector import judge_constrain
        berthed_c = json.loads((mp / "constrain-20260730T000002-3333.json").read_text())
        assert [x["judge"] for x in _jfindings(judge_constrain(berthed_c))] == ["constraint_traces"], \
            "the berth door must still refuse a constraint whose source is not there"

        # (vii) A TICKET THAT MOVES NOTHING is the normal case and says nothing.
        tfile.write_text(json.dumps({"id": "fwd-proof"}))
        assert names("moved") == ["charted_refs_resolve", "constraint_traces",
                                  "survey_holdings_resolve"]
        (mp / "orient-20260730T000000-1111.json").unlink()
        (mp / "survey-20260730T000001-2222.json").unlink()
        (mp / "constrain-20260730T000002-3333.json").unlink()
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
        assert [x["method"] for x in ef] == ["buildme_rides_the_chart"], ef
        assert ef[0]["component"] == "lonely" and \
            ef[0]["values"]["searched"] == str(eroot), ef[0]
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
        assert [x["method"] for x in xf] == ["proved_answers_the_chart"], xf
        assert xf[0]["about"] == "verdict artifact exists" and \
            str(val) in xf[0]["values"]["claiming"], xf[0]
        # a verdict answering someone ELSE's chart: red, not an answer here
        stray = xp / "verdict-20260729T000002-cccc.json"
        stray.write_text(json.dumps(
            {"ticket": "sworn", "validate_ref": str(xp / "elsewhere.json"),
             "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "pass",
                           "evidence": "seen",
                           "discriminating_observation": "reverted the fix; instrument exits 1"}],
             "dispositions": [{"piece": "p1", "expect": "e1",
                               "disposition": "confirmed", "by": "obs"}]}))
        xf = proved_answers_the_chart("sworn", berths_root=xroot)
        assert xf and "claiming" in xf[0]["about"], xf
        # narration (empty evidence) is malformed, loudly — done may not live there
        stray.unlink()
        bad = xp / "verdict-20260729T000003-dddd.json"
        bad.write_text(json.dumps(
            {"ticket": "sworn", "validate_ref": str(val),
             "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "pass",
                           "evidence": ""}],
             "dispositions": []}))
        xf = proved_answers_the_chart("sworn", berths_root=xroot)
        assert xf and xf[0]["about"] == "verdict artifact well-formed", xf
        # answered-and-FAILED + undispositioned: one complete finding EACH, first pass
        bad.unlink()
        half = xp / "verdict-20260729T000004-eeee.json"
        half.write_text(json.dumps(
            {"ticket": "sworn", "validate_ref": str(val),
             "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "fail",
                           "evidence": "it broke",
                           "discriminating_observation": "the failing run itself"}],
             "dispositions": []}))
        xf = proved_answers_the_chart("sworn", berths_root=xroot)
        assert len(xf) == 2, xf
        assert "FAILED" in xf[0]["about"] and "kick-back" in xf[0]["about"], xf[0]
        assert "undispositioned" in xf[1]["about"] and "p1" in xf[1]["about"], xf[1]
        # the complete answer stands: LATEST artifact wins, green, empty findings
        (xp / "verdict-20260729T000005-ffff.json").write_text(json.dumps(
            {"ticket": "sworn", "validate_ref": str(val),
             "verdicts": [{"claim": "c1", "instrument": "cmd", "outcome": "pass",
                           "evidence": "seen: exit 0 twice",
                           "discriminating_observation": "reverted the fix; instrument exits 1"}],
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
    _reseal(rogue)
    f = inspect(root=root, component="rogue")["findings"]
    assert [x["method"] for x in f] == ["sole_path_holds"], \
        f"the planted dialer must red exactly sole_path_holds: {f}"
    assert "dialer.py" in f[0]["about"], f[0]
    # the rogue's door reds the ROGUE's row alone — healthy keeps its clean.
    assert inspect(root=root, component="healthy")["clean"], \
        "another component's door must never red a clean component's row"
    # and the mesh's own exemption: the same import INSIDE inference_domain is the
    # sole path itself, not a second door.
    dom = _component(root, "inference_domain")
    (dom / "host.py").write_text("import urllib.request\n")
    _reseal(dom)
    assert inspect(root=root, component="inference_domain")["clean"], \
        "inference_domain IS the door — the mesh's 'only' must spare it"

    # ── durable_state_declared (relational-state-goes-through-the-one-door) ──
    # A charter declaring durable_state outside db_domain reds; one declaring
    # db_domain passes; one with no declaration passes silently.
    bad_ds = _component(root, "bad_durable")
    charter = json.loads((bad_ds / "intention+why.json").read_text())
    charter["durable_state"] = "local_file"
    (bad_ds / "intention+why.json").write_text(json.dumps(charter))
    _reseal(bad_ds)
    f = inspect(root=root, component="bad_durable")["findings"]
    assert [x["method"] for x in f] == ["durable_state_declared"], \
        f"a charter declaring durable_state: local_file must red exactly durable_state_declared: {f}"

    good_ds = _component(root, "good_durable")
    charter = json.loads((good_ds / "intention+why.json").read_text())
    charter["durable_state"] = "db_domain"
    (good_ds / "intention+why.json").write_text(json.dumps(charter))
    _reseal(good_ds)
    assert inspect(root=root, component="good_durable")["clean"], \
        "a charter declaring durable_state: db_domain must pass"

    assert inspect(root=root, component="healthy")["clean"], \
        "a charter with no durable_state field must pass silently"

    # ── learning_declared (learning-as-a-pattern) ────────────────────────────
    # A charter with a blank learns field fires; a populated one passes.
    bad_learn = _component(root, "bad_learns")
    charter = json.loads((bad_learn / "intention+why.json").read_text())
    charter["learns"] = ""
    (bad_learn / "intention+why.json").write_text(json.dumps(charter))
    _reseal(bad_learn)
    f = inspect(root=root, component="bad_learns")["findings"]
    assert [x["method"] for x in f] == ["learning_declared"], \
        f"a charter with learns: '' must red exactly learning_declared: {f}"

    assert inspect(root=root, component="healthy")["clean"], \
        "a charter with a populated learns field must pass"

    # A charter with no learns key at all also fires.
    no_learn = _component(root, "no_learns")
    charter = json.loads((no_learn / "intention+why.json").read_text())
    del charter["learns"]
    (no_learn / "intention+why.json").write_text(json.dumps(charter))
    _reseal(no_learn)
    f = inspect(root=root, component="no_learns")["findings"]
    assert [x["method"] for x in f] == ["learning_declared"], \
        f"a charter with no learns key must red exactly learning_declared: {f}"

    # ── claim_provenance (a-claim-carries-its-provenance) ────────────────────
    # A charter with missing or empty claim_provenance fires; a populated one passes.
    bad_cp = _component(root, "bad_claim_prov")
    charter = json.loads((bad_cp / "intention+why.json").read_text())
    charter["claim_provenance"] = {}
    (bad_cp / "intention+why.json").write_text(json.dumps(charter))
    _reseal(bad_cp)
    f = inspect(root=root, component="bad_claim_prov")["findings"]
    assert [x["method"] for x in f] == ["claim_provenance"], \
        f"a charter with empty claim_provenance must red exactly claim_provenance: {f}"

    assert inspect(root=root, component="healthy")["clean"], \
        "a charter with a populated claim_provenance dict must pass"

    # A charter with no claim_provenance key at all also fires.
    no_cp = _component(root, "no_claim_prov")
    charter = json.loads((no_cp / "intention+why.json").read_text())
    del charter["claim_provenance"]
    (no_cp / "intention+why.json").write_text(json.dumps(charter))
    _reseal(no_cp)
    f = inspect(root=root, component="no_claim_prov")["findings"]
    assert [x["method"] for x in f] == ["claim_provenance"], \
        f"a charter with no claim_provenance key must red exactly claim_provenance: {f}"

    # ── working_tree_clean (nothing-rides-loose) ────────────────────────────
    # The main fixture is NOT a git repo, so working_tree_clean returns []
    # vacuously for every component above. These teeth use a purpose-built
    # git repo (following test_history_integrity.py's pattern) and call the
    # sieve directly.

    import subprocess as _wt_sp

    def _wt_git(repo, *args):
        _wt_sp.run(["git", "-C", str(repo), *args],
                    check=True, capture_output=True, text=True)

    def _wt_row(name):
        return {"component": name, "dir": name, "charter_on_disk": True}

    # Tooth 1 — planted-graph: a dirty subtree fires working_tree_clean
    with scratch_dir("inspector-proof-wt-dirty-") as wt_root:
        _wt_git(wt_root, "init")
        _wt_git(wt_root, "config", "user.email", "test@test")
        _wt_git(wt_root, "config", "user.name", "test")
        comp = wt_root / "dirty_comp"
        comp.mkdir()
        (comp / "intention+why.json").write_text(
            json.dumps({"component": "dirty_comp"}))
        (comp / "source.py").write_text("x = 1\n")
        _wt_git(wt_root, "add", ".")
        _wt_git(wt_root, "commit", "-m", "initial")
        # now dirty it
        (comp / "source.py").write_text("x = 2\n")
        findings = working_tree_clean(_wt_row("dirty_comp"), comp)
        assert len(findings) == 1, \
            f"dirty subtree must fire exactly one finding: {findings}"
        assert findings[0]["method"] == "working_tree_clean", \
            f"finding method must be working_tree_clean: {findings[0]}"
        assert findings[0]["values"]["dirty_count"] >= 1, \
            f"dirty_count must be >= 1: {findings[0]}"

    # Tooth 2 — real-corpus: a clean subtree stays quiet
    with scratch_dir("inspector-proof-wt-clean-") as wt_root:
        _wt_git(wt_root, "init")
        _wt_git(wt_root, "config", "user.email", "test@test")
        _wt_git(wt_root, "config", "user.name", "test")
        comp = wt_root / "clean_comp"
        comp.mkdir()
        (comp / "intention+why.json").write_text(
            json.dumps({"component": "clean_comp"}))
        (comp / "source.py").write_text("x = 1\n")
        _wt_git(wt_root, "add", ".")
        _wt_git(wt_root, "commit", "-m", "initial")
        # no modifications — tree is clean
        findings = working_tree_clean(_wt_row("clean_comp"), comp)
        assert findings == [], \
            f"clean subtree must not fire: {findings}"

    # ── the nest (2026-08-06, ticket the-questions-are-the-sieve) ────────────
    #
    # BANDS ARE PHASES (Akien, 2026-08-12, ruled; confirmed 2026-08-21). All current
    # sieves take the subject — they are record sieves (band 1). The tooth verifies
    # that, and then mutates a sieve to take prior stamps and demands the phase MOVE
    # to postprocess (band 2) — DERIVED, never authored.
    nest = _insp.the_nest()
    banded = {name: b for b, names in nest for name in names}
    assert all(b == 1 for b in banded.values()), (
        f"all current sieves should be record (1): {banded}")
    assert [b for b, _ in nest] == sorted(b for b, _ in nest), \
        "the nest is shaken coarse band first — that ordering IS the nest"

    src = pathlib.Path(_insp.__file__).read_text()
    phases = _insp.import_sieve.phase_of(src)
    assert phases["charter_on_disk"] == 1, phases["charter_on_disk"]
    # now make that same sieve take stamps — it should become postprocess
    mutant = src.replace(
        "def charter_on_disk(row: dict, comp_dir: Path) -> list[dict]:",
        "def charter_on_disk(stamps, row: dict, comp_dir: Path) -> list[dict]:", 1)
    assert mutant != src, "the mutation did not apply — the tooth would be vacuous"
    moved = _insp.import_sieve.phase_of(mutant)
    assert moved["charter_on_disk"] == 2, (
        "a sieve that started reading stamps kept its phase — the phase is being "
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
    caught = {f["method"] for f in rep["findings"]}
    for f in rep["findings"]:
        # BY ADDRESS, NOT BY NAME (2026-08-13). The gradation is keyed by the component's
        # dir because two components answer to "orient"; correlating on the bare name here
        # would either KeyError (as it did the day the builder device landed) or, worse,
        # silently match the wrong subject's row and pronounce the pairing sound.
        assert rep["gradation"][f["at"]][f["method"]] == 0.0, f
    for comp, scores in rep["gradation"].items():
        for name, s in scores.items():
            if s == 1.0:
                assert not any(f["method"] == name and f["at"] == comp
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
