"""Teeth for ticket 67b78ae59c1d — nothing outside the tester reaches into its code.

RULE 1 (Akien, 2026-10-01): a device's public interface is the bus plus any client tool it
publishes. Measured 2026-10-02 before the build: 15 encapsulation rows landed on tester
modules other than its store — device 7, cli 3, hollow 3, scratch_sweep 1, discovery 1 —
from harbor_master, codemother, db_domain, proof_coverage, system_word and tools/base. The
declared paths are the bus (`run`: one proof, sink none, the record back as JSON) and the
tester's own proofs, so each foreign site either asks the verb or its tooth moves here.

One tooth per numbered falsifier clause, over the LIVE repo and the live bus:

  1. NO FOREIGN ROW. encapsulation_breaches('.') carries no row on cairn.devices.tester.*.
  2. THE VERB ANSWERS WITH THE TESTER'S VERDICT. declared_verbs() has `run`; a green fixture
     asked over the bus comes back green, a red one red — read, not granted.
  3. THE TOOL FLOOR STANDS ON NO DEVICE. cairn/tools/base/validation.py imports nothing from
     cairn.devices, at any depth of the module (function-local imports included); its discover
     answers over a scratch tree; and no code imports discovery from its old device address.

Clause 2 is also declared by constrain's own test_one_red_check_does_not_blanket_the_report,
the foreign caller that asks the run verb for an instrument's verdict — measured from inside
codemother, where RULE 1 puts that measurement.

    python3 cairn/devices/tester/proofs/test_the_tester_is_reached_only_through_its_interface.py
"""
from __future__ import annotations

import ast
import importlib
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.proof_coverage.proof_coverage import print_teeth_main  # noqa: E402

PROVES = {
    "67b78ae59c1d": {
        "1": "test_no_foreign_row_lands_on_the_tester",
        "2": "test_the_run_verb_answers_with_the_testers_verdict",
        "3": "test_the_tool_floor_stands_on_no_device",
    },
    # 45c168cc1ff1 clause (1): no row from the loop proof reaches into the tester.
    "45c168cc1ff1": {"1": "test_no_foreign_row_lands_on_the_tester"},
}

FIXTURES = Path(__file__).resolve().parent / "fixtures"


def test_no_foreign_row_lands_on_the_tester():
    # Resolved at call time, so the hollow taking the build away reads as a red tooth.
    inspector = importlib.import_module("cairn.machines.build_inspector.inspector")
    rows = [b for b in inspector.encapsulation_breaches(str(_REPO_ROOT))
            if (b.get("module") or "").startswith("cairn.devices.tester")]
    assert not rows, f"{len(rows)} reach(es) into the tester: " + "; ".join(
        f"{b['file']}:{b['line']} {b['module']}" for b in rows[:10])


def _ask_run(proof: Path) -> dict:
    from cairn.tools.bus_client.bus_client import reach
    reply = reach("tester").request(
        sender="tester-proof-67b78ae59c1d", to="tester", verb="run",
        why="the run verb's own tooth asks for a fixture's verdict",
        body={"path": str(proof), "caller": "test_the_tester_is_reached_only_through_its_interface"},
        timeout=120)
    assert isinstance(reply, dict) and isinstance(reply.get("body"), dict), reply
    return reply["body"]


def test_the_run_verb_answers_with_the_testers_verdict():
    device = importlib.import_module("cairn.devices.tester.device")
    verbs = device.TesterDevice().declared_verbs()
    assert "run" in verbs, f"the tester declares no `run` verb: {sorted(verbs)}"
    for name, want in (("green_proof.py", "green"), ("red_proof.py", "red")):
        body = _ask_run(FIXTURES / name)
        record = body.get("record")
        assert isinstance(record, dict), f"{name}: no record came back: {body}"
        assert record.get("verdict") == want, f"{name}: verdict {record.get('verdict')!r}, want {want!r}"
    refused = _ask_run(FIXTURES / "no_such_proof_67b78ae59c1d.py")
    assert refused.get("refused") and "record" not in refused, \
        f"a path that is not there must be refused by name, not run: {refused}"


def test_the_tool_floor_stands_on_no_device():
    src = _REPO_ROOT / "cairn" / "tools" / "base" / "validation.py"
    reaches = []
    for node in ast.walk(ast.parse(src.read_text(encoding="utf-8"))):
        mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        reaches += [f"{node.lineno} {m}" for m in mods if m.startswith("cairn.devices")]
    assert not reaches, f"cairn/tools/base/validation.py imports device code: {reaches}"
    # AND THE FLOOR STANDS ON THE TOOL, NOT ON A DEVICE COPY. The hollow measured 2026-10-02
    # that an import list says nothing about whether the floor still works: with the tool
    # removed, validation.py read clean here and could not discover a single proof. So the
    # floor is CALLED, over a scratch tree, at call time ...
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        proof = Path(tmp) / "c" / "proofs" / "test_floor_67b78ae59c1d.py"
        proof.parent.mkdir(parents=True)
        proof.write_text("", encoding="utf-8")
        validation = importlib.import_module("cairn.tools.base.validation")
        found = [Path(p).resolve() for p in validation.discover([tmp])]
        assert found == [proof.resolve()], f"validation.discover did not find the floor's proof: {found}"
    # ... and nothing in the repo still stands on discovery's old device address — the tester's
    # own cli included, which reached it until the move.
    old_address = "cairn.devices.tester." + "discovery"
    stale = []
    for py in sorted((_REPO_ROOT / "cairn").rglob("*.py")):
        try:
            tree = ast.parse(py.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                    else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
            stale += [f"{py.relative_to(_REPO_ROOT)}:{node.lineno}" for m in mods
                      if m == old_address or m.startswith(old_address + ".")]
    assert not stale, f"code still imports discovery from the tester device: {stale}"


if __name__ == "__main__":
    raise SystemExit(print_teeth_main(__file__))
