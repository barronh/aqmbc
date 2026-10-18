__all__ = ['open_ioapi', 'open_griddesc', 'attrs2proj4', 'timeindependent']

_lcctmpl = (
    '+proj=lcc +lat_1={P_ALP} +lat_2={P_BET} +lat_0={YCENT} +lon_0={P_GAM}'
    + ' +x_0={x_0} +y_0={y_0} +R={earth_radius} +to_meter={XCELL} +no_defs'
)
_poltmpl = (
    '+proj=stere +lat_0={lat_0} +lat_ts={P_BET} +lon_0={P_GAM}'
    + ' +x_0={x_0} +y_0={x_0} +R={earth_radius} +to_meter={XCELL} +no_defs'
)
_mertmpl = (
    '+proj=merc +lat_0={P_ALP} +lon_0={P_GAM}'
    + ' +x_0={x_0} +y_0={y_0} +R={earth_radius} +to_meter={XCELL} +no_defs'
)
_prjp = ('GDTYP', 'P_ALP', 'P_BET', 'P_GAM', 'XCENT', 'YCENT')
_grdp = (
    'PRJNAME', 'XORIG', 'YORIG', 'XCELL', 'YCELL', 'NCOLS', 'NROWS', 'NTHIK'
)


def attrs2proj4(attrs, earth_radius=6370000.0):
    """
    Convert IOAPI attributes to a proj4
    Arguments
    ---------
    attrs : dict
        IOAPI grid and projection attributes
    earth_radius : float
        Spherical earth radius; Defaults to WRF radius.

    Returns
    -------
    projstr : str
        Proj4 formatted projection string.

    Notes
    -----
    For details on attributes, see
    https://www.cmascenter.org/ioapi/documentation/all_versions/html/GRIDS.html

    """
    pattrs = {'earth_radius': earth_radius}
    pattrs.update({
        k: (v.item() if hasattr(v, 'item') else v)
        for k, v in attrs.items() if k != 'VGLVLS'
    })
    pattrs['x_0'] = -pattrs['XORIG']
    pattrs['y_0'] = -pattrs['YORIG']
    if attrs['GDTYP'] == 2:
        tmpl = _lcctmpl
    elif attrs['GDTYP'] == 6:
        tmpl = _poltmpl
        pattrs['lat_0'] = pattrs['P_ALP'] * 90.
    elif attrs['GDTYP'] == 7:
        tmpl = _mertmpl
    else:
        raise KeyError('Unknown grid type')
    projstr = tmpl.format(**pattrs)
    return projstr


def open_ioapi(path):
    """
    Open an IOAPI-meta data file from a netcdf file on disk.

    Arguments
    ---------
    path : str
        Path to IOAPI formatted file.

    Returns
    -------
    qf : xarray.Dataset
        Dataset with coordinates derived from IOAPI metadata
        - TSTEP will be derived from TFLAG or SDATE/STIME/TSTEP
        - LAY will be derived from VGLVLS
        - Spatial coordinates will depend on FTYPE:
          - FTYPE=1: ROW (0.5, NROWS - 0.5) and COL (0.5, NCOLS - 0.5)
          - FTYPE=2: PERIM (0.5, (NROWS + NCOLS + 2) * 2 - 0.5)
        the crs_proj4 attribute will be added for convenience.
    """
    import xarray as xr
    qf = xr.open_dataset(path, decode_cf=False)
    _addcoords(qf)
    return qf


def open_griddesc(grid, gdpath=None, **attrs):
    """
    Open an IOAPI-meta data file from a GRIDDESC file and GDNAM

    Arguments
    ---------
    grid : str or dict
        If str, references a named grid (GDNAM) in gdpath.
        If dict, provides all teh required attributes for a GRID
        - GDTYP, P_ALP, P_BET, P_GAM, XCENT, YCENT
        - PRJNAME, XORIG, YORIG, XCELL, YCELL, NCOLS, NROWS, NTHIK
        - FTYPE (1: GRIDDED; 2: PERIM)

    gdpath : str
        If provided, path to a grid path.
        Otherwise, defaults to environmental variable GRIDDESC, ./GRIDDESC
          or package GRIDDESC

    Returns
    -------
    qf : xarray.Dataset
        Dataset with grid attributes and coordinates. If FTYPE=1 (default),
        this is a gridded file. If FTYPE=2, this is a perimeter file.

    Notes
    -----
    For details on attributes, see
    https://www.cmascenter.org/ioapi/documentation/all_versions/html/GRIDS.html
    """
    import xarray as xr
    qf = xr.Dataset()
    if isinstance(grid, str):
        if gdpath is None:
            import os
            from os.path import join, exists
            from ..data import dataroot
            gdpath1 = os.environ.get('GRIDDESC', 'GRIDDESC')
            gdpath2 = join(dataroot, 'GRIDDESC')
            if exists(gdpath1):
                gdpath = gdpath1
            elif exists(gdpath2):
                gdpath = gdpath2
            else:
                raise IOError(f'{gdpath1} or {gdpath2} must exist.')
        gdattrs = parse_griddesc(gdpath)[grid]
    elif isinstance(grid, dict):
        gdattrs = grid
    else:
        raise TypeError(f'GDNAM must be a str or dict; got {type(grid)}')

    qf.attrs.update(gdattrs)
    attrs.setdefault('FTYPE', 1)
    qf.attrs.update(attrs)
    _addcoords(qf)
    return qf


def _addcoords(qf):
    """
    Add coordinates to an IOAPI formatted file.

    Arguments
    ---------
    qf : xarray.Dataset
        Dataset with IOAPI metadata.

    Returns
    -------
    qf : xarray.Dataset
        Dataset with coordinates derived from IOAPI metadata
        - TSTEP will be derived from TFLAG or SDATE/STIME/TSTEP
        - LAY will be derived from VGLVLS
        - Spatial coordinates will depend on FTYPE:
          - FTYPE=1: ROW (0.5, NROWS - 0.5) and COL (0.5, NCOLS - 0.5)
          - FTYPE=2: PERIM (0.5, (NROWS + NCOLS + 2) * 2 - 0.5)
        the crs_proj4 attribute will be added for convenience.
    """
    import xarray as xr
    import pandas as pd
    import numpy as np
    attrs = qf.attrs
    hastattrs = all([k in attrs for k in 'SDATE STIME TSTEP'.split()])
    if 'TFLAG' in qf.data_vars:
        js = xr.DataArray(np.array([1000000, 1]), dims=('DATE-TIME',))
        jdates = (qf['TFLAG'][:, 0, :] * js).sum('DATE-TIME')
        qf.coords['TSTEP'] = pd.to_datetime(jdates, format='%Y%j%H%M%S')
    elif hastattrs and 'TSTEP' in qf.sizes:
        nt = qf.sizes['TSTEP']
        dhhmmss = attrs['TSTEP']
        hh = dhhmmss // 10000
        mm = (dhhmmss % 10000) // 100
        ss = dhhmmss % 100
        ds = pd.to_timedelta(hh * 3600. + mm * 60. + ss, unit='s')
        t0 = pd.to_datetime(qf.SDATE * 1000000 + qf.STIME, format='%Y%j%H%M%S')
        time = pd.date_range(t0, periods=nt, freq=ds)
        qf.coords['TSTEP'] = time
    if 'VGLVLS' in attrs:
        qf.coords['LAY'] = (qf.VGLVLS[1:] + qf.VGLVLS[:-1]) / 2
    nr = qf.sizes.get('ROW', attrs['NROWS'])
    nc = qf.sizes.get('COL', attrs['NCOLS'])
    if attrs['FTYPE'] == 1:
        qf.coords['ROW'] = np.arange(nr) + 0.5
        qf.coords['COL'] = np.arange(nc) + 0.5
    if attrs['FTYPE'] == 2:
        nperim = qf.sizes.get('PERIM', (nr + 1 + nc + 1) * 2)
        qf.coords['PERIM'] = np.arange(nperim) + 0.5

    qf.attrs['crs_proj4'] = attrs2proj4(attrs)


def parse_griddesc(gdpath):
    """
    IOAPI GRIDDESC files contain projections and grid definitions. This utility
    reads those file formats and returns a dictionary with file attributes for
    each grid by its name.

    Arguments
    ---------
    gdpath : str or file-object
        Typically, a path to a GRIDDESC file, or
        any object that implements the read method (e.g, io.StringIO).

    Returns
    -------
    grids : dict
        Dictionary of IOAPI grid parameters keyed by name.
    """
    import io
    import re
    from os.path import exists
    if hasattr(gdpath, 'read'):
        gdf = gdpath
    elif exists(gdpath):
        gdf = open(gdpath, 'r')
    else:
        wmsg = 'WARN:: gdpath does not have read and does not exists'
        print(wmsg)
        gdf = io.StringIO(gdpath)

    gdtxt = gdf.read().replace(',', ' ').strip()
    # Fortran allows exponential notation to use D or d
    # instead of E or e, while Python does not.
    dble = re.compile(r'([\d.])[Dd]([\d])')
    gdtxt = dble.sub(r'\1e\2', gdtxt)
    gdlines = gdtxt.split('\n')
    gdlines = [line.strip() for line in gdlines]
    # Remove comments that start with !
    gdlines = [line.split('!')[0].strip() for line in gdlines]
    # IOAPI does not verify first line, simply discards.
    # dscgrid.f#L153
    # assert (gdlines[0].replace(' ', '') == "''")
    assert (gdlines[-1].replace(' ', '') == "''")
    i = 0
    blanks = []
    grd = {}
    prj = {}
    while i < len(gdlines):
        line = gdlines[i]
        if line.strip() in ("' '", "''", ""):
            blanks.append(i)
        else:
            i += 1
            parts = [eval(p) for p in gdlines[i].split()]
            key = eval(line)
            if len(blanks) == 1:
                prj[key] = dict(zip(_prjp, parts))
            elif len(blanks) == 2:
                grd[key] = dict(zip(_grdp, parts))
            else:
                pass
        i += 1

    for key in list(grd):
        myprj = prj[grd[key]['PRJNAME']]
        grd[key].update(GDNAM=key, **myprj)

    return grd


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


def cmaqready(
    inpaths, times, verbose=0, minvalue=1e-30
):
    """
    Concatenate inpaths on time and then interpolate to 25h instantaneous
    times for CMAQ. Also trims FILEDESC and HISTORY if they are too long.

    Arguments
    ---------
    inpaths : list or str
        List of paths to use as the source, or
        strftime template to find inputs using times
    times : list-like
        List-like of datetime objects for output. Note that typical CMAQ runs
        for 24h from 00Z to 00Z and expects to find the first 00Z datetime in
        the BCON file.
    verbose : int
        Level of verbosity
    minvalue : scalar
        Minimum value


    Returns
    -------
    outpath : str or dataset
        Output file or path.

    Example
    -------

    import pandas as pd
    from aqmbc.utils import cmaqready

    intmpl = 'outputs/BCON/geoscf_36US3_WRFHYBRID_35L_%Y-%m-%dT%H%M%S.nc'
    outpath = 'outputs/BCON/geoscf_36US3_WRFHYBRID_35L_%Y-%m-%d_00Z.nc'
    indates = pd.date_range('2025-03-31T23:30', '2025-04-02T00:30', freq='3h')
    inpaths = indates.strftime(intmpl)
    times = pd.date_range('2025-04-01', periods=25, freq='1h')
    outf = cmaqready(inpaths, times)
    outf.to_netcdf(outpath)

    """
    import warnings
    import pandas as pd
    import xarray as xr
    import numpy as np
    import os

    clim = 60 * 80
    if isinstance(inpaths, str):
        inpat = inpaths
        testinpaths = sorted(set([d.strftime(inpat) for d in times]))
        inpaths = [p for p in testinpaths if os.path.exists(p)]
        missingpaths = sorted(set(testinpaths).difference(inpaths))
        if len(missingpaths) > 0:
            if verbose > 0:
                print(f'Could not find {missingpaths}')
        if len(inpaths) == 0:
            raise IOError('Found no paths for specified dates')

    infiles = [xr.open_dataset(p, decode_cf=False) for p in inpaths]
    tmpds = xr.concat(infiles, dim='TSTEP')
    yyyyjjj = tmpds['TFLAG'][:, 0, 0].values
    hhmmss = tmpds['TFLAG'][:, 0, 1].values
    intime = pd.to_datetime([
        f'{yj}T{tj:06d}' for yj, tj in zip(yyyyjjj, hhmmss)
    ], format='%Y%jT%H%M%S')
    stime = times.min()
    etime = times.max()
    if intime.min() > stime:
        warnings.warn(
            f'Input files start {intime.min():%Y-%m-%dT%H}Z after target'
            f' start {stime:%Y-%m-%dT%H}; earliest date copied to fill.'
        )
    if intime.max() < etime:
        warnings.warn(
            f'Input files end {intime.max():%Y-%m-%dT%H}Z before target'
            f' end {etime:%Y-%m-%dT%H}; latest date copied to fill.'
        )
    tmpds.coords['TSTEP'] = intime
    nvars = tmpds.attrs['NVARS']
    tflagdata = np.array([
        times.strftime('%Y%j').astype('i'),
        times.strftime('%H%M%S').astype('i')
    ]).T[:, None, :].repeat(nvars, 1)
    tflag = xr.DataArray(
        tflagdata, dims=('TSTEP', 'VAR', 'DATE-TIME'),
        name='TFLAG', attrs=tmpds['TFLAG'].attrs
    )
    tmpds = tmpds.interp(TSTEP=times).reset_index(['TSTEP'], drop=True)
    outds = tmpds[[]]
    outds.attrs.update(tmpds.attrs)
    outds.attrs['SDATE'] = np.int32(stime.strftime('%Y%j'))
    outds.attrs['STIME'] = np.int32(stime.strftime('%H%M%S'))
    outds.attrs['TSTEP'] = np.int32(10000)
    fdesc = outds.attrs['FILEDESC']
    hist = outds.attrs['HISTORY'].strip()
    outds.attrs['FILEDESC'] = fdesc[:clim]
    hist = (
        'CMAQ ready interpolated from:'.ljust(79)
        + ', '.join(inpaths)
    )
    outds.attrs['HISTORY'] = hist[:clim]
    if len(fdesc) > clim:
        outds.attrs['description'] = fdesc
    outds['TFLAG'] = tflag.astype('i')
    titimes = list(enumerate(times))
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
    else:
        return outds
