# 3 TICKET (a machine, and the class every kind of ticket inherits from; a first class object)
- 3.1 PURPOSE: A unit of work or attention, written down so it can be followed.
- 3.2 WHY: Work written down can be gated, handed to any builder, and checked
  against what was promised. Tickets, gates and the rest are CC's process moved
  outside CC, so that CC builds what it said it would, deterministically, and so
  that how it works can be seen. And because each ticket carries its own
  workflow, a new kind of work costs only its handlers and its workflow:
  nothing else changes but the order things are built in.
- 3.3 INTENTION:
  - 3.3.1 Ticket is a class, and a machine: every real ticket is one of the kinds in
    3.4, and each kind inherits from it. WHY: a ticket is semi-autonomous; it
    navigates itself across its workflow (3.3.4), and the navigational parts
    belong to the ticket class, which makes it a machine (1.3.2).
  - 3.3.2 The abstract ticket owns what every kind shares: its birth (cast) and its
    three parts, each with one job: the plan (only what a builder builds
    from), the metadata and state (what gates and doors read and write as it
    moves), and the history (the append-only log). WHY: one job per part
    reduces confusion; a builder reads the plan and nothing else.
  - 3.3.3 Never a device. harbor_master (9.4.1) only reports over it.
  - 3.3.4 The ticket IS its own manager. It carries its workflow and status, and
    asks each gate whether it can transit. If refused, it gets itself back to
    design for fixing. If no handler is available to ask, it throws a trouble
    and waits until we decide. Design is CC and Akien until the outline is
    implemented; a design agent comes after that. Until then a refused ticket
    waits in the trouble lane, which both read when a session opens, and
    nothing posts to a design verb that no machine answers.
    - 3.3.4.1 The ticket owns its refusals: a gate refuses a crossing on the
      ticket's behalf. The gates are CodeMother's (9.3.5).
    - 3.3.4.2 The workflow drives it. When a step's work is finished, the ticket
      asks that step's gate. Once the gate passes, its post-gate probes send
      mail over the bus to every device that can do the next step, naming
      the step (BUILDME, PROVEME, ...), and a device comes to claim it. A
      builder never goes looking for what's next: it gets the mail and does
      that. When several compete, the least capable one that thinks it can
      do it claims it, leaving the more capable free for bigger work.
      - 3.3.4.2.1 How a builder declares what it can do is decided when there is
        more than one kind of builder. WHY: with one kind there is nothing
        to choose between.
    - 3.3.4.3 A ticket's code is a tool or machine; its life is data. All of its
      state is on disk, so anyone can instantiate it to talk to it, and any
      dialog is written to the relevant part of the ticket as it happens. To
      cross a gate the ticket asks that gate to queue it, sending only its
      fileref: devices/codemother/0/machines/<inspector>/queueme <fileref>.
      The gate instantiates the ticket from that fileref on its own side. A
      ticket instance then processes the pass or fail: on a pass it goes on
      to the next step, alerting the probes watching the gate (3.3.4.2); on
      a fail it asks design to queue it, the same way. Self-queuing is the
      abstract ticket's (3.3.2), so every kind inherits it and no caller
      queues a ticket on its behalf. WHY: encapsulation. The ticket crosses
      as a fileref and the other side builds its own instance, so nothing is
      shared across the boundary but the address.
  - 3.3.5 Commit often. WHY: so we never wind up with stray files or incomplete
    work.
    - 3.3.5.1 More than one builder works on one box, and there will be more than
      two, so the whole-tree rule (a PROVEME crossing refuses while anything
      in either tree is uncommitted, working_tree_clean) is re-examined for
      N builders on a box. One builder's work must not block another's
      crossing.
  - 3.3.6 More than one builder runs at a time, so work is kept apart by branches:
    each ticket's work on its own branch, named by the ticket id, merged
    locally with git, no pull request (GitHub is hosting only). WHY:
    branches are how many builders scale.
- 3.4 KINDS:
  - 3.4.1 Coding Ticket: what we usually mean.
    - 3.4.1.1 Has its own workflow stamped on it (the state string, with the
      cursor). Each workflow step declares what it needs.
    - 3.4.1.2 Carries its WATCHME spec.
    - 3.4.1.3 Lives in CairnCommons/tickets/ while staged; its trail migrates beside
      its code as that component's history while under way, and back to
      the commons after (Law 5).
  - 3.4.2 Inference Ticket: the record of one call to the inference proxy,
    everything that happened to that request.
    - 3.4.2.1 The call runs the request against our graph trees first. If they
      can't answer, it asks the cloud "what nodes do I need to understand
      this?", integrates them, and runs the query against the trees again
      (the miss path, 4.3.1.9.5).
    - 3.4.2.2 When it asks an upstream LLM, the nest and its sieves sort out the
      lowest cost way to resolve it (eg by the request's domain), and the
      call is made the way the current constraint set says is best.
    - 3.4.2.3 Models can be specified, but shouldn't be most of the time. The graph
      trees can be bypassed, but shouldn't be most of the time.
    - 3.4.2.4 The call returns two pieces: the resolution of the request, and the
      inference ticket.
    - 3.4.2.5 Used for learning, or for debugging when something fails. A logging
      artifact, so transient (4.3.2): disposable after 30 days.
  - 3.4.3 Trouble Ticket: an error that needs a non-automated fixer (CC or Akien).
    - 3.4.3.1 A diagnostic report, EXACTLY like the Trouble Tickets in the Number
      Five Crossbar Telephone Switch. It MUST include EVERYTHING needed to
      diagnose, isolate, and repair the trouble.
    - 3.4.3.2 A second observation of an open trouble NEVER issues a new ticket; it
      increments a counter on the open one.
      - 3.4.3.2.1 A trouble has a point of origin, and that is how they match: when
        raised, its emission source AND error message are checked against
        the open tickets. If found, increment; either way, pass the
        ticket back to the caller.
      - 3.4.3.2.2 The incrementing is part of the trouble ticket class.
      - 3.4.3.2.3 So the error a raiser reports is the same words every time;
        whatever changes from one time to the next (a pid, a timestamp, a
        temp path) goes in the details, not the error.
    - 3.4.3.3 Disposable once closed. File artifacts in the logging tree, cleared
      on the 30 day cycle by the cairn device during sleep (4.3.2.4).
    - 3.4.3.4 A device that errs while servicing another device's request can
      return a pointer to the trouble ticket, and the receiver can add
      details.
    - 3.4.3.5 The test before raising one: can only CC or Akien fix this? If not, it
      is a log line, not a trouble. One problem, one trouble.
    - 3.4.3.6 They show on the operator's to-do list (7.3.6).
    - 3.4.3.7 They live inside the Recovery device (6.3.4), since recovery has to
      work when other things don't.
    - 3.4.3.8 A trouble ticket is a work order. Whoever fixed it reports the fix to
      the originator (the device or machine that raised it), and the
      originator marks it fixed. A trouble that comes back is not designed
      for yet; if recurrent problems appear, we'll explore that.
  - 3.4.4 Task Ticket: work the system needs done that does not change code, eg
    deploying our environment onto a second computer to use its compute.
    - 3.4.4.1 Every ticket has a workflow, even if it is just open/close; that is
      the nature of a ticket. A task ticket gets gates only if we ever see
      one closed without actually being done: that is what gates are for.
  - 3.4.5 Ideas and questions are not tickets. An idea is a note that leads to an
    intention, and stops mattering once the intention is set down. A question
    exists only to deduce the why: once answered, what matters is the answer
    and the why, and nothing else.
