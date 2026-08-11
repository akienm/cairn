# Pattern — The ground loop

### One daemon in the whole system, and all it does is beat

> **The move.** There is exactly one long-running process. It does not execute, resolve,
> schedule, route, or write any other component's state — **it pulses.** Everything that wants to
> happen periodically hangs a **probe** on that pulse through its own shim. And the property the
> whole design exists to protect: **a probe is the same unit whether it fires on a cadence or on
> its own component's internal trigger.** Same shape, same firing path; only the owner and the
> location of its data differ.

---

## 1. The measured failure

**Dozens of daemons, rotting silently.** In this system's predecessor, each component that needed
to do something periodically grew its own loop. Each was reasonable in isolation. Collectively
they were unaccountable: nobody could say which were running, several had been dead for an
unknown length of time, and the only way to find out was to go looking. A dead daemon and an idle
one are indistinguishable from outside.

**The design failure, caught at *n*=1 and worth more than the fix.** The first build of this
component collapsed **three roles into one**: the heartbeat, the executor, and the scheduler. It
worked. It was also the shape that makes the sameness property impossible — once the loop knows
how to *run* things, a scheduled probe and a trigger-fired probe stop being the same object,
because one of them is now the loop's business and the other isn't.

The author caught it the same day, before it hardened. The correction was not a patch: the
executor and its method registry were **deleted**, a central scheduler service **dissolved**, and
one universal mechanism replaced three. **The component learned to be smaller.**

That is the general failure this pattern names: **freezing several roles into one device because
they happen to co-occur.** It is invisible in review, because the collapsed version does
everything the separated version does.

---

## 2. The pattern

### 2.1 The loop only beats

On each `beat(now, context)` it pulses the **shim** of every subscribed device, in subscription
order, and returns a legible beat-record. That is the entire behaviour.

**Handling a pulse lives in the shim** — evaluating the component's probes, each trigger
evaluated *where its data is owned*, and firing the due ones by poking the bus. Not in the loop,
and not in the component body either.

`now` is **passed in explicitly**, so the pulse is provable without a clock. The wall-clock
runner is a thin wrapper around a mechanism that does not need it, which is what lets the physics
be tested rather than waited on.

### 2.2 Firing lives in the shim, and that is what makes probes universal

The decisive property, stated as the charter states it:

> **The probe is the same unit whether it fires on a scheduled cadence or on a device's own
> internal trigger — same shape, same firing path in the shim, only the owner and location of its
> data differ.**

Keeping the ground loop to *just the beat* is what makes that sameness hold. The moment the loop
gains the ability to run something, "scheduled work" becomes a different kind of thing from
"triggered work," and you need two mechanisms, two mental models, and a rule about which to use.

A trigger is **any predicate**. A cadence is one predicate among many. There is no scheduler in
this system, because a scheduler is what you build when a clock is a privileged kind of reason.

### 2.3 Liveness is an owned fact, read — never scanned

The loop holds no runtime state, with exactly one ruled exception: **its own liveness record**,
in its own instance space. Every beat touches it atomically — last-run, state, pid — and a reader
asks a function for a `LIVE`/`DEAD` verdict at a **5-second threshold that has exactly one
address in the code.**

The detector is the whole point, and it is smaller than it sounds:

> **A crashed loop leaves the file behind but stops advancing the stamp. That is the entire
> mechanism.**

No process-table scan, no ping, no supervisor. Liveness is the loop's *own fact* about itself
(Law 6), published where anyone may read it. And because the threshold has one address, nobody
can disagree with anyone else about what "alive" means.

### 2.4 The door guards itself

Any entry point gets the only-once guarantee **by calling the loop**, not by remembering a rule.
The runner claims a singleton **atomically before constructing the device** — a file lock held for
the process's whole life.

The details are the interesting part:

- **Read-then-act is not atomic.** Two entry points can both read `DEAD` inside one window and
  both start. So the claim is the lock, not the reading.
- **The lock is kernel-released on death**, so a corpse leaves no stale claim needing a hand to
  break.
- **A losing launch reads the record, says what is already running, and exits 3** — a distinct
  code, so "someone else has it" is never confused with a crash.

This is what makes spawning the loop *always safe*: a caller does not need to check first, and
therefore cannot check wrongly.

### 2.5 The roster is the navigation, and it invents nothing

The loop publishes its roster at all times — the devices it beats to, in order, each with live
wakefulness. That roster is the authoritative navigation for the presentation surface.

Two things it deliberately is not: **no new owner and no new state.** The roster *is* the
subscription list the loop already holds. A registry of components would be a second copy of a
fact that already exists in one place — the manager smell this system names and refuses.

### 2.6 One web server; a device declares a pane

The loop gets a device page the way every device does: it **declares a pane** whose data *is* the
liveness read, plus a label naming the record it reports from. **Render, never derive** — the
threshold stays at its one address rather than being recomputed for display.

Its shim fronts the handed chassis by constructor injection — **never a lazily-constructed second
loop** — so the heartbeat subscribes to itself and rides its own roster. The self-subscription is
inert under the beat, since it declares no probes.

**Never a route, a port, or a server of its own.**

---

## 3. How it is enforced

**Physics today:** the beat pulses every subscribed shim in order and pokes nothing itself; a due
probe's poke comes from the shim; `subscribe` refuses a non-shim and is idempotent by device id;
**one shim raising cannot stop the beat**; the executor and its registry are provably absent; the
liveness stamp advances while running and not otherwise, is written atomically so no reader sees a
torn record, and the 5-second threshold has one address; the singleton claim is a lock rather than
a check, with the loser exiting on a distinct code.

**Still prose (tracked as debt):**

- **The runner is session-mortal.** A host unit file that keeps it alive across sessions is a
  standing debt — and it is a *host* seam, meaning its implementation lives where version control
  cannot see it, so it needs a replayable recipe and a re-runnable check rather than a file.
- **Subscription is in-process.** Discovering subscribers by scanning component trees grows when
  devices become separate operating-system processes.

---

## 4. What it costs

**A pulse that mostly finds nothing to do.** Every subscribed shim is pulsed on every beat,
whether or not any of its probes are due. That is cheap and it is not free, and it is the price of
having one mechanism instead of a scheduler with a due-time index.

**Terminal simplicity means the heartbeat cannot learn.** It is the floor everything beats on,
deliberately incapable of adaptation. All learning happens in the probes hung on it. If the
cadence itself should adapt, that adaptation has nowhere to live here — by design, and that design
is a bet.

**One process is a single point of failure**, and the honest mitigation is small: the loop
publishes its own liveness, so its death is *visible* rather than prevented. Nothing restarts it
today.

**The sameness property is a claim, not yet a measurement.** Whether one heartbeat plus
shim-fired probes really covers both a scheduled cadence and a component's own internal trigger
**with the same probe** gets settled as more real probes land. Today there are few.

---

## 5. What would falsify this

- **The loop does more than beat.** If it resolves a method, runs a probe, writes state, or
  routes a poke, it has re-absorbed the shim's role — the original collapse, returning.
- **Firing lives anywhere but the shim.** A component that must implement its own loop to get its
  probes fired breaks the universality claim outright.
- **A cadence-fired probe differs in shape or handling from a trigger-fired one.** The sameness
  is the whole point; if it does not hold, the ground loop is a scheduler wearing a smaller name.
- **The heartbeat grows runtime state** beyond its own liveness record.
- **The stamp advances while the loop is dead,** or fails to advance while it runs, or a reader
  sees a torn record, or the 5-second threshold gains a second address.
- **The only-once guarantee breaks:** two simultaneous launches yielding two loops, a loser
  blocking instead of refusing loudly, a dead winner's claim needing a hand to break, or the guard
  deciding from the process table instead of the lock and the record.
- **A second daemon appears anywhere in the system.** Reaching for a background process — and
  especially reaching for a periodic scan as a "backstop" — is how the predecessor's disease
  returns. The correct move is to find the event that already fires.

---

## 6. What is built, and what is red

**Built.** The beat and its ordered pulse; probe firing located in the shim; idempotent
subscription that refuses a non-shim; one raising shim unable to stop the beat; the liveness
record with its single-address threshold; the self-guarding runner with its lock and its distinct
loser exit; the roster as navigation; the declared liveness pane. Proofs green bare and under the
isolated tester — and they compose the **real** shim and probe with a spy bus, so the
beat → pulse → fire chain is proved end to end without a database.

**Red.**

- **The runtime spine has never run.** This is a live trouble in the system's own inbox, and it
  is the honest headline: the heartbeat exists, is proved, and has not yet carried a real fleet.
- **No real device shims are subscribed at launch.** The record needed a beating loop, not a
  populated roster; subscription grows against need.
- **The runner dies with its session.** No host unit file yet.
- **The universality claim is unmeasured** at any interesting number of probes.

---

*Pattern document, `press_office/PatternTheGroundLoop.md`. Part of the Cairn pattern series; the
spine is [`CairnArchitecture.md`](CairnArchitecture.md). Its peer substrate, communication, is
[`PatternTheBus.md`](PatternTheBus.md). All numbers from [`FactSheet.md`](FactSheet.md), measured
2026-08-11.*
