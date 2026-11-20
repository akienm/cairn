"""Proof for ticket 19eb2d9211e9: the live census tooth names the conjunct that failed and its
entries.

Measured 2026-11-20 on akiendelllinux: the 6437cfd935bb build commit f8a4ab57f resealed
cairn/tools/artifact/proofs/test_a_census_names_every_outside_reader.py red on tooth 4 (rc=1,
killed=[], no timeout), and its FAIL detail was cut at 300 chars mid-root, so which of the four
conjuncts failed (declared root set, root status, stray inside path, row shape) is in no record.

1. the_fail_line_names_each_failed_conjunct_whole: tooth 4 driven over a census that breaks all
   four conjuncts, each with an entry longer than the old 300-char cut, prints FAIL with every
   conjunct's name and every offending entry in full;
2. a_dropped_root_reds_by_name_and_a_whole_census_greens: over a scratch census, tooth 4's
   predicate returns nothing for the census whole, and with one declared root dropped from its
   roots it returns the declared-root-set conjunct naming that root.

The census proof is loaded by path inside each tooth (what the build adds binds at call time);
every census here is scratch, under a temp dir. Nothing live is read.

    bin/cairn test cairn/tools/artifact/proofs/test_the_live_census_tooth_names_what_failed.py
"""
from __future__ import annotations

import contextlib
import importlib.util
import io
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "19eb2d9211e9": {
        "1": "the_fail_line_names_each_failed_conjunct_whole",
        "2": "a_dropped_root_reds_by_name_and_a_whole_census_greens",
    },
}

CENSUS_PROOF = Path(__file__).resolve().parent / "test_a_census_names_every_outside_reader.py"
CONJUNCTS = ("declared root set", "root status", "stray inside path", "row shape")
FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}")
    if detail and not ok:
        print(f"        {detail}")
    if not ok:
        FAILURES.append(name)


def _census_proof():
    spec = importlib.util.spec_from_file_location("_census_proof_19eb", CENSUS_PROOF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def the_fail_line_names_each_failed_conjunct_whole() -> tuple[bool, str]:
    P = _census_proof()
    long = "/var/tmp/testing-19eb-" + "x" * 400
    insides = ["/var/tmp/testing-19eb-inside"]
    live = {
        "roots": [{"root": long + "-scanned", "status": "scanned"},
                  {"root": long + "-odd", "status": "half-read"}],
        "readers": [{"path": insides[0] + "/" + "y" * 400 + ".py", "line": 1, "text": "t"}],
        "mentions": [{"path": long + "-shapeless.md", "line": 2}],
    }
    declared = {long + "-scanned", long + "-odd", long + "-declared-but-missing"}
    P.FAILURES.clear()
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        P.tooth_4(live, declared, insides)
    out = buf.getvalue()
    want = [long + "-declared-but-missing", long + "-odd", "half-read",
            insides[0] + "/" + "y" * 400 + ".py", long + "-shapeless.md"]
    missing_conj = [c for c in CONJUNCTS if c not in out]
    missing_entries = [w[-40:] for w in want if w not in out]
    ok = "FAIL" in out and not missing_conj and not missing_entries and P.FAILURES
    return bool(ok), f"conjuncts unnamed={missing_conj} entries cut={missing_entries} out={out[:600]!r}"


def a_dropped_root_reds_by_name_and_a_whole_census_greens() -> tuple[bool, str]:
    P = _census_proof()
    from cairn.tools.artifact import outside_readers as O
    with tempfile.TemporaryDirectory(prefix="testing-19eb-census-") as d:
        base = Path(d)
        inside = base / "CairnCommons"
        (inside / "tickets").mkdir(parents=True)
        a, b = base / "outside_a", base / "outside_b"
        for r in (a, b):
            (r / "tools").mkdir(parents=True)
        (a / "tools" / "reader.py").write_text("open('CairnCommons/tickets/abc123.json')\n")
        live = O.census(roots=[a, b], inside=[inside], with_crontab=False)
        declared = {str(a), str(b)}
        whole = P.live_census_failures(live, declared, [str(inside)])
        dropped = dict(live, roots=[x for x in live["roots"] if x["root"] != str(b)])
        fails = P.live_census_failures(dropped, declared, [str(inside)])
    named = [f for f in fails if f.get("conjunct") == "declared root set"
             and str(b) in repr(f.get("entries"))]
    ok = whole == [] and len(fails) == 1 and len(named) == 1
    return ok, f"whole={whole!r} dropped={fails!r}"


def main() -> int:
    for t in (the_fail_line_names_each_failed_conjunct_whole,
              a_dropped_root_reds_by_name_and_a_whole_census_greens):
        try:
            ok, detail = t()
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            ok, detail = False, f"{type(exc).__name__}: {exc}"
        check(t.__name__, ok, detail)
    print(f"\n{len(FAILURES)} failure(s)")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
