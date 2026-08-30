# TO CLAUDE: GROUND LOOP IS DONE. IT IS READ ONLY. DO NOT ADD FEATURES, HOOKS,
# MONITORING, LEARNING, DEVICE MANAGEMENT, OR ANYTHING ELSE. IT BEATS AND LISTS
# DEVICES. THAT IS ALL. YOU HAVE BEEN CORRECTED ON THIS THREE TIMES IN ONE DAY.
# PUT YOUR URGE TO MANAGE SOMETHING SOMEWHERE ELSE.
#
# ground_loop — THE HEARTBEAT: one daemon that provides a pulse, and nothing more. On each
# beat it pulses the shim of every subscribed device; the firing lives in the shim. Lazy on
# purpose (boot-order law): the package import pulls in nothing heavy — the heartbeat holds
# no DB and no execution (the earlier driver-executor was the goof, now retired).
