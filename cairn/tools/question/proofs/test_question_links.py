"""Proof for ticket bc7b64626405 — a question and its ticket name each other, and an answer
names what it spawned.

Akien, 2026-09-14: *"if a question is about a ticket, it should have a bidirectional link.
and we should explicitly say 'and the answer spawned x, y and z new questions' in some
jsonic way that's not prose"* — something an inspector could inspect. The teeth, each
against the ticket's falsifier:

  1. opening a question writes BOTH ends in one act — the ticket's ``questions`` gains the
     id (journaled ``cast``) beside the question record (journaled ``question``); a ticket
     the id does not resolve to writes the question side only, and says so by writing nothing
     else;
  2. an answer without ``spawned`` is refused; ``[]`` is a recorded claim; a list opens each
     question born of this one on the same ticket and records the ids;
  3. a question bound to an intent berth path holds the BUILDME lane like one bound to the
     id, and ``rebind`` moves it onto the id and writes the ticket-side end (charter edge (a));
  4. the sieve ``question_links_agree`` reads a door-written world clean, reds each of the
     ways the two ends can be hand-broken with one finding apiece, and reads the LIVE corpus
     clean — the invariant the door's existence is supposed to make hold;
  5. the WATCHME probe is armed and measures a door-written commons with no lack;
  cli / renderer / wording / charter — the shell surfaces, the operator's ticket view, the
     prose that tells the next mind the verb, and the charter beside the code.

The subject is bound at CALL time so a reverted world reds every declared tooth by name
rather than crashing the reader.
"""

from __future__ import annotations

import json
import re
import os
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

Q = None  # type: ignore[assignment]  — bound in main()
A = None  # type: ignore[assignment]
I = None  # type: ignore[assignment]

REPO = Path(__file__).resolve().parents[4]
LIVE_COMMONS = REPO.parent / "CairnCommons"
TICKET = "bc7b64626405"
GATE_TICKET = "9adc6fddf185"  # the live ticket the entry gate is read over (its chain is berthed)
TID = "0badc0ffee00"          # the scratch world's ticket
BERTH = "/home/akien/.cairn/devices/skill_block/0/berths/intent/intent-20260101T000000-proofworld.json"
FAILURES: list[str] = []

PROVES = {
    "bc7b64626405": {
        "1": "test_opening_a_question_writes_both_ends_in_one_act",
        "2": "test_an_answer_says_what_it_spawned_or_is_refused",
        "3": "test_a_berth_bound_question_holds_the_gate_and_rebind_names_the_ticket",
        "4": "test_the_sieve_reds_each_hand_break_and_reads_the_live_corpus_clean",
        "5": "test_the_binding_sieve_predicts_no_unran_and_a_landed_hollow_reading_names_no_hollow_file",
        "probe": "test_the_probe_is_armed_and_measures_a_door_written_commons_clean",
        "cli": "test_the_cli_requires_spawned_rebinds_and_lists_the_tree",
        "renderer": "test_the_operators_ticket_view_renders_its_questions",
        "wording": "test_no_surface_still_says_follow_up",
        "charter": "test_the_charter_names_the_sieve_the_probe_and_this_proof",
    }
}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _world(tmp: Path) -> Path:
    """A scratch commons with ONE ticket filed, cast through the door under diagnostic roots."""
    commons = tmp / "CairnCommons"
    (commons / "questions").mkdir(parents=True)
    (commons / "tickets").mkdir()
    cairn = tmp / "cairn"
    cairn.mkdir()
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    doc = {"id": TID, "intent_berth": BERTH, "sorted_berth": "none, because a proof world",
           "questions": "none, because the proof opens them through the door",
           "workflow_and_state": "code-seam@v2: THINKME -> TICKETME -> [BUILDME:waiting] -> PROVEME -> PROVED"}
    A.write_json(commons / "tickets" / f"{TID}-a-proof-world-ticket.json", doc,
                 verb="cast", why="the scratch ticket the proof's questions are about")
    return commons


def _ticket(commons: Path) -> dict:
    return json.loads((commons / "tickets" / f"{TID}-a-proof-world-ticket.json").read_text(encoding="utf-8"))


def _env(commons: Path) -> dict:
    return dict(os.environ, PYTHONPATH=str(REPO), CAIRN_QUESTIONS_DIR=str(commons / "questions"),
                CAIRN_ARTIFACT_ROOTS=json.dumps({"CairnCommons": str(commons), "cairn": str(commons.parent / "cairn")}))


def _gate_in_subprocess(qdir: Path) -> dict:
    """The entry gate over the SCRATCH questions store and the LIVE 9adc ticket — question.py
    binds its store at import, so the gate runs where the environment hands it the scratch one;
    the ticket is live so the other three lanes read green and only the answers lane moves."""
    code = (
        "import json\n"
        "from cairn.tools.base.transitions import inspect_entry, _entry_gate, EntryGateRed\n"
        f"rec = inspect_entry({GATE_TICKET!r})\n"
        "lanes = {l['identity']: l.get('fatality') for l in rec}\n"
        "try:\n"
        f"    note, _ = _entry_gate({GATE_TICKET!r}); raised = None\n"
        "except EntryGateRed as exc:\n"
        "    raised = str(exc)\n"
        "print(json.dumps({'lanes': lanes, 'raised': raised}))\n"
    )
    r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                       env=dict(os.environ, PYTHONPATH=str(REPO), CAIRN_QUESTIONS_DIR=str(qdir)),
                       timeout=300, cwd=REPO)
    if r.returncode != 0:
        return {"lanes": {}, "raised": None, "error": r.stderr[-600:]}
    return json.loads(r.stdout.strip().splitlines()[-1])


def _sieve(commons: Path) -> list[dict]:
    return I.question_links_agree({"component": "question"}, REPO / "cairn/tools/question", commons=commons)


def teeth_door(tmp: Path) -> None:
    commons = _world(tmp)
    qdir = commons / "questions"
    print("THE DOOR — both ends, spawned, rebind, over a scratch world")

    # 1. open: the question record AND the ticket's questions list, in one act, both journaled
    rec = Q.open_question(TID, "does the ticket name me back?", "the link has two ends", root=qdir)
    qid = rec["id"]
    tk = _ticket(commons)
    listed = qid in Q.links_of(tk)
    journal = A.read_journal(commons)
    q_entry = any(e.get("verb") == "question" and qid in (e.get("path") or "") for e in journal)
    t_entry = any(e.get("verb") == "cast" and (e.get("path") or "").startswith("tickets/")
                  and qid in (e.get("why") or "") for e in journal)
    # the same id opened twice does not double the list; an unfiled ticket writes one end only
    Q._link_to_ticket(TID, qid, why="again")
    once = Q.links_of(_ticket(commons)).count(qid) == 1
    n_tickets = len(list((commons / "tickets").glob("*.json")))
    orphan = Q.open_question("feedfacefeed", "no ticket file for me?", "unfiled", root=qdir)
    orphan_wrote_only_itself = (qdir / f"{orphan['id']}.json").is_file() \
        and len(list((commons / "tickets").glob("*.json"))) == n_tickets \
        and orphan["id"] not in Q.links_of(_ticket(commons))
    check(PROVES[TICKET]["1"], listed and q_entry and t_entry and once and orphan_wrote_only_itself
          and rec.get("spawned") is None and "follow_ups" not in rec,
          f"listed={listed} journaled(question={q_entry}, cast={t_entry}) once={once} "
          f"orphan_one_end={orphan_wrote_only_itself} spawned_field={rec.get('spawned')!r}")

    # 2. spawned is a required claim: None refused, [] recorded, a list opened born_of and listed
    refused = False
    try:
        Q.answer(qid, "yes", root=qdir)
    except Q.Refused as exc:
        refused = "spawned" in str(exc)
    still_open = not Q.read(qid, root=qdir).get("resolved")
    none_rec = Q.answer(qid, "yes", spawned=[], root=qdir)
    none_ok = none_rec["resolved"] and none_rec["spawned"] == [] and "follow_ups" not in none_rec
    q2 = Q.open_question(TID, "and does an answer bear questions?", "the loop", root=qdir)
    two = Q.answer(q2["id"], "two of them", spawned=["first born?", "second born?"], root=qdir)
    kids = [Q.read(k, root=qdir) for k in two["spawned"]]
    tk = _ticket(commons)
    born_ok = (len(kids) == 2 and all(k["born_of"] == q2["id"] and k["ticket"] == TID
                                      and not k["resolved"] and k["id"] in Q.links_of(tk) for k in kids)
               and [k["question"] for k in kids] == ["first born?", "second born?"])
    not_a_question = False
    try:
        Q.answer(kids[0]["id"], "x", spawned=["a statement"], root=qdir)
    except Q.Refused:
        not_a_question = True
    entries = [e for e in A.read_journal(commons) if e.get("verb") == "answer"]
    says = any("spawned 2 question(s)" in (e.get("why") or "") for e in entries) \
        and any("spawned none" in (e.get("why") or "") for e in entries)
    check(PROVES[TICKET]["2"], refused and still_open and none_ok and born_ok and not_a_question and says,
          f"refused={refused} still_open={still_open} none_ok={none_ok} born_ok={born_ok} "
          f"statement_refused={not_a_question} journal_says={says}")

    # 3. a berth-bound question counts against the ticket, holds the live gate, and rebinds
    A.set_diagnostic_roots(None)
    try:
        live_berth = Q._berth_of(GATE_TICKET)
    finally:
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": tmp / "cairn", "parked": tmp / "parked"})
    b = Q.open_question(live_berth or "no-berth", "raised at /intent, before the id existed?",
                        "edge (a)", root=qdir)
    g_open = _gate_in_subprocess(qdir)
    lane = "the_ticket_has_every_answer_it_needs"
    held = g_open["lanes"].get(lane) not in (None, "none") and g_open["raised"] is not None
    Q.answer(b["id"], "it does", spawned=[], root=qdir)
    g_done = _gate_in_subprocess(qdir)
    released = g_done["lanes"].get(lane) == "none" and g_done["raised"] is None
    # the scratch ticket's berth: open on it, open_for counts it, rebind renames and links
    s = Q.open_question(BERTH, "bound to the scratch berth?", "edge (a)", root=qdir)
    counted = s["id"] in {q["id"] for q in Q.open_for(TID, root=qdir)}
    unlisted = s["id"] not in Q.links_of(_ticket(commons))
    moved = Q.rebind(TID, root=qdir)
    after = Q.read(s["id"], root=qdir)
    rebound = ([m["id"] for m in moved] == [s["id"]] and after["ticket"] == TID
               and s["id"] in Q.links_of(_ticket(commons)) and Q.rebind(TID, root=qdir) == [])
    no_file = False
    try:
        Q.rebind("feedfacefeed", root=qdir)
    except Q.Refused:
        no_file = True
    check(PROVES[TICKET]["3"], bool(live_berth) and held and released and counted and unlisted and rebound and no_file,
          f"live_berth={bool(live_berth)} held={held} released={released} "
          f"{g_open.get('error', '')[:100]}{g_done.get('error', '')[:100]} counted={counted} "
          f"unlisted_before={unlisted} rebound={rebound} no_file_refused={no_file}")

    # 4. the sieve: clean over the door's world; one finding per hand-break; the live corpus clean
    registered = I.SIEVES.get("question_links_agree") is I.question_links_agree
    clean = _sieve(commons)
    breaks = []
    tpath = commons / "tickets" / f"{TID}-a-proof-world-ticket.json"

    def hand(doc_fn, qid_, q_fn):
        # a hand edit, deliberately NOT through the door — the drift the sieve exists to see
        if doc_fn is not None:
            d = _ticket(commons); doc_fn(d)
            tpath.write_text(json.dumps(d, indent=2) + "\n", encoding="utf-8")
        if q_fn is not None:
            q = Q.read(qid_, root=qdir); q_fn(q)
            (qdir / f"{qid_}.json").write_text(json.dumps(q, indent=2) + "\n", encoding="utf-8")
        found = _sieve(commons)
        breaks.append(len(found))
        return found

    f1 = hand(lambda d: d["questions"].remove(qid), None, None)            # (ii) ticket forgot one
    f2 = hand(lambda d: d["questions"].append("open-ffffffffffff"), None, None)  # (i) a ghost id
    f3 = hand(None, q2["id"], lambda q: q.update(ticket="deadbeef0000"))     # (i) names another ticket
    f4 = hand(None, q2["id"], lambda q: q.update(spawned=[kids[0]["id"], "open-000000000000"]))  # (iii)
    ghost_child = Q.open_question(BERTH, "left on the berth after the cast?", "edge (a)", root=qdir)  # (iv)
    f5 = _sieve(commons)
    breaks.append(len(f5))
    abouts = [f["about"] for f in f5]
    each = (breaks == [1, 2, 3, 4, 5]
            and any(qid in a and "lists it back" in a for a in abouts)
            and any("open-ffffffffffff" in a and "record exists" in a for a in abouts)
            and any(q2["id"] in a and "names the ticket back" in a for a in abouts)
            and any("open-000000000000" in a and "born of it" in a for a in abouts)
            and any(ghost_child["id"] in a and "rebound to the id" in a for a in abouts))
    live = I.question_links_agree({"component": "question"}, REPO / "cairn/tools/question", commons=LIVE_COMMONS)
    scoped = I.question_links_agree({"component": "artifact"}, REPO / "cairn/tools/artifact", commons=commons) == []
    check(PROVES[TICKET]["4"], registered and clean == [] and each and live == [] and scoped,
          f"registered={registered} clean={len(clean)} breaks={breaks} each={each} live={len(live)} "
          f"scoped_to_question={scoped} {[a[:60] for a in abouts][:5]}")
    # put the world back the way the door left it, for the probe's reading
    hand(lambda d: d.update(questions=[x for x in d["questions"] if x != "open-ffffffffffff"] + [qid]), None, None)
    hand(None, q2["id"], lambda q: q.update(ticket=TID, spawned=[k["id"] for k in kids]))
    Q.rebind(TID, root=qdir)

    # 5. the probe: armed, and its measurement over this commons reads no lack
    try:
        from cairn.tools.question.probes import both_ends_agree as probe_mod
        probe = probe_mod.PROBE
        armed = callable(probe.carry) and callable(probe.enough) and callable(probe.trigger) \
            and probe.to == "harbor_master"
        ctx = probe_mod._measure({}, commons=commons)
        # trigger/enough read the LIVE commons; here the carry over the scratch reading is the tooth
        carried = probe_mod._carry(dict(ctx))
        measured = (ctx["lacks"] == [] and ctx["wrong_intent"] == [] and ctx["events"] >= 8
                    and ctx["answers"] >= 3 and ctx["with_spawned"] >= 1
                    and "both ends agreeing" in carried["finding"])
        detail = f"to={probe.to} events={ctx['events']} answers={ctx['answers']} spawned={ctx['with_spawned']} lacks={len(ctx['lacks'])}"
    except Exception as exc:  # noqa: BLE001 — an unimportable probe is the red
        armed, measured, detail = False, False, repr(exc)[:160]
    check(PROVES[TICKET]["probe"], armed and measured, detail)

    # renderer: the operator's ticket view carries a QUESTIONS section as a tree
    from cairn.tools.operator_inbox import inbox
    view = inbox._format_ticket(_ticket(commons), tpath)
    tree = Q.render_tree(Q.for_ticket(TID, root=qdir))
    check(PROVES[TICKET]["renderer"],
          "QUESTIONS" in view and qid in view and kids[1]["id"] in view and "spawned:" in view
          and q2["id"] in tree and kids[0]["id"] in tree and "spawned: none" in tree,
          f"view_has_section={'QUESTIONS' in view} ids_in_view={qid in view and kids[1]['id'] in view} "
          f"tree_lines={len(tree.splitlines())}")

    # cli: --spawned is required, `none` folds, two open two, rebind and list are verbs
    print("THE CLI")
    env = _env(commons)
    cli = [str(REPO / "bin" / "cairn"), "question"]
    run = lambda *a: subprocess.run(cli + list(a), capture_output=True, text=True, env=env, timeout=120)  # noqa: E731
    r_open = run("open", "--ticket", TID, "is the cli the same door?", "--why", "his shell reaches it")
    cid = next((tok for tok in r_open.stdout.split() if tok.startswith("open-")), "")
    r_missing = run("answer", cid, "yes")
    r_none = run("answer", cid, "yes", "--spawned", "NONE")
    r_open2 = run("open", "--ticket", TID, "and two more?", "--why", "the loop")
    cid2 = next((tok for tok in r_open2.stdout.split() if tok.startswith("open-")), "")
    r_two = run("answer", cid2, "yes", "--spawned", "one?", "--spawned", "two?")
    r_berth = run("open", "--ticket", BERTH, "raised before the id?", "--why", "edge (a)")
    r_rebind = run("rebind", TID)
    r_list = run("list", TID)
    tk = _ticket(commons)
    none_rec = Q.read(cid, root=qdir) if cid else {}
    check(PROVES[TICKET]["cli"],
          r_open.returncode == 0 and cid and cid in Q.links_of(tk)
          and r_missing.returncode == 2 and "spawned" in r_missing.stderr
          and r_none.returncode == 0 and none_rec.get("spawned") == [] and "spawned: none" in r_none.stdout
          and r_two.returncode == 0 and r_two.stdout.count("spawned: open-") == 2
          and r_berth.returncode == 0 and r_rebind.returncode == 0 and "rebound: open-" in r_rebind.stdout
          and r_list.returncode == 0 and cid in r_list.stdout and cid2 in r_list.stdout
          and "[answered]" in r_list.stdout and "[OPEN]" in r_list.stdout,
          f"open={r_open.returncode} missing={r_missing.returncode} none={r_none.returncode} "
          f"two={r_two.returncode} berth={r_berth.returncode} rebind={r_rebind.returncode} list={r_list.returncode} "
          f"{(r_open.stderr + r_missing.stderr + r_none.stderr + r_two.stderr + r_rebind.stderr + r_list.stderr)[-300:]}")


def teeth_beside() -> None:
    print("THE WORDING AND THE CHARTER")
    # wording: no surface this ticket wrote — the tool, its probes, the CLI, the skills that
    # tell the next mind the verb, the ruling face, the inbox renderer, the inspector — still
    # says follow-up in any form (the flag, the kwarg, the field, the probe's counters),
    # except a reader of pre-build records that says so on the same line. The librarian's
    # own follow-up questions are another word and out of this scope.
    word = re.compile(r"follow[-_]ups?\b", re.IGNORECASE)
    surfaces = [REPO / "cairn/tools/question", REPO / "skills/sorted", REPO / "skills/ruled",
                REPO / "cairn/machines/ruling/cli.py", REPO / "cairn/tools/operator_inbox/inbox.py",
                REPO / "cairn/machines/build_inspector/inspector.py", REPO / "bin/cmd/question"]
    tellers = []
    for base in surfaces:
        for p in sorted(base.rglob("*")) if base.is_dir() else [base]:
            if not p.is_file() or p.suffix not in (".py", ".md", ".sh", ".json", "") \
                    or "/proofs/" in str(p) or "/validations/" in str(p) \
                    or p.name in ("history.json", "state.json"):
                continue
            try:
                text = p.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue
            for n, line in enumerate(text.splitlines(), 1):
                if word.search(line) and "pre-build" not in line and "pre-2026-09-14" not in line:
                    tellers.append(f"{p.relative_to(REPO)}:{n}")
    sorted_md = (REPO / "skills" / "sorted" / "SKILL.md").read_text(encoding="utf-8")
    tells_rebind = "cairn question rebind" in sorted_md and "--spawned" in sorted_md
    check(PROVES[TICKET]["wording"], not tellers and tells_rebind,
          f"tellers={tellers[:6]} sorted_tells_rebind={tells_rebind}")
    # clause (5): the hollow reading is the tester's to take (`cairn test --hollow`), and this
    # tooth reads what stands about it — the binding sieve's prediction (no proof this ticket
    # names binds an added name at import, so nothing reads UNRAN), and, once a reading has
    # landed on this proof's own validation, that no written file read hollow or unreadable
    try:
        from cairn.tools.base import transitions as T
        from cairn.devices.tester import validation_store as V
        from cairn.tools.proof_coverage import proof_coverage as PC
        live = json.loads(Path(T._find_ticket(TICKET)).read_text(encoding="utf-8"))
        wrote = [w for w in PC._writes_to(live) if "/proofs/" not in w]
        binds = PC.proof_binds_its_subject_at_call_time(live, repo_root=REPO)
        trail = V.read_validations(str(Path(__file__).resolve()))
        landed = ((trail[-1].get("evidence") or {}).get("hollow") or {}).get(TICKET) if trail else None
        if landed is None:
            hollow_ok, hollow_detail = True, "no hollow reading landed yet — the tester takes it"
        else:
            bad = {f: t for f, t in landed.items() if not (isinstance(t, list) and t)}
            unread = [f for f in wrote if f not in landed]
            hollow_ok = not bad and not unread
            hollow_detail = (f"landed over {len(landed)} file(s), hollow/unreadable={sorted(bad)[:4]} "
                             f"unmeasured={unread[:4]}")
        check(PROVES[TICKET]["5"], len(wrote) >= 10 and binds == [] and hollow_ok,
              f"writes_to={len(wrote)} early_bindings={len(binds)} {hollow_detail}")
    except Exception as exc:  # noqa: BLE001 — the ticket or the sieve gone is the red
        check(PROVES[TICKET]["5"], False, repr(exc)[:160])
    charter = Path(__file__).resolve().parents[1] / "intention+why.json"
    try:
        doc = json.loads(charter.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        doc = {}
    blob = json.dumps(doc)
    names = all(w in blob for w in ("question_links_agree", "both_ends_agree.py", "test_question_links.py",
                                    "--spawned", "rebind", TICKET))
    check(PROVES[TICKET]["charter"], bool(doc) and names and "--follow-up" not in blob,
          f"{charter.name}: names={names} follow_up_gone={'--follow-up' not in blob}")


def _red_every_declared_tooth(reason: str) -> None:
    for name in PROVES[TICKET].values():
        if name not in FAILURES:
            check(name, False, reason)


def main() -> int:
    global Q, A, I
    try:
        from cairn.tools.question import question as subject
        from cairn.tools.artifact import artifact as door
        from cairn.machines.build_inspector import inspector as insp
        for name in ("_link_to_ticket", "links_of", "spawned_of", "rebind", "for_ticket", "render_tree"):
            getattr(subject, name)
        getattr(insp, "question_links_agree")
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject does not load: {exc!r}")
        _red_every_declared_tooth("subject absent")
        print(f"\nRED — {len(FAILURES)} failure(s)")
        return 1
    Q, A, I = subject, door, insp
    try:
        with tempfile.TemporaryDirectory(prefix="cairn-question-links-proof-") as d:
            try:
                teeth_door(Path(d))
            finally:
                A.set_diagnostic_roots(None)
        teeth_beside()
    except Exception as exc:  # noqa: BLE001 — a subject whose world was taken away
        import traceback; traceback.print_exc()
        print(f"the teeth could not run to the end: {exc!r}")
        _red_every_declared_tooth(f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    sys.exit(main())
