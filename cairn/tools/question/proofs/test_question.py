#!/usr/bin/env python3
"""Teeth for cairn.tools.question — a decision Akien makes is a question bound to its ticket.

One tooth per falsifier clause of ticket 9adc6fddf185, over a scratch world the proof owns
(``artifact.set_diagnostic_roots`` for the writes; ``CAIRN_QUESTIONS_DIR`` for the readers
that run in a subprocess — the BUILDME entry gate and the CLI):

  1. a question opens THROUGH THE ARTIFACT DOOR (the journal entry is read back) and the
     operator inbox lists it under its ticket;
  2. an answer resolves it, the journal names the caller class the kernel measured, and a
     spawned question is born of it on the same ticket — the loop going around (the field
     was ``follow_ups`` until ticket bc7b64626405 made ``spawned`` a required claim);
  3. the entry gate's fourth lane reds a ticket with an open question and ``_entry_gate``
     raises naming ``cairn question answer``; the same ticket crosses once answered. With
     the gate reverted the lane is absent and this tooth reds — the hollow reading;
  4. ``cairn ruling open`` and ``/ruled`` exit non-zero pointing at ``cairn question``, the
     Stop hooks carry no ruling hook, and no skill tells CC to open a ruling;
  5. the two sieves take an answered question id as same-act evidence and refuse an
     unanswered one and a cite of neither.

The subject is bound at CALL time so a reverted world reds every declared tooth by name
rather than crashing the reader.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

Q = None  # type: ignore[assignment]  — bound in main()
A = None  # type: ignore[assignment]

REPO = Path(__file__).resolve().parents[4]
TICKET = "9adc6fddf185"  # the ticket that built the gate — the first one measured by it
FAILURES: list[str] = []

PROVES = {
    "9adc6fddf185": {
        "1": "test_a_question_opens_through_the_door_and_the_inbox_lists_it_under_its_ticket",
        "2": "test_an_answer_resolves_it_and_a_spawned_question_is_born_of_it",
        "3": "test_a_ticket_with_an_open_question_is_refused_at_buildme_and_crosses_once_answered",
        "4": "test_ruling_open_is_retired_and_no_skill_opens_one",
        "5": "test_an_answered_question_is_same_act_evidence_for_the_sieves",
        "cli": "test_the_cli_opens_answers_and_lists",
        "charter": "test_the_charter_stands_beside_the_code_and_names_this_proof",
        "probe": "test_the_probe_is_armed_with_carry_and_enough",
    },
    # the links ticket re-worded two of these teeth: the answer's ``spawned`` opens each
    # question born_of it (clause 2) and the CLI says ``--spawned`` — the rest of that
    # ticket is proved beside this file in test_question_links.py
    "bc7b64626405": {
        "2": "test_an_answer_resolves_it_and_a_spawned_question_is_born_of_it",
        "cli": "test_the_cli_opens_answers_and_lists",
    },
}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _world(tmp: Path) -> Path:
    commons = tmp / "CairnCommons"
    (commons / "questions").mkdir(parents=True)
    (commons / "tickets").mkdir()
    cairn = tmp / "cairn"
    cairn.mkdir()
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    return commons


def _env(qdir: Path) -> dict:
    """The subprocess seam: the scratch questions store AND the scratch artifact roots — without
    the roots the CLI's ticket-side link (ticket bc7b64626405) lands on the LIVE 9adc ticket,
    which this proof did once, on 2026-09-14, two phantom ids the sieve then reported."""
    commons = qdir.parent
    return dict(os.environ, PYTHONPATH=str(REPO), CAIRN_QUESTIONS_DIR=str(qdir),
                CAIRN_ARTIFACT_ROOTS=json.dumps({"CairnCommons": str(commons),
                                                 "cairn": str(commons.parent / "cairn")}))


def _gate_in_subprocess(qdir: Path) -> dict:
    """The entry gate over the SCRATCH questions store — question.py binds its store at
    import, so the gate runs where the environment can hand it the scratch one."""
    code = (
        "import json\n"
        "from cairn.tools.base.transitions import inspect_entry, _entry_gate, EntryGateRed\n"
        f"rec = inspect_entry({TICKET!r})\n"
        "lanes = {l['identity']: l.get('fatality') for l in rec}\n"
        "try:\n"
        f"    note, _ = _entry_gate({TICKET!r}); raised = None\n"
        "except EntryGateRed as exc:\n"
        "    raised = str(exc)\n"
        "print(json.dumps({'lanes': lanes, 'raised': raised}))\n"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       env=_env(qdir), timeout=300, cwd=REPO)
    if r.returncode != 0:
        return {"lanes": {}, "raised": None, "error": r.stderr[-600:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def teeth_door(tmp: Path) -> None:
    commons = _world(tmp)
    qdir = commons / "questions"
    print("THE DOOR — open, answer, spawned, over a scratch world")

    # 1. open through the door; the inbox lists it under the ticket
    rec = Q.open_question(TICKET, "does the proof's question show in the inbox?",
                          "the inbox is where he sees it", root=qdir)
    qid = rec["id"]
    on_disk = (qdir / f"{qid}.json").is_file()
    journal = A.read_journal(commons)
    entry = next((e for e in journal if e.get("verb") == "question" and qid in (e.get("path") or "")), None)
    from cairn.tools.operator_inbox import inbox
    rendered = inbox.build_inbox(questions_dir=qdir)
    listed = qid in rendered and f"[{TICKET}]" in rendered and rec["question"] in rendered
    check(PROVES[TICKET]["1"], on_disk and entry is not None and listed and not rec["resolved"],
          f"on_disk={on_disk} journaled={entry is not None} listed={listed}")

    # 2. the answer resolves it, journals the caller class, bears a spawned question born of it
    ans = Q.answer(qid, "yes — and is the spawned one bound too?",
                   spawned=["is the spawned question bound to the same ticket?"], root=qdir)
    back = Q.read(qid, root=qdir)
    fu = back.get("spawned") or []
    child = Q.read(fu[0], root=qdir) if fu else {}
    journal = A.read_journal(commons)
    aentry = next((e for e in reversed(journal) if e.get("verb") == "answer"), None)
    cls = ((aentry or {}).get("caller") or {}).get("class")
    check(PROVES[TICKET]["2"],
          back["resolved"] and back["answer"] == ans["answer"]
          and cls in ("cc", "akien", "gate")
          and len(fu) == 1 and child.get("born_of") == qid and child.get("ticket") == TICKET
          and not child.get("resolved"),
          f"resolved={back.get('resolved')} class={cls} spawned={fu} child_born_of={child.get('born_of')}")
    twice = False
    try:
        Q.answer(qid, "again", spawned=[], root=qdir)
    except Q.Refused:
        twice = True
    check("a second answer is refused — it is a new question", twice)

    # 3. the gate: the spawned question stands open → the fourth lane is red and the crossing raises;
    #    answer it → every lane green and the crossing goes through.
    g_open = _gate_in_subprocess(qdir)
    lane = "the_ticket_has_every_answer_it_needs"
    red_and_raised = (g_open["lanes"].get(lane) not in (None, "none")
                      and g_open["raised"] is not None
                      and "cairn question answer" in g_open["raised"])
    Q.answer(fu[0], "yes", spawned=[], root=qdir)
    g_done = _gate_in_subprocess(qdir)
    green_and_crossed = g_done["lanes"].get(lane) == "none" and g_done["raised"] is None
    check(PROVES[TICKET]["3"], red_and_raised and green_and_crossed,
          f"open: lane={g_open['lanes'].get(lane)!r} raised={bool(g_open['raised'])} "
          f"{g_open.get('error', '')[:120]}; answered: lane={g_done['lanes'].get(lane)!r} "
          f"raised={bool(g_done['raised'])} {g_done.get('error', '')[:120]}")

    # 5. the sieves: an answered question is same-act evidence; an open one and neither are not
    os.environ["CAIRN_QUESTIONS_DIR"] = str(qdir)
    try:
        from cairn.machines.corrosion import citation
        from cairn.machines.exemptions import justification
        ok_ans, _ = citation.answered_question(qid)
        open_q = Q.open_question(TICKET, "still open?", "unanswered — must not count", root=qdir)
        ok_open, why_open = citation.answered_question(open_q["id"])
        base = {"id": "x", "path": "cairn/tools/question/question.py"}
        lack_ans = justification.justification_lack(dict(base, justification_kind="question", evidence=qid))
        lack_open = justification.justification_lack(dict(base, justification_kind="question", evidence=open_q["id"]))
        lack_none = justification.justification_lack(dict(base, justification_kind="none", evidence="because"))
        check(PROVES[TICKET]["5"],
              ok_ans and not ok_open and lack_ans == "" and lack_open != "" and lack_none != "",
              f"answered={ok_ans} open={ok_open} ({why_open[:40]}) lacks: ans={lack_ans!r} "
              f"open={lack_open[:40]!r} none={lack_none[:40]!r}")
    finally:
        os.environ.pop("CAIRN_QUESTIONS_DIR", None)

    # cli: open / answer / list / show, exit 2 on a refusal
    print("THE CLI")
    env = _env(qdir)
    cli = [str(REPO / "bin" / "cairn"), "question"]
    r_open = subprocess.run(cli + ["open", "--ticket", TICKET, "is the cli the same door?",
                                   "--why", "his shell reaches it"],
                            capture_output=True, text=True, env=env, timeout=120)
    cid = next((tok for tok in r_open.stdout.split() if tok.startswith("open-")), "")
    r_list = subprocess.run(cli + ["list", TICKET], capture_output=True, text=True, env=env, timeout=120)
    r_ans = subprocess.run(cli + ["answer", cid, "yes", "--spawned", "and its spawned question?"],
                           capture_output=True, text=True, env=env, timeout=120)
    r_show = subprocess.run(cli + ["show", cid], capture_output=True, text=True, env=env, timeout=120)
    r_bad = subprocess.run(cli + ["open", "--ticket", TICKET, "not a question", "--why", "x"],
                           capture_output=True, text=True, env=env, timeout=120)
    check(PROVES[TICKET]["cli"],
          r_open.returncode == 0 and cid and r_list.returncode == 0 and cid in r_list.stdout
          and r_ans.returncode == 0 and r_show.returncode == 0 and '"resolved": true' in r_show.stdout
          and r_bad.returncode == 2,
          f"open={r_open.returncode} id={cid!r} list={r_list.returncode} answer={r_ans.returncode} "
          f"show={r_show.returncode} bad={r_bad.returncode} {r_open.stderr[-200:]}{r_ans.stderr[-200:]}")


def teeth_retirement() -> None:
    print("THE RETIREMENT — rulings are questions now")
    r = subprocess.run([str(REPO / "bin" / "cairn"), "ruling", "open", "/dev/null"],
                       capture_output=True, text=True, timeout=120)
    ruling_refuses = r.returncode != 0 and "cairn question" in r.stderr
    r2 = subprocess.run([sys.executable, "-m", "skills.ruled.door"], capture_output=True, text=True,
                        env=dict(os.environ, PYTHONPATH=str(REPO)), cwd=REPO, timeout=120)
    ruled_refuses = r2.returncode != 0 and "cairn question" in r2.stderr
    try:
        settings = json.loads((REPO / ".claude" / "settings.json").read_text())
        stop = json.dumps(settings.get("hooks", {}).get("Stop", []))
    except (OSError, ValueError):
        stop = "UNREADABLE ruling"
    hook_gone = "ruling" not in stop
    tellers = []
    for skill in sorted((REPO / "skills").glob("*/SKILL.md")):
        for n, line in enumerate(skill.read_text(encoding="utf-8").splitlines(), 1):
            low = line.lower()
            if ("cairn ruling open" in low or "open a ruling" in low) and not any(
                    w in low for w in ("retired", "refuse", "never", "not ")):
                tellers.append(f"{skill.parent.name}:{n}")
    # the two prose surfaces that TELL the next mind where a decision goes: /ruled's own
    # SKILL.md must read as retired and point at the question door, and CLAUDE.md's
    # residue must name decision intake by `cairn question` rather than `cairn ruling`.
    ruled_md = (REPO / "skills" / "ruled" / "SKILL.md").read_text(encoding="utf-8").lower()
    ruled_md_retired = "retired" in ruled_md and "cairn question" in ruled_md
    claude_md = (REPO / "CLAUDE.md").read_text(encoding="utf-8")
    claude_md_tells = ("cairn question" in claude_md and TICKET in claude_md
                       and "ruling intake (`cairn ruling`)" not in claude_md)
    check(PROVES[TICKET]["4"], ruling_refuses and ruled_refuses and hook_gone and not tellers
          and ruled_md_retired and claude_md_tells,
          f"ruling open rc={r.returncode} /ruled rc={r2.returncode} hook_gone={hook_gone} tellers={tellers} "
          f"ruled_md_retired={ruled_md_retired} claude_md_tells={claude_md_tells}")


def teeth_beside() -> None:
    print("THE CHARTER AND THE PROBE")
    charter = Path(__file__).resolve().parents[1] / "intention+why.json"
    try:
        doc = json.loads(charter.read_text())
    except (OSError, ValueError):
        doc = {}
    # and the tool is a real package, not a namespace the interpreter improvises: the
    # tester's discovery and `python -m cairn.tools.question` both stand on __init__.py.
    import importlib.util
    spec = importlib.util.find_spec("cairn.tools.question")
    is_package = bool(spec and spec.origin and spec.origin.endswith("__init__.py"))
    check(PROVES[TICKET]["charter"],
          bool(doc) and "test_question.py" in json.dumps(doc) and bool(doc.get("why")) and is_package,
          f"{charter.name}: {sorted(doc)[:6]} package_origin={getattr(spec, 'origin', None)}")
    try:
        from cairn.tools.question.probes import no_crossing_with_an_open_question as probe_mod
        probe = probe_mod.PROBE
        armed = callable(probe.carry) and callable(probe.enough) and callable(probe.trigger)
        detail = f"to={probe.to} horizon={probe.horizon}"
    except Exception as exc:  # noqa: BLE001 — an unimportable probe is the red
        armed, detail = False, repr(exc)[:120]
    check(PROVES[TICKET]["probe"], armed, detail)


def _red_every_declared_tooth(reason: str) -> None:
    for name in PROVES[TICKET].values():
        if name not in FAILURES:
            check(name, False, reason)


def main() -> int:
    global Q, A
    try:
        from cairn.tools.question import question as subject
        from cairn.tools.artifact import artifact as door
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject does not load: {exc!r}")
        _red_every_declared_tooth("subject absent")
        print(f"\nRED — {len(FAILURES)} failure(s)")
        return 1
    Q, A = subject, door
    try:
        with tempfile.TemporaryDirectory(prefix="cairn-question-proof-") as d:
            try:
                teeth_door(Path(d))
            finally:
                A.set_diagnostic_roots(None)
        teeth_retirement()
        teeth_beside()
    except Exception as exc:  # noqa: BLE001 — a subject whose world was taken away
        print(f"the teeth could not run to the end: {exc!r}")
        _red_every_declared_tooth(f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
