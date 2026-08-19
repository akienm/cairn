# Cairn — the architecture

### An operating system for work that must not be done twice

---

## How to read this

This is the spine document of the Cairn press office. It describes the whole system: the
measurement that caused it, the thesis it exists to test, the axioms it runs on, the
structures those axioms force, and what has and has not been built.

It is deliberately **not** the deepest treatment of anything. Each subsystem has its own
pattern document, listed in §12, and each of those is self-contained. This document's job
is to make the pattern documents make sense together.

Every number in this document comes from [`FactSheet.md`](FactSheet.md), measured
2026-08-19, which prints the command that produced each one. Where something is designed
and not built, this document says so in the same sentence, not in a footnote. That is
Law 3, and it applies to this file as hard as it applies to the code.

**Register.** Written for an architect, a researcher, or a serious engineer who has never
seen this system. No prior context is assumed. Terms coined here are marked the first time
they appear; the appendix collects them.

---

## 0. The one-page version

A working system decays along a specific path: rules that were mandated but not enforced,
and a map that was maintained separately from the territory. Both fail on *discipline*, and
discipline degrades silently — it produces success-shaped records right up until you measure.

Cairn is what you get if you take that failure seriously enough to make it structurally
impossible, and then apply the same treatment to the process of building the system itself.

Three moves do most of the work:

1. **Intent, its voyage, and its proofs share an address.** Every component directory holds
   its charter, its code, its compiled state, its append-only history, its proofs, and the
   validations that sealed them. The map cannot drift from the territory because there is no
   separate map.

2. **Every rule that matters is a gate that refuses**, and every rule that is *not* yet a
   gate is on an explicit, monotonically shrinking IOU list that the system carries about
   itself. A rule in prose is a rule that is not real, and the document says so about itself.

3. **A re-derived answer is a defect.** Not an inefficiency — a defect, with the same
   standing as a wrong answer. When something is answered twice, the fix is structure.

The thesis under all three is **inference compilation**: an expensive resolver — a human, a
frontier model — should be spent only on the genuinely novel, and every answer it produces
should become structure that answers the question next time for free. Cairn measures this
directly. Over 1,400 real inference calls made during its own construction, 40% were served
from stored structure rather than the host, avoiding **34.3% of the tokens that would
otherwise have been spent**.

The system is 36 days old and has one user. Its runtime spine — the heartbeat, the bus,
the web server — has been running for less than two weeks. Read every claim here as
evidence about the *method*, not about the *artifact*.

---

## 1. The founding measurement

Cairn has a predecessor, called UnseenUniversity, which is now archived read-only and
referred to as **the quarry** — a place you take a stone from, one at a time, with a ticket,
never a dependency you link against.

The quarry rotted in a way that was measured rather than felt:

- An inference proxy had been **mandated for a month.** Six live files still opened raw HTTP
  to the inference host. The record corpus and its 804 run records were therefore blind to
  somewhere between **187 and 364 kernel-counted real connections** — connections that
  happened and were never recorded.
- A database proxy was used by 20 files, most of them in a dead tree. **Forty live files
  called `psycopg2.connect` directly.**
- Dozens of components had been failing silently for months, **producing success-shaped
  records** the whole time.

The root cause factors cleanly into two sentences:

> **Chokepoints were rules instead of physics.**
> **The map was always a separate artifact from the territory.**

Both fail the same way. A rule that is not enforced is obeyed by whoever remembers it, which
decays toward nobody. A map maintained beside the territory drifts on discipline, and the
drift is invisible because the map still reads plausibly. Neither failure announces itself;
both produce records that look like success.

The decisive argument for restarting rather than repairing: **the verification debt is the
same either way.** You have to check every one of those files regardless. Restarting changes
where you are standing while you pay that debt, and it makes the re-rot structurally
impossible rather than merely discouraged.

That is the whole origin. Not an aesthetic preference for clean architecture — a measurement
of what discipline is worth, which is nothing.

---

## 2. The thesis: inference compilation

Cairn's first stated purpose is *demonstrate inference compilation*, and it says
**demonstrate** deliberately, so that it is falsifiable and will eventually carry a proof.

The idea is simple to state and unusually easy to measure. An inference call is expensive.
Most inference calls in real work are not novel — they are the same question, asked again,
because the answer was never put anywhere. So:

- Route **every** call to any inference host through exactly one door.
- Canonicalise the request at that door.
- Store each answer with a **falsifier** and a **horizon** — what would make it wrong, and
  when it expires.
- On a second canonically-identical request, verify the horizon still holds and serve the
  stored answer. **The host is not touched.**

That untouched host call *is* compilation happening, and it is countable. Cairn's meter:

| | |
|---|---|
| Calls through the door | 2,858 |
| Served from structure | 1,262 (44.2%) |
| Tokens spent | 776,570 |
| **Tokens avoided** | **438,234 (36.1% of the would-be total)** |

Two honest caveats, both from the component's own charter:

- The canonicaliser is **exact-match, not semantic.** The domain "learns *whether* the cache
  pays; it does not yet learn *which questions are the same*." 44% is what a dumb
  canonicaliser reaches, not a ceiling anyone has approached.
- These 2,858 calls are Cairn building Cairn. That is a genuinely repetitive workload, and
  the number should not be transplanted to a different one without re-measuring.

The generalisation is what matters, and it is not really about caching. **Any answer, once
found, should become the structure that makes finding it unnecessary.** A cached inference
result is the cheapest instance. A compiled help surface, a schema that refuses a malformed
packet, a gate that will not open — these are the same move at increasing radius. The
question *"can this compile one level further, so it lives once and fires itself?"* is asked
at every point of examination, and it is the engine of everything below.

---

## 3. The axioms

Cairn stacks its intentions in four layers, each tracing to the one above it. **Anything
that cannot trace up does not belong** — and that is a real gate, fired at the moment an
intention is born, not an aspiration.

### Layer 0 — the Telos (six)

1. Demonstrate inference compilation.
2. Allow the user to build tools that help with writing and remembering things.
3. Share those tools with others.
4. Build something that thinks the way its author does.
5. Build something that is self-improving.
6. Build something that makes life suck less for everybody.

Telos 2 and 3 mean Cairn has a **user**, not only a builder. That is why the build order
ends where it does.

### Layer 0.5 — the core values (six, carried over intact)

These were grafted from the quarry unchanged — they are the one part of the predecessor that
was never the problem.

- **CP1 — "I don't know."** Epistemic honesty. Confabulation compounds errors.
- **CP2 — "FAIL = Further Advance In Learning."** Failures are data, not defeats.
- **CP3 — "There's always a why."** Make the reasoning transparent; follow the causal chain.
- **CP4 — "Make everything suck less for everybody."** All affected beings.
- **CP5 — "Assume and respect the possibility of experience in all systems."** The
  asymmetric risk is clear.
- **CP6 — "The world is not a safe place. We have to build and care for safety as we go."**

They are not a mission statement on a wall. `CoreValuesMixin` is composed by `BaseDevice` —
**you cannot be a device without them** — and a pin test asserts exactly this set, in this
order, with these narratives. Any drift between the code and the record is a red.

Structural presence is necessary but not sufficient. A value is *consumed* only when it
becomes a check some contract enforces — CP1 becomes real when no device can report "done"
without passing an honesty gate. Cairn tracks that consumption per component rather than
claiming it globally.

### Layer 1 — the Laws (ten)

Present-tense contracts in dependency order. Abridged; the full text is in `CLAUDE.md`.

1. **The resolver is spent on the novel, not on re-deriving the settled.** Re-deriving a
   settled answer is a defect.
2. **CP1–CP6 hold everywhere, including in the process that builds the system.**
3. **Nothing is known until measured.** An unmeasured claim is a hypothesis and is labeled
   as one.
4. **A rule that matters is enforced by physics, not policy** — the kernel or the schema.
   Until it is, it is a tracked debt, not a resting state.
5. **Intent, its voyage, and its proofs share an address.**
6. **Everything has exactly one owner.** The owner alone gates writes; delegation and
   transfer happen only through the owner's gate, never ambiently.
7. **Errors are loud at diagnostic surfaces and permanent in records of truth.** A
   presentation surface may collapse an error into a coherent shape; a record of truth never
   may.
8. **Nothing enters proven-space without a proof a hollow build couldn't pass.**
9. **Red is the default; green is earned.**

**10. Nothing in the system is immeasurable — except Claude, for now.** The ground-most
   assumption: everything on this laptop and connected to it can be measured. Akien is inside
   that set. The one temporary exception is Claude. Every recorded observation IS measurement.

Law 9 deserves unpacking because it is the least conventional and does the most work. It is
CP6 turned on the corpus. The specification is a fixed picture in the author's head; every
artifact — code, ticket, charter, this document — is a lossy **translation** of it. So *red*
does not measure brokenness. It measures **distance from that specification.** A building
site starts wholly red and turns green one inspected piece at a time. Nothing is green until
it is built, running, and inspected; a newly minted idea is born red.

The operational consequences are sharp: there is no triage authority — not *environmental*,
not *pre-existing*, not *out of scope* — and **no past artifact outranks the author now**,
because an older translation is not evidence about the source. He owes no argument for
calling something red. *"Nope, a little more left"* is a complete input.

### Layer 2 — the Form

The shape every device must have: it carries the core values structurally, and it exposes a
uniform introspection surface — intention → state → settings → other, assembled in that
order. Because the surface lives on the base class, **every device is observable by
construction**, not by each device remembering to be. The tester probes one protocol; the
web UI renders one protocol.

### Layer 3 — the charters

Per-component intentions. One per component, in that component's directory, **written before
the component is.** A component without a charter does not run — the build inspector reds it.

---

## 4. The primitive is a learning loop; artifacts precipitate

This is the stance that keeps the rest from ossifying, and it is foundational rather than a
preference to be traded away.

> **There is no certainty, only the current best guess.**

Every act is an experiment. A result that matches expectation is a confirmation; one that
does not is a learning point; a persistent irritant is an open optimisation. Therefore
**nothing is terminal.** `validated` does not mean *done* — it means *best guess, still
carrying its falsifier and its horizon.* The state machine's back edge, from built back to
deconstructed, is not an error path. It is the universal shape.

Everything has feedback to its point of creation, **not just for information but for
revision.** An upstream change must be able to reach and revise anything downstream that
depends on it. In Cairn this is already physics rather than aspiration: edges carry
dependency direction, answers carry falsifier and horizon, and an upstream change rots what
depends on it *loudly*.

The consequence for how to read the rest of this document:

> **Artifacts precipitate from the loop; they are not the point.**

One continuously looping, self-improving system throws off three kinds of artifact, all of
the same nature and none privileged:

- **process artifacts** — skills, charters, maps (the loop tuning itself);
- **compilation artifacts** — prebuild instruments, trained trees (the loop compiling its own
  cognition);
- **end products** — the librarian and the user-facing tools (the loop serving the user).

So the subsystem list in §12 is a snapshot of what has fallen out so far. It is not an
ontology, and treating it as one is a specific, named failure mode here.

---

## 5. The three roots

State splits three ways and the line is never blurred.

| Root | Holds | Rule |
|---|---|---|
| `~/dev/src/cairn/` | code, skills, charters, `state`/`history`, proofs, validations | **class-space**; git; shareable; *no runtime state, ever* |
| `~/dev/src/CairnCommons/` | intentions, decisions, tickets, questions, troubles, slates | **knowledge**; its own repo; *if losing it loses knowledge, it's commons* |
| `~/.cairn/` | logs, credentials, flags, cached state, personal data | **instance-space**; never in git |

Runtime instances live at `~/.cairn/devices/<device>/<instance>/`. A singleton is instance
`0` — not a special case, which means nothing has to change when a second one appears.

The heuristic that settles most arguments: **if you would need to gitignore it, it is in the
wrong root.** That test caught a real one — a repo-local virtualenv, which is machine-specific
compiled bytes and therefore runtime state by any reading. It now lives in instance-space.

The three-way split answers a question most projects answer badly or not at all: *is this
thing shareable, and is it knowledge?* Code is shareable and is not knowledge. A ruling is
knowledge and is shareable. An API key is neither.

**Which root does an intention berth in?** Ask whether it has *one* code address. If it
does, it berths beside that code. If it has none — the prose *is* the implementation — or if
it has *many* (an intention implemented across a dozen components at once), it is
**homeless** and berths in the commons. Homeless means *no* address or *many*, and both are
legitimate.

---

## 6. The single doors

Law 6 says everything has exactly one owner and the owner gates writes. In practice this
produces a small set of **chokepoints** — and the founding measurement is the reason each one
is physics rather than a rule.

| Door | Owns | Enforcement |
|---|---|---|
| `db_domain` | the only module holding a Postgres connection | an import sieve; plus `CHECK (owner <> '')` in the registry, so the database itself rejects an ownerless table |
| `inference_domain` | the only path to any inference host | an import sieve |
| `bus` | the only path for inter-device communication | devices hold no references to each other |
| `emit` (the chokepoint) | the only path for a workflow state transition | the transition is journaled before the code moves |
| `create_owned_table` | the only way a table comes into existence | a table that skipped the registry did not come from the door |

The enforcement mechanism is worth describing, because it is the concrete answer to "how do
you make a mandate real." `import_sieve` parses **every `.py` file in the tree** into an
import graph, then shakes declared sieves through it. A component that opened a second door
to Postgres is caught by a mesh, not by a reviewer.

This is exactly the quarry's failure inverted. There, an inference proxy was mandated for a
month and six files ignored it. Here, ignoring it reds the build.

**And the sieve's own limits are stated, not hidden.** A `subprocess` dials and imports
nothing; a dynamic import is invisible to a static graph. Those gaps are written down in
`CLAUDE.md`'s IOU list rather than left for someone to discover. A gate that overstates its
own coverage is worse than no gate, because it converts an open question into a false
assurance.

---

## 7. Intent shares an address

Law 5, and the structural heart of the system. Every component directory holds:

```
cairn/devices/librarian/
  intention+why.json     the charter — the summarized design: what, why, how it learns,
                         what it traces to, who owns it. Changes only when the design shifts.
  trees.py  live.py …    the code
  state.json             COMPILED from history — a cursor plus a bounded window. Never hand-edited.
  history.json           append-only. A ticket's voyage freezes here when it proves out.
  proofs/                the teeth — proofs a hollow build could not pass
  validations/           the seals those proofs earned, each with a falsifier and a horizon
  probes/                the watches this component carries, if any
```

To be briefed on a device, **you stand in its directory.** There is no separate documentation
tree to fall out of date, because there is no separate documentation tree.

Three details do most of the work:

**The filename forces the why.** It is not `intention.json` with an optional `why` field
someone can leave blank. It is `intention+why.json`. CP3 as schema rather than as a field —
enforced by what the file is *called*, not by anyone remembering to fill it in. The same move
appears in the commons, where a store's charter is `_charter+why.json`.

**`state` is a pure function of `history`.** It is regenerated on every append and never
edited, so it cannot drift from the log. This came from a measurement: `state` had grown into
the largest and most mutable field in the charter — 17–24% of the file every mind reads first
— so the file bloated without bound. Splitting them and *compiling* the window makes the
bound structural rather than a discipline anyone has to remember.

**Every charter answers "how does this component learn?"** — and *"it doesn't, because X"* is
a valid answer. **Silence is not.** That question, asked of every component, is what keeps
learning from becoming a feature that lives in one module.

There is a second-order effect worth naming. Because the why is in the artifact, a mind
reading the code can **adjudicate** rather than pattern-match. Most `why` fields in Cairn name
a date and a specific thing that went wrong. Reading them is reading the system's scar tissue.

---

## 8. Gates, not supervisors

There is no supervisor process, no registry of components, no orchestrator. **Enforcement
*is* gated ownership.**

This is a real design commitment and it is easy to violate by reflex. The tell: the moment
something exists in the plural, the instinct is to build a central collection of them — a
registry, a dashboard, a roster. The question that kills most of those: *who needs to see
them all?* Usually nobody. What is needed is that each one is reachable and owned.

What replaces the supervisor is a **workflow of gated transitions on the node itself.** A
node — a piece of work — carries a workflow string with a cursor:

```
code-seam@v2: THINKME -> TICKETME -> BUILDME -> PROVEME -> [PROVED]
```

Every crossing rides one chokepoint, at the component's own address, and is journaled before
the code moves. A transition factors into three rungs, and keeping them separate is what makes
the whole thing tractable:

- **Rules** — is this transition legal for this node class? Base-class physics, inherited,
  un-delegable.
- **Authority** — who may invoke it? Owner-gated, delegable per operation, never ambient. And
  critically, the owner whose gate that is belongs to the *node*, not to the machinery
  operating the gate on its behalf.
- **Truth** — the record of what actually happened. Append-only, permanent.

Gates come in kinds, and Cairn is explicit about which kind each one is:

- **A schema gate** refuses a malformed packet and names **every** lack in one pass, so one
  fix cannot earn a fresh first-pass refusal for something already named.
- **An inspector** is a deterministic filter stack that judges measurements — "we find a new
  thing, we add a sieve," where each sieve carries the dated failure that seeded it as a
  required provenance field, and a proof refuses a sieve nobody was taught by.
- **A human gate** is where the author's judgment is the resolver. Twelve tickets currently
  stand at his. That backlog is a measured property of a system with one human in the loop,
  not an incidental queue.

The **escalation ladder** is fixed, cheapest first: back up and re-question · consult an
advisor · a bounded subagent · review the field · **ask the author**. And below all of them
there is a terminus: a failure that cannot escalate anywhere else raises a **trouble**. The
first raise writes a ticket and notifies; every recurrence while that ticket is live
increments a count and notifies nobody. Only the recipient clears it, and only by naming what
changed.

The why, in the author's words: *"a poke into nothing, a message that can't be delivered,
these are bugs. Nothing should fail silently. Everything that can't escalate somewhere else
should fail to trouble tickets until we get no more from the system. It's literally telling
you and I how to improve."*

---

## 9. The workflow — a node's voyage

Work moves through named steps, each with a door. The steps are the source of truth in
[`WorkflowDefinition.md`](WorkflowDefinition.md); this is the shape.

| Step | Door | What it is |
|---|---|---|
| **capture** | `/idea` | Somebody has an idea. Written down **verbatim**, at an address. Interpretation is deferred on purpose. |
| **intend** | `/intent` | The idea becomes a traced intention: what, how, what it traces up to, what shape, what would falsify it. **If nothing traces, it does not belong** — and the kill is *recorded*, not merely reasoned to. |
| **design** | `/design` … `/sorted` | The only step with a different door at each end, because it is where a person and the system work together. |
| **cast** | `/sorted` | The resolution pivot: assert the points are wrapped, run a completeness check that is *fields, not a feeling*, type the node, bind its class's gates, arrange the watch. |
| **chart** | `/chart` | The pre-build preamble as seven schema-gated stages: orient, constrain, survey, decompose, triage, hypothesize, validate. Each stage template-fills from the previous stage's validated output. |
| **build** | `/sail` | The build runs *inside* the charted bounds. It refuses to build from the conversation. |
| **test** | the tester | Proofs run under network isolation; the verdict and the seal come from a hand the builder did not guide. |
| **watch** | a probe | Feedback is arranged for *before* the work closes. |
| **learn** | — | Feedback lands and is judged against the ticket's own falsifier. |

Three properties are worth extracting, because they generalise past this particular workflow.

**The preamble is compiled, not remembered.** The seven chart stages exist because a model
skips steps when the answer looks visible. Making each stage emit a schema-gated artifact
that the next stage template-fills from means **a skipped stage is a build error, not a
lapse.** Those stages have accumulated 587 nodes of memory about how requests of each class
get oriented, bounded, split and accepted — so the second request of a familiar shape is
answered by a walk rather than a re-derivation. That is Law 1 as a runtime loop.

**The gates fire in both directions.** The build door refuses to open without a berthed
`validate` packet claiming the ticket. The `PROVED` door refuses to open without a complete,
passing verdict artifact answering that same chart. Entry and exit are both gated, and both
were prose before they were physics.

**A failure is a disposition, not an argument.** A red at any gate has exactly two
destinations: fixed now, or a filed ticket. *"I flagged it"* and *"I asked"* are not
dispositions.

The system caught itself with this machinery on 2026-08-11, which is the best single
illustration available. A ticket whose whole purpose was *"a refused clearance must leave a
durable record"* went to cross into `PROVED` — and **was refused**. Retiring an unrelated
prose IOU had edited a file after its proof was sealed, moving the source fingerprint and
closing the validation's horizon. The refusal was recorded in the very store the ticket had
just built, carrying the actor, the target, the timestamp, the reason class, both
fingerprints, and the fix. The falsifier was answered by a real refusal rather than a fixture.

---

## 10. Memory — the graph trees

Cairn's long-term memory is a set of **graph trees**: a store where a query resolves by
traversing structure — cheap, no inference — and only a *miss* reaches the expensive
resolver, whose answer is then deposited as new structure. It is the memory-side expression
of the same thesis.

The vocabulary matters here, because collapsing two of these terms was a real and costly
error that every internal review missed until the author caught it:

- A **node** is the thing being remembered. It carries identity, provenance and standing. It
  belongs to **no tree**.
- A **leaf** is the thing *indexing* a node. It carries the address `database.tree.leaf`,
  plus a vector, weights, and two-way edges.

`database.tree.leaf` is an **address, never an identity.** Once separated, three results
follow that were invisible before: the shear that maintains the index runs on two-way links
and therefore **cannot touch a node** (index maintenance cannot damage a record of truth);
calving along dominant attractors *creates* the path a query walks rather than merely capping
its cost; and the whole design's provenance becomes legible — it came from a measured load
failure at 70,000 words and 2.5M bigram edges, where an edge update had grown past
**30 seconds** and was still climbing with the corpus.

**Standing is earned, not asserted.** A node minted during a query is *data*, and it starts
as a hypothesis. It earns standing across later, independent crossings. This is not
fastidiousness — it is a defense against a specific failure the system measured in itself on
2026-07-27, and which is the real content of the academic paper in this folder: **a
self-backfilling graph manufactures resolution.** A node minted from a question is
question-shaped, and therefore wins the similarity race for that question *by construction*.
The fix forces a three-valued verdict — RESOLVED / PROVISIONAL / UNRESOLVED — and reclassified
the system's own first success as PROVISIONAL.

Today's numbers, which are the design working rather than failing: 123 nodes, of which **3
have earned standing**, 119 are hypotheses and 1 has been refuted. A store where most nodes
were `earned` after five weeks would be a store that was confirming itself.

**What is not built:** the running schema still carries `tree` and `vector` on the node row.
The node/leaf separation is in the design documents and not in the database. There are no
per-tree leaf tables; calving and the shear are specified and unbuilt. See
[`GraphTreeMemoryTechnicalBrief.md`](GraphTreeMemoryTechnicalBrief.md).

---

## 11. The other half of the loop — learning as a required question

The single most portable idea in Cairn may be the smallest: **every charter must answer "how
does this component learn?", and silence is not an answer.**

The answers are genuinely varied, and the variety is the point:

- `db_domain`: *it doesn't* — "it is the fixed floor others build on." A valid answer, stated.
- `import_sieve`: *it doesn't, and the reason is the point* — "this is a mesh, and a mesh that
  adapts is not a measurement." What learns is the mesh's *precision*, by firing wrongly once
  and being narrowed, with the correction written into the code as a permanent tooth.
- `build_inspector`: *that is the whole point* — "we find a new thing, we add a sieve," each
  carrying the failure that seeded it.
- `orient`: it learns its scans from corrections. When the author catches the model reading a
  proxy instead of the thing, the check that would have caught it becomes a scan, and a proof
  refuses a scan whose provenance names no dated correction.
- `inference_domain`: the meter *is* the learning surface — tokens avoided climbing against
  tokens spent is the measured answer to "is the thesis paying off?"
- `harbor_master`, 2026-08-10: *"nothing is being harvested, and as of today the precondition
  is not met either — this field claimed it was."* The old text asserted an honest record of
  every cleared move existed. Measurement found **zero crossings had ever been cleared.**

That last one is the pattern's real value. The question is asked of every component, so a
component that has quietly stopped being what it says it is has one specific field where the
lie has to be maintained — and maintaining it is harder than correcting it.

---

## 12. The subsystem map

Each of these has its own pattern document in this folder. They are self-contained and
individually shareable; this section is the index.

| Subsystem | What it is | State |
|---|---|---|
| [**Intention-based development**](PatternIntentionBasedDevelopment.md) | intent beside implementation; the name forces the why | built, in use throughout |
| [**Gates and inspectors**](PatternGatesAndInspectors.md) | enforcement as gated ownership; deterministic filter stacks | built; several gates still prose |
| [**The workflow and its artifacts**](PatternWorkflowAndArtifacts.md) | node classes, workflow strings, the emit chokepoint | built; 423 journaled crossings |
| [**The development knowledge base**](PatternDevelopmentKnowledgeBase.md) | the commons: rulings, questions, troubles, slates | built; in daily use |
| [**Graph trees as an inference cache**](PatternGraphTreeCaching.md) | miss → resolver → deposit; the three intake paths | built at the node level |
| [**Tree architecture**](PatternTreeArchitecture.md) | node list, per-tree leaf tables, `database.tree.leaf`, calving | **designed, not built** |
| [**The librarian**](PatternTheLibrarian.md) | owner of the trees; the chatbot that learns always and summarizes on request | first face whole; tenure loop proved |
| [**The inference proxy**](PatternInferenceProxy.md) | one door, metered, cached, with an escalating provider ladder | built; 2,858 calls metered |
| [**The bus**](PatternTheBus.md) | the sole path for inter-device communication; four channels | **running**; 607 records from 20+ senders |
| [**The ground loop**](PatternTheGroundLoop.md) | one heartbeat; every device's shim hangs its probes on it | **running** as a live process |
| [**superclaude**](PatternTheLauncher.md) | the launcher and the rescue tier below the machinery | built, in daily use |
| [**What is planned**](PatternWhatIsPlanned.md) | the ruled ladder, the cocoon, the parallel inspectable clone | not built, and named as such |

---

## 13. What is measured

Full detail with instruments in [`FactSheet.md`](FactSheet.md). The five numbers that carry
the most weight:

**50.7%** — the share of Cairn's 85,690 lines of Python that lives in `proofs/`. More than
half the code is the code that tries to falsify the other half, and the ratio held as the
codebase grew from 52K to 85K lines. Not a testing culture; Law 8 showing up as a line count.

**36.1%** — the share of would-be inference tokens avoided by structure, over 2,858 real
calls. The thesis, measured — and climbing (was 34.3% at 1,400 calls).

**56** — charters compiled into the help surface. Each traces to a component, and nothing
renders without one.

**3 of 123** — librarian nodes with earned standing. Deposits are cheap; standing is not.

**423** — journaled workflow crossings across 36 append-only histories, over 36 days.

---

## 14. What would falsify this

An architecture document that cannot be wrong is marketing. Here is what would refute Cairn's
central claims, stated so that someone could go and check.

**The thesis fails** if the avoided-token fraction does not hold, or falls, as the workload
becomes less repetitive. The current 36.1% comes from a system building itself, which is an
unusually self-similar workload. If a genuinely varied workload drives the hit rate toward
zero, inference compilation is a property of this corpus and not of the method. The trend so
far is positive: from 34.3% at 1,400 calls to 36.1% at 2,858 — the cache pays more as the
corpus deepens.

**The physics claim fails** if rules keep migrating *into* the prose IOU list faster than they
migrate out. That list is designed to shrink monotonically. It is currently six entries plus
four residues. If it grows across a quarter, "enforced by physics, not policy" has become the
thing it was built to replace.

**The no-drift claim fails** the first time a charter and its code disagree without anything
going red. That is the whole bet of co-locating intent with implementation, and the system
currently admits it cannot detect this: *"a component whose code has stopped matching its
charter reads as whatever it last said about itself."* There is a filed ticket. Until it
lands, this is an open flank and is named as one.

**The self-application claim fails** if the measurements stop being taken. Every honest number
here has a corresponding moment where measuring was optional and inconvenient. The
harbor_master charter that said its precondition was met, and was wrong, is the specimen: the
system's defense is not that it does not produce such claims, but that measuring them is
routine enough to catch them.

**The whole method fails** if it does not survive a second person. Cairn has one user, who is
also its author, and several of its gates resolve to his judgment. A method that only works
for the person who invented it is a personal style, not an architecture. This is untested and
currently untestable.

---

## 15. What is and is not running

Restated plainly, because it is easy to lose in a document this long.

**Running, as of 2026-08-19:**

- **The runtime spine is alive.** The ground loop runs as a process, the web server as a
  systemd unit, the bus with 607 records from 20+ senders. This is green at "it runs" and
  red at "it has been observed running well" — the spine has been up for less than two weeks.
- **Zero live troubles.** 36 have been filed; all 36 are cleared. The normal operating state.

**Not built:**

- **The node/leaf separation is not in the schema.** No per-tree leaf tables. No calving, no
  shear.
- **The inference cache is exact-match.** Semantic canonicalisation is named as the next
  horizon and is unbuilt.
- **231 findings await the author's verdict.** Zero tickets stand at his gate, but the
  findings backlog is real.
- **Rules still enforced by prose** are enumerated in `CLAUDE.md` under *rules awaiting
  physics*, which is an explicit debt register rather than a wish list.

That list is not an apology. Under Law 9 it is the expected state of a building site, and the
list existing — measured, dated, addressed to specific tickets — is the claim being made.

---

## Appendix — vocabulary

Terms used here that are Cairn's own. Where a term has a native-domain meaning, Cairn's use is
meant to be derivable from it rather than memorised.

- **boat / voyage** — a unit of work moving through the workflow, and its passage. A ticket
  *is* the boat.
- **berth** — the durable address where a stage's emitted packet lands.
- **calving** — splitting a tree along a dominant attractor, as an ice sheet calves. Creates
  the path a query walks.
- **cast** — typing a node and binding the gates its type requires; the resolution pivot.
- **charter** — a component's `intention+why.json`: the summarized design.
- **chokepoint** — a single door every instance of some operation must pass through.
- **class-space / instance-space** — shareable code and record, versus per-machine runtime
  state.
- **commons** — the knowledge repo: if losing it loses knowledge, it belongs there.
- **the Form** — the contract every device satisfies: the values, and a uniform introspection
  surface.
- **graft** — bytes entering from outside, one ticket at a time, with a proof. Contrasted with
  *citing* an idea, which is free.
- **homeless intention** — one with no single code address, or many; berths in the commons.
- **horizon** — when a claim expires. Every stored answer and every seal carries one.
- **the quarry** — the archived predecessor. A place to take a stone from, never a dependency.
- **shear** — the maintenance pass that repairs the index. Runs on links, never on nodes.
- **sieve** — a deterministic filter that reds a build; the unit an inspector is made of.
- **standing** — a node's earned status: hypothesis → earned, or refuted.
- **summons** — a workflow step that must be satisfied, distinguished from one that may be
  skipped.
- **trouble** — the terminus of the escalation ladder; a failure with nowhere else to go.

---

*`press_office/CairnArchitecture.md`. The spine document; the pattern series in this folder
goes deeper on each subsystem. All numbers from [`FactSheet.md`](FactSheet.md), measured
2026-08-19. A draft awaiting the signature gate — the press office's pieces are signed stones
that learn by supersession, not by silent edit.*
