"""Proofs for the HTTP face of openai_wire (clauses c and d of the falsifier, and
the no-device half of clause a). The handler is driven against a fake socket —
make_server is never called, no port is bound — and every tooth asserts on the
bytes the handler wrote. A hollow handler that answered 200 {} to everything
fails the envelope, the 5xx, the refusal and the 404 teeth alike.

Provenance: ticket 76639374d9f9.
"""
import io
import json
import sys
import threading
import urllib.request
from pathlib import Path

from cairn.machines.openai_wire import make_handler, make_server, STREAM_GAP
from cairn.tools.import_sieve.sieve import imports_in

PASS = 0
FAIL = 0
HERE = Path(__file__).resolve().parent.parent

# Clause (e) is the holder's clause, and this proof plays the holder: the resolve it injects
# is a SCRIPTED stand-in for "ask inference_domain over the bus" (a netns seal can reach no
# bus), and what the tooth proves is that the machine carries a whole tool-using turn end to
# end through a real listener. The REAL holder is ticket cb97524c0e8e's; the live fire in
# this voyage's verdict artifact is where a real model answered through this same door.
PROVES = {
    "76639374d9f9": {
        "a": "the_machine_imports_no_device",
        "c": "a_raising_resolve_is_a_named_5xx_not_an_empty_answer",
        "d": "stream_true_is_refused_with_the_reason_on_the_wire",
        "e": "a_holder_serves_a_tool_using_turn_end_to_end_through_a_real_listener",
    },
}


def _tooth(name, fn):
    global PASS, FAIL
    try:
        fn()
    except Exception as exc:
        FAIL += 1
        print(f"  RED   {name}: {type(exc).__name__}: {exc}")
        return
    PASS += 1
    print(f"  green {name}")


class _FakeSocket:
    """What BaseHTTPRequestHandler needs from a connection and nothing more."""

    def __init__(self, raw: bytes):
        self._in = io.BytesIO(raw)
        self.out = io.BytesIO()

    def makefile(self, mode, *a, **k):
        return self._in

    def sendall(self, data):
        self.out.write(data)

    def close(self):
        pass


def _drive(handler, method, path, body=None):
    payload = b"" if body is None else json.dumps(body).encode()
    raw = (f"{method} {path} HTTP/1.1\r\nHost: t\r\nContent-Length: {len(payload)}\r\n"
           f"Connection: close\r\n\r\n").encode() + payload
    sock = _FakeSocket(raw)
    handler(sock, ("127.0.0.1", 0), None)
    head, _, tail = sock.out.getvalue().partition(b"\r\n\r\n")
    status = int(head.split(b" ")[1])
    headers = dict(line.decode().split(": ", 1) for line in head.split(b"\r\n")[1:])
    assert headers.get("Content-Type") == "application/json", headers
    assert int(headers["Content-Length"]) == len(tail), (headers, tail)
    return status, json.loads(tail)


def _handler(resolve=None, models=None):
    return make_handler(resolve=resolve or (lambda req: {"text": "alive", "role": "assistant", "tool_calls": []}),
                        models=models or (lambda: ["m1", "m2"]))


def models_lists_what_the_injected_callable_says():
    status, out = _drive(_handler(), "GET", "/v1/models")
    assert status == 200, (status, out)
    assert out["object"] == "list" and [d["id"] for d in out["data"]] == ["m1", "m2"], out
    assert all(d["object"] == "model" for d in out["data"]), out


def completion_carries_the_envelope_from_the_injected_resolve():
    seen = {}

    def resolve(req):
        seen.update(req)
        return {"text": "alive", "role": "assistant", "tool_calls": [],
                "usage": {"prompt_tokens": 4, "completion_tokens": 1}, "extra": {"hit": False}}

    body = {"model": "m1", "messages": [{"role": "user", "content": "hi"}],
            "tools": [{"type": "function", "function": {"name": "f"}}], "temperature": 0.5}
    status, out = _drive(_handler(resolve=resolve), "POST", "/v1/chat/completions", body)
    assert status == 200, (status, out)
    assert seen == {"model": "m1", "messages": body["messages"], "tools": body["tools"], "temperature": 0.5}, seen
    assert out["object"] == "chat.completion" and out["model"] == "m1", out
    assert out["choices"][0]["message"] == {"role": "assistant", "content": "alive"}, out
    assert out["choices"][0]["finish_reason"] == "stop", out
    assert out["usage"] == {"prompt_tokens": 4, "completion_tokens": 1, "total_tokens": 5}, out
    assert out["x_cairn"] == {"hit": False}, out


def tool_calls_come_back_openai_shaped():
    def resolve(req):
        return {"text": "", "tool_calls": [{"function": {"name": "read_file", "arguments": {"path": "a"}}}]}
    status, out = _drive(_handler(resolve=resolve), "POST", "/v1/chat/completions",
                         {"model": "m", "messages": [{"role": "user", "content": "go"}]})
    assert status == 200, out
    msg = out["choices"][0]["message"]
    assert out["choices"][0]["finish_reason"] == "tool_calls", out
    assert msg["content"] is None and isinstance(msg["tool_calls"][0]["function"]["arguments"], str), msg


def a_raising_resolve_is_a_named_5xx_not_an_empty_answer():
    class HostRefused(Exception):
        pass

    def resolve(req):
        raise HostRefused("hex.local said no")
    status, out = _drive(_handler(resolve=resolve), "POST", "/v1/chat/completions",
                         {"model": "m", "messages": [{"role": "user", "content": "hi"}]})
    assert status == 502, (status, out)
    assert out["error"]["type"] == "cairn_resolve_error", out
    assert "HostRefused" in out["error"]["message"] and "hex.local said no" in out["error"]["message"], out
    assert "choices" not in out, "a failed resolve must never wear a completion's shape"


def a_resolve_returning_garbage_is_a_named_5xx():
    status, out = _drive(_handler(resolve=lambda req: "not a dict"), "POST", "/v1/chat/completions",
                         {"model": "m", "messages": []})
    assert status == 502 and out["error"]["type"] == "cairn_resolve_error", (status, out)
    assert "str" in out["error"]["message"], out


def stream_true_is_refused_with_the_reason_on_the_wire():
    called = []
    status, out = _drive(_handler(resolve=lambda req: called.append(req)), "POST", "/v1/chat/completions",
                         {"model": "m", "messages": [{"role": "user", "content": "hi"}], "stream": True})
    assert status == 400, (status, out)
    assert out["error"]["type"] == "cairn_stream_gap" and out["error"]["message"] == STREAM_GAP, out
    assert called == [], "a refused request must never reach the answerer"


def unknown_paths_are_named_404s():
    for method, body in (("GET", None), ("POST", {"messages": []})):
        status, out = _drive(_handler(), method, "/v1/embeddings", body)
        assert status == 404 and out["error"]["type"] == "cairn_no_route", (method, status, out)
        assert "/v1/embeddings" in out["error"]["message"], out


def a_body_without_messages_is_a_named_400():
    status, out = _drive(_handler(), "POST", "/v1/chat/completions", {"model": "m"})
    assert status == 400 and out["error"]["type"] == "cairn_bad_request", (status, out)


def a_raising_models_is_a_named_5xx():
    def models():
        raise RuntimeError("no host")
    status, out = _drive(_handler(models=models), "GET", "/v1/models")
    assert status == 502 and out["error"]["type"] == "cairn_models_error", (status, out)
    assert "RuntimeError" in out["error"]["message"], out


def make_server_is_a_separate_door():
    assert callable(make_server)
    assert make_server.__module__ == "cairn.machines.openai_wire.serve"


def a_holder_serves_a_tool_using_turn_end_to_end_through_a_real_listener():
    """The holder's side, scripted: turn 1 asks with a tool and gets a tool call back; turn 2
    carries the tool result (arguments as a JSON STRING, as an OpenAI client sends them) and
    gets the final text. Both turns ride a real ThreadingHTTPServer on an ephemeral loopback
    port — make_server's own door — and the resolve sees provider-shaped arguments (objects)
    only because the holder ran translate.to_provider, which is the holder's job."""
    from cairn.machines.openai_wire import translate
    turns = []

    def bus_ask(request):                     # stands in for: ask inference_domain over the bus
        msgs = translate.to_provider(request["messages"])
        turns.append(msgs)
        if msgs[-1]["role"] == "tool":
            return {"text": f"the file holds {msgs[-1]['content']}", "role": "assistant",
                    "tool_calls": [], "usage": {"prompt_tokens": 9, "completion_tokens": 4}}
        return {"text": "", "role": "assistant",
                "tool_calls": [{"function": {"name": "read_file", "arguments": {"path": "a.py"}}}],
                "usage": {"prompt_tokens": 7, "completion_tokens": 3}}

    srv = make_server(_handler(resolve=bus_ask, models=lambda: ["m"]), "127.0.0.1", 0)
    port = srv.server_address[1]
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    try:
        def post(body):
            req = urllib.request.Request(f"http://127.0.0.1:{port}/v1/chat/completions",
                                         data=json.dumps(body).encode(),
                                         headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=5) as r:
                return json.loads(r.read())
        tools = [{"type": "function", "function": {"name": "read_file",
                                                   "parameters": {"type": "object"}}}]
        history = [{"role": "user", "content": "what is in a.py?"}]
        first = post({"model": "m", "messages": history, "tools": tools})
        msg = first["choices"][0]["message"]
        assert first["choices"][0]["finish_reason"] == "tool_calls", first
        call = msg["tool_calls"][0]
        assert json.loads(call["function"]["arguments"]) == {"path": "a.py"}, call
        history += [msg, {"role": "tool", "tool_call_id": call["id"], "content": "print(1)"}]
        second = post({"model": "m", "messages": history, "tools": tools})
        assert second["choices"][0]["finish_reason"] == "stop", second
        assert second["choices"][0]["message"]["content"] == "the file holds print(1)", second
        assert second["usage"]["total_tokens"] == 13, second
        listed = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/v1/models", timeout=5).read())
        assert [d["id"] for d in listed["data"]] == ["m"], listed
    finally:
        srv.shutdown()
        srv.server_close()
    assert len(turns) == 2, turns
    assert turns[1][1]["tool_calls"][0]["function"]["arguments"] == {"path": "a.py"}, \
        "the provider must see the tool-call arguments as an OBJECT on turn two"
    assert turns[1][1]["content"] == "", "null content must reach the provider as ''"


def the_machine_imports_no_device():
    for name in ("serve.py", "__init__.py", "translate.py"):
        found = imports_in((HERE / name).read_text(encoding="utf-8"))
        devices = sorted(m for m in found if m.startswith("cairn.devices"))
        assert not devices, (name, devices)


TEETH = [
    models_lists_what_the_injected_callable_says,
    completion_carries_the_envelope_from_the_injected_resolve,
    tool_calls_come_back_openai_shaped,
    a_raising_resolve_is_a_named_5xx_not_an_empty_answer,
    a_resolve_returning_garbage_is_a_named_5xx,
    stream_true_is_refused_with_the_reason_on_the_wire,
    unknown_paths_are_named_404s,
    a_body_without_messages_is_a_named_400,
    a_raising_models_is_a_named_5xx,
    make_server_is_a_separate_door,
    a_holder_serves_a_tool_using_turn_end_to_end_through_a_real_listener,
    the_machine_imports_no_device,
]

if __name__ == "__main__":
    for tooth in TEETH:
        _tooth(tooth.__name__, tooth)
    print(f"\n{PASS} passed, {FAIL} failed out of {PASS + FAIL}")
    sys.exit(1 if FAIL else 0)
