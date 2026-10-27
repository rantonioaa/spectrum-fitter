#!/usr/bin/env python3
# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2026 R. Amaya-Almazán
"""Execute a notebook with the project venv kernel and report per-cell status.

Usage:  sf_nbrun.py <notebook> [out_notebook]

- registers a local kernelspec pointing at ./.venv so the notebook runs in the
  pinned environment (not any global python),
- runs with CWD = project root (FSRQ_fit loads 'Hierro/...' relatively),
- prints one line per code cell, then the first failing cell's traceback tail.
"""

import os, sys
_PROJECT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(_PROJECT)          # templates and data use relative paths
sys.path.insert(0, _PROJECT)
PROJECT = _PROJECT          # this script resolves paths from the project root
import json
import os
import shutil
import sys
import tempfile

_venv_py = os.path.join(PROJECT, ".venv", "Scripts", "python.exe")
VENV_PY = _venv_py if os.path.exists(_venv_py) else sys.executable


def install_kernelspec():
    root = os.path.join(tempfile.gettempdir(), "sf_jupyter")
    kdir = os.path.join(root, "kernels", "sf-venv")
    os.makedirs(kdir, exist_ok=True)
    spec = {
        "argv": [VENV_PY, "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "SF venv (3.11)",
        "language": "python",
    }
    with open(os.path.join(kdir, "kernel.json"), "w", encoding="utf-8") as fh:
        json.dump(spec, fh)
    os.environ["JUPYTER_PATH"] = root
    return "sf-venv"


def main():
    src = sys.argv[1]
    out = sys.argv[2] if len(sys.argv) > 2 else None
    kernel = install_kernelspec()

    import nbformat
    from nbclient import NotebookClient

    nb = nbformat.read(src, as_version=4)
    client = NotebookClient(
        nb,
        timeout=1800,
        kernel_name=kernel,
        allow_errors=True,           # we want to see every failure, not stop at the first
        resources={"metadata": {"path": PROJECT}},
    )

    print(f"executing {os.path.basename(src)} with kernel {kernel}")
    client.execute()

    code_cells = [(i, c) for i, c in enumerate(nb.cells) if c.cell_type == "code"]
    failures = []
    for idx, cell in code_cells:
        errs = [o for o in cell.get("outputs", []) if o.get("output_type") == "error"]
        if errs:
            e = errs[0]
            tb = "\n".join(e.get("traceback", []))
            print(f"  cell {idx:2d}: FAIL  {e.get('ename')}: {str(e.get('evalue'))[:120]}")
            failures.append((idx, e.get("ename"), str(e.get("evalue")), tb))
        else:
            nimg = sum(1 for o in cell.get("outputs", []) if "image/png" in o.get("data", {}))
            print(f"  cell {idx:2d}: ok    ({len(cell.get('outputs', []))} outputs, {nimg} figures)")

    if out:
        nbformat.write(nb, out)
        print(f"\nwrote {out}")

    print(f"\nRESULT: {len(code_cells) - len(failures)}/{len(code_cells)} code cells ok")
    if failures:
        idx, ename, evalue, tb = failures[0]
        print(f"\nfirst failure (cell {idx}): {ename}: {evalue}")
        print("\n".join(tb.splitlines()[-12:]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
