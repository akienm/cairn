# 13 AIDER DEVICE (cairn/devices/aider/)
- 13.1 PURPOSE: Hold aider, so a cheap coder model types the code CC has already
  settled.
- 13.2 WHY: Every line is typed by the most expensive model, including lines whose
  shape was settled three chart stages earlier. That typing is transcription,
  which a 30B coder model on the local GPU box can do. Standing goal: "Claude
  has an assistant"; build until it works.
- 13.3 INTENTION:
  - 13.3.1 An external device (5.8.3.7.2): aider is a program we don't control; the
    shim adapts it.
  - 13.3.2 Every model call aider makes goes through the inference proxy.
- 13.4 TOOLS: base, chain, bus_client; db client; machine openai_wire: speaks
  OpenAI's wire format to the inference proxy, in the shim, per 5.8.3.8.
- 13.5 Builders are a family: anything that adapts every builder to Cairn goes in a
  base builder shim class shared by cc, aider, hermes and the rest; a base
  class, not a device. What adapts one builder stays in that builder's device.
