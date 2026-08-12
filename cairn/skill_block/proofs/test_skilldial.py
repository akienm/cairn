"""PROOF — the usage roster counts what it can and refuses to invent the rest.

Teeth a hollow build could not pass (Law 8), every root injected.

THE TOOTH THIS FILE EXISTS FOR is the one that would make the whole surface a liability
if it failed: a skill with no door must never render as **0**. Akien's disuse clause
says a skill "could wind up being excised through disuse" — so a surface that prints 0
for a skill nobody ever wired hands him evidence for excising a door that was never
tried. Unmeasured and zero are different facts and the renderer may not collapse them
(Law 7 at a diagnostic surface).

Two more that keep it honest: the roster IS the directory (no registry to fall out of
sync), and reading never writes (the dial's own law — a metric that disturbs what it
counts is not a metric).

Run bare:  PYTHONPATH=$HOME/dev/src/cairn python3 cairn/skill_block/proofs/test_skilldial.py
Run twice; never trust the first green.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_REPO))

from cairn.skill_block import skill_block as sb          # noqa: E402
from cairn.skill_block import counters                    # noqa: E402
from cairn.skill_block import skilldial                   # noqa: E402
from cairn.tester.scratch import scratch_dir                # noqa: E402

PASSES = 0


def ok(name: str, cond: bool, detail: str = ""):
    global PASSES
    if not cond:
        print(f"RED  {name}  {detail}")
        raise SystemExit(1)
    PASSES += 1
    print(f"  ok {name}")


def main() -> int:
    tmp = scratch_dir("skilldial-proof-")
    skills, traces, berths = tmp / "skills", tmp / "traces", tmp / "berths"

    # A tenant, a non-tenant, and a skill with no charter at all.
    (skills / "wired").mkdir(parents=True)
    (skills / "wired" / "intention+why.json").write_text(json.dumps(
        {"input_contract": {"thing": "why the thing is required"}}))
    (skills / "unwired").mkdir(parents=True)
    (skills / "unwired" / "intention+why.json").write_text(json.dumps(
        {"what": "a skill that fires no door"}))
    (skills / "charterless").mkdir(parents=True)

    kw = dict(skills_root=skills, berths=berths, trace_root=traces)

    # ── the roster is the directory ───────────────────────────────────────────
    ok("roster IS the directory listing — no registry",
       skilldial.skill_names(skills) == ["charterless", "unwired", "wired"])

    rows = {r["skill"]: r for r in skilldial.roster(skills_root=skills, traces=traces)}
    ok("every skill on disk gets a row", set(rows) == {"charterless", "unwired", "wired"})

    # ── THE TOOTH: unmeasured is not zero ─────────────────────────────────────
    ok("a non-tenant is marked NOT countable", rows["unwired"]["countable"] is False)
    ok("a non-tenant carries NO count fields at all",
       "firings" not in rows["unwired"], str(rows["unwired"]))
    ok("its why says so in words", "NOT zero uses" in rows["unwired"]["why_not_countable"])
    ok("a charterless skill is refused differently from an unwired one",
       rows["charterless"]["why_not_countable"] != rows["unwired"]["why_not_countable"])

    rendered = skilldial.render(list(rows.values()))
    unwired_line = next(l for l in rendered.splitlines() if l.startswith("unwired"))
    ok("THE RENDER TOOTH: the uncountable row prints no zero",
       "0" not in unwired_line, unwired_line)
    ok("the uncountable row says 'not countable' out loud",
       "not countable" in unwired_line)
    ok("the summary refuses to add the two kinds together",
       "not zero uses" in rendered)

    # ── a tenant, never fired, IS a zero — and that is a different fact ───────
    ok("a wired skill with no firings counts 0", rows["wired"]["firings"] == 0)
    ok("never-fired is rendered as 'never', not blank",
       "never" in next(l for l in rendered.splitlines() if l.startswith("wired")))
    ok("zero and uncountable render differently",
       next(l for l in rendered.splitlines() if l.startswith("wired")) !=
       next(l for l in rendered.splitlines() if l.startswith("unwired")))

    # ── the numbers are the trace's, re-derived ───────────────────────────────
    packet = {"thing": "x", "bullets": [{"text": "t", "stratum": "code"}],
              "exit": "routed_forward"}
    sb.fire("wired", packet, **kw)
    sb.fire("wired", packet, **kw)
    try:
        sb.fire("wired", {"bullets": [{"text": "t", "stratum": "code"}]}, **kw)
    except Exception:
        pass

    after = {r["skill"]: r for r in skilldial.roster(skills_root=skills, traces=traces)}
    ok("firings counted", after["wired"]["firings"] == 3, str(after["wired"]))
    ok("refusals counted separately", after["wired"]["send_backs"] == 1)
    ok("findings counted", after["wired"]["findings"] == 2)
    ok("last_fired appears once it has fired", after["wired"]["last_fired"] is not None)
    ok("last_fired is an ISO timestamp", after["wired"]["last_fired"].startswith("20"))
    ok("the non-tenant is STILL not countable after real traffic elsewhere",
       after["unwired"]["countable"] is False)
    ok("match_rate is None until a verdict exists — not 0%",
       after["wired"]["match_rate"] is None)

    # ── reading never writes ──────────────────────────────────────────────────
    trace_file = traces / "skill:wired.jsonl"
    before = trace_file.read_bytes()
    for _ in range(3):
        skilldial.roster(skills_root=skills, traces=traces)
    ok("THE PURE-READ TOOTH: the trace is byte-identical after three reads",
       trace_file.read_bytes() == before)

    # ── COUNTED ELSEWHERE (2026-08-04) ────────────────────────────────────────
    #
    # THE MEASUREMENT THAT ADDED THIS SECTION: five of the six skills this file called
    # "not countable" had been recording every firing all along — in git, in chart's own
    # packet berths, in the commons, in the tenant trees. The roster saw 19 of ~408. The
    # fix that looked obvious (give the six a contract) would have built six doors to
    # re-derive existing counts and berthed chart and commit TWICE per firing.
    #
    # So a third row shape exists now, and the teeth below exist because it is the row
    # shape most able to lie: it carries a real number, which makes every EMPTY column
    # beside it look like a measurement too.

    (skills / "elsewhere").mkdir()
    packets = tmp / "packets"
    packets.mkdir()
    for door, n in (("alpha", 3), ("beta", 2)):
        for i in range(n):
            (packets / f"{door}-2026080{i+1}T12000{i}-abc.json").write_text("{}")
    (skills / "elsewhere" / "intention+why.json").write_text(json.dumps(
        {"counted_by": {"reader": "files", "address": "tmp/packets",
                        "group_by_prefix": True,
                        "what_it_counts": "one packet per firing"}}))

    (skills / "dark").mkdir()
    (skills / "dark" / "intention+why.json").write_text(json.dumps(
        {"counted_by": {"reader": "none", "address": None,
                        "what_it_counts": "a mandatory artifact exists at a store this "
                                          "roster cannot filter down to"}}))

    # A charter that declares no reader AND says nothing about what it counts. The
    # roster owes the reader a different sentence here — there is nothing to quote.
    (skills / "mute").mkdir()
    (skills / "mute" / "intention+why.json").write_text(json.dumps(
        {"counted_by": {"reader": "none", "address": None}}))

    (skills / "bogus").mkdir()
    (skills / "bogus" / "intention+why.json").write_text(json.dumps(
        {"counted_by": {"reader": "invented-by-the-charter-author", "address": "tmp/x"}}))

    (skills / "gone").mkdir()
    (skills / "gone" / "intention+why.json").write_text(json.dumps(
        {"counted_by": {"reader": "files", "address": "tmp/never-created"}}))

    roots = {"tmp": tmp}
    rows2 = {r["skill"]: r for r in skilldial.roster(
        skills_root=skills, traces=traces, roots=roots)}

    ok("a skill with counted_by is COUNTABLE without any input_contract",
       rows2["elsewhere"]["countable"] is True, str(rows2["elsewhere"]))
    ok("its count is the real one, re-derived from the declared store",
       rows2["elsewhere"]["firings"] == 5)
    ok("`via` names the reader, so the number's provenance rides the row",
       rows2["elsewhere"]["via"] == "files")
    ok("`judged` is False — the store knows THAT, not how well",
       rows2["elsewhere"]["judged"] is False)
    ok("the per-door breakdown survives into detail",
       rows2["elsewhere"]["detail"] == {"alpha": 3, "beta": 2})

    # THE TOOTH THIS SECTION EXISTS FOR. A judged row carries send_backs/findings/
    # match_rate. An elsewhere-counted row must carry NONE of them — because the moment
    # one exists as 0, the surface is claiming this door has never refused anything, for
    # a door that cannot refuse at all.
    for k in ("send_backs", "findings", "match_rate", "approvals"):
        ok(f"THE INVENTED-JUDGEMENT TOOTH: no {k!r} key on an elsewhere-counted row",
           k not in rows2["elsewhere"], str(rows2["elsewhere"]))

    ok("reader 'none' is NOT countable — an undeclared reader is no measurement",
       rows2["dark"]["countable"] is False)
    ok("a declared-but-empty store reads differently from a never-wired skill",
       rows2["dark"]["why_not_countable"] != rows2["unwired"]["why_not_countable"])

    # THE TOOTH THIS SECTION EXISTS FOR (2026-08-11). The roster may say "I cannot count
    # this." It may NOT say "nothing anywhere records this" — that is a claim about the
    # world minted out of a charter's silence, and it was WRONG on the one live skill
    # that carried it: /sail's firings are not merely recorded, they are mandatory.
    dark_why = rows2["dark"]["why_not_countable"]
    for forbidden in ("no store", "leaves no", "anywhere", "no record"):
        ok(f"THE MINTED-ABSENCE TOOTH: reader 'none' never says {forbidden!r}",
           forbidden not in dark_why.lower(), dark_why)
    ok("...it says instead that nothing is DECLARED here",
       "declares no reader" in dark_why.lower(), dark_why)
    ok("...and it quotes the charter's own claim rather than replacing it",
       "a mandatory artifact exists at a store this roster cannot filter down to"
       in dark_why, dark_why)
    ok("a charter silent on BOTH reader and claim gets a different sentence — the "
       "silence itself is named as the thing to fix",
       "silent on what it counts" in rows2["mute"]["why_not_countable"] and
       rows2["mute"]["why_not_countable"] != dark_why,
       rows2["mute"]["why_not_countable"])
    ok("an unimplemented reader is refused as a CHARTER defect, not as zero",
       rows2["bogus"]["countable"] is False and
       "not one of" in rows2["bogus"]["why_not_countable"])
    ok("a declared store that is MISSING reads unreadable, never 0",
       rows2["gone"]["countable"] is False and
       "does not exist" in rows2["gone"]["why_not_countable"])
    ok("...and it says which reader was declared, so the fix is obvious in one pass",
       rows2["gone"].get("declared") == "files")

    rendered2 = skilldial.render(list(rows2.values()))
    line = next(l for l in rendered2.splitlines() if l.startswith("elsewhere"))
    ok("THE RENDER TOOTH: the elsewhere row prints its real count", " 5 " in f" {line} ")
    ok("...and three dashes beside it, not three zeros",
       line.count("—") == 3, line)
    ok("a dark row prints no number at all",
       next(l for l in rendered2.splitlines() if l.startswith("dark")).count("—") >= 4)
    ok("the summary separates judged from counted-elsewhere",
       "judged at a door" in rendered2 and "counted elsewhere" in rendered2)
    ok("the summary explains what the beside-dashes mean",
       "not how it went" in rendered2)

    # ── the template filter: a shared folder is not a usage count ─────────────
    #
    # 25 files sit in CairnCommons/notes/ and 3 of them are notes. Counting the folder
    # would have reported /note as the second-busiest skill in Cairn on the strength of
    # 22 hand-written design documents that merely share its address.
    store = tmp / "store"
    store.mkdir()
    (store / "_charter+why.json").write_text(json.dumps(
        {"template": {"id": "string", "text": "the note itself",
                      "relates_to": "optional — what it hangs off"}}))
    (store / "real-1.json").write_text(json.dumps({"id": "a", "text": "t", "date": "2026-08-01"}))
    (store / "real-2.json").write_text(json.dumps({"id": "b", "text": "t", "date": "2026-08-02"}))
    for i in range(6):
        (store / f"held-{i}.json").write_text(json.dumps({"id": f"h{i}", "the_view": "prose"}))

    got = counters.count({"reader": "files", "address": "tmp/store",
                          "conform_to_template": True}, roots=roots)
    ok("THE TEMPLATE TOOTH: only conforming records count", got["firings"] == 2, str(got))
    ok("...and the discarded majority stays visible in detail",
       got["detail"]["in_directory"] == 8 and got["detail"]["conforming"] == 2)
    ok("an optional field is not required to conform",
       "relates_to" not in got["detail"]["required_fields"])
    ok("last_fired comes from the record's own date",
       got["last_fired"] == "2026-08-02")

    no_tmpl = tmp / "no-template"
    no_tmpl.mkdir()
    (no_tmpl / "x.json").write_text("{}")
    got = counters.count({"reader": "files", "address": "tmp/no-template",
                          "conform_to_template": True}, roots=roots)
    ok("conform_to_template with nothing to conform TO is unreadable, not 1",
       "unreadable" in got, str(got))

    # ── an unreachable store is never zero (Law 7) ────────────────────────────
    def _dead_connect():
        raise RuntimeError("could not connect to server: Connection refused")

    got = counters.count({"reader": "tree-nodes", "provenance_kind": "moreabout_signal"},
                         connect=_dead_connect)
    ok("THE LAW 7 TOOTH: a stopped database reads unreadable, NOT 0 signals",
       "unreadable" in got and "firings" not in got, str(got))
    ok("...and says so in words a reader can act on",
       "not zero" in got["unreadable"].lower())

    # ── an address is a rooted token, not a filesystem path ───────────────────
    try:
        counters.resolve("/home/somebody/.cairn/devices/x", roots)
        ok("a bare absolute path is refused as an address", False)
    except counters.Unreadable as exc:
        ok("a bare absolute path is refused as an address", "not one of" in str(exc))

    # ── the live surface still renders ────────────────────────────────────────
    live = skilldial.roster()
    ok("the live roster covers every real skill",
       {"intent", "sorted", "idea", "design", "note"} <= {r["skill"] for r in live})
    ok("the live render does not crash", isinstance(skilldial.render(live), str))
    ok("every live skill is now either countable or says why not",
       all(r["countable"] or r.get("why_not_countable") for r in live))
    # Stated as a PROPERTY, not a census (2026-08-12): this tooth read
    # `== ["sail"]` and went red the moment /whatslefttodo was born declaring
    # honestly why it cannot be counted — i.e. it fired on the condition being
    # SATISFIED. The substance was never the cardinality of the set; it was
    # about /sail, whose records exist and are MANDATORY, so its dash is a
    # reader gap and not a store gap. The invariant tooth above already covers
    # everyone else ("countable or says why not"), so the "only" was a frozen
    # roster carrying no claim the neighbours don't already make.
    ok("LIVE: /sail is still uncountable — and 'cannot count' is the whole claim; "
       "its verdict berths exist and are mandatory",
       "sail" in [r["skill"] for r in live if not r["countable"]],
       str([r["skill"] for r in live if not r["countable"]]))
    sail_why = next(r for r in live if r["skill"] == "sail")["why_not_countable"]
    ok("LIVE: and the roster does not tell Akien /sail leaves no record anywhere",
       "leaves no" not in sail_why and "anywhere" not in sail_why, sail_why)

    print(f"GREEN — {PASSES} teeth")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
