"""``python3 -m cairn.devices.codemother.machines.outline_check <ticket>`` — see outline_check.run."""
import sys

from cairn.devices.codemother.machines.outline_check.outline_check import run

sys.exit(run(sys.argv[1:]))
