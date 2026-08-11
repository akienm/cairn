# Pattern — The escalating, capturing inference proxy

### One door to every model, so metering is free and complete — and *the cheapest answer is never the one you already have*

> **The move.** Every inference request in the system passes through one owned door. The door
> canonicalises the request, serves a stored answer whose horizon still holds, and only on a miss
> dials a host — choosing which host by walking an authored **rules stack**, cheapest route
> first. Because there is no second path, the meter is complete by construction: the saving is a
> measured fact rather than an estimate.

---

## 1. The measured failure

**The mandate with no teeth.** In this system's predecessor, an inference proxy was mandated for
a month. At the end of that month **six live files still opened raw HTTP to the host.** Nobody
defied the rule. A rule that lives in a document is obeyed by whoever remembers it that week,
and metering built on top of such a rule reports on the fraction of traffic that happened to
comply.

**The number that was measured and then thrown away.** The host reports its own token counters on
every call. The proxy had been recording them in the cache row **since the day it was built** —
and never returning them. So a caller could not ask what a call actually cost, and the ceiling on
embedding throughput lived in an operator's head as a rough figure people quoted at each other.
A measured number, taken at a seam, discarded one layer above it, and then re-derived by
guessing. Corrected 2026-07-29 by returning cost and provenance **additively** beside the answer.

**The lived symptom that produced the routing half, 2026-08-08.** A chat turn timed out at 120
seconds. The cause was not the model, the prompt, or the corpus: the resolver dialed **this
box's CPU-only loopback endpoint** while a dedicated GPU machine on the same LAN sat idle.

The available fixes were: buy hardware, tune the local model, or raise the timeout. The ruling
went the other way — **the defect is the routing, not the hardware** — and produced the line that
now governs the stack:

> **The lowest-cost answer is never `127.0.0.1`.**

A local model is not free. It is *slow*, and slow on the critical path of an interactive face is
the most expensive thing in the system.

---

## 2. The pattern

### 2.1 An inference request is a ticket, and the door runs its workflow

Not a bag of features — a **workflow with states**, run inside the owner:

```
RECEIVE → CANONICALIZE → lookup
                          ├── hit  → VERIFY → ANSWER
                          └── miss → METER → RESOLVE → RECORD → ANSWER
```

`VERIFY` before `ANSWER` is the clause that makes this a compiler rather than a cache: **a stored
answer carries its own horizon, and a hit past that horizon re-resolves.** Blind replay is a
listed falsifier.

Three primitives, and no more: `canonicalize(request)`, `resolve(request)` returning
`{answer, hit, canonical, cost, provenance}`, and `yield_report()` — the meter read back.

### 2.2 The sole path is what makes the meter honest

This is the argument for the whole design, and it is worth stating carefully.

**Because there is exactly one path to the host, there is no uninstrumented traffic.** Not "we
try to route everything through the proxy" — *there is no other door.* So `yield_report()`'s
count of tokens spent against tokens avoided is a complete measurement rather than a sample of
the compliant fraction.

Sole-path is enforced by an import mesh over **every `.py` file in the tree**, run both at proof
time and at build time. The residue is named rather than hidden: **a `subprocess` that shells out
to `curl` imports nothing and is invisible to an import graph.** That sentence lives in the
component's own falsifier list, so the gap is a tracked debt rather than a discovered surprise.

### 2.3 The store is the cache and the meter, and it is append-only

One owned table. **Every call lands a row.** Miss rows carry the resolved answer with its
falsifier, horizon, provenance and cost; hit rows carry the avoided spend and a served-from
marker.

**Append-only on purpose.** A stale answer is **out-voted by verification, not overwritten** —
which is Law 7 doing real work rather than decorating a schema: the record of what the host said
at that moment survives the answer being superseded. It also means insert-only store primitives
are sufficient, so the cache needs no update path at all.

### 2.4 Routing is an authored rules stack, walked cheapest-first

Three authored files beside the code, plus a nest of sieves that lets out the lowest-cost route:

| File | Holds |
|---|---|
| `providers.json` | costs, connection handling, enabled **and why** |
| `models.json` | names, parameters, pros and cons, scores |
| `combos.json` | the routable provider/model pairings |

The machine half — this LAN's actual endpoints and the API keys — lives in **instance-space**,
never in the repository.

The walk: shake the nest, dial survivors cheapest-first, **step to the next rung on
unreachability only**, and refuse loudly when the walk exhausts. Two clauses keep it honest:

- **A rung with no key refuses loudly** rather than being silently skipped. A provider listed and
  unreachable is visible.
- **A provider whose transport does not exist is walked past loudly, never dialed in some other
  provider's shape.** The wrong-protocol call is the failure mode that produces a confusing error
  three layers away.

**Loopback is cut categorically — even as the last rung standing.** Not down-ranked. Cut. The
proof pins that, because "prefer remote" degrades back to "dial local" exactly when the system is
under load, which is exactly when it hurts.

Authored costs are labelled as a **hypothesis** until the meter measures them. The stack is a set
of claims about what things cost, and it says so.

### 2.5 The routed default heals call sites without touching them

When the stack landed, **four bare call sites were healed with zero caller edits.** That is the
payoff of the single door: routing policy is a property of the door, so improving it improves
every caller at once, and a caller cannot opt out by being written before the improvement
existed.

---

## 3. How it is enforced

**Physics today:**

- Sole-path import mesh over the whole tree, at proof time *and* at build time — the latter added
  2026-08-08 on an explicit ruling.
- Owner-gated cache table; a non-owner write fails at the store.
- Compile-once pinned by proof: a canonically identical repeat must not call the resolver again.
- Verify-before-answer pinned by proof: an entry past its horizon re-resolves.
- The answer served byte-for-byte unchanged from the stored row.
- The meter's spent-versus-avoided arithmetic checked against a real store.
- Loopback cut categorically, unkeyed rungs refusing, and failover on unreachability *only* —
  all pinned by the routing proof.
- An armed probe watching whether a routed provider has ever actually answered live.

**Still prose (tracked as debt):**

- **`subprocess` and dynamic imports** are invisible to the mesh.
- **Semantic canonicalisation does not exist.** See §4.
- **The stored falsifier is carried but not evaluated.** Verification checks the horizon only;
  actively invalidating an answer whose falsifier has fired, and propagating that upstream, is a
  named later edge.

---

## 4. What it costs

**The canonicaliser is the ceiling, and it is dumb on purpose.** Canonicalisation is *structural*
— sorted-key JSON. It does not collapse semantic equivalence, so two paraphrases of the same
question are two questions and two host calls. The measured **40.0% hit rate is what a structural
canonicaliser reaches**; the remaining 60% is not all novel work, it is partly the same question
wearing different words.

Semantic canonicalisation is the obvious improvement and is deliberately unbuilt: **collapsing
two questions that are not actually the same is worse than missing the cache**, and no shape for
it has been committed without an adversarial pass.

**A cached refusal is sticky.** A malformed draft that the parser correctly refuses is still a
stored answer for that request, so the same question against the same inputs re-serves the
refusal. This is honest under the cache's own physics. The fix is a retry that rides a
**changed** request — the refusal folded into the prompt is a different key — and never a cache
bypass, because a bypass is a second door.

**The hit rate is workload-shaped.** The 40% comes from a system building itself, which is a
genuinely repetitive corpus. **That number should not be transplanted without re-measuring.**

**Instance-space credentials mean a rung can be listed and dead.** Rows exist in the stack for
providers whose keys have not landed. They refuse loudly, which is correct and also means the
stack's contents overstate what is reachable today.

---

## 5. What would falsify this

- **A canonically identical repeat touches the host.** Compile-once breached — the whole thesis.
- **A request past its horizon is served from the cache.** Blind replay.
- **A hit returns anything but the stored answer, byte for byte.** A record of truth mangled on
  the way out.
- **Any module but the domain opens the host.** Sole-path breached, and the meter becomes a
  sample.
- **A call lands no meter row,** or the report miscounts spent against avoided.
- **A miss lands with provenance pointing at loopback while a ruled provider is available.** The
  routing never crossed live — an armed probe watches exactly this.
- **The stacks exist but a route is decided by a literal anyway.** Rules decorative.
- **The wrong-shape signal:** if metering and caching turn out to need to live *inside* the
  resolver loop rather than at this boundary, **the domain was the wrong seam** — and that would
  invalidate the pattern, not merely the implementation.

---

## 6. What is built, and what is red

**Built and measured over real traffic:**

| | |
|---|---|
| calls through the door | **1,400** |
| served from the store | **560** — a **40.0%** hit rate |
| tokens spent on misses | **274,348** |
| tokens avoided by hits | **142,948** — **34.3%** of what would have been spent |

Also built: the three-file rules stack with the sieve nest; the categorical loopback cut;
cheapest-first failover; cost and provenance returned additively; the append-only store serving
as both cache and meter; sole-path enforcement at proof time and build time.

**Red.**

- **Semantic canonicalisation does not exist.** The device learns *whether* the cache pays; it
  does not yet learn *which questions are the same.*
- **Active falsifier invalidation does not exist.** It learns whether it pays; it does not learn
  *when an answer has gone wrong.*
- **Two provider rungs are listed and keyless**, refusing loudly until credentials land.
- **One provider's transport is unwritten.** Its rows are walked past.
- **Authored costs are unmeasured.** They are a labelled hypothesis, and the meter that would
  settle them is running but has not been read against them.
- **The runtime face is deferred.** Callers import the domain rather than poking it over the bus.

---

*Pattern document, `press_office/PatternInferenceProxy.md`. Part of the Cairn pattern series; the
spine is [`CairnArchitecture.md`](CairnArchitecture.md). The same compile-once idea applied to a
knowledge graph is [`PatternGraphTreeCaching.md`](PatternGraphTreeCaching.md). All numbers from
[`FactSheet.md`](FactSheet.md), measured 2026-08-11.*
