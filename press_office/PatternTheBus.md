# Pattern — The bus

### Communication has exactly one door, so observability is never a separate build

> **The move.** Devices never hold references to each other and never call each other. They
> **post**, and they **read**. Every envelope carries its *why* and its causality, so the
> substrate is a replayable causal record rather than raw traffic. Every later surface — a web
> feed, an inspector, a debug pane — is a **read-projection of that one substrate**, so
> "inspectable and logged" is not a feature anyone remembers to add.

---

## 1. The measured failure

**The split brain.** In this system's predecessor, some traffic went over a message bus and some
went through a web server, and the two never reconciled. Nothing was broken enough to fix, and
the consequence was that **no single place could answer what the system had actually said.** Every
new debugging surface was a fresh build against whichever half it happened to reach, and each one
re-derived what the other already had.

**The silence that reads as health.** A device that stops talking looks exactly like a device
with nothing to say. If communication is direct calls between objects, a component that quietly
stopped participating leaves no trace anywhere — the absence of a message is not an event. Nobody
notices for weeks, and then notices by accident.

**A true record that was silently partial.** A record was posted, and it was true. It was also
incomplete, and nothing about the way it was written made the incompleteness visible. That single
incident is now a permanent inspector sieve, because the general shape — *a record of truth that
quietly collapsed* — is the failure this substrate's channel rules exist to prevent.

---

## 2. The pattern

### 2.1 Two substrates, symmetric

| Substrate | Owns | Sole door |
|---|---|---|
| the store | durable **state** | the owner's gate |
| **the bus** | inter-device **communication** | `post` |

That symmetry is deliberate and it is the design's core claim: **the two things a distributed
system can lose track of are what it knows and what it said**, and each gets one owned, logged
door rather than a convention.

The bus **rides the store for durable transit** and opens no connection of its own. Its traffic
table is owner-gated like any other, so a non-bus writer cannot forge traffic. One door, one
owner, all the way down.

### 2.2 Four channels, split by whether they are records of truth

Every device has four:

| Channel | Kind | May collapse? |
|---|---|---|
| `announce` | **record of truth** | never |
| `personal` | **record of truth** | never |
| `info` | diagnostic | yes, as a view |
| `debug` | diagnostic | yes, as a view |

This split is **Law 7 as physics**: *errors are loud at diagnostic surfaces and permanent in
records of truth.* A presentation surface may collapse something into a coherent shape; a record
of truth never may.

So `digest()` collapses a diagnostic channel to a count plus a tail — and **refuses outright to
collapse a record channel.** The refusal is the point. Without it, "collapse the noise" becomes a
knob someone eventually turns on the channel that mattered, and the substrate stops storing full
truth while every reader still believes it does.

Note the second half of the guarantee, which is easy to miss: **a digest must not alter what
`read` returns.** The view is a view. The substrate always holds everything.

### 2.3 Every envelope carries its why and its causality

An envelope is refused without a `why`. It carries `sender` and `reply_to`.

That turns the traffic log into something you can actually reason over. Not *"these messages
happened in this order"* — which is data — but **"this happened because of that, for this
stated reason"**, which is a causal chain you can replay. A log without causality tells you what
occurred; a log with it tells you why.

Requiring the *why* on every message is the same forcing move used everywhere else in this
system: **put the reason in the structure so it cannot be left blank.**

### 2.4 Inspecting a device is reading its feed

There is no separate inspection API, no status endpoint, no health object. **You read the
device's feed.** A woken device rebuilds its own context the same way — by reading its own
history.

The consequences are the reason the pattern earns its keep:

- **A device that stops posting is a signal**, visible in the record instead of in silence.
- **A channel that floods is a signal**, visible in the same place.
- **Observability is never a separate build.** Every surface — a web feed, an inspector pane, a
  protocol adapter — is a projection of the one substrate. Nothing re-derives the traffic
  elsewhere, so no two surfaces can disagree about what was said.

### 2.5 The wire protocol is an adapter, not the substrate

Whatever protocol the outside world wants at the edge is an adapter *at the edge*. **The
substrate must not be held hostage to a protocol** — that is filed explicitly, because the usual
way a message bus dies is by becoming an implementation detail of whichever wire format arrived
first.

---

## 3. How it is enforced

**Physics today:**

- `post` is the only send path; devices hold no references to each other.
- An unknown channel is refused. A message with no `why` is refused.
- A record channel **refuses to collapse**; a diagnostic digest cannot alter what `read` returns.
- Durable transit is an owner-gated write through the store — the bus opens no connection of its
  own, which the import mesh enforces tree-wide.
- The device class carries the core values structurally and reports intention → state → settings
  in that order.

**Still prose (tracked as debt):**

- **Per-device-owned channels.** Today the bus owns the transit table on behalf of attributed
  senders; making each device the owner of its own inbound channel waits on a real multi-owner
  need.
- **Retention.** A rolling-window expiry for diagnostic channels waits on real volume — and it is
  the one place where "collapse the noise" will legitimately need a shape, which is exactly why
  it is not being designed in advance.

---

## 4. What it costs

**Indirection everywhere.** A device cannot simply call the thing it needs. Every interaction is
a post, a channel, and a read. For a two-component system this is pure overhead, and the payoff
only arrives at the point where you want to ask what happened and there is one place to look.

**A durable write per message.** Transit rides the store, so traffic costs rows. That is what
makes it replayable, and it is also what makes retention a real question rather than an academic
one.

**Four channels is a guess.** The channel set and the digest shape are best-guesses with an
expiry, stated as such. They firm up as real consumers exercise them — and today there are few.

**The human is not wired in yet.** The design intends the author to be a native participant with
channels like any device, rather than an operator reaching in through a side door. The channel
shape exists; the wiring does not.

---

## 5. What would falsify this

- **A posted message does not read back,** or loses its why, sender, or reply-to.
- **A record channel collapses.** The substrate storing less than full truth.
- **A digest alters what `read` returns.** The view mutating the record.
- **A non-bus writer writes the transit table,** or the bus opens its own connection.
- **A device calls another device directly.** One direct call and the trail is no longer
  complete — and a *partly* complete causal record is worse than none, because it reads as
  whole.
- **A surface re-derives traffic instead of projecting it.** The split-brain failure returning
  under a new name.

---

## 6. What is built, and what is red

**Built.** The substrate, its four channels, the record-versus-diagnostic refusal, envelope
validation on why and channel, owner-gated durable transit riding the store, and the device-class
conformance. Proofs green both bare and under the isolated tester.

**Red.**

- **The substrate has very few real consumers.** It was deliberately built *before* the things
  that fire onto it, so the traffic that would exercise the channel design is largely still
  ahead — and **the runtime spine has never run**, which is a live trouble in the system's own
  inbox.
- **Per-device channel ownership, retention, and the human's feeds** are all filed and unbuilt.
- **No protocol adapter exists.** The claim that the substrate is protocol-independent is
  currently a design property with no second protocol to prove it against.

---

*Pattern document, `press_office/PatternTheBus.md`. Part of the Cairn pattern series; the spine
is [`CairnArchitecture.md`](CairnArchitecture.md). Its peer substrate, the heartbeat, is
[`PatternTheGroundLoop.md`](PatternTheGroundLoop.md). All numbers from
[`FactSheet.md`](FactSheet.md), measured 2026-08-11.*
