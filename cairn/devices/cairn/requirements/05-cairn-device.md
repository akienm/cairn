# 5 CAIRN DEVICE (cairn/devices/cairn/)
- 5.1 PURPOSE: Represents the cairn system in aggregate.
- 5.2 WHY: Everything has exactly one owner (Law 6), so whatever is Cairn and has
  not been delegated needs one home, and the foundations every device stands on
  (bus, rack, heartbeat, shims) need an owner that is not one of the devices
  standing on them.
- 5.3 INTENTION:
  - 5.3.1 Cairn owns everything about the system that is Cairn and hasn't been
    delegated elsewhere. A delegated domain belongs to its device, not to
    Cairn, even though it is of Cairn: the librarian is delegated learning,
    research and answering queries on what's learned; the embeddings device
    is delegated producing the embeddings we search with. The OS and hardware
    belong to Recovery (6.6).
  - 5.3.2 Owns the foundational components: bus (5.5), ground loop (5.6), rack
    (5.7), shims (5.8) and the scheduler in them (5.9), launcher (5.4).
  - 5.3.3 Drives sleep.
    - 5.3.3.1 Sleep is an entry on Cairn's scheduled list (5.9). Since there is one
      Cairn in the swarm (5.5.3.8.1), Cairn always starts the sleep token,
      however many boxes there are. At its time Cairn runs its own sleep
      routine, then hands the sleep token over the bus to the next device,
      and so on round the rack in the rack's order (5.7.3.3).
    - 5.3.3.2 What each device does in its sleep depends on the device: the
      librarian consolidates memory; the learning blocks do the same on
      their smaller memory sets; Recovery might run backups or SSD checks;
      some (eg the embeddings device) do nothing.
    - 5.3.3.3 Cairn's own sleep has a lot to do, including clearing the logging
      tree of things older than 30 days (4.3.2).
    - 5.3.3.4 Sleep's base trigger is the clock (2300). Once we can tell how
      recently things were interacted with, that overrides the clock.
    - 5.3.3.5 When this box may be used is decided from three inputs: the schedule
      sets a baseline; observing Akien (how recently things were interacted
      with) can open time that would otherwise not exist, because measuring
      trumps rules; and an away window ("going to bed", "out to the
      theater", x to y) does the same.
      - 5.3.3.5.1 An opening lets the system as a whole put every available
        resource on a task or group of tasks. No orchestrator: no box
        hands work to another. Work shows up in the harbor (tasks,
        tickets, whatever), and any box with an opening runs it. Eg four
        laptops each reading one block at a time into the database with
        local inference, where a block could take 5 minutes.
  - 5.3.4 `cairn start` (= cairn cairn start) brings the system up: ground loop,
    bus, shims. `cairn stop` takes it down.
    - 5.3.4.1 Any cairn command brings up whatever it needs, including the whole
      install on the very first run (6.3.2). WHY: a well designed tool
      should disappear in use.
  - 5.3.5 There is no central supervisor. Each part starts what it needs by trying
    to use it: sending a message starts the bus if it is down, a message
    arriving wakes its shim, the shim wakes its device. Many very small
    supervisors, each one detect-and-start. WHY: a supervisor is one more
    thing to keep up, and the system must come up from any part that is
    touched.
    - 5.3.5.1 The detect-and-start lives in one tool, the waker, and it sits inside
      connect: every client's connect is a wake attempt, so no caller can
      forget one. A probe watches and reports; the waker acts.
    - 5.3.5.2 Two callers waking the same part at once start only one: the part
      that binds its socket first is the only one; a second copy finds it
      taken and exits quietly (as the ground loop does, 5.6.4.3).
      - 5.3.5.2.1 The second copy exits SILENTLY; refusing loudly has no reason
        behind it. A --force switch means "don't exit if another is
        running: kill the other and take over", for replacing a running
        older version with a newer one. This is the ground loop's rule;
        CC's reading is that it holds for every host singleton (bus,
        rack, a device name). - CC
      - 5.3.5.2.2 More than one instance of a device is allowed: many things can be
        singletons or not (eg a second embeddings generator on another
        host when traffic is heavy). Instances have distinct names so
        messages route. Naming is the shim's job: the launcher asks the
        shim for an instance, and a shim given no name when cc_0 exists
        launches cc_1.
      - 5.3.5.2.3 Declaring a new instance rotates, explicitly or implicitly:
        --new rotates explicitly, no flag rotates implicitly, --name
        overrides both. -amm
        Reading (superclaude is the rescue service's launcher,
        cairn/devices/cc/superclaude.py; none of these needs a folder prepared by
        hand):
        - `cairn superclaude --new` always rotates explicitly to the next
        undeclared n (cc_1 when cc_0 is declared, cc_2 when cc_1 is, and so
        on), then declares, wires and launches it.
        - `cairn superclaude` with no flag rotates implicitly: it starts
        cc_0 when cc_0 is free, and when cc_0 is taken (running) it rotates
        as --new does.
        - `cairn superclaude --name <x>` uses exactly x and overrides all of
        that: it declares x if absent, then launches it.
        - The declared folder commits through the door in the same act, so
        the house tree is not left dirty and crossings are not refused.
        - The one CC inference here: "implicitly" is read as taken (running)
        cc_0 means rotate, while a declared-but-stopped cc_0 is simply
        started.
        Tickets: aa05710a5124 reshapes to this; d13859e2ae46 is the implicit
        rotation; 0f7a8cada1ca names the next undeclared n.
        - akiendelllinux_orchestrator
    - 5.3.5.3 What the waker starts outlives whoever started it (detached, or
      through systemd-run --user, which gives it its own memory cap and log
      while still deciding nothing). Restarting a shim never takes down the
      bus it once woke.
      - 5.3.5.3.1 Nothing requires Akien's word for a proof to run. A proof that
        starts Windows processes runs without asking; no env var or
        standing flag gates it.
      - 5.3.5.3.2 On every Windows box, what Cairn starts runs without a console
        window by default; a window opens only when someone asks for one.
        WHY: the boxes serve him (the media box showed pop-ups during videos).
    - 5.3.5.4 A wake waits until the part answers, at most 60 s (5.5.3.9).
      Repeated failures back off, then file a trouble (5.8.3.2.2), so a
      crash loop cannot spin.
    - 5.3.5.5 Nobody sends to the ground loop, so the cairn command (and login)
      wake it; its pulse then wakes the shims (5.8.3.4).
  - 5.3.6 Holds the metrics table (17.27) until Recovery exists (6.6.3.4).
- 5.4 launcher (machine)
  - 5.4.1 PURPOSE: The operator's ramp onto the bus: the cairn command.
  - 5.4.2 WHY: One command reaches every verb in the system with no central list
    to maintain (2.4.11), and it must work even when nothing else does, so
    that the first thing a user types can also be the thing that installs
    or repairs Cairn (5.3.4.1).
  - 5.4.3 INTENTION:
    - 5.4.3.1 Owned by the Cairn device. Mostly a router.
    - 5.4.3.2 The launcher walks the words. `cairn cairn foo bar` (the long form)
      means "tell the cairn device to run foo with argument bar". At each
      level: is the next word a machine here? Step into it and take the
      next word. Is it a script in this level's bin/? Run it, pass back the
      result, done. Neither? It is a bus verb: send it to this level over
      the bus. So `cairn foo bar baz`: foo is a device; it has a machine
      bar; bar's bin/ has baz, so baz runs. No bar machine? bar goes to foo
      over the bus. Each check is one directory lookup, so it is fast. WHY
      scripts first: scripts are the simple path; the bus is the route to
      what a device answers itself.
    - 5.4.3.3 Any device or machine may have a bin/ beside its code. That folder IS
      its list of shortcuts: add a file to add one, delete it to remove one.
      A shortcut is a script that calls the long form (eg `cairn
      superclaude` -> `cairn cc superclaude`; `cairn show temp` -> `cairn
      recovery show temp`), which also saves the walk from searching
      farther, or does work itself (eg install). Shortcuts live beside what
      they serve (RULE 1). `cairn foo` whose first word is not a device
      means `cairn cairn foo`: top-level shortcuts are the cairn device's
      bin/.
      - 5.4.3.3.1 A new shortcut needs no watch. Most instance bins are links to
        their class bin, so the shortcut is reachable the moment its file
        lands; the build's proof is the whole guarantee.
    - 5.4.3.4 Scripts are Python wherever possible, run by Cairn's own interpreter,
      so one file works on every platform. Platform-specific ones match
      their platform: executable or .sh on Linux; .bat, .cmd or .ps1 on
      Windows.
    - 5.4.3.5 If a shortcut has the same name as a device, the launcher warns "x
      hides y" and then runs x.
    - 5.4.3.6 `cairn` speaks as the Operator (7).
    - 5.4.3.7 Repo-root bin/ holds only the launcher itself, the one thing on PATH.
      Every shortcut lives in the bin/ of the device or machine it belongs
      to; its bin/ plus its bus verbs is what help lists at that level.
    - 5.4.3.8 The launcher is Python (bin/cairn), run by Cairn's own interpreter, so
      Windows needs no bash. Typing `cairn` works on either platform.
      - 5.4.3.8.1 In front of it sits a thin platform shell (a shell script on
        Linux, cairn.cmd or cairn.ps1 on Windows) with enough brains to
        fall over to Rescue (6.5) when it can't find Cairn's Python, or
        Python throws, or anything else stops the launcher. The failure
        throws a trouble ticket (3.4.3), and the ticket is Rescue's "read
        this" (6.5.3.5); a repeat increments that ticket's counter.
        Rescue's prompt says: at the end of proving the fix, check for
        more errors, to clear or fix as appropriate. WHY: trouble has to
        be able to report when nothing else can (2.3.7.1.3).
      - 5.4.3.8.2 With no Python at all, the trouble class can't run, so the shell
        writes the trouble file itself, in the same format, and finds a
        matching open one to increment.
      - 5.4.3.8.3 Only a failure of the launcher itself falls over to Rescue. A
        command that runs and fails (eg a verb that exits 1) is that
        command's error, reported as usual. The Python launcher marks its
        own failure in a way the shell can tell apart (eg a reserved exit
        code).
      - 5.4.3.8.4 Rescue is interactive, so the shell launches it only when someone
        is at a terminal. Called from a script, a hook or a schedule, it
        throws (or increments) the trouble just the same and exits loudly
        with an error, leaving the ticket for the next Rescue. WHY:
        nothing may hang waiting on a Claude nobody sees.
      - 5.4.3.8.5 Each platform shell does two things, in order, before handing
        over: it elevates, then it runs Cairn's own Python on the launcher
        (on Windows `@python <path>\cairn ...`; on Linux the same without
        the @). Every decision after that is Python's; the shell holds no
        other logic beyond the fall-over above.
      - 5.4.3.8.6 Elevation is the shell's, settled before Python starts, and
        nothing inside asks again. On Windows the shell runs in an elevated
        PowerShell. On Linux the shell sudoes the launch, and claude runs
        as claude_code (17.2.2.2.1), an admin that may elevate without
        asking. WHY: the whole box is the sandbox, so settling elevation
        once at launch is simpler than elevating on request, and the
        session's uid is not the launch user's. -amm
- 5.5 bus (machine)
  - 5.5.1 PURPOSE: The message passing system devices talk through.
  - 5.5.2 WHY: The more of our messaging goes over the bus, the better we follow
    encapsulation (RULE 1), and that is known to be good for Claude: it cuts
    the complexity of the system to one part at a time, and with the global
    view in this outline, a section can be read and compared to its code
    without a lot of extra noise.
  - 5.5.3 INTENTION:
    - 5.5.3.1 It is the only way devices talk to one another.
    - 5.5.3.2 Every part is its own process: the bus, each shim, each device, the
      ground loop. Any one can be stopped and restarted alone while the
      rest run on. WHY: a self-modifying system needs that.
    - 5.5.3.3 Two kinds of request: Send, asynchronous, like sending an email; and
      Show/Get, synchronous, like requesting a web page.
    - 5.5.3.4 Messages sit in a SMALL buffer in memory. WHY: in memory is faster.
      - 5.5.3.4.1 A message nobody picks up within n milliseconds is pushed out of
        the buffer to the database, into a table that is just a table of
        messages. That table is the bus's exception to the memory model
        (4.3.1.5): it is not learning, and the buffer in front of it is
        what keeps the bus fast.
      - 5.5.3.4.2 Mail goes to the bus, and from the bus to the shims. If the bus
        has to start a shim to deliver, it may hold that mail in a
        transient tree (4.3.2) until the shim is up. That is mail waiting
        on a wake; 5.5.3.4.1 is mail nobody picked up.
    - 5.5.3.5 The shims, each connected to the bus, pick up the messages and route
      them to their device in whatever manner is appropriate.
    - 5.5.3.6 The Operator device and the cairn command are the operator's route
      onto the bus.
    - 5.5.3.7 Real-time inspection of bus traffic is not needed. Logging the
      messages to the transient pool (4.3.2) may be worth doing. The bus is part of the Cairn device, so a bus feed, when there
      is one, is a sub-panel off the Cairn device's page, listing everybody.
    - 5.5.3.8 One bus per cairn instance, not per host. Each box runs its own bus,
      and the buses talk to one another, so a device always talks to the bus
      on its own box; together they are the instance's one bus. A device
      runs on one box; the other boxes reach it over the buses. No box needs
      a full set of devices. WHY: so the instance can run several heavy
      tasks at once across boxes.
      - 5.5.3.8.1 Every box runs all the foundational things: a bus, a ground
        loop, the shims. They are the Cairn device's machines, and there is
        only one Cairn device: a singleton within the swarm, owning them on
        every box. WHY: Cairn is the system in aggregate, which is not the
        same thing as the host (6.6); a box is part of the host, and the
        swarm of boxes is still one Cairn.
    - 5.5.3.9 A shim waking its device never takes more than 60 s. A sync caller
      waits at most 60 s for the wake, then gets "not now" back; a wake that
      misses 60 s is a trouble. 600 s is the limit for an inference call to
      come back, not for a wake.
    - 5.5.3.10 A message is addressed to a name (a device instance), never to a
      connection. A shim that restarts reconnects and answers to the same
      name, so restarting it never restarts the bus.
    - 5.5.3.11 Transport: as fast as we can make it, settled by measuring on this
      box, not by choosing. Inside a Linux box the bus is our own small
      broker on Unix sockets, routing by name (measured 50 µs a round
      trip, against 110 for Postgres NOTIFY and 250 for NATS). Between
      boxes, and on Windows (Python there has no AF_UNIX), it is TCP,
      speaking TLS with pinned certificate fingerprints checked both ways;
      cairn install makes each box's certificate. WHY TLS: no tunnel,
      nothing extra to set up.
      - 5.5.3.11.1 A Unix socket path cannot be longer than 108 bytes, so a socket
        address is kept short and never nests deep in a device tree.
      - 5.5.3.11.2 Large things (embeddings, documents) never ride the bus: they go
        to the database or a file and the message carries the id.
        Database access stays an import in each process, one connection
        each.
      - 5.5.3.11.3 A rehearsal's reader gaps are written into the ticket and it is
        rehearsed again; the record does not stand unclean.
  - 5.5.4 TOOLS: base, public_feed, scratch_bus (2.3.7.1.4). VERBS: none.
- 5.6 ground_loop (machine): the heartbeat
  - 5.6.1 PURPOSE: The one timed thing in an event driven system.
  - 5.6.2 WHY: daemons for everything become impossible to shut down. So there
    is one loop, kept as simple as possible. The system is entirely event
    driven except for two timed things: Akien's away windows (x to y) and
    sleep.
  - 5.6.3 ANTI-INTENTION: what it must never grow back: a bus, a shim, probes, other
    kinds of pulses, staleness, managers.
  - 5.6.4 INTENTION:
    - 5.6.4.1 It is the only daemon in the system: the only thing that wakes on a
      clock. The few things that need timing hang off it, directly or
      through the scheduler (5.9), never on a daemon of their own.
    - 5.6.4.2 It re-starts itself when its own files change, unless
      COMMAND_DO_NOT_RESTART is set. COMMAND_EXIT stops it with exit code 0.
    - 5.6.4.3 A second copy refuses to start.
    - 5.6.4.4 It launches each device's cairn/devices/<device>/groundloop/pulse.py,
      each as its own process (5.8.3.4).
    - 5.6.4.5 It writes one JSON record at the end of a pass listing each device:
      beat time, device folder found or NOT FOUND, file mtime, pid spawned.
      It does no checks and no takeover.
    - 5.6.4.6 Beat interval is a setting, 60 s for now, expected to go a lot faster
      (under a second) now that nothing heavy hangs off it.
      So the scheduler fires an entry whose time fell since the last beat,
      not one that equals the beat's minute: any beat length fires each
      entry exactly once.
  - 5.6.5 TOOLS: base. VERBS: none.
- 5.7 rack (machine)
  - 5.7.1 PURPOSE: Holds the running devices: a stack of rackmount devices, with the
    bus connecting them all.
  - 5.7.2 WHY: So "what is running?" and "is it up?" have one answer, measured from
    the bus, with nothing stored.
  - 5.7.3 INTENTION: a dict of the device instances, in the form of their shims.
    - 5.7.3.1 It holds instances, not classes: one shim per instance. cc 0 and cc 1
      are two shims.
    - 5.7.3.2 It is the shims connected to the bus: who's in the rack is who's
      connected, which the bus can measure. A shim that isn't running isn't
      connected, so it isn't in the rack. The rack says what is running; it
      is not where instances are declared (5.7.3.4).
    - 5.7.3.3 The sleep token goes round in sequence, one sleeper at a time, so no
      one sleeper takes the whole system to everyone else's cost. The order
      itself doesn't matter: alphabetical by device, then by instance, the
      same on every box and nothing stored.
    - 5.7.3.4 An instance is declared by its folder existing in class-space:
      cairn/devices/<device>/<instance>/ (one address in two roots).
      Declared = the folders (read by the rack tool, 17.20); running = which
      of those are in the rack.
    - 5.7.3.5 "Is it up?" is the rack's to answer. A device that doesn't respond
      within about 30 seconds, while the CPU isn't pegged and slowing it
      down, MIGHT be a candidate for killing and restarting.
- 5.8 shims
  - 5.8.1 PURPOSE: Integrates its device into the system.
  - 5.8.2 WHY: So any program, ours or not, can live in Cairn as a device.
  - 5.8.3 INTENTION:
    - 5.8.3.1 Every device has a shim. Each shim is its own process, one per
      instance, and connects to the bus as a client. WHY: in the bus
      process, updating one shim meant bringing the whole bus down, and one
      shim's stall was everyone's. Separate, a shim restarts itself when its
      own files change, like the ground loop, and the bus stays up.
    - 5.8.3.2 The shim always starts its device. Nothing else does.
      - 5.8.3.2.1 It wakes the device when it's not running and is needed.
      - 5.8.3.2.2 If the device won't come up, the shim retries; after many retries
        it files a trouble ticket for Akien and CC. This holds for every
        wake: a request, a pulse, the sleep token.
      - 5.8.3.2.3 It answers what it can itself; when it can't (eg a health question
        it holds no answer to), it wakes the device and asks.
        - 5.8.3.2.3.1 A shim talks to its own device process over the same
          transport as the bus (5.5.3.11): Unix sockets inside a Linux
          box, TCP where Unix sockets won't work (Windows). WHY: sockets
          were the fastest we measured, and each piece has to be quick.
      - 5.8.3.2.4 A device may declare an idle time; the shim stops it after that
        long unused, and the next message wakes it again. With none
        declared it runs until `stop`. WHY: idle costs memory, not CPU,
        so the librarian, slow to load, stays warm for hours, while
        something cheap can stop after a minute.
    - 5.8.3.3 Processes all messages from the bus for its device.
    - 5.8.3.4 pulse.py is part of the shim. The ground loop calling it tells the
      shim the pulse has arrived, and starts the shim if it isn't running.
      - 5.8.3.4.1 The ground loop finds one pulse.py per device. pulse.py reads its
        own device's declared instances (5.7.3.4) and pulses each one, so
        the ground loop never needs to know instances exist. Pulsing an
        instance that isn't connected is what starts its shim.
      - 5.8.3.4.2 Any shim, through its pulse.py, brings the bus up if it's down:
        whatever is called brings up what it needs (5.3.4.1).
      - 5.8.3.4.3 pulse.py asks nobody anything. It starts the shim if it's down,
        else tells the mechanisms inside the shim that need a pulse "here
        ya go!" Only daemon-shaped things hang there, things that
        actually need a heartbeat (eg cc's Gmail fetch, 10.3.6);
        everything else fires on events. WHY: pulse.py is a place to hang
        daemons from, not managers.
    - 5.8.3.5 Processes the sleep cycle, if its device needs one: when the token
      arrives, it wakes its device to do its sleep (the device does the
      sleeping, not the shim), then passes the token on. If its device won't
      come up, the shim files the trouble and still passes the token on, so
      the rest of the rack sleeps.
    - 5.8.3.6 Writes its runtime data, if any, to ~/.cairn/devices/<device>/<instance>/.
    - 5.8.3.7 Three kinds of device sit behind a shim:
      - 5.8.3.7.1 Internal (eg librarian): ours, engineered to work with its shim,
        so the shim adapts little.
      - 5.8.3.7.2 External (eg Claude Code): a program we don't control; the shim
        does the adapting that lets it exist here.
      - 5.8.3.7.3 Virtual: the shim is the whole device. Eg a calibre device over
        calibre's own database, or a weather device over the acurite
        data, for when something else in Cairn (say, a personal assistant
        scheduling outdoor events) wants the weather.
    - 5.8.3.8 The shims handle all interfacing with the outside world: a device
      that needs to speak a foreign protocol (eg OpenAI's wire format) does
      it in its shim.
  - 5.8.4 COMMANDS: the Device commands (2.4). The shim answers start and stop
    itself.
- 5.9 scheduler (part of the base shim; uses tools base, rack)
  - 5.9.1 PURPOSE: Holds each device's list of scheduled things.
  - 5.9.2 WHY: The few timed things in the system hang off the one heartbeat, each
    on its own device's list, so no device grows a daemon of its own (5.6).
  - 5.9.3 INTENTION:
    - 5.9.3.1 The pulse triggers the check: each pulse, the shim checks its device's
      list against the clock. No match, the pulse is dropped; a match is a
      PROBE that kicks off that thing in the device (5.6.4.6).
    - 5.9.3.2 Sleep is one entry on Cairn's list (5.3.3.1).
    - 5.9.3.3 Part of the base shim, so every device can schedule things with it
      (eg Recovery's weekly SSD check is on Recovery's own list).
  - 5.9.4 COMMANDS: list, show, get, set (2.4.10).
- 5.10 COMMANDS: the Device commands (2.4) plus start and stop for the whole system
  (5.3.4); groundloop, compile (the intentions_model_compiler, 17.12),
  artifact (17.2), trash, as shortcuts in its bin/.
