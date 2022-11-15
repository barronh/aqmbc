# aqmbc

Air Quality Model Boundary Condition Tools

Air Quality Model Boundary Conditions is a tool to create time and space
boundary conditions for an Air Quality Model from one or many data sources.

## Installation

```bash
pip install git+https://github.com/barronh/aqmbc.git
```

or 

```bash
pip install https://github.com/barronh/aqmbc/archive/refs/heads/main.zip
```

## Example

```bash
# Create a working directory with standard configurations
python -m aqmbc --template examples
cd examples
# Edit a standard configuration file to point to your inputs/outputs
# - gcncv12.cfg
# - gcnd49v11.cfg
# - raqms.cfg
# Or make your own cfg
python -m aqmbc gcncv12.cfg
# Right now, the raqms reader/interpolator must be defined at runtime
# If using raqms, run python raqms.py
```

This process makes files that mirror the global air quality model structure.
However, CMAQ requires hourly lateral boundary condition files with
instantaneous values for every hour edges (24/day + 1).

It is often convenient to concatenate all days in a month using `ncrcat` or
other tools. Below is an example using `PseudoNetCDF`.

```python
import PseudoNetCDF as pnc
import glob

paths = (
    sorted(glob.glob('BCON/*2016-01-*.12US1.BCON.nc'))
    + sorted(glob.glob('BCON/*2016-02-01*.12US1.BCON.nc'))
)
mf = pnc.pncmfopen(paths, format='ioapi', stackdim='TSTEP')
mf.save('BCON_2016-01.12US1.BCON.nc')
```

If your data has fewer than hourly values, you will also need to add
interpolation. Currently, these steps are not supported because the
possibilities are too varied. I recommend xarray for this type of
processing.

## How to Contribute

* If you add a new set of definitions (new version of GEOS-Chem or a new model),
  consider opening an issue on github and posting it there. It would be great to
  include these in future versions.
* If you find a bug, open an issue.

## Prerequisites

- PseudoNetCDF (github.com/barronh/PseudoNetCDF).
- pyproj
