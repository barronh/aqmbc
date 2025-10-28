"""
TCR LBC for CMAQ
================================

This example shows how to use aqmbc with TROPESS Composition Reanalysis (TCR)
files, which are available thru NASA Earthdata Search

* Define translation.
* Extract and translate.
* Display figures and statistics."""

import glob
import pandas as pd
import xarray as xr
import aqmbc

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
dates = pd.date_range('2021-01-01', '2021-12-01', freq='1MS')

# %%
# Download from GMAO OpenDAP
# --------------------------
# - Example files have been downloaded.
# - This section is shown for reference.

# aqmbc.models.tcr.download(dates, bbox=(-150, 10, -40, 65))
inpat = 'inputs/TCR2/tropess.gesdisc.eosdis.nasa.gov/data/*/*/*2021.nc'
paths = sorted(glob.glob(inpat))
with open('inputs/TCR2/TCR2_MON_2021.txt', 'w') as tcrf:
    tcrf.write('\n'.join(paths))

# %%
# Define Configuration
# --------------------

config = {
    "source": "tcr",
    "intmpl": f"inputs/TCR2/TCR2_MON_%Y.txt",
    "GDNAM": GDNAM, "VGNAM": VGNAM,  # Destination Horizontal and Vertical Grids
    "bcon_dates": dates, "icon_dates": dates[:1],
    "exprs": ["tcr_o3so4.json"], # comment this out to default to full cb6_ae7 definitions
}
outpaths = aqmbc.driver(config)

# %%
# Figures and Statistics
# ----------------------

vprof = aqmbc.report.profile_report(outpaths['bcon'])

# %%
# Visualize Vertical Profiles
# ---------------------------

import matplotlib.pyplot as plt
fig, axx = plt.subplots(1, 2, figsize=(12, 6))
vprof['O3'].sel(PERIM='all', STAT='median').plot.line(y='LAY', ax=axx[0])
vprof['ASO4J'].sel(PERIM='all', STAT='median').plot.line(y='LAY', ax=axx[1])
axx[0].set(ylim=(1, 0), xscale='log')
axx[1].set(ylim=(1, 0), xscale='log')

# %%
# Report Range of Values
# ----------------------

statdf = aqmbc.report.rangereport(vprof)
statdf
