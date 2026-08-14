---
name: sail
description: Run the build under the charted course — the voyage a request earns. Starts by firing /chart, then builds inside what that chain settled; the build's own tool calls are the evidence that goes back to the chain.
---

# /sail — run the build under the charted course

You are firing the **build stage**: the voyage a request earns. /sail charts it
and then spends the model inside what that chain settled, under the discipline
that has until now lived in habit (the skill-door fact: discipline in habit
varies; a skill-step fires).

The charter lives beside this file in `intention+why.json`.

ARGUMENTS: the request being built.

## 0. Chart it — /sail RUNS /chart; it no longer requires one

**Fire `/chart <request>` now, as this skill's first act**, and work its seven
stages to their berths before reading step 1. Akien, 2026-08-14: *"slash sail
should just start with slash chart."* The preamble stopped being a thing the
caller must remember to have done and became step 0 of the build. A standalone
/chart is still a real firing — charting without building is a legitimate act —
but /sail never again refuses for want of one, because it makes its own.

**ONE CHART RUN PER VOYAGE.** The earlier design had a second, mid-build run, and
the condition on it was never "a correction appeared" — it was **how much had
changed for that component since the first chart was taken**. Dropped 2026-08-14
as too complicated, by the person who wanted it: *"this is too complicated, so
we'll simplify to run at the start of sail only. the thing i wanted to accomplish
by having two can be dealt with later. it's the least important part."* Feedback
still fires mid-build (step 9); a second **chart chain** does not.

## 0b. The chain is the input — and the refusal is still PHYSICS

Template-fill from the LAST berthed stage for this request — found by COMMAND,
never by eyeballing the packets directory (ticket berths-carry-request-identity):

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m skills.chart.live chain <ticket-id>
```

prints the standing chain (per stage, the latest berth claiming the ticket); the
deepest non-None entry is your input, deepest link first: validate →
hypothesize → triage → decompose → survey → constrain → orient. An all-None
chain **after step 0** means the chart did not berth — a red to dispose, never a
licence to build from the conversation. And the identity is physics all
three ways (tickets berths-carry-request-identity + the-claim-rides-every-link):
every chart door refuses a packet whose ref'd berth claims a DIFFERENT ticket
(a stale berth from another request reds instead of sailing), and refuses a
CLAIMLESS packet whose ref'd berth claims (on a claimed chain the claim rides
every link — it may enter mid-chain, never silently vanish; Akien's ruling:
no warns, refuse and send back). This is no longer only prose: since 2026-07-29 (ticket
buildme-rides-the-chart) the emit chokepoint REFUSES a cast ticket's BUILDME
crossing unless a berthed validate packet claims the ticket — building from
the conversation is a build error the door itself throws (`EntryGateRed`).

Also required, and required **before step 0 rather than before this one**: a
**cast ticket** (`CairnCommons/tickets/<id>.json`). Casting is /sorted's job, not
this skill's — and the order is taught by physics: the chart doors refuse a claim
on an unfiled ticket, so **/sorted casts BEFORE /chart claims**, and the chart's
packets carry `"ticket": "<id>"` so the entry gate can find them. Swallowing
/chart did not swallow /sorted: the sequence is still **/sorted → /sail**, and
/sail's own first act is the chart.

## 1. Journal BUILDME

Every crossing rides the emit chokepoint (`cairn.tools.base.transitions.emit`) at the
component's own address, carrying the ticket — the ticket on the crossing is
what the entry gate reads, so an unnamed ticket is an ungated (and unclaimed)
build. The record of truth moves before the code does.

## 2. Build inside the berths

- **constrain's bounds are hard edges** — `out` is out; wanting something out
  is a question for Akien, never a silent widening.
- **survey's holdings are what you COMPOSE** — a holding rebuilt in parallel is
  the stone-1 failure with the survey sitting right there.
- **survey's absences are what you may BUILD** — each was measured absent;
  build minimal, grow against need.
- Packets claiming this ticket will judge the promotion — build as if the
  inspector is watching, because it is.

## 3. Prove — twice

Proofs beside the code (`proofs/`), teeth a hollow build could not pass.
**Run twice; never trust the first green.** A proof over live data asserts
invariants, never snapshots.

## 4. Journal PROVEME, then seal

Cross PROVEME through the chokepoint (the build gate fires there — a red is a
finding to dispose, not to argue with), then seal under the tester
(`TesterDevice().run_proof(path, caller=..., isolation="netns")`) and persist
the validation beside the code.

## 5. Live fire

If the component has a live face, fire it for real once — the proof pins the
contract, the live fire catches what the fixture world was too clean to show
(the pattern holds: first live fires keep catching their builders).

## 6. Answer the chart — BEFORE the PROVED crossing (physics since 2026-07-29)

Run the claiming validate berth's **criteria by their instruments**, then write
the **verdict artifact** through `cairn.devices.builder.machines.verdict.verdict.write_verdict`: every
criterion a run verdict (claim verbatim, instrument, outcome, evidence — a
verdict without both instrument and evidence is narration and the door refuses
it), every hypothesis in the chain dispositioned `confirmed`|`killed` with the
deciding observation. A **failed** criterion is a kick-back, not a crossing.
Then deposit it (`python3 -m skills.chart.live learn <verdict-berth>`) — the
kills become the hypothesize tree's memory of what killed which.

Skipping this is a build error the door itself throws (ticket
proved-answers-the-chart): the emit chokepoint REFUSES a claimed ticket's
forward crossing into PROVED without a complete, passing verdict artifact
(`ExitGateRed`) — the mirror of step 0's entry gate, done verified by
instrument at the close.

## 7. Cross `WATCHME` — emit the probe (only if the ticket carries one)

`WATCHME(<object>)` is a **free summons** (`code-seam@v2`, 2026-07-30): zero or
more times, any position, and it is in the string only if the ticket's author put
it there. **Optional to carry, mandatory to satisfy once carried** — it is not in
`skippable_summons`, so the chokepoint's forward walk cannot step over it.

- **No `WATCHME` in the string → there is nothing to do here.** The obligation was
  discharged at `/sorted`, where the ticket recorded either a watch or
  `"none, because X"`. Silence there is the failure, not here.
- **A `WATCHME` in the string →** the probe must be **armed before the crossing**:
  a module at the berth the ticket's spec names, declaring a module-level `PROBE`
  (a frozen `cairn.tools.base.probe.Probe`) that carries both a `carry` and an `enough`.
  A probe berths **with what it watches**, not with the ticket it was compiled
  from. Then cross — the emission gate reads the crossing's ticket, finds the spec
  for that object, and refuses an unarmed one (`WatchmeEmissionRed`).

**The probe carries no authority.** It deposits and pokes; the back-edge that
re-opens a node whose intention did not work is the **owner's** act (Law 6).

## 8. Journal PROVED and settle the records

- Cross PROVED with a note worth reading in a year — the exit gate reads the
  crossing's ticket and journals its verdict on the record.
- Ticket cursor → `[PROVED]` with the story-bearing distinctions.
- Charter delta ONLY if the design shifted — and any charter write pokes
  `cairn/tools/intentions_model_compiler/recompile_gate.sh` in the same act.

## 9. Deposit the learnings

`python3 -m skills.chart.live learn <berth>` for each berth of this voyage (the
trees are the durable memory; skipping starves them). A correction surfaced
mid-build rides orient's brick loop (deposit → counsel → propose), never a
quiet local fix.

**AND THE TOOL CALLS ARE EVIDENCE ABOUT THE CHART, NOT ONLY ABOUT THE BUILD.**
Akien, 2026-08-14: /sail *"runs in sail, gets feedback about tool calls that
happen inside the build. and we add that feedback into our mechanisms."* This is
the segment's **-2- edge** with the build as the machine: the chain said where
the work lives, what the bounds are, and what already exists — and the tool calls
are the only place those claims meet the world. A file opened that survey never
listed, a path written outside constrain's bounds, a holding rebuilt that survey
had already found: each is a **finding about the chart leg that authored the
claim**, not a lapse of the builder's attention. So name them, here, with the
claim they falsify and the call that falsified it.

TODAY THAT IS A HAND'S ACT, and the charter says so rather than pretending
otherwise: nothing observes the calls and nothing delivers the finding (the
route is declared at `skills/sail/intention+why.json`, the observer is ticket
`the-builds-tool-calls-are-evidence-about-the-chart`). Writing them into the
deposit is what a hand can do without either.

**This step is BOOKKEEPING THE CLOSE DOES — it is not a summons, and it never
was.** Until 2026-07-30 the workflow carried a mandatory, ungated `LEARNME` that
this deposit was doing duty for, which is precisely how that crossing came to be
filled with close-bookkeeping instead of efficacy data. Depositing this voyage's
berths tells the trees what was *decided*; it says nothing about whether the
intention *worked*. That question is step 7's, and it is answered later, by a
probe, against the ticket's own falsifier.

## 10. Commit and push

Committed is part of done. Commit autonomously, push at smells-like-done, then
verify with the instrument (`python3 -m cairn.tools.orient.orient git`), never from
the narration.

## 11. Close the boundary — /saveslate, then /compact

Fire **/saveslate** (the in-commons continuity record — at_sea, next_direction,
open_threads). Then tell Akien the boundary is **compact-safe** and invite
`/compact`: everything durable is now on disk (berths, ticket, history, seals,
slate, git), so the context is scaffolding. /compact is a client command — you
cannot fire it; making the boundary loud is the step.

## Stay honest

- "Done" is verified in the world (ls, git plumbing, re-run proofs) — never a
  proxy metric, never the narration.
- Report reds with their output; a skipped step is reported as skipped.
- The cheapest path is not the default — get it really right, then move on.

## After everything else

/compact
