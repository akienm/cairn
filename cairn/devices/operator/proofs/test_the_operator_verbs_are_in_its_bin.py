#!/usr/bin/env python3
"""Proof for ticket fd597e74056f — the operator is a device whose bin carries the operator's verbs.

Measured 2026-11-05: no operator device existed under cairn/devices/ or ~/.cairn/devices;
`cairn operator` reached bin/cmd/operator, which ran cairn.tools.operator_inbox.inbox. Outline
8.4.4 (Q#27): answering is the operator acting, so it is `cairn operator answer`. Teeth, one per
falsifier clause:

  1. cairn/devices/operator/intention+why.json exists, and the instance bin
     ~/.cairn/devices/operator/0/bin resolves to cairn/devices/operator/0/bin — the directory
     itself, or (as cairn_wire_instances wires it) every script of the class bin reached through
     it resolves to that script;
  2. `cairn operator show inbox` prints the inbox through the device bin: bin/cairn's own trace
     execs <instance root>/operator/0/bin/show and never bin/cmd/operator, exit 0, and the
     inbox's header line is the one operator_inbox prints itself;
  3. `cairn operator answer <id> "<words>" --spawned none` on a scratch open question records
     the words verbatim exactly as `cairn question answer` does on its twin;
  4. no script in the bin imports or runs any module outside the public interfaces of
     operator_inbox and the question door.

The question corpus of tooth 3 is scratch (CAIRN_QUESTIONS_DIR + CAIRN_ARTIFACT_ROOTS); tooth 2
reads the live inbox and writes nothing.

    python3 cairn/devices/operator/proofs/test_the_operator_verbs_are_in_its_bin.py
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO = Path(__file__).resolve().parents[4]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

_DEV = _REPO / "cairn" / "devices" / "operator"
_BIN = _DEV / "0" / "bin"
_INSTANCE_ROOT = Path(os.environ.get("CAIRN_INSTANCE_ROOT", Path.home() / ".cairn" / "devices"))
VERBS = ("operator", "show", "answer")
TICKET = "fd597e74056f"
ALLOWED = {"cairn.tools.operator_inbox.inbox", "cairn.tools.question", "cairn.tools.question.question"}

PROVES = {"fd597e74056f": {
    "1": "clause_1_the_charter_stands_and_the_instance_bin_resolves",
    "2": "clause_2_show_inbox_runs_through_the_device_bin",
    "3": "clause_3_answer_records_the_words_as_the_question_door_does",
    "4": "clause_4_no_script_reaches_past_the_two_interfaces",
}}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}", flush=True)
    if detail:
        print(f"        {detail[:1500]}", flush=True)
    if not ok:
        FAILURES.append(name)


def clause_1_the_charter_stands_and_the_instance_bin_resolves() -> None:
    lacks = []
    charter = _DEV / "intention+why.json"
    try:
        doc = json.loads(charter.read_text(encoding="utf-8"))
        if not (isinstance(doc.get("what"), str) and doc["what"].strip()
                and isinstance(doc.get("why"), str) and doc["why"].strip()):
            lacks.append("the charter carries no what/why")
    except (OSError, ValueError) as exc:
        lacks.append(f"no readable charter: {exc}")
    inst = _INSTANCE_ROOT / "operator" / "0" / "bin"
    scripts = [p for p in sorted(_BIN.glob("*")) if p.is_file() and os.access(p, os.X_OK)] \
        if _BIN.is_dir() else []
    if sorted(p.name for p in scripts) != sorted(VERBS):
        lacks.append(f"class bin holds {[p.name for p in scripts]}, want {sorted(VERBS)}")
    if not inst.is_dir():
        lacks.append(f"{inst} is not a directory")
    elif inst.resolve() != _BIN.resolve():
        unresolved = [p.name for p in scripts if (inst / p.name).resolve() != p.resolve()]
        if unresolved or not scripts:
            lacks.append(f"{inst} neither resolves to {_BIN} nor carries its scripts: {unresolved}")
    check("clause_1_the_charter_stands_and_the_instance_bin_resolves", not lacks, "; ".join(lacks))


def _first_line(text: str) -> str:
    return next((l for l in text.splitlines() if l.strip()), "")


def clause_2_show_inbox_runs_through_the_device_bin() -> None:
    env = {**os.environ, "PYTHONPATH": str(_REPO)}
    r = subprocess.run(["bash", "-x", str(_REPO / "bin" / "cairn"), "operator", "show", "inbox"],
                       capture_output=True, text=True, env=env, cwd=str(_REPO), timeout=600)
    direct = subprocess.run([sys.executable, "-m", "cairn.tools.operator_inbox.inbox", "show", "inbox"],
                            capture_output=True, text=True, env=env, cwd=str(_REPO), timeout=600)
    trace = [l for l in r.stderr.splitlines() if l.startswith("+") and " exec " in f" {l[1:].lstrip('+ ')}"]
    want = str(_INSTANCE_ROOT / "operator" / "0" / "bin" / "show")
    lacks = []
    if r.returncode != 0:
        lacks.append(f"rc={r.returncode}")
    if not any(want in l for l in trace):
        lacks.append(f"bin/cairn never execs {want}: {trace[-3:]}")
    if "bin/cmd/operator" in r.stderr:
        lacks.append("bin/cmd/operator was reached")
    if not r.stdout.strip() or _first_line(r.stdout) != _first_line(direct.stdout):
        lacks.append(f"header {_first_line(r.stdout)!r} != operator_inbox's {_first_line(direct.stdout)!r}")
    check("clause_2_show_inbox_runs_through_the_device_bin", not lacks,
          "; ".join(lacks) + ("" if not lacks else f" | stderr tail {r.stderr[-300:]!r}"))


def clause_3_answer_records_the_words_as_the_question_door_does() -> None:
    words = "  Yes — the operator's words, verbatim: \"quoted\" & 'odd' $HOME `ticks`  "
    with tempfile.TemporaryDirectory(prefix="fd59-q-") as d:
        tmp = Path(d)
        commons = tmp / "CairnCommons"
        (commons / "questions").mkdir(parents=True)
        (commons / "tickets").mkdir()
        (tmp / "cairn").mkdir()
        # the ticket (its plan and its state) and the store charter its record set reads its keys from
        store = _REPO.parent / "CairnCommons" / "tickets"
        for src in [store / "_charter+why.json", *store.glob(f"{TICKET}-*.json")]:
            if src.is_file():
                (commons / "tickets" / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        qdir = commons / "questions"
        env = dict(os.environ, PYTHONPATH=str(_REPO), CAIRN_QUESTIONS_DIR=str(qdir),
                   CAIRN_ARTIFACT_ROOTS=json.dumps({"CairnCommons": str(commons), "cairn": str(tmp / "cairn")}))

        def cairn(*argv):
            return subprocess.run([str(_REPO / "bin" / "cairn"), *argv], capture_output=True, text=True,
                                  env=env, cwd=str(_REPO), timeout=300)

        ids = []
        for q in ("does the operator's answer land as his words?", "and the door's own twin?"):
            o = cairn("question", "open", "--ticket", TICKET, q, "--why", "the fd59 proof's scratch question")
            ids.append(next((t for t in o.stdout.split() if t.startswith("open-")), ""))
        lacks = []
        if not all(ids):
            lacks.append(f"scratch questions did not open: {ids}")
        else:
            a_op = cairn("operator", "answer", ids[0], words, "--spawned", "none")
            a_q = cairn("question", "answer", ids[1], words, "--spawned", "none")
            recs = []
            for qid in ids:
                try:
                    recs.append(json.loads((qdir / f"{qid}.json").read_text(encoding="utf-8")))
                except (OSError, ValueError) as exc:
                    recs.append({"unreadable": str(exc)})
            keys = ("resolved", "answer", "answered_by", "spawned")
            got = [{k: r.get(k) for k in keys} for r in recs]
            if a_op.returncode != 0 or a_q.returncode != 0:
                lacks.append(f"operator answer rc={a_op.returncode} {a_op.stderr[-300:]!r}; "
                             f"question answer rc={a_q.returncode} {a_q.stderr[-200:]!r}")
            if got[0] != got[1]:
                lacks.append(f"the two records differ: operator={got[0]} question={got[1]}")
            if got[0].get("answer") != words.strip() or got[0].get("resolved") is not True:
                lacks.append(f"the words were not recorded verbatim: {got[0].get('answer')!r}")
            if a_op.stdout.replace(ids[0], "<id>") != a_q.stdout.replace(ids[1], "<id>"):
                lacks.append(f"stdout differs: {a_op.stdout!r} vs {a_q.stdout!r}")
    check("clause_3_answer_records_the_words_as_the_question_door_does", not lacks, "; ".join(lacks))


_MOD = re.compile(r"(?:-m\s+|\bfrom\s+|\bimport\s+)(cairn(?:\.\w+)+)")


def clause_4_no_script_reaches_past_the_two_interfaces() -> None:
    lacks = []
    seen = {}
    for verb in VERBS:
        p = _BIN / verb
        if not p.is_file():
            lacks.append(f"{verb}: absent")
            continue
        mods = sorted(set(_MOD.findall(p.read_text(encoding="utf-8"))))
        seen[verb] = mods
        if not mods:
            lacks.append(f"{verb}: reaches no interface at all")
        extra = [m for m in mods if m not in ALLOWED]
        if extra:
            lacks.append(f"{verb} reaches {extra}")
    check("clause_4_no_script_reaches_past_the_two_interfaces", not lacks,
          "; ".join(lacks) or json.dumps(seen))


def main() -> int:
    os.chdir(_REPO)
    print("fd597e74056f — the operator is a device whose bin carries the operator's verbs")
    for tooth in (clause_1_the_charter_stands_and_the_instance_bin_resolves,
                  clause_2_show_inbox_runs_through_the_device_bin,
                  clause_3_answer_records_the_words_as_the_question_door_does,
                  clause_4_no_script_reaches_past_the_two_interfaces):
        try:
            tooth()
        except Exception as exc:  # noqa: BLE001 — a tooth that cannot run is a red, loudly
            check(tooth.__name__, False, f"raised {type(exc).__name__}: {exc}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
