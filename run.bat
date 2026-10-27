@echo off
REM Launch the Spectrum Fitter app (Windows).
REM Must run from the repository root: templates use relative Hierro\ paths.
cd /d "%~dp0"

set "PY=python"
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"

"%PY%" -c "import streamlit" 2>nul
if errorlevel 1 (
    echo streamlit is not installed for: %PY%
    echo   %PY% -m pip install -r requirements.txt
    exit /b 1
)

"%PY%" -m streamlit run app.py %*
