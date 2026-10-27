#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Oct 11 18:21:04 2021

@author: rantonioaa

Generates the optical Fe II template grid, FE_OPT_1..24.dat, by convolving the
unsmoothed template FE_OPT_og.dat with Gaussians of increasing width:

    index i  ->  FWHM = 700 + 100*(i-1) km/s      (700 .. 3000, 24 steps)

That is where the "24 templates" of the 4000-7000 A range come from: the grid is
defined by np.arange(700, 3100, 100) below. Run from this directory.

Usage:
    python grid_conv.py [outdir]        # default outdir: regenerated_grid
"""
import os
import sys

from astropy.modeling import models
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scipy.signal as sig

# ---------------------------------------------------------------------------
# Local stand-in for astroagn.lctools
# ---------------------------------------------------------------------------
# The original script did `from astroagn import lctools as lc` and used exactly
# two conversions from that package. They are reproduced here so the generator
# is self-contained (astroagn is not on PyPI). Both match the published
# templates in this directory to machine precision - see the README.
C_KMS = 300000.0          # speed of light, km/s
FWHM2SIGMA = 2.354820045      # 2*sqrt(2*ln2)


def kmstoangs(fwhm_kms, lam_angstrom):
    """FWHM in km/s -> FWHM in Angstrom at the given wavelength."""
    return fwhm_kms * lam_angstrom / C_KMS


def fwhmtosigma(fwhm):
    """FWHM -> Gaussian sigma."""
    return fwhm / FWHM2SIGMA


# Write to a subdirectory by default so the templates shipped in this folder
# cannot be overwritten by accident.
OUTDIR = sys.argv[1] if len(sys.argv) > 1 else 'regenerated_grid'
os.makedirs(OUTDIR, exist_ok=True)

template = pd.read_csv('FE_OPT_og.dat', delim_whitespace=True, names=['l', 'flux'])

fwhm_kms = np.arange(700, 3100, 100)

for i in range(len(fwhm_kms)):

    fwhm_angs = kmstoangs(fwhm_kms[i], np.mean(template.l))

    g = models.Gaussian1D(amplitude=max(template.flux),
                          mean=np.mean(template.l),
                          stddev=fwhmtosigma(fwhm_angs))

    gauss = g(template.l.values)

    new_temp = np.convolve(template.flux, gauss, mode='same')/sum(gauss)

    df_temp = pd.DataFrame({'l': template.l.values, 'flux': new_temp})
    df_temp.to_csv(os.path.join(OUTDIR, 'FE_OPT_' + str(i+1) + '.dat'),
                   sep=' ', index=False, header=None)

    # plt.plot(template.l,new_temp+fwhm_kms[i]-min(new_temp))

print(f'wrote {len(fwhm_kms)} templates to {OUTDIR}/')



# print(max(template.flux))
# print(max(new_temp))
# plt.yticks(fwhm_kms)
# gaussian_test = sig.windows.gaussian(1001,10)
# print(gaussian_test)
# plt.plot(template.l,gauss)
# plt.plot(template.l,template.flux)
# plt.show()
