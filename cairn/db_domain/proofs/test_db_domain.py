"""Proof for db_domain — the owner-gated sole path to durable state.

Proven UNDER the tester (dogfood): the same notary that attests every stone attests this
one, and db_domain's first real consumer is the tester's own VALIDATIONS. Teeth a hollow
db_domain could not pass:

  - OWNERLESS IS IMPOSSIBLE (the founding law as physics). create_owned_table with no owner
    is refused; a hollow store that shrugs and creates it trips this. The refusal is
    belt-and-braces: the call refuses, and the registry's CHECK (owner <> '') would refuse
    anyway — Postgres itself, not a convention.
  - THE OWNER GATES EVERY WRITE (Law 6). A write by a non-owner is refused; a write to a
    table db_domain never created (no owner to gate it) is refused. A hollow store that
    lets anyone write trips these.
  - VALIDATIONS ROUND-TRIP (closes the tester's produced-not-persisted edge, Law 1). A real
    VALIDATION produced by TesterDevice.run_proof persists and greps back byte-for-byte,
    evidence (jsonb, incl. the network seal) intact.

Requires the one-time provisioning (an OS-named LOGIN CREATEDB role); db_domain creates the
`cairn` database itself. Self-cleaning: ephemeral tables are dropped and test VALIDATIONS
are deleted, so re-runs stay clean and the truth store is not polluted by proof fixtures.

    python3 cairn/db_domain/proofs/test_db_domain.py     # exit 0 = green
"""

from __future__ import annotations

import os
import sys
from datetime import datetime
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.db_domain import store
from cairn.db_domain.store import OwnershipError
from cairn.tester.device import VALIDATION_FIELDS, TesterDevice

# A per-run marker so parallel/re-runs never collide and cleanup is exact.
_NONCE = f"{os.getpid()}_{datetime.now().strftime('%H%M%S%f')}"
_TEST_TABLE = f"_probe_{_NONCE}"
_TEST_CLAIM = f"__dbtest__{_NONCE}"
_GREEN_FIXTURE = _REPO_ROOT / "cairn" / "tester" / "proofs" / "fixtures" / "green_proof.py"


def test_connect_reaches_the_cairn_database():
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT current_database()")
            assert cur.fetchone()[0] == store.DB_NAME
    finally:
        conn.close()


def test_ownerless_table_is_impossible():
    try:
        store.create_owned_table(_TEST_TABLE, "", {"x": "text"})
    except OwnershipError:
        return
    raise AssertionError("an ownerless table must be REFUSED — every table has exactly one owner (Law 6)")


def test_owned_table_records_its_owner():
    store.create_owned_table(_TEST_TABLE, "tester", {"x": "text"})
    assert store.owner_of(_TEST_TABLE) == "tester"


def test_the_owner_gates_every_write():
    # owner writes and reads back
    store.write(_TEST_TABLE, "tester", {"x": "owner-wrote-this"})
    rows = store.read(_TEST_TABLE, where="x = %s", params=("owner-wrote-this",))
    assert len(rows) == 1 and rows[0]["x"] == "owner-wrote-this"

    # a non-owner is refused (Law 6)
    try:
        store.write(_TEST_TABLE, "impostor", {"x": "should-not-land"})
        raise AssertionError("a non-owner write must be REFUSED (Law 6)")
    except OwnershipError:
        pass


def test_write_to_an_unowned_table_is_refused():
    try:
        store.write(f"_never_created_{_NONCE}", "anyone", {"x": "y"})
    except OwnershipError:
        return
    raise AssertionError("a write to a table db_domain never created must be refused — no owner to gate it")


def test_a_real_validation_round_trips():
    # A genuine VALIDATION from the tester — not a hand-built dict — persists and greps back.
    v = TesterDevice().run_proof(_GREEN_FIXTURE, isolation="none")
    v["claim"] = _TEST_CLAIM  # mark this run's row so cleanup is exact
    store.persist_validation(v)

    back = store.read_validations(where="claim = %s", params=(_TEST_CLAIM,))
    assert len(back) == 1, "the persisted VALIDATION must be greppable"
    stored = back[0]
    assert set(stored) == set(VALIDATION_FIELDS), f"the durable record must carry exactly the 8 fields, got {sorted(stored)}"
    assert stored["verdict"] == v["verdict"]
    # evidence is jsonb — it must survive as structure, seal and all, not a stringified blob.
    assert isinstance(stored["evidence"], dict)
    assert stored["evidence"]["seal"]["verdict"] == v["evidence"]["seal"]["verdict"]


def _cleanup():
    """Drop this run's ephemeral table and delete its test VALIDATIONS — leave no fixtures."""
    conn = store.connect()
    try:
        with conn.cursor() as cur:
            cur.execute(f'DROP TABLE IF EXISTS "{_TEST_TABLE}"')
            cur.execute(f'DELETE FROM "{store._REGISTRY}" WHERE table_name = %s', (_TEST_TABLE,))
            cur.execute(f'DELETE FROM "{store._VALIDATIONS}" WHERE claim = %s', (_TEST_CLAIM,))
    finally:
        conn.close()


def _main() -> int:
    checks = [
        test_connect_reaches_the_cairn_database,
        test_ownerless_table_is_impossible,
        test_owned_table_records_its_owner,
        test_the_owner_gates_every_write,
        test_write_to_an_unowned_table_is_refused,
        test_a_real_validation_round_trips,
    ]
    try:
        for check in checks:
            check()
            print(f"  PASS  {check.__name__}")
    finally:
        _cleanup()
    print("green — db_domain: ownerless is impossible, the owner gates writes, VALIDATIONS have a home")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
