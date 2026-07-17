# The single import root — one heart (MAP.md: "the single import root").
#
# EMPTY / lazy forever. Importing any subpackage must never eager-import a
# DB-bound one (the boot-order law, carried from the quarry). Keep this file
# free of imports so `import cairn` costs nothing and binds to no device.
