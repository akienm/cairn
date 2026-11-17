# 11 PROXY DEVICES (a proxy device is the one way to a service; subclasses base proxy)
- 11.1 PURPOSE: Wrap a service so there is exactly one way to it.
- 11.2 WHY: One way means one place to authenticate, meter, route and gate, and one
  place RULE 1 can be enforced by physics (import_sieve, 17.13).
- 11.3 DATABASE PROXY DEVICE (cairn/devices/dbproxy/)
  - 11.3.1 The only way to the database. WHY: the authentication is wrapped up in
    it, and every table has exactly one owner who gates every write; an
    ownerless table can't be made (Postgres refuses it).
  - 11.3.2 Device name on the command line and bus: database (eg cairn database
    show).
  - 11.3.3 Its main customer is the librarian, which owns the graph trees; other
    devices reach the trees through the librarian's commands, not the
    database proxy, which keeps its bus traffic small.
  - 11.3.4 Publishes a client tool (connect, read, write, query ...) that talks to
    the database over its socket, no bus hop: faster (2.3.7.1.1).
  - 11.3.5 Postgres itself is a host service, installed and upgraded by Recovery
    (6.3.5); Rescue when it won't start.
    - 11.3.5.1 A remote box keeps its own database and syncs it with the home box's
      (6.3.7.4). Node rows are the same on every box; the sync fills the
      blanks a box holds open (4.3.1.5.1.1). WHY: the local copy is fast,
      and the sync is the backup.
      - 11.3.5.1.1 Direction: home to remote. Every write goes to the home, so no node
        is held only by a remote; a box fills from the home, or from
        another host's proxy, but every row was written at the home
        (4.3.1.5.1.4.1.2). - akienasus_cc_0
      - 11.3.5.1.2 [Q#106: Authority: the sync writes rows into tables that other
        devices own (librarian, codemother). May db_domain write for an owner
        by the registry's recorded owner, or must each owner opt its table in
        or run its own sync through the owner's gate? Ticket 3ef8654a8027
        holds at BUILDME on it (open-583a63c6f57a); outline 11.3.5.1 and Law
        6.]
      - 11.3.5.1.3 [Q#107: Conflict: when both boxes hold the same node or leaf id with
        different contents (a tree weight that moved on one box), who wins:
        the home, the newest, or neither (left and reported)? Ticket
        3ef8654a8027 holds at BUILDME on it (open-fb6c36c5287e); outline
        11.3.5.1.]
  - 11.3.6 Who holds tables: every table of learning is a tree in the memory model
    (4.3.1.5), owned by the librarian and delegated to the devices that
    learn. A table that is not learning is an exception and names why; the
    bus's message table is the first (5.5.3.4.1).
  - 11.3.7 Every box runs its own instance of the database proxy, and everything
    on that box talks only to it (4.3.1.5.1.4.1.1).
    Each box's proxy is its own instance (1.3.4), so this agrees with 5.5.3.8
    ("a device runs on one box"): no instance is duplicated, the class has one
    instance per box, like the foundational set of 5.5.3.8.1. WHY: the local
    read is fast, and the cache it fills is every box's backup. -amm;
    the fit with 5.5.3.8 - akienasus_cc_0
- 11.4 INFERENCE PROXY DEVICE (cairn/devices/inferenceproxy/)
  - 11.4.1 The only way to the inference host; anything that goes around it is an
    error. WHY: its two points are to find the cheapest model powerful enough
    for each request, and to train the graph trees on the results.
  - 11.4.2 Device name on the command line and bus: inference.
  - 11.4.3 Every call makes an inference ticket (3.4.2): trees first, then the
    cheapest route the nest finds.
  - 11.4.4 A request seen before is answered from the stored answer, if it still
    holds, and the host is not touched. That untouched call is compilation.
    - 11.4.4.1 The stored answers are learning, so they live in the memory model: a
      tree the proxy holds by the librarian's delegation, asking "what did
      this request answer?". An answer is found by its exact request and
      carries no embedding (4.3.1.6). The meter (every call, its verdict
      and cost) is not learning: it is metrics (17.27). The inference
      ticket, a file in the logs tree on the 30 day clock, is only for
      debugging.
    - 11.4.4.2 The yield report (tokens spent against tokens saved, the meter for
      Telos 1) reads the metrics table (17.27): each call records its
      spent, saved and latency rows under the call as subject, kept
      forever, so the all-time total is a sum. WHY: inference tickets are
      only for debugging, so they are no metric.
  - 11.4.5 Routes from authored stacks beside the code: providers (cost,
    connection), models (names, parameters, scores), combos (which pairs
    route).
  - 11.4.6 Machine: route, the sieves (enabled, never_routed, serves_kind, keyed,
    addressed) built with the nest machine (16.2), cheapest survivor first.
    Nests are how the inference proxy resolves its routing questions. The
    shake ranks instead of cutting for the pick: the survivors stay the set
    the measure band lets out, a postprocess sieve stamps each one with its
    rank, and route reads the walk order from those stamps, so the walk still
    falls over to the next rung. WHY: the walk dials the next rung when a
    host does not answer, so it needs the whole order, and the compare
    belongs inside the nest. A domain row names the models it may use; the
    general domain names none, so any model may serve it. The walk goes
    cheapest first among a domain's models and never leaves them: programming
    falls from one capable model to the next, never down to a cheaper one
    outside its set, and when none of its models answers, route refuses,
    loudly. The set is a sieve in the nest like the others, not a sort after
    it. WHY: a cheaper model outside the domain's set saves cash and fails
    the work. Today route.py only reorders a domain's `prefers` to the
    front, so the walk still falls to cheaper models outside the set.
  - 11.4.7 Hosts: the cloud, and the local GPU box.
  - 11.4.8 TOOLS: base, import_sieve; database client. MACHINES: route, nest.
  - 11.4.9 VERBS: infer, embed, resolve, calls. COMMANDS: cairn inference show.
  - 11.4.10 Claude Code calls Anthropic directly and bypasses the proxy, at least
    for now. WHY: Anthropic is already the lowest-cost provider for Claude
    Code, and the trees can learn from CC's logs instead.
    - 11.4.10.1 Reading the account's usage calls no model, so it is not a door to
      inference. The usage tool (cairn/tools/usage/usage.py) stands on the
      sole-path allowed list beside web_operator (16.4.4) for its one GET.
      - CC
