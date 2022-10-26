import os
import numpy as np
import PseudoNetCDF as pnc
import functools


def wndw(varfile, metaf, dimkeys, tslice):
    """
    Arguments
    ---------
    varfile : input file
    metafile : file with longitude and latitude

    Returns
    -------
    wndwf : file windows in lon/lat space
    i: indices for wndwf at metaf
    j: indices for wndwf at metaf
    """
    lon = metaf.variables['longitude']
    lat = metaf.variables['latitude']

    i, j = varfile.ll2ij(lon.ravel(), lat.ravel())
    i = i.reshape(lon.shape)
    j = j.reshape(lat.shape)

    # Create indices for windowed file
    # purely for speed
    imin, imax = i.min(), i.max()
    jmin, jmax = j.min(), j.max()
    if max(imin, jmin) > 10:
        # purely for speed, window the file
        print('window', flush=True)
        cslice = slice(imin, imax + 1)
        rslice = slice(jmin, jmax + 1)
        slices = {dimkeys['COL']: cslice, dimkeys['ROW']: rslice}
        if tslice is not None:
            slices[dimkeys['TSTEP']] = tslice
        wndwf = varfile.sliceDimensions(verbose=1, **slices)
        iwndw = i - imin
        jwndw = j - jmin
    else:
        if tslice is not None:
            print('window', flush=True)
            wndwf = varfile.sliceDimensions(**{dimkeys['TSTEP']: tslice})
        else:
            wndwf = varfile
        iwndw = i
        jwndw = j

    return wndwf, iwndw, jwndw


def ijslice(infile, metaf, i, j, dimkeys):
    """
    Arguments
    ---------
    infile : input file
    metafile : file with longitude and latitude

    Returns
    -------
    bconf : file at metaf
    """
    print('slice', flush=True)
    if 'ROW' in metaf.dimensions:
        dims = ('ROW', 'COL')
    else:
        dims = ('PERIM',)

    wslice = {dimkeys['COL']: i, dimkeys['ROW']: j}
    bconf = infile.sliceDimensions(**wslice,
                                   newdims=dims, verbose=1)
    return bconf


def kinterp(infile, metaf, vmethod):
    """
    Arguments
    ---------
    infile : input file
    metaf : file with longitude and latitude
    vmethod : method for vertical inteprolation

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
        print('vint', flush=True)
        bconvf = infile.interpSigma(vglvls=metaf.VGLVLS, vgtop=metaf.VGTOP,
                                    verbose=1, interptype=vmethod)
        if not hasattr(bconvf, 'VGTYP'):
            bconvf.VGTYP = metaf.VGTYP

    return bconvf


def translate(infile, exprpaths):
    """
    Arguments
    ---------
    infile : file input
    exprpaths : paths to expr file

    Returns
    -------
    outf : file output
    """
    # Translate species and/or units
    if len(exprpaths) == 0:
        outf = infile
    else:
        print('translate', flush=True)
        exprstr = ''.join([
            open(exprpath, 'r').read() for exprpath in exprpaths
        ])
        outf = infile.eval(exprstr, inplace=False)

    return outf


def bc(
    inpath, outpath, metaf,
    tslice=None, vmethod='conserve', exprpaths=None, clobber=False,
    dimkeys=None, format_kw=None, history=''
):
    """
    Arguments
    ---------
    inpath : path to input file
    outpath : path to output file
    metaf : metadata file (CRO for ICON, BDY for BCON)
    tslice : (optional) time slice (e.g., slice(0) for ICON
    vmethod : method to use for vertical interpolation
    exprpaths : text files with species translations
    clobber : overwrite existing files

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
    print('Converting', inpath, 'to', outpath)
    print('open', flush=True)
    infile = pnc.pncopen(inpath, **format_kw)

    # For debug speed, subset variables
    varfile = infile  # .subsetVariables(['O3']) # for testing

    wndwf, i, j = wndw(varfile, metaf, dimkeys, tslice)

    try:
        inij = np.prod(wndwf.variables['O3'].shape[2:])
        outij = metaf.variables['latitude'].size
        kfirst = inij < outij
    except Exception as e:
        print(str(e), 'vertical interp first')
        kfirst = True

    easyk = functools.partial(kinterp, metaf=metaf, vmethod=vmethod)
    easyij = functools.partial(ijslice, metaf=metaf, i=i, j=j, dimkeys=dimkeys)
    easyx = functools.partial(translate, exprpaths=exprpaths)

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
            'Boundary conditions from ' +
            '{}\nwith definitions {}:'.format(inpath, exprpaths) +
            '\n{}'.format(exprstr)
        )

    fhistory = getattr(outf, 'HISTORY', '')
    history = fhistory + history
    setattr(outf, 'HISTORY', history)
    return saveioapi(wndwf, outf, outpath, metaf, dimkeys)


def saveioapi(inf, outf, outpath, metaf, dimkeys):
    """
    Parameters
    ----------
    outf : netcdf-like file
        file for output
    metaf : netcdf-like file
        metadata file
    dimkeys : dict
        translation dictionary for dimensions

    Results
    -------
    out : netcdf-like file
        file that was output
    """
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
    props['HISTORY'] = outf.HISTORY
    props['FILEDESC'] = outf.FILEDESC
    outf.setncatts(props)
    if 'VAR' not in outf.dimensions:
        outf.createDimension('VAR', props['NVARS'])

    if 'DATE-TIME' not in outf.dimensions:
        outf.createDimension('DATE-TIME', 2)

    for dk in list(outf.dimensions):
        if dk not in outdims + ('VAR', 'DATE-TIME'):
            del outf.dimensions[dk]

    time = inf.getTimes()
    if 'TFLAG' not in outf.variables:
        tflag = outf.createVariable(
            'TFLAG', 'i', ('TSTEP', 'VAR', 'DATE-TIME')
        )
        tflag.units = '<YYYYJJJ,HHMMSS>'
        tflag.long_name = 'TFLAG'
        tflag.var_desc = 'TFLAG'
        YYYYJJJ = np.array([t.strftime('%Y%j') for t in time], dtype='i')
        HHMMSS = np.array([t.strftime('%H%M%S') for t in time], dtype='i')
        tflag[:, :, 0] = YYYYJJJ[:, None]
        tflag[:, :, 1] = HHMMSS[:, None]

    if len(time) > 1:
        outf.TSTEP = int(np.diff(time)[0].total_seconds() / 3600) * 10000
    else:
        outf.TSTEP = 10000

    outf.SDATE = int(time[0].strftime('%Y%j'))
    outf.STIME = int(time[0].strftime('%H%M%S'))
    # Save to outpath
    print('save', flush=True)

    gigs = (
        np.prod([len(outf.dimensions[dk]) for dk in outdims]) *
        outf.NVARS * 4 / 1024**3
    )
    if gigs > 2:
        outformat = 'NETCDF3_64BIT_OFFSET'
    else:
        outformat = 'NETCDF3_CLASSIC'

    out = outf.save(outpath, format=outformat, verbose=0, outmode='w')

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
