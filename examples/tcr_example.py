"""
TCR LBC for CMAQ
================================

This example shows how to use aqmbc with TROPESS Composition Reanalysis (TCR)
files, which are available thru NASA Earthdata Search

* Define translation.
* Extract and translate.
* Display figures and statistics."""

import PseudoNetCDF as pnc
import aqmbc
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.colors as mc
import copy
import glob

gdnam = '12US1'

# %%
# Define Translation Expressions
# ------------------------------

# In Notebooks, display available expressions
aqmbc.exprlib.avail('tcr')

# %%

exprpaths = aqmbc.exprlib.exprpaths([
    'tcr_cb6.expr', 'tcr_ae7.expr'
], prefix='tcr')

# For "real" VGLVLS use
# METBDYD_PATH = '...'
# metaf = pnc.pncopen(METBDY3D_PATH, format='ioapi')
metaf = aqmbc.options.getmetaf(bctype='bcon', gdnam=gdnam, vgnam='EPA_35L')
inpath = sorted(glob.glob('/work/ROMO/global/TCR-2/tropess.gesdisc.eosdis.nasa.gov/data/TCR2_MON_*/*/*.nc'))
suffix = f'_{gdnam}_BCON.nc'
dims = aqmbc.options.dims['tcr']
outpath = f'TROPESS_reanalysis_mon_2021_{gdnam}_BCON.nc'
history = f'From {inpath}'
outf = aqmbc.bc(
    inpath, outpath, metaf, vmethod='linear', exprpaths=exprpaths,
    dimkeys=dims, format_kw={'format': 'tcr'}, history=history,
    clobber=True, verbose=9
)

# %%
# Figures and Statistics
# ----------------------

import xarray as xr
import netCDF4
import pandas as pd

tflag = (outf['TFLAG'][:, 0, :].astype('l') * np.array([1000000, 1])).sum(1)
time = pd.to_datetime(tflag, format='%Y%j%H%M%S')
vprof = xr.Dataset(
    data_vars={
        k: (v.dimensions, v[:], {pk: v.getncattr(pk) for pk in v.ncattrs()})
        for k, v in outf.variables.items()
    },
    coords={'TSTEP': time, 'LAY': (outf.VGLVLS[:-1] + outf.VGLVLS[1:]) / 2}
).mean('PERIM',keep_attrs=True)
statdf = aqmbc.report.getstats([outpath])
sumdf = aqmbc.report.summarize(statdf)
sumdf.to_csv('tcr_summary.csv')

# %%
# Visualize Vertical Profiles
# ---------------------------

v1 = vprof['O3'] * 1000
v1.attrs.update(vprof['O3'].attrs)
v1.attrs['long_name'] = 'Ozone'
v2 = vprof['ASO4I'] + vprof['ASO4J']
v2.attrs.update(vprof['ASO4J'].attrs)
v2.attrs['long_name'] = 'ASO4IJ'


fig, axx = plt.subplots(1, 2, figsize=(18, 6), dpi=72, sharey=True)
cmap = plt.cm.nipy_spectral
nt = v1.sizes['TSTEP']
for ti, t in enumerate(v1.TSTEP):
    label = t.dt.strftime('%FT%H:%MZ').values
    axx[0].plot(v1.sel(TSTEP=t), v1.LAY, label=label, color=cmap(ti / nt))
axx[0].legend()
cmap = plt.cm.nipy_spectral
for ti, t in enumerate(v2.TSTEP):
    label = t.dt.strftime('%FT%H:%MZ').values
    axx[1].plot(v2.sel(TSTEP=t), v2.LAY, label=label, color=cmap(ti / nt))
axx[1].legend()
axx[0].set(
    xscale='log', xlabel='{long_name} [{units}]'.format(**v1.attrs),
    xlim=(None, 2000), ylabel='VGLVLS [$(p - p_t) / (p_s - p_t)$]', ylim=(1, 0))
axx[1].set(xscale='log', xlabel='{long_name} [{units}]'.format(**v2.attrs))
fig.suptitle('TCR Boundary Conditions for CMAQ')
fig.savefig('tcr_profiles.png')

# %%
# Barplot of Concentrations
# -------------------------

fig, axx = plt.subplots(2, 1, figsize=(18, 8), dpi=72, gridspec_kw=dict(hspace=.8, bottom=0.15))
gasds = sumdf.query('unit == "ppmV"').xs('Overall')['median']
aqmbc.report.barplot(gasds.sort_values(), bar_kw=dict(ax=axx[0]))
pmds = sumdf.query('unit == "micrograms/m**3"').xs('Overall')['median']
aqmbc.report.barplot(pmds.sort_values(), bar_kw=dict(ax=axx[1]))
fig.savefig('tcr_bar.png')