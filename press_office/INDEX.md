# The Cairn press office — the shelf

*What is here, what it is for, what supersedes what, and what is known stale.*

This is **the shelf, not a page.** Every other document in this folder is a signed stone
that learns by supersession — a shipped explainer must not change silently under its
readers. This index is the exception that makes that discipline usable: it is edited in
place, because a shelf whose cards do not match the shelf is worse than no cards.
(`WorkflowDefinition.md` is the other in-place exception, for its own stated reason.)

**Retirement is Akien's signature.** Nothing here is deleted or moved by the drafter. A
piece that has been overtaken is marked overtaken and stays on the shelf until its owner
says otherwise.

---

## Start here

| If you are… | Read |
|---|---|
| new to all of this | [`CairnArchitecture.md`](CairnArchitecture.md) — the spine |
| checking a number | [`FactSheet.md`](FactSheet.md) — every measurement, with its command |
| here for one pattern | the pattern series below; each is self-contained |
| implementing the workflow | [`WorkflowDefinition.md`](WorkflowDefinition.md) — the source of truth |
| evaluating the research claim | [`NoveltyDrivenGraphTreeExpansion.md`](NoveltyDrivenGraphTreeExpansion.md) |

---

## 1. The measurement component

**[`FactSheet.md`](FactSheet.md)** — measured 2026-08-11 against `cairn` and `CairnCommons`
at named commits. Every number in the pattern series and the spine traces here, and here
only.

> **The rule the shelf runs on: a piece cites the sheet; it does not restate a
> measurement.** Fifteen documents each carrying their own numbers are fifteen documents
> that drift apart. When the numbers move, they move here once.

If a piece and the sheet disagree, **the sheet is right and the piece is stale.**

---

## 2. The spine

**[`CairnArchitecture.md`](CairnArchitecture.md)** — the whole system in one document: the
measurement that caused it, the thesis it tests, the laws it runs on, the structures those
laws force, and what is and is not built. Deliberately not the deepest treatment of
anything; §12 is the map into the pattern series.

---

## 3. The pattern series

Twelve documents on one fixed skeleton — *the measured failure · the pattern · how it is
enforced · what it costs · what would falsify this · what is built, and what is red.* Each
stands alone and is individually shareable. Each opens with the failure that caused it,
because a pattern without its failure is a preference.

| # | Document | The move |
|---|---|---|
| 1 | [`PatternIntentionBasedDevelopment.md`](PatternIntentionBasedDevelopment.md) | intent, its voyage, and its proofs share an address |
| 2 | [`PatternGatesAndInspectors.md`](PatternGatesAndInspectors.md) | enforcement is gated ownership, not a supervisor |
| 3 | [`PatternWorkflowAndArtifacts.md`](PatternWorkflowAndArtifacts.md) | the workflow string is parsed by the door that gates it |
| 4 | [`PatternDevelopmentKnowledgeBase.md`](PatternDevelopmentKnowledgeBase.md) | if losing it loses knowledge, it is commons |
| 5 | [`PatternGraphTreeCaching.md`](PatternGraphTreeCaching.md) | a miss resolves, deposits, and is never asked again |
| 6 | [`PatternTreeArchitecture.md`](PatternTreeArchitecture.md) | separate the thing remembered from the thing indexing it |
| 7 | [`PatternTheLibrarian.md`](PatternTheLibrarian.md) | the conversation articulates the memory, never answers for it |
| 8 | [`PatternInferenceProxy.md`](PatternInferenceProxy.md) | one door to every model; the cheapest answer is never the one you already have |
| 9 | [`PatternTheBus.md`](PatternTheBus.md) | communication has one door, so observability is never a separate build |
| 10 | [`PatternTheGroundLoop.md`](PatternTheGroundLoop.md) | one daemon in the whole system, and all it does is beat |
| 11 | [`PatternTheLauncher.md`](PatternTheLauncher.md) | from parse to exec, nothing may abort |
| 12 | [`PatternWhatIsPlanned.md`](PatternWhatIsPlanned.md) | publish the roadmap the way you publish the code — red until measured |

**Reading order if you want the argument rather than a reference:** 1 → 2 → 3 → 5 → 6 → 12.
Documents 4 and 7–11 are subsystem detail and can be read in any order.

**Pairs that are deliberately distinct, not duplicates:**

- **5, 6, and 7** are the same subject from three angles — the *mechanism* (how a miss
  becomes memory), the *storage* (how it is laid out so it survives scale), and the
  *device* (the thing that owns it and talks). None restates another; each cross-links.
- **9 and 10** are peer substrates: the bus owns communication, the ground loop owns time.
  Each names the other.

---

## 4. Depth references

**[`GraphTreeMemoryTechnicalBrief.md`](GraphTreeMemoryTechnicalBrief.md)** — *draft,
awaiting the signature gate.* The memory system for someone who builds AI systems for a
living: the three intake paths, the amortization argument, the node/embedding/leaf
separation, calving and the shear, and a map of the closest outside work. **Documents 5, 6,
and 7 cite this rather than restate its cost model.**

**[`NoveltyDrivenGraphTreeExpansion.md`](NoveltyDrivenGraphTreeExpansion.md)** — *draft,
awaiting the signature gate.* The paper. Two-tier novelty and a defense against
self-confirming retrieval; its real content is a **negative result about our own design**,
measured 2026-07-27. Names its target venues.

**[`WorkflowDefinition.md`](WorkflowDefinition.md)** — the source of truth for the workflow,
and the one piece here that **learns in place**. If a skill, charter, ticket, or device
disagrees with it, the disagreement is a defect to fix rather than a difference to
reconcile.

---

## 4b. For sending outward

**[`OutreachPacket.md`](OutreachPacket.md)** — *drafted, awaiting the signature gate;
nothing has been sent.* Who to show this to and in what order (cognitive architecture →
neuro-symbolic → dynamic graph learning, ordered by *who can falsify us soonest*), the named
venues, **the document-components scheme** — a per-field Part I, with Part II and Part III
shared verbatim — and what would count as signal, stated in advance so the answer cannot be
reinterpreted after it arrives. Opens with the caveat that the target list and the
"nobody does this" claim rest on one secondary source.

**[`PreludeCognitiveArchitecture.md`](PreludeCognitiveArchitecture.md)** — *Part I of three,
prelude 1 of 3.* The architecture in SOAR/ACT-R/Sigma vocabulary: the correspondence, the
one divergence (the resolver is external and general, which is where every other difference
comes from), the failure mode their design never had to face, and four questions that are
better answered *"we did that in 1994"* than *"how interesting."* Also the worked example of
the prelude shape.

---

## 5. The founding pieces

**[`IntentionBasedDesignForHumans.md`](IntentionBasedDesignForHumans.md)** — the first piece
ever shipped from this folder, 2026-07-15. An explainer for an intelligent outsider, gentle
register, no prior context assumed.

> **Overtaken as the pattern statement, retained as the on-ramp.**
> [`PatternIntentionBasedDevelopment.md`](PatternIntentionBasedDevelopment.md) is the
> current statement of the same pattern: measured, on the series skeleton, with its
> falsifiers named. The founding piece is *gentler and less complete*, and it is kept
> because "read the friendly one first" is a real need the new one does not serve.
> Where the two disagree on a number or on what is built, **the newer one and the fact
> sheet are right.** Retirement, if it ever happens, is a signature.

**[`IntentionsBasedProgrammingClaudeFileTree.md`](IntentionsBasedProgrammingClaudeFileTree.md)**
— *draft, awaiting the signature gate.* A worked example from the inside: the assistant
describing its own cross-session memory tree as an instance of the pattern. Companion to
the founding piece; first-person voice. **Not superseded** — nothing else in the folder
covers this ground.

---

## 6. Known stale — Law 3 applied to the shelf itself

An index that only lists is a catalogue. This section is what makes it an instrument.

| Document | What is stale | The correction | Status |
|---|---|---|---|
| `GraphTreeMemoryTechnicalBrief.md` §2 and §8 | states the tenure loop is *"designed and not yet built"* and that *"every node in the store honestly still reads `hypothesis`"* | **the tenure loop was built and proved 2026-08-09**; nodes have since earned standing | corrected in the piece, 2026-08-11 |
| `NoveltyDrivenGraphTreeExpansion.md` §falsifiers | lists *"every node remains `hypothesis` in live use"* as an open falsifier of the design | that falsifier has been **survived**, not merely asserted — and the surviving is the news | corrected in the piece, 2026-08-11 |
| `IntentionBasedDesignForHumans.md` | predates the fact sheet; its numbers were true when written and are not re-measured | cite [`FactSheet.md`](FactSheet.md) for any figure | on the shelf, marked |

**Nothing in this table is a defect in the writing.** A signed stone is allowed to age; what
is not allowed is aging *silently*. This section is the whole reason the shelf is edited in
place.

---

## 7. What the shelf does not have yet

- **Two of three field preludes.** The components scheme is
  [`OutreachPacket.md`](OutreachPacket.md) §3 and prelude 1 is written; the neuro-symbolic
  and dynamic-graph-learning preludes are red.
- **A field-prelude compiler**, deliberately. It waits on three preludes, because a compiler
  written against one would freeze whatever that prelude happened to do into a schema.
  Until then assembly is a human concatenating three files, which costs a minute and is
  honest about how much structure has been earned.
- **Anything sent.** The outreach packet is a plan, and a plan is a hypothesis.
- **A second reader.** Every piece here was written by one model under one human's
  correction, on one machine. *"Does it survive a second person?"* is the standing
  falsifier over the entire folder, and it is unmeasured.

---

*Shelf card for `press_office/`. The charter is `press_office/intention+why.json`. This file
is edited in place by design; every other piece here learns by supersession, and retirement
is the owner's signature.*
