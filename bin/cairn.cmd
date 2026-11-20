@echo off
rem cairn.cmd -- thin Windows shim: runs the Python launcher (bin\cairn.py) with Cairns own interpreter.
rem When the LAUNCHER itself fails (no venv, or bin\cairn.py exits its reserved code 70) it files a trouble
rem itself, in the trouble format, and at a terminal falls over to Rescue: claude run with dangerous
rem permissions and the trouble's path (outline 5.4.3.8.1-4, ticket ddc9957704d2). A command that runs and
rem fails returns its own code and files nothing. Test seams: CAIRN_TROUBLE_STORE, CAIRN_LAUNCHER_TTY.
setlocal
set "PYTHONUTF8=1"
if not defined CAIRN_VENV set "CAIRN_VENV=%USERPROFILE%\.cairn\venv"
if not exist "%CAIRN_VENV%\Scripts\python.exe" goto :novenv
"%CAIRN_VENV%\Scripts\python.exe" "%~dp0cairn.py" %*
set "CAIRN_RC=%ERRORLEVEL%"
if not "%CAIRN_RC%"=="70" exit /b %CAIRN_RC%
set "CAIRN_TID=launcher-failed-exit-70"
set "CAIRN_WHY=the cairn launcher (bin\cairn.py) failed itself and exited its reserved code 70; its traceback is above"
goto :fail
:novenv
echo cairn: floor: venv - %CAIRN_VENV%\Scripts\python.exe is absent; lay the venv ^(cairn/devices/recovery/bootstrap.sh^) 1>&2
set "CAIRN_RC=3"
set "CAIRN_TID=launcher-failed-venv-absent"
set "CAIRN_WHY=the cairn launcher could not start: %CAIRN_VENV%\Scripts\python.exe is absent; lay the venv (cairn/devices/recovery/bootstrap.sh)"
:fail
set "CAIRN_PS_MODE=file"
set "CAIRN_TROUBLE_PATH="
for /f "usebackq delims=" %%P in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$t=[IO.File]::ReadAllText('%~f0'); iex $t.Substring($t.IndexOf('#<'+'ps>'))"`) do set "CAIRN_TROUBLE_PATH=%%P"
if not defined CAIRN_TROUBLE_PATH echo cairn: the launcher failed and the trouble could not be filed: %CAIRN_WHY% 1>&2 & exit /b %CAIRN_RC%
echo cairn: launcher failure filed as trouble %CAIRN_TROUBLE_PATH% 1>&2
if not defined CAIRN_LAUNCHER_TTY call :probetty
if not "%CAIRN_LAUNCHER_TTY%"=="1" echo cairn: no terminal, so Rescue is not launched; trouble left for the next Rescue at %CAIRN_TROUBLE_PATH% 1>&2 & exit /b %CAIRN_RC%
where claude >nul 2>&1
if errorlevel 1 echo cairn: claude was not found on PATH, so Rescue cannot start; trouble at %CAIRN_TROUBLE_PATH% 1>&2 & exit /b %CAIRN_RC%
call claude --dangerously-skip-permissions "read this: the cairn launcher failed and filed the trouble ticket %CAIRN_TROUBLE_PATH% . At the end of proving the fix, check for more errors, to clear or fix as appropriate."
exit /b %CAIRN_RC%
:probetty
set "CAIRN_PS_MODE=tty"
for /f "usebackq delims=" %%T in (`powershell -NoProfile -ExecutionPolicy Bypass -Command "$t=[IO.File]::ReadAllText('%~f0'); iex $t.Substring($t.IndexOf('#<'+'ps>'))"`) do set "CAIRN_LAUNCHER_TTY=%%T"
exit /b 0
#<ps>
$ErrorActionPreference = 'Stop'
if ($env:CAIRN_PS_MODE -eq 'tty') { if ([Console]::IsInputRedirected -or [Console]::IsOutputRedirected) { '0' } else { '1' }; return }
try {
  $store = if ($env:CAIRN_TROUBLE_STORE) { $env:CAIRN_TROUBLE_STORE } else { Join-Path $env:USERPROFILE '.cairn\logs\cairn\0\troubletickets' }
  New-Item -ItemType Directory -Force -Path $store | Out-Null
  $id = $env:CAIRN_TID
  $path = Join-Path $store ($id + '.json')
  $now = (Get-Date).ToUniversalTime().ToString('o')
  $occ = [ordered]@{ at = $now; caller = [ordered]@{ how = 'shell'; identity = 'cairn.cmd' }; detail = $env:CAIRN_WHY }
  $open = 'trouble@v1: [OPEN] -> CLEARED'
  if (Test-Path $path) {
    $r = Get-Content -Raw -Encoding UTF8 $path | ConvertFrom-Json
    $r.count = [int]$r.count + 1
    $r.last_seen = $now
    $r.workflow_and_state = $open
    $r.occurrences = @((@($r.occurrences) + @($occ)) | Select-Object -Last 20)
  } else {
    $r = [ordered]@{ id = $id; standing = 'OPEN'; why = $env:CAIRN_WHY; count = 1; first_seen = $now; last_seen = $now;
      occurrences = @($occ); notified = @('cc'); cleared_by = @(); recurred_after_clear = $null; prior_attempts = 0;
      node_class = 'trouble'; schema_version = 'trouble-v1'; workflow_and_state = $open }
  }
  [IO.File]::WriteAllText($path, ($r | ConvertTo-Json -Depth 8), (New-Object Text.UTF8Encoding($false)))
  $path
} catch { }
