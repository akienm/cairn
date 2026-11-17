# 4 GRAPH TREES MEMORY SERVICE (not a device, but a first class object)
- 4.1 PURPOSE: Where Cairn keeps what it knows, and what it holds for a little
  while.
- 4.2 WHY: So everything the system learns is one connected body the librarian can
  see whole, and patterns can be exported from all of it. And so no device
  invents its own way of storing things: there are two ways, and every device
  uses them.
- 4.3 INTENTION:
  - 4.3.1 Knowledge: one list of nodes, owned by the librarian.
    - 4.3.1.1 Other devices keep no node tables of their own. They put what they
      learn into the librarian's nodes through the librarian's verbs on the
      bus, and each depositor gets its own index over the shared nodes,
      because each asked different questions first while assimilating.
    - 4.3.1.2 The librarian sees what every other part learned, because it is all
      in its own store, so it can surface what others would find useful.
    - 4.3.1.3 Nodes are kept. The librarian can hand out the next free node.
    - 4.3.1.4 Ownership. The librarian owns every tree and delegates some to the
      devices that learn. EVERYTHING THAT LEARNS USING OUR GRAPH TREES IS A
      DELEGATE (CodeMother, chart and any learning block are examples, not
      a list), and each holds its trees by the librarian's delegation (Law
      6: delegation through the owner's gate). WHY: two holders with
      different weights over the same nodes have different perspectives
      and can debate points, and the librarian, asked anything, can look
      at the query from both.
      - 4.3.1.4.1 Delegation nests down the rungs: the librarian delegates a set of
        trees to a device, the device to its machines, a machine to its
        tools if one is ever that complex. Each stays co-owned by the one
        above. CodeMother's learning goes in her own tables, and she owns
        the learning blocks of her machines and tools.
      - 4.3.1.4.2 CC is not a delegate: no part of CC learns using our graph trees.
        One could appear later (eg in CC's shim); the librarian would own
        it and delegate to CC. Instead CC's process is being externalized
        (3.2).
    - 4.3.1.5 The memory model. Everything Cairn keeps as LEARNING in database
      memory is these five things, and only these. Logs, troubles, git
      records and a device's own state keep their own homes (4.3.2-4.3.4).
      WHY: one kind of access everywhere.
      - 4.3.1.5.1 Nodes: one long list, id = row. Every tree indexes it; no tree
        owns a node, so several trees can index the same node in
        different ways.
        - 4.3.1.5.1.1 A row number is the same on every box. Storing a memory
          first reserves its slot from the librarian on the home box
          (CAIRN_HOME_HOST, 6.3.7.4), so two boxes are never handed the
          same slot, and the slot stays reserved until the write is
          complete. If a box's list is shorter than the slot
          (eg it holds rows up to 100 and is handed 123 while a sync is
          bringing the rest), it adds the open slots in between as
          blanks, and the sync fills them in as it proceeds. WHY: node
          ids are in every link and blob pointer, so a row has to mean
          the same node everywhere.
        - 4.3.1.5.1.2 A node id is its master row number and never anything else.
          WHY: any other lookup needs a search, and a row id is direct;
          a search is far too slow on the target hardware. A node can be
          voided and its row reused; a node is never searched for.
          - 4.3.1.5.1.2.1 Fetch by id is never a search; it always goes directly
            there. WHY: the target hardware is a 10th-gen i7 with 16
            GB RAM and no GPU, and only a direct fetch keeps it from
            bogging down. The lived symptom: in the Igors, reading one
            word into a 3M-entry word graph took more than 1 second,
            and the laptop crawled. The row-id model comes from dBase
            II record numbers, the first database he used.
        - 4.3.1.5.1.3 A node is in one of three states: VOID (deleted, its row
          available), NOTCACHED, or its data, which follows the node schema.
          Data that does not follow the schema is a bug.
        - 4.3.1.5.1.4 The sync is the backup, and a local database is a cache of the
          master. A local call for a node or tree the box does not hold is
          fed from the master and populates the local copy. If the box holds 12 rows and is asked for row 123, the rows between are added as
          NOTCACHED.
          - 4.3.1.5.1.4.1 Every box holds a full copy of the database. WHY: no
            single box's loss loses the memory; this is why every box,
            yoga included, runs Postgres. -amm
            - 4.3.1.5.1.4.1.1 The full copy is a byproduct of the cache, not a
              separate backup. Every box runs its own database proxy
              (11.3.7), and a device, machine or tool only ever talks to its
              local one. A read is answered locally when the row is local
              and current; otherwise the local proxy gets it from another
              host's proxy, returns it, and caches it locally in the
              background. Sleep cycles also sync the databases across hosts,
              so NOTCACHED is a transient state and every box slowly builds a
              full copy. WHY: the cache already makes every copy, so there
              is no separate backup to make, and the same caching keeps
              every read as fast as possible. -amm
            - 4.3.1.5.1.4.1.2 A write goes through the local proxy to the home's
              proxy; the home writes it and stamps its seq, and the other
              boxes get it by the read fill and the sleep-cycle sync. The
              home is the one writer (4.3.1.5.1.6.9: slots come from the
              home). WHY: one writer means no box holds a row the home lacks,
              so the copies never conflict. - akiendelllinux_orchestrator
              -amm
        - 4.3.1.5.1.5 Proofs run against a TESTING database, separate from live.
          - 4.3.1.5.1.5.1 A proof MAY read the live database; what a test writes
            stays out of live, either in the TESTING database or
            marked as a testing artifact that the rest of the system
            ignores. WHY: reading live saves populating test data;
            ignoring testing artifacts keeps them from leaking into
            what the system believes. Test against live, marked as
            testing. -amm
          - 4.3.1.5.1.5.2 How the TESTING database works. (1) The db proxy is
            the seam (4.3.1.5.1.4.1.1, 11.3.7): proofs, devices and tools
            never choose a database; the proxy chooses by session context.
            (2) The test runner sets the context, never the proof:
            bin/cairn test and the hollow run open every db session with
            context=testing, so a proof can neither forget it nor pick
            live (Law 4). (3) In testing context, writes go only to the
            TESTING database: same schema, rows from a reserved address
            range, so a testing address never collides with a live one.
            (4) In testing context, reads are an overlay: testing rows
            first, live underneath, live pinned at the seq the run started
            at. A proof reads live with no fixtures, what it wrote
            shadows live for that run only, and the run repeats within
            itself. (5) In live context the proxy never consults the
            TESTING database, so testing artifacts are invisible to all
            but the run that made them, by construction rather than by
            filtering. (6) Each run's testing rows carry its run id and
            are dropped at run end; the sleep cycle sweeps orphans. (7) A
            proof over live data asserts invariants, never snapshots; a
            tooth that needs an exact value writes its fixture into the
            overlay first. Until the per-box proxy exists, the same
            routing sits in the store door (db_domain) and moves into the
            proxy when it is built. WHY: a context the proof sets is a
            context a proof can forget; the runner is the one place every
            proof passes through. - akiendelllinux_orchestrator -amm
        - 4.3.1.5.1.6 The node schema, with a flexible metadata field. WHY: nodes have to be
          really fast, and row ids are fastest; a payload can be anything,
          so a node points into blobs and lists.
          - 4.3.1.5.1.6.1 ADDRESS: every reference is one 64-bit integer, the top 16
            bits a table tag and the low 48 a row. A list of addresses can
            name nodes, blobs, leaves in any tree, lists and links. Every
            pointer is a direct row fetch, and a new kind of thing is a
            new tag, not a schema change.
          - 4.3.1.5.1.6.2 nodes (the one long list): row, gen, state
            (VOID|NOTCACHED|DATA), kind (the payload type), payload
            (inline when small), blob (an address, when large), meta
            (flexible json), out (a list address), in (a list address),
            seq (a change counter for the sync).
          - 4.3.1.5.1.6.3 lists: row, gen, state, owner, items (bigint[] of addresses),
            and optional weights (real[], parallel). A long list chains to
            a next chunk.
          - 4.3.1.5.1.6.4 links: row, gen, a, b, weight, traversals. One row per link;
            both endpoints' lists hold its address, so a link is
            bidirectional and its weight has one home.
          - 4.3.1.5.1.6.5 blobs: row, gen, state, kind (json|csv|text|bytes|vector...),
            bytes. Several blobs are a list of blob addresses.
          - 4.3.1.5.1.6.6 trees: leaf tables keep their shape and weights. A leaf points
            at a node address, and the node's in list holds the leaf's
            address back. So each leaf table gains an additive row bigint
            column and keeps leaf_id, and its table tag is assigned at its
            birth from a tag registry the home librarian holds (0x0100
            upward, synced like nodes); tags.json pins only the core four.
            - CC
          - 4.3.1.5.1.6.7 gen: a reference carries (row, gen). After a VOID row is
            reused, a mismatch reads loud as gone, never as wrong data.
          - 4.3.1.5.1.6.8 void: walk the node's in list, remove it from each source's
            out list, mark it VOID. No search.
          - 4.3.1.5.1.6.9 Slots are reserved from the home librarian in blocks (eg
            1,000), not per row; reserved rows not yet used sit VOID.
          - 4.3.1.5.1.6.10 sync: read-through fill (gap rows NOTCACHED), and the master
            sends the rows whose seq is past what the remote last saw.
            Row by row, no hashes.
          - 4.3.1.5.1.6.11 confidence: the first key in meta, 0 to 1. Measured results
            are high; things read on the internet are lower, by source.
            It is treated like a why when adjudicating conflicting
            information. Little used now, used later.
            - 4.3.1.5.1.6.11.1 [Q#121: Ticket 26acbf5314a5 migrates nodes with no
              confidence key in meta (a legacy value stays inside meta.provenance), so a
              migrated node reads unscored. This line puts confidence first in meta. Does
              the migration write it, or leave it absent?]
          - 4.3.1.5.1.6.12 The TESTING database (4.3.1.5.1.5) has the same schema in a
            separate database.
          - 4.3.1.5.1.6.13 An embedding is attached to a node per (node, question):
            its vector is in a blob, and it carries the question
            node's address. Any memory node can carry one; the
            embeddings generator device makes it by running the
            question and the data through the graph tree.
          - 4.3.1.5.1.6.14 Similarity is searched only inside a tree's own index,
            which hands back node addresses, and it may be
            consolidated out during sleep, as in human cognition. No
            search ever resolves an id (4.3.1.5.1.2.1).
          - 4.3.1.5.1.6.15 Cross-domain embedding search is one named search mode: a
            search for 'patterns about moving energy' returns
            electrical and microwave systems and also how biology
            does it. WHY: it mimics the cross-domain searches Akien's
            brain does.
        - 4.3.1.5.1.7 Dedup stays: the storer saves only what it finds is not
          already held. 'Is it already held?' is asked of a tree, a
          keyed content index found by its key (4.3.1.6), never a node
          search.
      - 4.3.1.5.2 Trees as tables, permanent: each asks one question, with the
        weights in its leaves. A tree past 5K leaves is calved at its
        dominant attractors, a deterministic code shear.
      - 4.3.1.5.3 Trees as tables, temporary: made for one activity and dropped
        after it. Two kinds so far: a working tree that sleep builds while
        consolidating and does not need afterwards, and config read from
        disk and held in the db. For config the file on disk stays the
        source: the tree is derived from it, rebuilt when the file
        changes, never edited in place.
      - 4.3.1.5.4 Bidirectional links, in lists of their own, id = row. A link that
        carries a tree's weights lives in that tree's own link list,
        because the weights belong to the tree's question. A link that is
        a fact about two nodes (derived from, part of, contradicts) lives
        in one shared list, readable from either end.
      - 4.3.1.5.5 Blobs: the storage layer stores bytes in blob rows (4.3.1.5.1.6.5)
        and nothing more. What gets stored is the storing part's decision,
        not the storage's. For things read, it stores a locator, where and
        how to find it again (author, title, local paths and the like),
        never every word read. WHY: importing all of it would be wasteful,
        and a path alone loses the content when the file moves.
    - 4.3.1.6 Embeddings. Not every node gets one. WHY: embedding every single
      thing would make an impossible mound of data, and that is not how
      Akien works, and this is meant to work the way he does. What gets
      embedded is the pattern: the answers to a few key questions that
      cross domains (4.3.1.8). A node without an embedding is found by its
      key (eg an exact request).
    - 4.3.1.7 Lifetimes. Each tree declares its lifetime when it is made: kept, one
      activity (eg one sleep run), or until its source file changes.
      Dropping a tree drops its leaves and its own links. A node goes only
      when no tree indexes it, so whatever a temporary tree's activity
      promoted into a permanent tree outlives it. The drop is enforced,
      not a habit. WHY: a run that ends without dropping its tables leaves
      them behind forever.
    - 4.3.1.8 Cross-domain questions (cognition questions): inherently cross
      domain, not domain specific. "How might that work?" is Akien's
      number one: it applies in almost every domain, and captures the
      pattern rather than the domain's answer. They are not design
      questions: a design question is a spec choice waiting on Akien
      (cairn question, CairnCommons/questions/).
      - 4.3.1.8.1 A question is a node in the one list. Two devices can have the
        same question: both hold the same node. Owning a question =
        holding a tree for it, with that device's own weights, as the
        librarian's delegate (4.3.1.4).
      - 4.3.1.8.2 The answers to cross-domain questions are what get embedded: an
        answer from any domain lands in that question's tree as a
        pattern, so a later search under the same question finds
        patterns from other domains, which often starts a cross-domain
        search.
      - 4.3.1.8.3 The corpus is a git JSON file beside the librarian's code
        (shareable spec, 4.3.4); the question trees are derived from it.
        Every entry carries its origin: verbatim (Akien's words, with
        date and source) or proposed (by CC, by Gemini, ...). All
        questions are included; the origin keeps his words apart. He
        expects a couple of hundred of his own.
      - 4.3.1.8.4 Questions that fire in sequence are linked "followed by" in the
        shared link list, so a walk can run a sequence. Two known:
        mechanism, need, fit, get inside, experiment; and best pattern,
        gaps, trim to fit, how might that work.
      - 4.3.1.8.5 Harvest: a deterministic pass over Akien's logs and notes
        proposes question-shaped lines in his words; he confirms each
        before it is marked verbatim. New ones are added through a
        librarian command as he says them.
    - 4.3.1.9 The walk: a first HYPOTHESIS (0.4.4). CC's draft, written so the
      experiments (4.3.1.10) have something to be wrong about; it is
      replaced by what they show. WHY: Akien sets what the trees are for
      and judges what they do; the mechanism is the teammate's draft, the
      way the geogebra model was for the 3d scanner, and it is learned here
      by running it, not by specifying it first.
      - 4.3.1.9.1 What a tree holds. A tree is one question. Its nodes are that
        question's answers in pattern words, not domain words: for "how
        might that work?" the nodes are mechanisms (buffer, gate, feedback
        loop, threshold, queue, lookup, broadcast ...), coarse at the top
        and finer beneath (gate -> latch, filter, valve). The vocabulary
        is grown by the miss path (4.3.1.9.5), never authored by hand.
      - 4.3.1.9.2 What a leaf weight is. Each node, in the tree's own leaf table,
        remembers the words that have led to it, with counts: "buffer"
        carries tank and cistern from plumbing, capacitor from
        electronics, inbox from mail, each with how often. This is where
        cross-domain comes from: the words of every field pile up on the
        same pattern node, so a new plumbing sentence reaches "buffer" by
        plumbing words and finds the electronics and the mail already
        there.
      - 4.3.1.9.3 The walk. The string is cut into words deterministically (stems,
        no LLM). Start at the top; at each node score each child by how
        much of the string's words it has seen before, weighted by the
        counts; step to the best child; stop at a leaf, or when no child
        scores above the floor (a setting, measured). The result is the
        path taken, with each step's score.
      - 4.3.1.9.4 The embedding. The path written as one string of node ids with the
        score bucketed at each step, eg /gate:7/latch:4/. A string so that
        LIKE is the search (14.3.2): a shared prefix is "the same family of
        mechanism", a shared substring is "shares a sub-pattern". Two
        things from two domains that walked the same path have the same
        embedding; that is what structural similarity means here.
      - 4.3.1.9.5 The miss. A walk that cannot leave the top, or scores under the
        floor everywhere, cannot answer. Then, and only then, the LLM is
        asked, given the question, the string, and the tree's vocabulary at
        the node where it stopped: which of these answer it, or what new
        node belongs under this one? It returns names, existing or new, and
        nothing else, so the integration is plain code: a new node goes in
        the one list and under its parent; the string's words are added to
        the named nodes' counts. Then the walk runs again and lands. That
        is the learning: the next string like it needs no LLM.
      - 4.3.1.9.6 Deposit. A hit reinforces: the string's words are added to the
        counts along the path it took. With `for <device>/<question>`
        (8.4.4) the same happens in that device's tree, so two holders of
        one question drift apart in weights by what each has seen.
      - 4.3.1.9.7 Sleep (consolidation). Merge sibling nodes whose word sets mostly
        overlap; let counts that have not moved in a long time fade; past
        5K leaves, calve at the nodes carrying the most count (the
        dominant attractors), each becoming the root of its own tree,
        linked to its parent (4.3.1.5.2).
      - 4.3.1.9.8 Which trees, when nobody says `for`. The depositor's own question
        trees first. The librarian's default is a sequence from 4.3.1.8.4
        starting at "how might that work?", going on to the next question
        only while the one before it landed. So a thing gets a handful of
        embeddings, never one per question (4.3.1.6). This is the
        attention problem, and the likeliest of these to be wrong.
    - 4.3.1.10 The bench. The trees are learned by watching them run, so the first
      thing built on them is a way to see them: a graph-trees pane on the
      librarian's page (15) that draws a tree, takes a string and a
      question, lights the path with its scores, shows the embedding and
      the miss when there is one, and walks two strings from two domains
      side by side to see whether they land together; and the same from
      the command line, `cairn librarian walk "<string>" for <question>`
      (8.4.5). Every number in 4.3.1.9 (the floor, the buckets, the merge
      rule) is a setting, so an experiment is changing one and walking
      again. WHY: the trees are understood by running experiments and
      seeing what happens. Nothing in 4.3.1.9 is known
      until this has measured it (Law 3).
  - 4.3.2 Transient: things held for seconds to days (mail, logs, test runs,
    trouble tickets, inference tickets). The logging tree.
    - 4.3.2.1 What Cairn stores in the database is a tree, with few exceptions
      (4.3.1.5). Transient trees are the mechanism for a transient need
      that wants one: like a temp folder, there are many, each made when it
      is needed and tossed when it is done. Nothing transient MUST be in a
      tree.
    - 4.3.2.2 Each kind of thing declares its lifetime, and it ages out on that
      clock.
    - 4.3.2.3 Cairn owns all of ~/.cairn/ and delegates each ~/.cairn/devices/
      subtree to its device. Everything outside devices/ (~/.cairn/logging/
      and the rest) is Cairn's, so every log is Cairn's and Cairn cleans
      them up in sleep. Transient things are files there; trouble tickets
      are logging items.
    - 4.3.2.4 Transient things may help debugging out to 30 days and won't be
      needed past that, eg an inference ticket looked at a week later
      because a bug turned up. No trouble should stand unresolved at 30
      days; sleep's cleanup may be made to spare one that does.
  - 4.3.3 A device's own state lives in its ~/.cairn/devices/<device>/<instance>/
    tree.
  - 4.3.4 Shareable provenance (charters, tickets, validations) is git JSON beside
    the code, never a row.
- 4.4 ANTI-INTENTION:
  - 4.4.1 Each device growing its own pool of tables.
  - 4.4.2 Any device reaching into the librarian's code other than through the
    trees tool it publishes. A delegate working its own trees through that
    tool is the delegation of 4.3.1.4, not a breach.
- 4.5 COMMANDS:
  - 4.5.1 The librarian's verbs for depositing and walking (8.4).
  - 4.5.2 Walks go through the librarian's published trees tool, not the bus
    (2.3.7.1.2).
  - 4.5.3 Most devices submit queries to the trees and never walk them: walk,
    nearest and neighbors are encapsulated by the librarian, which owns the
    processes of memory the way CodeMother owns the code. WHY: owning and
    encapsulating those processes is why the librarian exists at all.
