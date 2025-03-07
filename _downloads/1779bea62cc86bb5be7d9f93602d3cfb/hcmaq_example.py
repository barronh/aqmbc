"""
Hemispheric CMAQ LBC for CMAQ
=============================

This example shows how to use aqmbc with a synthetic Hemispheric CMAQ.

* Create synthetic exmaple files.
* Extract assuming no translation (same gas and aerosols as target).
* Display figures and statistics.

"""

from os.path import basename
import aqmbc
import numpy as np
import matplotlib.pyplot as plt

# %%
# Create Fake Hemispheric CMAQ Files
# ----------------------------------

inpaths = [
    'HCMAQFAKECONC.20190401_0000z.nc4',
    'HCMAQFAKECONC.20190701_0000z.nc4',
]
tmpf = aqmbc.options.getmetaf(
    bctype='icon', gdnam='5940NHEMI2', vgnam='EPA_44L'
)
keys = ['O3', 'ASO4I', 'ASO4J']
for k in keys:
    v = tmpf.createVariable(k, 'f', ('TSTEP', 'LAY', 'ROW', 'COL'))
    v.setncatts(dict(long_name=k.ljust(16), var_desc=k.ljust(80)))

tmpf.variables['ASO4I'].units = 'micrograms/m**3'.ljust(16)
tmpf.variables['ASO4J'].units = 'micrograms/m**3'.ljust(16)
tmpf.variables['O3'].units = 'ppmV'.ljust(16)
tgtx = np.log(tmpf.VGLVLS[1:])
o3vals = np.interp(tgtx, np.log([.01, .2, .3, 1]), [1, .1, .06, .04])
so4vals = np.interp(tgtx, np.log([.01, .2, .6, .9, 1]), [.06, .06, 0.2, 1, 1])
for i, (inpath, factor) in enumerate(zip(inpaths, [1, .9])):
    tmpf.variables['O3'][:] = o3vals[None, :, None, None] * factor
    tmpf.variables['ASO4I'][:] = so4vals[None, :, None, None] * 0.01 * factor
    tmpf.variables['ASO4J'][:] = so4vals[None, :, None, None] * 0.99 * factor
    tmpf.subset(keys).save(inpath, format='NETCDF3_CLASSIC', verbose=0).close()

# %%
# Tranlate Files and Make Time-independent
# ----------------------------------------

gdnam = '12US1'
suffix = f'_{gdnam}_BCON.nc'
metaf = aqmbc.options.getmetaf(bctype='bcon', gdnam=gdnam, vgnam='EPA_35L')
# For "real" VGLVLS use
# METBDYD_PATH = '...'
# metaf = pnc.pncopen(METCRO3D_PATH, format='ioapi')

bcpaths = []
for inpath in inpaths:
    print(inpath, flush=True)
    outpath = basename(inpath).replace('.nc4', suffix)
    history = f'From {outpath}'
    outf = aqmbc.bc(
        inpath, outpath, metaf, vmethod='linear',
        exprpaths=[], format_kw={'format': 'ioapi'}, history=history,
        clobber=True, verbose=0
    )
    if outf is not None:
        # if not already archived
        aqmbc.cmaq.timeindependent(outf)

    bcpaths.append(outpath)

# %%
# Figures and Statistics
# ----------------------

vprof = aqmbc.report.get_vertprof(bcpaths)
statdf = aqmbc.report.getstats(bcpaths)
statdf.to_csv('hcmaq_summary.csv')

# %%
# Visualize Vertical Profiles
# ---------------------------

fig = aqmbc.report.plot_2spc_vprof(vprof)
fig.suptitle('Fake Hemispheric CMAQ Boundary Conditions for CMAQ')
fig.savefig('hcmaq_profiles.png')

# %%
# Barplot of Concentrations
# -------------------------

fig = aqmbc.report.plot_gaspm_bars(statdf)
fig.savefig('hcmaq_bar.png')
