# Prelude — for a cognitive architecture researcher

### Cairn: Cognition Apparatus for Investigation of Reasoning Networks

*Part I of three. Written for someone who thinks in impasses, chunks, activation, and utility.*

**Prelude 1 of 3.** Part II is
[`NoveltyDrivenGraphTreeExpansion.md`](NoveltyDrivenGraphTreeExpansion.md) — the
architecture and the protocol. Part III is [`FactSheet.md`](FactSheet.md) — every
measurement with the command that produced it. Parts II and III are shared verbatim across
all preludes; this part is the only one written for you.

---

## 1. Why you are the first reader

Because you are the person most likely to tell me this was solved before I was writing
software, and that is the outcome I am optimising for.

The system this describes is a working one, in daily use, that I did not build as
cognitive-architecture research. I built it to stop re-deriving answers I had already
found. Somewhere in the middle of building it I noticed that its central loop was a
worse-specified version of something your field has had since the 1980s — and that the
place where it *does* differ is precisely where it acquires a failure mode your version
does not have.

So this prelude is short and it has one job: put the correspondence in front of you
quickly enough that you can tell me which of my problems are already named.

---

## 2. The correspondence

The system's core loop, in one line: **a question arrives, the graph is searched, and on a
miss the miss is resolved by an external model, the result is deposited, and the original
question is re-submitted against the enlarged graph.**

### 2.1 SOAR

| SOAR | here |
|---|---|
| impasse — no operator applies | similarity floor miss: best score $s^* < \theta$ |
| subgoal created to resolve the impasse | the question is put to an external resolver |
| the result is **chunked** into a new rule | the result is **deposited** as nodes, and the question re-submitted |
| the impasse does not recur | the walk now resolves it without a call |

The shape is the same and I want to be plain that I did not arrive at it by reading you. I
arrived at it by having a cache miss and being annoyed about it. The correspondence is
evidence that the shape is forced by the problem, which is a compliment to the design you
already had.

### 2.2 ACT-R

The retrieval side maps onto declarative memory more closely than onto production memory:

| ACT-R | here |
|---|---|
| a declarative chunk | a **node** — one claim, in natural language, with provenance |
| base-level activation, decaying with time and use | **standing** plus a decay horizon evaluated lazily at read |
| spreading activation from context | a walk over the embedding neighbourhood, weights moving with use |
| utility learning over production selection | **tenure** — promotion earned by resolving questions the node was not minted from |

I am fairly sure that last row is the one where I am about to be told I have re-derived
something with worse notation. I would like to be.

### 2.3 Sigma

The correspondence I have not been able to work out, and would most like help with, is
Sigma's. The graphical unification — one representation carrying what other architectures
split across memory types — is close in spirit to a design here that runs the same machinery
for a cadence-fired probe and an internally-triggered one, and stores the walked path rather
than a separate edge table. Whether that is a real correspondence or a surface rhyme, I
cannot tell from outside.

---

## 3. The divergence, stated sharply

**The resolver is an external, general model rather than the architecture's own
problem-solving.**

That single substitution is the whole difference, and every other difference falls out of
it:

- **The deposited structure is not derived from valid internal reasoning.** A SOAR chunk
  summarises reasoning the architecture actually performed. My deposit summarises what a
  language model said when asked. Those are not the same epistemic object and cannot be
  trusted the same way.
- **Therefore every node carries provenance as an admission requirement**, not as
  metadata. The deposit door *refuses* a node nobody can trace. A fabricated attribution in
  a draft is a bad afternoon; in a memory node it is a permanent resident every future walk
  may ground on.
- **Therefore every node carries a standing** — `hypothesis` at birth, `earned` by tenure,
  `refuted` when retired — so a claim can be doubted, expired, or invalidated without being
  deleted.

Nothing is trusted because it was written down. That sentence is doing structural work
here, not rhetorical work.

---

## 4. The problem you do not have

This is the part worth your time, and it is a **negative result about my own design**,
measured on 2026-07-27.

If a system resolves a miss by asking a model, and deposits the answer, and then re-asks
the original question — **the newly deposited nodes are question-shaped.** They were minted
from that question. They win the similarity race for it by construction.

Measured: cosine **0.8568** and **0.8295** on two separate crossings, both comfortably over
the acceptance floor, both carried *entirely* by nodes the question itself had just
created. Every provenance field was honest. Every log line was true. A consumer reading the
verdict would have called the question answered.

> **A self-backfilling graph can manufacture resolution where the graph held nothing.**

Your chunking mechanism has no analogous problem, because a chunk is derived from the
architecture's own valid reasoning — it cannot be *fabricated in response to the query* in
the way mine can. So your design never had to grow a defense against it, and mine does.

The defense, in brief: define the **mint relation** $\mu(n)$ — the question a node was born
from — and compute a second score $s^\dagger$ over only those nodes *not* minted from the
current question. Where $s^* \ge \theta > s^\dagger$, the verdict is neither resolved nor
unresolved; it is **`PROVISIONAL`**, and it names its own basis. Promotion to `earned`
requires the node to carry the resolution of at least $m$ questions it was **not** minted
from, within a window, or it expires.

One sentence: **a node earns residence by being useful to a question that did not create
it.**

That mechanism was designed, then built and proved on 2026-08-09. Measured 2026-08-11 over
88 nodes: 80 `hypothesis`, 3 `earned`, 1 `refuted`. Three out of eighty-eight after two
weeks is the loop working rather than failing — a store where most nodes read `earned` this
early would be a store confirming itself. It is also *n* = 88, which is an existence proof
of the mechanism and evidence about nothing else.

---

## 5. The ask

Four questions, and every one of them is better answered *"we did that"* than *"how
interesting."*

1. **Is the manufactured-resolution failure named in your literature?** I have looked with
   the tools available to me and found the closest neighbours to be about
   self-confirmation in retrieval rather than about structure a query generated for itself.
   If speedup learning met this under another name, I want that name.

2. **Is tenure a rediscovery of the utility problem?** My understanding — which is
   second-hand and may be wrong in the details — is that speedup learning ran into learned
   rules whose retrieval and match cost exceeded their benefit, and that a substantial
   literature followed on when a learned rule should be kept. If tenure is that literature
   with different words, the correct move is to borrow the equations and delete mine. ACT-R's
   activation and decay in particular look directly applicable, and I would rather cite than
   re-derive.

3. **Is my promotion criterion measuring the wrong thing?** Promotion counts *distinct
   questions a node resolved that did not mint it.* The obvious objection is that this
   measures **popularity rather than correctness** — a node that is merely well-connected
   accrues witnesses. I have written that objection into the paper's falsifier list rather
   than answering it, because I cannot answer it from inside.

4. **What should I be reading?** Concretely: chunking's known failure modes, over-general
   and expensive chunks, utility-based retention, and the meta-level/object-level split. I
   am not asking for a reading list out of politeness. Re-deriving a settled answer is
   treated here as a defect, formally — it is the system's first law — so a citation that
   deletes a component of mine is the highest-value reply available.

---

## 6. What this is not

It is not a results paper. Part II says so of itself: an architecture-and-protocol paper
whose measurements are *n* = 1 and are labelled as such throughout, with an evaluation
protocol stated but not yet run.

It is also not a claim of novelty. The nearest-work survey behind it started from a single
secondary source and has **not** been verified against the primary literature. Every
*"nobody does this"* in these documents is a hypothesis about the field, not a search
result — which is exactly why the first reader is someone who reads these venues.

**If you tell me this was done in 1994, that is the most useful thing that can happen to
this document.**

---

*Part I of three, `press_office/PreludeCognitiveArchitecture.md`. Part II:
[`NoveltyDrivenGraphTreeExpansion.md`](NoveltyDrivenGraphTreeExpansion.md). Part III:
[`FactSheet.md`](FactSheet.md), measured 2026-08-11. Assembly and target list:
[`OutreachPacket.md`](OutreachPacket.md).*
