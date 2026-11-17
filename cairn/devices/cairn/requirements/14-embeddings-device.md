# 14 EMBEDDINGS DEVICE (cairn/devices/embeddings/)
- 14.1 PURPOSE: Turns a string plus a question into an embedding, by walking the
  graph tree that asks that question.
- 14.2 WHY: Structural embeddings match how things work across domains, not surface
  similarity (8.3.6). The librarian is its biggest user, so it is built before
  the librarian: the first device after CC and Cairn.
- 14.3 INTENTION:
  - 14.3.1 Each tree asks one question (4.3.1.5.2). Send any string with a question;
    that tree, a word graph, returns a histogram: the weighted path it
    followed. The histogram is the embedding. How the walk goes: 4.3.1.9;
    the bench it is learned on: 4.3.1.10.
  - 14.3.2 An embedding is searched with LIKE (4.3.1.9.4).
  - 14.3.3 A memory node can carry any number of embeddings, one per question asked
    of it. We don't routinely generate every possible one: that becomes a
    sea of useless data (4.3.1.6).
  - 14.3.4 Which embeddings get made is what the memory intends. Like Akien's mind
    running science fiction past "how might that work", looking for things
    from other domains it could use later. First hypothesis: 4.3.1.9.8.
