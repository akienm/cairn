"""openai_wire — the OpenAI chat-completions wire shape as a machine anybody can
include: a pure translation (translate) and an HTTP face with its answerers
injected (serve). It imports no device; the holder brings the answerer.
Charter: intention+why.json beside this file."""
from cairn.machines.openai_wire import translate
from cairn.machines.openai_wire.serve import make_handler, make_server, STREAM_GAP

__all__ = ["translate", "make_handler", "make_server", "STREAM_GAP"]
