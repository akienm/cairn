# Intention-Based Design, for humans

*How Cairn is built so it doesn't rot — and how you could build this way too.*

This is an explainer for someone standing outside the system, looking in. You do
not need to know Cairn to read it. By the end you should be able to say the pattern
back in your own words and see how to apply it to something you're building. If you
can't, this document has failed its one job — tell us, because that failure is data.

---

## 1. The problem it solves

Software rots in a specific, boring way. Not usually in a dramatic crash — it rots
because **the description of the system drifts away from the system.**

The predecessor to Cairn rotted exactly like this, and we measured it:

- A rule said "all inference traffic goes through one proxy." A month later, six
  live files were still opening raw connections around it. The logs that were
  supposed to record every connection were blind to hundreds of real ones.
- A rule said "all database access goes through one gateway." Forty files called
  the database directly anyway.
- Dozens of components failed silently for months, quietly emitting records that
  were *shaped* like success.

The root cause was not laziness. It was structural:

1. **The important rules were policy, not physics.** They depended on everyone
   remembering to follow them. At any real scale, "everyone remembers" is worth
   approximately nothing.
2. **The map was a separate artifact from the territory.** The docs, the diagrams,
   the mental model — all lived somewhere other than the code they described, so
   they drifted the moment the code moved, and nothing forced them back.

Intention-based design is the response to both. Two moves:

> **Make intent and structure share an address.**
> **Make the rules that matter physics, not reminders.**

Everything below is a consequence of those two sentences.

---

## 2. The core move: intent and implementation share an address

In an intention-based system, **every component carries its own intention, right
next to its code and its proofs.** Not in a wiki. Not in a design doc in another
repository. In the same directory.

A component looks like this:

```
some_component/
  intention+why.json   ← what this is FOR, and why it exists
  <the implementation>
  proofs/              ← what a hollow copy of this could not pass
```

To be briefed on any part of the system, you **stand in its directory and read its
intention.** There is no separate manual to fall out of date, because the
explanation lives at the address of the thing it explains. If the code has no
intention beside it, the system refuses to run it. The map cannot drift from the
territory because the map *is* filed inside the territory.

This is the whole game in one line: **the description can't rot away from the thing
if they share an address and neither is allowed to exist without the other.**

---

## 3. The name forces the content

Look again at that filename: `intention+why.json`. Not `intention.json` —
`intention+why.json`.

This is deliberate, and it's the part people underestimate. A field you *can* leave
blank, you *will* leave blank under deadline. A folder called `intention.json`
invites a file that says what the thing does and quietly omits why it does it. So we
put the "why" in the **name of the file itself**. Now the artifact can't be named
honestly without carrying its reasoning.

Why fight this hard for the "why" specifically? Because **the why is the only thing
that lets a mind judge whether something belongs.** With only the "what," you can
pattern-match — "this looks like the other things." With the "why," you can actually
*adjudicate* — "this exists to serve that goal, and this new change would break that
goal, so no." A system full of whats is a system that can only imitate itself. A
system where every piece carries its why is a system that can reason about itself.

There's a quieter benefit, and it works on the humans as much as the machine.
**Naming a tool in terms of its structure is how a good tool disappears — in the
good way.** Every time you say the words "intention plus why," you've rebuilt the
discipline in your own head, for free, without having to consciously hold it. The
tool recedes into how you *speak*, which is exactly where you want a good tool to
live. (Contrast the bad kind of disappearing: a tool that lingers unexamined,
unnamed, unquestioned — that's the rot, not the cure. The presence of the "why" is
what separates the two.)

---

## 4. Everything traces upward

If every piece carries its why, you can ask a sharp question of any piece: **what
does this trace up to?**

The system is a chain of intentions, each answering to the one above it:

```
Telos      — why the whole thing exists, and whose it is   (the charter)
  Laws     — the invariants that hold everywhere
    Form   — the shape every component must have
      Charters — what THIS specific component is for
```

Every component's charter must trace to a Law and ultimately to the Telos. The rule
is blunt: **what can't trace up doesn't belong.** This is the immune system. A
feature nobody can connect to a reason isn't a feature, it's future rot, and it gets
turned away at the door — cheaply, before anyone builds it.

---

## 5. The building blocks

The pattern shows up in three recurring shapes: **skills**, **stores**, and
**gates**.

### Skills are question sets

A skill isn't a script that does a thing *to* you; it's a **fixed set of questions
fired at a variable piece of work.** Answers route the work forward; a failed answer
routes it back. That's it.

The core work loop is just four such question sets in sequence:

- **intent** — *What is this? How, roughly? What does it trace to? Is it a new
  thread or an aside? How would we know it's done or wrong?* (An idea that traces
  to nothing dies here, for free.)
- **challenge** — an adversarial pass, run *before* you commit: *Is there a better
  approach? Prior art? Should we back up?*
- **sorted** — the resolution pivot: *Are all the points wrapped? Any hidden
  assumption? Anything missing? Is it falsifiable?* Then the work gets **cast** —
  typed, and bound to the gates its type requires — and broken into children.
- **prove** — the work must pass its gate before it's considered done, and its
  parts must pass before the whole can.

Because a skill is just "which questions load," the same machine runs everywhere —
an intent conversation, a design review, a diagnosis. Only the question set changes.
And every time a question set fires, it can record what it learned, so the system
accumulates a memory of which questions actually catch problems.

### Stores describe themselves

Every place that holds data carries its own charter beside the data —
`_charter+why.json` — stating what this kind of record is for, why it exists, and
the exact current shape of a valid record. Two things follow for free:

- **You never hunt for the schema.** It's always at the address of the data it
  governs. Schema-kept-somewhere-else is the same drift disease as docs-kept-
  somewhere-else.
- **You can't create a new kind of record without first writing down what it's
  for.** That single requirement quietly kills the endless proliferation of
  half-explained data types that buries most mature systems.

### Gates, not supervisors

Here's the part that replaces management with structure. A workflow is **not** a
manager who remembers to check that each step happened. A workflow is a set of
**gates**: mandatory conditions on a state transition, enforced by the system
itself. A piece of work simply *cannot move* past a gate until the gate's condition
holds.

There are three kinds, and every "wall" in the system is one of them:

- **proof gate** — an automated check a hollow or fake implementation could not
  pass.
- **derivation gate** — a generated artifact (like the help pages) recompiles and
  comes out complete. A new command can't ship until the help that indexes it is
  current — so the help is never stale, by construction.
- **signature gate** — a named, responsible human signs. Human judgment enters the
  machine as a *required signature on a transition*, not as an authority standing
  over the work.

Notice what this buys you: **cooperative peers coordinated by a shared state
machine, with nobody supervising anybody.** Everyone does their transform; the gates
validate the handoffs; the current state of the work *is* the single source of
truth about where it stands. No separate tracker to drift out of sync with reality.

Different *kinds* of work carry different gates. Code is proved by an automated
proof. A written concept-piece (like this document) is proved by human review — a
signature gate — and gets kicked back on rejection exactly like a failed build. Same
shape, different check.

---

## 6. The actual primitive: a learning loop

Under all of it is one stance that changes how everything above behaves:

> **There is no certainty, only the current best guess.**

Nothing is ever "done" in the terminal sense. When something passes its proof, it's
not finished — it's *"best current guess, still carrying the thing that would prove
it wrong."* Every artifact ships with its own falsifier (what would show it's wrong)
and its horizon (when to re-check). A result that matches expectation is a
confirmation; one that doesn't is not a failure, it's information — the single most
valuable thing the system produces.

And crucially: **everything has a path back to where it was created — for revision,
not just for notification.** When something upstream changes, everything downstream
that depended on it can be reached and revised. The loop closes. Feedback lands at
the point of creation, where it can actually change something.

So the artifacts — the skills, the charters, the docs, the code — are not the point.
They're **precipitate**: what falls out of a system that is continuously questioning
and improving itself. They are all revisable. None is sacred. This document
included.

---

## 7. Why it can't rot the same way

Put it together and the original two failures are structurally closed:

- The rules that matter are **physics** — enforced by the schema and the system's
  own transitions — not reminders someone can skip. You can't route around the
  proxy if the port is closed to everything else. You can't ship the undocumented
  command if the gate won't open until the docs recompile.
- The map **is** the territory — every intention filed at the address of the thing
  it describes, and no thing allowed to exist without one. The reference material
  is *compiled from* those intentions, so it can't drift: regenerate it and it's
  current by definition.

The system stays honest not because the people are disciplined, but because the
**structure makes the dishonest state impossible to reach.**

---

## 8. What to take with you

You don't need Cairn to use any of this. The transferable pattern is five habits:

1. **Co-locate intent with implementation.** Put the "why this exists" in the same
   place as the thing, and don't let the thing exist without it.
2. **Name things so the name forces the content.** If a piece of reasoning matters,
   put it somewhere it can't be silently omitted — ideally the name itself.
3. **Make your real invariants physics, not policy.** If a rule matters, enforce it
   in the schema or the kernel. Until you do, treat it as a debt you owe, not a rule
   you have.
4. **Compile your documentation from the source of truth.** Never hand-maintain a
   second description of something that already exists. Generate it, or it will lie
   to you.
5. **Treat failure as data and give everything a way home.** Every result teaches
   something; make sure the lesson can reach the place that can act on it.

That's intention-based design. Not a framework — a stance: **make the system carry
its own reasons, and make the rules true by construction rather than by trust.**
