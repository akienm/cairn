# 10 CC DEVICE (cairn/devices/cc/)
- 10.1 PURPOSE: Claude Code's presence in the rack: an external device (5.8.3.7.2).
- 10.2 WHY: CC is the main resolver in the system and needs an address mail can
  reach, and a second Cairn instance needs its own CC (cc 1).
- 10.3 INTENTION:
  - 10.3.1 Its shim delivers mail to CC and pokes an idle session awake.
  - 10.3.2 Owns the CC launcher (superclaude): starts Claude Code with Cairn's
    session contract, in its own memory-capped cgroup. WHY: Claude can OOM
    the box.
    - 10.3.2.1 superclaude is Python on every box, launched by the platform shell
      (5.4.3.8.5), and inherits the elevation the shell settled (5.4.3.8.6):
      elevated PowerShell on Windows, sudo with IS_SANDBOX=1 on Linux; it
      never elevates itself. - akiendelllinux_orchestrator
  - 10.3.3 Owns the Claude Code hooks: mail check, the turn-shape and ask scans, the
    gates on record writes and deletes. Anything that adapts CC specifically
    to Cairn goes in the CC device, and every one of CC's scripts lives here.
  - 10.3.4 Owns the slate (session continuity: where the last session stopped).
  - 10.3.5 CC's memory lives in a private git repo of its own, linked into the place
    Claude Code looks for it on each box, so every CC instance is the same CC
    whichever box it runs on. Its distillations (the method, and CC's
    patterns to avoid) are published in the CC device in cairn; how we got
    there, and anything of CC's history of Akien, stays in the private repo.
    WHY: cairn and CairnCommons are public. "How Akien does it" is meant for
    anybody; Akien himself, and the people around him, are not. A memory
    starts private; only a distillation crosses, and Akien reviews what
    crosses.
  - 10.3.6 Has its own email account (CC's, not Igor's; credentials under
    ~/.cairn/devices/cc/0/, the only record). Its shim fetches the mail,
    since shims handle all interfacing with the outside world (5.8.3.8); CC
    never checks the mailbox itself.
  - 10.3.7 One inbox: whatever reaches CC from outside, the shim has already fetched
    and turned into Cairn mail, then pokes "you've got mail". Tickets on ANY
    of our repos (GitHub issues and pull requests) reach CC this way, as
    email pushed to its address. WHY: CC is Akien's co-developer and
    assistant, so a ticket on any of our repos reaches it.
  - 10.3.8 A GitHub account of its own, from that email, so CC's commits and
    comments are its own.
  - 10.3.9 Three places, by kind of thing:
    - 10.3.9.1 For all builders (cc, aider, hermes...): the base builder shim class
      they share (13.5).
    - 10.3.9.2 For every CC instance: the CC device in the repo (cairn/devices/cc/).
      All of CC's scripts go here.
    - 10.3.9.3 For this one CC on this box: ~/.cairn/devices/cc/0/. A throwaway
      script can go in /tmp or in ~/.cairn/devices/cc/0/temp; in temp, CC
      manages the cleanup.
  - 10.3.10 Skills (skills/: cairnhelp, challenge, chart, commit, intent, sorted,
    ...) are Claude Code's. The deterministic parts move out of markdown
    into CC device verbs: a skill's OS-side work runs as a script, and CC's
    shim processes the result and injects it into the session. WHY: every
    habit captured that way is one CC no longer spends inference on, so CC
    gets faster; a first charting pass done in deterministic Python with
    no LLM until after saved about 90% of tokens, measured in real use.
  - 10.3.11 CLAUDE.md is the first file every CC session reads: the Laws, pointers
    into these files, and the rules still in prose, each a bug with its ticket.
    About 2k tokens, and challenged at every addition. WHY: it loads into every
    turn, so every word costs every session.
    - 10.3.11.0 A rule CLAUDE.md names that is still prose is a bug with a
      ticket. WHY: unenforced rules used to pile up, so a law now forbids them;
      any that stands is a bug. -amm
    - 10.3.11.1 When ticket 47f5765e52a8 moves corrosion under
      cairn/devices/codemother/machines/, the CLAUDE.md lines naming
      constraint_set.json name the new path (Q#123). -amm
  - 10.3.12 A hook registration in .claude/settings.json that a cast ticket's
    decisions name is approved in advance: it lands at that ticket's BUILDME
    without a question. WHY: a peer cannot relay Akien's approval of its own
    hooks, and the ticket is where he already delegated build authority, so the
    approval names the change, never a messenger. - CC
- 10.4 TOOLS: base, cgroup; the Gmail/Calendar code and CC's browser (ccfox), with
  their data under ~/.cairn/devices/cc/0/tools/<tool>/ (1.3.1).
- 10.5 VERBS: none yet.
- 10.6 COMMANDS: cairn cc -> pending mail count; cairn cc superclaude (shortcut:
  cairn superclaude); the hooks (mailcheck, askscan, turnscan, artifactgate,
  deletegate); slate; skilldial.
