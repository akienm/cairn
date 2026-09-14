"""Teeth for the binding sieve — a proof that binds a build-added name at module level is red
at PROVEME, by line, before the hollow reading spends its budget to say UNRAN.

Charter: cairn/tools/proof_coverage/intention+why.json
Ticket:  CairnCommons/tickets/c5b6b128a376-a-proof-that-binds-an-added-name-at-import-is-red-at-proveme-not-unran-at-hollow.json

Run: python3 cairn/tools/proof_coverage/proofs/test_call_time_binding.py

THIS PROOF OBEYS THE RULE IT PROVES. ``proof_coverage`` is bound at module level below
because the package existed before this build (the sieve reads green over it by the same
measurement it applies to everyone: ``proof_coverage.py`` is a modified file, and the only
names this proof binds at import are the module objects, not the added function). The
sieve itself — the added name — is reached INSIDE each tooth, so the hollow reading that
takes it away reds a tooth here instead of crashing the runner. The fixtures live under
``proofs/``, which hollow never reverts.
"""
from __future__ import annotations

import ast
import json
import shutil
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(REPO_ROOT))

from cairn.tools import proof_coverage as pc  # noqa: E402  (the package existed before the build)
from cairn.tools.proof_coverage.proofs.fixtures import historical_instances as H  # noqa: E402

PROVES = {
    "c5b6b128a376": {
        "1": "test_a_direct_module_level_import_of_an_added_file_is_red_by_line_and_green_inside_main",
        "2": "test_a_transitive_binding_is_red_naming_the_chain",
        "3": "test_the_three_historical_shapes_red_at_the_line_the_hand_fix_touched",
        "4": "test_the_sieve_names_the_file_hollow_reads_unran_and_without_it_the_ticket_reaches_hollow",
        "5": "test_the_sail_liturgy_carries_the_rule_and_the_sail_proof_declares_it",
    }
}

TICKET = "c5b6b128a376"
COMMONS = REPO_ROOT.parent / "CairnCommons"
_SCRATCH: list[tempfile.TemporaryDirectory] = []


def _tmp() -> Path:
    d = tempfile.TemporaryDirectory(prefix="cairn_binding_sieve_fixture_")
    _SCRATCH.append(d)
    return Path(d.name)


def _sieve():
    """The added name, resolved at call time — the rule this file proves."""
    return pc.proof_coverage.proof_binds_its_subject_at_call_time


def _lacks(world: H.World) -> list[dict]:
    return _sieve()(world.ticket, repo_root=world.repo, roots=world.roots)


# ── clause 1 ──────────────────────────────────────────────────────────────────────────

def test_a_direct_module_level_import_of_an_added_file_is_red_by_line_and_green_inside_main():
    red = H.direct_added_file(_tmp())
    found = _lacks(red)
    assert len(found) == 1, f"expected one lack, got {json.dumps(found, indent=1)}"
    lack = found[0]
    assert lack["kind"] == "proof_binds_its_subject_at_call_time", lack["kind"]
    v = lack["values"]
    assert v["proof"].endswith(red.proof), v["proof"]
    assert v["line"] == red.notes["binding_line"], v
    assert v["file"] == red.notes["added_file"], v
    assert v["chain"][0].endswith(f"{red.proof}:{red.notes['binding_line']}"), v["chain"]
    assert "call time" in lack["why"] and "UNRAN" in lack["why"], lack["why"]
    green = H.direct_added_file(_tmp(), moved_into_main=True)
    assert _lacks(green) == [], "the same import inside main() must read green"
    return True


# ── clause 2 ──────────────────────────────────────────────────────────────────────────

def test_a_transitive_binding_is_red_naming_the_chain():
    world = H.transitive_added_file(_tmp())
    found = _lacks(world)
    assert len(found) == 1, json.dumps(found, indent=1)
    v = found[0]["values"]
    assert v["file"] == world.notes["added_file"], v
    assert v["chain"] == [f"{world.proof}:{world.notes['proof_line']}",
                          f"runner_that_existed.py:{world.notes['helper_line']}"], v["chain"]
    # the lack is anchored where the binding IS — the helper's line, where the hand fix went
    # on 2026-09-10 — and the chain runs from the proof down to it
    assert v["module"] == "runner_that_existed.py" and v["line"] == world.notes["helper_line"], v
    assert v["chain"][-1] == f"{v['module']}:{v['line']}", v
    return True


# ── clause 3 ──────────────────────────────────────────────────────────────────────────

def test_the_three_historical_shapes_red_at_the_line_the_hand_fix_touched():
    # 2026-09-10 proof_coverage.py -> crossings.py (transitive added FILE)
    first = H.transitive_added_file(_tmp())
    # 2026-09-13 a38204e test_artifact_door.py (direct added FILE)
    second = H.direct_added_file(_tmp())
    # 2026-09-14 e1dcc6e test_exemption_set.py -> justification -> citation (added NAME)
    third = H.transitive_added_name(_tmp())
    # each hand fix landed at the innermost hop — proof_coverage.py itself on 09-10, the
    # proof on 09-13, justification.py on 09-14 — and that is the line the sieve anchors
    for world, line in ((first, first.notes["helper_line"]),
                        (second, second.notes["binding_line"]),
                        (third, third.notes["justification_line"])):
        found = _lacks(world)
        assert len(found) == 1, (world.proof, json.dumps(found, indent=1))
        assert found[0]["values"]["line"] == line, (world.proof, found[0]["values"])
    v = _lacks(third)[0]["values"]
    assert v.get("name") == third.notes["added_name"] and v.get("in") == third.notes["in"], v
    assert v["chain"][-1].endswith(f":{third.notes['justification_line']}"), v["chain"]
    # the hand fix that landed in e1dcc6e — try/except with a stub — reads green
    fixed = H.transitive_added_name(_tmp(), hand_fixed=True)
    assert _lacks(fixed) == [], "the hand-fixed shape must read green"
    # the fourth shape — a loader call — is the charter's filed edge: green by construction
    blind = H.loader_call_blind_spot(_tmp())
    assert _lacks(blind) == [], "the loader-call shape is hollow's, not the sieve's"
    charter = json.loads((REPO_ROOT / "cairn/tools/proof_coverage/intention+why.json").read_text())
    edges = json.dumps(charter.get("filed_edges") or charter.get("edges") or charter)
    assert "importlib" in edges and "proof_binds_its_subject_at_call_time" in edges, (
        "the charter must file the loader-call blind spot as the sieve's edge")
    # and the tester's charter names the sieve as hollow's FRONT DOOR — hollow stays the
    # backstop for the shapes the walk cannot see, and says so where hollow is chartered
    tester = json.loads((REPO_ROOT / "cairn/devices/tester/intention+why.json").read_text())
    tedges = json.dumps(tester.get("filed_edges") or []).lower()
    assert "proof_binds_its_subject_at_call_time" in tedges and "front door" in tedges, (
        "the tester's charter must name the sieve as the hollow reading's front door")
    return True


# ── clause 4 — the self-reference tooth ───────────────────────────────────────────────

def test_the_sieve_names_the_file_hollow_reads_unran_and_without_it_the_ticket_reaches_hollow():
    world = H.direct_added_file(_tmp())
    # (a) lacks() carries the sieve's finding on the same list PROVEME reads
    full = pc.lacks(world.ticket, repo_root=world.repo, roots=world.roots)
    binding = [l for l in full if l["kind"] == "proof_binds_its_subject_at_call_time"]
    assert len(binding) == 1, [l["kind"] for l in full]
    predicted = binding[0]["values"]["file"]
    # (b) with the sieve reverted, the same ticket passes lacks() clean of it — reaches hollow
    module = pc.proof_coverage
    real = module.proof_binds_its_subject_at_call_time
    module.proof_binds_its_subject_at_call_time = lambda *a, **k: []
    try:
        without = pc.lacks(world.ticket, repo_root=world.repo, roots=world.roots)
    finally:
        module.proof_binds_its_subject_at_call_time = real
    assert not [l for l in without if l["kind"] == "proof_binds_its_subject_at_call_time"], (
        "the tooth must depend on the sieve being present")
    assert [l["kind"] for l in without] == [l["kind"] for l in full
                                            if l["kind"] != "proof_binds_its_subject_at_call_time"]
    # (c) hollow, run over the same world, reads exactly that file UNRAN for that proof
    from cairn.devices.tester import hollow  # bound here: the tester is another component
    reading = hollow.measure(world.ticket["id"], repo_root=world.repo, commons=world.commons,
                             berths_root=world.roots["berths"], timeout=120, log=lambda *_: None)
    unran = reading.get("unran") or {}
    assert predicted in unran, (predicted, reading.get("verdict"), reading.get("reasons"))
    assert any(p.endswith(world.proof) for p in unran[predicted]), unran
    assert reading.get("verdict") == "red", reading.get("verdict")
    # (d) in life the same comparison is the WATCHME probe's: every hollow UNRAN measured
    # against what the sieve predicted. Armed, or the crossing cannot be made.
    _probe_is_armed()
    return True


def _probe_is_armed():
    import importlib  # bound here: the probe berths with what it watches, added by this build
    pkg = importlib.import_module("cairn.tools.proof_coverage.probes")
    assert pkg.__file__ and pkg.__file__.endswith("__init__.py"), (
        "the probes berth is a regular package, not a namespace fallback — its __init__ says "
        "what berths there")
    assert "WATCHME" in (pkg.__doc__ or ""), pkg.__doc__
    mod = importlib.import_module("cairn.tools.proof_coverage.probes.sieve_predicts_unran")
    probe = mod.PROBE
    assert probe.to == "harbor_master" and callable(probe.carry) and callable(probe.enough)
    carried = probe.carry({})
    assert "finding" in carried and "unpredicted" in carried, carried
    assert isinstance(carried["readings_since_build"], int)
    assert isinstance(carried["unpredicted"], list)
    return carried


# ── clause 5 ──────────────────────────────────────────────────────────────────────────

def test_the_sail_liturgy_carries_the_rule_and_the_sail_proof_declares_it():
    skill = (REPO_ROOT / "skills/sail/SKILL.md").read_text(encoding="utf-8")
    step3 = skill.split("## 3. Prove")[1].split("\n## ")[0]
    assert "at call time" in step3 and "proof_binds_its_subject_at_call_time" in step3, step3
    proof = REPO_ROOT / "skills/sail/proofs/test_sail_pins_its_refusals.py"
    declared = pc.proof_coverage.declared(proof)
    assert declared.get(TICKET, {}).get("5"), declared
    tooth = declared[TICKET]["5"]
    assert tooth in proof.read_text(encoding="utf-8")
    run = subprocess.run([sys.executable, str(proof)], capture_output=True, text=True, timeout=120)
    assert run.returncode == 0, run.stdout + run.stderr
    assert f"ok   {tooth}" in run.stdout, run.stdout
    return True


# ── extras — not clauses, still teeth ────────────────────────────────────────────────

def test_the_watchme_probe_is_armed_with_carry_and_enough():
    _probe_is_armed()
    return True


def test_this_proof_binds_nothing_the_build_added_at_module_level():
    """The sieve over THIS ticket's own proofs: the rule applied to the file that proves it.
    Silent when the crossing record is not there yet (before PROVEME the sieve has no
    pre-build commit to diff against) — but never a lack."""
    tickets = {t["id"]: t for t in pc.proof_coverage.load_tickets(COMMONS)}
    ticket = tickets.get(TICKET)
    assert ticket, f"{TICKET} not in the commons"
    found = _sieve()(ticket, repo_root=REPO_ROOT)
    assert found == [], json.dumps(found, indent=1)
    return True


def test_every_live_corpus_lack_is_a_module_level_import_of_something_absent_at_pre():
    """Invariant over the live corpus, never a snapshot: each lack anchors an Import or
    ImportFrom at the line it names, and the file it names was truly absent (or the name
    truly unbound) at the ticket's pre-build commit."""
    from cairn.tools.base.crossings import buildme_crossing
    tickets = pc.proof_coverage.load_tickets(COMMONS)
    checked = 0
    for ticket in tickets:
        if not buildme_crossing(ticket["id"]):
            continue
        for lack in _sieve()(ticket, repo_root=REPO_ROOT):
            v = lack["values"]
            assert v["chain"][0].startswith(v["proof"] + ":"), (ticket["id"], v)
            assert v["chain"][-1] == f"{v['module']}:{v['line']}", (ticket["id"], v)
            for hop in v["chain"]:
                head = hop.rsplit(":", 1)
                src, line = REPO_ROOT / head[0], int(head[1])
                stmts = [n for n in ast.parse(src.read_text(encoding="utf-8")).body
                         if isinstance(n, (ast.Import, ast.ImportFrom)) and n.lineno == line]
                assert stmts, (ticket["id"], hop, "is not a module-level import")
            pre = pc.proof_coverage._prebuild_commit(buildme_crossing(ticket["id"])["at"],
                                                     repo_root=REPO_ROOT)
            assert pre, ticket["id"]
            if "file" in v:
                shown = pc.proof_coverage._git(REPO_ROOT, "show", f"{pre}:{v['file']}")
                assert shown is None, (ticket["id"], v["file"], "existed at", pre)
            else:
                shown = pc.proof_coverage._git(REPO_ROOT, "show", f"{pre}:{v['in']}")
                assert shown is not None, (ticket["id"], v["in"])
                assert v["name"] not in pc.proof_coverage._top_level_names(shown), (
                    ticket["id"], v["name"], "bound at", pre)
            checked += 1
    print(f"       (live corpus: {checked} lack(s) each anchored on a module-level import "
          f"of something absent at pre)")
    return True


# ── runner ────────────────────────────────────────────────────────────────────────────

def main() -> int:
    reds = 0
    teeth = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    for name, fn in teeth:
        try:
            fn()
            print(f"  ok   {name}")
        except Exception:  # noqa: BLE001 — a proof reports, never hides
            reds += 1
            print(f"RED  {name}")
            traceback.print_exc()
    for d in _SCRATCH:
        d.cleanup()
    print(f"{'GREEN' if not reds else 'RED'} — {len(teeth) - reds}/{len(teeth)} teeth")
    return 1 if reds else 0


if __name__ == "__main__":
    raise SystemExit(main())
