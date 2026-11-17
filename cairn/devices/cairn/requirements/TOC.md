# Cairn requirements: the schematic

What Cairn is: how every part works, and why. Built or not does not matter here; the code
catches up to this, never the reverse. One file per section, numbered as the outline is
numbered; refer to any line by its number ("5.5.3"). `cairn outlinecheck` reads every
`NN-*.md` here, in filename order, as one outline.

- [00-how-to-read-this.md](00-how-to-read-this.md): how to read these files: whys, whos, confidence, signing, questions, entry shape
- [01-the-rungs.md](01-the-rungs.md): what every component is: tool, machine, device, instance
- [02-device.md](02-device.md): the device, a top level Cairn entity
- [03-ticket.md](03-ticket.md): the ticket: a unit of work, its kinds and its plan
- [04-graph-trees-memory-service.md](04-graph-trees-memory-service.md): graph trees: where Cairn keeps what it knows
- [05-cairn-device.md](05-cairn-device.md): the cairn device: launcher, bus, ground loop, rack, shims
- [06-recovery-device.md](06-recovery-device.md): recovery: the host, install, upgrades, Rescue, troubles
- [07-operator-device.md](07-operator-device.md): the operator: command-line access to the bus
- [08-librarian-device.md](08-librarian-device.md): the librarian: owns what Cairn knows
- [09-codemother-device.md](09-codemother-device.md): CodeMother: looks after the codebase; its machines and verbs
- [10-cc-device.md](10-cc-device.md): CC: Claude Code as an external device
- [11-proxy-devices.md](11-proxy-devices.md): proxies: the one way to a service (database, inference)
- [12-intention-extractor-device.md](12-intention-extractor-device.md): the intention extractor: design prose to candidate intentions
- [13-aider-device.md](13-aider-device.md): aider: a cheap coder types what CC designed
- [14-embeddings-device.md](14-embeddings-device.md): embeddings: structural embeddings by walking the trees
- [15-web-server-device.md](15-web-server-device.md): the web server: the one web surface
- [16-shared-machines.md](16-shared-machines.md): shared machines several devices hold
- [17-tools.md](17-tools.md): tools: the general collection, one entry each
- [18-press-office.md](18-press-office.md): the press office: explaining Cairn to others
