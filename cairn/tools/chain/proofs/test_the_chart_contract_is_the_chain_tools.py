"""Proof for ticket d8e8a2dc1176 — the chart chain's contract lives in the chain tool, and no gate,
probe or dial reaches into codemother's machines to read it.

RULE 1 (Akien, 2026-10-01): every component talks to every other only through its public
interface; a device's is the bus plus any client tool it publishes. The verdict coverage reader
(`unanswered` and the falsifier reader under it) and the verdict-deposit ledger are chart's
contract — verdict.py's own comment reads "Law 6: chart owns the ledger" — which codemother's
verdict machine happened to hold, and the seven stage field tuples are the chain's shapes, which
the chart dial imported seven machines to read. Measured before the build: the build inspector,
the PROVED crossing in transitions, two tools/base probes, three proofs and the dial reached into
codemother for them.

One tooth per numbered falsifier clause, over the LIVE repo (invariants, never snapshots). The
teeth READ codemother's files and never import them, so this proof is not itself a reach:

  1. NOTHING REACHES CODEMOTHER FOR THE CONTRACT. No encapsulation_breaches row lands in
     codemother's verdict machine except from skills/chart/live.py (the deposit, sibling
     the-chart-deposit-is-a-codemother-verb), and none from skills/chart/dial.py lands in
     codemother at all.
  2. THE CONTRACT STANDS IN THE CHAIN TOOL. The chain charter declares
     cairn.tools.chain.verdict_contract, that module imports nothing from cairn.devices, it
     exposes the coverage reader and the ledger, and the ledger is still chart's file.
  3. CODEMOTHER BINDS THE SAME OBJECTS. verdict.py defines none of the moved names and imports
     each from the chain tool; every stage machine's AUTHORED_FIELDS is
     STAGE_AUTHORED_FIELDS['<stage>'], and the table holds exactly the seven stages with the
     values the machines carried before the move.

    python3 cairn/tools/chain/proofs/test_the_chart_contract_is_the_chain_tools.py   # exit 0 = green
"""
import ast
import json
import os
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))


class _Late:
    """The build's names resolve AT CALL TIME, so `cairn test --hollow` taking the module away
    reads as red teeth rather than an import that never ran."""

    def __init__(self, module):
        self._module = module

    def __getattr__(self, name):
        import importlib
        return getattr(importlib.import_module(self._module), name)


_inspector = _Late("cairn.machines.build_inspector.inspector")

PROVES = {"d8e8a2dc1176": {"1": "nothing_reaches_codemother_for_the_contract",
                           "2": "the_contract_stands_in_the_chain_tool",
                           "3": "codemother_binds_the_same_objects"}}

CHAIN_DIR = _REPO_ROOT / "cairn" / "tools" / "chain"
CONTRACT = "cairn.tools.chain.verdict_contract"
MACHINES = _REPO_ROOT / "cairn" / "devices" / "codemother" / "machines"
VERDICT_DIR = "cairn/devices/codemother/machines/verdict"
DEPOSIT_CALLER = "skills/chart/live.py"
DIAL = "skills/chart/dial.py"
MOVED = ("unanswered", "falsifier_criteria", "FALSIFIER_REF", "VerdictRefused",
         "LEDGER_PATH", "read_ledger", "pending", "enqueue_verdict", "mark_deposited")
CALLABLE = ("unanswered", "falsifier_criteria", "read_ledger", "pending", "enqueue_verdict",
            "mark_deposited")
# The values each machine carried at the cast (2026-10-02), copied from the machines' own
# AUTHORED_FIELDS lines: the move is a relocation, so a value that changed is a defect.
STAGES = {
    "orient": ("intent", "domain", "scope", "refs", "unknowns"),
    "constrain": ("intent_ref", "constraints", "bounds", "unknowns"),
    "survey": ("constrain_ref", "sought", "holdings", "absences", "unknowns"),
    "decompose": ("survey_ref", "sub_problems", "unknowns"),
    "triage": ("decompose_ref", "order", "unknowns"),
    "hypothesize": ("triage_ref", "hypotheses", "unknowns"),
    "validate": ("hypothesize_ref", "criteria", "unknowns"),
}

PASS = 0
FAIL = 0


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:  # noqa: BLE001 — a proof reports, never hides
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
    else:
        PASS += 1
        print(f"  green {name}")


def _rel(path) -> str:
    p = Path(path)
    return str(p.relative_to(_REPO_ROOT)) if p.is_absolute() else str(p)


def nothing_reaches_codemother_for_the_contract():
    rows = _inspector.encapsulation_breaches(str(_REPO_ROOT))
    into_verdict = [b for b in rows
                    if str(b["target"]).startswith(VERDICT_DIR) and _rel(b["file"]) != DEPOSIT_CALLER]
    from_dial = [b for b in rows
                 if _rel(b["file"]) == DIAL and str(b["target"]).startswith("cairn/devices/codemother")]
    bad = into_verdict + from_dial
    assert not bad, f"{len(bad)} reach(es) into codemother for the chart contract: " + \
        "; ".join(f"{_rel(b['file'])}:{b['line']} -> {b['module']}" for b in bad[:10])


def the_contract_stands_in_the_chain_tool():
    charter = json.loads((CHAIN_DIR / ("intention+" + "why.json")).read_text())
    declared = charter.get("public_interface") or []
    assert CONTRACT in declared, f"the chain charter does not declare {CONTRACT}: {declared}"
    src = CHAIN_DIR / "verdict_contract.py"
    assert src.is_file(), f"{_rel(src)} does not exist"
    reaches = []
    for node in ast.walk(ast.parse(src.read_text(encoding="utf-8"))):
        mods = ([a.name for a in node.names] if isinstance(node, ast.Import)
                else [node.module or ""] if isinstance(node, ast.ImportFrom) else [])
        reaches += [m for m in mods if m.startswith("cairn.devices")]
    assert not reaches, f"the chain tool's contract imports device code: {reaches}"
    import importlib
    mod = importlib.import_module(CONTRACT)
    missing = [n for n in MOVED if not hasattr(mod, n)]
    missing += [n for n in CALLABLE if hasattr(mod, n) and not callable(getattr(mod, n))]
    assert not missing, f"{CONTRACT} does not expose {missing}"
    grammar = importlib.import_module("cairn.tools.chain.grammar")
    want = os.path.join(os.path.dirname(grammar.INSTANCE_DIR), "verdict-deposits.jsonl")
    assert mod.LEDGER_PATH == want, f"the ledger moved: {mod.LEDGER_PATH} != {want}"


def _defined_and_imported(path: Path):
    tree = ast.parse(path.read_text(encoding="utf-8"))
    defined, imported = set(), {}
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            defined.add(node.name)
        elif isinstance(node, ast.Assign):
            defined.update(t.id for t in node.targets if isinstance(t, ast.Name))
        elif isinstance(node, ast.ImportFrom):
            for a in node.names:
                imported[a.asname or a.name] = node.module
    return tree, defined, imported


def codemother_binds_the_same_objects():
    _tree, defined, imported = _defined_and_imported(MACHINES / "verdict" / "verdict.py")
    own = sorted(n for n in MOVED if n in defined)
    assert not own, f"verdict.py still defines {own} — two copies of the contract drift"
    unbound = sorted(n for n in MOVED if imported.get(n) != CONTRACT)
    assert not unbound, f"verdict.py does not import {unbound} from {CONTRACT}"
    import importlib
    grammar = importlib.import_module("cairn.tools.chain.grammar")
    table = getattr(grammar, "STAGE_AUTHORED_FIELDS", None)
    assert table == STAGES, f"STAGE_AUTHORED_FIELDS is {table!r}, not the seven stages' fields"
    wrong = []
    for stage in STAGES:
        tree, _d, imp = _defined_and_imported(MACHINES / stage / f"{stage}.py")
        binding = [n.value for n in tree.body if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == "AUTHORED_FIELDS" for t in n.targets)]
        ok = (len(binding) == 1 and isinstance(binding[0], ast.Subscript)
              and isinstance(binding[0].value, ast.Name)
              and binding[0].value.id == "STAGE_AUTHORED_FIELDS"
              and isinstance(binding[0].slice, ast.Constant) and binding[0].slice.value == stage
              and imp.get("STAGE_AUTHORED_FIELDS") == "cairn.tools.chain.grammar")
        if not ok:
            wrong.append(stage)
    assert not wrong, f"these machines do not bind AUTHORED_FIELDS = STAGE_AUTHORED_FIELDS[stage]: {wrong}"


TEETH = [nothing_reaches_codemother_for_the_contract, the_contract_stands_in_the_chain_tool,
         codemother_binds_the_same_objects]

if __name__ == "__main__":
    for fn in TEETH:
        _tooth(fn.__name__, fn)
    print(f"{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
