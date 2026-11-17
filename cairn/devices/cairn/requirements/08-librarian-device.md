# 8 LIBRARIAN DEVICE (cairn/devices/librarian/)
- 8.1 PURPOSE: Owns what Cairn knows: the knowledge graph trees (4.3.1), and
  answers questions from them.
- 8.2 WHY: the librarian is a chat bot that learns always and summarizes when
  asked. A query resolves by walking the trees, cheap and
  with no inference; on a miss the LLM supplies the missing nodes, which are
  kept, so the next time is a walk.
- 8.3 INTENTION:
  - 8.3.1 Owns the graph trees: the one list of nodes, and each depositor's index
    over them (4.3.1.1). Owns all learning in the system and delegates it
    (4.3.1.4); CC's learning records belong here too.
  - 8.3.2 Learns always: takes what other devices deposit, and decides itself what
    else to learn from the work going on around it.
  - 8.3.3 Summarizes when asked. Its chat pane is its face.
  - 8.3.4 Surfaces to each device what others learned that it would find useful
    (4.3.1.2).
  - 8.3.5 Its sleep is consolidation.
  - 8.3.6 Is the embeddings device's biggest user (14): its embeddings are tree
    histograms from there, not vectors from the inference proxy's embed verb.
    Structural embeddings: matching how things work, across domains, not
    surface similarity.
  - 8.3.7 Research: the librarian goes out on its own, through the general
    web_operator machine (16.4), which it holds as that machine's first user.
- 8.4 VERBS:
  - 8.4.1 ask "<query>". Implicit: a text that matches no other verb or command is
    taken as a query (`cairn librarian how does X work` asks).
  - 8.4.2 read <file | url | book>: ingest. A url is read through web_operator.
  - 8.4.3 research "<topic>" (also said "learn about"): the librarian goes out and
    learns the topic.
  - 8.4.4 Every research/read/learn verb takes `for <device>/<question>`: the
    learning is applied to that question tree, belonging to that device, and
    is also available to the librarian. Eg `cairn librarian research
    cognitive columns for "igor/how does the human mind work"`. Afterwards a
    query can go to either that device or the librarian, and they won't
    necessarily weigh it the same: several trees index the same nodes, each
    with its own question and weights: each graph tree is a question
    space.
  - 8.4.5 walk, nearest, neighbors: not the verbs a device uses; the librarian
    encapsulates them under ask (4.5.3). `walk "<string>" for <question>` is
    also the bench's verb for the operator (4.3.1.10): diagnostic, showing
    the path and scores, never how a device asks.
- 8.5 TOOLS: trees (its own, published as a client tool); base, question,
  bus_client, system_word, gate; machines learning_block, web_operator; db
  client.
  - 8.5.1 The trees tool's charter lists in its public interface what it offers: the
    module, and deposit_keyed, find and the keyed leaf's shape beside it.
- 8.6 COMMANDS: cairn librarian ask <question> (or just cairn librarian
  <question>); cairn librarian read <file|url|book> [for <device>/<question>];
  cairn librarian research "<topic>" [for <device>/<question>].
  - 8.6.1 A bare `cairn librarian` never prints URLs. It (1) launches the
    librarian's shim, which (2) parses the request (nothing) and so (3)
    launches the librarian and (4) launches a browser pointed at the
    librarian's chat page. That http request arrives at the web server's
    shim, which launches the web server, which displays the librarian's page
    with focus on the chat window. Each part is self-initializing (5.3.5).
