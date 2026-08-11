# Pattern — The development knowledge base

### One test decides where a fact lives: *if losing it loses knowledge, it's commons*

> **The move.** Everything the project *knows* — as distinct from everything it *does* — lives in
> a second repository, split into typed stores, each with its own charter and its own door. A
> store cannot exist without writing down what it is for, and the type is the thing that makes
> "what is open?" answerable at all.

---

## 1. The measured failure

**A ruling that existed only as conversation.** Measured 2026-07-31: four times in one session
the author's stated intent and the code's shape disagreed, **and the code won.** Two hours went
to one of them — his ruling that a particular compiled artifact was retired existed only in the
transcript, while the compiler that wrote the file existed as source with green proofs.

The lesson, stated plainly:

> **When drift comes, written beats spoken — and there was nothing written on his side of the
> room.**

That is not a discipline problem. It is a missing artifact. A ruling with no address is a ruling
the next reader reconstructs *from the code*, which inverts the direction authority actually
flows: **code and its proofs are evidence of what was built, never of what is intended.** A green
proof means conformance to a spec, and a spec is exactly what a ruling changes.

The store this now writes into already existed and held exactly one entry — authored *after* a
different ruling got lost and had to be reconstructed from a transcript.

**An idea spoken and gone.** Without an address for raw capture, an idea surfaces, the
conversation moves on, and there is nothing for the next step to reach for. The author's framing,
2026-08-04: *"capture gets `/idea [prose]` and it's a one and done. its end state is just when
you and I move on to the next thing. the gate is just captured text that I can interpret later."*

**Continuity held in a context window.** Sessions end at a context limit. Anything the next
session needs and cannot re-derive was, until it had a store, simply lost.

---

## 2. The pattern

### 2.1 The commons test

Three roots hold state, and one question sorts them:

| Root | Holds | Test |
|---|---|---|
| the code repo | code, charters, `state`/`history`, proofs | shareable, and not knowledge |
| **the commons** | intentions, decisions, tickets, questions, troubles, notes, ideas, slates | **if losing it loses knowledge, it's commons** |
| instance-space | logs, credentials, flags, cached state | neither shareable nor knowledge; never in git |

The commons is its own repository. That is deliberate: it must be carryable to a bare machine on
its own, and it must survive the code being wrong.

### 2.2 Typed stores, each with a charter

Eleven stores as of measurement. Each has a `_charter+why.json` — the same forcing convention as
a component's `intention+why.json`, with the underscore marking it as authored rather than
compiled.

| Store | Holds | Count |
|---|---|---|
| `tickets/` | cast nodes — the universal work unit | 101 |
| `decisions/` | the author's rulings, verbatim plus a checkable reading | 33 |
| `notes/` | frictionless captures: prose and a timestamp | 40 |
| `slates/` | session-boundary continuity records | 77 |
| `troubles/` | live failure records | 11 |
| `ideas/` | captured verbatim, interpretation deferred | 9 |
| `questions/` | two declared lanes (see §2.4) | 6 |
| `adjudications/` | things needing a decision before they can be anything else | 4 |
| `node_classes/` | what kinds of node exist, and their gate-sets | 6 |
| `intentions-not-beside-code/` | the homeless intentions | — |
| `intentions-congruency-lab/` | a compiled copy of every intention in the system | 49 |

**A store cannot exist without writing down what it is for.** That is the artifact-proliferation
resistance, and it is why there are eleven rather than forty.

### 2.3 The distinctions that earn their keep

The stores look similar from outside. Each split exists because a question could not be asked of
a mixed store.

- **Idea vs note.** A note is a fact worth keeping. An idea is a candidate for work. The question
  *"what have I not turned into work yet?"* cannot be asked of a mixed store. (The case for
  collapsing the two is recorded inside the ideas charter, rather than argued away.)
- **Ticket vs everything.** A ticket carries **no domain.** An "inference ticket" and a
  "concept-piece ticket" are the same artifact with a different class field, because workflow
  rides on node-class rather than on the node's identity. And the load-bearing consequence:
  **the ticket's state field *is* the pipeline instance.** No orchestrator holds a second copy of
  where work stands, so the state of the tickets is the state of all things, always.
- **Adjudication vs trouble.** A trouble is a failure with nowhere else to escalate. An
  adjudication is anything needing a decision — by the author, by the model, or by the two
  together — before it can be anything else. A trouble that needs work before it can be ticketed
  goes there. The author, 2026-08-02: *"maybe just everything that needs an adjudication by you
  or me or us together is inherently a question more than it's anything else?"*
- **Homeless intentions vs beside-code charters.** Law 5 says intent shares its implementation's
  address — which silently assumes every implementation *has* an address we own. A hook in a
  settings file, a package on the box, a widget in a dotfile directory: real built things,
  fulfilled intentions, and nowhere in the code repo to be beside. Without this store they are
  lost.

### 2.4 The question store's two lanes, never mixed

- **The probe corpus** — the questions the system *asks*. Reusable, fired deterministically at
  nexuses over varying content, each carrying a measured **yield**.
- **The open lane** — the questions the system *has*. The tree's frontier, each asking "what's
  beyond here?"

> **A probe is fired again and again; an open question is resolved once and retired at its
> source.**

The reason probes must become first-class records rather than staying embedded in skill files:
**a probe inside a markdown file is asked but never measured.** No probe has ever been retired
for uselessness, and no probe has ever earned tenure, because the promotion-and-retirement
mechanism has no substrate until the probes are records.

### 2.5 The ruling intake door

The failure in §1 produced a specific artifact. A ruling becomes a schema-gated packet carrying
**the author's words verbatim** beside a one-line reading, plus the two lists that make the
reading checkable: `what_dies` and `what_conforms`.

The door refuses, with every reason at once: a malformed packet; a path that is not on disk at
intake; a reading longer than 280 characters or wider than one line; and **a packet that confirms
itself.** It stamps `confirmed: false` and measures a `sha256` of each conformer, so neither
field can be authored by the thing being gated.

`verify` is the mechanical verdict — **UNCONFIRMED** until signed off, **STILL ALIVE** if
something ruled dead is on disk, **UNTOUCHED** if a conformer is byte-identical to intake,
**VANISHED** if a conformer was deleted instead of changed. A hook reports every red ruling every
turn and never blocks.

**Retirement is supersession, never deletion.** `supersede <old> <new> "<evidence>"` retires a
misfiled packet by stamping the *confirmed successor* — never the retired record, which stays on
disk byte-identical and visible, but no longer open. It refuses, with every reason at once: empty
evidence, unknown ids, self-supersession, an **unconfirmed** successor (*a guess cannot outvote a
signature*), a doubled retirement, and retirement by a packet that is itself retired.

### 2.6 The corpus is its own training signal

Every ruling packet is a **labelled pair** — the author's words, and the reading of them. So the
store accumulates exactly the training signal for the failure it exists to catch: the rulings
where he red-penned the reading are the ones where the code's shape pulled the reader off his
intent, and they sit together, in one folder, sorted by date.

There is a second signal in the verdict trail. A ruling that goes red *long after* confirmation
is one that was obeyed and then drifted from — a different defect from misreading it, wanting a
different fix.

Neither is compiled yet. The store is small enough to read by hand, and building a learner over
an *n* of one is the eagerness the design explicitly warns against: **migrate on evidence, not on
eagerness.**

---

## 3. How it is enforced

**Physics today:**

- Every store has a charter; anything `_`-prefixed is authored and never touched by a compiler.
- The ruling intake door's ten-plus refusal conditions, including the self-confirmation refusal
  and the authored-fingerprint refusal.
- The compiled copy folder is regenerated **whole** by a single owner-gated door, byte-identical
  per file, so a deleted source takes its copy with it and a collision raises rather than
  silently dropping.
- The slate door refuses a write whose recorded git heads do not match the live repositories —
  so "I looked at what happened this session" cannot be faked from the transcript.
- The `/idea`, `/intent` and `/sorted` doors each refuse an incomplete packet with every lack
  named in one pass, and record the refusal as data.

**Still prose (tracked as debt):**

- **Nothing makes anyone open a ruling packet.** The hook sees packets that exist, not rulings
  never recorded. The intake door is only as good as the habit of walking through it.
- The compiled copy folder is derived-never-authored, but regeneration makes a hand-edit
  *transient* rather than impossible, and nothing announces one while it lives.
- Nothing reds a component that keeps relational state outside the store primitives — *where data
  lives* is a different question from *who imports a driver*.

---

## 4. What it costs

**A second repository.** Two clones, two histories, two push targets. The slate door's
head-matching check exists partly because two repositories can disagree about what happened.

**The slate is a standing context cost.** Slates are read unconditionally at every session open,
which makes a slate's *length* a permanent tax rather than an optional one. The ceiling is
measured (10,000 characters; the corpus median is around 6,900) and **long slates are the defect,
not the flex.**

**Human gates accumulate here.** 12 tickets stand at the author's gate; 68 findings await a
verdict. The stores make the backlog visible, which is the point, and do nothing to shrink it.

**Verbatim capture is unedited.** The ideas store keeps prose exactly as spoken — three rambling
sentences stay three rambling sentences — because *capture is the one moment where translation
loss is zero, and tidying spends it.* The cost is a store that does not read like documentation.

---

## 5. What would falsify this

- **A store nobody reads.** Each store's justification is a question somebody asks of it. If the
  question stops being asked, the store is overhead — and the notes/ideas split is the first
  candidate for collapse.
- **Rulings stop being recorded.** The corpus can only train on what walks through the door; the
  door cannot make anyone approach it.
- **The reading is never red-penned.** If no ruling's one-line reading is ever corrected, either
  the readings are perfect or nobody is checking, and the base rate says which.
- **Slates grow past their ceiling.** A continuity record that costs more to read than it saves
  is a net loss at every session open.
- **The commons and the code disagree without anything going red.** Same open flank as the
  charter pattern: co-location and typing prevent a *silent* second copy, not a *stale* one.

---

## 6. What is built, and what is red

**Built.** Eleven chartered stores holding 101 tickets, 33 rulings, 40 notes, 77 slates, 11
troubles, 9 ideas, 6 questions, 4 adjudications, 6 node classes, and a 49-file compiled copy of
every intention in the system. Doors on `/idea`, `/intent`, `/sorted`, `/saveslate` and ruling
intake, each refusing completely on the first pass and recording the refusal. 379 commits in 28
days — **more commits in the knowledge repo than in the code repo** (268).

**Red.**

- **The probe corpus is unstarted.** The question store's first lane has no records, so no probe
  has earned tenure or been retired for uselessness; the promotion mechanism has no substrate.
- **Nothing forces a ruling to be recorded, or a recorded ruling to be read.**
- The verdict trail is uncompiled; both training signals are read by hand.
- 12 tickets and 68 findings stand at a single human gate, which is a measured property of the
  design rather than a queue that will drain.

---

*Pattern document, `press_office/PatternDevelopmentKnowledgeBase.md`. Part of the Cairn pattern
series; the spine is [`CairnArchitecture.md`](CairnArchitecture.md). All numbers from
[`FactSheet.md`](FactSheet.md), measured 2026-08-11.*
