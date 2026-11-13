"""Proof for ticket 74b4209b71ee — the no-hand-drop tooth asks what a leak is made of, not what it says.

Measured 2026-11-12: 201a37bf1613's tooth 4 was a text grep for the leak's two spellings, and it
redded test_an_owned_index_is_owner_gated.py for an SQL-injection payload — a string handed to
store.add_owned_index, a mention, not a hand drop. The tooth now asks the AST
(``_hand_leaks`` in test_scratch_cannot_outlive_its_process.py). Four teeth, one per clause:

(1) a source that mentions DROP TABLE only inside a string handed to a non-execute call — and in
    a docstring, and in an ``_NONCE`` that is read, never assigned — yields no offence;
(2) ``cur.execute(f"DROP TABLE IF EXISTS {t}")`` yields an offence naming its line, as does the
    same SQL through ``executemany`` and spelled in lower case;
(3) ``_NONCE = os.getpid()`` yields an offence naming its line, annotated or not;
(4) the whole cairn/**/proofs/*.py corpus yields no offence.

A hollow build could not pass: the text grep reds tooth 1 (the fixture says DROP TABLE), and a
predicate that catches nothing reds teeth 2 and 3, whose expected lines are exact.

    PYTHONPATH=. python3 cairn/devices/db_domain/proofs/test_a_mention_is_not_a_hand_drop.py
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PROVES = {"74b4209b71ee": {
    "1": "test_a_mention_yields_no_offence",
    "2": "test_an_executed_drop_is_caught_at_its_line",
    "3": "test_a_minted_nonce_is_caught_at_its_line",
    "4": "test_the_proofs_corpus_yields_no_offence",
}}

_TOOTH = Path(__file__).with_name("test_scratch_cannot_outlive_its_process.py")


def _predicate():
    spec = importlib.util.spec_from_file_location("db_domain_scratch_tooth_under_proof", _TOOTH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod._hand_leaks


def test_a_mention_yields_no_offence() -> None:
    src = (
        '"""A docstring that says DROP TABLE cairn_x."""\n'
        't = "cairn_x"\n'
        'store.add_owned_index(t, "o", "b", ["x) ; DROP TABLE " + t + " ; --"])\n'
        'log("refusing DROP TABLE " + t)\n'
        'print(_NONCE)\n'
        'cur.execute("SELECT 1")\n'
    )
    hits = _predicate()(src)
    assert hits == [], f"a mention became a catch: {hits}"
    print("ok test_a_mention_yields_no_offence")


def test_an_executed_drop_is_caught_at_its_line() -> None:
    src = (
        'import os\n'
        'cur.execute(f"DROP TABLE IF EXISTS {t}")\n'
        'cur.executemany("drop   table " + t, [])\n'
    )
    hits = _predicate()(src)
    assert hits == ["execute DROP TABLE @ 2", "execute DROP TABLE @ 3"], f"hand drops missed: {hits}"
    print("ok test_an_executed_drop_is_caught_at_its_line")


def test_a_minted_nonce_is_caught_at_its_line() -> None:
    src = (
        'import os\n'
        '_NONCE = os.getpid()\n'
        '_NONCE: int = 7\n'
    )
    hits = _predicate()(src)
    assert hits == ["_NONCE assigned @ 2", "_NONCE assigned @ 3"], f"hand nonces missed: {hits}"
    print("ok test_a_minted_nonce_is_caught_at_its_line")


def test_the_proofs_corpus_yields_no_offence() -> None:
    leaks = _predicate()
    offenders = {}
    paths = sorted((ROOT / "cairn").rglob("proofs/*.py"))
    for path in paths:
        hits = leaks(path.read_text(encoding="utf-8", errors="replace"))
        if hits:
            offenders[str(path.relative_to(ROOT))] = hits
    assert paths, "no proofs found — the corpus tooth measured nothing"
    assert not offenders, f"proofs that drop a table or mint a nonce by hand: {offenders}"
    print(f"ok test_the_proofs_corpus_yields_no_offence ({len(paths)} proofs read)")


if __name__ == "__main__":
    from cairn.tools.proof_coverage.proof_coverage import print_teeth_main
    raise SystemExit(print_teeth_main(__file__))
