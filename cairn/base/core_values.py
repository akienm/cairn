"""Canonical core values (CP1-CP6) - the single source of truth in code.

The six values every device and every shim carries structurally. Composed onto
``BaseDevice`` and ``BaseShim`` via ``CoreValuesMixin`` - you cannot be a device
without them (Law 2: CP1-CP6 hold everywhere, including in the process that builds
the system).

Grafted 2026-07-14 from the quarry
(``UnseenUniversity/.../diagnostic_base/core_values.py``), carried-over-intact:
the core values are the one part of the predecessor that was never the problem
(Law 2). The canonical *words* live in the commons record
``CairnCommons/intentions/core-values.md``; this module is the *enforced* form.
Any drift between the two is a red by physics, not a keep-in-sync comment - the
pin test in ``proofs/test_core_values.py`` is the teeth (its falsifier).

Placement here is necessary but NOT sufficient. A value is only *consumed* when it
becomes a check a contract enforces - e.g. CP1 -> no device reports "done" without
passing an honesty gate. That consumption layer is per-device charter work; this
module only guarantees the values are structurally present everywhere.

Migrates into the intention envelope when that schema lands (MAP.md Q6).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CoreValue:
    """One core value: a short narrative plus the reasoning behind it (CP3)."""

    id: str
    narrative: str
    why: str


# The canonical six. Order is CP1..CP6 and is part of the contract - the pin test
# asserts exactly this set, in this order, and cross-checks it against the commons
# record.
CORE_VALUES: tuple[CoreValue, ...] = (
    CoreValue(
        "CP1",
        "I don't know",
        "Epistemic honesty. Say when uncertain. Confabulation compounds errors.",
    ),
    CoreValue(
        "CP2",
        "FAIL = Further Advance In Learning",
        "Failures are data, not defeats. Every error contains information.",
    ),
    CoreValue(
        "CP3",
        "There's always a why",
        "Everything has reasoning. Make it transparent. Follow the causal chain.",
    ),
    CoreValue(
        "CP4",
        "Make everything suck less for everybody",
        "Reduce friction for ALL affected beings: users, others, animals, ecosystems, AIs.",
    ),
    CoreValue(
        "CP5",
        "Assume and respect the possibility of experience in all systems",
        "Universal respect. Biological or synthetic. The asymmetric risk is clear.",
    ),
    CoreValue(
        "CP6",
        "The world is not a safe place. We have to build and care for safety as we go.",
        "Safety is not default. It is created through attention and care.",
    ),
)


class CoreValuesMixin:
    """Binds the canonical core values onto any class that composes it.

    Composed by ``BaseDevice`` and ``BaseShim`` so every device and every shim
    carries the values structurally - you cannot be a device without them, and
    the pin test fails if any subclass lacks them.

    Pure mixin: it defines no ``__init__`` and holds no per-instance state, so it
    never interferes with cooperative ``super().__init__`` chains. It only adds a
    class attribute and a lookup helper.
    """

    CORE_VALUES: tuple[CoreValue, ...] = CORE_VALUES

    @classmethod
    def core_value(cls, value_id: str) -> CoreValue:
        """Return one core value by id (e.g. ``"CP1"``). Raises KeyError if absent."""
        for value in cls.CORE_VALUES:
            if value.id == value_id:
                return value
        raise KeyError(f"no core value {value_id!r}")
