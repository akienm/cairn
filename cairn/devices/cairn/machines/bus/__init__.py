# bus — the ONE common messaging substrate: the sole path for inter-device
# communication, as db_domain is the sole path to durable state. Lazy on purpose
# (boot-order law): importing the package pulls in nothing heavy; db_domain comes
# in only when a message is actually posted.
