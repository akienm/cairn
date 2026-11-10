"""test_codemother declares its budget (ticket c42e4e436d6c) — teeth a hollow build could not pass.

Measured 2026-11-09: cairn/devices/codemother/proofs/test_codemother.py runs 169 s and the
tester's default budget is 120 s, so every reseal of it timed out and stood as a trouble.
A proof names its own budget with PROOF_TIMEOUT_S (ticket 8383a32d20c5). These teeth read the
declaration with ast; they import nothing of the tester.
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]

PROVES = {
    "c42e4e436d6c": {
        "1": "test_the_proof_declares_an_integer_budget",
        "2": "test_the_budget_fits_the_measured_run",
    },
}

_PROOF = _REPO_ROOT / "cairn" / "devices" / "codemother" / "proofs" / "test_codemother.py"
_MEASURED_S = 169


def _declared():
    tree = ast.parse(_PROOF.read_text(encoding="utf-8"), filename=str(_PROOF))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
                isinstance(t, ast.Name) and t.id == "PROOF_TIMEOUT_S" for t in node.targets):
            return node.value
    return None


def test_the_proof_declares_an_integer_budget():
    v = _declared()
    assert v is not None, "test_codemother.py assigns no module-level PROOF_TIMEOUT_S"
    assert isinstance(v, ast.Constant) and type(v.value) is int, f"PROOF_TIMEOUT_S is {ast.dump(v)}"


def test_the_budget_fits_the_measured_run():
    v = _declared()
    assert v is not None, "test_codemother.py assigns no module-level PROOF_TIMEOUT_S"
    n = getattr(v, "value", None)
    assert isinstance(n, int) and 2 * _MEASURED_S <= n <= 3600, f"PROOF_TIMEOUT_S = {n}"


if __name__ == "__main__":
    failed = 0
    for _name, _fn in list(globals().items()):
        if _name.startswith("test_") and callable(_fn):
            try:
                _fn()
                print(f"PASS {_name}")
            except BaseException as exc:  # noqa: BLE001 — every tooth reports, red or raising
                failed += 1
                print(f"FAIL {_name}: {type(exc).__name__}: {str(exc)[:300]}")
    sys.exit(1 if failed else 0)
