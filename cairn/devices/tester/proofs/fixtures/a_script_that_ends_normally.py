"""Fixture for ticket 0a807f816e9f: a .py script that ends by falling off its last line.

Run as a subprocess by test_a_subprocess_script_that_ends_normally_is_in_the_seals_closure.py.
CPython 3.14 pops ``__main__.__file__`` when a script runs to its end, so before the ticket the
reach log never named this file. Stdlib only, and no ``raise SystemExit``: that ending is the case.
"""

print("a script that ends normally")
