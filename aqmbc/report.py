__all__ = ['profile_report', 'range_report']

_deffuncs = ['mean', 'median', 'std', 'min', 'max']


def profile_report(
    paths, varkeys=None, funcs=None, as_dataframe=False,
    outpath=None, verbose=0
):
    """
    Arguments
    ---------
    paths : list or str
        A list of paths
        If str, use glob to create a sorted list of paths.
    varkeys : list
        A subset of keys to process. Defaults to all.
    funcs : list
        List of strings representing functions of the file (defaults to: mean,
        std, min, max, median)
    as_dataframe : bool
        If False, return an xarray.Dataset object.
        If True, return a pandas.DataFrame

    Returns
    -------
    outf : xarray.Dataset or pandas.DataFrame
        Object with statistics applied across parts of domain.
    """
    import glob
    import os
    import pandas as pd
    import xarray as xr
    import numpy as np

    if outpath is not None:
        if os.path.exists(outpath):
            if paths is not None:
                print(f'WARN:: using cached {outpath}; delete to remake')
            if as_dataframe:
                idxcols = ['TSTEP', 'LAY', 'PERIM', 'STAT']
                return pd.read_csv(outpath, index_col=idxcols)
            else:
                return xr.open_dataset(outpath)
    if isinstance(paths, str):
        if verbose > 0:
            print(f'INFO:: Using glob with {paths}')
        paths = sorted(glob.glob(paths))
        if verbose > 0:
            print(f'INFO:: Got {len(paths)}')
            print(f'INFO:: {paths[0]} ... {paths[-1]}')

    exbf = xr.open_dataset(paths[0])
    _defvarkeys = [k for k in exbf.data_vars if k != 'TFLAG']
    if varkeys is None:
        varkeys = _defvarkeys

    if funcs is None:
        funcs = _deffuncs

    slices = [('all', slice(None))]
    nc = exbf.NCOLS
    nr = exbf.NROWS
    bcnames = ['south', 'east', 'north', 'west']
    bclens = [nc + 1, nr + 1, nc + 1, nr + 1]
    ss = 0
    if verbose > 1:
        nperim = exbf.sizes['PERIM']
        print(f'INFO:: PERIM length {nperim}')
    for bck, bcn in zip(bcnames, bclens):
        es = ss + bcn
        bcs = slice(ss, es)
        slices.append((bck, bcs))
        if verbose > 1:
            print(f'INFO:: {bck} {bcs}')
        ss = es

    sfs = []
    dimorder = ('TSTEP', 'LAY', 'PERIM', 'STAT')
    lay = (exbf.VGLVLS[:-1] + exbf.VGLVLS[1:]) / 2
    for path in paths:
        if verbose > 1:
            print(f'INFO:: Working on {path}')

        bf = xr.open_dataset(path, mode='rs')
        jdates = bf['TFLAG'][:, 0, :]
        jdates = (jdates * np.array([1000000, 1])).sum('DATE-TIME')
        if bf.attrs['TSTEP'] == 0:
            # anticipating all zero values for time independent, so try again
            jdates = np.maximum(jdates, 1970001000000)

        tstep = [pd.to_datetime(jdates, format='%Y%j%H%M%S').mean()]
        bf = bf[varkeys]
        efs = []
        for ek, es in slices:
            if verbose > 2:
                print(f'INFO:: Working on {path} {ek}')

            ebf = bf.sel(PERIM=es).load()
            outfs = []
            for fstr in funcs:
                if verbose > 3:
                    print(f'INFO:: Working on {path} {ek} {fstr}')
                outf = xr.concat([
                    getattr(ebf, fstr)(('TSTEP', 'PERIM'), keepdims=True)
                ], dim='PERIM').expand_dims(STAT=[fstr]).transpose(*dimorder)
                outf.coords['TSTEP'] = tstep
                outfs.append(outf)
            efs.append(xr.concat(outfs, dim='STAT'))
        sfs.append(xr.concat(efs, dim='PERIM'))

    outf = xr.concat(sfs, dim='TSTEP')
    for varkey in varkeys:
        outf[varkey].attrs.update(bf[varkey].attrs)
    outf.coords['PERIM'] = [ek for ek, es in slices]
    outf.coords['STAT'] = funcs
    outf.coords['LAY'] = lay
    if as_dataframe:
        outf = outf.isel(**{'VAR': 0, 'DATE-TIME': 0}).to_dataframe()

    if outpath is not None:
        if as_dataframe:
            outf.to_csv(outpath)
        else:
            outf.to_netcdf(outpath)

        return profile_report(None, as_dataframe=as_dataframe, outpath=outpath)

    return outf


def range_report(vprof, PERIM='all', STAT=None):
    import pandas as pd
    if STAT is None:
        STAT = _deffuncs
    statdfs = []
    for stat in STAT:
        subds = vprof.sel(STAT=stat, PERIM=PERIM)
        statds = getattr(subds, stat)(('TSTEP', 'LAY'))
        statds = statds.expand_dims(STAT=[stat])
        statdf = statds.drop_vars(['PERIM']).to_dataframe().T
        statdfs.append(statdf)
    statdf = pd.concat(statdfs, axis=1)
    statdf['units'] = statdf.index.to_series().apply(
        lambda k: vprof[k].units.strip()
    )
    return statdf
