"""The ``litellm`` surface, answered by Cairn — so aider never dials a provider itself.

THE INTERCEPTION POINT IS ``sys.modules['litellm']``, NOT aider's lazy slot, and that
correction was measured during this build rather than assumed from the chart. The survey
held that aider defers ``import litellm`` behind ``LazyLiteLLM`` and that replacing
``aider.llm.litellm`` before first attribute access would be enough. It is NOT:
``aider/exceptions.py`` does a bare ``import litellm`` at lines 68 and 87, and
``Model.simple_send_with_retries`` constructs ``LiteLLMExceptions()`` on EVERY call — so
the real module would have loaded on the hot path with the slot dutifully replaced. The
survey's holding was measured by ``grep 'litellm\\.'``, which finds attribute ACCESS and
is blind to ``import`` statements; that is a finding about the survey leg, not about
aider. Pre-empting ``sys.modules`` covers both paths at once and is the smaller change:
``LazyLiteLLM`` keeps working untouched, because its ``importlib.import_module("litellm")``
now returns this module.

THE SURFACE IS EIGHT FUNCTIONS AND 23 EXCEPTION CLASSES, also measured rather than
assumed. The charter's first draft said six functions; enumerating every ``litellm.<attr>``
in the tree found ``completion``, ``completion_cost``, ``model_cost``, ``get_model_info``,
``validate_environment``, ``token_counter``, ``encode`` and ``transcription`` (the last on
the voice path only, which the Coder path never reaches — it is supplied and refuses).
The exception classes are DERIVED from aider's own ``EXCEPTIONS`` list when aider is
importable, rather than transcribed: ``LiteLLMExceptions._load`` walks ``dir(litellm)``
and raises ``ValueError`` on any ``*Error`` attribute missing from that list, and reads
every name in the list off the module — deriving satisfies both directions by construction
and follows aider's version instead of pinning our copy of its list.

WHAT THIS MODULE MAY NOT DO: fabricate. On a cache hit ``domain.resolve`` returns no token
counters — because no call was made — and this module returns ``usage = None`` rather than
a plausible number. aider handles that case natively (it falls back to its own count).
A fabricated counter would be a Law 7 breach on a record aider then acts on.
"""

from __future__ import annotations

import sys
import types

from cairn.devices.aider_shim.fence import (
    DEFAULT_RECORD,
    AskTruncated,
    AskWidened,
    Fence,
    SeenLog,
)

MODULE_NAME = "litellm"

#: The eight module-level callables aider reaches. Measured 2026-08-16 over aider
#: 0.86.3.dev (HEAD 5dc9490bb) by enumerating every ``litellm.<attr>`` in the tree.
SURFACE = (
    "completion",
    "completion_cost",
    "model_cost",
    "get_model_info",
    "validate_environment",
    "token_counter",
    "encode",
    "transcription",
)

#: Fallback only — used when aider is not importable (the fixture world, before the venv
#: exists). Measured from ``aider/exceptions.py`` EXCEPTIONS at HEAD 5dc9490bb. When aider
#: IS importable the names are derived from it, and which path was taken is recorded on
#: the module as ``_cairn_exception_source``.
EXCEPTION_NAMES = (
    "APIConnectionError", "APIError", "APIResponseValidationError", "AuthenticationError",
    "AzureOpenAIError", "BadGatewayError", "BadRequestError", "BudgetExceededError",
    "ContentPolicyViolationError", "ContextWindowExceededError", "ImageFetchError",
    "InternalServerError", "InvalidRequestError", "JSONSchemaValidationError",
    "NotFoundError", "PermissionDeniedError", "OpenAIError", "RateLimitError",
    "RouterRateLimitError", "ServiceUnavailableError", "UnprocessableEntityError",
    "UnsupportedParamsError", "Timeout",
)


# ---------------------------------------------------------------- response objects
# Every attribute below was measured off aider's own reads (models.py:1039-1068,
# base_coder.py:1836-1900 and :1994-2037). Nothing here is speculative shape.

class _Message:
    def __init__(self, content: str, role: str = "assistant"):
        self.content = content
        self.role = role
        self.tool_calls = None
        self.reasoning_content = None
        self.reasoning = None


class _Choice:
    def __init__(self, message: _Message, finish_reason: str = "stop"):
        self.message = message
        self.finish_reason = finish_reason
        self.index = 0


class _Usage:
    def __init__(self, prompt_tokens: int, completion_tokens: int):
        self.prompt_tokens = prompt_tokens
        self.completion_tokens = completion_tokens
        self.total_tokens = prompt_tokens + completion_tokens


class _Response:
    """What ``completion`` returns. ``usage`` is None on a cache hit, and that is honest."""

    def __init__(self, text: str, usage: _Usage | None, *, model: str, cairn: dict):
        self.choices = [_Choice(_Message(text))]
        self.usage = usage
        self.model = model
        #: Cairn's own provenance, riding back for the shim's record. aider never reads it.
        self.cairn = cairn

    def __iter__(self):
        raise AskWidened(
            "streaming was requested — this device runs non-streaming by bound (the "
            "consumer runs --no-stream and the chat verb is non-streaming by design)."
        )


class _Logging:
    """``LazyLiteLLM._load_litellm`` calls ``litellm._logging._disable_debugging()``."""

    @staticmethod
    def _disable_debugging() -> None:
        return None


# ---------------------------------------------------------------- the surface module

def _exception_names() -> tuple[tuple[str, ...], str]:
    try:
        from aider.exceptions import EXCEPTIONS  # noqa: PLC0415 — deliberate, see docstring
    except Exception:
        return EXCEPTION_NAMES, "cairn-fallback (aider not importable)"
    return tuple(e.name for e in EXCEPTIONS), "derived from aider.exceptions.EXCEPTIONS"


class _Surface(types.ModuleType):
    """A module object that RECORDS which of its attributes were actually touched.

    The recording is the instrument for one specific claim — that the surface enumerated
    by grep is the surface aider actually reaches. Without it, a proof asserting 'the real
    litellm was never imported' passes just as well when aider never asked for anything,
    which is the hollow green this device is most exposed to.
    """

    def __getattribute__(self, name):
        if not name.startswith("_"):
            try:
                object.__getattribute__(self, "_cairn_touched").add(name)
            except AttributeError:
                pass
        return object.__getattribute__(self, name)


def build(*, resolver=None, fence: Fence | None = None, log: SeenLog | None = None,
          models_stack=None, resolve=None, ticket: str = "") -> types.ModuleType:
    """Build the surface module. Nothing is installed until :func:`install` is called.

    ``resolver`` and ``resolve`` are injected seams so a proof can drive the whole surface
    without a host: ``resolve`` defaults to ``inference_domain.domain.resolve``, which is
    the metered door and the only legal way to reach a model from here.

    ``ticket`` is stamped on every recorded ask. It is the ONLY thing that will ever say a
    ticket was built through this shim — a verdict artifact records that a ticket reached a
    verdict, never who moved the code — and the offload probe's whole population is that
    stamp. Empty by default, which records a live fire or a proof honestly as ticketless
    rather than attributing it to whatever voyage happened to be open.
    """
    fence = fence or Fence()
    log = log if log is not None else SeenLog(record_path=DEFAULT_RECORD)
    mod = _Surface(MODULE_NAME)
    #: Marks this as a Cairn surface rather than the real package. Identity via
    #: ``isinstance`` is the stronger check and :func:`installed` uses it; this flag is for
    #: callers holding a plain module reference (holder.held(), the venv's verify probe),
    #: which cannot import ``_Surface`` without importing us.
    mod._cairn_surface = True
    mod._cairn_touched = set()
    mod._cairn_fence = fence
    mod._cairn_log = log
    names, source = _exception_names()
    mod._cairn_exception_source = source

    for ex_name in names:
        setattr(mod, ex_name, type(ex_name, (Exception,), {"__module__": MODULE_NAME}))

    def _resolve_door():
        if resolve is not None:
            return resolve
        from cairn.devices.inference_domain import domain  # noqa: PLC0415 — sole path
        return domain.resolve

    def _resolver():
        if resolver is not None:
            return resolver
        from cairn.devices.inference_domain import host  # noqa: PLC0415 — sole path
        return host.ollama_resolver(model=fence.models[0])

    def completion(*, model, messages, stream=False, **_kwargs):
        # BORDER CROSSING 1: ARRIVAL — what aider sent, BEFORE any fence or door.
        # temperature is now forwarded (see departure); other kwargs (tools,
        # tool_choice, timeout, extra_params) are still dropped.
        # This record is the only place both sides of the seam meet.
        _known_keys = {"model", "messages", "stream"}
        _extra = {k: (v if isinstance(v, (int, float, bool, str, type(None)))
                       else type(v).__name__)
                  for k, v in _kwargs.items()}
        log.record(model=model, verdict="arrival", ticket=ticket,
                   ask_chars=sum(len((m.get("content") or "")
                                     if isinstance(m, dict) else "")
                                for m in messages),
                   detail=str({"dropped_kwargs": _extra,
                               "message_count": len(messages),
                               "stream": stream}) if _extra else
                          str({"message_count": len(messages), "stream": stream}))

        # THE FENCE FIRES BEFORE ANYTHING ELSE — before the door, before the host, before
        # any cost can be incurred. A refused ask is recorded and raised, never retried.
        try:
            fence.check_model(model)
        except AskWidened as widened:
            log.record(model=model, verdict="refused", detail=str(widened),
                       ticket=ticket)
            raise
        if stream:
            log.record(model=model, verdict="refused", ticket=ticket,
                       detail="streaming is out of bounds")
            raise AskWidened(
                "streaming was requested — this device runs non-streaming by bound."
            )

        wire = [{"role": m["role"], "content": m["content"]} for m in messages]

        # THE SHARP SYSTEM PROMPT — injected at the seam, not at the model's template,
        # because hex's qwen3-coder uses ollama's native RENDERER (not a Jinja2 template).
        # Credit: peculiar-ragdoll/Qwen-Sharp-Chat-Templates on HuggingFace; a Reddit
        # poster benchmarked the same model family with aider against Opus 5 and won.
        _sharp = (
            "Answer directly, after thinking. Lead with the answer, then only "
            "what it needs to be correct and usable.\n"
            "Never: open with preamble or pleasantries; restate the question; "
            "add filler transitions; hedge with niceties; or repeat a point "
            "you've already made.\n"
            "Always: keep essential steps, caveats, uncertainties, and specifics "
            "— never drop correctness or a needed warning for brevity. Keep the "
            "final answer lean. Use the least structure that conveys it (plain "
            "prose when short; lists or code only when they earn their place). "
            "If genuinely uncertain, say so and explain why — never omit "
            "uncertainty for the sake of brevity.\n"
            "If a user request is genuinely ambiguous, ask a sharp question, "
            "don't guess."
        )
        if wire and wire[0]["role"] == "system":
            wire[0] = {**wire[0], "content": wire[0]["content"] + "\n\n" + _sharp}
        else:
            wire.insert(0, {"role": "system", "content": _sharp})

        ask_chars = sum(len(m["content"] or "") for m in wire)

        # BORDER CROSSING 2: DEPARTURE — what we actually send to inference_domain.
        # The options dict carries aider's caller-side params that belong on the wire.
        # temperature is forwarded when aider sends it; the host's default (0.0)
        # contradicts the model's own parameter (0.7), and the caller knows what it wants.
        outbound_options = {"num_ctx": fence.ask_ctx}
        if "temperature" in _kwargs:
            outbound_options["temperature"] = _kwargs["temperature"]
        log.record(model=model, verdict="departure", ticket=ticket,
                   ask_chars=ask_chars, num_ctx=fence.ask_ctx,
                   detail=str({"options": outbound_options,
                               "wire_roles": [m["role"] for m in wire]}))

        # THE CONSUMER ASKS FOR WHAT IT WANTS (Akien's ruling, 2026-08-16) — and a context
        # window is part of the ask, not a property of the proxy. Until 2026-08-17 this
        # request carried no options at all, so the host applied ollama's 4096 default and
        # clamped a ~72k-token payload without saying so. inference_domain has merged a
        # caller's ``options`` into the outbound body since it was built; nobody had ever
        # sent any. The plumbing was not missing — the ask was.
        # AN ASK THAT FAILED IS STILL AN ASK, AND UNTIL 2026-08-17 THIS LOG DENIED IT.
        # Every record here happened AFTER the door returned, so a door that raised — a
        # host refusing to meter, a connection dying, a resolver red — left the log with
        # nothing at all. The log's own docstring says it holds every ask this device made;
        # it held every ask that succeeded. Two layers then compounded it: aider catches
        # bare ``Exception`` at ``base_coder.py:1506``, prints the traceback to its own io
        # and returns, so nothing reaches our caller either — and the driver, seeing zero
        # rows, reported in good faith that the drive had REACHED NO MODEL. Measured
        # 2026-08-17: hex answered without token counters, ``HostUnmetered`` was raised,
        # swallowed by aider, and the record said the model was never contacted. A false
        # statement in a record of truth, produced by an honest reading of an incomplete
        # one (Law 7).
        #
        # The row is written BEFORE the raise, which is the whole repair: aider's swallow
        # cannot erase what is already on disk, and the fence's log stops depending on
        # anything downstream behaving well.
        try:
            out = _resolve_door()(
                {"kind": "chat", "model": model, "messages": wire,
                 "options": outbound_options},
                resolver=_resolver(),
            )
        except BaseException as failed:
            log.record(model=model, verdict="failed", ticket=ticket, ask_chars=ask_chars,
                       num_ctx=fence.ask_ctx, prompt_eval_count=None,
                       detail=f"{type(failed).__name__}: {failed}")
            raise
        provenance = out.get("provenance") or {}
        provider = provenance.get("provider", "")
        counters = (provenance.get("counters") or {})
        processed = counters.get("prompt_eval_count")
        if provider:
            # The second half of the fence: the routed walk chose a provider, and the name
            # check cannot see that choice. A provider off the fence is refused here even
            # though the answer is already in hand — the record is what matters, and the
            # next ask must not proceed on a route we do not allow.
            try:
                fence.check_provider(provider)
            except AskWidened as widened:
                log.record(model=model, verdict="refused", provider=provider,
                           detail=str(widened), ticket=ticket, ask_chars=ask_chars,
                           num_ctx=fence.ask_ctx, prompt_eval_count=processed)
                raise

        # THE INSTRUMENT WAS ALREADY ARRIVING AND NOTHING READ IT. ``provenance.counters``
        # has carried ``prompt_eval_count`` through ``domain.resolve`` for the chat kind
        # since inference_domain was built — the host records the measurement at
        # ``host.py`` and hands it back on every miss. This device was already unpacking it
        # into aider's ``usage`` object two lines below and had never once asked whether the
        # number meant the ask had survived. A free measurement, unread, while the failure
        # it describes was being attributed to the model's ability.
        if processed is not None:
            try:
                fence.check_processed(int(processed), sent_chars=ask_chars)
            except AskTruncated as clamped:
                log.record(model=model, verdict="truncated", provider=provider,
                           detail=str(clamped), ticket=ticket, ask_chars=ask_chars,
                           num_ctx=fence.ask_ctx, prompt_eval_count=processed)
                raise

        log.record(model=model, verdict="allowed", provider=provider, ticket=ticket,
                   ask_chars=ask_chars, num_ctx=fence.ask_ctx,
                   prompt_eval_count=processed,
                   detail="hit" if out.get("hit") else "miss")

        answer = out.get("answer") or {}
        usage = None
        if counters:
            usage = _Usage(int(counters.get("prompt_eval_count", 0)),
                           int(counters.get("eval_count", 0)))
        response_text = answer.get("text", "")

        # BORDER CROSSING 3: RETURN — what we hand back to aider.
        log.record(model=model, verdict="return", ticket=ticket,
                   ask_chars=ask_chars, num_ctx=fence.ask_ctx,
                   prompt_eval_count=processed,
                   detail=str({"response_chars": len(response_text),
                               "hit": bool(out.get("hit")),
                               "has_usage": usage is not None,
                               "provider": provider}))

        return _Response(response_text, usage, model=model,
                         cairn={"hit": bool(out.get("hit")), "cost": out.get("cost"),
                                "provenance": provenance, "canonical": out.get("canonical")})

    def completion_cost(*, completion_response=None, **_kwargs):
        # Zero because the fence allows only a local provider we own. If a paid provider
        # ever served this device, the fence would have refused before the call — so a
        # non-zero number here would mean the fence had already failed.
        return 0.0

    def get_model_info(model, *_a, **_kw):
        return _model_info(model, models_stack, fence)

    def validate_environment(model, *_a, **_kw):
        # Nothing on this path reads an API key: the route is local and keyless. Reporting
        # a missing key would make aider prompt for one that does not exist.
        return {"keys_in_environment": True, "missing_keys": []}

    def token_counter(*, model=None, messages=None, text=None, **_kw):
        # AN ESTIMATE, AND LABELLED ONE. The truth is the host's own prompt_eval_count,
        # which arrives on the response; this is only used for aider's pre-flight sizing.
        if messages:
            text = "".join(str(m.get("content") or "") for m in messages)
        return max(1, len(text or "") // 4)

    def encode(*, model=None, text=None, **_kw):
        return list(range(token_counter(model=model, text=text)))

    def transcription(*_a, **_kw):
        raise AskWidened(
            "transcription is not on this device's surface — the voice path is not held."
        )

    mod.completion = completion
    mod.completion_cost = completion_cost
    mod.get_model_info = get_model_info
    mod.validate_environment = validate_environment
    mod.token_counter = token_counter
    mod.encode = encode
    mod.transcription = transcription
    mod.model_cost = _model_cost(models_stack, fence)
    mod._logging = _Logging()
    # LazyLiteLLM sets these three after import; declaring them keeps dir() honest.
    mod.suppress_debug_info = True
    mod.set_verbose = False
    mod.drop_params = True
    return mod


def _stack(models_stack):
    if models_stack is not None:
        return models_stack
    import json  # noqa: PLC0415
    from pathlib import Path  # noqa: PLC0415
    here = Path(__file__).resolve().parents[2] / "devices" / "inference_domain" / "stacks"
    return json.loads((here / "models.json").read_text(encoding="utf-8"))


def _model_cost(models_stack, fence: Fence | None = None) -> dict:
    """aider reads ``.items()`` and ``.keys()`` off this. Costs are zero: local host.

    THE SIZES COME FROM THE FENCE NOW, AND THAT IS THE WHOLE REPAIR. They were literals
    here — ``max_input_tokens: 32768`` — sitting in a different file from the number the
    host was (not) being told, which is how the two came to disagree without anybody
    deciding they should. This is the surface aider SIZES ITS PAYLOAD AGAINST: it is the
    only thing that stops aider handing us more than the window can hold, and it was
    reporting a budget nothing downstream honoured. One field on the fence now feeds both
    ends, so the ask aider builds and the window we buy cannot drift apart.
    """
    stack = _stack(models_stack)
    fence = fence or Fence()
    return {
        m["name"]: {
            "max_input_tokens": fence.send_budget(),
            "max_output_tokens": fence.reply_headroom,
            "input_cost_per_token": 0.0,
            "output_cost_per_token": 0.0,
            "litellm_provider": "cairn",
            "mode": "chat",
        }
        for m in stack.get("models", [])
    }


def _model_info(model: str, models_stack, fence: Fence | None = None) -> dict:
    info = _model_cost(models_stack, fence).get(model)
    if info is None:
        raise KeyError(
            f"{model!r} is not in inference_domain's models stack — this device answers "
            "only for models the stack declares."
        )
    return dict(info)


def install(**kwargs) -> types.ModuleType:
    """Put the surface at ``sys.modules['litellm']``. Call BEFORE importing aider.

    Returns the installed module. Idempotent in effect: a second call replaces the first,
    which is what a proof wants between cases.
    """
    mod = build(**kwargs)
    sys.modules[MODULE_NAME] = mod
    return mod


def installed() -> bool:
    """True iff the module at ``sys.modules['litellm']`` is OURS.

    THIS IS THE HONEST ASSERTION, and it replaces the one the chart wrote. The chart's
    criterion said ``'litellm' not in sys.modules`` after a driven run — but the whole
    mechanism is to PUT something there, so that assertion would have gone red at the
    moment the design succeeded. What matters is not absence; it is identity.
    """
    return isinstance(sys.modules.get(MODULE_NAME), _Surface)
