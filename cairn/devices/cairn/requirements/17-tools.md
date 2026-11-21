# 17 TOOLS (cairn/tools/: the general collection; tools have users, not owners)
- 17.1 base
  - 17.1.1 PURPOSE: What every device is built on.
  - 17.1.2 WHY: the base-most things (the six truths, logging, diagnostics, the core
    patterns) must be the same everywhere, so they are written once and
    inherited.
  - 17.1.3 INTENTION:
    - 17.1.3.1 The six truths (CP1-CP6) everything else is predicated on.
    - 17.1.3.2 Logging and diagnostics, including diagnostic_inspector: the smart
      reader of the dumb breadcrumbs base's logging leaves; complete
      diagnosis on the first pass.
      - 17.1.3.2.1 The first miss of a datum is a learning signal, folded into
        the report; the same gap recurring is the defect.
    - 17.1.3.3 The core patterns.
    - 17.1.3.4 A tool, not a machine, even though it spans several files; the
      base-most stuff belongs to Cairn.
    - 17.1.3.5 The base classes all inherit from base, and so bring its logging,
      diagnostics and core patterns with them:
      - 17.1.3.5.1 base device: the base class for every internal device.
      - 17.1.3.5.2 base shim: the base class for every shim, customized for the
        device it interfaces with, internal or external. Carries the
        panes every device has (2.3.8), the scheduler (5.9), and the
        [all] verbs (2.4.11.2).
      - 17.1.3.5.3 base proxy: the base class for every proxy device (11).
- 17.2 artifact: the one door a record of truth changes through, and the journal of
  who came through it (hash-chained, caller read from the kernel). WHY: errors
  are permanent in records of truth (Law 7), and the journal is what shows a
  record moved by hand. USERS: everyone who writes a record.
  - 17.2.1 The one writer question is LLM or code, and only for gate-pass
    certificates; who authored a write is not tracked otherwise. So on
    Windows the caller class comes from the process chain: claude.exe
    above the writer means cc; otherwise it is not cc. Env vars are a
    fallback only. Certificates are made where the sealer runs
    (9.4.2.3.3.1), so Windows does not need a gate class of its own. - CC
  - 17.2.2 CC over ssh is told from Akien by the key sshd accepted: CC on each
    box gets a dedicated ssh key. Until it lands, approve and the operator
    close refuse any sshd-session caller, Akien's included (Q#115). -amm
    - 17.2.2.1 It grows into a claude_code user per box: Cairn runs as akien,
      and superclaude launches the claude executable as claude_code. Over
      ssh, CC logs in as claude_code where it can and launches claude there.
      WHY: the user id is the kernel's word for who wrote what, not an
      asserted variable. -amm
    - 17.2.2.2 claude_code is an admin, elevating on request rather than
      standing elevated, and CC may talk to other CCs over the inter-CC
      messaging and use ssh to set up and fix boxes like an IT admin. WHY:
      Akien uses CC for IT work on his boxes, and two CCs together can fix
      what one box alone cannot see. -amm
- 17.3 bus_client: gets a process onto the bus (reach a device, or connect). Its
  connect is a wake attempt (5.3.5.1). USERS: every process that speaks.
- 17.4 cgroup: reads which cgroup a process lives in. WHY: 10.3.2. USERS: CC,
  artifact.
- 17.5 chain: the grammar every chart stage speaks. WHY: one grammar lets stages
  chain in any order. USERS: CodeMother (heaviest), base, tester, rehearsal,
  build_inspector, proof_coverage, aider, skills/chart.
- 17.6 charter: compiles a component's bounded state from its history. WHY: state
  is compiled from the component's tickets, never hand-edited (Law 5). Held by
  CodeMother.
- 17.7 data_recorder: a mailbox for feedback records until an inspection reads them;
  called a mailbox because for many recorders the data arrives over the bus.
  The records are JSON files under the holder that assembled it
  (~/.cairn/devices/<holder>/<n>/tools/data_recorder/), not a tree: the
  plainest thing that works. [why?]
- 17.8 determinism: for each component, where is the LLM? Deterministic, mostly
  deterministic, or not. WHY: what is deterministic can be moved out of
  inference (10.3.10). USERS: CodeMother.
- 17.9 edges: the frontier view: every charter's admitted gaps plus the open
  questions. [why?] USERS: CodeMother.
- 17.10 feedback: where a component's failing findings go (the -2-> edge). WHY: a
  finding that goes nowhere teaches nothing. USERS: the inspectors.
  - 17.10.1 No rule refuses a route spelled as a keyword where a finding is
    built: the old charter clause asking for one measured the wrong thing, and
    is retired (Q#116). -amm
- 17.11 gate: the == compare, in one place. A gate opens when every expected equals
  its actual. No oracle, ever.
  - 17.11.1 WHY: the inspector does all the checks, so there is no need for more
    checks anywhere else. The inspector's output is consumed by the gate.
    The gate's output is the certificate. (Akien: the design as meant
    from the start.)
  - 17.11.2 The certificate is one file type you can't write. It carries a
    cryptographic (or similar) way to say that the right code wrote it, on
    this date, at this time, with these hashed findings. That signing
    belongs in the base gate class, so every gate has it.
  - 17.11.3 Entry gates exist only to kick back what doesn't meet the entry
    requirements. Nothing in them is about who writes what.
  - 17.11.4 The crossing is the ticket's own act. The gate's probe (the same kind
    that sends notice of gate passage) tells the passing ticket "you can
    now advance to X", and the ticket updates itself.
  - 17.11.5 What a gate asks is "does this meet the intentions", never who did it.
    Every intention carries a why, and so does every test case whose
    purpose is not plain. A change that makes a ticket or a test case meet
    the intentions better is good, and downstream supports it when the whys
    show it isn't a fast one. Measuring who did what serves none of that.
  - 17.11.6 The inspectors are not assumed correct; they are examined when they
    refuse. After a gate refuses, an LLM sets the refusing sieve's intention
    and why beside the ticket's intention and why and asks: is this sieve
    the best we can do right now? If yes, the ticket changes. If no, the
    sieve is fixed through its own ticket and proof. Either way the system
    improves. WHY: a disagreement becomes an update to an intention or its
    implementation, never a conversation about procedure. The sieves stay
    deterministic and never weigh a why; the LLM check comes only after a
    failure, and it is never a lock pick because it has no third outcome.
    Nothing passes a ticket over a red.
    - 17.11.6.1 Every sieve carries its own why, and the why names where it came
      from. Akien designed the inspector tools; CC built each specific sieve
      from what it read him to mean. So the adjudication in 17.11.6 is against
      the sieve's own why, done by CC, and never a question to him. The sieves
      are not perfect and nothing here will be: the whole is always under
      improvement, and each sieve's why is what lets it be judged. Today
      build_inspector registers 43 sieves, and the 36 sieves/*.json
      records carry name, band and dials but no why. The whys live only in
      docstrings.
    - 17.11.6.2 The same boundary runs wherever Akien designed a tool or machine and
      CC filled in its specific contents: the nest and its questions, the
      inspectors and their sieves, the gates and their checks, the corrosion
      set, the skill doors and their field lists. Each such component's
      charter carries a design_boundary naming what Akien designed, what CC
      designed, and how a red over CC's part is settled. CC's part is CC's to
      adjudicate against its own why. Akien may be asked whether a part could
      be better, with the whys laid out, and whatever CC can't sort goes to
      him. A new component that has this boundary declares it in its charter
      when it is born.
  - 17.11.7 A sieve's rule follows the ticket's kind, read off the ticket, so it
    stays deterministic; 17.11.6 is left for what the rules do not cover.
    - 17.11.7.1 New or changed code (code-seam): at BUILDME the named proof exists
      and its PROVES names the ticket, and it may be red, since a new
      proof is red before its build. At PROVED it is sealed green and
      hollow-measured.
    - 17.11.7.2 Fixit (bug): at BUILDME the ticket names the red it fixes (the
      proof), and that proof really is red on disk now. The fix may change
      the test case itself without a ruling: the proof's why names the
      ticket and says what it tests and why it changed, and names any
      tooth it removed. At PROVED it is sealed green and hollow-measured.
    - 17.11.7.3 A ticket cannot call itself a fixit to get the fixit rule: it needs
      a real red on disk, which code checks.
- 17.12 intentions_model_compiler: copies every intention into
  intentions-congruency-lab/. WHY: so that one folder can regrow the system on
  a bare machine. USERS: Cairn (cairn compile).
- 17.13 import_sieve: one parse of every .py into an import graph; what reaches what.
  WHY: enforces "only the proxy reaches the host/database" and RULE 1 by
  physics. USERS: CodeMother, the inference proxy.
  - 17.13.1 The RULE 1 check is a path check: code inside device bar may not import
    cairn.devices.foo (anything not under cairn.devices.bar), except a tool
    foo publishes (cairn.devices.foo.tools.<x>, its charter saying
    published_by_device). Inside one device there is one owner, so nothing
    is checked there. A charter's public_interface describes what the
    component offers (modules, functions, bus verbs, commands); the check
    does not read it. WHY: a path check is the simplest thing the code can
    test.
    - 17.13.1.1 A ticket is owned only by its intention. A change that makes
      serious, custom edits to many components is split, one ticket per
      component; a blanket replace that happens to touch many is one ticket
      under a spanning intention, because it breaks for all of them or for
      none, and that is a HYPOTHESIS its proofs test (Q#103). -amm
- 17.14 operator_inbox: builds the operator's to-do list from live state, storing
  nothing (7.3.7). USERS: Operator.
- 17.15 orient: the measuring scans before a build (where is X called, what's in
  each component). WHY: a build starts from what is, measured, not recalled.
  USERS: CodeMother's orient machine.
  - 17.15.1 One verb, qualified by its target: build (the scans), session (the
    slate), debug (diagnostic_inspector).
- 17.16 proof_coverage: joins a ticket's falsifier clauses to the proofs that cover
  them and the seals that ran green. WHY: a falsifier nobody proves is a
  hypothesis (Law 3). USERS: the tester.
- 17.17 proof_discovery: resolves `cairn test` targets to proof files. USERS: the
  tester.
- 17.18 public_feed
  - 17.18.1 PURPOSE: Draws a feed panel for any device, or any machine with a panel
    (2.3.8.5). By default it filters for the device it's in; from the bus's
    sub-panel on the Cairn device's page it lists everybody.
  - 17.18.2 WHY: Debugging: did the message go by when the command was typed? One
    tool, so every device's feed looks and filters the same way.
  - 17.18.3 INTENTION: three channels, public feed (bus messages), console (INFO),
    debug (that device's debug messages). The panel keeps its own
    short-lived buffer (about the last 5 minutes), however we want to do
    it. Filtering is always available: by channel, device, sender,
    addressee or verb.
  - 17.18.4 USERS: every device's feed pane; machines with a panel, through their
    host device; the bus's sub-panel on the Cairn device.
- 17.19 question: the open-question door: a decision only the operator can make,
  bound to its ticket, answered in the operator's words. WHY: a spec choice
  is settled by Akien's head, recorded verbatim, never by a paragraph of
  CC's. USERS: tickets and CodeMother open them; the operator answers
  (7.4.2).
- 17.20 rack: reads the declared instances, the device folders (5.7.3.4). USERS:
  the rack machine, pulse.py, the scheduler.
- 17.21 scratch: a proof's throwaway temp dirs and worktrees, cleaned up by the
  door. WHY: a run must leave nothing behind (4.3.1.7). USERS: the tester.
- 17.22 system_word: case-folding for system words (device names, verbs, statuses).
  WHY: anything you type is case-insensitive. USERS: everyone that parses a
  command.
- 17.23 ticket_inspector: completeness checks over tickets at rest. [why?] USERS:
  CodeMother.
- 17.24 tree: the nexus graph-tree face (deposit, counsel, propose) over the
  librarian's trees. The same tool everywhere. It stays a tool and does not
  fold into the librarian's verbs: a learning block holding its trees by the
  librarian's delegation works them through it, and one that needs a special
  adaptation gets a subclass. USERS: every delegate (4.3.1.4).
- 17.25 validation_store: reads and writes seals. USERS: the tester.
- 17.26 Where a tool lives: the general collection, cairn/tools/, is the default. A
  tool goes with its holder (cairn/devices/<d>/tools/) only when nothing else
  could ever use it (a tool for a part only that one device has). If there is any chance somebody else might want it,
  it goes in the general collection.
  - 17.26.1 A client tool a device publishes (2.3.7.1) is not the general case: it
    is the device's own interface, made for other components to use, so it
    lives with its device (cairn/devices/<d>/tools/<t>/, published_by_device).
    Scratch bus, the database client, the trouble store, the librarian's trees
    and the system device's host tool all live there. CC's decision, from
    2.3.7.1 and Akien's "hostname should come from the system device"
    (2026-11-21). - akiendelllinux_cc_0
- 17.27 metric: records a measurement of anything. WHY: a metric is a primitive;
  its job is to measure whatever it is, and like feedback (which a metric
  strictly is) it must eventually have a consumer. USERS: any probe or tool.
  - 17.27.1 A metric is recorded into its holder's data recorder (17.7): no bus, no
    database. A probe that records and does not send is recording metrics.
  - 17.27.2 Metrics land in one table so any metric can be reported fast from one
    place: at, name, source (the device/tool that recorded it), start,
    end, value, unit, subject (the thing measured), info (json). Fields
    not relevant to a source stay blank. Indexed on name and source by
    time. One thing (eg an inference call) may record several metrics in
    its short life, sharing one subject.
  - 17.27.3 The table picks up what waits in the recorders when a consumer asks
    for a report, then answers (the read is the event; nothing polls).
  - 17.27.4 Each metric name is declared, with its consumer, in the charter of
    the component that records it. A name with no consumer is a red.
  - 17.27.5 Rows are kept forever: they are small, and the table is the history.
- 17.28 dataref: one address for any stored record, in any format, and the thin
  class that reads it. WHY: a config, a ticket or a node can say
  WHERE a value lives without carrying it, so the repo stays shareable and a
  private value stays in ~/.cairn; and one way of pointing works across every
  format and every box. USERS: anything that reads stored data.
  - 17.28.1 The scheme names the root; the path finds the record; the part after #
    finds the item inside it. Each root is found on the box it runs on, so
    one address works on Linux, on Windows and on a fresh machine.
    - 17.28.1.1 cairn:/// is the repo (from the environment, or from where bin/cairn
      itself lives); cairncommons:/// is the commons repo beside it;
      instance:/// is ~/.cairn; claude:/// is ~/.claude (the project's
      own .claude/ is already cairn:///.claude/, so it gets no second
      name); db:///cairn/table/row is the database; file:/// keeps its
      usual meaning, a real path on the filesystem, for what no root
      holds. claude: is also the Claude app's link scheme on this box:
      the resolver never hands an address to the system, so only a click
      on one opens the app.
    - 17.28.1.2 A host names that box's copy: cairn://akiendell/devices/... is the
      Windows box's repo, read over the bus. A node id means the same node
      on every box (4.3.1.5.1), so a db address names a host only to mean
      that box's copy.
    - 17.28.1.3 After #, names separated by /: #key (an env file), #section/key (an
      ini file), #a/b/c (into json).
    - 17.28.1.4 secret: wraps any whole address and hands back what it points at as
      a Secret: secret:instance:///devices/cc/0/.env#githubtoken,
      secret:db:///cairn/t/row#token. Take off "secret:" and what is left
      is a complete address, whose # is its own. One colon, no //: a //
      says a host comes next, so secret://file://... would read "file" as
      a host. Precedent: jar:file:, view-source:https:.
  - 17.28.2 Dataref is the base class. Secret is its subclass: its str, repr and
    format are all **********, so a log line or an f-string cannot show it;
    .secret fetches the value at that moment. WHY: printing it by mistake
    shows stars, and every place a secret is unmasked is a .secret anyone
    can grep for. Prior art: pydantic's SecretStr, and
    fsspec for one interface over many stores (cited, not grafted).
  - 17.28.3 A Dataref reads; it never writes. A write goes through the owner's gate
    (Law 6), and a db: address is read through db_domain's own client,
    never a second dial to 5432. An address on another box is read over
    the bus. WHY: one address system must not become one back door.
  - 17.28.4 A file Dataref keeps its value and re-reads only when the file's
    modification time, size or inode has changed (a stat reads no data;
    a write that replaces the file in one step gets a new inode, which
    catches a change where timestamps are coarse). A Secret keeps nothing
    between reads. A db Dataref does not cache until a measured need asks
    for it. HYPOTHESIS: it will be read often enough for the cache to pay;
    the reads are counted (a metric, 17.27) to find out.
  - 17.28.5 One that does not resolve is loud and names its address, never a value.
    A sieve reds a class-space config holding a plain value where a secret
    belongs.
    - 17.28.5.1 A secret is marked when the need for it is created, not by a list or
      a key's name: the day a secret comes into being, its value goes into
      its holder's env file and the code names its key there, and from
      that day every use of it is a secret: address, so the factory hands
      back a Secret (17.28.2). The place a secret belongs is wherever such
      a key is used; a plain value there is the red. WHY: the need for a
      secret is what makes it one, as with CC's own email address: the day
      it was made, its values went in CC's env file and its keys into the
      code.
