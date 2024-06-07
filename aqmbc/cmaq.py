__all__ = ['cmaqready']


def timeindependent(ncf):
    """
    Edit SDATE, STIME, TSTEP and TFLAG values to 0. IOAPI reads this as time
    independent.

    Arguments
    ---------
    ncf : netcdf file
        Must be editable

    Returns
    -------
    None
    """
    tflag = ncf['TFLAG']
    if tflag.shape[0] > 1:
        raise ValueError('Files with 2+ times cannot be time-independent')
    ncf['TFLAG'][:] = 0
    ncf.SDATE = tflag[0, 0, 0]
    ncf.STIME = tflag[0, 0, 0]
    ncf.TSTEP = tflag[0, 0, 0]


def batch_timeindependent(inpaths, verbose=0):
    """Apply timeindependent to many files on disk"""
    import netCDF4 as nc
    if isinstance(inpaths, str):
        inpaths = [inpaths]
    for inpath in inpaths:
        if verbose:
            print(inpath)
        ncf = nc.Dataset(inpath, mode='r+')
        timeindependent(ncf)


def cmaqready(date, inpaths, outpath=None, verbose=0, minvalue=1e-30):
    """
    Concatenate inpaths on time and then interpolate to 25h instantaneous
    times for CMAQ. Also trims FILEDESC and HISTORY if they are too long.

    Arguments
    ---------
    date : date-like or string
        Date for CMAQ-ready file.
    inpaths : list or str
        List of paths to use as the source or template to find inputs
    outpath : str or None
        If None, return the file.
        Otherwise, write it out and return the path
    verbose : int
        Level of verbosity
    minvalue : scalar
        Minimum value

    Returns
    -------
    outpath : str or dataset
        Output file or path.
    """
    import warnings
    import pandas as pd
    import xarray as xr
    import numpy as np
    import os

    clim = 60 * 80
    if outpath is not None and os.path.exists(outpath):
        print(f'Keeping {outpath}; remove to remake')
        return

    date = pd.to_datetime(date)
    dd = pd.to_timedelta('1d')
    outtimes = pd.date_range(date, date + dd, freq='1h')
    if isinstance(inpaths, str):
        inpat = inpaths
        indates = [date - dd, date, date + dd]
        testinpaths = [d.strftime(inpat) for d in indates]
        inpaths = [p for p in testinpaths if os.path.exists(p)]
        missingpaths = sorted(set(testinpaths).difference(inpaths))
        if len(missingpaths) > 0:
            if verbose > 0:
                print(f'Could not find {missingpaths}')

    infiles = [xr.open_dataset(p, decode_cf=False) for p in inpaths]
    tmpds = xr.concat(infiles, dim='TSTEP')
    yyyyjjj = tmpds['TFLAG'][:, 0, 0].values
    hhmmss = tmpds['TFLAG'][:, 0, 1].values
    intime = pd.to_datetime([
        f'{yj}T{tj:06d}' for yj, tj in zip(yyyyjjj, hhmmss)
    ], format='%Y%jT%H%M%S')
    if intime.min() > date:
        warnings.warn(
            f'Input files start {intime.min():%Y-%m-%dT%H}Z after target'
            f' start {date:%Y-%m-%dT%H}; earliest date copied to fill.'
        )
    if intime.max() < (date + dd):
        warnings.warn(
            f'Input files end {intime.max():%Y-%m-%dT%H}Z before target'
            f' end {date + dd:%Y-%m-%dT%H}; latest date copied to fill.'
        )
    tmpds.coords['TSTEP'] = intime
    nvars = tmpds.attrs['NVARS']
    tflagdata = np.array([
        outtimes.strftime('%Y%j').astype('i'),
        outtimes.strftime('%H%M%S').astype('i')
    ]).T[:, None, :].repeat(nvars, 1)
    tflag = xr.DataArray(
        tflagdata, dims=('TSTEP', 'VAR', 'DATE-TIME'),
        name='TFLAG', attrs=tmpds['TFLAG'].attrs
    )
    tmpds = tmpds.interp(TSTEP=outtimes).reset_index(['TSTEP'], drop=True)
    outds = tmpds[[]]
    outds.attrs.update(tmpds.attrs)
    outds.attrs['SDATE'] = np.int32(date.strftime('%Y%j'))
    outds.attrs['STIME'] = np.int32(date.strftime('%H%M%S'))
    outds.attrs['TSTEP'] = np.int32(10000)
    fdesc = outds.attrs['FILEDESC']
    hist = outds.attrs['HISTORY']
    outds.attrs['FILEDESC'] = fdesc[:clim]
    outds.attrs['HISTORY'] = hist[:clim]
    if len(fdesc) > clim:
        outds.attrs['description'] = fdesc
    outds['TFLAG'] = tflag.astype('i')
    titimes = list(enumerate(outtimes))
    for key in tmpds.data_vars:
        if key == 'TFLAG':
            continue
        # outds[key] = tmpds[key].astype('f')
        tmpv = np.maximum(tmpds[key].astype('f'), minvalue)
        for ti, t in titimes[::-1]:
            if t < intime.min():
                tmpv[ti] = tmpv[ti + 1]
                warnings.warn(f'{t} back filled')
        for ti, t in titimes:
            if t > intime.max():
                tmpv[ti] = tmpv[ti - 1]
                warnings.warn(f'{t} forward filled')
        outds[key] = tmpv
    if outpath is not None:
        outds.to_netcdf(outpath)
        return outpath
    else:
        return outds
