@echo off
rem cairn.cmd -- thin Windows shim: runs the Python launcher (bin\cairn.py) with Cairns own interpreter.
setlocal
set "PYTHONUTF8=1"
if not defined CAIRN_VENV set "CAIRN_VENV=%USERPROFILE%\.cairn\venv"
if not exist "%CAIRN_VENV%\Scripts\python.exe" (
  echo cairn: floor: venv - %CAIRN_VENV%\Scripts\python.exe is absent; lay the venv ^(cairn/devices/recovery/bootstrap.sh^) 1>&2
  exit /b 3
)
"%CAIRN_VENV%\Scripts\python.exe" "%~dp0cairn.py" %*
exit /b %ERRORLEVEL%
