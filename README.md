# aqmbc

Air Quality Model Boundary Condition Tools

Air Quality Model Boundary Conditions is a tool to create time and space
boundary conditions for an Air Quality Model from one or many data sources.

## Installation

pip install https://github.com/barronh/aqmbc.git

## Example

```bash
python -m aqmbc --template examples
cd examples
# Edit a configuration file to point to your inputs/outputs
# - gcncv12.cfg
# - gcnd49v11.cfg
# - raqms.cfg
python -m aqmbc gcncv12.cfg
# If using raqms, run python raqms.py
```

## Prerequisites

- PseudoNetCDF (github.com/barronh/PseudoNetCDF).
- pyproj
