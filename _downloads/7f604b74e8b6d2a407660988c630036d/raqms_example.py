"""
RAQMS LBC for CMAQ
================================

This example shows how to use aqmbc with RAQMS's publicly available forecasts.

* Download from RAQMS (only if not available in RAQMS folder).
* Define translation.
* Extract and translate.
* Display figures and statistics."""

from os.path import basename
import aqmbc
import glob
import pandas as pd
import matplotlib.pyplot as plt

gdnam = '12US1'

# %%
# Download from RAQMS via HTTP
# ----------------------------

todayat12z = (
    pd.to_datetime('now', utc=True).floor('1d') + pd.to_timedelta('12h')
)
dates = [todayat12z]

aqmbc.models.raqms.download(dates)

# %%
# Define Translation Expressions
# ------------------------------

# In Notebooks, display available expressions
aqmbc.exprlib.avail('raqms')

# %%

exprpaths = aqmbc.exprlib.exprpaths([
    'raqms_o3so4.expr'
    # 'raqms_to_cb6r4_ae6.expr'  # for full run
], prefix='raqms')

# %%
# Translate RAQMS for use by CMAQ
# -------------------------------

# For "real" VGLVLS use
# METBDYD_PATH = '...'
# metaf = pnc.pncopen(METBDY3D_PATH, format='ioapi')
metaf = aqmbc.options.getmetaf(bctype='bcon', gdnam=gdnam, vgnam='EPA_35L')
inpaths = sorted(glob.glob('RAQMS/uwhyb*.nc'))
bcpaths = []
suffix = f'_{gdnam}_BCON.nc'
gcdims = aqmbc.options.dims['raqms']
for inpath in inpaths:
    print(inpath, flush=True)
    outpath = basename(inpath).replace('.nc', suffix)
    history = f'From {outpath}'
    outf = aqmbc.bc(
        inpath, outpath, metaf, vmethod='linear', exprpaths=exprpaths,
        dimkeys=gcdims, format_kw={'format': 'raqms'}, history=history,
        clobber=True, verbose=0
    )
    bcpaths.append(outpath)

# %%
# Figures and Statistics
# ----------------------

vprof = aqmbc.report.get_vertprof(bcpaths)
statdf = aqmbc.report.getstats(bcpaths)
sumdf = aqmbc.report.summarize(statdf)
sumdf.to_csv('raqms_summary.csv')

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
    xlim=(None, 100), ylabel='VGLVLS [$(p - p_t) / (p_s - p_t)$]', ylim=(1, 0))
axx[1].set(xscale='log', xlabel='{long_name} [{units}]'.format(**v2.attrs))
fig.suptitle('RAQMS Boundary Conditions for CMAQ')
fig.savefig('raqms_profiles.png')

# %%
# Barplot of Concentrations
# -------------------------

fig, axx = plt.subplots(
    2, 1, figsize=(18, 8), dpi=72, gridspec_kw=dict(hspace=.8, bottom=0.15)
)
gasds = sumdf.query('unit == "ppmV"').xs('Overall')['median']
aqmbc.report.barplot(gasds.sort_values(), bar_kw=dict(ax=axx[0]))
pmds = sumdf.query('unit == "micrograms/m**3"').xs('Overall')['median']
aqmbc.report.barplot(pmds.sort_values(), bar_kw=dict(ax=axx[1]))
fig.savefig('raqms_bar.png')
