# The outreach packet

### Who to show this to, in what order, what to send them, and what would count as signal

**Status:** drafted 2026-08-11, awaiting the signature gate. Nothing here has been sent.
Sending is Akien's act, not the drafter's.

---

## 0. The caveat that goes first, because it protects the sender

The list of people below, and the claim that *"nobody is doing this,"* both come from **one
conversation with one assistant on 2026-08-04** (`~/.akien/20260804…`). That conversation
was not a literature search. It named no papers, no years, and no search it had run.

> **Every "nobody does X" in the source is a hypothesis about the field, not a result.**

Both drafts already say this in their own related-work sections, and the packet says it
again because this is the point where it can actually cost something: an email that opens
with *"nobody has built this"* to someone who built a version of it in 2003 ends the
conversation in one reply. An email that opens with *"here is the correspondence I see
between this and SOAR's chunking, and here is where I think it diverges — am I wrong?"*
survives being wrong.

**The whole strategy is built to be wrong safely.** From the paper's own conclusion: *if
any one of them says "this is new," that is signal. If any one of them says "we solved that
in 2003," that is better signal.*

---

## 1. The three groups, in the order to approach them

The order is not arbitrary and it is not by prestige. It is by **who will understand the
hardest part fastest** — approach the group that can falsify you soonest, first.

### First — cognitive architecture

| | |
|---|---|
| **Who** | John Laird (SOAR, Michigan) · Christian Lebiere (ACT-R, CMU) · Paul Rosenbloom (Sigma, USC) · the OpenCog community |
| **Why first** | They already think in production rules, question-like operators, and self-modifying inference. The core loop — miss → resolve → deposit → the miss does not recur — is *structurally SOAR's impasse → subgoal → chunk*, and they will see that in one paragraph. |
| **What they will recognize** | the loop, immediately |
| **What they can tell us that nobody else can** | which of our "new" problems were solved in the 1990s. ACT-R's activation and decay equations are directly relevant to tenure, and we would rather borrow them than re-derive them badly. |
| **Send** | [`PreludeCognitiveArchitecture.md`](PreludeCognitiveArchitecture.md) + the paper + the fact sheet |

### Second — neuro-symbolic reasoning

| | |
|---|---|
| **Who** | IBM Research's neuro-symbolic group · MIT's concept-bottleneck-models group · DeepMind's neuro-symbolic reasoning team |
| **Why second** | They share the instinct that structure should be inspectable rather than only distributed — concept bottlenecks in particular share the *one claim per node, and it must be nameable* constraint. What they do not have is deterministic, question-driven expansion with a gate that refuses insufficient input. |
| **What they will recognize** | the graph-tree novelty expansion |
| **Send** | prelude (unwritten) + the paper + the fact sheet |

### Third — program synthesis and dynamic graph learning

| | |
|---|---|
| **Who** | Microsoft Research (PROSE) · Google Brain (neural program synthesis) · the CMU Graph Learning Lab |
| **Why third** | They understand structural update mechanics better than anyone, and they are the readers most likely to have a sharp opinion on the calving/shear cost model — which is the part with the largest gap between design and measurement. |
| **What they will recognize** | the structural update mechanics |
| **Send** | prelude (unwritten) + the paper + the fact sheet, and lead with §6 |

---

## 2. Venues

Named in the source conversation, unchanged: **AAAI · CogSci · NeurIPS (workshop track) ·
ICLR (workshop track) · the AGI Conference.**

One honest note on fit. [`NoveltyDrivenGraphTreeExpansion.md`](NoveltyDrivenGraphTreeExpansion.md)
says of itself that it is an **architecture-and-protocol paper, not a results paper**, and
that its measurements are *n*=1 and labeled as such. The workshop tracks and the AGI
Conference are the honest fit for that today. AAAI and CogSci become honest when §7's
evaluation protocol has actually been run — **and running it, not rewriting the paper, is
what closes that gap.**

---

## 3. Document components — how one paper serves several fields

Akien's constraint, from the request that began this work: *prefer not to produce a
specialized paper per field; a field-specific first part with the generalizations as the
second part.* That is the scheme.

```
  PART I   — the field prelude          ~1,500 words   ONE PER FIELD
             written in that field's own vocabulary
             ↓
  PART II  — the architecture           the paper      SHARED VERBATIM
             ↓
  PART III — the measurements           the fact sheet SHARED VERBATIM
```

**Part I is the only part that varies.** It does one job: put the reader on ground they
already stand on, then walk them to the door of Part II. Its shape is fixed:

1. **The correspondence** — this architecture in *your* vocabulary, as a table.
2. **The divergence** — the one place it is genuinely not your thing, stated sharply.
3. **The problem you do not have** — the failure mode our design exists to survive, and
   why your design never had to face it. This is the part that earns the reading.
4. **The ask** — the specific question only this field can answer, phrased so that
   *"solved in 2003"* is a welcome answer rather than an embarrassing one.

**Parts II and III are shared verbatim, never re-cut per field.** The moment a field gets
its own edit of the architecture section, there are three architectures and no way to tell
which one anybody read.

**No compiler is built until three preludes exist.** A compiler written against one prelude
is a compiler built to a shape of one — it would freeze whatever the first prelude happened
to do into a schema. Until then, assembly is a human concatenating three files in order,
which costs about a minute and is honest about how much structure has actually been earned.

**Built today:** [`PreludeCognitiveArchitecture.md`](PreludeCognitiveArchitecture.md), the
first prelude and the worked example of the shape. The other two are red.

---

## 4. What to send, concretely

For the first contact, the source conversation's own prescription is right and short — the
problem, the architecture, the novelty mechanism, the constraint layer, a worked example, a
diagram, and a comparison to existing approaches. All seven exist across the current
documents. The mapping:

| What is wanted | Where it already is |
|---|---|
| the problem | prelude §1–3, paper §1 |
| the architecture | paper §3–4, brief §2 |
| the novelty mechanism | paper §4 — proto-node, window, promotion |
| the constraint layer | paper §4.3 |
| a worked example | paper §5 — and it is a *negative* result about our own design |
| a diagram | paper §3.3 |
| comparison to existing approaches | brief §5, prelude §2 |

**Nothing new needs to be written to make first contact.** That was worth checking, and it
is the reason this packet stops here rather than proposing another document.

---

## 5. What would count as signal

Stated in advance, so that the answer cannot be reinterpreted after it arrives:

- **"This is new."** — Weak positive. One person's read. Two independent ones is a
  different thing.
- **"We solved that in 2003."** — **The best outcome on this list.** It converts a
  re-derivation into a citation, which is Law 1 operating at the scale of a field.
- **"Your failure mode is real and here is what we call it."** — The single most valuable
  reply available, because the manufactured-resolution finding is the paper's actual
  content and it is *ours*, measured, at *n*=1.
- **"Your tenure rule is ACT-R's utility equation with different words."** — Also excellent.
  Borrow it, cite it, and delete our version.
- **Silence.** — Data about the pitch, not about the architecture. Silence from all three
  groups says the framing failed to reach anyone, which is a fixable problem and a real
  measurement.

**What would not be signal:** general encouragement. It is the most likely reply and it
means nothing. Do not record it as validation.

---

## 6. What is red

- **Nothing has been sent.** This is a plan, and a plan is a hypothesis.
- **Two of three preludes are unwritten.**
- **The evaluation protocol in the paper's §7 has not been run.** It is what would move the
  paper from a workshop fit to a conference fit, and it is a larger piece of work than
  everything in this folder combined.
- **The field survey behind the target list is one secondary source.** A literature pass by
  someone who reads these venues is the right next step and has not happened.
- **No one has read any of this but its two authors.** *Does it survive a second person?*
  remains the standing falsifier over the whole press office.

---

*`press_office/OutreachPacket.md`. Targets and venues from the 2026-08-04 conversation at
`~/.akien/20260804.AkienAndCopilotOnWirtignAPaper.txt`. The shelf is
[`INDEX.md`](INDEX.md); all numbers are in [`FactSheet.md`](FactSheet.md), measured
2026-08-11.*
