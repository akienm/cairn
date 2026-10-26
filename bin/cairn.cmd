@echo off
rem cairn.cmd -- thin Windows shim: runs the one real dispatcher (bin\cairn) under Git Bash.
rem Git Bash shares %USERPROFILE% as $HOME, so ~/.cairn is the same instance-space as Windows sees.
set "MSYS=winsymlinks:nativestrict"
"C:\Program Files\Git\bin\bash.exe" "%~dp0cairn" %*
exit /b %ERRORLEVEL%
