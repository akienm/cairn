"""chart_ticket.py <spec.json> — run the seven chart stages for one ticket from a spec, depositing each.

Spec keys: ticket, request, intent, scope, unknowns (extra, appended to floor's), constraints [{text,source,kind}],
bounds {in,out}, sought [..], holdings [{what,address}], absences [{what,measure}],
pieces [{what,why,kind,fills,uses,writes_to,why_now,expect,falsifier,instrument}],
criteria [{claim,instrument,timeout_s?}]  (each criterion covers every piece).
Prints the berth of each stage; the last line is the validate berth.
"""
import json, subprocess, sys

spec = json.load(open(sys.argv[1]))
T = spec["ticket"]


def learn(b):
    subprocess.run([sys.executable, "-m", "skills.chart.live", "learn", b], check=True, capture_output=True)
    print(b, flush=True)


from cairn.devices.codemother.machines.orient.orient import floor_packet, write_packet
fp = floor_packet(spec["request"])
unk = fp["unknowns"]
if spec.get("unknowns"):
    unk = list(unk or []) + spec["unknowns"]
o = write_packet({"request": spec["request"], "intent": spec["intent"], "domain": fp["domain"],
                  "scope": spec["scope"], "refs": fp["refs"], "unknowns": unk if unk is not None else [],
                  "ticket": T, "confidence": 0.85,
                  "provenance": {"intent": "claude", "scope": "claude"}})
learn(o)
from cairn.devices.codemother.machines.constrain.constrain import write_constrain
c = write_constrain({"intent_ref": o, "ticket": T, "constraints": spec["constraints"], "bounds": spec["bounds"],
                     "unknowns": [], "confidence": 0.85, "provenance": {"intent_ref": "floor", "bounds": "claude"}})
learn(c)
from cairn.devices.codemother.machines.survey.survey import write_survey
s = write_survey({"constrain_ref": c, "ticket": T, "sought": spec["sought"], "holdings": spec["holdings"],
                  "absences": spec["absences"], "unknowns": [], "confidence": 0.85,
                  "provenance": {"constrain_ref": "floor", "sought": "claude", "holdings": "claude",
                                 "absences": "claude", "unknowns": "claude"}})
learn(s)
P = spec["pieces"]
from cairn.devices.codemother.machines.decompose.decompose import write_decompose
d = write_decompose({"survey_ref": s, "ticket": T, "sub_problems": [
    {k: p[k] for k in ("what", "why", "kind", "fills", "uses", "writes_to")} for p in P],
    "unknowns": [], "confidence": 0.85,
    "provenance": {"survey_ref": "floor", "sub_problems": "claude", "unknowns": "claude"}})
learn(d)
from cairn.devices.codemother.machines.triage.triage import write_triage
t = write_triage({"decompose_ref": d, "ticket": T, "order": [{"what": p["what"], "why_now": p["why_now"]} for p in P],
                  "unknowns": [], "confidence": 0.85,
                  "provenance": {"decompose_ref": "floor", "order": "claude", "unknowns": "claude"}})
learn(t)
from cairn.devices.codemother.machines.hypothesize.hypothesize import write_hypothesize
h = write_hypothesize({"triage_ref": t, "ticket": T, "hypotheses": [
    {"piece": p["what"], "expect": p["expect"], "falsifier": p["falsifier"], "instrument": p["instrument"]} for p in P],
    "unknowns": [], "confidence": 0.85,
    "provenance": {"triage_ref": "floor", "hypotheses": "claude", "unknowns": "claude"}})
learn(h)
from cairn.devices.codemother.machines.validate.validate import write_validate
v = write_validate({"hypothesize_ref": h, "ticket": T, "criteria": [
    dict(c_, covers=[p["what"] for p in P]) for c_ in spec["criteria"]],
    "unknowns": [], "confidence": 0.85,
    "provenance": {"hypothesize_ref": "floor", "criteria": "claude", "unknowns": "claude"}})
learn(v)
