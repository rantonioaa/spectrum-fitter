#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2026 R. Amaya-Almazán
"""Regression matrix v2 for the Spectrum Fitter Streamlit app.

Covers every "widget state with a None upload" that used to crash with a raw
traceback, plus the working paths, through streamlit.testing.v1.AppTest.

  A nothing uploaded               -> info prompt
  F txt + params-file radio, no file -> info prompt
  G txt + comp file + Fe template + template radio, no file -> info prompt
  B txt + no component type        -> warning
  C txt + comp file + full fit     -> fits
  D + explicit fit window          -> fits
  E + Fe II 5-group template       -> fits (exercises Zw widgets)

Run with CWD = project root (relative 'Hierro/...' paths).
"""

import os, sys
_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_PROJECT)          # templates and data use relative paths
sys.path.insert(0, _PROJECT)
import io
import os
import sys
import warnings

warnings.simplefilter("ignore")

APP = "app.py"
SPEC = "testdata/ejemplo_Hbeta_OIII.txt"
PARAMS = "testdata/params_componentes.txt"

DECLINE = set()  # uploader keys that should return None


def stub_uploader(label, type=None, key=None, **kw):
    if key in DECLINE:
        return None
    if key in ("comp", "temp"):
        return io.StringIO(open(PARAMS).read())
    return io.StringIO(open(SPEC).read())


def fresh():
    import streamlit as st
    from streamlit.testing.v1 import AppTest
    st.file_uploader = stub_uploader
    return AppTest.from_file(APP, default_timeout=600)


def set_by(widgets, prefix, value):
    for w in widgets:
        if w.label.startswith(prefix):
            w.set_value(value)


def check(name, at, expect_info=None, expect_warn=None):
    exc = len(at.exception)
    ok = exc == 0
    if expect_info:
        ok = ok and any(expect_info in i.value for i in at.info)
    if expect_warn:
        ok = ok and any(expect_warn in w.value for w in at.warning)
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: exceptions={exc}")
    for e in at.exception:
        print("        EXC:", str(e.message)[:200])
    for i in at.info:
        print("        INFO:", i.value[:110])
    for w in at.warning:
        print("        WARN:", w.value[:110])
    return ok


R = {}

# A: nothing uploaded (no stub at all -> real uploader returns None)
import streamlit as st
from streamlit.testing.v1 import AppTest
at = AppTest.from_file(APP, default_timeout=120)
at.run()
R["A"] = check("A nothing uploaded", at, expect_info="Sube un espectro")

# F: spectrum uploaded, params-file radio on, no params file
DECLINE.clear(); DECLINE.add("comp")
at = fresh(); at.run()
at.radio[0].set_value("txt"); at.run()
set_by(at.radio, "¿Desea usar archivo de parámetros para las componentes", "Sí")
at.run()
R["F"] = check("F params radio, no params file", at, expect_info="Sube el archivo de parámetros de las componentes")

# G: comp file present, Fe II template on, template radio on, no template file
#    (the template-params radio only exists for the 5-group range)
DECLINE.clear(); DECLINE.add("temp")
at = fresh(); at.run()
at.radio[0].set_value("txt"); at.run()
set_by(at.radio, "¿Desea usar archivo de parámetros para las componentes", "Sí")
at.run()
set_by(at.checkbox, "Utilizar un template de Fe II", True)
at.run()
set_by(at.selectbox, "En qué rango espectral", "4000-5500 Angstroms (Multiple components)")
at.run()
set_by(at.radio, "¿Desea usar archivo de parámetros iniciales para el template", "Sí")
at.run()
R["G"] = check("G template radio, no template file", at, expect_info="Sube el archivo de parámetros iniciales del template")

# B..E: working path, chained on one session
DECLINE.clear()
at = fresh(); at.run()
at.radio[0].set_value("txt"); at.text_input[0].set_value("TEST"); at.run()
R["B"] = check("B no component type", at, expect_warn="Selecciona al menos")

set_by(at.radio, "¿Desea usar archivo de parámetros para las componentes", "Sí"); at.run()
R["C"] = check("C comp file + full fit", at)

set_by(at.radio, "¿Desea especificar un rango", "Sí"); at.run()
R["D"] = check("D explicit fit window", at)

set_by(at.checkbox, "Utilizar un template de Fe II", True); at.run()
set_by(at.selectbox, "En qué rango espectral", "4000-5500 Angstroms (Multiple components)"); at.run()
R["E"] = check("E Fe II 5-group template", at)

print("\nSUMMARY:", "ALL PASS" if all(R.values()) else "FAILED: " + ",".join(k for k, v in R.items() if not v))

sys.exit(0 if all(R.values()) else 1)
