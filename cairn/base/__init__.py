# cairn.base — the Form, embodied. EMPTY / lazy (boot-order law): importing the
# base must never pull in a device or a DB-bound module. Import leaves directly,
# e.g. `from cairn.base.core_values import CoreValuesMixin`.
