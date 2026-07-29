# /chart — run the pre-build preamble as stackable learning bricks

You are firing the **chart chain**: the pre-build preamble run as explicit,
schema-gated stages instead of invisible reasoning. Five stages carry today —
the **orient brick**, the **constrain brick**, the **survey brick**, the
**decompose brick**, then the **triage brick**. Stages land one at a time; each
stage's prompt is template-filled from the previous stage's validated file, so
a skipped stage is a build error, not a lapse.

The device charter lives at `cairn/chart/intention+why.json`; this skill's charter
beside this file.

ARGUMENTS: the request to chart (the `<something>` of `/chart <something>`).

## Stage 1 — ORIENT

One narrow question: **what is actually being asked, and where does it live?**
Not how to do it, not what the answer is — that's later stages' work.

### 1. Run the floor (deterministic — before you reason)

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.orient import floor_facts
print(json.dumps(floor_facts(sys.argv[1]), indent=2))
" '<the request, verbatim>'
```

The floor reports **what exists** — components mentioned (against the live
charter roster), skills mentioned, referenced paths verified found-vs-missing.
It never decides what applies; that judgment is yours, in the loop below.

### 2. The tree — walk before you reason

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.chart.live counsel '<the request, verbatim>'
```

The nexus's own graph tree answers with prior orientation learnings and the
resolution floor **visible and labeled** (it is an n=1 guess — treat it as one).
Counsel is COUNSEL: nodes at or above the floor are candidates, and each carries
the berth path of the packet that taught it — read that packet if the counsel
applies. **You decide what applies; the tree only says what is near.** A field
you fill from a walked node's packet is provenance `tree`.

If the embed host is unreachable, the stratum refuses loudly — record
`"tree stratum unavailable: <the refusal>"` in `unknowns` and proceed on
floor + claude. Never silently skip the walk.

### 3. The curtain (an IOU held as discipline until it is physics)

During orient, read **only the request and the floor facts**. Do not open the
target folders or files — proximity to a plausible answer is exactly what
collapses orient into pattern-matching (the measured failure this nexus exists
to stop). Grounding *what is asked* needs the map, not the territory; the
territory is survey's job, a later stage.

### 4. The ceiling — your mini agentic loop

Think → act → observe until the LOCAL exit condition: *the packet's fields are
filled and honest*. Actively assemble (never bare-lookup):

- **intent** — the request restated grounded and disambiguated. If the request
  is ambiguous, the ambiguity goes in `unknowns`, not silently resolved.
- **domain** — where in the system this lives (component/root/concept).
- **scope** — what is in and what is explicitly out.
- **refs** — pointers (paths, component names) downstream will need. ONLY
  floor-verifiable refs — the gate refuses invented ones. References beat
  restatement: point, don't quote.
- **unknowns** — what orient could NOT ground. An honest non-empty list
  outranks a confident hollow one.
- **confidence** — a float in [0,1], as data, not hedging prose.
- **provenance** — per authored field: `floor` | `tree` | `claude`. A fact
  taken from floor output is `floor`; a field filled from a walked node's
  packet is `tree`; your assembly is `claude`.

Loose process, tight output: reason as wide as the request needs — only the
emitted packet is narrow.

### 5. The gate and the berth

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.orient import write_packet
print(write_packet(json.load(open(sys.argv[1]))))
" <scratchpad>/orient_packet.json
```

A refusal is loud and specific — fix the packet, don't argue with the gate.
The berth is instance-space (`~/.cairn/devices/chart/0/packets/`).

### 6. Deposit back — the tree learns this crossing

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.chart.live learn <the berth path>
```

The packet's intent becomes a node the next similar request will walk to
(Law 1 as the nexus's runtime). This is how the stratum boundary moves down —
skipping it starves the tree. The command also prints the nexus's dial
aggregate: the floor/tree/claude fractions the whole intention is measured by.

### 7. Hand forward

Carry the berth path — stage 2 template-fills from it, never from this
conversation.

## Stage 2 — CONSTRAIN

One narrow question: **what BOUNDS this request?** Not what to build, not how —
later stages. This brick was built UNDER pre-installed judges (the inspector's
`constraint_traces` + `constraint_bounds_complete`, proved before the module
existed): a packet the door passes is a packet the promotion gate passes.

### 1. The floor — template-filled from stage 1's berth

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.constrain import constrain_floor
print(json.dumps(constrain_floor(sys.argv[1]), indent=2))
" <the orient berth path>
```

It surfaces each ref'd component's charter **falsifier / gates / owner
verbatim, with its address**. The floor surfaces text; you decide what applies.
A paraphrased constraint is a constraint with laundered provenance — quote or
point, don't reword the charter.

### 2. The tree — walk before you reason

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.chart.live counsel '<the request, verbatim>' constrain
```

Prior bounds for this class of request, floor labeled as always.

### 3. The ceiling — assemble the bounds

- **intent_ref** — the orient berth path (provenance `floor`).
- **constraints** — each `{text, source, kind}`: the text states the bound, the
  source must RESOLVE (the judges refuse invented sources), kind is an open
  string (law | charter | ticket | memory | ruling…).
- **bounds** — `{in: [...], out: [...]}` — BOTH non-empty. An empty `out` is
  the founding failure (bounds-checking that never ran to completion) and the
  judges refuse it. Saying what is OUT is the work.
- **unknowns / confidence / provenance** — as in stage 1; provenance covers
  intent_ref, constraints, bounds, unknowns.

### 4. The gate and the berth

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.constrain import write_constrain
print(write_constrain(json.load(open(sys.argv[1]))))
" <scratchpad>/constrain_packet.json
```

The door runs the inspector's own judges — a refusal names the judge; fix the
packet, don't argue with the gate.

### 5. Deposit back

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.chart.live learn <the constrain berth path>
```

The bounds become the constrain tree's memory of this class of request.

### 6. Hand forward

Carry the constrain berth path — stage 3 template-fills from it.

## Stage 3 — SURVEY

One narrow question: **what already EXISTS that bears on this request?** Not
what is asked, not what bounds it, not how to split it. This is where the
territory legitimately OPENS (orient's curtain lifts here). This brick was
built UNDER pre-installed judges (`survey_holdings_resolve` +
`survey_coverage_complete`, proved before the module existed).

### 1. The floor — template-filled from stage 2's berth

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.survey import survey_floor
print(json.dumps(survey_floor(sys.argv[1]), indent=2))
" <the constrain berth path>
```

It surfaces each ref'd component's **device_census row verbatim** (measured
state: charter, proofs, validations, devices, emit sites — constrain already
surfaced the authored charter text; survey reads what is provably THERE) plus
existence-measured non-component refs, found vs missing kept apart, under the
stage-2 bounds. The chain is re-checked whole: a broken link refuses.

### 2. The tree — walk before you sweep

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.chart.live counsel '<the request, verbatim>' survey
```

What past sweeps of this class of request found, floor labeled as always.

### 3. The ceiling — the wide sweep that earns its keep

Sweep as wide as the request needs — parsimony must NOT squeeze the survey
(loose process, tight output). Assemble:

- **constrain_ref** — the constrain berth path (provenance `floor`).
- **sought** — where you pointed the light, non-empty. An empty sought is the
  sweep that never ran wide (the stone-1 parallel-roster failure) and the
  judges refuse it.
- **holdings** — each `{what, address}`: what exists that bears on the request;
  the address must RESOLVE (the judges re-check it at promotion — a holding the
  world doesn't hold is state-reported-from-records).
- **absences** — each `{what, measure}`: what was sought and NOT found, with
  the measure that established it. **An absence is a claim** — '0 of 13' was an
  absence established by word-grep; the judges refuse a measureless one.
- **unknowns / confidence / provenance** — as before; provenance covers
  constrain_ref, sought, holdings, absences, unknowns.

### 4. The gate and the berth

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.survey import write_survey
print(write_survey(json.load(open(sys.argv[1]))))
" <scratchpad>/survey_packet.json
```

### 5. Deposit back

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.chart.live learn <the survey berth path>
```

The inventory becomes the survey tree's memory of this class of request.

### 6. Hand forward

Carry the survey berth path — stage 4 template-fills from it.

## Stage 4 — DECOMPOSE

One narrow question: **how does this request SPLIT?** Not what to build with
the pieces — that is /sail's voyage. This brick was built UNDER pre-installed
judges (`decompose_composes_holdings` + `decompose_builds_absences`, proved
before the module existed). Known-vs-novel is physics here: every piece's kind
is a claim the survey berth can check.

### 1. The floor — template-filled from stage 3's berth

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.decompose import decompose_floor
print(json.dumps(decompose_floor(sys.argv[1]), indent=2))
" <the survey berth path>
```

It re-reads the chain whole (depth 4 — a broken link anywhere refuses) and
hands you the **judges' vocabularies verbatim**: `holding_addresses` (what a
compose piece may use) and `absence_whats` (what a build piece may fill),
with the intent and bounds they operate under. The floor never decides the
split; the seams are yours.

### 2. The tree — walk before you split

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.chart.live counsel '<the request, verbatim>' decompose
```

How past requests of this class divided, floor labeled as always.

### 3. The ceiling — the split

- **survey_ref** — the survey berth path (provenance `floor`).
- **sub_problems** — each `{what, why, kind, ...}`:
  - `kind: "compose"` — `uses` lists holding addresses the survey berth
    carries. Composing outside the inventory is refused — if a piece needs
    it, the survey must hold it first (the chain pushes back up).
  - `kind: "build"` — `fills` names a measured absence, **verbatim** from the
    berth. Build-minimal is physics: only what was measured absent may be
    built. A build piece may also list `uses` (holdings it composes).
  - the `why` is forced per piece — a piece that cannot say why it exists
    cannot be adjudicated.
- **unknowns / confidence / provenance** — as before; provenance covers
  survey_ref, sub_problems, unknowns.

### 4. The gate and the berth

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.decompose import write_decompose
print(write_decompose(json.load(open(sys.argv[1]))))
" <scratchpad>/decompose_packet.json
```

### 5. Deposit back

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.chart.live learn <the decompose berth path>
```

The split becomes the decompose tree's memory of how this class divides.

### 6. Hand forward

Carry the decompose berth path — stage 5 template-fills from it.

## Stage 5 — TRIAGE

One narrow question: **in what order is the split attacked, and by what stated
standard?** Not what the pieces are (decompose), not what outcome each will
have (hypothesize — a later brick). This brick was built UNDER pre-installed
judges (`triage_covers_the_split` + `triage_reasons_the_order`, proved before
the module existed). Position IS the rank — no numeric priority field exists
to drift against the list.

### 1. The floor — template-filled from stage 4's berth

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.triage import triage_floor
print(json.dumps(triage_floor(sys.argv[1]), indent=2))
" <the decompose berth path>
```

It re-reads the chain whole (depth 5 — a broken link anywhere refuses) and
hands you the pieces verbatim, the split's unknowns, and the **coverage
vocabulary**: `piece_whats` — the exact multiset your order must cover. The
floor never decides the order; the standard is yours.

### 2. The tree — walk before you rank

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.chart.live counsel '<the request, verbatim>' triage
```

How past requests of this class ranked, floor labeled as always.

### 3. The ceiling — the order

- **decompose_ref** — the decompose berth path (provenance `floor`).
- **order** — a complete permutation of the split's pieces, first-to-last:
  each `{what, why_now}`, the `what` **verbatim** from the berth. Nothing
  dropped (a silent drop is descoping without the word — that is a bounds
  change through Akien's gate, never a ranking), nothing invented, nothing
  double-ordered. The `why_now` is forced per entry — the ranking standard
  travels with the rank, so the order can be adjudicated (the cheap-first
  reflex hides exactly in unstated standards; the honest order often inverts
  the appealing one — solidify the layer below).
- **unknowns / confidence / provenance** — as before; provenance covers
  decompose_ref, order, unknowns.

### 4. The gate and the berth

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.triage import write_triage
print(write_triage(json.load(open(sys.argv[1]))))
" <scratchpad>/triage_packet.json
```

### 5. Deposit back

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -m cairn.chart.live learn <the triage berth path>
```

The order becomes the triage tree's memory of how this class ranks.

### 6. Hand forward

The chain ends at triage today: report the five berths. The ranked split is
/sail's input — pieces in hand, first things first, standards stated. Later
stages (hypothesize, validate) template-fill from the triage berth as each
brick lands.

## Stay honest

- The floor answers WHAT EXISTS; only your loop decides WHAT APPLIES.
- Parsimony test before you emit: could the next stage's prompt be built by
  template-filling from this packet with zero re-reading? If not, it is
  shortened, not compiled.
- Don't inflate confidence to feel done; `unknowns` is where honesty lives.
