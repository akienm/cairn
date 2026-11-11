import sys
# Kept in class-space 2026-11-09 (from ~/.cairn/devices/cc/0/scratch-keep/2026-11-05): cross a ticket through clearance.clear (codemother/machines/clearance) and write the cursor back through the ticket door.
from cairn.tools.base import ticket_file, transitions
from cairn.tools.base.cross import charter_dir
from cairn.devices.codemother.machines.clearance.clearance import clear
ID, TARGET, WHY = sys.argv[1], sys.argv[2], sys.argv[3]
proven = sys.argv[4:] or None
tp = ticket_file.plans_of(ID, ticket_file._TICKETS)[0]; t = ticket_file.read_ticket(tp)
dev = charter_dir(t['owning_intention'], transitions._REPO_ROOT, ticket_file._TICKETS.parent)
kw = dict(actor='CC', boat_id=ID, history_path=str(dev/'history.json'), state_path=str(dev/'state.json'), ticket=ID, why=WHY)
kw['proven_by'] = proven
new = clear(t['workflow_and_state'], TARGET, **kw)
print(new)
t2 = ticket_file.read_ticket(tp)
if t2['workflow_and_state'] != new:
    t2['workflow_and_state'] = new; ticket_file.rewrite_ticket(tp, t2, verb='cast', why=WHY)
    print('ticket written')
