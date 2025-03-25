"""
WACCM LBC for CMAQ
================================

This example shows how to use aqmbc with WACCM's publicly available forecasts.

* Download from waccm (only if not available in WACCM folder).
* Define translation.
* Extract and translate.
* Display figures and statistics."""

from os.path import basename
import aqmbc
import matplotlib.pyplot as plt
import glob

gdnam = '12US1'

# %%
# Download from waccm via HTTP
# ----------------------------

dates = ['2023-04-15', '2023-07-15']

aqmbc.models.waccm.download(dates)

# %%
# Define Translation Expressions
# ------------------------------

# In Notebooks, display available expressions
aqmbc.exprlib.avail('waccm')

# %%

exprpaths = aqmbc.exprlib.exprpaths([
    'waccm_o3so4.expr'                     # for full run, comment this
    # 'waccm_met.expr', 'waccm_cb6.expr',  # for full run, uncomment this
    # 'waccm_ae7.expr'                     # for full run, uncomment this
], prefix='waccm')

# %%
# Translate WACCM for use by CMAQ
# -------------------------------

# For "real" VGLVLS use
# METBDYD_PATH = '...'
# metaf = pnc.pncopen(METBDY3D_PATH, format='ioapi')
metaf = aqmbc.options.getmetaf(bctype='bcon', gdnam=gdnam, vgnam='EPA_35L')
inpaths = sorted(glob.glob('WACCM/f.e22*.nc'))
bcpaths = []
suffix = f'_{gdnam}_BCON.nc'
gcdims = aqmbc.options.dims['waccm']
for inpath in inpaths:
    print(inpath, flush=True)
    outpath = basename(inpath).replace('.nc', suffix)
    history = f'From {outpath}'
    outf = aqmbc.bc(
        inpath, outpath, metaf, vmethod='linear', exprpaths=exprpaths,
        dimkeys=gcdims, format_kw={'format': 'waccm'}, history=history,
        clobber=True, verbose=0
    )
    bcpaths.append(outpath)

# %%
# Figures and Statistics
# ----------------------

vprof = aqmbc.report.get_vertprof(bcpaths)
statdf = aqmbc.report.getstats(bcpaths)
statdf.to_csv('waccm_summary.csv')

# %%
# Visualize Vertical Profiles
# ---------------------------

fig = aqmbc.report.plot_2spc_vprof(vprof)
fig.suptitle('WACCM Boundary Conditions for CMAQ')
fig.savefig('waccm_profiles.png')

# %%
# Barplot of Concentrations
# -------------------------

fig = aqmbc.report.plot_gaspm_bars(statdf)
fig.savefig('waccm_bar.png')
