__all__ = ['cmaqready']


def cmaqready(date, inpaths, outpath=None):
    """
    Concatenate inpaths on time and then interpolate to 25h instantaneous
    times for CMAQ. Also trims FILEDESC and HISTORY if they are too long.

    Arguments
    ---------
    date : date-like or string
        Date for CMAQ-ready file.
    inpaths : list
        List of paths to use as the source.
    outpath : str or None
        If None, return the file.
        Otherwise, write it out and return the path
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
            f' start {date:%Y-%m-%dT%H}'
        )
    if intime.max() < (date + dd):
        warnings.warn(
            f'Input files end {intime.max():%Y-%m-%dT%H}Z before target'
            f' end {date + dd:%Y-%m-%dT%H}'
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
    for key in tmpds.data_vars:
        if key == 'TFLAG':
            continue
        outds[key] = tmpds[key].astype('f')

    if outpath is not None:
        outds.to_netcdf(outpath)
        return outpath
    else:
        return outds
