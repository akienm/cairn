# Pattern — The librarian

### A memory you can talk to, where the conversation *articulates* the memory and never answers for it

> **The move.** One device owns the corpus. It reads documents onto a shelf at **frozen citable
> addresses**, folds them into a graph as nodes, answers by **walking** that graph, and renders
> what the walk found into prose. The model is spent on *articulation* — turning a walk into
> sentences — never on supplying the facts. Every citation is built by code from the walked
> region, so a citation the walk cannot anchor is a refusal, not a sentence.

---

## 1. The measured failure

**The one that named the pattern.** Ask a corpus a question and you get back either a search
engine's list of hits, which you must read, or a chat interface's fluent paragraph, which you
must trust. The first does not answer. The second answers from the model, and you cannot tell
which sentence came from your documents.

**The one that shaped this device, measured on 2026-08-09 and worth stating plainly because it
is a failure of *ours*.** The chat face had been built, proved, and declared whole. Its author
sat down and typed `hello`.

What came back was a **wall of resolution diagnostics** — cosine scores, node counts, verdict
fields.

Everything was working. Every proof was green. The device had kept the words *chat bot* while
**replacing what they meant**: "chat" had quietly come to mean *the loop's verdict, printed.*
Nothing scanned as missing, because the word was still there. The correction was one sentence
from the author — *"the intentions say it should be chatting and it's not"* — and it cost a
rebuild of the reply path.

That failure has a name in this project: **words kept, meanings replaced.** It is invisible to
every check that looks for absence, because nothing is absent.

**A third failure gave the device its intake rules.** A document extractor once produced a
fabricated attribution in a draft. In a draft that is a bad day. **In a graph node it is a
permanent resident** — every later walk touches it, and it looks exactly like the real ones.

---

## 2. The pattern

### 2.1 The shelf: frozen copies at addresses that cannot rot

Before a document can be remembered it is **shelved** — copied into a room the device owns, with
its digest registered. The rules are small and absolute:

- **Re-shelving identical content writes nothing.**
- **Different content at a standing address is refused.** An address must never change meaning,
  because provenance anchors point *into* it.
- Citations use **raw paragraph position**, so filtering never renumbers what a citation points
  at.

**The graph is the catalog, not the shelf.** Learning a shelved file deposits one node per
passage, each anchored `{source: library:<address>, passage: p<n>, sha256}`. The claim lives in
the graph; the bytes stay on the shelf; the anchor survives both.

Founding intake, measured: **134 files, 41 MB, three rooms, zero failures** — and the re-shelve
wrote nothing at all.

### 2.2 The answer comes from a walk

A question embeds, the device walks the tree by proximity, and if the walk clears its resolution
floor, **that is the answer** — no inference in the answer path at all. A miss goes to the
inference loop described in [`PatternGraphTreeCaching.md`](PatternGraphTreeCaching.md), which
asks the model for *nodes* and then re-asks the original question.

Two properties fall out of the storage design, and they are the ones people find surprising:

- **There is no edge table.** Edges are *derived from the vectors at walk time.* The design's
  own phrasing: **the embedding IS the path through the graph trees.** An edge table appearing
  is a listed falsifier.
- **Decay is a property of the read, not of the tree.** A year-old node still ranks by raw
  cosine when the tree is asked; it is the librarian's *reading* that fades an uncorroborated
  hypothesis. The store never lies about what it holds.

### 2.3 Summarising is a transducer, and its output goes back in

`summarize` renders a **dense region** of the graph — the nearest *k* source nodes around the
question — into articulated, why-carrying prose. The physics around it is where the pattern is:

- **A summary is a view over the graph, never a document the graph forgets.** The rendered prose
  **deposits back** as a node, its provenance naming the exact nodes it rendered and the
  region's digest. What the librarian articulates, it also remembers, and a follow-up *walks* to
  it instead of re-rendering.
- **The transducer never eats its own output.** Gathering excludes summary-sourced nodes. Without
  that clause you get a photocopy of a photocopy, and the drift is invisible because each
  generation reads fluently.
- **Citations are code-built.** The model may only emit `[n]` marks against a numbered region
  that rides the prompt whole. The code maps the marks back. **An unanchored or minted citation
  refuses loudly, with the raw draft carried whole** — never silently dropped.
- Idempotence comes free: same question plus same source region is the same render prompt, which
  is a cache hit and a duplicate deposit. Measured on the first re-fire: **3 calls, all cache
  hits, zero writes.**

**Depth travels with the artifact** — region reached versus tree size — so a reader can see how
much of the corpus a summary actually looked at.

### 2.4 The chat face adds no third mechanism

This is the correction from §1, and it is the load-bearing distinction in the whole device:

> **The loop *answers*. The chat face *articulates the answer*. Facts come only from structure.**

One `generate` call per resolving turn, spent solely on turning the walk into conversational
prose. The walk rides the render prompt whole and numbered; citations are code-built from the
marks exactly as in the transducer; the loop's **entire verdict dict rides the reply as data**
even though the surface collapses it to one line — Law 7, a presentation surface may simplify,
a record of truth may not.

And the honest asymmetry: **zero anchors are legal here.** A greeting grounds on nothing. That
single clause is the whole difference between the chat verb and the summarize verb, and it is
the clause whose absence produced the diagnostics wall.

**Routing is physics, not inference.** `summarize:` is a stated prefix — one case-insensitive
string comparison, **zero model calls on the routing path.** Spending inference to guess what
the user meant is a listed falsifier. If people cannot find the affordance, *the fix is the
surface wording first and intent inference last.*

**Reply prose is runtime state and never deposits.** The transcript dies with the session; the
graph is the memory that survives it.

### 2.5 The carrier: a declared pane, not a route

There is **one web server in the whole system.** The librarian does not get a route, a port, or
a server. It **declares a chat pane**, its shim rides the roster and *starts the device if it is
not running*, and a posted utterance travels `web_server → shim.deliver → device.receive` as
ordinary mail.

This was a correction, taken on the author's word in 2026-07-28: the first build wired a bespoke
`/chat` route with injected source — a parallel door. **A device gets a declared pane; it never
gets its own server.**

### 2.6 Correction enters by hand, and the gate keys on authority

The fifth tenure behaviour, built 2026-08-10. A stated correction retires a node: standing flips
to `refuted`, the refuter and evidence append, in **exactly one owner-gated write**. Content,
vector and birth provenance stay byte-identical — **invalidate, never delete** — and every later
walk returns the node **present, labelled, and uncounted.**

Two clauses carry the weight:

**Refutation is an input, never a discovery.** Cosine finds nodes that are *alike*, and a
statement and its negation are alike. Nothing here detects contradiction; the door is entered by
a hand through a literal `correct: <node_id> <why>` prefix.

**The gate keys on provenance *authority*, not on standing.** Every node is born a hypothesis, so
a gate keyed on standing would leave the author's own correction unable to retire an *earned*
node. This is the gate that protects the corpus **from its author's own past work** — a node in
the tree is a past artifact, and no past artifact outranks him now.

---

## 3. How it is enforced

**Physics today.** The provenance gate at the deposit door. Dimension mismatch refused in both
directions. Owner-gating through the store, so no non-librarian write lands. Frozen shelf
addresses with digest checks — a rotted copy refuses rather than quietly grounding a citation.
Code-built citations at both rendering verbs, with a minted citation refusing loudly and the raw
carried whole. Prefix routing with no model call. **Import purity by AST allowlist on every
module** — the tree, loop, library, summarize and chat modules cannot reach the host or the
database directly; live composition is confined to one file. **68 proof teeth across five
scripts**, all run under a measured network-namespace seal.

**Still prose.** Whether the conversation is actually *good* is not provable by a tooth — the
live measure is the author's next real conversation. That is exactly how the diagnostics wall
survived a green build, and the honest statement is that a proof pins the contract and a human
finds the wrong shape.

---

## 4. What it costs

**Every deposit is an embedding call.** Bulk intake — folding a shelved document in passage by
passage — is the expensive part of owning this memory.

**Proximity is computed in Python, O(*n*) per walk,** and every deposit re-reads the tree for its
dimension check. Correct at the current size and openly filed: computing proximity where the
vectors live is a change a real load will pull, not one to make in advance.

**Diagram-shaped text ranks poorly.** Measured: a flow diagram with arrows and numbered steps
scored **0.4943** against a prose question it directly answers — *below two less relevant prose
passages*. Anything whose meaning is carried by layout embeds badly. The fix is a prose rendering
before embedding, which is more transduction, not a lower floor.

**A binary shelves but refuses to learn.** Non-UTF-8 files need a reader in front of the verb.
Loud refusal today, not a silent skip.

**A cached bad draft is sticky.** The drafting model once emitted invalid JSON; the parser
refused loudly, as designed — but the same question against the same graph now *hits that cached
refusal*, so it cannot backfill until the graph changes. Honest under the cache's own physics.
The fix, if it bites, is a retry that rides a **changed** request — never a cache bypass.

**Three dials are still hand-set:** the resolution floor (0.65), the promotion threshold (2), and
the decay horizon (14 days). Each is an *n*=1 guess, returned in every verdict so no caller
mistakes it for settled. **A hand-set constant in a gate is a learned value stranded in a human's
head**, and these three are named as such rather than defended.

---

## 5. What would falsify this

- **An answer comes from the model instead of the walk.** The device demoted to a vector cache
  with a conversation on top.
- **A reply asserts corpus content its walk never held**, or lands a citation the walk cannot
  anchor.
- **A resolving turn returns a diagnostics dump instead of conversation.** The original failure,
  named as a standing wrong-shape signal rather than filed as fixed.
- **Inference is spent on routing** — a guessed intent where a stated prefix is the physics.
- **An edge table appears.** The derived-edges claim gone hollow.
- **A summary does not land back in the graph,** or the transducer renders its own prior output.
- **A refuted node counts as evidence** on a later walk, or a retirement deletes rather than
  invalidates, or lands in more than one write.
- **Contradiction gets detected rather than stated** — any path retiring a node without a hand
  naming it.
- **Everything is still a hypothesis weeks into live use.** The tenure loop built and decorative.
  An armed probe watches exactly this.
- **A refused turn kills the session,** or is swallowed silently. A refusal is a reply.

---

## 6. What is built, and what is red

**Built, and live-fired.** All five stones: the tree spine, the core loop, the library and learn
verb, the summarize transducer, the chat face — plus the carried page at the one web server, and
all five tenure behaviours through refutation. 88 nodes: 80 hypothesis, **3 earned**, 1 refuted.
68 proof teeth under a measured netns seal; the database reachable through its Unix socket while
the network is gone.

Each verb has been fired for real, and each first live fire found something a green proof had
not: the summariser's follow-up crossing exposed manufactured resolution; the chat face's first
live fire exposed a citation parser that refused comma-grouped marks; the author's first real
conversation exposed the diagnostics wall. **First live fires keep catching their builders** —
that pattern is now expected, not surprising.

**Red.**

- **The conversation has an *n* of very few.** The face was reconciled 2026-08-09; whether it
  converses well is measured by use, not by teeth.
- **One utterance is treated as one question.** Decomposing a conversation into questions is
  filed, not built.
- **The transcript is in-process only.** A persistent conversation berths in instance-space when
  a real need pulls it.
- **The desk does not exist.** A workspace holding an assignment's topic, what has been folded so
  far, open threads and a resume event — the thing a multi-day research face needs — is filed and
  unbuilt.
- **Cross-tree resolution is an open question.** In the measured manufactured-resolution incident,
  a *different* tree held the answer and was never consulted.
- **The storage that survives scale is unmigrated** — see
  [`PatternTreeArchitecture.md`](PatternTreeArchitecture.md).

---

*Pattern document, `press_office/PatternTheLibrarian.md`. Part of the Cairn pattern series; the
spine is [`CairnArchitecture.md`](CairnArchitecture.md). The caching mechanism it runs is
[`PatternGraphTreeCaching.md`](PatternGraphTreeCaching.md); the storage design beneath it is
[`PatternTreeArchitecture.md`](PatternTreeArchitecture.md). All numbers from
[`FactSheet.md`](FactSheet.md), measured 2026-08-11.*
