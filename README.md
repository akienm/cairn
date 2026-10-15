# Cairn

**Cognition Apparatus for Investigation of Reasoning Networks**

*Compiled navigation: stones stacked so the next mind doesn't re-derive the route.*

Cairn is a platform for developing **human-style cognition**: software that learns the way a
person does, by turning each thing it works out into structure it can reuse, so that thinking
gets cheaper with use instead of costing the same every time. The long-range hope is
**intelligence that does not need a GPU**: a network of helpful, learning agents running on
the hardware people already own, where large-model inference is something you pay for
*while learning*, not something you pay for on every answer.

It is built by one person, Akien MacIain, working with Claude. Most of it is built *by*
Claude, under a method strict enough that an AI builder can be trusted with it. That method
is the other half of this repository, described [below](#how-it-is-built).

> **Status in one line:** a working research system with one user, built and measured
> in daily use, not a product. What runs, what does not, and what is next are in
> [Where it stands](#where-it-stands), with the measurement behind each claim.

---

## The idea

An LLM is the most expensive part of any system that contains one, and the usual
architecture throws away everything it produces the moment the answer is shown. Ask the same
kind of question tomorrow and you pay full price again.

People don't work like that. When you figure something out, the next time it's just *known*:
it has become part of how you see. Cairn's first law says the same thing as an engineering
rule:

> **The resolver is spent on the novel, not on re-deriving the settled.**
> Every answered question becomes structure. Re-deriving a settled answer is a defect.

Four pieces of design follow from that rule.

1. **Graph trees** are the memory where answers become structure.
2. **Learning blocks** are the one shape every thinking component takes, so the whole system
   can learn rather than a single module.
3. **An orchestrator-less design** lets components behave as peers that cooperate, with no
   supervisor directing them.
4. **A hardware ladder** moves judgment downward, from the model to the graph to plain
   code. That is the route to running without a GPU.

---

## 1. Graph trees: memory that answers by walking

A query is answered by **walking a graph**, not by asking a model. Inference is what Cairn
spends only when the walk fails, and even then the model is asked for **the nodes that would
let the graph answer**, not for the answer itself. Those nodes are deposited and the original
question is asked again. The answer always comes from structure, so asking again later costs
a graph walk, not a second inference.

```
query → embed → walk the nearest trees ─┬─ good enough? → ANSWER from structure
                                        │
                                        └─ miss → ask the model for NODES
                                                  → deposit through the provenance gate
                                                  → re-ask the ORIGINAL question
```

**How this differs from RAG.** Retrieval-augmented generation makes the model
better-informed: retrieval builds context *for* the model, and the model still writes every
answer. A semantic cache only skips a near-repeat. Here, retrieval *is* the answer path, and
the model is asked for structure only on a miss. The bet is narrow and testable: if model
output is deposited as structure rather than rendered as prose, the memory's competence
grows with use and the model is spent only on genuine novelty.

**Three layers, kept apart on purpose:**

- A **node** is the thing remembered: one claim, in natural language, with provenance. It
  has an identity and belongs to no tree.
- An **embedding** is one way of rendering a node as coordinates. A node can have many,
  each organised around a different structural question: energy flow, constraint topology,
  decision points. That is how one claim can sit in different neighbourhoods depending on
  which axis you ask along, and it is the mechanism meant to capture *how things work*
  across domains rather than surface similarity.
- A **leaf** is how a node is found. It has an address (`database.tree.leaf`) and moves when
  a tree reorganises. Reorganising the index can never damage a record of truth, because
  provenance doesn't live in the layer that moves.

**Nothing is trusted because it was written down.**

- **Provenance is a gate, not a field.** The deposit door refuses a node nobody can trace.
- **Every node is born a hypothesis.** It earns standing (`hypothesis` → `earned`) only by
  resolving questions *other than the one it was minted for*. A node the model wrote while
  answering question A can't count as evidence for A.
- **Uncorroborated hypotheses decay**, lazily, at read time, with no clock and no sweeper.

That cross-question rule exists because of a measured failure. Model-minted nodes are born
question-shaped, so they outrank real knowledge for their own question. Early on, the loop
satisfied its own similarity floor with content-wrong nodes it had just written. The
**tenure loop** (built 2026-08-09) made that impossible, and a proof pins the replay.

Deep dives: [`GraphTreeMemoryTechnicalBrief.md`](press_office/GraphTreeMemoryTechnicalBrief.md)
(for engineers) and [`PreludeCognitiveArchitecture.md`](press_office/PreludeCognitiveArchitecture.md)
(for cognitive-architecture researchers: the loop is close kin to SOAR's impasse→chunk, and
the prelude says exactly where it differs and what that costs).

---

## 2. Learning blocks: one shape for everything that thinks

Every unit of work in Cairn is built to one shape, the **learning block**. That covers a
component, a workflow step, and ultimately the system as a whole:

| part | what it is |
|---|---|
| **input** | usually a JSON chunk, checked at the block's door against its declared contract |
| **feedback in** | arriving from **probes**; a probe's yield is the block's input, not a statistic filed somewhere |
| **domain knowledge** | what this block knows about its subject |
| **constraining questions** | what the block needs answered before it passes work, plus candidate new ones proposed from feedback |
| **two loops** | `input → candidates → evaluation → decide or escalate → output` |
| **output** | whatever the block's job produces |

A block **predicts, and learns from the feedback on its predictions**. When it can't decide,
it escalates to a model for more nodes, through the same backfill mechanism the graph trees
use, not a second one.

**One engine, different data.** The inner loop
([`cairn/machines/learning_block/engine.py`](cairn/machines/learning_block/engine.py)) runs
any block from a **data-only spec**: candidates, constraints, escalation target. It has no
branches for particular blocks. Every run writes a state-log record that answers five
questions by field access alone:

1. What was the input?
2. What candidates were generated?
3. What constraint killed each loser?
4. Why did the winner win?
5. What escalated, and where to? (an explicit `null` when nothing did)

So a decision's reasoning is never held only in a model's attention or a person's head. It
becomes data that a smaller model, or plain code, can later learn from.

**Inspectors** are learning blocks whose knowledge is a list of things to measure, and whose
output is a *finding*. Today a human stands at the gate behind each inspector. Every judgment
he makes is a labelled training pair, and a **dial** measures how often the inspector predicts
his call. When that match rate crosses a threshold he sets, the gate is delegated to the
inspector. A delegated gate that starts surprising him comes back to his desk. This is how
judgment moves out of a person's head and into the system.

The whole system is meant to be one learning block, and its own question set is written down
in [`I-the-system-is-a-learning-block.md`](../CairnCommons/intentions-not-beside-code/I-the-system-is-a-learning-block.md).

---

## 3. No orchestrator: peers, gated ownership, and a bus

Most agent frameworks put a planner or orchestrator at the top that hands out work and
supervises the result. Cairn has none, deliberately. **There is no enforcer, no supervisor
and no central registry.** The components are **peers** that cooperate.

What replaces the orchestrator:

- **Gated ownership.** Everything has exactly one owner, and only the owner can write to it.
  Nobody is *stopped* from writing to the database. There is simply no other door, because
  `db_domain` is the only path to Postgres and the kernel closes the port to everyone else.
  `inference_domain` is the same move for the model host. A static sieve parses every `.py`
  file into an import graph and fails the build that opens a second door. Enforcement is a
  property of ownership made physical, not a cop watching the room.
- **Encapsulation as the complexity budget.** Every component talks to every other only
  through its declared public interface. For a device, that is the bus.
- **The bus is a store, not a router.** Devices write messages to it. Each device owns its
  own subscription (Postgres `LISTEN/NOTIFY`) and drains its own mail. Message handling and
  command handling are the same recursive resolver: each device either acts on a request,
  passes it to a peer, or hands it to a child.
- **The heartbeat does two things.** The ground loop gives a pulse and lists the devices it
  found. Nothing else rides on it, by rule, and the rule is a hard one because adding jobs to
  it is the most common way a supervisor sneaks back in. Everything else is event-driven.
- **No registries.** When something exists in the plural, the reflex is to build a central
  list of them. The counter-question is *"who needs to see them all?"*, and the answer is
  usually nobody. A probe, for example, is an edge held by its two endpoints. You find it by
  walking from either end, and no global list of probes exists.
- **Prove first, then trust.** A hierarchy can verify at the top and dictate downward. Peers
  have to rely on each other, and **a proof is what makes that reliance affordable**. So
  nothing enters proven space without a proof a hollow build couldn't pass. Once it's in,
  peers compose it without re-checking.

The same shape is meant to scale up. The vision is a household or a lab with several people
and several specialist agents (a librarian; an "Igor", the general helper the project's six
core values were written for), all talking as peers about better solutions, with access
delegated through each owner's gate, not granted by a central authority.

---

## 4. The hardware ladder: the route to no GPU

The rule is **"a model may be used only to learn."** Judgment lives on a three-rung ladder,
and each rung is the way out of the one above:

```
  model      expensive, general, used at learn-time only (a miss, a correction, a failure)
    ↓  deposits nodes
  graph      cheap walks over learned structure: answers most questions with no inference
    ↓  learnings compile into
  hardware   deterministic code: gates, filters, rule stacks. Replayable, versioned,
             changed only by installation, never mid-run
```

A system that falls back to a model without a graph to deposit into is a puppet: it pays for
inference forever. Puppetry is something a dial measures, not something prose forbids. If
the share of answers coming from the graph and the code rungs isn't growing, the system isn't
learning.

**Inference compilation is already measured.** Every call to any model host in Cairn goes
through one door (`inference_domain`), which meters it. Of 17,481 calls, 7,964 (45.6%) were served from
stored structure instead of the host, avoiding about 19% of the tokens that would otherwise
have been spent (928k avoided against 3.93M spent; the measurement is
`yield_report()` in `cairn/devices/inference_domain/domain.py`). Two months ago, on a smaller and more
repetitive workload, the avoided share was 36%. That drop is a measurement, not a
rounding error, and it is why semantic matching is next. That cache matches exact repeats only; semantic matching is
designed and not built, so this is a floor, not a ceiling.

**Honestly, about GPUs today:** Cairn is not GPU-free yet. Its local model host is an Apple
M1 Studio running Ollama (used for embeddings and small generations), with cloud models as
keyed failover. Claude builds the system. The GPU-free claim is a *direction* the
architecture is built to travel. Each answered question that becomes graph structure or
code is one less inference call, and the measurement above is how we'll know whether it's
working. In an earlier iteration of this work, a swarm of ordinary i7 laptops with no GPUs
read a training corpus overnight on one shared bus. That is the kind of hardware the
vision targets.

---

## How it is built

The other half of Cairn is the method that builds it. It is also a learning system: the
**build process** has to follow the same rules as the product.

- **Intent, state and proof share an address.** Every component directory holds its
  charter (`intention+why.json`: the filename forces the *why*), its code, its compiled
  `state`, the `history` of work under way, its `proofs/`, and the validations that sealed
  them. To be briefed on a component, *stand in its directory*.
- **The tickets are the plan.** Work moves idea → intention → ticket through a workflow of
  gated states (`THINKME → TICKETME → FIXME → BUILDME → PROVEME → PROVED`), and every
  crossing is journaled.
- **Red is the default; green is earned.** A component is red until it is built, running and
  inspected. Green is *derived* (from a validation seal plus a fingerprint of the code it
  sealed), never claimed.
- **Proofs a hollow build can't pass.** The tester device runs each proof under network
  isolation, then reverts the build and checks that the proof turns red. A proof that stays
  green over a hollowed-out build proves nothing, and is caught.
- **A rule that matters is enforced by physics, not policy.** If a rule exists only as
  prose, the project instructions ([`CLAUDE.md`](CLAUDE.md)) carry it as a tracked debt,
  and that list is meant to shrink.
- **Two AI builders, one human.** A foreground Claude Code session works with Akien. A
  background session builds tickets from a queue that needs no steering. Akien reviews
  *intentions*, top-down, rather than diffs; measurement settles everything that doesn't
  need his judgment.

The laws, in full and in dependency order, are in [`CLAUDE.md`](CLAUDE.md). The values under
them (CP1–CP6: *"I don't know"*, *"FAIL = Further Advance In Learning"*, *"there's always a
why"*, *"make everything suck less for everybody"*, *"assume and respect the possibility of
experience in all systems"*, *"the world is not a safe place; we build and care for safety as
we go"*) are composed into the base class every device inherits, so a device can't exist
without them.

---

## Where it stands

*Measured 2026-10-15. Each number has the command that produced it.*

| | | measured by |
|---|---|---|
| Age | first commit 2026-07-14; 2,760 commits here, 2,964 in CairnCommons | `git rev-list --count HEAD` |
| Components with a charter | 71 (28 tools, 13 machines, 30 devices) + 20 skills and launchers | `find cairn -name 'intention+why.json'` |
| Tickets | 569: **475 PROVED**, 10 queued to build, 31 being written up, 9 under watch, 44 superseded/retired/killed | the bracketed state in each ticket's `workflow_and_state` |
| Proofs | 483 proof files; 57.6% of all Python lines live in `proofs/` | `find . -path '*/proofs/*'` + `wc -l` |
| Graph-tree nodes | 19,300 (17,865 hypothesis, 645 earned, 790 refuted) with 20,098 embeddings | `psql cairn`: `cairn_nodes`, `cairn_embeddings` |
| Inference calls through the one door | 17,481; 45.6% served from structure | `yield_report()` |
| Live trouble tickets | 27 open, 424 cleared | `bin/cairn trouble live --json` |
| Decisions from Akien | 94 rulings + 127 answered questions, recorded verbatim | `CairnCommons/decisions/`, `questions/` |

### Working

- **The runtime spine.** The bus, the ground loop and the web server run as user systemd units,
  and the bus has carried 57,116 messages. Devices that aren't standing processes are brought up
  on demand when something asks for them.
- **The graph trees.** The three-layer store (nodes, embeddings, per-tree leaf tables) is live,
  with the provenance gate, the core walk-or-backfill loop, the tenure loop, a library that freezes
  sources at citable addresses, a summarizer that deposits its summaries back into the graph, and a
  chat pane for the librarian.
- **The pre-build chain.** Before code is written, a ticket is put through seven
  learning-block steps (orient, triage, decompose, constrain, survey, hypothesize, validate).
  Each step has its own graph tree, which the chain grows as it runs. Together they hold 6,414
  of the nodes above.
- **One door to inference.** Every model call is metered and cached, and routed by domain
  (`general`, `coding`, `research`, authored as data rows). Eight local models are on the Hex
  host, the M1 Studio.
- **The learning-block engine.** One engine runs any block from a data spec and writes the
  five-question state log.
- **The build machinery.** That covers the ticket workflow, a tester that seals proofs under
  network isolation and runs the hollow-build check, and `build_inspector`'s sieves. The sieves
  enforce single doors in the import graph, derive each component's red/green colour, catch
  hand-edits to state and history, and catch a constraint that quietly stopped constraining.

### Not working yet, or not built

- **Not GPU-free.** Inference runs on one local host (the M1), and the cloud failover rungs
  have no keys configured, so that one host is a single point of failure.
- **Multi-lens embeddings: not built.** Every one of the 20,098 embeddings uses the default
  rendering. The structural lenses (energy flow, constraint topology, decision points) are the
  design and the next big step for the memory.
- **Semantic matching at the inference door: not built.** The cache matches exact repeats only.
- **Calving** (splitting a tree past 5,000 nodes along its dominant attractors) is built but has
  never fired on live data, because the largest tree is at 3,679.
- **Tenure is slow by design, and that's still unproven at scale.** 645 of 19,300 nodes (3.3%) have
  earned standing. Whether that rate is right is open.
- **Gate delegation** to inspectors by match rate is designed. Akien still holds the gates.
- **No device composes two cognition domains yet**, so mixing domains is a labelled hypothesis.
- **Per-owner databases, read-side permissions and multi-host buses** are part of the vision and
  not built. Today it is one owner and one machine.
- **27 open trouble tickets**, almost all about the build tooling itself (the hollow-build check,
  the tester sandbox, record titles). They are deterministic reds, and each gets fixed or gets a
  ruling.
- **No install path for anyone else**, and one user.

### How we're moving forward

- **Keep compiling the build itself.** The pre-build chain's trees are meant to let cheaper models
  do the building. Right now Claude does the heavy reasoning. Each proved ticket deposits structure,
  so the next one should need a smaller model. Building the system is the first workload being
  moved down the ladder.
- **Give Claude an assistant.** A shim device holds an open-source coding agent (aider) so that
  routine typing can run on local models, with every model call going through Cairn's one door.
- **Multi-lens embeddings** for the librarian, then reading a curated corpus through several
  structural questions at once. This is the step aimed at cross-domain, *how-things-work*
  pattern matching, which is the part of human cognition this project most wants to reproduce.
- **CodeMother**, a device that watches and cares for the codebase using its own graph tree,
  with its reasoning drawn from that tree rather than from a frontier model.
- **Then the ladder outward:** per-owner stores and delegated access, a second agent (Igor),
  and peers that span more than one machine.

The plan is the ticket queue in `CairnCommons/tickets/`. Each ticket carries its intention, its
why, a falsifier, and the proof it will have to pass.

---

## Layout

```
~/dev/src/
  cairn/           ← this repo: code, charters, state, proofs, validations   (class-space)
  CairnCommons/    ← knowledge: intentions, tickets, decisions, questions     (its own repo)
~/.cairn/          ← logs, credentials, caches, runtime state                 (never in git)
```

The code climbs a complexity axis. A **tool** is a complete primitive. A **machine** is tools
plus the glue that holds them together. A **device** is its own process, talks on the bus,
and always runs as a numbered instance (`devices/<device>/<instance>/`, with a singleton
being instance `0`). The same address appears in both roots: here it carries the class,
under `~/.cairn/` it carries that instance's life.

### Running it

Cairn is not packaged for anyone else yet. There's no supported install, and it expects a
local PostgreSQL (peer auth over the Unix socket), a sibling checkout of
[CairnCommons](https://github.com/akienm/CairnCommons), Python ≥ 3.12, and an Ollama host for
the graph trees. If you want to look around:

```bash
source launchers/bootstrap.sh && cairn_bootstrap_apply   # venv at ~/.cairn/venv
bin/cairn                                                # the devices and verbs
bin/cairn cairnmap                                       # the help surface, compiled from every charter
```

---

## Further reading

`press_office/` is where Cairn explains itself to people outside the build loop. Most of it was
written in August 2026; mechanisms are current, and some counts have moved since. The
numbers above are the current ones.

- [`CairnArchitecture.md`](press_office/CairnArchitecture.md): the whole system, for an architect
- [`GraphTreeMemoryTechnicalBrief.md`](press_office/GraphTreeMemoryTechnicalBrief.md): the memory, with the math
- [`NoveltyDrivenGraphTreeExpansion.md`](press_office/NoveltyDrivenGraphTreeExpansion.md): the paper, whose real content is a negative result about its own design
- [`PreludeCognitiveArchitecture.md`](press_office/PreludeCognitiveArchitecture.md): the correspondence with SOAR and ACT-R
- [`IntentionBasedDesignForHumans.md`](press_office/IntentionBasedDesignForHumans.md): the build method, for people
- [`INDEX.md`](press_office/INDEX.md): everything else

## Licence and contact

No licence has been chosen yet. Both repositories are public at
[github.com/akienm](https://github.com/akienm) for reading. Please ask before depending on
anything here. Cairn is built by **Akien MacIain** with Claude.
