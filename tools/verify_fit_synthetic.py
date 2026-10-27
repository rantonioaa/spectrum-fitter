#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2026 R. Amaya-Almazán
"""Verify FSRQ_fit.Fit_Spec recovers known parameters.

Builds a synthetic rest-frame, continuum-normalized Hbeta + [O III] spectrum
with known Gaussian parameters, fits it with the project's own fitting
function (including the Kovacevic Fe II template groups), and compares the
recovered values against the injected truth.

Run with CWD = project root (templates use relative 'Hierro/...' paths).
"""

import os, sys
_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_PROJECT)          # templates and data use relative paths
sys.path.insert(0, _PROJECT)
import warnings

import numpy as np

warnings.simplefilter("ignore")

import os
import sys


from astropy import units as u
from astropy.modeling import models
from specutils.spectra import SpectralRegion

from FSRQ_fit import Fit_Spec, kmstoangs

# ---------------------------------------------------------------- truth
L = np.arange(4400.0, 5600.0, 0.5)

TRUE = {
    # name: (center, amplitude, fwhm_kms)
    "Hbeta_broad": (4861.0, 0.30, 2200.0),
    "Hbeta_narrow": (4861.0, 0.20, 400.0),
    "[OIII]_4959": (4959.0, 0.20, 350.0),
    "[OIII]_5007": (5007.0, 0.60, 350.0),
}


def gauss(center, amp, fwhm_kms):
    sd = kmstoangs(fwhm_kms, center, mode="g")
    return amp * np.exp(-0.5 * ((L - center) / sd) ** 2)


cont = 1.0 + 0.00006 * (L - 5000.0)
flux = cont.copy()
for c, a, f in TRUE.values():
    flux += gauss(c, a, f)

rng = np.random.default_rng(11)
flux += rng.normal(0, 0.004, L.size)

# ------------------------------------------------- gaussian config blocks
# [init, min, max, fixed] per parameter, exactly as in example.ipynb
gaussians = [
    # 0: broad Hbeta
    [[4861.0, 4800.0, 4920.0, False], [0.30, 0.0, 2.0, False], [2500.0, 500.0, 6000.0, False]],
    # 1: narrow Hbeta (FWHM tied to [OIII]5007 when hb_oiii=True)
    [[4861.0, 4855.0, 4867.0, False], [0.20, 0.0, 1.0, False], [400.0, 100.0, 900.0, False]],
    # 2: [OIII] 4959 (amp and wave tied to 5007)
    [[4959.0, 4950.0, 4970.0, False], [0.20, 0.0, 1.0, False], [400.0, 100.0, 900.0, False]],
    # 3: [OIII] 5007
    [[5007.0, 5000.0, 5015.0, False], [0.60, 0.0, 2.0, False], [400.0, 100.0, 900.0, False]],
]

feii_params = [
    # group f also carries the shared Doppler smoothing (3rd element, group 0 only)
    [[0.02, 0.0, 1.0, False], [-1.0, -20, 20, False], [2000, 700, 2800, False]],
    [[0.02, 0.0, 1.0, False], [1.0, -20, 20, False]],    # g
    [[0.02, 0.0, 1.0, False], [1.0, -20, 20, False]],    # s
    [[0.02, 0.0, 1.0, True], [0.0, -20, 20, True]],      # p (fixed)
    [[0.02, 0.0, 1.0, False], [-1.0, -20, 20, False]],   # zw
]

print("=== running Fit_Spec (with Kovacevic Fe II template groups) ===")
model, params, cont_params = Fit_Spec(
    L=L,
    FLUX=flux,
    gaussians=gaussians,
    inclContRegions=None,
    exclContRegions=None,
    hb_oiii=True,
    feii_temp="4000-5500 Angstroms (Multiple components)",
    feii_params=feii_params,
    fit_window=SpectralRegion(4400 * u.AA, 5400 * u.AA),
)

print("\n=== recovered continuum (power law) ===")
print(f"amplitude={cont_params[0]:.4f}  x_0={cont_params[1]:.1f}  alpha={cont_params[2]:.4f}")

print("\n=== recovered emission lines vs truth ===")
names = list(TRUE)
ok = True
for i, name in enumerate(names):
    c0, a0, f0 = TRUE[name]
    cen = float(getattr(model, f"mean_{i}").value)
    amp = float(getattr(model, f"amplitude_{i}").value)
    sd = float(getattr(model, f"stddev_{i}").value)
    fwhm = sd * 2.354820045 / cen * 299792.458
    print(f"{name:14s} center {cen:8.2f} (true {c0:8.2f})   "
          f"amp {amp:6.4f} (true {a0:6.4f})   FWHM {fwhm:7.1f} km/s (true {f0:7.1f})")
    if abs(cen - c0) > 3.0:
        ok = False
    if abs(amp - a0) > 0.06:
        ok = False

print("\n=== Fe II template groups (amplitud, shift, doppler) ===")
for i, grp in enumerate(["f", "g", "s", "p", "Zw"]):
    print(f"  {grp:3s} amp={float(getattr(model, f'amplitud_{4+i}').value):+.4f} "
          f"shift={float(getattr(model, f'shift_{4+i}').value):+.2f} "
          f"doppler={float(getattr(model, f'doppler_{4+i}').value):.0f}")

print("\nRESULT:", "PASS - parameters recovered within tolerance" if ok else "FAIL - out of tolerance")
