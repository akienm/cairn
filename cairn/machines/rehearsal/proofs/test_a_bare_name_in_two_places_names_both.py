"""Proof for ticket 6548996bd5c0 — WHAT EXISTS names every place a bare file name is found.

Measured 2026-11-09: rehearsal record CairnCommons/rehearsals/5183005fa134-20261109T221718.json
carries three gaps, each naming cairn/devices/cairn/machines/bus/__main__.py missing, and the file
exists. The rendered WHAT EXISTS said ``present path __main__.py (at
cairn/tools/bus_client/__main__.py)``: the base walk stopped at the first directory holding the
bare name, and bus_client's had been seen first. Outline 9.4.7.1: these records are a learner's
training data, so a false gap is a wrong label.

  1. a bare name found under two bases rides as ONE present entry naming both, in base order, and
     the printed line names both.
  2. a bare name found under exactly one base rides as before: ``at X``, no ``also``.
  3. rendering 5183005fa134 from the live commons (read only) names
     cairn/devices/cairn/machines/bus/__main__.py among __main__.py's locations.
  4. the rehearsal's own what-exists proof and its base proof stay green.

The machine is resolved at call time inside each tooth, so a reverted build reds teeth instead of
killing the import.

    python3 cairn/machines/rehearsal/proofs/test_a_bare_name_in_two_places_names_both.py
"""
from __future__ import annotations

import importlib
import shutil
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from cairn.tools.scratch.scratch import scratch_dir  # noqa: E402

PROVES = {
    "6548996bd5c0": {
        "1": "tooth_1_a_bare_name_in_two_places_names_both",
        "2": "tooth_2_a_bare_name_in_one_place_rides_as_before",
        "3": "tooth_3_the_bus_main_is_named_for_5183005fa134",
        "4": "tooth_4_the_standing_what_exists_proofs_stay_green",
    },
}
BUS_MAIN = "cairn/devices/cairn/machines/bus/__main__.py"
FAILURES: list[str] = []


def _R():
    return importlib.import_module("cairn.machines.rehearsal.rehearsal")


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if detail:
        print(f"        {detail[:900]}", flush=True)
    if not ok:
        FAILURES.append(name)


def _scratch():
    base = scratch_dir("rehearsal-bare-name-twice-")
    repo = base / "repo"
    for d in ("cairn/tools/a", "cairn/tools/b"):
        (repo / d).mkdir(parents=True)
        (repo / d / "x.py").write_text("")
    (repo / "cairn/tools/a/only.py").write_text("")
    (repo / "cairn/tools/a/m.py").write_text("")
    (repo / "cairn/tools/b/n.py").write_text("")
    texts = ["edit cairn/tools/a/m.py and cairn/tools/b/n.py; then x.py gains a flag; only.py too"]
    return base, repo, texts


def tooth_1() -> None:
    name = PROVES["6548996bd5c0"]["1"]
    base, repo, texts = _scratch()
    try:
        R = _R()
        entries = R.what_exists(texts, [repo, base / "CairnCommons"])
        x = [e for e in entries if e["name"] == "x.py"]
        line = next((ln for ln in R._what_exists_lines(entries).splitlines() if " x.py" in ln), "")
        ok = (len(x) == 1 and x[0]["found"] is True and x[0].get("at") == "cairn/tools/a/x.py"
              and x[0].get("also") == ["cairn/tools/b/x.py"]
              and "cairn/tools/a/x.py" in line and "cairn/tools/b/x.py" in line)
        check(name, ok, f"entries={x} line={line!r}")
    finally:
        shutil.rmtree(base, ignore_errors=True)


def tooth_2() -> None:
    name = PROVES["6548996bd5c0"]["2"]
    base, repo, texts = _scratch()
    try:
        R = _R()
        entries = R.what_exists(texts, [repo, base / "CairnCommons"])
        only = [e for e in entries if e["name"] == "only.py"]
        line = next((ln for ln in R._what_exists_lines(entries).splitlines() if " only.py" in ln), "")
        ok = (len(only) == 1 and only[0].get("at") == "cairn/tools/a/only.py" and "also" not in only[0]
              and line == "present path only.py (at cairn/tools/a/only.py)")
        check(name, ok, f"entries={only} line={line!r}")
    finally:
        shutil.rmtree(base, ignore_errors=True)


def tooth_3() -> None:
    name = PROVES["6548996bd5c0"]["3"]
    text, _, _ = _R().render("5183005fa134")
    exists = text[text.index("# WHAT EXISTS"):]
    line = next((ln for ln in exists.splitlines() if ln.startswith("present path __main__.py")), "")
    check(name, BUS_MAIN in line, f"line={line!r}")


def tooth_4() -> None:
    name = PROVES["6548996bd5c0"]["4"]
    here = Path(__file__).parent
    bad = {}
    for p in ("test_the_rehearsal_is_a_build_simulator.py", "test_rehearsal.py"):
        r = subprocess.run([sys.executable, str(here / p)], cwd=REPO, capture_output=True, text=True,
                           timeout=600)
        if r.returncode != 0:
            bad[p] = (r.stdout + r.stderr)[-400:]
    check(name, not bad, f"{bad}" if bad else "both green")


def main() -> int:
    for t in (tooth_1, tooth_2, tooth_3, tooth_4):
        try:
            t()
        except Exception as exc:  # noqa: BLE001 — a tooth's failure is its verdict
            check(PROVES["6548996bd5c0"][t.__name__.split("_")[1]], False, f"{type(exc).__name__}: {exc}")
    print(f"{4 - len(FAILURES)} passed, {len(FAILURES)} failed")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
