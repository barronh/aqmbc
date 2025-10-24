"""
Preparing AQMBC Output for CMAQ
===============================

CMAQ expects BCON files to have 25 instantaneous outputs that cover from 00Z
on the simulation day to 00Z on the next day. `aqmbc` is run on individual files,
which can be a single hour or a few hours. Therefore, often the `aqmbc` outputs
need to be combined.

This example uses single hour outputs from GEOS-CF to make CMAQ-ready BCON
inputs. That is what `aqmbc.cmaq.cmaqready` is for. To do its jobs, `cmaqready`
takes a `date` to be made, the `inpaths` to make it from, and the outpath to
save it to.

The example below creates two days of output from 18 input files. The
inputs cover 2023-04-30T21:30Z to 2023-05-03T00:30Z in 3-hour intervals.
To create the inputs, modify the geoscf_example.py script to run for more
hours. The outputs each cover 25 hours from 00Z to 00Z+1day. To run the
example, you must have already created the inputs. After the run is complete,
you will have the outputs.

Required Inputs:
 - geoscf_mcx_tavg_1hr_g1440x721_v36_2023-04-30T2130Z_12US1_BCON.nc
 - geoscf_mcx_tavg_1hr_g1440x721_v36_2023-05-01T0030Z_12US1_BCON.nc
 - ... 14 others ...
 - geoscf_mcx_tavg_1hr_g1440x721_v36_2023-05-02T2130Z_12US1_BCON.nc
 - geoscf_mcx_tavg_1hr_g1440x721_v36_2023-05-03T0030Z_12US1_BCON.nc

Produced Outputs:
 - geoscf_mcx_tavg_1hr_g1440x721_v36_2023-05-01_12US1_BCON_hourly.nc
 - geoscf_mcx_tavg_1hr_g1440x721_v36_2023-05-02_12US1_BCON_hourly.nc
"""

# %%
# Import libraries
# ----------------

from pandas import date_range, to_timedelta
import aqmbc

# %%
# User Inputs
# -----------

# Use the domain name for your domain
gdnam = '12US1'

# Define the date range of interest
outdates = date_range('2023-05-01', '2023-05-02', freq='1d')

# Define a strftime templates for paths from aqmbc (intmpl) that need to be
# concatenated and interpolated to make CMAQ-ready files (outtmpl)
intmpl = f'geoscf_mcx_tavg_1hr_g1440x721_v36_%Y-%m-%dT%H%MZ_{gdnam}_BCON.nc'
outtmpl = f'geoscf_mcx_tavg_1hr_g1440x721_v36_%Y-%m-%d_{gdnam}_BCON_hourly.nc'

# %%
# Daily Processing
# ----------------

# For each output date, concatenate input files and interpolate hourly output.
for date in outdates:
    # Define output path
    outpath = date.strftime(outtmpl)
    # Get paths for date-1day 21:30 ... date+1day 00:30 by 3-hours
    indates = date_range(date, freq='3h', periods=10) + to_timedelta('-2.5h')
    inpaths = indates.strftime(intmpl)
    # Make 1 output with 25h from 10 single-hour inputs
    aqmbc.cmaq.cmaqready(date, inpaths, outpath=outpath)
