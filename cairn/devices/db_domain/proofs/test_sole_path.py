"""Proof for db_domain's FOURTH falsifier — the one that has never been enforced.

The charter says RED on "any module OTHER than db_domain opens a connection to 5432
(sole-path breached — enforced by the tester import-scan once that tooth exists)". The
tooth did not exist. From 2026-07-18 to 2026-08-06 the sole path to durable state was
sole BY CONSTRUCTION — which is a claim about the present that nothing re-checked, and
the difference between a rule and a habit (Law 4).

SEPARATE FROM test_db_domain.py ON PURPOSE. That proof needs a provisioned Postgres and a
LOGIN CREATEDB role; this one needs nothing but the tree. Folded in there, the sole-path
check would go unrun on exactly the machine where nobody had set the database up — and a
bare machine is where a second door is most likely to be built, because the first one does
not work yet.

    python3 cairn/devices/db_domain/proofs/test_sole_path.py     # exit 0 = green
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[4]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from cairn.tools.import_sieve import sieve

# The mesh: every way into a Postgres wire protocol that exists as an import. Named
# exactly, matched on the full dotted name, so a module that merely TALKS ABOUT 5432 in a
# docstring is not a door (learning_block learned that on its own docstring, 2026-08-01).
DRIVERS = ("psycopg2", "psycopg", "asyncpg", "pg8000", "sqlalchemy", "pymysql")

RULE = {"kind": "sole_path",
        "capability": "durable state at port 5432",
        "modules": DRIVERS,
        "only": "cairn/devices/db_domain/"}

SQLITE_DRIVERS = ("sqlite3",)

SQLITE_RULE = {"kind": "sole_path",
               "capability": "local relational state outside db_domain",
               "modules": SQLITE_DRIVERS,
               "only": "cairn/devices/db_domain/"}


def test_db_domain_is_the_only_module_that_can_reach_5432():
    caught = sieve.catches(sieve.import_graph(str(_REPO_ROOT)), RULE)
    assert caught == [], (
        "a SECOND module can open a database connection — Law 6's owner-gate is only a gate "
        "if there is one door, and the whole of db_domain's why rests on that. If the new "
        "importer is legitimate, it belongs inside cairn/devices/db_domain/ or in this rule WITH a "
        "reason, which is the conversation this red exists to force:\n  " + "\n  ".join(caught))


def test_the_tooth_reds_on_a_planted_second_door():
    """Non-vacuity. The tooth above passes over a clean corpus and would pass identically
    if the mesh caught nothing at all — so the same rule is shaken over a planted graph."""
    planted = {f"filler/m{i}.py": {"json"} for i in range(25)}
    planted["cairn/devices/librarian/store.py"] = sieve.imports_in("import psycopg2")
    planted["cairn/devices/db_domain/store.py"] = sieve.imports_in("import psycopg2")
    caught = sieve.catches(planted, RULE)
    assert len(caught) == 1, f"exactly the rogue, and db_domain itself spared: {caught}"
    assert "cairn/devices/librarian/store.py" in caught[0]
    assert "5432" in caught[0], "the refusal names the capability, not just the module"


def test_a_docstring_about_the_database_is_not_a_door():
    """The mesh tests capability, never mention — db_domain's own charter and store.py
    talk about 5432 at length, and prose cannot open a socket."""
    planted = {f"filler/m{i}.py": {"json"} for i in range(25)}
    planted["cairn/notes/why.py"] = sieve.imports_in(
        '"""The only path to 5432 is psycopg2 inside db_domain."""\nimport json\n')
    assert sieve.catches(planted, RULE) == [], "prose about the driver was read as a door"


def test_sqlite3_sole_path_is_clean_on_the_real_corpus():
    caught = sieve.catches(sieve.import_graph(str(_REPO_ROOT)), SQLITE_RULE)
    assert caught == [], (
        "a module outside db_domain imports sqlite3 — local relational state that bypasses "
        "the one door. If legitimate, it belongs inside cairn/devices/db_domain/ or this rule "
        "WITH a reason:\n  " + "\n  ".join(caught))


def test_sqlite3_sole_path_reds_on_a_planted_offender():
    planted = {f"filler/m{i}.py": {"json"} for i in range(25)}
    planted["cairn/devices/librarian/cache.py"] = sieve.imports_in("import sqlite3")
    planted["cairn/devices/db_domain/local.py"] = sieve.imports_in("import sqlite3")
    caught = sieve.catches(planted, SQLITE_RULE)
    assert len(caught) == 1, f"exactly the rogue, db_domain itself spared: {caught}"
    assert "cairn/devices/librarian/cache.py" in caught[0]


def _main() -> int:
    checks = [
        test_db_domain_is_the_only_module_that_can_reach_5432,
        test_the_tooth_reds_on_a_planted_second_door,
        test_a_docstring_about_the_database_is_not_a_door,
        test_sqlite3_sole_path_is_clean_on_the_real_corpus,
        test_sqlite3_sole_path_reds_on_a_planted_offender,
    ]
    for check in checks:
        check()
        print(f"  PASS  {check.__name__}")
    print("green — db_domain: the sole path to durable state (5432 + sqlite3) is measured, not assumed")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
