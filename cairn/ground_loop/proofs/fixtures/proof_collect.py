"""The proof that puts `collect` in proven-space (Law 8): a hollow method couldn't pass it.

The method-registry runs THIS under the tester before admitting `collect`; the ground_loop
resolves `collect` only because this exits 0. Change `collect` and this reds — the method
falls out of proven-space and the ground_loop refuses to wire it.

    python3 .../fixtures/proof_collect.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.ground_loop.proofs.fixtures.collect import collect


def _main() -> int:
    assert collect() == {"value": "42"}, "collect must return its pinned reading"
    print("green — collect() reads its pinned value")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
