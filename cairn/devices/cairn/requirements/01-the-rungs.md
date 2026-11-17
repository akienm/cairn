# 1 THE RUNGS (the complexity axis)
- 1.1 PURPOSE: Name what every component is, so it has one place to live.
- 1.2 WHY: Each rung adds one thing to the rung below, so a component's place says
  how complex it is, and the line between rungs is measured, not judged.
  Without hard boundaries Claude creates a tangled mess that exceeds its own
  complexity limit long before completion.
- 1.3 INTENTION:
  - 1.3.1 Tool: a complete primitive. Has users, not an owner. Calls no other Cairn
    component (stdlib and base only) and owns no state of its own. Lives in
    cairn/tools/ (17). Its data for a holder lives under that holder:
    ~/.cairn/devices/<device>/<instance>/tools/<tool>/.
  - 1.3.2 Machine: tools plus the glue that holds them together. Has an owner.
    Anything that calls another component, uses other tools, or owns state it
    must gate is a machine. Lives inside its device
    (cairn/devices/<device>/machines/<machine>/), or in cairn/machines/ when
    several devices hold one (16).
  - 1.3.3 Device: its own process, in the rack, on the bus (2).
  - 1.3.4 Instance: every device has at least one; a singleton is instance 0.
  - 1.3.5 First class object: a thing with a charter that stands on its own in
    this outline (Ticket, a machine; Graph Trees; Rescue).
  - 1.3.6 Tools and machines are peers in the tree; the rung is complexity, not
    rank.
  - 1.3.7 Code that is no longer needed is deleted. Git history keeps it if we ever
    need it back.
    - 1.3.7.1 Deleting code is about running code, not about the record of what
      happened. A retired path that something still CALLS is the defect; a
      retired path named by a record of what passed through (history, state,
      validations, verdicts, a measured fixture) is not. Requirements that
      police history are de-emphasized, because the aim is less history
      noise in front of Claude, not hidden history (Law 5).
      - 1.3.7.1.1 A retirement proof measures callers: a retired module nothing
        imports, a retired command or path nothing runs. A file that only names a
        retired path (a fixture, a record, a charter) is not measured. Why? Naming
        is history; only a caller breaks.
