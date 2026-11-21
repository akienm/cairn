# 6 RECOVERY DEVICE (cairn/devices/recovery/; Recovery And Installation Manager: the host, install, upgrades, root, Rescue and trouble tickets)
- 6.1 PURPOSE: Owns the host Cairn runs on. Gets Cairn installed and running, gets
  it running again when it breaks, and reports usefully when things don't work.
- 6.2 WHY:
  - 6.2.1 A well designed tool should disappear in use: so little friction it's
    almost an extension of the user. Traditional software makes installing,
    opening and using it three separate tasks; Cairn makes them one command.
  - 6.2.2 It's part of our recovery system, so it has to work when other things
    don't, so it can report usefully on them.
- 6.3 INTENTION:
  - 6.3.1 It operates when the bus is down, and when nothing is installed at all.
    The cairn command calls it directly.
  - 6.3.2 The very first run:
    - 6.3.2.1 A user downloads Cairn for the very first time. The readme says
      `cairn/bin/cairn librarian` (the full path, because no paths to the
      cairn command are set up). No database is installed. Nothing.
    - 6.3.2.2 The cairn command sees that, and calls the recovery device directly,
      reporting that we're not set up.
    - 6.3.2.3 It explains that before we can start the librarian we need to do a
      few things first. Easy setup or DIY setup? Most people take easy.
    - 6.3.2.4 It asks for your password so it can install a, b, c, d. The password
      is kept only in an env var, and goes away when the program ends.
    - 6.3.2.5 If we can sort our location, we don't ask. If Cairn needs a password
      of its own (highly likely at some point), it asks during this setup.
    - 6.3.2.6 We install and set up everything, and the user is presented with a
      web based chat window (the librarian's).
    - 6.3.2.7 So the user entered a single command, and all needed setup was
      complete with an absolute minimum of interaction.
  - 6.3.3 Later the user changes something and breaks it. Recovery is called again,
    and invokes Rescue (6.5) if needed to get it all fixed up.
  - 6.3.4 Trouble tickets (3.4.3) live here. Any device has a direct line to raise
    one, not over the bus (2.3.7.1.3).
  - 6.3.5 Install and upgrades live here: the installer machine walks the host-seam
    intentions, verifies each, offers what's missing, applies, re-verifies.
    If xyz library needs an update, this is the component that does it. Any
    change to what the host is goes through here (6.6.3.1.1).
    - 6.3.5.1 The installer verifies every host-seam on every box. It never skips
      one because of the box's platform.
  - 6.3.6 It has a shim, like every device, so it's on the bus when the bus is up
    (upgrades, its troubles, its last repair). It's still called directly when
    the bus is down or Cairn isn't installed.
  - 6.3.7 The setup panels (easy and DIY alike):
    - 6.3.7.1 Each panel is a block of text asking a question, with the default
      answer selected, so the user can go next, next, next until they reach
      the thing they want to change.
    - 6.3.7.2 A set of simple, related questions (eg 10) goes on one panel, to
      approve all or adjust before next.
    - 6.3.7.3 Or a statement: "the following necessary things will be installed:"
      and the list, with the why for each one.
    - 6.3.7.4 One setup question: "Is this a cairn home? No? Then what's the
      hostname/IP for the cairn home I should attach to?" The answer is an
      env var (CAIRN_HOME_HOST), beside the ones for where the repo and the
      runtime folder are.
  - 6.3.8 sudo_relay (machine): Recovery's way to root on Linux, needed for installs
    and upgrades.
    - 6.3.8.1 A command goes in, runs as root, and a permanent audit record comes
      out: the command line, return code, stdout, stderr, plus an id and
      date. The audit folder keeps a rolling one month.
    - 6.3.8.2 A machine, not a tool: it keeps the audit records (state it must
      gate), and runs as its own root process inside Recovery's boundary
      (2.3.2.1).
    - 6.3.8.3 Other platforms get their own way to root (eg on Windows, Rescue and
      the installer run from an elevated PowerShell, 6.5.3.3).
    - 6.3.8.4 Any device may ask Recovery to run something as root. The operator
      answers each ask: decline, accept now, accept always, accept with a
      new rule, or (for a chat-enabled device) chat about it. Cairn owns it.
      - 6.3.8.4.1 For "accept with new rule", an LLM call in the moment helps ask
        the question and sorts the answer, so the rule can be cast. The
        cast rule is DATA (which device, the command's argv prefix or
        pattern, an optional expiry), checked by plain code; never code
        run through eval(). WHY: the rule guards root, and a rule that
        runs code is itself a way to root.
- 6.4 COMMANDS:
  - 6.4.1 cairn recovery: run setup, upgrade or repair by hand. cairn install.
  - 6.4.2 cairn rescueclaude (6.5.4).
  - 6.4.3 cairn trouble live | clear (6.3.4).
  - 6.4.4 cairn recovery sudo <command>: run one command as root through the relay
    (6.3.8).
- 6.5 Rescue (Claude Code outside Cairn; part of Recovery, not a device of its own)
  - 6.5.1 PURPOSE: The mechanic. Claude Code running outside the system, called when
    Cairn won't run or isn't set up yet, to pick up the pieces or get it
    set up.
  - 6.5.2 WHY: A broken system can't fix itself, and a deterministic installer can't
    handle what it didn't foresee. CC is a senior builder INSIDE Cairn; Rescue
    is Claude outside it, getting it running and keeping it running.
  - 6.5.3 INTENTION:
    - 6.5.3.1 Each platform gets a good deterministic installer. When it fails, it
      falls over to Rescue. So does the launcher (5.4.3.8.1).
    - 6.5.3.2 When something won't start (eg the database), Rescue gets called.
    - 6.5.3.3 Bringing Cairn to a new platform is a Rescue job, done on that
      platform (eg Windows, from inside an elevated PowerShell). WHY: Claude
      writes better Windows code on Windows.
    - 6.5.3.4 Needs nothing of Cairn's to run: no bus, no tmux.
    - 6.5.3.5 Launched automatically by a failed install, start or launch, with
      "read this" and the trouble ticket saying what happened and what it
      wants to make happen. The operator can also launch it by hand.
    - 6.5.3.6 Always launched with dangerous permissions, so it CAN do what's
      needed.
    - 6.5.3.7 What Rescue fixes by hand, it turns into a step in that platform's
      deterministic installer, so next time the installer handles it alone.
      Each rescue makes the next one less likely: the system keeps
      learning.
    - 6.5.3.8 On a new platform a simple cairn.bat comes first: at the start it
      takes only the rescueclaude option, launching Claude with 200K context
      and dangerous permissions.
    - 6.5.3.9 Code home: the bootstrap floor that comes up before anything else
      lives in the Recovery device; superclaude, the CC launcher, lives in
      the CC device (10).
  - 6.5.4 COMMANDS: cairn rescueclaude - launch Rescue's Claude Code. It starts
    nothing else. (Contrast cairn superclaude, which brings the rest of Cairn
    up first; both run with dangerous permissions.)
- 6.6 The host
  - 6.6.1 PURPOSE: Abstracts the swarm of systems that Cairn is running on.
  - 6.6.2 WHY: Recovery has to diagnose and repair the host when the rest is down,
    so the host's readings and the changes to it belong to Recovery, not to
    any device that could be the one that is broken.
  - 6.6.3 INTENTION:
    - 6.6.3.1 Recovery owns the OS and hardware Cairn runs on. Everything that is
      Cairn itself belongs to the Cairn device or to whichever device it's
      been delegated to.
      - 6.6.3.1.1 The line is using vs changing. Any device may USE the OS's
        services (write a file, open a socket, start or stop its own unit
        with systemctl). CHANGING what the host is (installing or
        updating systemd unit files, packages, udev rules, cron entries)
        goes through Recovery. Eg Cairn restarts the bus itself; putting
        the bus's unit file in place goes through Recovery.
    - 6.6.3.2 It is aware of and makes available CPU use, system temps, SSD space,
      etc. A device that wants a trigger on a host reading (eg CPU over 80)
      subscribes; Recovery pokes it when it crosses. The reading stays in
      Recovery.
    - 6.6.3.3 It owns app probes related to the hardware and network.
    - 6.6.3.4 It owns all system metrics: the metrics table (17.27). Until Recovery
      exists the cairn device holds it (5.3.6).
    - 6.6.3.5 Cross system communication belongs to the bus (5.5.3.8).
    - 6.6.3.6 The host readings Recovery needs to diagnose (disk full? is postgres
      running?) work when the bus is down, like the rest of Recovery.
    - 6.6.3.7 The hostname comes from the system device. It answers which box
      (the short hostname, lowercased) and which OS family, and nothing else in
      Cairn asks the OS for either. Callers reach it through the client tool it
      publishes (2.3.7.1.5), so a box names itself on every OS, Windows
      included, with no bus running. - akiendelllinux_cc_0
  - 6.6.4 COMMANDS:
    - 6.6.4.1 show/get health - cpu use, memory, ip, uptime, temps, network up/down
    - 6.6.4.2 show/get env - the env vars relevant to cairn as set at the moment
