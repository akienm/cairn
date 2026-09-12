"""The wire translation between the OpenAI chat-completions shape and the shape a
provider-side answerer (ollama's /api/chat, measured) speaks — stdlib only, dicts
in, dicts out, nothing dialed. Lifted from the measured source
CairnCommons/measurements/2026-09-11-hermes-openai-door-spike.py (ticket
76639374d9f9), where each translation was proved on the wire against hermes-agent
0.21.1 before it was named here.

Two directions and an envelope:

  to_provider(messages)  — OpenAI carries tool-call arguments as a JSON STRING;
                           the provider wants an OBJECT and refuses the string with
                           "Value looks like object, but can't find closing '}'
                           symbol" (measured 2026-09-11, hex.local, qwen3-coder:30b,
                           second turn of a tool-using conversation). null content
                           becomes "".
  to_openai(answer)      — the provider returns tool calls as
                           {"function": {"name", "arguments": <dict>}}; the OpenAI
                           shape needs an id, a type, and arguments as a STRING.
  completion(answer, model, usage) — the chat.completion envelope around one
                           to_openai message, finish_reason derived from whether
                           tool calls are present.
"""
import json
import time
import uuid


def to_provider(messages):
    """OpenAI-shaped messages -> provider-shaped messages. Pure: returns new dicts,
    never mutates the input. An argument string that is not JSON is kept, not
    dropped — under "_unparsed" — so the provider sees that something was said
    (Law 7: the error stays loud rather than collapsing to {})."""
    out = []
    for m in messages:
        m = dict(m)
        calls = m.get("tool_calls")
        if calls:
            fixed = []
            for c in calls:
                c = dict(c)
                fn = dict(c.get("function") or {})
                args = fn.get("arguments")
                if isinstance(args, str):
                    try:
                        fn["arguments"] = json.loads(args) if args.strip() else {}
                    except Exception:
                        fn["arguments"] = {"_unparsed": args}
                c["function"] = fn
                fixed.append(c)
            m["tool_calls"] = fixed
        if m.get("content") is None:
            m["content"] = ""
        out.append(m)
    return out


def _arguments_as_string(fn):
    args = fn.get("arguments")
    if isinstance(args, (dict, list)):
        return json.dumps(args)
    return str(args if args is not None else "")


def to_openai(answer):
    """Provider-shaped answer {"text", "role", "tool_calls"} -> one OpenAI
    assistant message. Empty text becomes null content, which is what the
    OpenAI shape carries beside tool calls."""
    msg = {"role": answer.get("role", "assistant"), "content": answer.get("text", "") or None}
    calls = answer.get("tool_calls") or []
    if calls:
        msg["tool_calls"] = [{
            "id": "call_" + uuid.uuid4().hex[:20],
            "type": "function",
            "function": {"name": (c.get("function") or {}).get("name", ""),
                         "arguments": _arguments_as_string(c.get("function") or {})},
        } for c in calls]
    return msg


def completion(answer, model, usage=None):
    """The chat.completion envelope around one answer. `usage` is the holder's
    count as {"prompt_tokens", "completion_tokens"}; absent counts read 0, never
    invented."""
    usage = dict(usage or {})
    prompt = int(usage.get("prompt_tokens", 0) or 0)
    done = int(usage.get("completion_tokens", 0) or 0)
    return {
        "id": "chatcmpl-" + uuid.uuid4().hex[:24],
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0,
                     "finish_reason": "tool_calls" if answer.get("tool_calls") else "stop",
                     "message": to_openai(answer)}],
        "usage": {"prompt_tokens": prompt, "completion_tokens": done,
                  "total_tokens": prompt + done},
    }
