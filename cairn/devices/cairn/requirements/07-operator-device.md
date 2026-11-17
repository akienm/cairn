# 7 OPERATOR DEVICE (cairn/devices/operator/)
- 7.1 PURPOSE: Represents the operator(s) of the system.
- 7.2 WHY: Akien gets command-line access to the bus, using the system the
  way any device does (eating our own dogfood). And
  the operator needs an address: mail sent to the operator, questions only the
  operator can answer, and asks only the operator may accept all need somewhere
  to land.
- 7.3 INTENTION:
  - 7.3.1 Receives mail sent to the operator, and makes it available on its web
    page.
  - 7.3.2 Represents the user on the bus.
  - 7.3.3 Retains information related to the operator.
  - 7.3.4 Processes queries from the cairn command sent to operator.
  - 7.3.5 More than one operator means instances: operator 0 is Akien, operator 1
    someone else. CC never acts as an operator; it always speaks as the CC
    device, so it can never accept an ask that only an operator may (eg a
    root ask, 6.3.8.4).
  - 7.3.6 Its web panel is the operator's to-do list: email, trouble tickets, open
    questions (the ones only the operator can answer). The list is live:
    items appear as they arrive and leave as they're answered or resolved.
    - 7.3.6.1 Artifacts awaiting review are not on it. Artifact review is replaced:
      the intentions say what it should look like, and CC assesses each
      artifact against them as one of: it gets us closer (keep); it could
      get us closer with changes (change it); it points the wrong way and
      should be replaced; it points the wrong way and should be dropped;
      ask more questions in order to decide.
  - 7.3.7 Machine: the operator inbox builds the to-do list from live state,
    storing nothing (the operator_inbox tool, 17.14).
- 7.4 COMMANDS:
  - 7.4.1 The `cairn` command is the operator's interface, so it is special: it
    speaks as the operator (5.4.3.6). How it resolves a command, and how help
    lists: 5.4.3.2 and 2.4.11.
  - 7.4.2 Answering a question is the operator acting, so it is `cairn operator
    answer <id> "<words>"`, never a verb on whichever device asked.
  - 7.4.3 cairn operator inbox (the to-do list); cairn review <id> "<words>".
