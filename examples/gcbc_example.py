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
# Using gc14_o3so4.expr, which only uses ozone and sulfate aerosols.
#

print(aqmbc.exprlib.avail('gc'))  # Show all possible expressions
exprpaths = aqmbc.exprlib.exprpaths([                      # for a full run,
    'gcnc_airmolden.expr',                                 # keep this
    'gc14_o3so4.expr',                                     # Comment this
    # 'gc14_to_cb6r5.expr', 'gc14_to_cb6mp.expr',          # Uncomment this
    # 'gc14_soas_to_ae7.expr'                              # uncomment this
], prefix='gc')


# %%
# Tranlate Files and Make Time-independent
# ----------------------------------------

gdnam = '12US1'
gcdims = aqmbc.options.dims['gc']
suffix = f'_{gdnam}_BCON.nc'
metaf = aqmbc.options.getmetaf(bctype='bcon', gdnam=gdnam, vgnam='EPA_35L')

# For "real" VGLVLS use
# METBDY3D_PATH = '...'
# METCRO3D_PATH = '...'
# metaf = pnc.pncopen(METBDY3D_PATH, format='ioapi').subset(['PRES'])
# pnc.conventions.ioapi.add_cf_from_ioapi(metaf)

bcpaths = []
for inpath in inpaths:
    print(inpath, flush=True)
    outpath = basename(inpath).replace('.nc4', suffix)
    history = f'From {outpath}'
    outf = aqmbc.bc(
        inpath, outpath, metaf, vmethod='linear', exprpaths=exprpaths,
        dimkeys=gcdims, format_kw={'format': 'gcbench'}, history=history,
        clobber=True, verbose=0, timeindependent=True
    )

    bcpaths.append(outpath)

# %%
# Figures and Statistics
# ----------------------

vprof = aqmbc.report.get_vertprof(bcpaths)
statdf = aqmbc.report.getstats(bcpaths)
statdf.to_csv('gcbc_summary.csv')

# %%
# Plot Vertical Profiles
# ~~~~~~~~~~~~~~~~~~~~~~

fig = aqmbc.report.plot_2spc_vprof(vprof)
fig.suptitle('GEOS-Chem v14 Boundary Conditions for CMAQ')
fig.savefig('gcbc_profiles.png')

# %%
# Plot Normalized Means
# ~~~~~~~~~~~~~~~~~~~~~

fig = aqmbc.report.plot_gaspm_bars(statdf)
fig.savefig('gcbc_bar.png')
