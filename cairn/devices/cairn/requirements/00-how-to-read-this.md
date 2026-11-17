# 0 HOW TO READ THIS
- 0.1 Every line has an outline number; refer to anything by it ("5.5.3"). Lines
  are renumbered after each round of edits, so a number holds within one
  conversation, not across them.
- 0.2 WHYS: what these files keep is the intention and its why.
  - 0.2.1 A line states the intention (the build target) in plain words: what it
    is and why. Every new input, answered question or measurement is read
    for how it changes or elaborates an intention or a why. That meaning is
    folded in; the words and the history that carried it are left out.
  - 0.2.2 Every entry has a why. [why?] marks one still to be written. WHY: the
    why is what a later adjudication reads.
- 0.3 WHOS: who settles what.
  - 0.3.1 Akien's head is the spec: what the system should be. Every artifact,
    these files included, is a translation of it.
  - 0.3.2 CC (any CC session) writes readings: its translation of what he means,
    and the specific contents of the tools he designed (17.11.6.1).
  - 0.3.3 Evidence, a measurement, says what is. It settles what it measures,
    for everyone.
- 0.4 CONFIDENCE: what each mark means.
  - 0.4.1 A CC by-line: 80%+. Enough to build on and learn from; it does not hold
    the build.
  - 0.4.2 "-amm": Akien's call, 90%. It outranks a CC by-line in adjudication.
  - 0.4.3 Evidence tops even "-amm".
  - 0.4.4 HYPOTHESIS marks a mechanism written as a first draft so that
    experiments have something to be wrong about. It is not a decision;
    what the experiments show replaces it (Law 3).
- 0.5 SIGNING: where a decision must be recorded, the line ends with a by-line
  naming who made the call. Lines with no decision in them carry none.
  - 0.5.1 Akien signs "-amm", and adds it himself to the lines he approves.
  - 0.5.2 A CC session signs "- <session name>" (eg
    "- akiendelllinux_orchestrator", "- akienasus_cc_0").
  - 0.5.3 A CC reading he approves carries both: the CC by-line, then "-amm".
  - 0.5.4 A line without "-amm" is not his call. When lines conflict, the
    by-lines are checked first. WHY: the by-line says whose call a line
    is, so an adjudication starts from who decided rather than
    re-deriving it.
- 0.6 QUESTIONS: a question is [Q#n: ...], placed at the line it bears on. Its #n
  is its own and never changes; a new one takes the next unused number,
  which is 124. An answered question disappears: its answer is folded into
  the intention and why (0.2.1), and signed where it records a decision
  (0.5).
- 0.7 Entry shape: PURPOSE / WHY / INTENTION / ANTI-INTENTION (where needed) /
  COMMANDS (VERBS on the bus; USERS for a tool).
- 0.8 Everything expressed here (names, concepts, implementations) is what we
  keep. Where the code still says otherwise, the code changes.
- 0.9 These files live in cairn/devices/cairn/requirements/, one per section, and
  TOC.md names each. They are the map of the system; there is no other. Git keeps every version.
- 0.10 An artifact is present tense or past tense, never both. Present tense is
  rewritten whole and points at its provenance; past tense is append-only, opened
  when needed, and read cold only through a compiled face (state, the latest
  slate). WHY: what a cold reader loads at an address should be what is true now.
  - 0.10.1 A dated aside (retired, formerly, a date in parentheses) in a
    present-tense artifact is history in the wrong place, and reads red.
