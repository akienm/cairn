"""Proof (0c2c trio item a): a proof that stands a fake in for ``remote._spawn`` gives it every keyword the real one takes.

0c2c3f53c2be (d839314f7) added ``env`` to ``remote._spawn`` and made ``ensure_bus`` pass ``env=env``. The one fake that
replaces ``_spawn`` with a named function, ``spawn`` in test_a_draining_bus_is_used_not_raced.py, kept the old signature
``(h, scratch, *, via_unit=True)``, so ``test_an_idle_replace_still_spawns`` raised ``TypeError: spawn() got an unexpected
keyword argument 'env'`` at remote.py:358, the ``_spawn(home, scratch, via_unit=beside, env=env)`` call. The fault is in
the FAKE, not in the bus. This tooth reads source only (ast), so it needs no bus, no socket and no OS feature: it finds
every function a bus_client proof assigns to ``remote._spawn`` and compares its parameters to the real signature.

    python <this file>
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
REMOTE = REPO / "cairn" / "tools" / "bus_client" / "remote.py"
PROOFS = REPO / "cairn" / "tools" / "bus_client" / "proofs"

PROVES = {
    "0c2c3f53c2be": {
        "1": "every_fake_standing_in_for_spawn_accepts_every_keyword_the_real_spawn_takes",
        "2": "the_tooth_finds_the_fake_it_is_about",
    },
}


def _real_keywords() -> set[str]:
    tree = ast.parse(REMOTE.read_text(encoding="utf-8"))
    fn = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_spawn")
    return {a.arg for a in fn.args.kwonlyargs}


def _fakes() -> list[tuple[Path, str, ast.FunctionDef]]:
    """(proof file, name, def) for each function a proof assigns to ``remote._spawn``."""
    found = []
    for path in sorted(PROOFS.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        defs = {n.name: n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)}
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            pairs = []
            for tgt in node.targets:
                if isinstance(tgt, ast.Tuple) and isinstance(node.value, ast.Tuple):
                    pairs += list(zip(tgt.elts, node.value.elts))
                else:
                    pairs.append((tgt, node.value))
            for tgt, val in pairs:
                if isinstance(tgt, ast.Attribute) and tgt.attr == "_spawn" and isinstance(val, ast.Name) and val.id in defs:
                    found.append((path, val.id, defs[val.id]))
    return found


def every_fake_standing_in_for_spawn_accepts_every_keyword_the_real_spawn_takes() -> None:
    real = _real_keywords()
    assert real, "found no keyword-only parameters on remote._spawn: the tooth would compare nothing"
    bad = []
    for path, name, fn in _fakes():
        if fn.args.kwarg is not None:
            continue
        have = {a.arg for a in fn.args.kwonlyargs} | {a.arg for a in fn.args.args}
        if missing := sorted(real - have):
            bad.append(f"{path.name}:{fn.lineno} {name}() lacks {missing}")
    assert not bad, "a fake _spawn does not accept what ensure_bus passes: " + "; ".join(bad)


def the_tooth_finds_the_fake_it_is_about() -> None:
    names = {(p.name, n) for p, n, _ in _fakes()}
    assert ("test_a_draining_bus_is_used_not_raced.py", "spawn") in names, f"the draining proof's fake was not found: {sorted(names)}"
    assert "env" in _real_keywords(), "remote._spawn no longer takes env: this proof's premise is gone"


TEETH = [every_fake_standing_in_for_spawn_accepts_every_keyword_the_real_spawn_takes, the_tooth_finds_the_fake_it_is_about]


def main() -> int:
    failed = 0
    for t in TEETH:
        try:
            t()
            print(f"  PASS  {t.__name__}")
        except BaseException as e:  # noqa: BLE001
            failed += 1
            print(f"  FAIL  {t.__name__}: {type(e).__name__}: {str(e)[:400]}")
    print(f"\n{len(TEETH) - failed}/{len(TEETH)} teeth green")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
