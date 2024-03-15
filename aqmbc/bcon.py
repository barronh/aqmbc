import os
import numpy as np
import PseudoNetCDF as pnc
import functools


def wndw(varfile, metaf, dimkeys, tslice, speedup=None, verbose=1):
    """
    Arguments
    ---------
    varfile : netcdf-like
        input file
    metafile : netcdf-like
        file with longitude and latitude

    Returns
    -------
    wndwf : file windows in lon/lat space
    i: indices for wndwf at metaf
    j: indices for wndwf at metaf
    """
    lon = metaf.variables['longitude']
    lat = metaf.variables['latitude']

    i, j = varfile.ll2ij(lon.ravel(), lat.ravel(), bounds='warn', clean='clip')
    i = i.reshape(lon.shape)
    j = j.reshape(lat.shape)
    if verbose > 3:
        import pandas as pd
        dimstr = '_'.join(lon.dimensions)
        gdnam = metaf.GDNAM.strip()
        cellcsv = f'{gdnam}_{dimstr}.csv'
        print(f'Saving cell mapping to {cellcsv}')
        outdata = dict(
            tgtlon=lon.ravel(), tgtlat=lat.ravel(), i=i.ravel(), j=j.ravel()
        )
        if 'lon' in varfile.variables:
            outdata['srclon'] = varfile.variables['lon'][i.ravel()]
            outdata['srclat'] = varfile.variables['lat'][j.ravel()]
        csvdf = pd.DataFrame(outdata)
        csvdf.index.name = 'ordinal'
        csvdf.to_csv(cellcsv)

    # Create indices for windowed file
    # purely for speed
    imin, imax = i.min(), i.max()
    jmin, jmax = j.min(), j.max()
    dni = imax - imin
    dnj = jmax - jmin
    sni = len(varfile.dimensions[dimkeys['COL']])
    snj = len(varfile.dimensions[dimkeys['ROW']])
    ifrac = dni / sni
    jfrac = dnj / snj
    if speedup is None:
        speedup = (ifrac < 0.5 or jfrac < 0.5)
    if speedup:
        # purely for speed, window the file
        if verbose > 0:
            print('window', flush=True)
        cslice = slice(imin, imax + 1)
        rslice = slice(jmin, jmax + 1)
        slices = {dimkeys['COL']: cslice, dimkeys['ROW']: rslice}
        if tslice is not None:
            slices[dimkeys['TSTEP']] = tslice
        wndwf = varfile.slice(verbose=verbose, **slices)
        iwndw = i - imin
        jwndw = j - jmin
    else:
        if tslice is not None:
            if verbose > 0:
                print('window', flush=True)
            wndwf = varfile.slice(**{dimkeys['TSTEP']: tslice})
        else:
            wndwf = varfile
        iwndw = i
        jwndw = j

    return wndwf, iwndw, jwndw


def ijslice(infile, metaf, i, j, dimkeys, verbose=1):
    """
    Arguments
    ---------
    infile : netcdf-like
        input file
    metafile : netcdf-like
        file with longitude and latitude

    Returns
    -------
    bconf : file at metaf
    """
    if verbose > 0:
        print('slice', flush=True)
    if 'ROW' in metaf.dimensions:
        dims = ('ROW', 'COL')
    else:
        dims = ('PERIM',)

    wslice = {dimkeys['COL']: i, dimkeys['ROW']: j}
    bconf = infile.slice(**wslice, newdims=dims, verbose=verbose)
    return bconf


def kinterp(infile, metaf, vmethod, verbose=1):
    """
    Arguments
    ---------
    infile : netcdf-like
        input file
    metaf : netcdf-like
        file with longitude and latitude
    vmethod : str
        method for vertical inteprolation (conserve or linear)

    Returns
    -------
    bconvf : file at new vertical levels
    """
    # Extract output vertical if not already the same
    tgt_vglvls = getattr(infile, 'VGLVLS', np.array([0], 'f'))
    src_vglvls = metaf.VGLVLS
    tgt_vgtop = getattr(infile, 'VGTOP', np.array([-1], 'f'))
    src_vgtop = metaf.VGTOP
    tgt_nlays = tgt_vglvls.size - 1
    src_nlays = metaf.VGLVLS.size - 1
    if tgt_nlays != src_nlays:
        lvinterp = True
    elif not (tgt_vglvls == src_vglvls).all():
        lvinterp = True
    elif not (tgt_vgtop == src_vgtop).all():
        lvinterp = True
    else:
        lvinterp = False

    if not lvinterp:
        bconvf = infile
    else:
        if verbose > 0:
            print('vint', flush=True)
        bconvf = infile.interpSigma(vglvls=metaf.VGLVLS, vgtop=metaf.VGTOP,
                                    verbose=verbose, interptype=vmethod)
        if not hasattr(bconvf, 'VGTYP'):
            bconvf.VGTYP = metaf.VGTYP

    return bconvf


def translate(infile, exprpaths, verbose=1):
    """
    Arguments
    ---------
    infile : netcdf-like
        File input
    exprpaths : list
        paths to expr file

    Returns
    -------
    outf : file output
    """
    # Translate species and/or units
    if len(exprpaths) == 0:
        outf = infile
    else:
        if verbose > 0:
            print('translate', flush=True)
        exprstr = ''.join([
            open(exprpath, 'r').read() for exprpath in exprpaths
        ])
        outf = infile.eval(exprstr, inplace=False)

    return outf


def bc(
    inpath, outpath, metaf,
    tslice=None, vmethod='conserve', exprpaths=None, clobber=False,
    dimkeys=None, format_kw=None, history='', speedup=None,
    timeindependent=False, verbose=1
):
    """
    Arguments
    ---------
    inpath : str
        path to input file
    outpath : str
        path to output file
    metaf : netcdf-like
        Metadata file (CRO for ICON, BDY for BCON)
    tslice : slice
        Optional time slice (e.g., slice(0) for ICON)
    vmethod : str
        method to use for vertical interpolation (conserve or linear)
    exprpaths : list
        text files with species translations
    clobber : bool
        overwrite existing files
    speedup : bool
        slice file to load into memory. More mem, but faster
    timeindependent: bool
        If True and input has just 1 time, write out as an IOAPI
        time-independent file.

    Returns
    -------
    None

    Notes
    -------
    * Saves BCON or ICON to file.
    * Operations:
        1. window
        2. horizontal extraction
        3. vertical interpolation
        4. species translation
    """
    global imin, imax, jmin, jmax, iwndw, jwndw, props
    if format_kw is None:
        format_kw = dict(format='ioapi')
    if dimkeys is None:
        dimkeys = {
            'ROW': 'ROW', 'COL': 'COL', 'TSTEP': 'TSTEP', 'LAY': 'LAY'
        }
    if not clobber and os.path.exists(outpath):
        print('Using cached', outpath, '...')
        return
    if verbose > 0:
        print('Converting', inpath, 'to', outpath)
    if verbose > 0:
        print('open', flush=True)
    infile = pnc.pncopen(inpath, **format_kw)

    # For debug speed, subset variables
    varfile = infile  # .subsetVariables(['O3']) # for testing

    wndwf, i, j = wndw(
        varfile, metaf, dimkeys, tslice,
        speedup=speedup, verbose=verbose
    )

    try:
        checkk = [
            k for k, v in wndwf.variables.items()
            if (
                k not in wndwf.dimensions
                and k != 'TFLAG'
                and len(v.shape) == 4
            )
        ][0]
        inij = np.prod(wndwf.variables[checkk].shape[2:])
        outij = metaf.variables['latitude'].size
        kfirst = inij < outij
    except Exception as e:
        print(str(e), 'vertical interp first')
        kfirst = True

    easyk = functools.partial(
        kinterp, metaf=metaf, vmethod=vmethod, verbose=verbose
    )
    easyij = functools.partial(
        ijslice, metaf=metaf, i=i, j=j, dimkeys=dimkeys, verbose=verbose
    )
    easyx = functools.partial(
        translate, exprpaths=exprpaths, verbose=verbose
    )

    if kfirst:
        funcs = [easyk, easyij, easyx]
    else:
        funcs = [easyij, easyk, easyx]

    outf = wndwf
    for func in funcs:
        outf = func(outf)

    if exprpaths is None:
        outf.FILEDESC = 'Boundary conditions from {}'.format(inpath)
    else:
        exprstr = ''.join([
            open(exprpath, 'r').read() for exprpath in exprpaths
        ])
        outf.FILEDESC = (
            'Boundary conditions from '
            + '{}\nwith definitions {}:'.format(inpath, exprpaths)
        )[:60*80]
        outf.description = exprstr

    fhistory = getattr(outf, 'HISTORY', '')
    history = fhistory + history
    setattr(outf, 'HISTORY', history)
    return saveioapi(
        wndwf, outf, outpath, metaf, dimkeys,
        timeindependent=timeindependent, verbose=verbose
    )


def saveioapi(
    inf, outf, outpath, metaf, dimkeys, timeindependent=False, verbose=1
):
    """
    Parameters
    ----------
    inf : netcdf-like file
        Must support getTimes method
    outf : netcdf-like file
        file for output
    metaf : netcdf-like file
        metadata file
    dimkeys : dict
        translation dictionary for dimensions
    timeindependent : bool
        If True and number of times is 1, the file will be stored as IOAPI
        time-independent

    Results
    -------
    out : netcdf-like file
        file that was output
    """
    from datetime import timedelta
    # Prepare metadata
    props = metaf.getncatts()
    for outdk, indk in dimkeys.items():
        if outdk not in outf.dimensions:
            if indk in outf.dimensions:
                outf.renameDimension(indk, outdk, inplace=True)

    if 'PERIM' in metaf.dimensions:
        outdims = ('TSTEP', 'LAY', 'PERIM')
    else:
        outdims = ('TSTEP', 'LAY', 'ROW', 'COL')

    outkeys = [
        vk
        for vk, vo in outf.variables.items()
        if (
            vo.dimensions == outdims
        )
    ]

    for ok in outkeys:
        outv = outf.variables[ok]
        outv.long_name = ok.ljust(16)
        outv.var_desc = ok.ljust(80)
        outv.units = outv.units.ljust(16)
        outv.actual_range = np.array([
            outv.min(), outv.max()
        ], dtype=outv.dtype)
        outv.actual_median = np.median(outv)

    extrakeys = set(list(outf.variables)).difference(outkeys + ['TFLAG'])
    for ek in extrakeys:
        if ek in outf.variables:
            del outf.variables[ek]

    props['NVARS'] = len(outkeys)
    props['VAR-LIST'] = ''.join([k.ljust(16) for k in outkeys])
    props['HISTORY'] = outf.HISTORY[:60*80]
    props['FILEDESC'] = outf.FILEDESC[:60*80]
    outf.setncatts(props)
    if 'VAR' not in outf.dimensions:
        outf.createDimension('VAR', props['NVARS'])

    if 'DATE-TIME' not in outf.dimensions:
        outf.createDimension('DATE-TIME', 2)

    for dk in list(outf.dimensions):
        if dk not in outdims + ('VAR', 'DATE-TIME'):
            del outf.dimensions[dk]
    # Get the actual times of the data
    time = inf.getTimes()
    p1h = timedelta(hours=1)
    if len(time) > 1:
        dt = np.diff(time).mean()
        dth = dt // p1h
        outf.TSTEP = dth * 10000
    else:
        if timeindependent:
            outf.TSTEP = 0
            dth = 0
        else:
            outf.TSTEP = 10000
            dth = 1
    if 'TFLAG' not in outf.variables:
        tflag = outf.createVariable(
            'TFLAG', 'i', ('TSTEP', 'VAR', 'DATE-TIME')
        )
        tflag.units = '<YYYYJJJ,HHMMSS>'
        tflag.long_name = 'TFLAG'
        tflag.var_desc = 'TFLAG'
        if dth == 0:
            tflag[:, :, :] = 0
        else:
            otime = time[0] + timedelta(hours=dth) * np.arange(len(time))
            JDATE = np.array([t.strftime('%Y%j') for t in otime], dtype='i')
            ITIME = np.array([t.strftime('%H%M%S') for t in otime], dtype='i')
            tflag[:, :, 0] = JDATE[:, None]
            tflag[:, :, 1] = ITIME[:, None]

    outf.SDATE = int(time[0].strftime('%Y%j'))
    outf.STIME = int(time[0].strftime('%H%M%S'))
    # Save to outpath
    if verbose > 0:
        print('save', flush=True)

    gigs = (
        np.prod([len(outf.dimensions[dk]) for dk in outdims]) *
        outf.NVARS * 4 / 1024**3
    )
    if gigs > 2:
        outformat = 'NETCDF3_64BIT_OFFSET'
    else:
        outformat = 'NETCDF3_CLASSIC'

    wverbose = max(verbose - 1, 0)
    out = outf.save(outpath, format=outformat, verbose=wverbose, outmode='w')

    if verbose > 0:
        print('done', flush=True)

    return out


def formatparser(fmtstr):
    """
    Parameters
    ----------
    fmtstr : str
        string with format and option key value pairs delimited by commas
        option key value pairs should be in a format consistent with
        dict call dict(key1=val1, key2=val2, ...)

    Returns
    -------
    out : dict
        format=first word
        otherkeys=key value pairs delimited by commas
    """
    pieces = fmtstr.split(',')
    out = dict(format=pieces[0])
    if len(pieces) > 1:
        opts = eval('dict(' + ','.join(pieces[1:]) + ')')
        out.update(**opts)

    return out


def dimparser(dimstr):
    """
    Parameters
    ----------
    dimstr : str
        key=value pairs delimited by commas

    Returns
    -------
    out : dict
        mapping table between IOAPI gridded and input dimensions
    """
    return dict([kv.split('=') for kv in dimstr.split(',')])


if __name__ == '__main__':
    import argparse
    # variables for metafile
    _vglvls = (1., 0.9975, 0.995, 0.99, 0.985, 0.98, 0.97, 0.96, 0.95, 0.94,
               0.93, 0.92, 0.91, 0.9, 0.88, 0.86, 0.84, 0.82, 0.8, 0.77,
               0.74, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3,
               0.25, 0.2, 0.15, 0.1, 0.05, 0.)
    _vgtop = np.float32(5000.)
    _gc_dimkeys = {
        'ROW': 'latitude',
        'COL': 'longitude',
        'TSTEP': 'time',
        'LAY': 'layer47'
    }
    parser = argparse.ArgumentParser()
    parser.add_argument('-O', '--clobber', default=False, action='store_true')
    parser.add_argument(
        '--format', default=None, type=formatparser,
        help=('File format for input files. CMAQ: "ioapi"; GEOS-Chem: ' +
              '"bpch,nogroup=True"')
    )
    parser.add_argument(
        '--dimkeys', default=None, type=dimparser,
        help=('Translations from IOAPI to input dimensions'
              'e.g., TSTEP=time,LAY=layer47,ROW=latitude,COL=longitude')
    )
    parser.add_argument(
        '--vglvls', type=lambda x: tuple(x.split(',')), default=_vglvls,
        help='Output vertical grid levels (WRF sigma)'
    )
    parser.add_argument(
        '--vgtop', default=_vgtop, type=np.float32,
        help='Top of model atmosphere in Pa')
    parser.add_argument('--grid', default=None, help='Grid name from GRIDDESC')
    parser.add_argument('--icon', default=False, action='store_true')
    parser.add_argument(
        '--expr', dest='exprpaths', default=[], action='append',
        help='Expressions for model'
    )
    parser.add_argument(
        '--interp', choices=['linear', 'conserve'], default=None,
        help=('Conserve is mass conserving and may be more complex without ' +
              'much benefit in some cases')
    )
    parser.add_argument('inpath')
    parser.add_argument('outpath')
    args = parser.parse_args()
    if args.format is None:
        if args.inpath.endswith('bpch'):
            args.format = dict(format='bpch', nogroup=True)
        else:
            args.format = dict(format='ioapi')

    if args.interp is None:
        if args.format['format'] == 'bpch':
            args.interp = 'linear'
        else:
            args.interp = 'conserve'

    if args.dimkeys is None and args.format['format'] == 'bpch':
        args.dimkeys = _gc_dimkeys

    metaf = pnc.pncopen(
        '../GRIDDESC', format='griddesc',
        VGLVLS=np.array(args.vglvls, dtype='f'), VGTOP=np.float32(args.vgtop),
        FTYPE=(1 if args.icon else 2),
        GDNAM=args.grid
    )
    if args.icon:
        tslice = metaf.createVariable('time', 'i', ('TSTEP',))
        tslice[0] = 0
    else:
        tslice = None

    bc(args.inpath, args.outpath, metaf,
       tslice=tslice, vmethod=args.interp,
       exprpaths=args.exprpaths, clobber=args.clobber,
       dimkeys=args.dimkeys, format_kw=args.format,
       history=str(args))
