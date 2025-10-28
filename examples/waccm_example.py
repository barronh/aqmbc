"""
WACCM LBC for CMAQ
================================

This example shows how to use aqmbc with WACCM's publicly available forecasts.

* Download from waccm (only if not available in WACCM folder).
* Define translation.
* Extract and translate.
* Display figures and statistics."""

import aqmbc
import pandas as pd
import xarray as xr

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
dates = pd.date_range('2025-04-15', periods=4, freq='6h')

# %%
# Download from NCAR
# --------------------------
# - Example files have been downloaded.
# - This section is shown for reference.

# aqmbc.models.waccm.download(dates)

# %%
# Define Configuration
# --------------------

config = {
    "source": "waccm",
    "intmpl": f"inputs/WACCM/f.e22.beta02.FWSD.f09_f09_mg17.cesm2_2_beta02.forecast.001.cam.h3.%Y-%m-%d-00000.nc",
    "GDNAM": GDNAM, "VGNAM": VGNAM,  # Destination Horizontal and Vertical Grids
    "bcon_dates": dates, "icon_dates": dates[:1],
    "exprs": ["waccm_o3so4.json"], # comment this out to default to full cb6_ae7 definitions
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
fig.savefig('figs/wacmm_profiles.png')

# %%
# Report Range of Values
# ----------------------

statdf = aqmbc.report.rangereport(vprof)
statdf.to_csv('outputs/docs/wacmm_range.csv')
