import os
from glob import glob

import PseudoNetCDF as pnc

def bc(
    inpath, outpath, metaf,
    tslice=None, vmethod='conserve',
    exprpath=None, clobber=False
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
    if not clobber and os.path.exists(outpath):
        print('Using cached', outpath, '...')
        return
    print('Converting', inpath, 'to', outpath)
    print('open', flush=True)
    infile = pnc.pncopen(inpath, format='ioapi')

    lon = metaf.variables['longitude']
    lat = metaf.variables['latitude']

    i, j = infile.ll2ij(lon, lat)

    # Create indices for windowed file
    # purely for speed
    imin, imax = i.min(), i.max()
    jmin, jmax = j.min(), j.max()

    # For debug speed, subset variables
    varfile = infile #.subsetVariables(['O3']) # for testing

    if max(imin, jmin) > 10:
        # purely for speed, window the file
        print('window', flush=True)
        cslice = slice(imin, imax + 1)
        rslice = slice(jmin, jmax + 1)
        slices = dict(COL=cslice, ROW=rslice)
        if tslice is not  None:
            slices['TSTEP'] = tslice
        wndwf = varfile.sliceDimensions(verbose=1, **slices)
        iwndw = i - imin
        jwndw = j - jmin
    else:
        if tslice is not  None:
            wndwf = varfile.sliceDimensions(TSTEP=tslice)
        else:
            wndwf = varfile
        iwndw = i
        jwndw = j
    
    # Extract output horizontal -- assuming required...
    # if not, done do this
    print('slice', flush=True)
    if 'ROW' in metaf.dimensions:
        dims = ('ROW', 'COL')
    else:
        dims = ('PERIM',)
    bconf = wndwf.sliceDimensions(COL=iwndw, ROW=jwndw,
                                  newdims = dims, verbose=1)

    # Extract output vertical if not already the same
    if (
        getattr(bconf, 'VGLVLS', []) == metaf.VGLVLS and
        getattr(bconf, 'VGTOP', -1) == bconf.VGTOP
    ):
        bconvf = bconf
    else:
        print('vint', flush=True)
        bconvf = bconf.interpSigma(vglvls=metaf.VGLVLS, vgtop=metaf.VGTOP,
                                   verbose=1, interptype=vmethod)

    # Translate species and/or units
    if exprpath is None:
        outf = bconvf
    else:
        outf = bconvf.eval(exprpath, inplace=False)

    # Prepare metadata
    props = metaf.getncatts()
    del props['NVARS']
    del props['VAR-LIST']
    outf.setncatts(props)

    outf.FILEDESC = 'Boundary conditions from {}'.format(inpath)

    # Save to outpath
    print('save', flush=True)
    outf.save(outpath, format='NETCDF3_CLASSIC', verbose=0)

    print('done', flush=True)


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-O', '--clobber', default=False, action='store_true')
    parser.add_argument('--icon', default=False, action='store_true')
    parser.add_argument('inpath')
    parser.add_argument('outpath')
    args = parser.parse_args()
    # variables for metafile
    _vglvls= [1., 0.9975, 0.995, 0.99, 0.985, 0.98, 0.97, 0.96, 0.95, 0.94,
              0.93, 0.92, 0.91, 0.9, 0.88, 0.86, 0.84, 0.82, 0.8, 0.77,
              0.74, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3,
              0.25, 0.2, 0.15, 0.1, 0.05, 0.]
    _vgtop = 5000.

    metaf = pnc.pncopen(
        '../GRIDDESC', format='griddesc',
        VGLVLS=_vglvls, VGTOP=_vgtop,
        GDNAM='36US3', FTYPE=(1 if args.icon else 2)
    )
    if args.icon:
        tslice=slice(0, 1)
    else:
        tslice=None


    bc(args.inpath, args.outpath, metaf,
       tslice=tslice, vmethod='conserve', exprpath=None, clobber=args.clobber)

