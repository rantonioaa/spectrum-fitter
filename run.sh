#!/usr/bin/env bash
# Launch the Spectrum Fitter app.
# Must run from the repository root: templates use relative 'Hierro/...' paths
# and results are written to the working directory.
set -e
cd "$(dirname "$0")"

PY=python
if [ -x .venv/bin/python ]; then
    PY=.venv/bin/python
elif [ -x .venv/Scripts/python.exe ]; then
    PY=.venv/Scripts/python.exe
fi

if ! "$PY" -c "import streamlit" 2>/dev/null; then
    echo "streamlit is not installed for: $PY"
    echo "  $PY -m pip install -r requirements.txt"
    exit 1
fi

exec "$PY" -m streamlit run app.py "$@"
