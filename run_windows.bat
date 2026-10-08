@echo off
setlocal
set "APP_DIR=%~dp0"
set "PYTHON_EXE=C:\Users\andy_\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"

if exist "%PYTHON_EXE%" (
  start "" "%PYTHON_EXE%" "%APP_DIR%desktop_launcher.py"
) else (
  start "" python "%APP_DIR%desktop_launcher.py"
)
