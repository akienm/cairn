# Pattern — Graph trees as an inference cache

### On a miss, ask the model for *nodes* — never for the answer

> **The move.** A query resolves by walking stored structure: cheap, no inference. Only a **miss**
> reaches the expensive resolver, and what the resolver returns is not an answer — it is
> **nodes**. They deposit through the same provenance gate as everything else, and the *original
> question is resubmitted*. The answer always comes from structure, so asking again is a walk.

*Full technical treatment, including the cost model and the storage design:*
[`GraphTreeMemoryTechnicalBrief.md`](GraphTreeMemoryTechnicalBrief.md). *This document is the
pattern, stated so it can be lifted.*

---

## 1. The measured failure

**The one that produced the pattern.** An expensive resolver — a frontier model, a human — is
asked the same question repeatedly because nobody put the answer anywhere it could be reached.
Cairn's first law names this precisely: *re-deriving a settled answer is a defect,* not an
inefficiency. Same standing as a wrong answer.

**The one that shaped the pattern's honesty rules, and it is the more interesting failure.**
Measured 2026-07-27, on the system's own first successful crossing of this loop.

A question missed. The model was asked for nodes. It supplied one. The node deposited. The
original question re-resolved and came back **RESOLVED at cosine 0.8568** — a clean success by
every check in place at the time.

It was not a success. **A node minted from a question is question-shaped, and therefore wins the
similarity race for that question by construction.** The graph had not resolved anything; it had
been handed its own question back in node form and recognised it. A self-backfilling graph
**manufactures resolution.**

The same shape was independently measured in a second place: a chart nexus scored by its own
tree's confidence read **0.8295** — home-field manufactured resolution, now a standing red in
that component's falsifier list.

The system's own first success was reclassified as PROVISIONAL, and the mechanism it exposed is
the subject of the academic paper in this folder.

---

## 2. The pattern

### 2.1 The loop

```
question
  → walk the graph                       (cheap; no inference)
  → best cosine ≥ RESOLUTION_FLOOR?      → RESOLVED, answer from structure
  → miss
      → ask the resolver for NODES       (never for the answer)
      → deposit through the provenance gate
      → resubmit the ORIGINAL question
      → repeat, bounded
```

Two rules make it more than a cache:

- **The resolver supplies nodes, never answers.** If the model's prose could be the reply, the
  device is a chat wrapper with a vector index. Because it can only add structure, every miss
  makes the *next* walk more likely to succeed without it.
- **The answer always comes from a walk.** A returned answer that came from the resolver is a red
  in this component's falsifier list: *the host in the answer path.*

### 2.2 Crossing honesty — the fix for manufactured resolution

A node minted during a crossing is labelled `evidence: False` and **cannot resolve the question
that spawned it.** The first touch returns **UNRESOLVED**, with the honest reason `learned`: the
graph grew, and the question is honestly still open.

Validation completes at a **later, independent crossing** — when standing structure resolves what
a fresh mint may not.

That is the whole correction, and it costs a success. The 2026-07-27 result that read RESOLVED
now reads UNRESOLVED-but-learned, which is what it always was.

### 2.3 Termination that cannot livelock

Backfilling into a cache creates an obvious trap: the same question, asked again, canonicalises
to the same cache key, returns the same nodes, forever.

Fixed as physics at the junction: **the backfill prompt carries the graph's own state digest.**
Same question plus a changed graph is a different cache key. And a round that lands nothing fresh
**terminates loudly**, with a distinguishable reason:

| Reason | Meaning |
|---|---|
| `learned` | the crossing deposited; the graph grew, honestly unresolved |
| `no_progress` | the round deposited nothing |
| `exhausted` | a zero-deposit budget-out |

Three reasons, because collapsing them would hide the difference between *working* and *stuck*.

### 2.4 Standing is earned across crossings, not asserted at birth

**Every node is born a hypothesis.** Five behaviours move it, each riding an event the loop
already fires — **no clock and no daemon anywhere:**

- **Crossing honesty** — a same-crossing mint is data, not evidence.
- **Provenance append** — a duplicate deposit lands its incoming provenance as a timestamped
  attestation on the standing row. Corroboration is kept; table growth is still refused.
- **Promotion** — cross-question corroboration fires *on* the resolution event. A threshold number
  of **distinct questions beyond the birth question** earns `standing = earned`.
- **Lazy decay** — uncorroborated, attestation-less hypotheses past a horizon fade from evidence
  **at read**. A same-question echo never exempts, or the home-field shard would immortalise
  itself.
- **Refutation** — a stated correction retires a node: `standing = refuted`, with the refuter and
  evidence appended, in exactly **one** owner-gated write. The retirement **invalidates and never
  deletes** — content, vector and birth provenance stay byte-identical — and every later walk
  returns the retired node **present, labelled, and uncounted.**

Two details in refutation are load-bearing:

**Refutation is an input, never a discovery.** Cosine finds nodes that are *alike*, and a
statement and its negation are alike. Nothing here detects contradiction; the door is entered by
a hand, through a literal prefix (`correct: <node_id> <why>`) — one string comparison, zero model
calls on the routing path. Any code path that retires a node without a hand naming it is a red:
*cosine mistaken for a contradiction detector.*

**The standing gate keys on provenance authority, not on standing.** Every node is born a
hypothesis, so a gate keyed on standing would leave the author's own correction unable to retire
an *earned* node. This is the gate protecting the corpus **from its author's own past work** — a
node in the tree is a past artifact, and no past artifact outranks him now.

### 2.5 The deposit door refuses the untraceable

A node is content + vector + provenance + standing. **The untraceable never lands.**

The reason is the extractor's founding defect carried one layer down: *a fabricated attribution in
a draft is a bad day; in a graph node it is a permanent resident.*

### 2.6 The inference proxy is the same pattern at the cheapest radius

One door to every inference host, canonicalising each request and serving a stored answer whose
horizon still holds. Measured over 1,400 real calls: **560 hits (40.0%)**, and **34.3% of the
tokens that would otherwise have been spent were avoided.** Same shape, no graph required — see
[`PatternInferenceProxy.md`](PatternInferenceProxy.md).

---

## 3. How it is enforced

**Physics today:** the deposit door's provenance gate; the crossing-honesty filter on the
evidence flag; the promotion threshold counted over *distinct questions beyond the birth
question*; the decay's same-question exemption refusal; refutation as exactly one owner-gated
update with byte-identity checks on content, vector and birth provenance; the refuted clause
evaluated **before** the earned pass-through, so a node earned and then refuted is still
uncounted; the refuter allowlist read as an allowlist rather than a denylist; the livelock tooth
pinning canonicalisation *inequality* across a changed graph; an import allowlist on the loop and
tree modules so no second door to the host exists.

**Still prose (tracked as debt):** whether standing actually *moves* under live use is not
enforceable — it is watched, by an armed probe (`probes/standing_moves_under_live_use.py`), whose
question is exactly the wrong-shape signal *every node still 'hypothesis' weeks into live use.* A
second armed probe watches whether revisions hold: exercised at all, adjudicated ever, and not
storming.

---

## 4. What it costs

**Every deposit is an embedding call.** The intake path is not free, and bulk intake (folding a
shelved document in passage by passage) is the expensive part of owning this memory.

**Success rates look bad on purpose.** 3 of 88 nodes have earned standing. Under the pre-honesty
rules the number would have been far higher and far less true. If you adopt this pattern, budget
for a metric that gets *worse* the day you make it honest.

**Three-valued verdicts complicate every consumer.** RESOLVED / PROVISIONAL / UNRESOLVED is more
work for a caller than a boolean, and UNRESOLVED must never be booked anywhere as a saving.

**The canonicaliser is the ceiling.** Cairn's is exact-match, not semantic. It *learns whether the
cache pays; it does not yet learn which questions are the same.* 40% is what a dumb canonicaliser
reaches.

---

## 5. What would falsify this

- **The answer comes from the resolver.** A returned answer the walk did not produce means the
  device has been demoted to a vector cache with a conversation on top.
- **Everything stays a hypothesis.** Weeks of live use with no promotions means the tenure loop is
  built and decorative.
- **A refuted node counts as evidence** on any later walk, or a retirement deletes rather than
  invalidates.
- **Contradiction gets detected rather than stated.** Any code path retiring a node without a hand
  naming it.
- **A duplicate deposit grows the table.** Law 1 at the door: an answered question becomes
  structure once.
- **The hit rate collapses on a less self-similar workload.** The measured 40% comes from a system
  building itself. That is a genuinely repetitive corpus, and the number should not be
  transplanted without re-measuring.

---

## 6. What is built, and what is red

**Built.** The deposit gate, the proximity walk, the core miss-to-nodes loop (measured live
2026-07-27), the library/shelf intake with frozen citable addresses, the summarise transducer,
the chat face, and all five tenure behaviours including refutation (2026-08-10). 88 nodes: 80
hypothesis, **3 earned**, 1 refuted, plus 4 founding hypotheses. 587 nodes across the seven
chart-stage trees, which are the same mechanism serving the pre-build preamble.

**Red.**

- **The canonicaliser is exact-match.** Semantic canonicalisation and active falsifier
  invalidation are the two named edges where this deepens, and neither exists.
- **Both watches are armed and unfired.** Whether standing moves and whether revisions hold under
  live use are open questions with probes waiting, not answers.
- **Refutation has never been exercised in anger.** Built 2026-08-10; its own wrong-shape signal
  is *built and never once used.*
- The storage design that makes this survive scale is designed and unmigrated — see
  [`PatternTreeArchitecture.md`](PatternTreeArchitecture.md).

---

*Pattern document, `press_office/PatternGraphTreeCaching.md`. Part of the Cairn pattern series;
the spine is [`CairnArchitecture.md`](CairnArchitecture.md). Depth in
[`GraphTreeMemoryTechnicalBrief.md`](GraphTreeMemoryTechnicalBrief.md); the manufactured-resolution
result is written up in [`NoveltyDrivenGraphTreeExpansion.md`](NoveltyDrivenGraphTreeExpansion.md).
All numbers from [`FactSheet.md`](FactSheet.md), measured 2026-08-11.*
