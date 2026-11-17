# 12 INTENTION EXTRACTOR DEVICE (cairn/devices/intention_extractor/)
- 12.1 PURPOSE: Turn raw design prose (a chat excerpt, a note) into a candidate
  intention: what, why, anchors, read.
- 12.2 WHY: CC is the most expensive resolver; moving extraction to a watchable
  stage a cheaper model can do lets it be measured and improved until it's
  settled.
- 12.3 INTENTION:
  - 12.3.1 The draft comes from the inference proxy; the judgment is deterministic
    (machine judge: the record has the right shape, and every anchor is
    really in the source).
  - 12.3.2 Its own device, and a future one. It will interview the user and ask
    questions to resolve ambiguity. Right now Claude does all that;
    eventually this device does it for us.
- 12.4 TOOLS: gate, bus_client, base; machine judge.
