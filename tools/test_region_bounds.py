#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2026 R. Amaya-Almazán
"""Region-selection regression cases (the bounds that defaulted to 0.0)."""

import os, sys
_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_PROJECT)          # templates and data use relative paths
sys.path.insert(0, _PROJECT)
import io
import os
import sys
import warnings

warnings.simplefilter("ignore")

import streamlit as st
from streamlit.testing.v1 import AppTest

APP = "app.py"


def stub(label, type=None, key=None, **kw):
    if key in ("comp", "temp"):
        return io.StringIO(open("testdata/params_componentes.txt").read())
    return io.StringIO(open("testdata/ejemplo_Hbeta_OIII.txt").read())


def set_by(widgets, prefix, value):
    for w in widgets:
        if w.label.startswith(prefix):
            w.set_value(value)


def check(name, at):
    ok = len(at.exception) == 0
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: exceptions={len(at.exception)}")
    for e in at.exception:
        print("        EXC:", str(e.message)[:200])
    errs = [e.value for e in at.error]
    for e in errs:
        print("        ERROR:", e[:120])
    return ok


R = {}
st.file_uploader = stub

# H: only "exclude regions" ticked
at = AppTest.from_file(APP, default_timeout=600)
at.run(); at.radio[0].set_value("txt"); at.run()
set_by(at.checkbox, "Regiones del espectro para excluir", True)
at.run()
R["H"] = check("H exclude-regions ticked", at)

# I: both exclude and include ticked
set_by(at.checkbox, "Regiones del espectro para incluir", True)
at.run()
R["I"] = check("I exclude+include ticked", at)

# J: also with the component parameter file, to reach the fit
set_by(at.radio, "¿Desea usar archivo de parámetros para las componentes", "Sí")
at.run()
R["J"] = check("J regions + params file + fit", at)

print("\nSUMMARY:", "ALL PASS" if all(R.values()) else "FAILED: " + ",".join(k for k, v in R.items() if not v))

sys.exit(0 if all(R.values()) else 1)
