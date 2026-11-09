"""verdict_ticket.py <spec.json> — write and deposit the verdict for a charted ticket.

Spec: {ticket, verdicts: [{claim, instrument, outcome, evidence, discriminating_observation, timeout_s?}],
       by: "<the deciding observation for every hypothesis>" | {piece_prefix: by}}
Reads the ticket's standing chain (validate + hypothesize) itself; prints the verdict berth.
"""
import json, subprocess, sys
sys.path.insert(0, "/home/akien/dev/src/cairn")
from cairn.devices.codemother.machines.verdict.verdict import write_verdict

spec = json.load(open(sys.argv[1]))
T = spec["ticket"]
out = subprocess.run([sys.executable, "-m", "skills.chart.live", "chain", T], capture_output=True,
                     text=True, check=True, cwd="/home/akien/dev/src/cairn").stdout
chain = json.loads(out[out.index("{"):])
chain = chain.get("chain", chain)
HB = json.load(open(chain["hypothesize"]))
by = spec["by"]
disp = []
for h in HB["hypotheses"]:
    b = by if isinstance(by, str) else next(v for k, v in by.items() if h["piece"].startswith(k))
    disp.append({"piece": h["piece"], "expect": h["expect"], "disposition": "confirmed", "by": b})
v = write_verdict({"ticket": T, "validate_ref": chain["validate"], "verdicts": spec["verdicts"],
                   "dispositions": disp})
print(v)
subprocess.run([sys.executable, "-m", "skills.chart.live", "learn", v], check=True, capture_output=True,
               cwd="/home/akien/dev/src/cairn")
