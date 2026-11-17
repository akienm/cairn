# 16 SHARED MACHINES (cairn/machines/: machines several devices hold)
- 16.1 learning_block
  - 16.1.1 PURPOSE: The engine of a learning block: input -> candidates -> evaluate
    -> decide or escalate. In the walk's terms (4.3.1.9): decide is a walk
    that landed, and the deposit reinforces its path; escalate is a miss,
    first to the LLM (4.3.1.9.5), and when the LLM returns nothing usable,
    a question to the operator (17.19).
  - 16.1.2 WHY: Many devices learn in the same shape; one engine, held by each,
    holding its trees by the librarian's delegation (4.3.1.4). A learning
    block is a composite of many parts, so it is a machine.
  - 16.1.3 The first compile (ticket e889b197a3f6) learns from the runs that carry
    Akien's answers: the host backfill, where carries_his_answer killed 5, 6
    and 5 of 6 candidates. The engine traces (4 of 7 the same question with
    the same winner) only show the engine agreeing with itself, so they are
    the floor's agreement check, not its teacher. - CC
- 16.2 nest
  - 16.2.1 PURPOSE: A nest of sieves that lets out just the parts we want.
  - 16.2.2 WHY: Questions that can be answered deterministically should never reach
    an LLM; a nest composes those questions so routing and inspection run
    without inference.
  - 16.2.3 INTENTION:
    - 16.2.3.1 A machine made of sieve tools. Each question is a sieve; sieves can
      come after others. Bands are phases: preprocess, measure,
      postprocess. A postprocess sieve stamps a rank rather than a cut,
      and the shake hands back the survivors in rank order (11.4.6).
    - 16.2.3.2 Sieves measure, never judge: deterministic Python.
  - 16.2.4 USERS: the inference proxy, through its route machine (11.4.6);
    build_inspector (9.4.3).
- 16.3 skill_block
  - 16.3.1 PURPOSE: The door a skill's firing passes through, so a skill can't skip
    its gate.
  - 16.3.2 WHY: a rule that matters is enforced by physics, not policy (Law 4).
  - 16.3.3 CC's for now; CodeMother's eventually, as CC's role diminishes and the
    Cairn factory builds other graph-tree factories. No urgency.
- 16.4 web_operator
  - 16.4.1 PURPOSE: The general machine a device holds to go out on the web. It
    operates web pages, for reading and other purposes. The web server (15)
    serves pages; this one works them.
  - 16.4.2 WHY: several devices need to go out on the web, and each would otherwise
    build its own way. CC's own browser (ccfox, 10.4) is the precedent, not
    this machine: it is CC's alone.
  - 16.4.3 Each holder keeps its own data under
    ~/.cairn/devices/<holder>/<n>/machines/web_operator/. The librarian is
    the first holder (8.3.7).
  - 16.4.4 web_operator may talk on the web by any means: direct HTTP, a browser
    driven over WebDriver (selenium or similar), or anything like them. So it
    is on the inference sole-path rule's allowed list (11.4.1).
