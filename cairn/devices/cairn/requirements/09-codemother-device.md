# 9 CODEMOTHER DEVICE (cairn/devices/codemother/)
- 9.1 PURPOSE: The mother that looks after the codebase.
- 9.2 WHY: CC papers over things and doesn't hold a boundary across a session, and
  memory doesn't stick. Akien watches for the papering; CodeMother is the
  response to it, so the watching is not his alone.
- 9.3 INTENTION:
  - 9.3.1 She is NOT a builder: Claude and aider build. She owns the care of the
    code: the inspectors, gates, processes and workflows the builders pass
    through are hers to own and, eventually, to optimize.
  - 9.3.2 Prebuild face: the chart chain, eight machines, each answering one
    question before a build begins: orient (what is asked, where does it
    live), constrain (what bounds it), survey (what already exists), decompose
    (how does it split), triage (what first, by what standard), hypothesize
    (what do we expect, how would we know we're wrong), validate (what does
    DONE mean, measured), and after the build, verdict (what done actually
    meant).
    - 9.3.2.1 Each stage moves from the model to deterministic code once a
      proof a hollow build could not pass can hold it; hypothesize stays with the
      model longest. Validate sends a local miss back to hypothesize and a
      structural one back to design. A build that finds new work spawns children
      that enter at decompose.
  - 9.3.3 Watcher face: watches the code and the builders' work over time, reasons
    over it with graph trees (held by the librarian's delegation), and learns
    the failure modes. Learns from: code, chat logs, books, past projects,
    CC's failure modes.
  - 9.3.4 There is no builder device. The builder is a CC session (or aider, 13),
    and the chart stages it uses are machines inside CodeMother.
  - 9.3.5 Owns the inspectors and gates (9.4): everything in the code pipeline that
    checks. The exception is diagnostic_inspector, which is base's (17.1).
    - 9.3.5.1 Outline check: when a ticket is cast, the cheapest model reads it
      beside the outline sections it touches. A conflict, or an open
      question in those sections, becomes a question on the ticket, which
      holds its build until answered. It reads the outline as it stands
      each time, so editing the outline costs nothing.
      - 9.3.5.1.1 A ticket's plan carries only what a door can check. A decision
        line's by (free prose on every ticket) is not checked
        and not kept: the cast door checks writes_to and reads, and by
        goes. Who authored a line is not tracked, except on a gate-pass
        certificate. WHY: tickets moved from prose to JSON so their
        contents can be checked; a field no door checks is prose. - CC
      - 9.3.5.1.2 A ticket's plan is a plan, not a list of decisions:
        constraints, outcomes and resources.
        - Outcomes, not tasks: each is a claim a proof can check. An
        outcome hides the how.
        - Constraints: the bounds, and every how Akien is attached to
        (encapsulation, the bus as the only channel).
        - Order comes only from real dependencies (you can't test the
        bus envelope shape until the bus works), and those also set
        ticket order.
        - Resources: existing machines, tools and design patterns,
        named when they need stating.
        - A plan too big splits into tickets. Early steps can reshape
        later ones, so the whole is checked for coherence at the end.
        -amm
        - 9.3.5.1.2.1 The reading:
          - A plan is three parts. Constraints: the bounds, plus every how
          Akien is attached to, carried verbatim (encapsulation, the
          bus as the only channel, ...): a how he states is a
          constraint. Then outcomes. Then resources.
          - An outcome is {n, claim, writes_to, reads, after: [n or a
          ticket id], via?}. The claim is falsifiable, one proof tooth
          per outcome. The falsifier's clauses merge into the outcomes;
          there is no separate falsifier list. Old clause n stays
          outcome n; outcomes made from decisions number after them.
          via (optional) names the tool or pattern to use, drawn from
          resources.
          - Order comes from after: only real dependencies, which also
          shape ticket order. Nothing invents them; list order is reading
          order only.
          - Resources: pre-existing machines, tools and design patterns,
          named when they need stating.
          - The migration is two steps. Mechanical, on every open ticket
          now: the plan moves to the new field with clause numbers kept,
          the trail moves whole to the log, by moves to the log.
          Judgement, when a ticket is next opened for build, never in
          bulk: each decision becomes an outcome or a constraint, then a
          coherence check (every step reads as current; a conflict
          moves to the log or is named).
          - CC inference: the mechanical step writes each old decision as
          an outcome numbered after the clauses, carrying its text and
          no claim; an outcome with no claim is awaiting judgement and
          holds BUILDME until the judgement step gives it a claim or
          moves it to constraints. - akienasus_cc_0
          - During the change every reader accepts both shapes. Readers
          are censused first; one sibling ticket per reader component
          (RULE 1).
          - The cast door refuses an outcome with no falsifiable claim, and
          a plan of more than about 7 outcomes, naming children; each
          refusal is recorded so the ceiling can be tuned (the 7 is CC's
          guess).
          - The [?] markers go.
          - Tickets: aa3e9a70db47 is the migration (rehearsal);
          d421051bc1f7 is the hand-built worked example; each reader
          component has its sibling.
          - akiendelllinux_orchestrator -amm
  - 9.3.6 Holds the charter tool's instance (17.6): build-quality feedback is hers.
- 9.4 MACHINES:
  - 9.4.1 harbor_master
    - 9.4.1.1 PURPOSE: Reports where every ticket stands.
    - 9.4.1.2 WHY: tickets live in several places (staged, beside code, in port), so
      one register answers "where is everything?" without asking each. [why?]
    - 9.4.1.3 INTENTION: harbor master is a reporting system and nothing more: it
      reports where everything is, and nothing else. It owns no
      gates and controls nothing. It keeps the register of every ticket:
      open, at sea, in port. Task, trouble and fixit tickets show there too;
      inference tickets do not.
    - 9.4.1.4 TOOLS: base, artifact, charter, operator_inbox, proof_coverage,
      question, system_word; machine learning_block.
    - 9.4.1.5 VERBS: status queries only (show, get), and crossing, the notice a
      ticket sends as it moves, which keeps the register. It answers no gate
      and moves no ticket. A ticket that would cross a gate asks that gate
      itself for an inspection, and either receives a pass or sends itself
      back to design (3.3.4). WHY: crossing is the ticket's act, not the
      register's. So `clear` and `watch` leave the bus face (both are
      still there today). COMMANDS: cairn codemother harbor_master
      -> "652 boats (570 open, 82 in port)".
  - 9.4.2 tester
    - 9.4.2.1 PURPOSE: The system's notary: runs proofs and seals their verdicts.
    - 9.4.2.2 WHY: Law 8: nothing enters proven-space without a proof a hollow build
      couldn't pass, and the verdict must come from a hand the builder did
      not guide. A green cannot be self-granted. A machine under
      CodeMother, not a device: CodeMother does not build, so the tester
      inside her puts no builder between a build and its verdict, and
      nothing here needs its own process in the rack, since each proof run
      is its own process already.
    - 9.4.2.3 INTENTION:
      - 9.4.2.3.1 Runs a proof as its own process and writes a validation record
        (claim, caller, date, method, verdict, evidence, falsifier,
        horizon).
      - 9.4.2.3.2 Hollow runs: proves a proof goes red when the build is removed.
        - 9.4.2.3.2.1 A tooth whose live subject was deleted retires with it, when
          fixture teeth still cover the behaviour.
      - 9.4.2.3.3 Seals: one current validation per proof, beside the proof. A seal
        holds while the code it measured is unchanged.
        - 9.4.2.3.3.1 A seal is host independent: one record per proof, whichever
          box asks. Seals are made by one sealing machine in the cairn
          device, and there is only ever one cairn (until a laptop dies
          and a backup takes over), so there is one sealer. A box that
          is not cairn's home asks the sealer instead of writing its own
          seal.
      - 9.4.2.3.4 A timed-out run is its own outcome, not red.
      - 9.4.2.3.5 Notices: what a run saw that nobody asked about, surfaced to the
        operator.
      - 9.4.2.3.6 Test runs are transient (30 days, 4.3.2); seals are records of
        truth (git).
      - 9.4.2.3.7 Test tiers: commit, hourly, daily and weekly. Each tier runs
        only what it must, so a commit needs only its own proofs and
        the long runs wait for the long tiers; nothing runs just in
        case.
        - 9.4.2.3.7.1 Commit: the proofs of the component the ticket changed,
          since RULE 1 bounds a change to its component. Passing them
          puts the component in service, yellow: proven where it
          changed, not yet measured against what depends on it.
          In service needs only the best we can do now: 80% trust.
        - 9.4.2.3.7.2 Hourly: an entry on Cairn's scheduled list (5.9) reseals every
          yellow component and everything that depends on it. Commit a
          is fine and commit b is fine, and an hour later the run finds
          a new red. That is the system doing what it was designed to do,
          and the window to search is one hour's
          landings.
        - 9.4.2.3.7.3 Daily, in sleep (5.3.3): every proof.
        - 9.4.2.3.7.4 Weekly: what is too long or too host-bound to run daily,
          such as hollow re-runs of every proof and each box's own
          run of the proofs it can run.
        - 9.4.2.3.7.5 Reds don't get lost. Each run writes a ticket for every new
          red it finds and every orphaned file it sees, unless one is
          already open for it. A red seen in passing gets the same
          treatment. Every red and every orphaned file is fixed; one
          unrelated to the work in hand is ticketed, and once it is,
          that crossing can go ahead.
        - 9.4.2.3.7.6 A red is first a question: is the code wrong, or is the tooth
          measuring the wrong thing? An LLM reads the work against the
          component's why, the tooth's why and CP1-CP6, because even the
          Laws rest finally on the core principles. Either the code or
          the tooth changes, and a tooth change carries that decision in
          the same act (corrosion, 17.11.6). A tooth a hollow build
          could pass is worthless at every tier (Law 8).
      - 9.4.2.3.8 A proof that cannot go red without its build (its hollow is
        empty) stands only on Akien's answered approval, recorded as the hollow
        reading and re-read at clearance; any other empty hollow is red.
      - 9.4.2.3.9 A green no one vouched for still completes, and notifies the
        operator with the file, the diff and the rate.
    - 9.4.2.4 TOOLS: base, validation_store, proof_coverage, scratch, question,
      proof_discovery, chain, bus_client, artifact, system_word; machine
      build_inspector; db client.
    - 9.4.2.5 VERBS: run, notices, CodeMother's verbs reached over the bus (RULE 1).
      COMMANDS: cairn codemother test (--hollow, --seal, --exec, ...),
      shortcut cairn test; proofgate (the hook: proofs run by hand).
      - 9.4.2.5.1 The seal is checked where the proof runs, not in the command's
        text: a proof refuses to run outside the tester's seal, so no spelling
        reaches the live ~/.cairn. proofgate only rewrites the common spelling
        for convenience. CC's decision, Q#101.
  - 9.4.3 build_inspector
    - 9.4.3.1 PURPOSE: Python sieves run over a build; reds a component that fails
      one (no charter, no proofs, a silent device, ...). A new kind of
      failure found is a new sieve added.
    - 9.4.3.2 WHY: the inspector does all the checks, so there is no need for more
      checks anywhere else (17.11.1).
    - 9.4.3.3 INTENTION:
      - 9.4.3.3.1 It outputs only its findings. It certifies nothing, records no
        crossing, and posts nothing; the gate consumes its findings.
      - 9.4.3.3.2 It is the READY TO MERGE ONTO MAIN step of the pipeline:
        everything's proved, and merging implies pushing it up. With a
        branch per ticket (3.3.6), commits on the branch are as often as
        we like; the inspector is the step at ready to merge. Checking
        what a change touched belongs here; nothing hangs off the git
        post-commit hook.
      - 9.4.3.3.3 Built with the nest machine (16.2).
      - 9.4.3.3.4 Once build_inspector moves into CodeMother, code outside her
        reaches it over the bus: the 18 crossing calls in transitions.py,
        the other code sites and the 82 proofs that run a sieve over
        themselves. No published client tool, no fifth exception: that is
        what the bus is for.
      - 9.4.3.3.5 A rule not yet enforced is made into a ticket now, never left
        floating as an IOU. So ticket f5dbfddea8c6 makes the rewrites it
        proposed at the remaining sites (the press
        office, PROOF.md). Where a site names a rule whose physics is not
        built, it names that rule's real ticket id, cast now if none
        exists; the word "ticket" with no id behind it does not count. - CC
        - 9.4.3.3.5.1 CLAUDE.md and MAP.md are not edited site by site: CLAUDE.md
          is rewritten from these pieces (10.3.11) and MAP.md dissolves, so
          neither carries the word after that. The three rules CLAUDE.md
          still lists as gaps (relational state, the derived lab, history
          reach) are built (inspector.py, compiler.py verify_lab), so the
          rewrite drops them. CC's decision, Q#117 and Q#118. - CC
  - 9.4.4 plan_inspector: reads charters' own admissions of what they don't yet do,
    so nothing reads as done while it says otherwise.
  - 9.4.5 corrosion: catches a constraint that stopped constraining with no decision
    behind it. WHY: drift with a decision behind it is the system learning;
    drift with none is decay.
  - 9.4.6 exemptions: the declared list of places a check skips something, each with
    its reason. WHY: a skip with no written reason is a hole nobody can see.
  - 9.4.7 rehearsal: the cheapest model reads a ticket cold and tries to build it on
    paper, saying where it got stopped or what is missing.
    - 9.4.7.1 PURPOSE: training data, so graph trees learn to judge "buildable as
      written" without an LLM call.
    - 9.4.7.2 WHY: a simulation costs tokens; it earns them only by teaching a tree.
      It was never meant to catch every shortcoming of every ticket, and
      where it teaches nothing it costs more than the builder simply
      building and recording where it got stuck. So until a learner reads
      the records, a rehearsal is not a BUILDME requirement; the records
      stand as the learner's first corpus.
    - 9.4.7.3 The read is handed the plan steps, the frame (intention, why,
      falsifier), and what exists and what does not, measured before the
      read. "Cold" means no conversation, history, chart or process, not
      blind to the disk.
  - 9.4.8 The chart chain machines (9.3.2): orient, constrain, survey, decompose,
    triage, hypothesize, validate, verdict.
    - 9.4.8.1 The verdict's instrument run is a seal-grade run, so it runs where
      the sealer runs (9.4.2.3.3.1), under bubblewrap. A box without
      bubblewrap (Windows) asks for it and does not run it itself. A
      bwrap-only tooth reads not-run on such a box, never red; its outcome is
      the sealer's. - CC
      - 9.4.8.1.1 Three instrument runs at once share the repo, /tmp, the
        network and git, so a red can come from a neighbour. HYPOTHESIS: a red
        is re-run once, alone, before it is recorded; both readings stand on
        the verdict, and a red that turns green alone is a contention red.
        Its WATCHME brings cc_0 every re-run's pair of readings, so the
        hypothesis is reviewed against them (0.6.1). - CC
  - 9.4.9 skill_block, eventually (16.3).
- 9.5 TOOLS: base, chain, tree, gate, bus_client, system_word, proof_coverage,
  orient, operator_inbox, determinism, edges, import_sieve, ticket_inspector.
- 9.6 VERBS: activate, charter, deposit, drain, feedback, question, sealed (plus get
  and show). Moving a ticket across its workflow is the ticket's own act;
  CodeMother's gates only answer it (3.3.4). Each chart stage (orient through
  validate) and the verdict is a gate machine that answers queueme <fileref>;
  the ticket class queues itself to each in turn (3.3.4.3), so there is no chart
  or verdict verb, and `cross` leaves with the harbor's `clear` (9.4.1.5).
- 9.7 COMMANDS: cairn codemother cast | cross | question | rehearse | tickets |
  whatsnext | seed | show dashboard; the inspectors' own shortcuts
  (determinism, edges, probescan, cleanup, feedbackmap) in her bin/.
