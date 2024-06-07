"""
GEOS-CF LBC for CMAQ
================================

This example shows how to use aqmbc with GEOS-CF's publicly available OpenDAP.

* Download from NASA GMAO (if not available in %Y/%m/%d folder).
* Define translation.
* Extract and translate.
* Display figures and statistics."""

from os.path import basename
import aqmbc
import matplotlib.pyplot as plt
import glob

gdnam = '12US1'

# %%
# Download from GMAO OpenDAP
# --------------------------

dates = ['2023-04-15T12:30', '2023-07-15T12:30']
# Typical downloading takes ~4 minutes per hour of source data
# For the tutorial, we only download 'o3' and 'so4' to make it fast.
aqmbc.models.geoscf.download_window(
    gdnam, dates,
    chmvars=['o3', 'so4'], xgcvars=[]  # for full run, comment out this line
)

# %%
# Define Translation Expressions
# ------------------------------

# In Notebooks, display available expressions
aqmbc.exprlib.avail('cf')

# %%

# A real run will use geoscf_met.expr, geoscf_cb6.expr and geoscf_ae7.expr
# For simplicity, we use just a simple ozone exmaple
exprpaths = aqmbc.exprlib.exprpaths([
    'geoscf_o3so4.expr'                      # for full run, comment
    # 'geoscf_met.expr', 'geoscf_cb6.expr',  # for full run, uncomment
    # 'geoscf_ae7.expr'                      # for full run, uncomment
], prefix='cf')

# %%
# Translate GEOS-CF for use by CMAQ
# ---------------------------------

# For "real" VGLVLS use
# METBDYD_PATH = '...'
# metaf = pnc.pncopen(METBDY3D_PATH, format='ioapi')
metaf = aqmbc.options.getmetaf(bctype='bcon', gdnam=gdnam, vgnam='EPA_35L')
inpaths = sorted(glob.glob(f'GEOSCF/{gdnam}/????/??/??/geoscf_*.nc'))
bcpaths = []
suffix = f'_{gdnam}_BCON.nc'
gcdims = aqmbc.options.dims['gc']
for inpath in inpaths:
    print(inpath, flush=True)
    outpath = basename(inpath).replace('.nc', suffix)
    history = f'From {outpath}'
    outf = aqmbc.bc(
        inpath, outpath, metaf, vmethod='linear', exprpaths=exprpaths,
        dimkeys=gcdims, format_kw={'format': 'geoscf'}, history=history,
        clobber=True, verbose=0
    )
    bcpaths.append(outpath)

# %%
# Figures and Statistics
# ----------------------

vprof = aqmbc.report.get_vertprof(bcpaths)
statdf = aqmbc.report.getstats(bcpaths)
statdf.to_csv('geoscf_summary.csv')

# %%
# Visualize Vertical Profiles
# ---------------------------

fig = aqmbc.report.plot_2spc_vprof(vprof)
fig.suptitle('GEOS-CF Boundary Conditions for CMAQ')
fig.savefig('geoscf_profiles.png')

# %%
# Barplot of Concentrations
# -------------------------

fig = aqmbc.report.plot_gaspm_bars(statdf)
fig.savefig('geoscf_bar.png')
