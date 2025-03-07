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
statdf.to_csv('raqms_summary.csv')

# %%
# Visualize Vertical Profiles
# ---------------------------

fig = aqmbc.report.plot_2spc_vprof(vprof)
fig.suptitle('RAQMS Boundary Conditions for CMAQ')
fig.savefig('raqms_profiles.png')

# %%
# Barplot of Concentrations
# -------------------------

fig = aqmbc.report.plot_gaspm_bars(statdf)
fig.savefig('raqms_bar.png')
