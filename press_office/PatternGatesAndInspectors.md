# Pattern — Gates and inspectors (hard gates)

### There is no supervisor. Enforcement *is* gated ownership.

> **The move.** No orchestrator, no registry of components, no watchdog process. Every rule that
> matters is a door that refuses, owned by exactly one thing, and every rule that is *not* yet a
> door is on a published, monotonically shrinking debt list. A rule in prose is a rule that is
> not real, and the system says so about itself.

---

## 1. The measured failure

Two failures, one shape.

**The mandate that nobody obeyed.** In Cairn's predecessor, an inference proxy was mandated for
a month. Six live files still opened raw HTTP. A database proxy was used by twenty files while
forty called the driver directly. Nobody defied the rule; the rule simply had no teeth, and
teeth are the only part that scales past the week someone remembers.

**The sentence that enforced itself.** Five artifacts in Cairn had been standing on the phrase
*"enforced by the tester import-scan once that tooth exists"* since 2026-07-18. One of them was
a ruling packet whose own line read **"Guarded by import-scan, never by prose."** The sentence
asserting the rule was not prose was itself the only thing enforcing it.

That second one has a lived symptom attached. On 2026-08-05 two ruling packets sentenced
`cairn/tools/base/probe.py` — the Probe primitive — to deletion, **while nineteen live modules imported
it.** The confirm screen shows the author the *reading*, which was correct; nothing showed him
the kill list. Both packets were caught by hand, which is the wrong mechanism twice over.

A third failure gave the pattern its other half. Cairn's author observed, over years, that a
model *does not add logging until told* — and that no amount of instruction fixes this, because
instruction is discipline and discipline varies with the model, the context length, and the
hour. His conclusion, verbatim on 2026-07-27:

> *"the next thing is a post build inspector (also in python with SIEVES) that can catch these
> kinds of things. we find a new thing, we add a new sieve."*

---

## 2. The pattern

### 2.1 Every rule that matters is a door that refuses — the hard gate

A **hard gate** is a deterministic door that refuses, with no model in the loop and no override
path. Not a lint warning, not a code review checklist, not a convention. A call that returns an
exception. The term names the distinction this pattern is built on: a *soft* gate is a rule that
depends on an observer remembering to apply it, and §1's measurements are the record of how
that goes.

| Door | What it refuses |
|---|---|
| `create_owned_table` | a table with no owner — and the registry column carries `CHECK (owner <> '')`, so Postgres itself rejects it |
| `db_domain.write` | any writer but the recorded owner |
| `emit` | an illegal workflow transition: a forward skip past a gate summons, an off-vocabulary target, an unknown class, a no-op self-loop |
| the `/intent` door | a birth with no `traces_to`, or with the required adversarial pass unanswered |
| the `/sorted` door | a cast whose completeness answers are one-word, whose node class does not resolve, or whose watch names no probe berth |
| the chart stage doors | a packet whose upstream reference claims a *different* ticket, or which drops a claim the upstream carried |
| the ruling intake door | a packet that confirms itself, or names a `what_dies` path that is not on disk |

**A refusal names every lack in one pass.** This is a rule about the refusals themselves: one
fix must not earn a fresh first-pass refusal for something already named. Making an author play
twenty questions is its own named defect.

### 2.2 An inspector is a stack of sieves, each carrying the failure that taught it

The build inspector is a deterministic filter stack. Founding sieves:

- `charter_on_disk` ← seeded by the orientation instrument flagging its own missing charter,
  2026-07-27.
- `proofs_exist` ← seeded by a bus record that was true but silently partial, 2026-07-25.
- `silent_device` ← seeded by a device with zero `emit()` sites, against a stated claim that no
  device can opt out, 2026-07-27.
- `state_is_projection` ← seeded by the compiled-view debt; a hand-edited `state.json` reds.

**Provenance is a required field.** A proof tooth refuses a sieve whose docstring names no dated
correction — *a check nobody was taught by.* Growth rule: a failure the author catches that a
sieve could have caught becomes a sieve, and the class stops recurring.

**The verdict is always hardware.** A gate that consults an oracle is not a gate. Inference may
serve the *learning* of sieves, but a learning lands by installation — evidence-provenanced,
ratified, versioned — never mid-fire. Replayability (same input plus same registry revision
yields the same verdict) is what lets a verdict be permanent in a record of truth.

**"Only once" holds by construction.** The whole-repo sweep brings the existing tree to the gate
one time; thereafter every build passes through the inspector. So *wanting a second sweep is
itself the loudest possible finding* — it means a build bypassed the gate.

### 2.3 The mesh: how a chokepoint becomes checkable

`import_sieve` parses **every `.py` file in the tree** into an import graph and shakes declared
sieves through it. Two rule kinds, because the corpus asks two questions:

- `sole_path` — these modules may be imported **only** from inside this prefix. The domain
  chokepoint.
- `forbidden` — this prefix may not import these at all. A fork, so one thing survives the other
  breaking.

The rules are **owned by the component whose constraint they are** — `db_domain` owns the 5432
mesh, `inference_domain` owns the host mesh — and live at that component's address. There is
deliberately **no central rule registry.** That is the no-supervisor stance applied to the
enforcement mechanism itself.

The mesh's own honesty rule: shaking a sieve over a tree it did not read **raises**, rather than
reporting clean. A green over zero files is not a green.

### 2.4 The escalation ladder ends in a trouble

Cheapest first: back up and re-question · consult an advisor · a bounded subagent · review the
field · **ask the author.**

Below all of them is a terminus. A failure that cannot escalate anywhere else raises a
**trouble**. The first raise writes a ticket and notifies; every recurrence while that ticket is
live increments a count and notifies nobody. Only the recipient clears it, and only by naming
what changed. A fault that returns after a clear is a *new* ticket at count 1, carrying the fix
that did not hold.

The author's framing, 2026-07-25:

> *"a poke into nothing, a message that can't be delivered, these are bugs. nothing should fail
> silently. everything that can't escalate somewhere else should fail to trouble tickets until we
> get no more from the system. it's literally telling you and i how to improve it :)"*

and the damping half, in the same breath:

> *"a system alarm is raised. it's not raised again and again, it's count can increment...
> demanding more attention when there is none to give is not productive."*

**The trouble stream is the improvement backlog. The count is what keeps it readable.**

### 2.5 The manager smell

The named failure mode this pattern guards against: *the moment something exists in the plural,
build a central collection of them.* A registry, a dashboard, a roster.

The question that kills most of those: **who needs to see them all?** Usually nobody. What is
actually needed is that each one is reachable and owned.

---

## 3. How it is enforced

**Physics today:**

- Ownership on every table, checked by Postgres, with `create_owned_table` as the only door.
- Sole-path meshes over the whole tree for the Postgres driver and the inference host, run at
  proof time *and* at build time (the build sieve was added 2026-08-08 on an explicit ruling:
  *"THAT NEEDS TO BE IN THE BUILD INSPECTION"*).
- The emit chokepoint refusing illegal transitions, with six distinct seats: rules, entry gate,
  promotion sweep, exit gate, watch-emission gate, clearance gate.
- The build inspector's exit code — 0 clean, 1 findings — gate-able by anything that reads one.
- A sieve without provenance refuses to join the registry.

**Still prose (tracked as debt):**

- **A `subprocess` dials and imports nothing.** `subprocess.run(['psql', ...])` is invisible to
  an import graph, as is a dynamic import. This residue is written into the component's own
  falsifier rather than left for someone to discover.
- **Nothing reds a component that keeps relational state somewhere else entirely.** The door is
  sealed; *where data lives* is not the same question as *who imports a driver*.
- **Nothing makes anyone open a ruling packet.** The hook sees packets that exist, not rulings
  never recorded.
- **A code floor cannot tell a concern about work in flight from the word "caveat" in a
  retrospective.** The turn-shape check is heuristic.

---

## 4. What it costs

**Gates fire on you.** The system refused its own `PROVED` crossing on 2026-08-11 because
retiring an unrelated prose IOU had edited a file after its proof was sealed. That was correct
and it also cost a re-seal. A gate you can talk past is not a gate; a gate you cannot talk past
will occasionally be right about something inconvenient.

**A false red is expensive.** `import_sieve` has been narrowed three times, each by a human
adjudicating a wrong catch: whole-source scanning became import-line scanning, port-literal
matching became capability matching, word matching became full-dotted-name matching. Each
correction is now a permanent paired tooth. The rule after a fourth false red is *a new paired
tooth, never a loosened assertion* — which means precision is paid for one incident at a time.

**Refusal-first design is more code.** The build inspector carries 28 proof teeth. Every one
exists because a check that always fires gets unwired, and a check that never fires proves
nothing. Each sieve is paired: shaken over a planted graph (must catch) and over the real corpus
(must not), because either half alone is satisfied by a sieve made of solid sheet metal.

**Human gates queue.** Twelve tickets stand at the author's gate and 68 findings await a verdict.
With one human in the loop, that backlog is a measured property of the design, not an accident.

---

## 5. What would falsify this

- **The debt list grows across a quarter.** It is designed to shrink monotonically. If rules
  migrate *into* prose faster than they migrate out, "physics not policy" has become the thing it
  replaced.
- **A second whole-repo sweep is genuinely needed.** By the inspector's own charter, that is the
  loudest finding available: it means builds are bypassing the gate.
- **A healthy component draws a finding.** A gate that always fires gets unwired, and the
  unwiring is silent.
- **The sieve registry goes static.** If the author's corrections stop becoming sieves — if the
  registry is unchanged three corrections from now — the learning half is hollow and this is a
  linter.
- **A central registry appears.** The no-supervisor claim dies the day something needs to see
  them all.

---

## 6. What is built, and what is red

**Built.** 28 inspector teeth across the sieve stack and the three crossing-jurisdiction gates.
Sole-path meshes live at proof time and build time. The trouble lane with its first-raise /
increment / clear-by-naming-what-changed semantics, holding 11 live records. The ruling intake
door with a supersession retirement path. 69 green validations, 0 red.

**Red.**

- Subprocess and dynamic-import residues in every import mesh, named but unclosed.
- No sieve for *where relational state lives*, only for who imports the driver.
- Nothing forces a ruling to be recorded, or a recorded ruling to be read.
- The clearance gate had cleared **zero** crossings for the first three weeks of its existence —
  its own falsifier was met continuously and undetected until someone measured on 2026-08-10.
  It now holds 2 grants and 1 real refusal. n=1 by one hand cannot distinguish a gate that works
  from a gate that agrees with whoever calls it; a probe is armed to say when that changes.

---

*Pattern document, `press_office/PatternGatesAndInspectors.md`. Part of the Cairn pattern series;
the spine is [`CairnArchitecture.md`](CairnArchitecture.md). All numbers from
[`FactSheet.md`](FactSheet.md), measured 2026-08-11.*
