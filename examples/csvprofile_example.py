"""
Vertical Profile LBC for CMAQ
=============================

This example shows how to use aqmbc with a csv file.

* Create synthetic exmaple files.
* Extract assuming no translation (same gas and aerosols as target).
* Display figures and statistics."""

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
dates = ['2019-04-01T00']

# %%
# Create CSV on Disk
# ------------------
#
# - ps(Pa) is surface pressure and pmid(Pa) is mid-level pressure
# - lon(degrees_east) and lat(degrees_north) are required if spatially varying.
# - lev(none) is required if ps and pmid vary by lon/lat

csvpath = 'inputs/csvprofile.csv'
with open(csvpath, 'w') as csvf:
    csvf.write("""
ps(Pa),pmid(Pa),O3(ppmV),ASO4J(micrograms/m**3)
1e5,8e4,0.04,0.8
,6e4,0.05,0.2
,4e4,0.06,0.1
,2e4,0.08,0.04
,1e4,.4,0.02
,0.5e4,2,0.02
""")

# %%
# Define Configuration
# --------------------

import aqmbc

config = {
    "source": "csvprofile",
    "intmpl": csvpath,
    "GDNAM": GDNAM, "VGNAM": VGNAM,  # Destination Horizontal and Vertical Grids
    "bcon_dates": dates, "icon_dates": dates[:1],
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
statdf.to_csv('outputs/docs/csvprofile_range.csv')

# %%
# Visualize Vertical Profiles
# ---------------------------

import matplotlib.pyplot as plt

fig, axx = plt.subplots(1, 2, figsize=(12, 6))
vprof['O3'].sel(PERIM='all', STAT='median').plot.line(y='LAY', ax=axx[0])
vprof['ASO4J'].sel(PERIM='all', STAT='median').plot.line(y='LAY', ax=axx[1])
axx[0].set(ylim=(1, 0), xscale='log', xlabel='O3 [ppmv]')
axx[1].set(ylim=(1, 0), xscale='log', xlabel='ASO4J [micrograms/m**3]')
fig.savefig('outputs/figs/csvprofile_profiles.png')
