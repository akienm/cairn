"""proof_coverage — the join between a ticket's clauses, a proof's declaration, and a seal.

Charter: cairn/tools/proof_coverage/intention+why.json
"""
from cairn.tools.proof_coverage.proof_coverage import (  # noqa: F401
    GREEN_MARKERS,
    RED_MARKERS,
    WHOLE,
    clauses,
    declared,
    lacks,
    load_tickets,
    print_teeth_main,
    teeth_printed,
)
# the function unseen_patches is NOT exported here: it would shadow the submodule of the same name
from cairn.tools.proof_coverage.unseen_patches import unseen_patch_proofs  # noqa: F401,E402
