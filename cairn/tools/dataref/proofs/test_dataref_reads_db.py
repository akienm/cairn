"""Proof: a dataref reads a db: address through db_domain's client, and caches nothing.

Ticket eb16737ff959 (outline 17.28.1.1, 17.28.1.4, 17.28.3, 17.28.4, 17.28.5). Measured 2026-11-10:
dataref.py refused every db: address as not built, so the outline's own example
secret:db:///cairn/t/row#token raised. Every tooth reads one scratch table minted through
store.scratch (dropped on exit, swept by pid if not); no live row is read.

  1. db:///cairn/<table>/<key>#<column> gives the column as text (text as written, an integer as
     its digits); no # gives the whole row as a json object.
  2. #<column>/a/b walks into a json column, a list index included.
  3. a Secret over a db: address shows stars in str, repr and an f-string, and .secret is the
     value; after the row is updated the next .secret and the next Dataref .value read the new one.
  4. a missing row, column or table, a database other than cairn, a NULL column, an address with
     no row, and one naming a host each raise DatarefMiss naming the address, with no value from
     the table in the message and no chained exception.
  5. dataref.py imports no database driver and no socket: its only way to Postgres is
     cairn.devices.db_domain.tools.client.store.

    python3 cairn/tools/dataref/proofs/test_dataref_reads_db.py
"""
from __future__ import annotations

import ast
import json
import secrets
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {"eb16737ff959": {
    "1": "a_column_reads_as_text",
    "2": "a_json_column_is_walked",
    "3": "a_secret_masks_and_reads_fresh",
    "4": "a_miss_names_its_address",
    "5": "the_only_way_in_is_the_client",
}}
DR = REPO / "cairn/tools/dataref/dataref.py"
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str) -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + ("" if ok else f"\n        {detail[:1200]}"), flush=True)
    if not ok:
        FAILURES.append(name)


def guarded(name, fn, *a) -> None:
    try:
        fn(*a)
    except Exception as e:  # noqa: BLE001 — a tooth reds by name, whatever broke it
        check(name, False, f"{type(e).__name__}: {e}")


def a_column_reads_as_text(t: str, token: str) -> None:
    from cairn.tools.dataref import ref
    base = f"db:///cairn/{t}/row1"
    tok, n, whole = ref(base + "#token").value, ref(base + "#n").value, ref(base).value
    row = json.loads(whole)
    ok = tok == token and n == "42" and row.get("id") == "row1" and row.get("token") == token and row.get("n") == 42
    check("a_column_reads_as_text", ok, f"token_ok={tok == token} n={n!r} row_keys={sorted(row)}")


def a_json_column_is_walked(t: str, token: str) -> None:
    from cairn.tools.dataref import ref
    base = f"db:///cairn/{t}/row1#j"
    deep, idx, sub = ref(base + "/a/b").value, ref(base + "/list/1").value, json.loads(ref(base + "/a").value)
    check("a_json_column_is_walked", deep == "deep" and idx == "y" and sub == {"b": "deep"},
          f"deep={deep!r} idx={idx!r} sub={sub!r}")


def a_secret_masks_and_reads_fresh(t: str, token: str) -> None:
    from cairn.devices.db_domain.tools.client import store
    from cairn.tools.dataref import MASK, Dataref, Secret, ref
    addr = f"secret:db:///cairn/{t}/row1#token"
    s = ref(addr)
    shown = [str(s), repr(s), f"{s}", f"{s:>20}"]
    leaked = [x for x in shown if token in x]
    first = s.secret
    d = Dataref(f"db:///cairn/{t}/row1#token")
    before = d.value
    fresh = secrets.token_hex(8)
    store.update(t, "dataref", {"token": fresh}, where="id = %s", params=("row1",))
    after_s, after_d = s.secret, d.value
    ok = (isinstance(s, Secret) and not leaked and MASK in str(s) and first == token and before == token
          and after_s == fresh and after_d == fresh)
    check("a_secret_masks_and_reads_fresh", ok,
          f"secret={isinstance(s, Secret)} leaked={len(leaked)} first_ok={first == token} "
          f"before_ok={before == token} after_secret_fresh={after_s == fresh} after_dataref_fresh={after_d == fresh}")
    store.update(t, "dataref", {"token": token}, where="id = %s", params=("row1",))


def a_miss_names_its_address(t: str, token: str) -> None:
    from cairn.tools.dataref import DatarefMiss, ref
    cases = {
        "missing row": f"db:///cairn/{t}/nope#token",
        "missing column": f"secret:db:///cairn/{t}/row1#nocolumn",
        "missing table": "db:///cairn/no_such_table_eb16737ff959/row1#token",
        "other database": f"db:///postgres/{t}/row1#token",
        "null column": f"db:///cairn/{t}/row1#gone",
        "no row": f"db:///cairn/{t}",
        "host": f"db://akiendell/cairn/{t}/row1#token",
    }
    bad = {}
    for name, addr in cases.items():
        try:
            r = ref(addr)
            _ = r.secret if hasattr(r, "secret") else r.value
            bad[name] = "did not raise"
        except DatarefMiss as e:
            msg = str(e)
            chained = e.__cause__ or (None if e.__suppress_context__ else e.__context__)
            if addr not in msg or token in msg or chained is not None:
                bad[name] = f"named={addr in msg} leaked={token in msg} chained={type(chained).__name__ if chained else None}"
        except Exception as e:  # noqa: BLE001
            bad[name] = f"raised {type(e).__name__}, not DatarefMiss"
    check("a_miss_names_its_address", not bad, f"{bad}")


def the_only_way_in_is_the_client() -> None:
    tree = ast.parse(DR.read_text(encoding="utf-8"))
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods |= {a.name for a in node.names}
        elif isinstance(node, ast.ImportFrom) and node.module:
            mods.add(node.module)
    banned = {m for m in mods if m.split(".")[0] in {"psycopg2", "psycopg", "asyncpg", "socket", "pg8000", "sqlalchemy"}}
    reaches = any(m.startswith("cairn.devices.db_domain.tools.client") for m in mods)
    check("the_only_way_in_is_the_client", not banned and reaches, f"banned={sorted(banned)} reaches_client={reaches}")


def main() -> int:
    from cairn.devices.db_domain.tools.client import store
    token = secrets.token_hex(12)
    cols = {"id": "TEXT PRIMARY KEY", "token": "TEXT", "n": "INTEGER", "j": "JSONB", "gone": "TEXT"}
    with store.scratch("dataref", "dataref_db", cols) as t:
        store.write(t, "dataref", {"id": "row1", "token": token, "n": 42,
                                   "j": json.dumps({"a": {"b": "deep"}, "list": ["x", "y"]}), "gone": None})
        for name in list(PROVES["eb16737ff959"].values())[:4]:
            guarded(name, globals()[name], t, token)
    guarded("the_only_way_in_is_the_client", the_only_way_in_is_the_client)
    if FAILURES:
        print(f"RED: {len(FAILURES)} tooth/teeth failed: {FAILURES}")
        return 1
    print("GREEN: every tooth passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
