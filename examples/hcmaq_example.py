"""
Hemispheric CMAQ LBC for CMAQ
=============================

This example shows how to use aqmbc with a synthetic Hemispheric CMAQ.

* Create synthetic exmaple files.
* Extract assuming no translation (same gas and aerosols as target).
* Display figures and statistics.

"""

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

import pandas as pd

GDNAM = '108US2'
VGNAM = 'WRFHYBRID_35L'
dates = pd.date_range('2019-04-01T00', '2019-04-02T00', freq='1h')

# %%
# Download from RSIG
# ------------------
# - RSIG has 3D hemispheric data from equates for select species
# - the aqmbc cmaq bcon processors passes thru species by default.
# - so, here we just collect a few species for example.

# import xarray as xr
# import pyrsig
# xr.set_options(keep_attrs=True)
# bbox = (-160, 10, -50, 65)
# api = pyrsig.RsigApi(bbox=bbox, bdate='2019-04-01', edate='2019-04-02')
# fs = [api.to_ioapi(f'cmaq.equates.hemi.conc.{k}') for k in ['O3', 'PMF_SO4']]
# f = xr.merge(fs)
# f['O3'] = f['O3'] * 1000
# f['O3'].attrs.update(units='ppm')
# f['ASO4J'] = f['PMF_SO4'] * 0.99
# f['ASO4J'].attrs.update(long_name='ASO4J')
# f['ASO4I'] = f['PMF_SO4'] * 0.01
# f['ASO4I'].attrs.update(long_name='ASO4I')
# pyrsig.cmaq.save_ioapi(f, "inputs/CMAQ/cmaq.equates.hemi.conc.2019-04-01.nc")

# %%
# Define Configuration
# --------------------

import aqmbc

config = {
    "source": "cmaq",
    "intmpl": "inputs/CMAQ/cmaq.equates.hemi.conc.%Y-%m-%d.nc",
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

statdf = aqmbc.report.rangereport(vprof)
statdf.to_csv('outputs/docs/hcmaq_range.csv')

# %%
# Visualize Vertical Profiles
# ---------------------------

import matplotlib.pyplot as plt

fig, axx = plt.subplots(1, 2, figsize=(12, 6))
vprof['O3'].sel(PERIM='all', STAT='median').plot.line(y='LAY', ax=axx[0])
vprof['ASO4J'].sel(PERIM='all', STAT='median').plot.line(y='LAY', ax=axx[1])
axx[0].set(ylim=(1, 0), xscale='log', xlabel='O3 [ppmv]')
axx[1].set(ylim=(1, 0), xscale='log', xlabel='ASO4J [micrograms/m**3]')
fig.savefig('outputs/figs/hcmaq_profiles.png')
