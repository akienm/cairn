"""THE DEPRECATION REPORT, run from the clearance gate's own address.

    python3 -m cairn.devices.codemother.machines.clearance <intention-address>
"""

from __future__ import annotations

import sys


def _retirement_report(intention: str) -> int:
    """THE DEPRECATION REPORT — print who rides one intention, and what the read could not see.

    Composes ``clearance.riders_of`` and prints it. There is deliberately NO arithmetic here:
    every integer below is one the library already returned, so the printed answer and the
    programmatic answer cannot drift (Law 7 — a presentation surface may arrange, it may not
    compute a second version of the truth).

    It moved here from the harbor register's ``__main__`` with the gate it reads (ticket
    0be964512fb0): the report composes the clearance library and nothing of the harbor.

        python3 -m cairn.devices.codemother.machines.clearance <intention-address>

    The consumer is the hand deciding whether to retire an intention — which is why the
    blind classes are printed at the same weight as the findings rather than as a footnote.
    A report that whispers its blindness is the one this whole build exists to forbid.
    """
    from cairn.devices.codemother.machines.clearance.clearance import riders_of

    r = riders_of(intention)
    blind = r.blind
    print(f"DEPRECATION REPORT — {intention}\n")
    print(f"RIDING IT ({len(r.riding)} in-flight boat(s) name this intention):")
    for b in r.riding:
        print(f"  {b}")
    if not r.riding:
        print("  (none)")
    print(f"\nWHAT THIS READ COULD NOT SEE — over {r.in_flight} in-flight boats, "
          f"{r.attributable} were attributable:")
    print(f"  unattributed  {blind['unattributed']:4}  in flight, naming no owning intention")
    print(f"  unresolvable  {blind['unresolvable']:4}  naming an intention that resolves nowhere")
    print(f"  unreadable    {blind['unreadable']:4}  whose flight status could not be judged")
    for boat, addr in r.unresolvable:
        print(f"      {boat}  ->  {addr}")
    for boat, why in r.unreadable:
        # TRUNCATED HERE AND NOWHERE ELSE. ``Riders`` carries the whole reason; a printout
        # is a presentation surface and may arrange (Law 7 permits the collapse HERE and
        # forbids it in the record) — one ticket's state field is a 900-character essay,
        # and letting it push the counts off the top of the screen would be a report that
        # hides its own findings.
        print(f"      {boat}  ::  {why[:120]}{'…' if len(why) > 120 else ''}")
    print("\nA clean 'nobody is riding this' means nothing while those three counts are "
          "non-zero.\nRetiring the intention is the owner's act; this read informs it and "
          "decides nothing (Law 6).")
    return 0



def _main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    if len(args) != 1:
        print("usage: python3 -m cairn.devices.codemother.machines.clearance <intention-address>",
              file=sys.stderr)
        return 2
    return _retirement_report(args[0])


if __name__ == "__main__":
    raise SystemExit(_main())
