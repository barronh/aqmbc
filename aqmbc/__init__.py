__all__ = ['bc', 'runcfg', 'cmaq', 'report']

import os
import io
import pandas as pd
import PseudoNetCDF as pnc
import numpy as np
import warnings
import configparser
from .bcon import bc


__doc__ = """
Code for making CMAQ-ready boundary condition files

Contents
========

bcon : module
    module with functions for making boundary condition files
cmaq : module
    module for making files CMAQ ready
report : module
    module with convenience functions for reporting
defnpath : str
    Path to all definition files available in examples.
runcfg : function
    Function to run aqmbc from configuration files


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

* 0.4.0: Change verbose to string for newer configparser compat
         Update FILEDESC and HISTORY outputs to limit to 60*80 char
         Added cmaq module with cmaqready to stack, interpolate, and
         when necessary clean metadata.
         Added some reporting tools, expression library and examples.
         Needs better documentation on many objects.
"""

__version__ = '0.4.0'

defnpath = os.path.join(os.path.dirname(__file__), 'examples', 'definitions')


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
    """
    import json
    warnings.simplefilter(warningfilter)
    config = configparser.ConfigParser(
        default_section='common',
        interpolation=configparser.ExtendedInterpolation()
    )
    defopts = {
        'common': {'overwrite': False, 'verbose': '0', 'PWD': os.getcwd()}
    }
    if cfgtype == 'path':
        defopts['common']['rcpath'] = os.path.dirname(
            os.path.realpath(cfgobjs[0])
        )
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

    infmt = config.get('source', 'format')
    infmt = json.loads(infmt)
    intmpl = config.get('source', 'input')
    dimkeys = config.get('source', 'dims')
    dimkeys = json.loads(dimkeys)

    ictmpl = config.get('ICON', 'output')
    bctmpl = config.get('BCON', 'output')
    overwrite = config.getboolean('common', 'overwrite')
    interpopt = config.get('common', 'vinterp')

    gdnam = config.get('common', 'gdnam')
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
            dimkeys=dimkeys, format_kw=infmt, speedup=speedup
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
            dimkeys=dimkeys, format_kw=infmt, speedup=speedup
        )

        tmp = io.StringIO()
        config.write(tmp)
        tmp.seek(0, 0)
        opts['history'] = tmp.read()
        bc(**opts)
