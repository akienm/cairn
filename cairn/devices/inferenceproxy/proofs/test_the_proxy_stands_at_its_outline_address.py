"""Proof for ticket f942a413f26d — the inference proxy stands at its outline address in both roots.

Outline 11.4 names the device's folder ``cairn/devices/inferenceproxy/`` and 11.4.2 the name it
answers to on the command line and bus, ``inference``. Measured 2026-11-13: the folder was
``inference_domain/`` and the old name was the device's live identity in six places. The code
moved in git (D1, D2); instance-space moves by the recipe ``rename_instance.py`` (D4), which its
holder runs on each box in the same act as the restart.

One tooth per numbered falsifier clause:

  1. No tracked code under cairn/, skills/ or bin/ names the old name, outside the recipe's
     old-name constants, the append-only and compiled records (history, state, validations,
     journals, the dated judgments) and this file. The charter declares ``answers_as``
     ``inference``, the shim's device_id is ``inference``, the rack's address book resolves
     ``inference`` to this folder's shim, and bin/cairn maps a typed ``answers_as`` to the folder.
  2. Every other proof under cairn/devices/inferenceproxy/ is green, each run as its own process.
  3. Over a scratch HOME, apply moves the devices and logs dirs (merging into a standing target
     without dropping a byte), a second apply changes nothing, and verify is red before and
     green after.
  4. Over testing-named tables, the table step renames the table, its two indexes and its
     registry row (new name, new owner), keeps every row, a second run changes nothing, and a
     testing metric table holding rows under the old source is byte-for-byte untouched.

Requires the db_domain provisioning for tooth 4; every table it makes is testing-named and
dropped in a finally. Tooth 2 runs the siblings with CAIRN_F942_INNER=1 so a sibling that runs
this file back (98ab0e9db57f's tooth 9 runs every sibling) does not run them all again.

    bin/cairn test cairn/devices/inferenceproxy/proofs/test_the_proxy_stands_at_its_outline_address.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

PROOF_TIMEOUT_S = 3600

PROVES = {"f942a413f26d": {
    "1": "no_live_code_names_the_old_name_and_it_answers_as_inference",
    "2": "every_other_proof_under_the_device_is_green",
    "3": "the_recipe_moves_instance_space_once",
    "4": "the_recipe_renames_the_table_and_its_row_and_not_the_metrics",
}}

DEVICE = _REPO / "cairn" / "devices" / "inferenceproxy"
OLD = "inference" + "_domain"          # spelled split: tooth 1 greps the tree this file is in
_RECORDS = re.compile(r"(history\.json|state\.json|/validations/[^/]*\.json|\.jsonl|"
                      r"dated_append_judgments\.json)$")
_ALLOWED = {"cairn/devices/inferenceproxy/rename_instance.py",
            "cairn/devices/inferenceproxy/proofs/test_the_proxy_stands_at_its_outline_address.py"}
INNER = "CAIRN_F942_INNER"

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _recipe():
    from cairn.devices.inferenceproxy import rename_instance
    return rename_instance


# ── 1 ────────────────────────────────────────────────────────────────────────

def no_live_code_names_the_old_name_and_it_answers_as_inference() -> None:
    listed = subprocess.run(["git", "-C", str(_REPO), "ls-files", "-co", "--exclude-standard",
                             "--", "cairn", "skills", "bin"], capture_output=True, text=True,
                            check=True).stdout.split("\n")
    named = []
    for rel in filter(None, listed):
        if rel in _ALLOWED or _RECORDS.search(rel) or "__pycache__" in rel:
            continue
        p = _REPO / rel
        try:
            if p.is_file() and OLD in p.read_text(encoding="utf-8"):
                named.append(rel)
        except UnicodeDecodeError:
            continue
    recipe_code = (DEVICE / "rename_instance.py").read_text(encoding="utf-8").split('"""', 2)[2]
    code_lines = [ln for ln in recipe_code.splitlines() if OLD in ln and not ln.lstrip().startswith("#")
                  and not ln.startswith(("OLD = ", "TABLES = ", "MERGED_SUFFIX = "))]
    check("no tracked code names the old name", not named, f"{len(named)}: {named[:10]}")
    check("the recipe names it only in its constants and its docstring", not code_lines,
          f"{code_lines[:5]}")

    charter = json.loads((DEVICE / "intention+why.json").read_text(encoding="utf-8"))
    check("the charter declares answers_as inference", charter.get("answers_as") == "inference",
          repr(charter.get("answers_as")))
    src = (DEVICE / "shim.py").read_text(encoding="utf-8")
    m = re.search(r"def device_id\(self\)[^:]*:\s*return \"([^\"]+)\"", src)
    sid = m.group(1) if m else None
    check("the shim's device_id is inference", sid == "inference", repr(sid))
    from cairn.tools.rack import rack
    found = rack.shim_of("inference")
    check("the rack resolves inference to this folder's shim",
          found is not None and Path(found).resolve() == (DEVICE / "shim.py").resolve(), str(found))
    check("the rack's folder_of names inferenceproxy",
          getattr(rack.folder_of("inference"), "name", None) == "inferenceproxy",
          str(rack.folder_of("inference")))
    cli = (_REPO / "bin" / "cairn").read_text(encoding="utf-8")
    check("bin/cairn maps a typed answers_as to its folder",
          '\\"answers_as\\": \\"$device\\"' in cli and 'device="$(basename "$(dirname "$_charter")")"' in cli
          and '"$CAIRN_BUS_MOUTH" "$bus_name"' in cli, "the answers_as block or the bus_name hand-off is absent")
    check("no folder stands at the old address", not (_REPO / "cairn" / "devices" / OLD).exists())


# ── 2 ────────────────────────────────────────────────────────────────────────

def every_other_proof_under_the_device_is_green() -> None:
    if os.environ.get(INNER):
        print("  PASS  inner run — the outer run judges the siblings")
        return
    here = Path(__file__).resolve()
    env = dict(os.environ, **{INNER: "1"})
    red = {}
    n = 0
    for p in sorted(DEVICE.rglob("proofs/test_*.py")):
        if p.resolve() == here:
            continue
        n += 1
        r = subprocess.run([sys.executable, str(p)], cwd=str(_REPO), capture_output=True, text=True,
                           timeout=1800, env=env, stdin=subprocess.DEVNULL)
        if r.returncode != 0:
            red[p.relative_to(DEVICE).as_posix()] = (r.stdout + r.stderr).strip().splitlines()[-3:]
    check(f"every other proof under the device is green ({n} run)", not red, f"{len(red)} red: {red}")


# ── 3 ────────────────────────────────────────────────────────────────────────

def _tree(root: Path) -> dict[str, bytes]:
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in sorted(root.rglob("*")) if p.is_file()}


def the_recipe_moves_instance_space_once() -> None:
    from cairn.tools.scratch.scratch import scratch_dir
    rec = _recipe()
    home = scratch_dir("testing_f942_home")
    cairn = home / ".cairn"
    (cairn / "devices" / OLD / "0" / "bin").mkdir(parents=True)
    (cairn / "devices" / OLD / "0" / "bin" / "launcher").write_text("old launcher\n")
    (cairn / "devices" / OLD / "0" / "overlay.json").write_text('{"old": true}\n')
    (cairn / "logs" / OLD / "0").mkdir(parents=True)
    (cairn / "logs" / OLD / "0" / "a.log").write_text("old log\n")
    # a target that already stands (the restarted device wrote one line before the recipe ran)
    (cairn / "logs" / "inferenceproxy" / "0").mkdir(parents=True)
    (cairn / "logs" / "inferenceproxy" / "0" / "a.log").write_text("new log\n")
    (cairn / "logs" / "inferenceproxy" / "0" / "b.log").write_text("only new\n")

    before = rec.verify(home, tables=())
    check("verify is red before apply", len(before) == 2, f"{before}")
    first = rec.apply_dirs(home)
    dev = _tree(cairn / "devices" / "inferenceproxy")
    logs = _tree(cairn / "logs" / "inferenceproxy")
    check("apply moves the devices dir", dev == {"0/bin/launcher": b"old launcher\n",
                                                  "0/overlay.json": b'{"old": true}\n'}, f"{dev}")
    check("apply merges the logs dir without dropping a byte",
          logs == {"0/a.log": b"new log\n", "0/a.log.from-inference_domain": b"old log\n",
                   "0/b.log": b"only new\n"}, f"{logs}")
    check("no old dir stands", not (cairn / "devices" / OLD).exists() and not (cairn / "logs" / OLD).exists())
    second = rec.apply_dirs(home)
    check("a second apply changes nothing", second == [] and _tree(cairn / "logs" / "inferenceproxy") == logs
          and _tree(cairn / "devices" / "inferenceproxy") == dev, f"{second}")
    after = rec.verify(home, tables=())
    check("verify is green after apply", after == [] and len(first) == 2, f"after={after} first={first}")


# ── 4 ────────────────────────────────────────────────────────────────────────

def the_recipe_renames_the_table_and_its_row_and_not_the_metrics() -> None:
    from cairn.devices.db_domain.tools.client import store
    rec = _recipe()
    tag = f"{os.getpid()}"
    old_t, new_t = f"testing_f942_{tag}_old_nodes", f"testing_f942_{tag}_new_nodes"
    metric_t = f"testing_f942_{tag}_metrics"
    old_o, new_o = "testing_f942_old", "testing_f942_new"
    conn = store.connect()
    made = []
    try:
        store.create_owned_table(old_t, old_o, {"leaf_id": "text PRIMARY KEY", "key": "text"}, conn=conn)
        made.append((old_t, old_o))
        store.add_owned_index(old_t, old_o, f"{old_t}_key", ["key"], conn=conn)
        for i in range(3):
            store.write(old_t, old_o, {"leaf_id": f"l{i}", "key": f"k{i}"}, conn=conn)
        store.create_owned_table(metric_t, old_o, {"id": "text PRIMARY KEY", "source": "text"}, conn=conn)
        made.append((metric_t, old_o))
        for i in range(2):
            store.write(metric_t, old_o, {"id": f"m{i}", "source": OLD}, conn=conn)
        metrics_before = store.read(metric_t, conn=conn)

        pairs = ((old_t, new_t),)
        lacks_before = [x for x in rec.verify(Path("/nonexistent-f942"), tables=pairs, conn=conn)]
        check("verify names the old table and its row", lacks_before == [f"table {old_t} stands",
                                                                         f"registry row {old_t} stands"],
              f"{lacks_before}")
        done = rec.apply_tables(pairs, old_owner=old_o, new_owner=new_o, conn=conn)
        made.append((new_t, new_o))
        with conn.cursor() as cur:
            cur.execute("SELECT indexname FROM pg_indexes WHERE tablename = %s ORDER BY indexname", (new_t,))
            idx = [r[0] for r in cur.fetchall()]
        check("the table is renamed", store.owner_of(old_t, conn=conn) is None
              and store.owner_of(new_t, conn=conn) == new_o, f"{done}")
        check("its indexes are renamed", idx == [f"{new_t}_key", f"{new_t}_pkey"], f"{idx}")
        rows = sorted(r["leaf_id"] for r in store.read(new_t, conn=conn))
        check("every row is kept", rows == ["l0", "l1", "l2"], f"{rows}")
        again = rec.apply_tables(pairs, old_owner=old_o, new_owner=new_o, conn=conn)
        check("a second run changes nothing", again == [], f"{again}")
        lacks_after = rec.verify(Path("/nonexistent-f942"), tables=pairs, conn=conn)
        check("verify is green after", lacks_after == [], f"{lacks_after}")
        check("the metric rows under the old source are untouched",
              store.read(metric_t, conn=conn) == metrics_before, f"{metrics_before}")
        src = (DEVICE / "rename_instance.py").read_text(encoding="utf-8")
        code = "\n".join(ln for ln in src.split('"""', 2)[2].splitlines() if not ln.lstrip().startswith("#"))
        check("the recipe's code names no metric table", "metric" not in code.lower())

        both_o, both_n = f"testing_f942_{tag}_both_old", f"testing_f942_{tag}_both_new"
        store.create_owned_table(both_o, old_o, {"leaf_id": "text PRIMARY KEY", "key": "text"}, conn=conn)
        made.append((both_o, old_o))
        store.create_owned_table(both_n, new_o, {"leaf_id": "text PRIMARY KEY", "key": "text"}, conn=conn)
        made.append((both_n, new_o))
        for t, o, rows_in in ((both_o, old_o, (("l0", "old"), ("l1", "old"))),
                              (both_n, new_o, (("l1", "new"), ("l9", "new")))):
            for leaf, key in rows_in:
                store.write(t, o, {"leaf_id": leaf, "key": key}, conn=conn)
        both = ((both_o, both_n),)
        folded = rec.apply_tables(both, old_owner=old_o, new_owner=new_o, conn=conn)
        merged = sorted((r["leaf_id"], r["key"]) for r in store.read(both_n, conn=conn))
        check("when both stand, every row of both is kept and the old one's bytes win a shared leaf",
              merged == [("l0", "old"), ("l1", "old"), ("l9", "new")], f"{merged} {folded}")
        check("when both stand, one table and one registry row remain, under the new name and owner",
              store.owner_of(both_o, conn=conn) is None and store.owner_of(both_n, conn=conn) == new_o
              and rec.verify(Path("/nonexistent-f942"), tables=both, conn=conn) == [], f"{folded}")
    finally:
        for table, owner in made:
            try:
                store.drop_table(table, owner, conn=conn)
            except Exception as exc:  # noqa: BLE001 — loud, never hidden
                print(f"  cleanup: drop_table({table}) failed: {type(exc).__name__}: {exc}")
        conn.close()


TEETH = [no_live_code_names_the_old_name_and_it_answers_as_inference,
         every_other_proof_under_the_device_is_green,
         the_recipe_moves_instance_space_once,
         the_recipe_renames_the_table_and_its_row_and_not_the_metrics]


def main() -> int:
    for tooth in TEETH:
        before = len(FAILURES)
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            check(tooth.__name__, False, f"{type(exc).__name__}: {str(exc)[:300]}")
        print(f"  {'PASS' if len(FAILURES) == before else 'FAIL'}  {tooth.__name__}")
    print(f"{len(TEETH)} teeth, {len(FAILURES)} failed check(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
