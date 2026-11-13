"""Proof for ticket 46851816800f: a census names every reader outside our repos that reads a
record by its json name.

e78c9858f5fb's WRONG-INTENT clause rests on one measurement: does any code outside cairn and
CairnCommons read a record of truth by its .json name? This instrument takes it, per box.

1. a code file naming tickets/<x>.json in a scratch outside root is listed as a reader with its
   path and line;
2. a .md naming one is a mention, not a reader; a symlink resolving into an inside root, and a
   file inside the repos, are not counted;
3. every declared root reads scanned or absent; an absent root is reported, never skipped;
4. live over this box's declared roots the census completes, and every root reads scanned or
   absent (invariants only, never a count).

Clauses 1-3 run on scratch roots under a temp dir. Clause 4 reads the live roots, read-only.
``outside_readers`` is imported inside ``main``.

Run bare:  PYTHONPATH=. python3 cairn/tools/artifact/proofs/test_a_census_names_every_outside_reader.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "46851816800f": {
        "1": "a_planted_code_reader_is_listed_with_path_and_line",
        "2": "a_prose_mention_and_an_inside_link_are_not_readers",
        "3": "every_declared_root_reads_scanned_or_absent",
        "4": "the_live_census_completes_over_every_root",
    },
}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail:
        print(f"        {detail[:300]}")
    if not ok:
        FAILURES.append(name)


def main() -> int:
    from cairn.tools.artifact import outside_readers as O
    with tempfile.TemporaryDirectory(prefix="cairn-outside-readers-proof-") as d:
        base = Path(d)
        inside = base / "CairnCommons"
        (inside / "tickets").mkdir(parents=True)
        (inside / "tickets" / "abc.json").write_text("{}\n")
        (inside / "reader_inside.py").write_text("open('tickets/abc.json')\n")
        out = base / "outside"
        (out / "tools").mkdir(parents=True)
        (out / "tools" / "reader.py").write_text(
            "import json\n\nDOC = json.load(open('CairnCommons/tickets/abc123.json'))\n")
        (out / "notes.md").write_text("we once read tickets/abc123.json by hand\n")
        (out / "unrelated.py").write_text("print('nothing here')\n")
        (out / "link_in.py").symlink_to(inside / "reader_inside.py")
        (out / "dirlink").symlink_to(inside)
        missing = base / "no_such_root"

        r = O.census(roots=[out, missing], inside=[inside], with_crontab=False)
        readers = {(x["path"], x["line"]) for x in r["readers"]}
        want = (str(out / "tools" / "reader.py"), 3)
        check(PROVES["46851816800f"]["1"], want in readers, f"readers={sorted(readers)}")

        paths = {x["path"] for x in r["readers"]}
        mentions = {x["path"] for x in r["mentions"]}
        leaked = [p for p in paths | mentions
                  if "link_in" in p or "dirlink" in p or p.startswith(str(inside))]
        check(PROVES["46851816800f"]["2"],
              str(out / "notes.md") in mentions and str(out / "notes.md") not in paths
              and not leaked and str(out / "unrelated.py") not in paths,
              f"readers={sorted(paths)} mentions={sorted(mentions)} leaked={leaked}")

        status = {x["root"]: x["status"] for x in r["roots"]}
        check(PROVES["46851816800f"]["3"],
              status.get(str(out)) == "scanned" and status.get(str(missing)) == "absent"
              and len(r["roots"]) == 2,
              f"roots={r['roots']}")

    live = O.census()
    declared = {str(x["root"]) for x in O.default_roots()} | {"crontab"}
    got = {x["root"]: x["status"] for x in live["roots"]}
    insides = [str(p) for p in O.default_inside()]
    stray = [x["path"] for x in live["readers"] + live["mentions"]
             if any(x["path"].startswith(i + "/") for i in insides)]
    check(PROVES["46851816800f"]["4"],
          set(got) == declared and all(v in ("scanned", "absent") for v in got.values())
          and not stray
          and all({"path", "line", "text"} <= set(x) for x in live["readers"] + live["mentions"]),
          f"roots={got} stray={stray[:3]}")

    print(f"\n{len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
