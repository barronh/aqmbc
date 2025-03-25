__all__ = [
    'bc', 'runcfg', 'bcon', 'exprlib', 'options', 'cmaq', 'report', 'models'
]

import os
import io
import pandas as pd
import PseudoNetCDF as pnc
import numpy as np
import warnings
import configparser
from .bcon import bc
from . import bcon
from . import exprlib
from . import options
from . import cmaq
from . import report
from . import models


__doc__ = """
Code for making CMAQ-ready boundary condition files

Contents
========

* bcon : module with functions for making boundary condition files
* cmaq : module for making files CMAQ ready
* report : module with convenience functions for reporting
* defnpath : string path to all definition files available in examples.
* runcfg : Function to run aqmbc from configuration files


Examples
========

Ex Python GEOS-Chem
-------------------

import PseudoNetCDF as pnc
import aqmbc

inpath = '/path/to/geoschem.nc'
bcpath = 'BCON.nc'
# using built in expressions
exprpaths = [f'{aqmbc.defnpath}/gc/gcnc_airmolden.expr',
             f'{aqmbc.defnpath}/gc/gc14_to_cb6r5.expr']
metaf = pnc.pncopen('/path/to/METCRO3D_ANYDATE', format='ioapi')
bc(inpath, bcpath, metaf, vmethod='linear', exprpaths=exprpaths,
   dimkeys=dict(TSTEP='time', LAY='lev', ROW='lat', COL='lon'),
   format_kw='gcnc', history='just a test')


Ex Scripting
------------

python -m aqmbc -t runfolder
cd runfolder
# copy a cfg file as run.cfg
# edit run.cfg for your application.
python -m aqmbc run.cfg

Version History
===============

* 0.4.2: Added geoschem benchmark quick reader and timeindependent options
         to the config approach.
         Adding improved documentation.
* 0.4.1: Update bc and cmaqready to apply a minimum value and allow inpaths
         to be provided by a template. The minimum value (minvalue) can be
         set in the common configuration section. Also, improved reporting
         functions and automated reporting via the config file.
* 0.4.0: Change verbose to string for newer configparser compat
         Update FILEDESC and HISTORY outputs to limit to 60*80 char
         Added cmaq module with cmaqready to stack, interpolate, and
         when necessary clean metadata.
         Added some reporting tools, expression library and examples.
         Needs better documentation on many objects.
"""

__version__ = '0.4.2'

defnpath = os.path.join(os.path.dirname(__file__), 'examples', 'definitions')


def loadcfg(cfgobjs, cfgtype='path'):
    """
    Arguments
    ---------
    cfgobjs : list
        List of configuration objects
    cfgtype : str
        path, file, dict

    Returns
    -------
    config : configparser.ConfigParser
        Configuration loaded with defaults added.
    """
    config = configparser.ConfigParser(
        default_section='common',
        interpolation=configparser.ExtendedInterpolation()
    )
    vglvlstxt = """[
    1.0, 0.9975, 0.995, 0.99, 0.985, 0.98, 0.97, 0.96, 0.95, 0.94,
    0.93, 0.92, 0.91, 0.9, 0.88, 0.86, 0.84, 0.82, 0.8, 0.77,
    0.74, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3,
    0.25, 0.2, 0.15, 0.1, 0.05, 0.0
    ]
"""
    defopts = {
        'common': {
            'overwrite': False, 'verbose': '0', 'PWD': os.getcwd(),
            'vgtop': '5000', 'vglvls': vglvlstxt, 'vinterp': 'linear',
            'expressions': '[]', 'griddesc': 'GRIDDESC', 'minvalue': '1e-30'
        },
        'REPORT': {
            'summaryspcs': '[]', 'vprofspcs': '[]', 'standardfigs': 'Y',
            'summary': 'bcon_summary.csv', 'vprofmean': 'bcon_mean.nc4',
            'vprofmin': 'bcon_min.nc4', 'vprofmax': 'bcon_max.nc4',
            'debug': '0'
        },
        'BCON': {
            'freq': 'd', 'output': 'BCON_%Y-%m-%d.nc', 'timeindependent': False
        },
        'ICON': {
            'output': 'ICON_%Y-%m-%d.nc', 'timeindependent': True
        }
    }

    if cfgtype == 'path':
        defopts['common']['rcpath'] = os.path.dirname(
            os.path.realpath(cfgobjs[0])
        )
    print('Default options:')
    print(defopts)
    config.read_dict(defopts)

    if cfgtype == 'path':
        config.read(cfgobjs)
    elif cfgtype == 'file':
        for cfgf in cfgobjs:
            config.read_file(cfgf)
    elif cfgtype == 'dict':
        for cfgd in cfgobjs:
            config.read_dict(cfgd)
    else:
        raise ValueError(
            'cfgtype must be either path, file or dict; got {cfgtype}'
        )

    return config


def runcfg(
    cfgobjs, cfgtype='path', warningfilter='ignore', dryrun=False, speedup=None
):
    """
    Arguments
    ---------
    cfgobjs : list
        List of paths, files, or dictionaries
    cfgtype : str
        'path', 'file', or 'dict'
    warningfilter : str
        str accepted by warnings.simplefilter
    dryrun : bool
        If True, return config after testing parsing.
    speedup : bool or None
        If True, use more memory but run faster. If None, heursitcally decide.

    Returns
    -------
    None
    """
    import json
    warnings.simplefilter(warningfilter)
    config = loadcfg(cfgobjs, cfgtype=cfgtype)
    infmt = config.get('source', 'format')
    infmt = json.loads(infmt)
    intmpl = config.get('source', 'input')
    dimkeys = config.get('source', 'dims')
    dimkeys = json.loads(dimkeys)

    ictmpl = config.get('ICON', 'output')
    ictimeindependent = config.get('ICON', 'timeindependent')
    bctmpl = config.get('BCON', 'output')
    bctimeindependent = config.get('BCON', 'timeindependent')
    overwrite = config.getboolean('common', 'overwrite')
    interpopt = config.get('common', 'vinterp')

    gdnam = config.get('common', 'gdnam')
    minvalue = eval(config.get('common', 'minvalue'))
    vgtop = config.getfloat('common', 'vgtop')
    vgtop = np.float32(vgtop)
    vglvls = json.loads(config.get('common', 'vglvls'))
    vglvls = np.array(vglvls, dtype='f')
    # config parser does not allow number-first strings, so they
    # are explicitly quoted, which is interpreted as part of the string
    freq = config.get('BCON', 'freq')
    if freq.startswith('"') or freq.startswith("'"):
        freq = freq[1:-1]
    bdates = pd.date_range(
        config.get('BCON', 'start_date'),
        config.get('BCON', 'end_date'),
        freq=freq
    )
    tslice = None

    exprpaths = config.get('common', 'expressions')
    exprpaths = json.loads(exprpaths)

    if dryrun:
        return config

    bmetaf = pnc.pncopen(
        config.get('common', 'GRIDDESC'),
        format='griddesc', GDNAM=gdnam, FTYPE=2,
        VGLVLS=vglvls, VGTOP=vgtop
    )
    for bdate in bdates:
        inpath = bdate.strftime(intmpl)
        outpath = bdate.strftime(bctmpl)
        outdir = os.path.dirname(outpath)
        os.makedirs(outdir, exist_ok=True)
        opts = dict(
            inpath=inpath, outpath=outpath, metaf=bmetaf,
            tslice=tslice, vmethod=interpopt,
            exprpaths=exprpaths, clobber=overwrite,
            dimkeys=dimkeys, format_kw=infmt, speedup=speedup,
            minvalue=minvalue, timeindependent=bctimeindependent
        )
        tmp = io.StringIO()
        config.write(tmp)
        tmp.seek(0, 0)
        opts['history'] = tmp.read()
        print(opts['history'])
        bc(**opts)

    imetaf = pnc.pncopen(
        config.get('common', 'griddesc'),
        format='griddesc', GDNAM=gdnam, FTYPE=1,
        VGLVLS=vglvls, VGTOP=vgtop
    )
    idates = pd.to_datetime(json.loads(config.get('ICON', 'dates')))
    tslice = 0
    for idate in idates:
        inpath = idate.strftime(intmpl)
        outpath = idate.strftime(ictmpl)
        outdir = os.path.dirname(outpath)
        os.makedirs(outdir, exist_ok=True)
        opts = dict(
            inpath=inpath, outpath=outpath, metaf=imetaf,
            tslice=tslice, vmethod=interpopt,
            exprpaths=exprpaths, clobber=overwrite,
            dimkeys=dimkeys, format_kw=infmt, speedup=speedup,
            timeindependent=ictimeindependent
        )

        tmp = io.StringIO()
        config.write(tmp)
        tmp.seek(0, 0)
        opts['history'] = tmp.read()
        bc(**opts)
