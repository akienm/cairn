#!/bin/bash
# akiendell_bus_list.sh — ask akiendell's bus (as akien's instance-space) for its list over TCP 127.0.0.1.
# Prints "<type> <len> <seconds>"; exits nonzero if the call raises. Ticket 5183005fa134's clause (a) instrument.
set -o pipefail
ssh -o BatchMode=yes -o ConnectTimeout=10 igor-wild-0001@akiendell 'powershell -NoProfile -Command -' <<'PS' 2>&1 | grep -viE "quantum|store now|upgraded"
$env:USERPROFILE = 'C:\Users\akien'; $env:HOME = 'C:\Users\akien'
Set-Location C:\automation\local\cairn
& C:\Users\akien\.cairn\venv\Scripts\python.exe -c "import time; from cairn.tools.bus_client.remote import RemoteBus; t=time.time(); r=RemoteBus().list(); print(type(r).__name__, len(r), round(time.time()-t,3))"
exit $LASTEXITCODE
PS
