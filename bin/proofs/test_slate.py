#!/usr/bin/env python3
"""Proof for ``bin/cmd/slate`` — the session-open program.

TEETH A HOLLOW BUILD COULD NOT PASS (Law 8). Each case below is written against a
way this could be built that LOOKS right and is not:

  1. NEWEST BY DATE, NOT BY MTIME. The obvious implementation sorts by mtime. On the
     real commons that is WRONG and was already wrong before this program existed:
     fourteen slates were bulk-touched at 2026-07-29 18:03 by an unrelated edit, so
     mtime names the wrong slate as current. The fixture makes the two orders
     DISAGREE — an mtime implementation picks the decoy and fails here.
  2. ORDER IS LOAD-BEARING. Troubles print ABOVE the slate. A build that appends them
     at the bottom passes every content check and still fails the user, because a
     blocked thing learned about after the plan is learned too late.
  3. THE CARRIED SET IS CLOSED. Two real slates have grown extra keys. A build that
     prints "everything in the file" silently widens what every session reads, and
     nothing would ever catch it.
  4. LOUD, NEVER FATAL. Corrupt slate, empty directory, unreachable trouble lane —
     each must SAY SO and still exit 0. A session-open announcement that can kill
     session open is worse than the silence it replaces (Law 7's diagnostic half,
     without taking the session down).
  5. MALFORMED TROUBLES STILL COUNT. The lane's ``live()`` deliberately counts a
     record with a missing standing as live. This program must not re-derive that
     rule or quietly drop the record — that would be a second owner of what LIVE
     means (Law 6).
  6. THE RECEIPT IS FALSIFIABLE, NOT A MARKER. The cheap build prints a fixed
     "complete" string, which would go green over a silently wrong answer — it
     attests that a hook fired, not that a slate was read. Case 10 runs TWO
     different fixtures and requires the receipts to DISAGREE, and requires the
     one live value (the trouble count) to ride along. A hardcoded marker cannot
     pass both halves.
  7. THE HOOK SHAPE IS PINNED WITHOUT A RESTART. Whether the CLI honours the JSON
     is the host's half and needs a real session open. OURS is checkable now:
     stdout must PARSE, must nest the banner under hookSpecificOutput.additional-
     Context, and must name hookEventName. Getting that nesting wrong loses the
     slate silently while still printing a cheerful receipt — so it is pinned.
  8. THE DAY IS NOT THE RANK. Date-then-filename is the build that shipped, and it
     passes every case above because they all use distinct dates. On 2026-08-03 three
     slates shared a date and the alphabetical title tiebreak named the 15:50 one
     current over the 16:41 one — the session opened a voyage behind and did not know
     /challenge had shipped. Case 19 makes filename order and write order DISAGREE, so
     only a written_at build lands right; and when a day genuinely cannot be ranked it
     requires the reader to SAY the answer is a guess (Law 7) without warning on the
     lone unstamped slate that is the whole historical corpus.
  9. THE LAP HIDES BY THE FIELD, NOT BY THE FILE. An adjudication leaves by recording
     `resolved` and STAYING on disk, so the discriminator is that field. A build that
     prints every file passes an "it surfaces" check and never stops shouting; one
     that skips the malformed record loses a decision nobody can read.
 10. THE OPEN LANE IS BOUNDED BY A PREFIX AND KNOWS IT IS PARTIAL. Two hollow builds
     here. First, ``questions/`` holds two kinds — probes and open questions — and the
     store's charter makes the ``open-`` prefix the boundary ("a probe file never wears
     it, an open question always does"); a build that globs ``*.json`` surfaces probes
     as frontier and looks perfectly healthy doing it, so case 19 plants a probe file
     carrying a ``question`` key. Second, the chartered lane is COMPILED from two
     sources and the projector for the charters' ``filed_edges`` half does not exist —
     a build that prints the homeless half silently hands Akien a map with its edges
     cropped off, which is the exact defect the ruling was made against, so the lane is
     required to SAY it is showing half and to name the missing projector.

INVARIANTS, NOT SNAPSHOTS. Every case runs against a temp tree this proof owns, so
nothing here pins a value that legitimately moves. The one live-data assertion (case
9) checks only that the real commons is READABLE and the exit code is 0 — never what
today's slate happens to say.

    python3 bin/proofs/test_slate.py     # exit 0 = green
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent                      # <...>/cairn
SLATE = REPO / "bin" / "cmd" / "slate"

FAILURES: list[str] = []
CHECKS = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global CHECKS
    CHECKS += 1
    if condition:
        print(f"  ok   {label}")
    else:
        print(f"  RED  {label}" + (f"  — {detail}" if detail else ""))
        FAILURES.append(label)


def run(slates_dir: Path | str, troubles_dir: Path | str, *args: str,
        traces_dir: Path | str | None = None,
        adjudications_dir: Path | str | None = None,
        questions_dir: Path | str | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    env["CAIRN_SLATES_DIR"] = str(slates_dir)
    env["CAIRN_TROUBLES_DIR"] = str(troubles_dir)
    # The open lane, same reason as the lap below — and it bites harder here, because
    # this store is meant to GROW: CC files an open question for every "to be clear, I
    # did not do X" (Akien, 2026-08-11), so unset, fixture output would move on an
    # ordinary Tuesday.
    env["CAIRN_QUESTIONS_DIR"] = str(
        questions_dir if questions_dir is not None
        else Path(env["CAIRN_SLATES_DIR"]).parent / "questions_empty")
    # The lap lane, same reason as the trace berth below: unset, every case would read
    # the REAL CairnCommons/adjudications/ and fixture output would move whenever a real
    # item was filed. A proof over live data can only assert invariants, and these cases
    # assert exact text.
    env["CAIRN_ADJUDICATIONS_DIR"] = str(
        adjudications_dir if adjudications_dir is not None
        else Path(env["CAIRN_SLATES_DIR"]).parent / "adjudications_empty")
    # The gate lane reads the trace berth; every case runs against a berth this
    # proof owns (empty unless the case says otherwise) so a REAL pending finding
    # can never rewrite fixture output.
    env["CAIRN_LB_TRACE_ROOT"] = str(traces_dir if traces_dir is not None
                                     else Path(env["CAIRN_SLATES_DIR"]).parent / "traces_empty")
    return subprocess.run([sys.executable, str(SLATE), *args],
                          capture_output=True, text=True, env=env)


def write_slate(d: Path, name: str, **fields) -> Path:
    p = d / name
    p.write_text(json.dumps(fields, ensure_ascii=False), encoding="utf-8")
    return p


def write_trouble(d: Path, name: str, **fields) -> Path:
    d.mkdir(parents=True, exist_ok=True)
    p = d / name
    p.write_text(json.dumps(fields, ensure_ascii=False), encoding="utf-8")
    return p


def main() -> int:
    print(__doc__.strip().splitlines()[0])
    print()

    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)

        # ── 1. newest-by-date, with mtime pointing the OTHER way ──────────────────
        print("1. newest slate is chosen by its date field, not by mtime")
        s1 = root / "slates_a"
        s1.mkdir()
        write_slate(s1, "2026-01-01-decoy.json", id="DECOY", date="2026-01-01",
                    author="CC", at_sea="decoy at sea", next_direction="decoy next",
                    open_threads=["decoy thread"])
        write_slate(s1, "2026-06-06-the-real-one.json", id="REAL", date="2026-06-06",
                    author="CC", at_sea="real at sea", next_direction="real next",
                    open_threads=["real thread"])
        # Make the DECOY the most-recently-modified file — mtime now contradicts date.
        os.utime(s1 / "2026-01-01-decoy.json", (2_000_000_000, 2_000_000_000))
        os.utime(s1 / "2026-06-06-the-real-one.json", (1_000_000_000, 1_000_000_000))
        t_empty = root / "troubles_empty"
        t_empty.mkdir()

        r = run(s1, t_empty)
        check("picks the later DATE", "REAL" in r.stdout, r.stdout[:200])
        check("does NOT pick the later mtime", "DECOY" not in r.stdout,
              "an mtime-sorted build lands here")
        check("exit 0", r.returncode == 0, f"rc={r.returncode}")

        # ── 2. underscore-prefixed store files are not slates ─────────────────────
        print("\n2. _charter+why.json is not mistaken for a slate")
        write_slate(s1, "_charter+why.json", id="CHARTER", date="2099-01-01",
                    at_sea="should never be read")
        r = run(s1, t_empty)
        check("ignores _-prefixed files even with the latest date",
              "CHARTER" not in r.stdout and "REAL" in r.stdout, r.stdout[:200])

        # ── 3. the carried set is CLOSED ──────────────────────────────────────────
        print("\n3. an extra key on a slate does not widen what is read")
        s2 = root / "slates_extra"
        s2.mkdir()
        write_slate(s2, "2026-06-06-extra.json", id="EXTRA", date="2026-06-06",
                    author="CC", at_sea="carried", next_direction="carried",
                    open_threads=["carried"],
                    how_this_session_went="SHOULD-NOT-APPEAR",
                    the_sweep_in_one_line="ALSO-SHOULD-NOT-APPEAR")
        r = run(s2, t_empty)
        check("prints the three ratified fields", r.stdout.count("carried") >= 3)
        check("does not print an unratified extra key",
              "SHOULD-NOT-APPEAR" not in r.stdout and "ALSO-SHOULD-NOT-APPEAR" not in r.stdout,
              "a print-everything build lands here")

        # ── 4. a missing ratified field is NAMED, not skipped ─────────────────────
        print("\n4. a slate missing a ratified field says so")
        s3 = root / "slates_missing"
        s3.mkdir()
        write_slate(s3, "2026-06-06-thin.json", id="THIN", date="2026-06-06",
                    author="CC", at_sea="only this one")
        r = run(s3, t_empty)
        check("names the absence", "(absent from this slate)" in r.stdout, r.stdout[:300])
        check("still exit 0", r.returncode == 0)

        # ── 5. corrupt slate: loud, not fatal, and the good one still wins ────────
        print("\n5. a corrupt slate is loud and does not take the run down")
        s4 = root / "slates_corrupt"
        s4.mkdir()
        (s4 / "2026-07-07-broken.json").write_text("{ this is not json", encoding="utf-8")
        write_slate(s4, "2026-06-06-good.json", id="GOOD", date="2026-06-06",
                    author="CC", at_sea="good", next_direction="good",
                    open_threads=["good"])
        r = run(s4, t_empty)
        check("warns about the unreadable file", "unreadable slate" in r.stdout, r.stdout[:300])
        check("still restores the readable one", "GOOD" in r.stdout)
        check("exit 0", r.returncode == 0, f"rc={r.returncode}")

        # ── 6. no slates at all: loud, exit 0 ─────────────────────────────────────
        print("\n6. an empty slate store opens cold, loudly")
        s5 = root / "slates_none"
        s5.mkdir()
        r = run(s5, t_empty)
        check("says no slate was restored", "NO SLATE RESTORED" in r.stdout, r.stdout[:300])
        check("points at the fallback", "MAP.md" in r.stdout)
        check("exit 0 — never wedges session open", r.returncode == 0, f"rc={r.returncode}")

        # ── 7. troubles print ABOVE the slate ─────────────────────────────────────
        print("\n7. live troubles print above the slate, and malformed ones still count")
        t_live = root / "troubles_live"
        write_trouble(t_live, "a-real-one.json", id="a-real-one", standing="OPEN",
                      count=3, why="WHY-MARKER-ONE")
        write_trouble(t_live, "no-standing-at-all.json", id="no-standing-at-all",
                      count=1, why="WHY-MARKER-TWO")
        write_trouble(t_live, "already-cleared.json", id="already-cleared",
                      standing="CLEARED", count=9, why="WHY-MARKER-CLEARED")
        r = run(s1, t_live)
        i_trouble = r.stdout.find("LIVE TROUBLE")
        i_slate = r.stdout.find("SLATE  ")
        check("troubles section exists", i_trouble != -1)
        check("troubles come BEFORE the slate", -1 < i_trouble < i_slate,
              f"trouble@{i_trouble} slate@{i_slate}")
        check("a well-formed live trouble is shown", "WHY-MARKER-ONE" in r.stdout)
        check("a trouble with NO standing is still live", "WHY-MARKER-TWO" in r.stdout,
              "re-deriving LIVE here would be a second owner of it")
        check("a CLEARED trouble is not shown", "WHY-MARKER-CLEARED" not in r.stdout)
        check("the count rides along", "[3x]" in r.stdout, r.stdout[:400])

        # ── 8. zero troubles is stated, not silent ────────────────────────────────
        print("\n8. zero live troubles is announced, not silence")
        r = run(s1, t_empty)
        check("says the inbox is empty", "no live troubles" in r.stdout, r.stdout[:300])

        # ── 9. the real commons is readable and the exit code holds ───────────────
        #     INVARIANT ONLY: never asserts what today's slate says.
        print("\n9. against the real commons: readable, exit 0, both sections present")
        r = subprocess.run([sys.executable, str(SLATE)], capture_output=True, text=True)
        check("exit 0 on the live tree", r.returncode == 0, f"rc={r.returncode} err={r.stderr[:200]}")
        check("emits a session-open banner", "CAIRN — SESSION OPEN" in r.stdout)
        check("emits a trouble verdict (either shape)",
              ("LIVE TROUBLE" in r.stdout) or ("no live troubles" in r.stdout))
        check("carries the Law 3 footer", "POINTER TO VERIFY" in r.stdout)

        # ── 10. --hook: the JSON shape, and a receipt that can be WRONG ───────────
        print("\n10. --hook emits the host's JSON shape with a falsifiable receipt")
        r = run(s1, t_live, "--hook")
        check("exit 0 under --hook", r.returncode == 0, f"rc={r.returncode} err={r.stderr[:200]}")
        try:
            payload = json.loads(r.stdout)
        except Exception as exc:
            payload = None
            check("stdout parses as JSON", False, f"{exc} — stdout={r.stdout[:200]}")
        if payload is not None:
            check("stdout parses as JSON", True)
            hso = payload.get("hookSpecificOutput") or {}
            check("names the hook event", hso.get("hookEventName") == "SessionStart",
                  f"got {hso.get('hookEventName')!r}")
            ctx = hso.get("additionalContext") or ""
            check("the BANNER rides in additionalContext", "CAIRN — SESSION OPEN" in ctx,
                  "wrong nesting loses the slate silently — stdout={}".format(r.stdout[:200]))
            check("the slate rides in additionalContext, not the receipt", "REAL" in ctx)
            check("troubles still precede the slate inside the context",
                  -1 < ctx.find("LIVE TROUBLE") < ctx.find("SLATE  "))

            receipt = payload.get("systemMessage") or ""
            check("a receipt is present", bool(receipt), f"got {receipt!r}")
            check("the receipt names the CHOSEN slate", "REAL" in receipt, f"got {receipt!r}")
            # 3 records, one CLEARED → 2 live. The well-formed one carries count=3
            # OCCURRENCES; a build that reported occurrences, or that counted the
            # cleared record, lands here. These two numbers being different is the
            # whole reason this tooth is worth having.
            check("the receipt counts LIVE TROUBLES, not occurrences",
                  "2 live trouble(s)" in receipt,
                  f"got {receipt!r} — expected 2 live (3 records, 1 CLEARED); "
                  f"'3' would be the occurrence count of one record")
            check("the receipt is not the whole banner", "CAIRN — SESSION OPEN" not in receipt)

            # THE ANTI-MARKER TOOTH: a different tree must produce a different receipt.
            r2 = run(s5, t_empty, "--hook")           # s5 = the EMPTY slate store
            receipt2 = (json.loads(r2.stdout) or {}).get("systemMessage") or ""
            check("a different tree yields a DIFFERENT receipt", receipt2 != receipt,
                  f"a hardcoded marker lands here: {receipt2!r}")
            check("the empty store is named in the receipt", "NO SLATE RESTORED" in receipt2,
                  f"got {receipt2!r}")
            check("zero troubles reads as zero", "0 live trouble(s)" in receipt2,
                  f"got {receipt2!r}")

        # ── 11. plain text remains the DEFAULT (the fallback diagnostic) ──────────
        print("\n11. without --hook the output is still plain text, not JSON")
        r = run(s1, t_live)
        check("bare run starts with the banner rule", r.stdout.lstrip().startswith("═"),
              r.stdout[:120])
        check("bare run is not JSON", not r.stdout.lstrip().startswith("{"))

        # ── 12. the AT-YOUR-GATE lane: a pending finding reaches session open ─────
        print("\n12. a finding awaiting his verdict prints at the gate, above the slate")
        g1 = root / "traces_pending"
        g1.mkdir()
        (g1 / "some-block.jsonl").write_text(json.dumps({
            "block": "some-block", "event": "finding", "id": "f1e2d3c4b5a6",
            "when": "2026-08-01T10:00:00+00:00", "consumer": "training",
            "data": {"bullets": [{"stratum": "code", "text": "the wire landed"}]},
        }) + "\n", encoding="utf-8")
        r = run(s1, t_empty, traces_dir=g1)
        check("the lane announces the gate", "AT AKIEN'S GATE" in r.stdout, r.stdout[:400])
        check("the finding's block and bullet ride along",
              "some-block" in r.stdout and "the wire landed" in r.stdout)
        check("the answering command is named", "cairn recordverdict" in r.stdout)
        check("the gate prints ABOVE the slate",
              r.stdout.index("AT AKIEN'S GATE") < r.stdout.index("REAL"),
              "a thing only HE can move must not hide below the plan")
        check("exit 0", r.returncode == 0, f"rc={r.returncode}")
        rj = run(s1, t_empty, "--hook", traces_dir=g1)
        receipt = json.loads(rj.stdout)["systemMessage"]
        check("the receipt counts the gate", "1 at the gate" in receipt, receipt)

        # ── 13. zero pending is SILENT (the tool is invisible when it works) ───────
        print("\n13. an empty gate adds nothing to the banner")
        r = run(s1, t_empty)
        check("no gate section", "AT AKIEN'S GATE" not in r.stdout)
        rj = run(s1, t_empty, "--hook")
        receipt = json.loads(rj.stdout)["systemMessage"]
        check("the receipt still carries the moving value", "0 at the gate" in receipt, receipt)

        # ── 14. a broken gate lane is LOUD and never wedges session open ───────────
        print("\n14. an unreadable trace berth says so and the session still opens")
        g_bad = root / "traces_bad"
        g_bad.mkdir()
        (g_bad / "corrupt.jsonl").write_text("this is not json\n", encoding="utf-8")
        r = run(s1, t_empty, traces_dir=g_bad)
        check("the failure is named", "gate lane" in r.stdout, r.stdout[:400])
        check("the banner survives (never-wedge)", "REAL" in r.stdout and r.returncode == 0,
              f"rc={r.returncode}")

        # ── 15. THE LAP ───────────────────────────────────────────────────────────
        # Akien, 2026-08-02: "akien asks what's next? surface what's in that folder."
        # The whole value is that an undecided thing is IMPOSSIBLE to miss at session
        # open, so the teeth are: unresolved surfaces, resolved does not, and the two
        # are told apart by the field rather than by the file existing.
        print("\n15. the lap surfaces what is undecided and hides what is decided")
        a1 = root / "adjudications"
        a1.mkdir()
        (a1 / "_charter+why.json").write_text(
            json.dumps({"store": "adjudications", "what": "CHARTERTEXT"}), encoding="utf-8")
        (a1 / "undecided.json").write_text(json.dumps({
            "id": "LAPOPENZZ", "whose": "akien", "what": "decide the thing",
            "blocks": "BLOCKSTEXT", "resolved": None}), encoding="utf-8")
        (a1 / "decided.json").write_text(json.dumps({
            "id": "LAPSHUTZZ", "whose": "akien", "what": "already settled",
            "resolved": {"at": "2026-08-02", "by": "akien", "became": "TICKET"}}),
            encoding="utf-8")
        r = run(s1, t_empty, adjudications_dir=a1)
        check("an unresolved item surfaces", "LAPOPENZZ" in r.stdout, r.stdout[:400])
        check("what it BLOCKS surfaces (an item that blocks nothing is a note)",
              "BLOCKSTEXT" in r.stdout, r.stdout[:400])
        check("a RESOLVED item does not surface", "LAPSHUTZZ" not in r.stdout,
              "resolved is the discriminator, not the file's existence")
        check("_-prefixed store files are not items", "CHARTERTEXT" not in r.stdout)
        check("the count is the unresolved count", "1 item(s) in the lap" in r.stdout,
              r.stdout[:400])

        print("\n16. an unreadable item counts as UNRESOLVED, and is never silent")
        # Same direction the trouble lane chose: a decision nobody can read is not a
        # decision that got made (Law 7). The dangerous build is the one that skips it.
        a2 = root / "adjudications_bad"
        a2.mkdir()
        (a2 / "corrupt.json").write_text("{not json", encoding="utf-8")
        r = run(s1, t_empty, adjudications_dir=a2)
        check("the unreadable file is named", "unreadable adjudication" in r.stdout,
              r.stdout[:400])
        check("it still COUNTS as in the lap", "1 item(s) in the lap" in r.stdout,
              "a build that skips the malformed case passes hollow (Law 8)")
        check("the banner survives (never-wedge)", "REAL" in r.stdout and r.returncode == 0,
              f"rc={r.returncode}")

        print("\n17. an empty lap — or none at all — is total silence")
        # Both shapes are the same claim: nothing undecided, nothing printed. A fresh
        # clone has no folder yet and must not open the session shouting.
        a3 = root / "adjudications_empty_case"
        a3.mkdir()
        for label, d in (("empty", a3), ("absent", root / "no_such_dir")):
            r = run(s1, t_empty, adjudications_dir=d)
            check(f"{label}: no lap section, no lap receipt, no error claimed",
                  "NEEDS ADJUDICATION" not in r.stdout
                  and "in the lap" not in r.stdout
                  and "unreadable adjudication" not in r.stdout, r.stdout[:300])
            check(f"{label}: the banner survives", "REAL" in r.stdout and r.returncode == 0)

        print("\n18. the receipt carries the lap count (it MOVES, so it cannot be fixed text)")
        r = run(s1, t_empty, "--hook", adjudications_dir=a1)
        payload = json.loads(r.stdout)
        check("systemMessage names the lap", "1 in the lap" in payload.get("systemMessage", ""),
              payload.get("systemMessage", ""))
        check("the banner reaches the model via additionalContext",
              "LAPOPENZZ" in payload.get("additionalContext", "")
              or "LAPOPENZZ" in json.dumps(payload), json.dumps(payload)[:300])

        # ── 19-21: THE OPEN LANE ───────────────────────────────────────────────────
        # Akien, 2026-08-11: "open questions is part of what i should see from the hook
        # where it says 'you still have things to decide on'." Same field-not-file
        # discriminator as the lap, plus two teeth the lap does not need: the `open-`
        # PREFIX is the store charter's own lane boundary ("a probe file never wears
        # it, an open question always does"), and this lane knowingly shows HALF the
        # compiled lane, so it must SAY so — a silently partial frontier is the cropped
        # map the ruling was made against.
        print("\n19. the open lane surfaces the standing frontier and hides the closed")
        q1 = root / "questions"
        q1.mkdir()
        (q1 / "_charter+why.json").write_text(
            json.dumps({"store": "questions", "role": "QCHARTERTEXT"}), encoding="utf-8")
        (q1 / "open-standing.json").write_text(json.dumps({
            "id": "QOPENZZZZ", "raised_by": "CC", "question": "QUESTIONTEXT",
            "whats_beyond": "beyond", "resolved": None}), encoding="utf-8")
        (q1 / "open-settled.json").write_text(json.dumps({
            "id": "QSHUTZZZZ", "raised_by": "CC", "question": "already answered",
            "resolved": {"at": "2026-08-10", "by": "akien"}}), encoding="utf-8")
        (q1 / "tool-shaped-or-domain-shaped.json").write_text(json.dumps({
            "id": "QPROBEZZZ", "probe": "a probe, not an open question",
            "question": "PROBETEXT"}), encoding="utf-8")
        r = run(s1, t_empty, questions_dir=q1)
        check("a standing question surfaces", "QOPENZZZZ" in r.stdout, r.stdout[:500])
        check("its text surfaces, not just its id", "QUESTIONTEXT" in r.stdout)
        check("a RESOLVED question does not surface", "QSHUTZZZZ" not in r.stdout,
              "resolved is the discriminator, not the file's existence")
        check("THE PREFIX TOOTH: a probe file is not in the lane, though it sits in the "
              "same folder and carries a `question` key",
              "QPROBEZZZ" not in r.stdout and "PROBETEXT" not in r.stdout,
              "the `open-` prefix IS the lane boundary (questions/_charter+why.json)")
        check("the store charter is not an item", "QCHARTERTEXT" not in r.stdout)
        check("the count is the standing count", "1 standing" in r.stdout, r.stdout[:500])
        check("THE HALF-LANE TOOTH: it says it is showing half, and names the missing "
              "projector — a silently partial frontier is worse than none",
              "SHOWING HALF THE LANE" in r.stdout
              and "open-the-frontier-projector" in r.stdout, r.stdout[:800])
        check("the lane says who owns it — CC, not Akien (Law 6: the surface is not "
              "the custody)", "CC owns these" in r.stdout, r.stdout[:800])

        print("\n20. an unreadable question counts as STANDING, and is never silent")
        q2 = root / "questions_bad"
        q2.mkdir()
        (q2 / "open-corrupt.json").write_text("{not json", encoding="utf-8")
        r = run(s1, t_empty, questions_dir=q2)
        check("the unreadable file is named", "unreadable open question" in r.stdout,
              r.stdout[:400])
        check("it still COUNTS as standing", "1 standing" in r.stdout,
              "a build that skips the malformed case passes hollow (Law 8)")
        check("the banner survives (never-wedge)", "REAL" in r.stdout and r.returncode == 0,
              f"rc={r.returncode}")

        print("\n21. an empty frontier — or none at all — is total silence, and the "
              "receipt carries the count because it MOVES")
        q3 = root / "questions_empty_case"
        q3.mkdir()
        for label, d in (("empty", q3), ("absent", root / "no_such_q_dir")):
            r = run(s1, t_empty, questions_dir=d)
            check(f"{label}: no open lane, no receipt fragment, no error claimed",
                  "OPEN QUESTIONS" not in r.stdout
                  and "standing" not in r.stdout
                  and "unreadable open question" not in r.stdout, r.stdout[:300])
            check(f"{label}: the banner survives", "REAL" in r.stdout and r.returncode == 0)
        r = run(s1, t_empty, "--hook", questions_dir=q1)
        payload = json.loads(r.stdout)
        check("systemMessage names the open count",
              "1 open question(s)" in payload.get("systemMessage", ""),
              payload.get("systemMessage", ""))
        check("the lane reaches the model via additionalContext",
              "QOPENZZZZ" in json.dumps(payload), json.dumps(payload)[:300])

        # ── 19. within a date, written_at ranks — and an unrankable day says so ────
        # The build this is written against is the one that SHIPPED: date + filename.
        # Every case above uses distinct dates, so it passes all of them and still
        # named the 15:50 slate current over the 16:41 one on 2026-08-03. Here the
        # filename order and the write order DISAGREE, so only a written_at build
        # lands on LATER.
        print("\n22. same-day slates rank by written_at, not by filename")
        s_day = root / "slates_sameday"
        s_day.mkdir()
        write_slate(s_day, "2026-08-03-aaa-the-later-one.json", id="LATER",
                    date="2026-08-03", written_at="2026-08-03T16:41:35", author="CC",
                    at_sea="the later voyage", next_direction="later next",
                    open_threads=["later thread"])
        write_slate(s_day, "2026-08-03-zzz-the-earlier-one.json", id="EARLIER",
                    date="2026-08-03", written_at="2026-08-03T15:50:12", author="CC",
                    at_sea="the earlier voyage", next_direction="earlier next",
                    open_threads=["earlier thread"])
        r = run(s_day, t_empty)
        check("picks the later WRITTEN_AT", "LATER" in r.stdout, r.stdout[:300])
        check("does NOT pick the alphabetically-last filename",
              "EARLIER" not in r.stdout, "a date+filename build lands here")
        check("no ambiguity warning when the winner is stamped",
              "written_at" not in r.stdout, r.stdout[:300])
        check("exit 0", r.returncode == 0, f"rc={r.returncode}")

        # A record written before the stamp existed must not outrank one written after
        # it on the same day — the stamped record is by construction the later writer.
        print("\n    ...and an unstamped record of the same day ranks below a stamped one")
        write_slate(s_day, "2026-08-03-mmm-no-stamp.json", id="UNSTAMPED",
                    date="2026-08-03", author="CC", at_sea="legacy at sea",
                    next_direction="legacy next", open_threads=["legacy thread"])
        r = run(s_day, t_empty)
        check("stamped still wins", "LATER" in r.stdout, r.stdout[:300])
        check("unstamped does not win", "UNSTAMPED" not in r.stdout, r.stdout[:300])

        # The honest half: when the day CANNOT be ranked, the reader must not present
        # its guess as the answer. It still picks (a wrong slate beats no slate) and
        # still exits 0 — it just refuses to be silent about the guess (Law 7).
        print("\n    ...and a day of only-unstamped slates is named as a guess, not an answer")
        s_amb = root / "slates_ambiguous"
        s_amb.mkdir()
        for nm, ident in (("2026-08-03-aaa-one.json", "AMBONE"),
                          ("2026-08-03-zzz-two.json", "AMBTWO")):
            write_slate(s_amb, nm, id=ident, date="2026-08-03", author="CC",
                        at_sea=f"{ident} at sea", next_direction="next",
                        open_threads=["thread"])
        r = run(s_amb, t_empty)
        check("says the ranking fell back to filename order",
              "written_at" in r.stdout and "alphabetical" in r.stdout, r.stdout[:400])
        check("names how many slates share the date", "2 slates share date" in r.stdout,
              r.stdout[:400])
        check("still restores a slate", "AMBTWO" in r.stdout, r.stdout[:300])
        check("still exit 0", r.returncode == 0, f"rc={r.returncode}")

        # No false alarm: one unstamped slate on its day is the whole historical corpus.
        # A build that warns on every legacy slate is noise, and noise gets ignored.
        print("\n    ...and a lone unstamped slate does not cry ambiguity")
        s_lone = root / "slates_lone"
        s_lone.mkdir()
        write_slate(s_lone, "2026-07-01-alone.json", id="ALONE", date="2026-07-01",
                    author="CC", at_sea="alone at sea", next_direction="next",
                    open_threads=["thread"])
        r = run(s_lone, t_empty)
        check("no warning for a lone unstamped slate",
              "alphabetical" not in r.stdout, r.stdout[:300])
        check("restores it", "ALONE" in r.stdout, r.stdout[:200])

    print()
    print(f"{CHECKS - len(FAILURES)}/{CHECKS} green")
    if FAILURES:
        print("RED:")
        for f in FAILURES:
            print(f"  - {f}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
