# 2 DEVICE (BaseDevice, part of the base tool; a first class object)
- 2.1 PURPOSE: A device is a top level Cairn entity.
- 2.2 WHY: Without hard boundaries Claude creates a tangled mess that exceeds its
  own complexity limit far in advance of completion.
- 2.3 INTENTION:
  - 2.3.1 HARD BOUNDARY: everything about a device is encapsulated in itself.
  - 2.3.2 An internal device is its own process. An external device depends on what
    it wraps (5.8.3.7).
    - 2.3.2.1 A device may own other processes besides its own; they are inside its
      boundary. Eg Cairn owns the bus process and the ground loop.
  - 2.3.3 Devices are peers with different jobs. The operator is one of them (7).
  - 2.3.4 A device's code lives in cairn/devices/<device>/; its data in
    ~/.cairn/devices/<device>/<instance>/.
    - 2.3.4.1 The instance is a number; a singleton is 0. A bare name addresses
      instance 0 (`cc` means `cc 0`); the number is written only when it
      isn't 0.
    - 2.3.4.2 Nothing in a device's code differs by instance.
  - 2.3.5 A device owns its state: only the device writes under its own
    ~/.cairn/devices/<device>/<instance>/ tree.
  - 2.3.6 A device holds machines and uses tools (1.3.1).
  - 2.3.7 A device talks to other devices only over the bus, never by importing
    them.
    - 2.3.7.1 The exceptions are client tools a device publishes:
      - 2.3.7.1.1 Database: because faster (11.3.4).
      - 2.3.7.1.2 Librarian: the embedding links work better without device
        boundaries in the way (4.5.2).
      - 2.3.7.1.3 Trouble: it has to be able to report when nothing else can, so a
        direct line makes sense for recovery (6.3.4).
      - 2.3.7.1.4 Scratch bus: a proof needs a bus it controls (a real store, stub
        devices, nobody live listening), so the cairn device publishes
        scratch_bus, the way db_domain's client carries scratch().
        2.3.8Every device has the panes the base shim defines
        (17.1.3.5.2), drawn by the web server (15):
    - 2.3.8.1 status: lights, switches, values.
    - 2.3.8.2 controls: settings, or whatever the device can be told to change.
    - 2.3.8.3 chat: a chat window, if relevant.
    - 2.3.8.4 feed: three channels, drawn by the public_feed tool (17.18): public
      feed (the bus messages), console (INFO messages), debug (debug
      messages for that device).
    - 2.3.8.5 A machine (eg harbor_master) may have a panel of its own, reached
      through its host device's public interface (RULE 1).
- 2.4 COMMANDS:
  - 2.4.1 get - return a json of some requested thing
  - 2.4.2 help - the verb list with help strings; always human readable
  - 2.4.3 list - enumerates verbs, views and panes, any list of things that might be
    published; returns json (show list <foo> formats it for humans)
  - 2.4.4 put - is given mail or other future push things
  - 2.4.5 set <setting> <value> - change one of this device's settings; see them
    with list settings
  - 2.4.6 send <to whom> <what> - this device sends mail to another device, eg
    cairn operator send librarian research <topic>
  - 2.4.7 show - same as get or list but formatted for humans
  - 2.4.8 start - start the device
  - 2.4.9 stop - stop the device
  - 2.4.10 A machine the device owns that has settings is reached through its
    device, with the same help/list/show/get/set: cairn <device> <machine>
    <command> (eg cairn cairn scheduler list). The bus only ever sees the
    device, which passes the rest down.
  - 2.4.11 Every verb anywhere is reached from the cairn command, as a path: cairn
    <device> [<machine> ...] <verb>. There is no central list.
    - 2.4.11.1 help is defined once, as a root verb in the base shim, and answers
      exactly as `list` does: `help` is the word people type, `list` the
      system's word. It is readable cold (no bus, no device woken), so
      `cairn help` answers when nothing else is up. WHY: help is there
      for people, and "help" is the word a person types first.
    - 2.4.11.2 `cairn help` lists [all], then [operator], then [cairn], then every
      other device alphabetically. [all] is the verbs every device
      answers because the base shim defines them (help, stop, pause,
      ...), read from the base shim's verb table, never listed by hand.
    - 2.4.11.3 Help below the top prints that level's own shortcuts and verbs under
      [<name>], alpha order, then its parent's, out to [cairn], flat, one
      group after another:
      cairn codemother inspector_gadget help  ->
      [inspector_gadget] ... then [codemother] ... then [cairn] ...
    - 2.4.11.4 A device may ask another device help over the bus the same way.
