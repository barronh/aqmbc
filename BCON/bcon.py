import os
import numpy as np
import PseudoNetCDF as pnc
import functools

def wndw(varfile, metaf, dimkeys):
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
    if (
        getattr(infile, 'VGLVLS', []) == metaf.VGLVLS and
        getattr(infile, 'VGTOP', -1) == infile.VGTOP
    ):
        bconvf = infile 
    else:
        print('vint', flush=True)
        bconvf = infile.interpSigma(vglvls=metaf.VGLVLS, vgtop=metaf.VGTOP,
                                    verbose=1, interptype=vmethod)
        if not hasattr(bconvf, 'VGTYP'):
            bconvf.VGTYP = metaf.VGTYP

    return bconvf

def translate(infile, exprpath):
    """
    Arguments
    ---------
    infile : file input
    exprpath : path to expr file

    Returns
    -------
    outf : file output
    """
    # Translate species and/or units
    if exprpath is None:
        outf = infile
    else:
        print('translate', flush=True)
        outf = infile.eval(open(exprpath, 'r').read(), inplace=False)

    return outf

def bc(
    inpath, outpath, metaf,
    tslice=None, vmethod='conserve',
    exprpath=None, clobber=False,
    dimkeys=None, format_kw=None
):
    """
    Arguments
    ---------
    inpath : path to input file
    outpath : path to output file
    metaf : metadata file (CRO for ICON, BDY for BCON)
    tslice : (optional) time slice (e.g., slice(0) for ICON
    vmethod : method to use for vertical interpolation
    exprpath : text file with species translations
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
        format_kw=dict(format='ioapi')
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

    wndwf, i, j = wndw(varfile, metaf, dimkeys)

    try:
        inij = np.prod(wndwf.variables['O3'].shape[2:])
        outij = metaf.variables['latitude'].size
        kfirst = inij < outij
    except Exception as e:
        print(str(e), 'vertical interp first')
        kfirst = True
    
    easyk = functools.partial(kinterp, metaf=metaf, vmethod=vmethod)
    easyij = functools.partial(ijslice, metaf=metaf, i=i, j=j, dimkeys=dimkeys)
    easyx = functools.partial(translate, exprpath=exprpath)

    if kfirst:
        funcs = [easyk, easyij, easyx]
    else:
        funcs = [easyij, easyk, easyx]

    outf = wndwf
    for func in funcs:
        outf = func(outf)

    # Prepare metadata
    props = metaf.getncatts()
    for outdk, indk in dimkeys.items():
        if outdk not in outf.dimensions:
            if indk in outf.dimensions:
                outf.renameDimension(indk, outdk, inplace=True)

    del props['NVARS']
    del props['VAR-LIST']
    if 'PERIM' in metaf.dimensions:
        outdims = ('TSTEP', 'LAY', 'PERIM')
        ndim = 3
    else:
        outdims = ('TSTEP', 'LAY', 'ROW', 'COL')
        ndim = 4

    outkeys = [
        vk
        for vk, vo in outf.variables.items()
        if (
            vo.dimensions == outdims
        )
    ]

    for ok in outkeys:
        outf.variables[ok].long_name = ok.ljust(16)
        outf.variables[ok].var_desc = ok.ljust(80)

    extrakeys = set(list(outf.variables)).difference(outkeys + ['TFLAG'])
    for ek in extrakeys:
        if ek in outf.variables:
            del outf.variables[ek]

    props['NVARS'] = len(outkeys)
    props['VAR-LIST'] = ''.join([k.ljust(16) for k in outkeys])
    outf.setncatts(props)
    if 'VAR' not in outf.dimensions:
        outf.createDimension('VAR', props['NVARS'])

    if 'DATE-TIME' not in outf.dimensions:
        outf.createDimension('DATE-TIME', 2)

    for dk in list(outf.dimensions):
        if dk not in outdims + ('VAR', 'DATE-TIME'):
            del outf.dimensions[dk]

    time = wndwf.getTimes()
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
    if exprpath is None:
        outf.FILEDESC = 'Boundary conditions from {}'.format(inpath)
    else:
        outf.FILEDESC = (
            'Boundary conditions from ' +
            '{} with {}'.format(inpath, exprpath)
        )

    # Save to outpath
    print('save', flush=True)

    gigs = np.prod([len(outf.dimensions[dk]) for dk in outdims]) * outf.NVARS * 4 / 1024**3
    if gigs > 2:
        outformat='NETCDF3_64BIT_OFFSET'
    else:
        outformat='NETCDF3_CLASSIC'

    outf.save(outpath, format=outformat, verbose=0, outmode='w')

    print('done', flush=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-O', '--clobber', default=False, action='store_true')
    parser.add_argument('--grid', default=None, help='Grid name from GRIDDESC')
    parser.add_argument('--icon', default=False, action='store_true')
    parser.add_argument(
        '--expr', dest='exprpath', default=None, help='Expressions for model'
    )
    parser.add_argument('inpath')
    parser.add_argument('outpath')
    args = parser.parse_args()
    # variables for metafile
    _vglvls = [1., 0.9975, 0.995, 0.99, 0.985, 0.98, 0.97, 0.96, 0.95, 0.94,
               0.93, 0.92, 0.91, 0.9, 0.88, 0.86, 0.84, 0.82, 0.8, 0.77,
               0.74, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3,
               0.25, 0.2, 0.15, 0.1, 0.05, 0.]
    _vgtop = 5000.
    dimkeys = {
        'ROW': 'latitude',
        'COL': 'longitude',
        'TSTEP': 'time',
        'LAY': 'layer47'
    }
    metaf = pnc.pncopen(
        '../GRIDDESC', format='griddesc',
        VGLVLS=_vglvls, VGTOP=_vgtop,
        FTYPE=(1 if args.icon else 2),
        GDNAM=args.grid
    )
    if args.icon:
        tslice = metaf.createVariable('time', 'i', ('TSTEP',))
        tslice[0] = 0
    else:
        tslice = None

    bc(args.inpath, args.outpath, metaf,
       tslice=tslice, vmethod='conserve',
       exprpath=args.exprpath, clobber=args.clobber,
       dimkeys=None, format_kw=dict(format='ioapi'))
