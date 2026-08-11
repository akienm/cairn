# Pattern — Tree architecture

### Separate the thing remembered from the thing indexing it, and reorganisation stops being dangerous

> **The move.** Three layers, never collapsed. A **node** is what is remembered and has an
> *identity*; it belongs to no tree. An **embedding** is one rendering of it as coordinates, and
> is derived. A **leaf** is how it is found, and has an *address* — `database.tree.leaf` — which
> changes when a tree reorganises. Because reorganisation touches only leaves, **index
> maintenance can never damage a record of truth.**

*Full technical treatment with the cost arithmetic:*
[`GraphTreeMemoryTechnicalBrief.md`](GraphTreeMemoryTechnicalBrief.md) §4, and
[`NoveltyDrivenGraphTreeExpansion.md`](NoveltyDrivenGraphTreeExpansion.md) §6.

---

## 1. The measured failure

A system built the ordinary way — conventional tables, one stored edge table — reached **70,000
words and 2.5 million bigram edges,** at which point **every single edge update took more than 30
seconds,** and was still climbing.

The mechanism is unremarkable, which is the point. Ingesting one memory means many `UPDATE`s
against a 2.5M-row edge table: each an index seek or a scan, each taking a write lock, each
syncing. **The cost grows with the corpus.** The system got slower exactly as it learned more,
which is the one direction a memory must not move. A different engine buys perhaps an order of
magnitude and then meets the same wall, because the wall is not the engine.

**Name the wall precisely, because it is easy to name too broadly.** The wall is *a link
structure with no bound per item.* It is **not** "storing links at all." Reading it the broad way
is how you end up forbidding the one thing that would let the index learn, on the authority of a
number that never measured it.

There is a second failure, and it is one of vocabulary. For weeks the design used *node* and
*leaf* as if they were one thing. Every internal review passed. The collapse was caught by the
author on 2026-08-05, and it had been hiding three distinct results.

---

## 2. The pattern

### 2.1 The three layers

```
node = {                    # THE THING BEING REMEMBERED
  content:    text          — one claim, in natural language
  provenance: {source, …}   — where it came from, always
  standing:   hypothesis | earned | refuted
}                           # has an IDENTITY. Never belongs to a tree.

embedding = {               # A RENDERING OF IT, AS COORDINATES
  node:       → a node's identity — and the node points back
  vector:     float[d]      — one way of putting that claim in space
}                           # MANY PER NODE. Derived, therefore regenerable.

leaf = {                    # THE THING INDEXING IT
  embedding:  → one embedding
  weights, edges: → other leaf addresses, two-way
}                           # has an ADDRESS: database.tree.leaf
```

**An address is not an identity.** A leaf has both: an identity of its own, and an address that
can change. The node it points at has only an identity. Keep these apart and reorganisation is
cheap; collapse them and every reorganisation becomes a re-identification pass across the whole
corpus.

**Why the embedding is its own layer** rather than a column on the leaf: a leaf was doing two
unrelated jobs — holding the coordinates *and* holding the connections. Separating them means a
node can have **more than one rendering** (a diagram-shaped passage and a prose rendering of the
same claim both stay retrievable, instead of one having to win), and it gives an exhaustive
fallback search a table to run on that needs no trees at all.

And an embedding is **derived.** Regenerate it from the node and you get it back. Nothing about it
is a record of truth — which is what makes §2.4's guarantee hold.

### 2.2 One node list per database; each tree is a table of leaves

Within a database there is **one node list** — one table of remembered things, shared by every
tree above it, and *not* partitioned by tree. Nodes are the substrate; what varies is how they
are indexed.

Each tree is a **physical table of leaves**, not a row in a table of trees. What that buys:

- The walk is bounded by the **tree**, not the corpus.
- Calving is a table operation on leaves, not a mass rewrite of remembered things.
- **Two different tree sets can index one node set** — the same claims organised along different
  axes, with no duplication of the claims themselves.

Default access is **private-down, grant-up**: a tree indexes into what is below it privately, and
reaching upward into shared material is an explicit grant.

### 2.3 The address carries its table

`database.tree.leaf`. Consequences:

- Reaching a leaf is **addressing, not searching.** No index traversal, no lookup by content, no
  growth in access variance as the graph grows. That constant-time, constant-variance property is
  the whole point — it is what 30-seconds-per-edge-update was the symptom of losing.
- **A cross-tree link is just a leaf address with a different table part.** The standard objection
  to per-tree tables — *"you'll need an edge index to cross trees"* — assumes you must *search*
  for edges. Addressing eliminates the search, so the objection does not bind here.

### 2.4 Calving builds the path; the shear repairs the index

A tree that grows past its bound **calves**: it splits along its **dominant attractors** — the
regions the content has actually clustered into, rather than an arbitrary partition. A **shear**
then renumbers leaf addresses along the split.

Splitting on attractors rather than on size alone is what keeps each post-calve tree semantically
coherent, which is what keeps *routing* tractable. A split down the middle of a cluster pushes
the routing cost straight back up. **Calving does not merely cap the walk's cost — it creates the
path a query walks.**

**Why the links are two-way.** A moved leaf leaves stale pointers behind it, and the question is
how you find their holders. Because every articulated edge is mirrored, **a moved leaf's in-link
list *is* the exact set of holders** — the affected set is not merely small, it is *addressable.*
One-way, that set exists with no address, and you find it by reading every leaf's out-links: the
searching this whole design exists to eliminate, reappearing in the reverse direction.

With bound *B*, corpus *N*, articulated degree *g*, growth to *N* costs about *N/B* calves:

| | per calve | over growth to *N* |
|---|---|---|
| one-way links | full scan, *O(N)* | *O(N²g/B)* |
| two-way links | incident edges only, *O(Bg)* | *O(Ng)* |

Quadratic versus linear — and the quadratic version gets expensive precisely as the corpus grows
large enough to need calving.

**Both halves of a link need one door.** If the out-half and in-half can be written separately
they can drift, and a drifted back-reference means the shear misses a leaf — whose stale pointer
then does not dangle but **silently retargets** to whatever now occupies that address. So: one
operation writes both halves, or the link does not exist. Cheap insurance regardless: **never
reuse leaf numbers after a shear,** so anything missed dangles loudly instead of retargeting
quietly.

### 2.5 The property that matters most

**A calve never touches a node.** It is a pure leaf operation. The things being remembered are not
read and not written.

The embedding layer makes that argument *stronger* rather than complicating it. A calve may have
to touch an embedding's back-references — and that is the acceptable case, because an embedding
is derived: damage one and you regenerate it from the node. **A node cannot be regenerated from
anything.** So the deepest layer index maintenance can reach is exactly the layer that is cheap to
rebuild, and the layer it must never reach is the one it structurally cannot.

### 2.6 The trade, stated plainly

| | write cost | read cost |
|---|---|---|
| unbounded edges | **grows with the corpus** | cheap |
| bounded edges + bounded trees | **constant in corpus size** | bounded by the bound, not the corpus |

The operative word is **unbounded**, not *stored*. Adding a memory writes one node row, one
embedding row, one leaf row, and a neighbour list of *k* entries — *k* a constant we choose —
where the build that died wrote a list that grew with everything it had ever learned. Nothing
whose size depends on the corpus is touched.

---

## 3. How it is enforced

**Physics today:** one owner per table, enforced by a `CHECK` in the schema plus a single
connection-holding module. Ownership is the layer this design's guarantees ultimately rest on: a
shear cannot reach into a table it does not own.

**Everything else in this document is prose.** The node/leaf/embedding split, per-tree leaf
tables, bounded neighbour lists, calving and the shear are **specified and unbuilt.** The running
store is a single table in which the node, the vector and the leaf are the same row, with no link
columns at all — so there is currently nothing for a shear to renumber and nowhere for an
articulated edge to live.

This is stated here rather than in a footnote because Law 9 makes red the default. **The node/leaf
split is a prerequisite for calving, not a detail of it.**

---

## 4. What it costs

**Read cost rises.** The trade moves work from write time to read time. It is capped there — by
the calving bound rather than by how much has been learned — but it is not free, and a workload
that writes rarely and reads constantly may prefer the wall it never hits.

**More layers, more joins.** Three tables where one would do, plus a leaf table per tree. Every
retrieval crosses at least two of them.

**Cross-tree in-links are cross-owner writes.** If a leaf in tree B points into tree T, T's calve
must rewrite a row B's owner gates — and under one-owner-per-store the shear cannot reach in.
Two-way links make this tractable (T knows exactly whom to notify) but not free; the fixup still
travels through B's gate.

**Open parameters, each a dial that must be learned.**

1. **How fast a weight falls.** A weight that strengthens whenever its path resolves is a positive
   feedback loop — a wrong route that resolves once gets stronger, is likelier to be chosen next
   time, and manufactures its own confirmation with a ratchet on it. The correction is the same
   asymmetry the gates already demand: **counter-evidence lowers a weight faster than confirmation
   raises it** — and *how much* faster is unmeasured. Born red.
2. **The bound.** Provisionally 5,000 leaves. An earlier generation used 1,000, which is evidence
   the threshold moves with the content — a parameter to learn, not a constant to enshrine.
   Whether it is one bound or two (size *and* depth) is open.
3. **Whether a node carries back-references to its leaves.** *"Where is this node indexed?"* is
   otherwise a lookup against every tree table. Storing the list makes it one read — **but then a
   calve does write nodes,** and §2.5's guarantee holds only if it doesn't.

---

## 5. What would falsify this

**The benchmark that has not been run, stated as the authors would want to be held to it.**

This must be measured **at the scale it was designed for** — on the order of **2.5 million
nodes**, which is not a projected scale but the corpus size at which the previous build died.
Proving the shape on a few hundred rows fails this outright.

The test is **two-sided**, because the baseline is two-sided:

- **access must not degrade with graph size,** and
- **write cost must not grow with corpus size.**

Either one alone is satisfiable by a design that is worse than what it replaced.

Further falsifiers:

- **An out-link with no mirror in-link.** The shear's correctness rests entirely on the mirror.
- **A calve that writes a node row.** The one guarantee this whole architecture is for.
- **A leaf number reused after a shear.** Converts a loud dangle into a silent retarget.
- **Routing cost climbing after a calve.** Means the split was on size rather than on attractors.

Until that benchmark runs, this section is **a design with an unusually good provenance and no
benchmark, and we say so.**

---

## 6. What is built, and what is red

**Built.** One owner per table, checked by the schema, with a single connection-holding module —
15 owned tables. The node layer's own contracts: one claim per node; provenance as a *gate*, not
a field; every node born a hypothesis; and, since 2026-08-09/10, the tenure loop that moves
standing (3 of 88 nodes have earned it, 1 is refuted).

**Red — nearly all of it.**

- **No node/leaf/embedding split in the schema.** `librarian_nodes` still carries `tree` and
  `vector` on the node row.
- **No per-tree leaf tables.** No leaf addresses. No `database.tree.leaf`.
- **No stored articulated edges,** in either direction. Edges are derived from vectors at walk
  time.
- **No calving, no shear, no bound.**
- **No benchmark at any scale**, let alone the one that matters. The largest live measurement is
  88 nodes — four orders of magnitude below the falsifier.

The design exists, its provenance is a measured death at a named scale, and none of it is
running. That is the honest state.

---

*Pattern document, `press_office/PatternTreeArchitecture.md`. Part of the Cairn pattern series;
the spine is [`CairnArchitecture.md`](CairnArchitecture.md). Depth in
[`GraphTreeMemoryTechnicalBrief.md`](GraphTreeMemoryTechnicalBrief.md) §4. The caching loop this
storage serves is [`PatternGraphTreeCaching.md`](PatternGraphTreeCaching.md). All numbers from
[`FactSheet.md`](FactSheet.md), measured 2026-08-11.*
