@echo off
rem AEL Research Agent v0 - double-click to open the control panel in your browser.
cd /d "%~dp0"
if not "%1"=="run" (cmd /k "%~f0" run & exit /b)
set PY=
where py >nul 2>nul && py -3 -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set PY=py -3
if not defined PY where python >nul 2>nul && python -c "import sys; sys.exit(0 if sys.version_info>=(3,10) else 1)" >nul 2>nul && set PY=python
if not defined PY for /d %%D in ("%LOCALAPPDATA%\Programs\Python\Python3*") do if exist "%%D\python.exe" set PY="%%D\python.exe"
if not defined PY (
  echo Python 3.10 or newer was not found.
  echo Install it from https://www.python.org/downloads/ and tick "Add python.exe to PATH".
  goto :eof
)
%PY% app.py
echo.
echo The control panel has stopped. You can close this window.
