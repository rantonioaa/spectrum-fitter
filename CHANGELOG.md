# Changelog

## 2.0.0 — revival on a current Python stack

The 2020-2021 code could not run on any interpreter newer than roughly Python
3.9 with a 2021 dependency set. Nine defects were fixed; the modelling logic in
`FSRQ_fit.py` is untouched.

### Environment

- Rebuilt on **Python 3.11** with a pinned stack. Upgrading is the wrong default
  here — the code uses `ndarray.newbyteorder()` (removed in numpy 2.0),
  `Spectrum1D(flux=..., spectral_axis=...)` (removed from specutils after 1.3),
  and `read_csv(delim_whitespace=True)` (removed in pandas 3.0). See the comments
  in `requirements.txt` for why each pin is load-bearing.
- `pyarrow` is pinned to 14: releases >= 15 are built against the numpy 2 ABI and
  refuse to import next to numpy 1.26, which breaks `streamlit`. Pin the
  *transitive* dependency down rather than lifting numpy.

### GUI (`app.py`)

1. **Duplicate widget keys.** Every field of every component reused one key
   (`key=i` for all nine widgets of Gaussian *i*, `key='f'` for the whole Fe II
   f-group, `key='Zw'`, `key='fullfit'` twice). Streamlit >= 1.14 raises
   `DuplicateWidgetID`, so the parameter-file path — the reproducible one —
   died on the first component. Fixed with a `_wk()` counter factory; 153 `key=`
   arguments replaced. Values are still read from widget return values, so
   nothing downstream changed.
2. **`NameError: spec_`** — in "Método de ajuste", the continuum-subtracted
   spectrum was only created inside the three region-selection branches, so
   leaving both region checkboxes unticked crashed at the fit. Added the missing
   full-spectrum branch.
3. **`np.float`** (13 uses) — alias removed in numpy 1.24. Replaced with the
   builtin `float`; identical behaviour.
4. **Shelled-out traceback on first render.** `filename is None` was passed into
   `fits.open()`, so every fresh session opened on a red `ValueError`. Guards now
   cover all three uploaders (spectrum, component parameter file, Fe II template
   parameter file).
5. **`NameError: models_aj`** — selecting no Gaussian, no Lorentzian and no
   template is a legal widget state but never built the model. Now an explicit
   warning instead of a crash; likewise for a template-only fit in the
   single-template ranges, which never defines `models_aj`.
6. **Region bounds defaulted to 0.0** (five sites) — `SpectralRegion(0, 0)`
   raised *"Lower bound must be strictly less than the upper bound"* as soon as
   a region checkbox was ticked. Regions are built through a validating
   `_region(lo, hi)` helper. Exclude-regions default to a narrow 5 % band (a
   default covering the whole spectrum leaves the fit with no data — that showed
   up as a scipy `N=3 must not exceed M=1` error); include-regions default to the
   full range, which is a legitimate window.
7. **Template count hardcoded to 50.** The optical Fe II grid has 24 entries by
   construction (`grid_conv.py` sweeps 700-3000 km/s), so `for i in range(50)`
   died on `FE_OPT-1_25.dat`. The loop and the smoothing slider now follow the
   files actually present, and a caption states how many are available.

### Template generator

10. `Hierro/Hidrogeno/grid_conv.py` imported `astroagn.lctools` — a private
    package that is not on PyPI — for two conversions it used nowhere else. Both
    are now defined inline (`kmstoangs` with c = 300 000 km/s, `fwhmtosigma`
    with the full-precision 2√(2ln2) = 2.354820045), so the generator runs
    standalone. Verified by regenerating all 24 templates from `FE_OPT_og.dat`
    and comparing against the shipped files: max relative difference 3e-10, i.e.
    float64 round-off — the truncated 2.35482 would have been off by 1.3e-8.
    Output now goes to `regenerated_grid/` instead of the working directory, so
    running it cannot overwrite the templates in place.

### Notebooks

8. `example.ipynb` cannot run as shipped: cell 4 loads spectra from
   `/home/rantonioaa/...`, a path on the author's old machine. Unmodified it
   fails at cell 4 and every data-dependent cell after it fails as collateral.
9. `examples/example_local.ipynb` replaces only that cell, using a synthetic
   spectrum built as the forward model of the notebook's own initial parameters
   (continuum + 8 Gaussians + the 5 Fe II groups). It runs 12/12 cells and
   recovers the injected centres to <0.1 Å. `examples/example_pks1510.ipynb` is
   the same notebook pointed at real PKS 1510-089 spectra, which are not
   distributed here.

### Verification

- GUI: 10 widget states driven headlessly through `AppTest`, 0 exceptions.
- `Fit_Spec`: synthetic spectrum with known parameters — centres to <0.1 Å,
  amplitudes to <=0.02, Fe II groups correctly converging to ~0 when absent.
- Real-data notebook: 12/12 cells; residual RMS 4-6 % of the continuum, with all
  eight Gaussians railing on a bound — a priors/epoch mismatch, not a code fault.
