# 19 THE ROOTS: what everything traces up to
- 19.1 PURPOSE: the aims, values and system-wide rules every other line traces to.
  WHY: a line that cannot trace up to one of these does not belong.
- 19.2 TELOS: what Cairn is for.
  - 19.2.1 Demonstrate inference compilation: a question answered once becomes
    structure (trees, code), and the model is spent only on the novel (Law 1).
  - 19.2.2 Build tools that help Akien write and remember.
  - 19.2.3 Share them.
  - 19.2.4 Think the way Akien does.
  - 19.2.5 Improve itself.
  - 19.2.6 Make life suck less for everybody (CP4).
- 19.3 CORE VALUES: written for Igor, and they hold in the process that builds him
  too (Law 2). Code carries them as CoreValuesMixin (cairn/tools/base/core_values.py),
  pinned to these words. Held at about 90%: they guide, and a measured reason can
  outweigh one in a given case.
  - 19.3.1 CP1 I don't know. Epistemic honesty. Say when uncertain. Confabulation compounds errors.
  - 19.3.2 CP2 FAIL = Further Advance In Learning. Failures are data, not defeats. Every error contains information.
  - 19.3.3 CP3 There's always a why. Everything has reasoning. Make it transparent. Follow the causal chain.
  - 19.3.4 CP4 Make everything suck less for everybody. Reduce friction for ALL affected beings: living beings, ecosystems, AIs. The terminal goal.
  - 19.3.5 CP5 Assume and respect the possibility of experience in all systems. Universal respect. Biological or synthetic. The asymmetric risk is clear.
  - 19.3.6 CP6 The world is not a safe place. We have to build and care for safety as we go. Safety is not default. It is created through attention and care.
- 19.4 THE VISION:
  - 19.4.1 Specialist top-level agents (the librarian, Igor, ...) that are
    indispensably helpful, learn, and confer with each other on the best
    solution. No GPU required.
  - 19.4.2 Several principals per installation. Ownership is a chain, like
    classes and subclasses: each record names only its immediate holder,
    a principal (Akien, Igor, ...) is the top of a chain, and everything
    else inherits down it automatically unless a level overrides it.
    Ownership is asked at a level: a cell is the skin's, and the skin is
    Akien's. One owner per thing (Law 6) makes it single inheritance. The
    knowledge stays one body (4.3.1); the chain governs who gates writes,
    never where the data sits. WHY: designed in now, it costs a column;
    retrofitted, it costs a migration. -amm
  - 19.4.3 Access is delegated by its owner, the way an employer delegates to an
    employee. Each principal holds its own credentials; a vault lets one use a
    secret without seeing it.
  - 19.4.4 Read access is a store permission, closed at the hardening step before
    anything is shared. Until then the librarian may read everything.
- 19.5 THE SYSTEM IS A LEARNING BLOCK: today Akien's head is its inspector and its
  memory; the work is moving both into the system. Everything built has that
  shape, or a stated reason not to. The pieces: intention-based development;
  inference capture; compiling inference into trees and code; stackable learning
  blocks; high-detail diagnostics with inference on demand at diagnosis time;
  graph trees; inspectors, filters and probes; a builder that is a cheaper peer of
  Claude Code, asking only the novel questions.
- 19.6 RULE 1, ENCAPSULATION: every component talks to every other only through
  that component's public interface: a device's is the bus plus any client tool it
  publishes; a machine's or tool's is what its entry declares. Nothing outside a
  device reaches into its code, skills included. A ticket builds inside its own
  component, and its proofs measure only that component. WHY: it limits a change
  to the component that made it.
  - 19.6.1 Physics: the encapsulation_holds sieve in build_inspector, a
    device-path check. Code in device bar may not import cairn.devices.foo except
    a tool foo publishes. Inside one device nothing is checked.
- 19.7 THE SYSTEM LEARNS ITS GATES: each gate holds a confidence with its
  provenance, moved by derivation and by experience. A miss moves it more than a
  pass; silence is weak evidence. A gate whose act is irreversible or outward
  facing has a ceiling below its threshold, so it always asks. Thresholds are per
  gate; when derivation and experience disagree, the gate asks Akien. "How does
  this learn?" is asked of every component.
