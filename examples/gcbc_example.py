"""
GEOS-Chem Benchmark LBC for CMAQ
================================

This example shows how to use aqmbc with GEOS-Chem's publicly available
benchmark outputs.

* Dowload from Harvard (if not previously downloaded).
* Define translations.
* Extract, translate, and create time-independent files.
* Display figures and statistics.

Time-independence allows files to be used in CMAQ with multiple dates in the
same month, or as a climatology for other years."""

from os.path import basename, exists
import aqmbc
import matplotlib.pyplot as plt
import requests
import tarfile

# %%
# Download from Harvard
# ---------------------

inpaths = [
    'OutputDir/GEOSChem.SpeciesConc.20190401_0000z.nc4',
    'OutputDir/GEOSChem.SpeciesConc.20190701_0000z.nc4',
]
if any([not exists(p) for p in inpaths]):
    # Download 7G tar file
    rurl = 'http://ftp.as.harvard.edu/gcgrid/geos-chem/1yr_benchmarks/'
    url = f'{rurl}/14.0.0-rc.0/GCClassic/FullChem/OutputDir.tar.gz'
    dest = basename(url)
    if not exists(dest):
        with requests.get(url, stream=True) as r:
            r.raise_for_status()
            with open(dest, 'wb') as f:
                for chunk in r.iter_content(chunk_size=1024*1024):
                    f.write(chunk)
    else:
        print('Using cached OutputDir.tar.gz')

    # Unzip only files that will be used.
    tf = tarfile.open(dest)
    for memb in tf.getmembers():
        if memb.path in inpaths:
            if not exists(memb.path):
                tf.extract(memb)
            else:
                print('Using cached', memb.path)

# %%
# Define Chemical Translation
# ---------------------------
#
# Using gcbench14_o3so4, which only uses ozone and sulfate aerosols.
# To expand, select from expressions available gc14 expressions and modify them:
# 1. Typically used with BoundaryConditions (prefix SpeciesBC_), which requires
#    updating for SpeciesConc (prefix SpeciesConc_).
# 2. Output does not have pressure (surface or mid) or temperature variables.
#    For simplicity, we use a US standard atmosphere as a surrogate.
#
print(aqmbc.exprlib.avail('gc'))
exprpaths = aqmbc.exprlib.exprpaths([
    #                                                      # for a full run,
    'gcbench14_o3so4.expr'                                 # 1. comment this
    # 'gcnc_usstd_airmolden.expr', 'gc14_to_cb6r5.expr',   # 2. uncomment this
    # 'gc14_to_cb6mp.expr', 'gc14_soas_to_ae7.expr'        # 3. uncomment this
], prefix='gc')

#                                                          # 4. uncomment these
# import os
# os.makedirs('tempdef', exist_ok=True)
# exprpaths = list(exprpaths)
# for i, path in enumerate(exprpaths):
#     with open(path, 'r') as inf:
#         txt = inf.read()
#     outpath = os.path.join('tempdef', basename(path))
#     with open(outpath, 'w') as outf:
#         outf.write(txt.replace('SpeciesBC_', 'SpeciesConc_'))
#     exprpaths[i] = outpath


# %%
# Tranlate Files and Make Time-independent
# ----------------------------------------

gdnam = '12US1'
gcdims = aqmbc.options.dims['gc']
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
        inpath, outpath, metaf, vmethod='linear', exprpaths=exprpaths,
        dimkeys=gcdims, format_kw={'format': 'gcnc'}, history=history,
        clobber=True, verbose=0, timeindependent=True
    )

    bcpaths.append(outpath)

# %%
# Figures and Statistics
# ----------------------

vprof = aqmbc.report.get_vertprof(bcpaths)
statdf = aqmbc.report.getstats(bcpaths)
sumdf = aqmbc.report.summarize(statdf)
sumdf.to_csv('gcbc_summary.csv')

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
fig.suptitle('GEOS-Chem v14 Boundary Conditions for CMAQ')
fig.savefig('gcbc_profiles.png')

# %%
# Plot Normalized Means
# ~~~~~~~~~~~~~~~~~~~~~

gasds = sumdf.query('unit == "ppmV"').xs('Overall')['median']
pmds = sumdf.query('unit == "micrograms/m**3"').xs('Overall')['median']

fig, (gax, pax) = plt.subplots(
    2, 1, figsize=(18, 8), dpi=72, gridspec_kw=dict(hspace=.8, bottom=0.15)
)
aqmbc.report.barplot(gasds.sort_values(), bar_kw=dict(ax=gax))
aqmbc.report.barplot(pmds.sort_values(), bar_kw=dict(ax=pax))
fig.savefig('gcbc_bar.png')
