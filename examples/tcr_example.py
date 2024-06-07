"""
TCR LBC for CMAQ
================================

This example shows how to use aqmbc with TROPESS Composition Reanalysis (TCR)
files, which are available thru NASA Earthdata Search

* Define translation.
* Extract and translate.
* Display figures and statistics."""

import aqmbc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import glob
import xarray as xr

gdnam = '12US1'

# %%
# Define Translation Expressions
# ------------------------------

# In Notebooks, display available expressions
aqmbc.exprlib.avail('tcr')

# %%

exprpaths = aqmbc.exprlib.exprpaths([
    'tcr_o3so4.expr',                 # for a full run, comment this
    # 'tcr_cb6.expr', 'tcr_ae7.expr'  # for a full run, uncomment this
], prefix='tcr')

# For "real" VGLVLS use
# METBDYD_PATH = '...'
# metaf = pnc.pncopen(METBDY3D_PATH, format='ioapi')
metaf = aqmbc.options.getmetaf(bctype='bcon', gdnam=gdnam, vgnam='EPA_35L')
inpath = sorted(glob.glob(
    'TCR-2/tropess.gesdisc.eosdis.nasa.gov/data/TCR2_MON_*/*/*.nc'
))
suffix = f'_{gdnam}_BCON.nc'
dims = aqmbc.options.dims['tcr']
outpath = f'TROPESS_reanalysis_mon_2021_{gdnam}_BCON.nc'
history = f'From {inpath}'
outf = aqmbc.bc(
    inpath, outpath, metaf, vmethod='linear', exprpaths=exprpaths,
    dimkeys=dims, format_kw={'format': 'tcr'}, history=history,
    clobber=True, verbose=0
)

# %%
# Figures and Statistics
# ----------------------

tflag = (outf['TFLAG'][:, 0, :].astype('l') * np.array([1000000, 1])).sum(1)
time = pd.to_datetime(tflag, format='%Y%j%H%M%S')
vprof = xr.Dataset(
    data_vars={
        k: (v.dimensions, v[:], {pk: v.getncattr(pk) for pk in v.ncattrs()})
        for k, v in outf.variables.items()
    },
    coords={'TSTEP': time, 'LAY': (outf.VGLVLS[:-1] + outf.VGLVLS[1:]) / 2}
).mean('PERIM', keep_attrs=True)
statdf = aqmbc.report.getstats([outpath])
statdf.to_csv('tcr_summary.csv')

# %%
# Visualize Vertical Profiles
# ---------------------------

fig = aqmbc.report.plot_2spc_vprof(vprof)
fig.suptitle('TCR Boundary Conditions for CMAQ')
fig.savefig('tcr_profiles.png')

# %%
# Barplot of Concentrations
# -------------------------

fig = aqmbc.report.plot_gaspm_bars(statdf)
fig.savefig('tcr_bar.png')
