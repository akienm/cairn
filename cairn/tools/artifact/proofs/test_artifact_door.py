#!/usr/bin/env python3
"""Teeth for cairn.tools.artifact — the one door a record of truth changes through.

FIRST TOOTH, AND THE ONE THE WHOLE DESIGN RESTS ON: the three caller classes are measured
over REAL processes in REAL cgroups — a transient ``cairn-*.service`` for a gate, this
very session for CC (and a scope CC forges to look like a hand, which the ancestry walk
still reads as CC), and a live process in a desktop-app or login-session scope for
Akien. If the kernel does not tell the three apart on this host, the door has nothing
to journal and this proof reds rather than reasons.

Then the door itself over a scratch world (``set_diagnostic_roots``): a journaled write
with a chained entry, a no-op that writes no entry, an out-of-jurisdiction write that
says so, a chain break that ``verify_chain`` names, the pre-commit question refusing a
record staged around the door and passing one that went through it, and the hand-edit
park/approve/refuse round trip — approve refused from CC by measurement.

A hollow build could not pass these: every verdict is read back from disk or from a
subprocess the proof did not control the cgroup of.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4]))

# The subject is bound at CALL time, never at import: the hollow reading takes artifact.py
# (and jurisdiction.json) away and reruns this proof, and a proof that cannot even start
# reads UNREADABLE rather than red. ``A`` is resolved in main(); an absent or unloadable
# subject reds every declared tooth below instead of crashing the reader.
A = None  # type: ignore[assignment]

REPO = Path(__file__).resolve().parents[4]
FAILURES: list[str] = []

# The declared teeth — one per falsifier clause of the ticket, read by proof_coverage and by
# the hollow reading (each file the ticket writes_to, reverted, must red one of these).
PROVES = {
    "30531f6e1c5d": {
        "1": "test_a_record_edited_around_the_door_is_refused_at_the_commit_question",
        "2": "test_the_three_caller_classes_measure_gate_cc_akien",
        "3": "test_a_chain_break_is_detected_by_replay",
        "4": "test_hand_edit_parks_and_the_record_stays_at_its_journaled_bytes",
        "5": "test_a_scratch_world_never_reaches_the_live_journal",
        "charter": "test_the_charter_stands_beside_the_code_and_names_this_proof",
        "probe": "test_the_probe_is_armed_with_carry_and_enough",
        "hook": "test_the_hook_blocks_a_commit_made_around_the_door",
        "cli": "test_the_cli_front_door_answers_caller_with_a_measured_class",
        "journal": "test_the_live_cairn_journal_verifies_from_genesis",
        "seal_writer": "test_the_seal_store_writes_its_validation_through_the_door",
        "projector_writer": "test_the_projector_writes_history_and_state_through_the_door",
        "ticket_writer": "test_the_phase_writer_moves_a_ticket_through_the_door",
    },
    # off Linux the caller teeth fail by name, the hook teeth reach the door (ticket 2a208067d036)
    # its key 2 and 30531f6e1c5d's tester_hook moved with the tester-hook tooth to the tester's
    # own proofs, keys kept (ticket 4d10cd50ef56; RULE 1)
    "2a208067d036": {
        "1": "test_off_linux_the_linux_only_teeth_fail_by_name_not_by_crash",
        "3": "test_the_three_caller_classes_measure_gate_cc_akien",
    },
}


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


def _caller_in(*wrapper: str) -> dict | None:
    cmd = [*wrapper, "env", f"PYTHONPATH={REPO}", sys.executable, "-m", "cairn.tools.artifact",
           "caller"]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        print(f"      (wrapper failed: {r.stderr.strip()[:300]})")
        return None
    return json.loads(r.stdout)


def _live_akien_pids() -> list[int]:
    base = Path("/sys/fs/cgroup/user.slice/user-1000.slice")
    pids = []
    for d in list(base.glob("session-*.scope")) + list(base.glob("user@*.service/app.slice/app-*.scope")):
        try:
            pids += [int(x) for x in (d / "cgroup.procs").read_text().split()[:2]]
        except (OSError, ValueError):
            continue
    return pids


LINUX_ONLY = ("a process under a transient cairn-*.service reads as GATE",
              "a live process in a login-session or desktop-app scope reads as AKIEN",
              "test_the_three_caller_classes_measure_gate_cc_akien")


def _has_linux_callers() -> bool:
    """The caller teeth drive systemd-run and read /sys/fs/cgroup; a box without both cannot
    measure them (ticket 2a208067d036)."""
    return sys.platform.startswith("linux") and shutil.which("systemd-run") is not None \
        and Path("/sys/fs/cgroup").is_dir()


def _linux_caller_teeth(me: dict) -> None:
    tag = f"cairn-proof-artifact-{os.getpid()}"
    gate = _caller_in("systemd-run", "--user", "--wait", "--pipe", "--quiet", "--unit",
                      f"{tag}.service", "-p", f"WorkingDirectory={REPO}")
    check("a process under a transient cairn-*.service reads as GATE",
          gate is not None and gate["class"] == "gate", f"{gate and gate['unit']}")

    if me["class"] == "cc":
        forged = _caller_in("systemd-run", "--user", "--scope", "--quiet", "--unit",
                            f"app-proof-forged-{os.getpid()}.scope")
        check("a scope CC forges to look like a desktop app STILL reads as cc — by ancestry",
              forged is not None and forged["class"] == "cc" and "via_ancestor" in forged,
              f"{forged and forged.get('via_ancestor')}")
        child = _caller_in()
        check("a plain child of CC reads as cc", child is not None and child["class"] == "cc")

    pids = _live_akien_pids()
    hits = [(p, A.classify(A.ancestry(p)[0]["cgroup"])["class"]) for p in pids if A.ancestry(p)]
    check("a live process in a login-session or desktop-app scope reads as AKIEN",
          bool(hits) and all(c == "akien" for _, c in hits), f"{hits[:4]}")
    check("no live hand-at-a-terminal process has a cc ancestor (the ancestry walk does not "
          "over-reach)", all(not any(a["class"] == "cc" for a in A.ancestry(p)[1:]) for p in pids))
    check("test_the_three_caller_classes_measure_gate_cc_akien",
          gate is not None and gate["class"] == "gate" and me["class"] in ("cc", "akien", "gate")
          and bool(hits) and all(c == "akien" for _, c in hits),
          f"gate={gate and gate['class']} me={me['class']} akien={len(hits)} live pids")


def _name_the_unran_linux_teeth() -> None:
    for name in LINUX_ONLY:  # named reds: an unmeasured tooth is not green, and not a crash
        check(name, False, "UNRAN: needs linux cgroups and systemd-run, not measurable on this box")


def _the_unran_linux_teeth_are_named_on_every_box() -> None:
    """Clause 1 of ticket 2a208067d036, measurable on any box: the off-Linux branch, driven with
    a recording check, names every Linux-only tooth as a red carrying the reason, and raises
    nothing. On Windows the real branch has already run it; here it runs against a recorder."""
    seen: list[tuple[str, bool, str]] = []
    real = globals()["check"]
    globals()["check"] = lambda name, ok, detail="": seen.append((name, ok, detail))
    try:
        _name_the_unran_linux_teeth()
        err = ""
    except Exception as exc:  # noqa: BLE001 — a crash is the red this tooth exists to show
        err = repr(exc)
    finally:
        globals()["check"] = real
    check("test_off_linux_the_linux_only_teeth_fail_by_name_not_by_crash",
          not err and [n for n, _, _ in seen] == list(LINUX_ONLY)
          and all(not ok and "needs linux cgroups" in d for _, ok, d in seen),
          err or f"{[(n, ok) for n, ok, _ in seen]}")


def teeth_callers() -> None:
    print("THE CALLER — measured over real processes, never over a string the proof made up")
    me = A.caller()
    # The verdict gate re-runs this proof under its own cairn-*.service unit (ticket
    # 23c822fe8095, FIXME 1), so the gate is a real starter too: the claim is that this process
    # classifies by its real ancestry as one of the three, never that only CC or Akien runs it.
    check("this proof's own process classifies as cc, akien or gate (it was started by one of them)",
          me["class"] in ("cc", "akien", "gate"), f"{me['class']} {me['cgroup']}")

    if _has_linux_callers():
        _linux_caller_teeth(me)
    else:
        _name_the_unran_linux_teeth()
    _the_unran_linux_teeth_are_named_on_every_box()

    from cairn.tools.base.script_argv import bash_script_argv
    r = subprocess.run([*bash_script_argv(REPO / "bin" / "cairn"), "artifact", "caller"],
                       capture_output=True, text=True, timeout=60)
    try:
        via_cli = json.loads(r.stdout)
    except ValueError:
        via_cli = {}
    check("test_the_cli_front_door_answers_caller_with_a_measured_class",
          r.returncode == 0 and via_cli.get("class") == me["class"]
          and (bool(via_cli.get("cgroup")) or not _has_linux_callers()),  # no cgroup off Linux
          f"rc={r.returncode} class={via_cli.get('class')}")

    print("THE CLASSIFIER — pinned over text so the rule is readable")
    check("cairn-web-server.service → gate",
          A.classify("/user.slice/user-1000.slice/user@1000.service/app.slice/cairn-web-server.service")["class"] == "gate")
    check("superclaude-<pid>.scope → cc",
          A.classify("/user.slice/user-1000.slice/user@1000.service/app.slice/superclaude-42.scope")["class"] == "cc")
    check("app-org.kde.konsole-….scope → akien",
          A.classify("/user.slice/user-1000.slice/user@1000.service/app.slice/app-org.kde.konsole-7e5c.scope")["class"] == "akien")
    check("session-2.scope → akien", A.classify("/user.slice/user-1000.slice/session-2.scope")["class"] == "akien")
    check("a bare slice → unknown", A.classify("/user.slice/user-1000.slice/user@1000.service")["class"] == "unknown")
    check("None → unknown, not a raise", A.classify(None)["class"] == "unknown")
    check("a service that merely mentions cairn is not a gate (cairnx.scope)",
          A.classify("/a/cairn-web.scope")["class"] == "unknown")


def _git(root: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(root), *args], check=True, capture_output=True,
                          text=True).stdout


def _world(tmp: Path) -> tuple[Path, Path]:
    commons = tmp / "CairnCommons"
    (commons / "tickets").mkdir(parents=True)
    cairn = tmp / "cairn"
    (cairn / "cairn" / "tools" / "x").mkdir(parents=True)
    for r in (commons, cairn):
        _git(r, "init", "-q")
        _git(r, "config", "user.email", "proof@cairn")
        _git(r, "config", "user.name", "proof")
        _git(r, "config", "commit.gpgsign", "false")
    A.set_diagnostic_roots({"CairnCommons": commons, "cairn": cairn, "parked": tmp / "parked"})
    # The door reads a ticket's keys from the store charter beside it (1fc53d5d96cc). The
    # charter is itself a record, so it lands through the door and is the journal's first entry.
    A.write_json(commons / "tickets" / "_charter+why.json", {"plan_fields": ["id", "x", "workflow_and_state"]},
                 verb="cast", why="proof: the scratch store's charter")
    return commons, cairn


def teeth_door(tmp: Path) -> None:
    commons, cairn = _world(tmp)
    print("THE DOOR — over a scratch world the proof owns")
    t = commons / "tickets" / "abc123def456-proof.json"
    out = A.write(t, json.dumps({"id": "abc123def456"}, indent=2) + "\n", verb="cast", why="proof: first write")
    check("a write to a record is journaled", out["journaled"] and out["entry"]["verb"] == "cast")
    e = out["entry"]
    check("the entry names the caller class from the kernel", e["caller"]["class"] in ("cc", "akien", "gate"))
    check("the entry carries a stack whose top frame is this proof, not the door",
          bool(e["stack"]) and "test_artifact_door.py" in e["stack"][0], e["stack"][0])
    check("the first entry chains from genesis",
          A.read_journal(commons)[0]["prev"] == "genesis" and e["sha_before"] == "absent")
    check("the bytes on disk hash to sha_after", A._sha(t.read_bytes()) == e["sha_after"])
    again = A.write(t, json.dumps({"id": "abc123def456"}, indent=2) + "\n", verb="cast", why="proof: same bytes")
    check("writing the same bytes is a no-op with no entry", not again["journaled"] and again.get("unchanged"))
    out2 = A.write(t, json.dumps({"id": "abc123def456", "x": 1}, indent=2) + "\n", verb="append", why="proof: second write")
    check("the second entry's prev is the first entry's sha", out2["entry"]["prev"] == e["entry"])
    check("the second entry's sha_before is the first's sha_after", out2["entry"]["sha_before"] == e["sha_after"])
    check("verify_chain is clean", A.verify_chain(commons) == [])
    scratch = A.write(tmp / "scratch.json", "{}", verb="cast", why="proof: outside")
    check("a write outside the jurisdiction is plain and says journaled: False",
          not scratch["journaled"] and (tmp / "scratch.json").exists())
    lab = A.write(commons / "intentions-congruency-lab" / "x.json", "{}", verb="cast", why="derived")
    check("a derived surface (intentions-congruency-lab) is not a record", not lab["journaled"])
    try:
        A.write(commons / "tickets" / "nowhy.json", "{}", verb="cast", why="")
        check("a write with no why is refused", False)
    except A.Refused as exc:
        check("a write with no why is refused", "why" in str(exc))
    try:
        A.write(commons / "tickets" / "badverb.json", "{}", verb="scribble", why="x")
        check("an unknown verb is refused", False)
    except A.Refused:
        check("an unknown verb is refused", True)

    print("THE WRITERS — the standing doors ride this one, each with its own verb")
    from cairn.tools.validation_store import validation_store as vs
    from cairn.tools.charter import projector
    from cairn.tools.base import transitions
    proof = cairn / "cairn" / "tools" / "x" / "proofs" / "test_x.py"
    proof.parent.mkdir(parents=True, exist_ok=True)
    proof.write_text("# stand-in proof\n")
    rec = {"claim": "x", "caller": "proof", "date": "2026-09-13", "method": "stand-in", "verdict": "green",
           "evidence": {"returncode": 0, "source_fingerprint": vs.source_fingerprint(str(proof))},
           "falsifier": "none", "horizon": "none"}
    sealed = Path(vs.persist_validation(rec, proof_path=str(proof)))
    ent = [e for e in A.read_journal(cairn) if e["path"].endswith("validations/test_x.json")]
    check("test_the_seal_store_writes_its_validation_through_the_door",
          sealed.exists() and ent and ent[-1]["verb"] == "seal" and ent[-1]["sha_after"] == A._sha(sealed.read_bytes()),
          f"{len(ent)} entries, verb={ent and ent[-1]['verb']}")
    hp, sp = cairn / "cairn" / "tools" / "x" / "history.json", cairn / "cairn" / "tools" / "x" / "state.json"
    projector.append_entry(str(hp), str(sp), {"standing": "one"})
    j = A.read_journal(cairn)
    hv = [e["verb"] for e in j if e["path"].endswith("x/history.json")]
    sv = [e["verb"] for e in j if e["path"].endswith("x/state.json")]
    check("test_the_projector_writes_history_and_state_through_the_door",
          hv == ["append"] and sv == ["append"] and A.last_sha(j, "cairn/tools/x/state.json") == A._sha(sp.read_bytes()),
          f"history={hv} state={sv}")
    transitions._write_ticket(t, {"id": "abc123def456", "workflow_and_state": "proof@v1: [A] -> B"},
                              False, True, why="proof: phase")
    tv = [e for e in A.read_journal(commons) if e["path"] == "tickets/abc123def456-proof.json"]
    check("test_the_phase_writer_moves_a_ticket_through_the_door",
          tv and tv[-1]["verb"] == "phase" and tv[-1]["sha_after"] == A._sha(t.read_bytes()),
          f"verb={tv and tv[-1]['verb']}")
    A.write(t, json.dumps({"id": "abc123def456", "x": 1}, indent=2) + "\n", verb="cast", why="proof: restore the shape the teeth below expect")

    print("THE MODE — the validation store's 0444 seals keep their mode")
    v = cairn / "cairn" / "tools" / "x" / "validations" / "test_x.json"
    A.write(v, "{}", verb="seal", why="proof: seal", mode=0o444)
    A.write(v, json.dumps({"a": 1}, indent=2), verb="seal", why="proof: reseal")
    check("a 0444 record rewritten through the door stays 0444", (v.stat().st_mode & 0o777) == 0o444)

    print("THE COMMIT QUESTION — staged bytes must be the journal's last sha_after")
    _git(commons, "add", "-A")
    check("a record written through the door passes check_staged", A.check_staged("CairnCommons") == [])
    check("check_staged staged the journal too",
          ".artifact-journal.jsonl" in _git(commons, "diff", "--cached", "--name-only"))
    _git(commons, "commit", "-qm", "through the door")
    t.write_text('{"id": "abc123def456", "hand": true}\n')
    _git(commons, "add", "-A")
    faults = A.check_staged("CairnCommons")
    check("test_a_record_edited_around_the_door_is_refused_at_the_commit_question",
          len(faults) == 1 and "changed around the door" in faults[0], faults and faults[0][:80])
    check("the refusal names the way through", faults and "cairn artifact hand-edit" in faults[0])
    never = commons / "tickets" / "never.json"
    never.write_text("{}")
    _git(commons, "add", "-A")
    faults = A.check_staged("CairnCommons")
    check("a record never journaled is refused as such", any("NEVER journaled" in f for f in faults))
    never.unlink()
    _git(commons, "add", "-A")

    print("THE HAND EDIT — parked, restored, then approved only by a measured hand")
    park = A.park_hand_edit(t, why="proof: I edited it by hand")
    check("test_hand_edit_parks_and_the_record_stays_at_its_journaled_bytes",
          A._sha(t.read_bytes()) == A.last_sha(A.read_journal(commons), "tickets/abc123def456-proof.json"))
    check("the park is listed", any(p["id"] == park["parked"] for p in A.parked()))
    rec = next(p for p in A.parked() if p["id"] == park["parked"])
    check("the parked record carries the proposed bytes", '"hand": true' in rec["proposed"])
    me = A.caller()["class"]
    try:
        A.approve(park["parked"], "fine by me")
        approved = True
    except A.Refused as exc:
        approved = False
        msg = str(exc)
    if me == "akien":
        check("approve from a hand at a terminal journals verb=hand-edit", approved and
              A.read_journal(commons)[-1]["verb"] == "hand-edit")
        check("the approved bytes now stand", '"hand": true' in t.read_text())
    else:
        check(f"approve from {me} is REFUSED by measurement", not approved and "only" in msg, msg[:90])
        check("the record still stands at its journaled bytes", '"hand": true' not in t.read_text())
        out = A.refuse(park["parked"], "proof: refused")
        check("refuse discards the park", out["refused"] == park["parked"] and not A.parked())
    try:
        A.park_hand_edit(t, why="nothing changed")
        check("parking an unchanged record is refused", False)
    except A.Refused:
        check("parking an unchanged record is refused", True)
    _git(commons, "add", "-A")
    check("after the park the tree passes the commit question again", A.check_staged("CairnCommons") == [])

    print("THE CHAIN — a tampered journal is named, not skipped")
    jp = A.journal_path(commons)
    lines = jp.read_text().splitlines()
    tampered = json.loads(lines[0]); tampered["why"] = "rewritten history"
    lines[0] = json.dumps(tampered, ensure_ascii=False, sort_keys=True)
    jp.write_text("\n".join(lines) + "\n")
    faults = A.verify_chain(commons)
    check("test_a_chain_break_is_detected_by_replay", any("entry sha" in f for f in faults), faults and faults[0][:80])
    check("the commit question carries the chain fault", any("journal chain" in f for f in A.check_staged("CairnCommons")))

    print("GENESIS — every standing record gets one entry (the charter, the ticket, old1, old2), "
          "and the second run is a no-op")
    (commons / "tickets" / "old1.json").write_text("{}")
    (commons / "tickets" / "old2.json").write_text("{}")
    jp.unlink()
    g1 = A.genesis("CairnCommons", why="proof: genesis")
    g2 = A.genesis("CairnCommons", why="proof: genesis again")
    check("genesis journals each standing record once", g1["journaled"] == 4 and g2["journaled"] == 0, f"{g1} {g2}")
    check("the genesis chain verifies", A.verify_chain(commons) == [])
    _git(commons, "add", "-A")
    check("after genesis the whole tree passes the commit question", A.check_staged("CairnCommons") == [])

    print("REMOVE and RENAME — through the door, deletions are journaled as absent")
    A.remove(commons / "tickets" / "old2.json", why="proof: remove")
    check("a removed record's last entry says absent",
          A.last_sha(A.read_journal(commons), "tickets/old2.json") == "absent")
    _git(commons, "add", "-A")
    check("a journaled deletion passes the commit question", A.check_staged("CairnCommons") == [])
    A.rename(commons / "tickets" / "old1.json", commons / "tickets" / "old1-moved.json", why="proof: rename")
    check("a rename leaves the old path absent and the new path journaled",
          A.last_sha(A.read_journal(commons), "tickets/old1.json") == "absent"
          and A.last_sha(A.read_journal(commons), "tickets/old1-moved.json") == A._sha(b"{}"))


def teeth_hook(tmp: Path) -> None:
    print("THE HOOK — installed into a scratch clone, it blocks a commit made around the door")
    commons = tmp / "CairnCommons"
    r = subprocess.run([sys.executable, "-m", "cairn.tools.artifact", "install-hook", "CairnCommons"],
                       capture_output=True, text=True, cwd=REPO,
                       env={**os.environ, "PYTHONPATH": str(REPO),
                            "CAIRN_ARTIFACT_ROOTS": json.dumps({"CairnCommons": str(commons)})})
    check("install-hook writes .git/hooks/pre-commit", r.returncode == 0 and
          (commons / ".git" / "hooks" / "pre-commit").exists(), r.stderr[-200:])
    # CAIRN_REPO names the door: the hook's other fallbacks are a sibling or ~/dev/src/cairn,
    # and a box whose checkout is neither would refuse every commit here for that, not for the tooth.
    env = {**os.environ, "PYTHONPATH": str(REPO), "CAIRN_REPO": str(REPO),
           "CAIRN_ARTIFACT_ROOTS": json.dumps({"CairnCommons": str(commons)})}
    (commons / "tickets" / "sneaky.json").write_text("{}")
    _git(commons, "add", "-A")
    # Every commit here names its paths (ticket 23c822fe8095 refuses a shared-index commit),
    # and the refusal asserted is the record check's own, not the shared-index one.
    c = subprocess.run(["git", "-C", str(commons), "commit", "-qm", "sneak", "--", "tickets/sneaky.json"],
                       capture_output=True, text=True, env=env)
    check("test_the_hook_blocks_a_commit_made_around_the_door", c.returncode != 0 and
          "around the artifact door" in c.stderr, c.stderr.strip().splitlines()[-1][:100] if c.stderr else "")
    (commons / "tickets" / "sneaky.json").unlink()
    _git(commons, "add", "-A")
    staged = _git(commons, "diff", "--cached", "--name-only").split()
    c = subprocess.run(["git", "-C", str(commons), "commit", "-qm", "clean", "--", *staged],
                       capture_output=True, text=True, env=env)
    check("git commit of a journaled tree passes the hook", c.returncode == 0, c.stderr[-200:])

    # The tester's pre-commit hook asks this door's commit question before its reseal ladder:
    # that tooth reads the tester's code, so it is the tester's own proof (ticket 4d10cd50ef56,
    # RULE 1): test_the_tester_hook_asks_the_commit_question_first.py in its proofs.


def teeth_beside(tmp: Path) -> None:
    print("THE CHARTER AND THE PROBE — the tool carries its why and its watch beside the code")
    charter = Path(__file__).resolve().parents[1] / "intention+why.json"
    try:
        doc = json.loads(charter.read_text())
    except (OSError, ValueError):
        doc = {}
    check("test_the_charter_stands_beside_the_code_and_names_this_proof",
          bool(doc) and "test_artifact_door.py" in json.dumps(doc) and bool(doc.get("why")),
          f"{charter.name}: {sorted(doc)[:6]}")
    try:
        from cairn.tools.artifact.probes import callers_are_known as probe_mod
        probe = probe_mod.PROBE
        armed = callable(probe.carry) and callable(probe.enough) and callable(probe.trigger)
        detail = f"to={probe.to} horizon={probe.horizon}"
    except Exception as exc:  # noqa: BLE001 — an unimportable probe is the red
        armed, detail = False, repr(exc)[:120]
    check("test_the_probe_is_armed_with_carry_and_enough", armed, detail)

    print("THE LIVE JOURNALS — cairn's verifies from genesis, and the scratch world above never touched either")
    cj = A.journal_path(A.roots()["cairn"])
    cj_faults = A.verify_chain(A.roots()["cairn"]) if cj.exists() else ["absent"]
    cj_lines = len(cj.read_text().splitlines()) if cj.exists() else 0
    check("test_the_live_cairn_journal_verifies_from_genesis", cj_lines > 0 and cj_faults == [],
          f"{cj_lines} entries, faults={cj_faults[:2]}")
    live = A.journal_path(A.roots()["CairnCommons"])
    after = live.read_text().splitlines() if live.exists() else []
    leaked = [ln for ln in after if str(tmp) in ln or "abc123def456" in ln]
    # The why is "scratch never reaches live", and `leaked` measures exactly that. The live
    # journal's line count is NOT asserted: on a busy fleet box another writer appends during
    # the run (measured 2026-11-13 on the Dell, 37470 -> 37471 lines, 0 scratch entries, under
    # 0f8aefbba1d0's verdict gate), so a count equality over live data is a snapshot that reds
    # for a writer this proof does not own. The count rides the detail as evidence only.
    check("test_a_scratch_world_never_reaches_the_live_journal",
          LIVE_LINES_BEFORE >= 0 and not leaked,
          f"{LIVE_LINES_BEFORE} → {len(after)} lines, {len(leaked)} scratch entries")


LIVE_LINES_BEFORE = -1


def _red_every_declared_tooth(reason: str) -> None:
    """The subject is gone or the world it needs is: every tooth this proof declares reds,
    by name, so proof_coverage and the hollow reading see a red rather than a crash."""
    for name in {n for teeth in PROVES.values() for n in teeth.values()}:
        if name not in FAILURES:
            check(name, False, reason)


def main() -> int:
    global A, LIVE_LINES_BEFORE
    try:
        from cairn.tools.artifact import artifact as door
    except Exception as exc:  # noqa: BLE001 — the reverted world is the case this handles
        print(f"the subject cairn.tools.artifact.artifact does not load: {exc!r}")
        _red_every_declared_tooth("subject absent")
        print(f"\nRED — {len(FAILURES)} failure(s)")
        return 1
    A = door
    try:
        live = A.journal_path(A.roots()["CairnCommons"])
        LIVE_LINES_BEFORE = len(live.read_text().splitlines()) if live.exists() else 0
        teeth_callers()
        with tempfile.TemporaryDirectory(prefix="cairn-artifact-door-proof-") as d:
            tmp = Path(d)
            try:
                teeth_door(tmp)
                teeth_hook(tmp)
            finally:
                A.set_diagnostic_roots(None)
            teeth_beside(tmp)
    except Exception as exc:  # noqa: BLE001 — a subject whose world was taken away
        print(f"the teeth could not run to the end: {exc!r}")
        _red_every_declared_tooth(f"aborted: {type(exc).__name__}")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
