"""
Hemispheric CMAQ LBC for CMAQ
=============================

This example shows how to use aqmbc with a synthetic Hemispheric CMAQ.

* Create synthetic exmaple files.
* Extract assuming no translation (same gas and aerosols as target).
* Display figures and statistics.

"""

import PseudoNetCDF as pnc
from os.path import basename, join, exists
from os import makedirs
import aqmbc
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mc
import copy
import requests
import tarfile

# %%
# Create Fake Hemispheric CMAQ Files
# ----------------------------------

inpaths = [
    'HCMAQFAKECONC.20190401_0000z.nc4',
    'HCMAQFAKECONC.20190701_0000z.nc4',
]
tmpf = aqmbc.options.getmetaf(bctype='icon', gdnam='5940NHEMI2', vgnam='EPA_44L')
keys = ['O3', 'ASO4I', 'ASO4J']
for k in keys:
    v = tmpf.createVariable(k, 'f', ('TSTEP', 'LAY', 'ROW', 'COL'))
    v.setncatts(dict(long_name=k.ljust(16), var_desc=k.ljust(80), units='micrograms/m**3'.ljust(16)))

tmpf.variables['O3'].units = 'ppmV'.ljust(16)
o3vals = np.interp(np.log(tmpf.VGLVLS[1:]), np.log([.01, .2, .3, 1]), [1, .1, .06, .04])
so4vals = np.interp(np.log(tmpf.VGLVLS[1:]), np.log([.01, .2, .6, .9, 1]), [.06, .06, 0.2, 1, 1])
#so4vals = 0.02 * 100**tmpf.VGLVLS
for i, inpath in enumerate(inpaths):
    tmpf.variables['O3'][:] = o3vals[None, :, None, None] * .9**i
    tmpf.variables['ASO4I'][:] = so4vals[None, :, None, None] * 0.01 * .9**i
    tmpf.variables['ASO4J'][:] = tmpf.variables['ASO4I'][:] * 99

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
sumdf = aqmbc.report.summarize(statdf)
sumdf.to_csv('hcmaq_summary.csv')

# %%
# Plot Verical Profiles
# ~~~~~~~~~~~~~~~~~~~~~

v1 = vprof['O3'] * 1000
v1.attrs.update(vprof['O3'].attrs)
v2 = vprof['ASO4I'] + vprof['ASO4J']
v2.attrs.update(vprof['ASO4I'].attrs)
v2.attrs['long_name'] = 'ASO4IJ'

fig, (ax0, ax1) = plt.subplots(1, 2, figsize=(18, 6), dpi=72, sharey=True)
cmap = plt.cm.hsv
nt = v1.sizes['TSTEP']
for ti, t in enumerate(v1.TSTEP):
    label = inpaths[ti].split('_')[0].split('.')[-1][:-2]
    ax0.plot(v1.sel(TSTEP=t), v1.LAY, label=label, color=cmap(ti / nt))
    ax1.plot(v2.sel(TSTEP=t), v2.LAY, label=label, color=cmap(ti / nt))
ax0.legend()
ax1.legend()

ax0.set(
    xscale='log', xlabel='{long_name} [{units}]'.format(**v1.attrs),
    xlim=(None, 100), ylabel='VGLVLS [$(p - p_t) / (p_s - p_t)$]', ylim=(1, 0))
ax1.set(xscale='log', xlabel='{long_name} [{units}]'.format(**v2.attrs))
fig.suptitle('Fake Hemispheric CMAQ Boundary Conditions for CMAQ')
fig.savefig('hcmaq_profiles.png')

# %%
# Plot Normalized Means
# ~~~~~~~~~~~~~~~~~~~~~

gasds = sumdf.query('unit == "ppmV"').xs('Overall')['median']
pmds = sumdf.query('unit == "micrograms/m**3"').xs('Overall')['median']

fig, (gax, pax) = plt.subplots(2, 1, figsize=(18, 8), dpi=72, gridspec_kw=dict(hspace=.8, bottom=0.15))
aqmbc.report.barplot(gasds.sort_values(), bar_kw=dict(ax=gax))
aqmbc.report.barplot(pmds.sort_values(), bar_kw=dict(ax=pax))
fig.savefig('hcmaq_bar.png')