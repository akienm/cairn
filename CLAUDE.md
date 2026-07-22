# Cairn

Compiled navigation: stones stacked so the next mind doesn't re-derive the route.
You are standing in **class-space** (`~/dev/src/cairn/`) — code and the record of
how it got here; no *runtime* state, ever (that lives in instance-space).
This is the first file every Cairn mind reads; it stays true and small by
construction. Its charter: `CairnCommons/intentions-other/I-cairn-claude-md.md`.

**Orientation**

- `MAP.md` — the working map (transitional; dissolves into intentions + tickets).
- `CairnCommons/intentions-other/telos.md` — the charter everything traces up to.
- To be briefed on a device, **stand in its directory**: every component
  co-locates its **charter** (`intention+why.json` — the *summarized design*:
  authored, the settled why+role, changes only when the design shifts) + code +
  `state` (compiled from the component's tickets; never hand-edited) + `history`
  (append-only; a ticket's voyage freezes here when it proves out) + `proofs/`
  and the validations that sealed them. A component without an intention doesn't
  run. (The filename forces the why — CP3 as schema, not as a field someone can
  leave blank.)

## The Laws

Present-tense contracts, dependency order. Everything Cairn does traces to one;
what can't trace up doesn't belong.

1. **The resolver is spent on the novel, not on re-deriving the settled.** Every
   answered question becomes structure; re-deriving a settled answer is a defect.
2. **CP1–CP6 hold everywhere, including in the process that builds the system.**
   (The six: `CairnCommons/intentions-other/core-values.md`.)
3. **Nothing is known until measured.** An unmeasured claim is a hypothesis and
   is labeled as one.
4. **A rule that matters is enforced by physics, not policy** — the kernel or the
   schema. Until it is, it is a tracked debt (an IOU), not a resting state.
5. **Intent, its voyage, and its proofs share an address.** Every component
   carries its charter, its `state` + `history`, and its proofs and validations
   beside its code. The thing and the story of the thing cannot drift apart.
6. **Everything has exactly one owner.** The owner alone gates writes to it;
   delegated access and ownership transfer happen only through the owner's gate,
   never ambiently.
7. **Errors are loud at diagnostic surfaces and permanent in records of truth.**
   A presentation surface may collapse an error into a coherent shape; a record
   of truth never may.
8. **Nothing enters proven-space without a proof a hollow build couldn't pass.**
   Entry from outside is by grafting, one ticket at a time.

## The three roots

| Root | Holds | Rule |
|---|---|---|
| `~/dev/src/cairn/` | code, skills, charters, `state`/`history`, proofs, validations | class-space; git; shareable; no *runtime* state |
| `~/dev/src/CairnCommons/` | intentions, decisions, tickets, questions, troubles, proofs, slates | knowledge; own repo; *if losing it loses knowledge, it's commons* |
| `~/.cairn/` | logs, credentials, flags, cached state, personal data | instance-space; never in git |

Runtime instances live at `~/.cairn/devices/<device>/<instance>/`; a singleton
is instance `0`, not a special case.

**Which root?** Ask whether the intention has **one** code address. A
**code-seam** does, so it berths in `cairn/` beside it — its ticket stages in
`CairnCommons/tickets/`, then migrates beside the code to become that
component's `history`. Everything else berths in
`CairnCommons/intentions-other/` and never migrates: a **concept-piece** (the
prose *is* the implementation), a **host-seam** (the machine itself — a hook, a
package, a unit file), the **roots** (`telos.md`, `core-values.md` — implemented
by the whole system), and **spanning** intentions (plenty of code, but in many
places at once, so no one directory can hold them). Homeless means *no* address
or *many*. Everything we intend to share is a git file; the database holds only
the graph trees.

`intentions/` is **compiled** from `intentions-other/` plus the charters homed
beside the code — which is what lets that one folder be carried to a bare
machine and regrow the system. A host-seam therefore carries a replayable
`apply` recipe and a re-runnable `verify`: its implementation lives where git
cannot see it, and its seal expires (the host drifts with nothing in git
changing).

## Rules awaiting physics

Prose here is an IOU for enforcement. Each rule's home is its device's charter;
this file points. Each retires the moment the tester enforces it — this section
shrinks monotonically.

- Durable *relational* state — the graph trees — goes through `db_domain` / the
  store primitives; shareable provenance is git-JSON beside the code, not a row.
  → tester import-scan · *ticket pending tickets-store*
- A compiled view is never hand-edited: `state` is written only by the
  projector's append door, and a record of truth is never changed in place.
  → single write-door + tester drift check · *ticket charter-state-history-split*
- The inference host is reached only through `inference_domain`.
  → kernel network ownership · *ticket pending tickets-store*
- Port 5432 is reached only through `db_domain`.
  → kernel-closed port · *ticket pending tickets-store*
- Every component's charter answers "how does this component learn?" — "it doesn't,
  because X" is a valid answer; silence is not.
  → charter-schema field + tester non-hollow check (Law 8) · *ticket learning-as-a-pattern*

This file has its own charter and stands the `/challenge` gate on a cadence —
the file that briefs every session is the most-challenged artifact in the system.
