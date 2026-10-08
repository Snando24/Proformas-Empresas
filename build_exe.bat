@echo off
setlocal
set "APP_DIR=%~dp0"
set "PYTHON_EXE=C:\Python314\python.exe"

if not exist "%PYTHON_EXE%" set "PYTHON_EXE=python"

"%PYTHON_EXE%" -m PyInstaller ^
  --noconfirm ^
  --onefile ^
  --name ProformasTractotec ^
  --add-data "%APP_DIR%static;static" ^
  --add-data "%APP_DIR%proforma_app;proforma_app" ^
  --icon "%APP_DIR%static\assets\app-icon.ico" ^
  "%APP_DIR%desktop_launcher.py"

echo.
echo Si todo salio bien, el ejecutable queda en dist\ProformasTractotec.exe
