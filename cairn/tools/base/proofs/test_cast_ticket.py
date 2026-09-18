"""Proof for ticket 23089d52d805 — casting rides a door.

Teeth a hollow build could not pass (Law 8), every one over a SCRATCH commons the proof
owns (``artifact.set_diagnostic_roots``), restored in ``finally`` — the live journal and
the live store are never touched, and no tooth reads them.

1. a cast with every field lands at tickets/<id>-<slug>.json, stamps ``cast`` only when
   absent, and the artifact journal's line — verb cast, sha_before absent, transitions.py's
   own cast_ticket frame — IS the who/when record;
2. a cast lacking three fields with a malformed workflow and an unresolvable exemption is
   refused ONCE naming every lack, and neither the store nor the journal moved;
3. an id the store already holds is refused;
4. the sweep classifies the four arrival shapes and never raises;
5. the WATCHME probe is not enough at nine, not at ten on one day, enough at ten across
   three days, and back down after one hand-dropped file;
6. the callers and residues point at the door (SKILL.md step 5, the sorted charter,
   watchme_spec's residue);
all. the composite: the six above end to end — the one tooth the unnumbered falsifier asks
   for (PROVES keyed "all").

THE SUBJECT IS BOUND AT CALL TIME. ``_S`` resolves ``cast_ticket``, ``sweep_casts`` and the
probe when a tooth asks, so a worktree with the build reverted reds every declared tooth
by name instead of failing at import.

Run bare:  PYTHONPATH=. python3 cairn/tools/base/proofs/test_cast_ticket.py
"""
from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[4]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

PROVES = {
    "23089d52d805": {
        "all": "test_the_door_the_sweep_and_the_watch_end_to_end",
    },
}

FAILURES: list[str] = []


def check(name: str, ok: bool, detail: str = "") -> None:
    print(f"  {'PASS' if ok else 'FAIL'}  {name}" + (f"  — {detail}" if detail else ""))
    if not ok:
        FAILURES.append(name)


class _Subject:
    """The build's names, resolved when a tooth asks — never at import."""

    def __getattr__(self, name):
        if name in ("sweep_casts", "classify"):
            from cairn.tools.base import cast
            return getattr(cast, name)
        if name == "probe":
            from cairn.tools.base.probes import the_casting_door_has_callers
            return the_casting_door_has_callers
        from cairn.tools.base import transitions
        return getattr(transitions, name)


_S = _Subject()

WORKFLOW = "code-seam@v2: THINKME -> [TICKETME:waiting] -> BUILDME -> PROVEME -> PROVED"
DOOR_FRAME = "/cairn/tools/base/transitions.py:1:cast_ticket"


def _fields(tmp: Path, tid: str = "abc123def456", **over) -> dict:
    """A complete cast over scratch berths (the sorted berth agrees with the doc)."""
    sorted_berth = tmp / "sorted.json"
    sorted_berth.write_text(json.dumps({"skill": "sorted", "answers": {
        "workflow": WORKFLOW, "node_class": "code-seam"}}), encoding="utf-8")
    intent_berth = tmp / "intent.json"
    intent_berth.write_text(json.dumps({"skill": "intent"}), encoding="utf-8")
    doc = {
        "id": tid, "title": "Casting rides a door!!  Proof", "date": "2026-09-18",
        "owner": "codemother", "owning_intention": "skills/sorted/intention+why.json",
        "intention": "a ticket enters the store through one judge", "why": "proof",
        "traces_to": "Law 4", "how": "cast_ticket", "falsifier": "DONE when the door refuses",
        "node_class": "code-seam", "workflow_and_state": WORKFLOW,
        "watchme": "none, because cairn/tools/base/transitions.py",
        "sorted_berth": str(sorted_berth), "intent_berth": str(intent_berth),
    }
    doc.update(over)
    return doc


def _journal(A, commons: Path) -> list[dict]:
    return A.read_journal(commons)


def _plant_entry(A, commons: Path, path: str, at: str, stack: list[str], verb: str = "cast",
                 sha_before: str = "absent") -> None:
    """A synthetic journal line in the shape the door leaves — used ONLY for the probe's
    calendar teeth, and only after tooth 1 has pinned that the real door's line classifies
    the same way."""
    jp = A.journal_path(commons)
    with jp.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"at": at, "path": path, "verb": verb, "sha_before": sha_before,
                             "sha_after": "x", "stack": stack, "caller": {"class": "cc"}}) + "\n")


# --------------------------------------------------------------------------- the teeth


def test_a_cast_lands_and_the_journal_line_is_the_record(A, tmp: Path, commons: Path) -> None:
    tickets = commons / "tickets"
    doc = _fields(tmp)
    before = len(_journal(A, commons))
    path = _S.cast_ticket(doc, actor="proof", tickets_dir=tickets)
    check("the cast lands at tickets/<id>-<slug>.json",
          path == tickets / "abc123def456-casting-rides-a-door-proof.json" and path.is_file(),
          str(path))
    check("the slug lower-cases and collapses non-alphanumerics",
          _S._slug("Casting rides a door!!  Proof") == "casting-rides-a-door-proof")
    written = json.loads(path.read_text(encoding="utf-8"))
    check("cast is stamped with today's date when absent",
          written.get("cast") == __import__("datetime").date.today().isoformat(), str(written.get("cast")))
    check("no other key was touched",
          {k: v for k, v in written.items() if k != "cast"} == {k: v for k, v in doc.items() if k != "cast"})
    entries = _journal(A, commons)
    e = entries[-1]
    check("exactly one journal line was added", len(entries) == before + 1)
    check("the line is verb cast, sha_before absent, why naming id title actor",
          e["verb"] == "cast" and e["sha_before"] == "absent"
          and e["why"] == "cast_ticket: abc123def456 Casting rides a door!!  Proof by proof", e.get("why"))
    check("the line carries transitions.py's own cast_ticket frame",
          _S.classify(e) == "through_the_door", str(e.get("stack", [])[:1]))
    dated = _fields(tmp, tid="abc123def457", cast="2026-01-01")
    p2 = _S.cast_ticket(dated, actor="proof", tickets_dir=tickets)
    check("a cast that already carries its date keeps it",
          json.loads(p2.read_text())["cast"] == "2026-01-01")


def test_a_multi_lack_cast_is_refused_naming_every_lack_and_writes_nothing(A, tmp: Path, commons: Path) -> None:
    tickets = commons / "tickets"
    doc = _fields(tmp, tid="0123456789ab", workflow_and_state="not a workflow",
                  intent_berth="none, because we talked about it")
    del doc["why"]
    doc["how"] = "   "
    doc["falsifier"] = None
    files_before = sorted(p.name for p in tickets.iterdir())
    lines_before = len(_journal(A, commons))
    try:
        _S.cast_ticket(doc, actor="proof", tickets_dir=tickets)
        check("a malformed cast is refused", False, "it landed")
        return
    except _S.CastRefused as exc:
        refused = exc
        lacks = refused.lacks
    check("the refusal is a CastRefused that is an IllegalTransition",
          isinstance(lacks, list) and issubclass(_S.CastRefused, _S.IllegalTransition))
    named = " | ".join(lacks)
    check("every lack is named in one pass: why, how, falsifier, workflow, the berth's workflow, intent exemption",
          all(x in named for x in ("'why'", "'how'", "'falsifier'", "does not parse",
                                   "answers.workflow differs", "no resolvable referent"))
          and len(lacks) == 6, named)
    check("the message promises nothing was written", "Nothing was written" in str(refused))
    check("the store did not move", sorted(p.name for p in tickets.iterdir()) == files_before)
    check("the journal did not move", len(_journal(A, commons)) == lines_before)
    # the sorted berth that disagrees with the doc is a lack too
    doc2 = _fields(tmp, tid="0123456789ab", node_class="skill")
    try:
        _S.cast_ticket(doc2, actor="proof", tickets_dir=tickets)
        check("a sorted berth whose class disagrees is refused", False)
    except _S.CastRefused as e2:
        check("a sorted berth whose class disagrees is refused",
              any("node_class" in l for l in e2.lacks), str(e2.lacks))


def test_a_held_id_is_refused(A, tmp: Path, commons: Path) -> None:
    tickets = commons / "tickets"
    doc = _fields(tmp, title="a different title for the same id")
    try:
        _S.cast_ticket(doc, actor="proof", tickets_dir=tickets)
        check("an id the store holds is refused", False, "it landed")
    except _S.CastRefused as e:
        check("an id the store holds is refused",
              any("already held" in l for l in e.lacks), str(e.lacks))
    try:
        _S.cast_ticket(_fields(tmp, tid="ABC123DEF456"), actor="proof", tickets_dir=tickets)
        check("an id outside twelve lowercase hex is refused", False)
    except _S.CastRefused as e:
        check("an id outside twelve lowercase hex is refused",
              any("twelve lowercase hex" in l for l in e.lacks))


def test_the_sweep_classifies_the_four_arrivals(A, tmp: Path, commons: Path) -> None:
    tickets = commons / "tickets"
    # journaled_beside: a creation through the artifact door by some other frame
    A.write(tickets / "beside000001-beside.json", '{"id": "beside000001"}\n', verb="cast",
            why="proof: beside the door")
    # pre_door: a genesis-first entry over a standing file
    (tickets / "predoor00001-genesis.json").write_text('{"id": "predoor00001"}\n')
    _plant_entry(A, commons, "tickets/predoor00001-genesis.json", "2026-09-01T00:00:00+00:00",
                 ["x.py:1:genesis"], verb="genesis")
    # unjournaled: a hand-dropped file
    (tickets / "handdrop0001-hand.json").write_text('{"id": "handdrop0001"}\n')
    # underscore files are not tickets
    (tickets / "_charter+why.json").write_text("{}\n")
    s = _S.sweep_casts(commons)
    check("the sweep counts the four classes",
          s["counts"] == {"through_the_door": 2, "journaled_beside": 1, "pre_door": 1,
                          "unjournaled": 1}, str(s["counts"]))
    check("the landing is the first door-cast's entry",
          s["landing"] is not None and s["landing"]["path"].startswith("tickets/abc123def456-"))
    check("underscore files are outside the sweep",
          "tickets/_charter+why.json" not in s["tickets"])
    s2 = _S.sweep_casts(tmp / "no-such-commons")
    check("the sweep never raises — an absent commons reads as empty",
          s2["counts"] == {c: 0 for c in s["counts"]} and s2["landing"] is None)
    # THE SHIM IS RUN, NOT READ: bin/cmd/cast is a writes_to file of the build, and the
    # hollow reading named it HOLLOW while no tooth fired it (2026-09-18).
    import subprocess
    shim = REPO / "bin" / "cmd" / "cast"
    run = subprocess.run([str(shim), "--sweep", str(commons)], capture_output=True, text=True,
                         timeout=120, cwd=str(REPO))
    try:
        via_shim = json.loads(run.stdout)
    except ValueError:
        via_shim = {}
    check("bin/cmd/cast --sweep prints the same counts, exit 0",
          run.returncode == 0 and via_shim.get("counts") == s["counts"],
          f"rc={run.returncode} {run.stderr.strip()[-300:]}")
    empty = tmp / "empty_fields.json"
    empty.write_text("{}\n", encoding="utf-8")
    files_before = sorted(p.name for p in tickets.iterdir())
    run = subprocess.run([str(shim), str(empty), "--actor", "proof"], capture_output=True,
                         text=True, timeout=120, cwd=str(REPO))
    check("bin/cmd/cast refuses an empty cast on stderr with exit 1 and writes nothing",
          run.returncode == 1 and "15 lacks" in run.stderr and "Nothing was written" in run.stderr
          and sorted(p.name for p in tickets.iterdir()) == files_before,
          f"rc={run.returncode} {run.stderr.strip()[-200:]}")


def test_the_probe_is_enough_only_at_ten_across_three_days_and_goes_back_down(A, tmp: Path) -> None:
    P = _S.probe
    from cairn.tools.base.probe import Probe
    check("PROBE is a frozen Probe with carry and enough",
          isinstance(P.PROBE, Probe) and callable(P.PROBE.carry) and callable(P.PROBE.enough)
          and P.PROBE.to == "harbor_master")
    c2 = tmp / "probe-commons"
    (c2 / "tickets").mkdir(parents=True)
    A.set_diagnostic_roots({"CairnCommons": c2, "cairn": REPO})
    ctx = lambda: {"roots": {"commons": str(c2)}}  # noqa: E731
    days = ["2026-09-10", "2026-09-11", "2026-09-12"]
    for i in range(9):
        _plant_entry(A, c2, f"tickets/{i:012d}-t.json", f"{days[0]}T0{i}:00:00+00:00", [DOOR_FRAME])
        (c2 / "tickets" / f"{i:012d}-t.json").write_text("{}\n")
    check("not enough at nine", not P.PROBE.enough(ctx()) and P.PROBE.trigger(None, ctx()))
    _plant_entry(A, c2, "tickets/000000000009-t.json", f"{days[0]}T10:00:00+00:00", [DOOR_FRAME])
    (c2 / "tickets" / "000000000009-t.json").write_text("{}\n")
    check("not enough at ten on one day", not P.PROBE.enough(ctx()))
    check("carry names the calendar as the finding",
          "calendar days" in P.PROBE.carry(ctx())["finding"], P.PROBE.carry(ctx())["finding"])
    for i, d in ((10, days[1]), (11, days[2])):
        _plant_entry(A, c2, f"tickets/{i:012d}-t.json", f"{d}T09:00:00+00:00", [DOOR_FRAME])
        (c2 / "tickets" / f"{i:012d}-t.json").write_text("{}\n")
    check("enough at ten consecutive across three distinct days",
          P.PROBE.enough(ctx()) and not P.PROBE.trigger(None, ctx()),
          json.dumps(P.survey_the_casts(c2)))
    (c2 / "tickets" / "hand00000000-dropped.json").write_text("{}\n")
    check("one hand-dropped file takes it back down",
          not P.PROBE.enough(ctx()) and P.PROBE.trigger(None, ctx())
          and "beside" in P.PROBE.carry(ctx())["finding"])
    check("carry names the offending path and the owning ticket",
          "tickets/hand00000000-dropped.json" in P.PROBE.carry(ctx())["counts"]["unjournaled"]
          and "23089d52d805" in str(P.PROBE.carry(ctx())["ticket"]))
    (c2 / "tickets" / "hand00000000-dropped.json").unlink()
    _plant_entry(A, c2, "tickets/beside000000-b.json", f"{days[2]}T10:00:00+00:00", ["scratch/castlib.py:83:cast_ticket"])
    (c2 / "tickets" / "beside000000-b.json").write_text("{}\n")
    check("a creation through some other frame — even one named cast_ticket — takes it back down",
          not P.PROBE.enough(ctx()) and "tickets/beside000000-b.json" in P.PROBE.carry(ctx())["counts"]["journaled_beside"])


def test_the_callers_and_residues_point_at_the_door() -> None:
    skill = (REPO / "skills" / "sorted" / "SKILL.md").read_text(encoding="utf-8")
    check("SKILL.md step 5 fires cairn cast", "cairn cast " in skill and "--actor cc" in skill)
    what = json.loads((REPO / "skills" / "sorted" / "intention+why.json").read_text(encoding="utf-8"))["what"]
    check("the sorted charter's what names cast_ticket", "cast_ticket" in what)
    spec = (REPO / "cairn" / "tools" / "base" / "watchme_spec.py").read_text(encoding="utf-8")
    check("watchme_spec's residue no longer says casting has no chokepoint",
          "CASTING HAS NO" not in spec and "cast_ticket" in spec)


def test_the_door_the_sweep_and_the_watch_end_to_end(A) -> None:
    with tempfile.TemporaryDirectory(prefix="cairn-cast-ticket-proof-") as d:
        tmp = Path(d)
        commons = tmp / "CairnCommons"
        (commons / "tickets").mkdir(parents=True)
        A.set_diagnostic_roots({"CairnCommons": commons, "cairn": REPO})
        try:
            print("1. the cast lands and the journal line is the record")
            test_a_cast_lands_and_the_journal_line_is_the_record(A, tmp, commons)
            print("2. a multi-lack cast is refused once and writes nothing")
            test_a_multi_lack_cast_is_refused_naming_every_lack_and_writes_nothing(A, tmp, commons)
            print("3. a held id is refused")
            test_a_held_id_is_refused(A, tmp, commons)
            print("4. the sweep classifies the four arrivals")
            test_the_sweep_classifies_the_four_arrivals(A, tmp, commons)
            print("5. the probe's enough")
            test_the_probe_is_enough_only_at_ten_across_three_days_and_goes_back_down(A, tmp)
        finally:
            A.set_diagnostic_roots(None)
        print("6. the callers and residues")
        test_the_callers_and_residues_point_at_the_door()


def main() -> int:
    try:
        from cairn.tools.artifact import artifact as A
        live = A.journal_path(A.roots()["CairnCommons"])
        live_before = live.read_bytes() if live.exists() else b""
        test_the_door_the_sweep_and_the_watch_end_to_end(A)
        live_after = live.read_bytes() if live.exists() else b""
        check("the live journal never moved", live_before == live_after)
    except Exception as exc:  # noqa: BLE001 — a subject whose build was taken away
        print(f"the teeth could not run to the end: {exc!r}")
        for name in PROVES["23089d52d805"].values():
            if name not in FAILURES:
                check(name, False, f"aborted: {type(exc).__name__}: {exc}")
    # THE COMPOSITE IS PRINTED ON BOTH OUTCOMES. The hollow reading takes the declared teeth
    # from the PASS lines at HEAD; a composite that only ever printed on failure read as
    # "not green at HEAD" and made every reversion unreadable (measured 2026-09-18).
    for name in PROVES["23089d52d805"].values():
        if name not in FAILURES:
            check(name, not FAILURES, "a tooth inside it failed" if FAILURES else "")
    print(f"\n{'GREEN' if not FAILURES else 'RED — ' + str(len(FAILURES)) + ' failure(s)'}")
    for f in FAILURES:
        print(f"  - {f}")
    return 1 if FAILURES else 0


if __name__ == "__main__":
    raise SystemExit(main())
