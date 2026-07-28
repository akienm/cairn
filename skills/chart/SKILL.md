# /chart — run the pre-build preamble as question nexi

You are firing the **chart chain**: the pre-build preamble run as explicit,
schema-gated stages instead of invisible reasoning. v0 carries ONE stage — the
**orient nexus**. Stages land one at a time; each stage's prompt is template-filled
from the previous stage's validated file, so a skipped stage is a build error, not
a lapse.

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

### 2. The curtain (an IOU held as discipline until it is physics)

During orient, read **only the request and the floor facts**. Do not open the
target folders or files — proximity to a plausible answer is exactly what
collapses orient into pattern-matching (the measured failure this nexus exists
to stop). Grounding *what is asked* needs the map, not the territory; the
territory is survey's job, a later stage.

### 3. The ceiling — your mini agentic loop

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
  taken from floor output is `floor`; your assembly is `claude`. (`tree` waits
  on the tree-stratum stone.)

Loose process, tight output: reason as wide as the request needs — only the
emitted packet is narrow.

### 4. The gate and the berth

```bash
PYTHONPATH=$HOME/dev/src/cairn python3 -c "
import json, sys
from cairn.chart.orient import write_packet
print(write_packet(json.load(open(sys.argv[1]))))
" <scratchpad>/orient_packet.json
```

A refusal is loud and specific — fix the packet, don't argue with the gate.
The berth is instance-space (`~/.cairn/devices/chart/0/packets/`).

### 5. Hand forward

v0 ends at orient: report the packet (its fields, its berth path) to the user
and carry it in-conversation as the grounding for whatever runs next. Later
stages (constrain, survey, …) will template-fill from the berthed file as each
nexus lands.

## Stay honest

- The floor answers WHAT EXISTS; only your loop decides WHAT APPLIES.
- Parsimony test before you emit: could the next stage's prompt be built by
  template-filling from this packet with zero re-reading? If not, it is
  shortened, not compiled.
- Don't inflate confidence to feel done; `unknowns` is where honesty lives.
