"""
GEOS-Chem Benchmark LBC for CMAQ
================================

This example shows how to use aqmbc with GEOS-Chem's publicly available
benchmark outputs.

* Download from Harvard (if not previously downloaded).
* Extract, translate, and create time-independent files.
* Display figures and statistics.

Time-independence allows files to be used in CMAQ with multiple dates in the
same month, or as a climatology for other years."""


# %%
# Scope Definitions
# -----------------
# - GDNAM defines the horizontal CMAQ domain from the default GRIDDESC file.
#   - the default GRIDDESC has some 12km US domains (12US2, 12US1), a 36km
#     North American domain (36US3), a hemispheric polar stereographic grid
#     (108NHEMI2), and a test domain for the US at 108km (108US2).
#   - add gdpath='...' to use your own GRIDDESC file.
# - VGNAM is used to define the vertical
#   - known VGNAM inclue WRFHYBRID_35L, WRFHYBRID_44L, EMBER_35L
#   - add vgpath='...' to use your own CSV file to define A and B
#     components of a vertical coordinate (P=A+B*ps [Pa])
# - dates are the dates from which to derive BCON and ICON
#   - This project uses two dates as an example.
#   - More typical would be hourly or 3-hourly in chunks that cover a day

GDNAM = '108US2'
VGNAM = 'WRFHYBRID_35L'
dates = ['2019-04-01T00:00', '2019-07-01T00:00']

# %%
# Download from Harvard
# ---------------------
#
# In the example, the archive was downloaded and unzipped in inputs/OutputDir
#

# %%
# Define Configuration
# --------------------

import aqmbc

config = {
    "source": "gcbench",
    "intmpl": 'inputs/OutputDir/GEOSChem.SpeciesConc.%Y%m%d_0000z.nc4',
    "GDNAM": GDNAM, "VGNAM": VGNAM,  # Destination Horizontal and Vertical Grids
    "bcon_dates": dates, "icon_dates": dates[:1],
    "exprs": ["gc14_o3so4.json"],  # comment out; default to cb6_ae7
}
outpaths = aqmbc.driver(config)

# %%
# Figures and Statistics
# ----------------------

vprof = aqmbc.report.profile_report(outpaths['bcon'])

# %%
# Report Range of Values
# ----------------------

statdf = aqmbc.report.range_report(vprof)
statdf.to_csv('outputs/docs/gcbc_range.csv')

# %%
# Visualize Vertical Profiles
# ---------------------------

import matplotlib.pyplot as plt

fig, axx = plt.subplots(1, 2, figsize=(12, 6))
vprof['O3'].sel(PERIM='all', STAT='median').plot.line(y='LAY', ax=axx[0])
vprof['ASO4J'].sel(PERIM='all', STAT='median').plot.line(y='LAY', ax=axx[1])
axx[0].set(ylim=(1, 0), xscale='log', xlabel='O3 [ppmv]')
axx[1].set(ylim=(1, 0), xscale='log', xlabel='ASO4J [micrograms/m**3]')
fig.savefig('outputs/figs/gcbc_profile.png')
