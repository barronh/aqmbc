__all__ = ['download_window']
import PseudoNetCDF as pnc


def tryandtime(tmpf, label, verbose=1):
    """
    This function tries to download data in tmpf via OpenDAP. If it fails,
    then it tries again up to maxtries. The entire process is timed.

    Arguments
    ---------
    tmpf : xarray.Dataset
        File from GEOS-CF
    verbose : int
        Level of verbosity

    Returns
    -------
    dt : float
        Time elapsed.
    """
    import time

    maxtries = 10
    t0 = time.time()
    ntries = 0
    success = False
    while not success and ntries < maxtries:
        ntries += 1
        try:
            # Might fail
            tmpf.load()
            success = True
        except Exception as e:
            if verbose > 0:
                print(str(e), end='.retry.')

    t1 = time.time()
    dt = t1 - t0
    if verbose > 0:
        msg = f'{label} {dt:.0f}s'
        if ntries > 1:
            msg = f'{msg} ({ntries} tries)'
        print(msg)

    return dt


def download_window(
    gdnam, dates, sleep=60,
    metvars=None, chmvars=None, xgcvars=None
):
    """
    gdnam : str
        Grid name with definition in GRIDDESC at environ['GRIDDESC'],
        ./GRIDDESC or in the GRIDDESC distributed with aqmbc
    dates : list
        Dates to process. Each will be saved separately on disk.
    sleep : int
        GEOS-CF OpenDAP will crash if too many calls are made sequentially.
        Heuristically, a minute between calls prevents crashes.
    """
    import pandas as pd
    import aqmbc
    import numpy as np
    import xarray as xr
    import os
    import time

    sleep = 60
    dates = pd.to_datetime(dates)
    metaf = aqmbc.options.getmetaf(bctype='bcon', gdnam=gdnam)
    lonp = metaf.variables['longitude']
    xlim = slice(*np.quantile(lonp, [0, 1]) + np.array([-1, 1]))
    latp = metaf.variables['latitude']
    ylim = slice(*np.quantile(latp, [0, 1]) + np.array([-1, 1]))

    rooturl = 'https://opendap.nccs.nasa.gov/dods/gmao/geos-cf/assim'
    meturl = f'{rooturl}/met_tavg_1hr_g1440x721_v36'
    chmurl = f'{rooturl}/chm_tavg_1hr_g1440x721_v36'
    xgcurl = f'{rooturl}/xgc_tavg_1hr_g1440x721_v36'

    mf = xr.open_dataset(meturl)
    cf = xr.open_dataset(chmurl)
    xf = xr.open_dataset(xgcurl)

    if metvars is None:
        metvars = ['zl', 'airdens', 'ps', 'delp', 'q', 't']
    else:
        metvars = list(metvars)
    if chmvars is None:
        chmvars = list(cf.data_vars)
    else:
        chmvars = list(chmvars)
    if xgcvars is None:
        xgcvars = list(xf.data_vars)
    else:
        xgcvars = list(xgcvars)
    for t in dates:
        tv = mf.time.sel(time=t, method='nearest').values
        stime = pd.to_datetime(tv).to_pydatetime()
        outdir = f'{gdnam}/{stime:%Y/%m/%d}'
        pathsuf = f'{stime:%Y-%m-%dT%H%M}Z.nc'
        outpath = f'{outdir}/geoscf_mcx_tavg_1hr_g1440x721_v36_{pathsuf}'
        if os.path.exists(outpath):
            print(f'Keeping cached: {outpath}')
            continue

        tmpmf = mf[metvars].sel(time=tv, lat=ylim, lon=xlim)
        tryandtime(tmpmf, 'met')
        mergefs = [tmpmf]
        if len(chmvars) > 0:
            tmpcf = cf[chmvars].sel(time=tv, lat=ylim, lon=xlim)
            tryandtime(tmpcf, 'chm')
            mergefs.append(tmpcf)
        if len(xgcvars) > 0:
            tmpxf = xf[xgcvars].sel(time=tv, lat=ylim, lon=xlim)
            tryandtime(tmpxf, 'xgc')
            mergefs.append(tmpxf)
        outf = xr.merge(mergefs)
        outf.attrs['data_source'] = f'{meturl}, {chmurl}, {xgcurl}'
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        outf.expand_dims(time=[stime]).to_netcdf(outpath)
        if len(dates) > 1:
            time.sleep(sleep)


class geoscf(pnc.PseudoNetCDFFile):
    def __init__(self, *args, **kwds):
        """
        Thin wrapper around raqms files to add ll2ij, getTimes, and
        interpSigma functions.
        """
        f = pnc.pncopen(*args, **kwds)
        self.dimensions = f.dimensions
        self.variables = f.variables
        for k in f.ncattrs():
            setattr(self, k, f.getncattr(k))
        self.setCoords(
            ['time', 'lat', 'lon', 'lev']
        )

    def ll2ij(self, lon, lat, bounds='warn', clean='clip'):
        import numpy as np
        lon = np.asarray(lon)
        lat = np.asarray(lat)
        i = self.val2idx('lon', lon)
        j = self.val2idx('lat', lat)
        ni = self.variables['lon'].size
        nj = self.variables['lat'].size
        ic = np.minimum(np.maximum(i, 0), ni - 1)
        jc = np.minimum(np.maximum(j, 0), nj - 1)
        if ((ic != i).any() | (ic != i).any()):
            import warnings
            warnings.warn('Some cells are outside the source domain')

        return ic, jc

    def getTimes(self, datetype='datetime', bounds=False):
        import cftime
        import numpy as np
        time = self.variables['time']
        out = np.asarray(cftime.num2pydate(time[:], units=time.units))
        return out

    def interpSigma(
        self, vglvls, vgtop=None, interptype='linear', extrapolate=False,
        fill_value='extrapolate', verbose=0
    ):
        """
        Parameters
        ----------
        vglvls : iterable
            the new vglvls (edges)
        vgtop : scalar
            Converting to new vgtop
        interptype : string
             'linear' uses a linear interpolation
             'conserve' uses a mass conserving interpolation
        extrapolate : boolean
            allow extrapolation beyond bounds with linear, default False
        fill_value : boolean
            set fill value (e.g, nan) to prevent extrapolation or edge
            continuation

        Returns
        -------
        outf : ioapi_base
            PseudoNetCDFFile with all variables interpolated

        Notes
        -----
        When extrapolate is false, the edge values are used for points beyond
        the inputs.
        """
        from PseudoNetCDF.coordutil import sigma2coeff
        import numpy as np

        psfc = self.variables['ps'][:][:, None, ...]
        delp = self.variables['delp'][:]
        plow = psfc - np.cumsum(delp[:, ::-1], axis=1)[:, ::-1]
        pedges = np.concatenate([plow, psfc], axis=1)
        pmid = plow + delp * 0.5
        ptop = psfc - delp.sum(1)
        pedges = np.concatenate([ptop, ptop + np.cumsum(delp, axis=1)], axis=1)
        newshape = list(delp.shape)
        nzout = len(vglvls) - 1
        newshape.insert(2, nzout)
        itershape = [newshape[0]] + newshape[3:]
        sigma = (pedges - vgtop) / (psfc - vgtop)
        tmpv = np.zeros(newshape, dtype='f')
        for idx in np.ndindex(*itershape):
            srcidx = (idx[0], slice(None)) + tuple(idx[1:])
            destidx = (idx[0], slice(None), slice(None)) + tuple(idx[1:])
            fromvglvls = sigma[srcidx]
            # sigma2coeff expects vglvls to decrease (i.e., surface to top),
            # but RAQMS is ordered top-to-surface. So, the vglvls are reversed
            # and the results are reversed as well.
            tmpv[destidx] = sigma2coeff(
                fromvglvls[::-1], vglvls
            )[::-1]

        pweight = tmpv[:] * pmid[:, :, None, ...]
        pnorm = pweight.sum(1)
        exprkeys = [
            key
            for key, var in self.variables.items()
            if var.dimensions[:2] == ('time', 'lev')
        ]
        outdims = self.variables[exprkeys[0]].dimensions

        outf = pnc.PseudoNetCDFFile()
        for k, d in self.dimensions.items():
            if k == 'lev':
                outf.createDimension(k, nzout)
            else:
                outf.createDimension(k, len(d))
        for k in self.ncattrs():
            outf.setncattr(k, self.getncattr(k))
        outf.setncattr('VGLVLS', vglvls)
        outf.setncattr('VGTOP', vgtop)
        outf.setncattr('VGTYP', 7)
        for key in exprkeys:
            invar = self.variables[key]
            props = {k: invar.getncattr(k)
                     for k in self.variables['delp'].ncattrs()}
            outvar = outf.createVariable(
                key, invar.dtype.char, outdims, **props
            )
            outvar[:] = (
                invar[:][:, :, None, ...] * pweight
            ).sum(1) / pnorm
        for key, var in self.variables.items():
            if key not in exprkeys and key not in self.dimensions:
                outf.copyVariable(var, key=key)

        return outf
