__all__ = ['download_window', 'geoscf', 'cfdriver']
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
    metvars=None, chmvars=None, xgcvars=None, gdpath=None, protocol='opendap'
):
    """
    Arguments
    ---------
    gdnam : str
        Grid name with definition in GRIDDESC at environ['GRIDDESC'],
        ./GRIDDESC or in the GRIDDESC distributed with aqmbc
    dates : list
        Dates to process. Each will be saved separately on disk.
    sleep : int
        GEOS-CF OpenDAP will crash if too many calls are made sequentially.
        Heuristically, a minute between calls prevents crashes.
    metvars : list
        Optional list of metvars to subset. See GEOS-CF fluid documentation.
    chemvars : list
        Optional list of chmvars to subset. See GEOS-CF fluid documentation.
    xgcvars : list
        Optional list of xgcvars to subset. See GEOS-CF fluid documentation.
    gdpath : str
        Path to GRIDDESC for custom location
    protocol : str
        opendap or https

    Returns
    -------
    outpaths : list
        List of paths that were created by download
    """
    protocol = protocol.lower()
    opts = dict(
        gdnam=gdnam, dates=dates, sleep=sleep,
        metvars=metvars, chmvars=chmvars, xgcvars=xgcvars,
        gdpath=gdpath
    )
    if protocol == 'opendap':
        out = download_window_opendap(**opts)
    elif protocol == 'https':
        out = download_window_https(**opts)
    else:
        raise ValueError(f'protocol must be opendap or https; got {protocol}')
    return out


def download_window_https(
    gdnam, dates, sleep=10,
    metvars=None, chmvars=None, xgcvars=None, gdpath=None,
    keepglobal=False
):
    """
    see download_window
    """
    import pandas as pd
    import numpy as np
    import xarray as xr
    import os
    import time
    from urllib.request import urlretrieve
    from ..options import getmetaf

    dates = pd.to_datetime(dates)
    metaf = getmetaf(bctype='bcon', gdnam=gdnam, gdpath=gdpath)
    lonp = metaf.variables['longitude']
    xlim = slice(*np.quantile(lonp, [0, 1]) + np.array([-1, 1]))
    latp = metaf.variables['latitude']
    ylim = slice(*np.quantile(latp, [0, 1]) + np.array([-1, 1]))
    hroot = 'https://portal.nccs.nasa.gov/datashare/gmao/geos-cf/v1/das/'
    outpaths = []
    if metvars is None:
        metvars = ['zl', 'airdens', 'ps', 'delp', 'q', 't']
    else:
        metvars = list(metvars)
    if chmvars is not None:
        chmvars = list(chmvars)
    if xgcvars is not None:
        xgcvars = list(xgcvars)

    for date in dates:
        outdir = f'GEOSCF/{gdnam}/{date:%Y/%m/%d}'
        pathsuf = f'{date:%Y-%m-%dT%H%M}Z.nc'
        outpath = f'{outdir}/geoscf_mcx_tavg_1hr_g1440x721_v36_{pathsuf}'

        if os.path.exists(outpath):
            print(f'Keeping cached: {outpath}')
            outpaths.append(outpath)
            continue

        print(f'Making: {outpath}', flush=True)
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        prefix = f'{hroot}/{date:Y%Y/M%m/D%d}/GEOS-CF.v01.rpl'
        meturl = f'{prefix}.met_tavg_1hr_g1440x721_v36.{date:%Y%m%d_%H%M}z.nc4'
        chmurl = f'{prefix}.chm_tavg_1hr_g1440x721_v36.{date:%Y%m%d_%H%M}z.nc4'
        xgcurl = f'{prefix}.xgc_tavg_1hr_g1440x721_v36.{date:%Y%m%d_%H%M}z.nc4'
        metdest = meturl[8:]
        chmdest = chmurl[8:]
        xgcdest = xgcurl[8:]
        t0 = time.time()
        removes = []
        if not os.path.exists(metdest):
            os.makedirs(os.path.dirname(metdest), exist_ok=True)
            urlretrieve(meturl, metdest)
            removes.append(metdest)
        mf = xr.open_dataset(metdest)
        mf = mf.rename({k: k.lower() for k in mf if k != k.lower()})
        tmpmf = mf[metvars].sel(lat=ylim, lon=xlim).load()
        mergefs = [tmpmf]
        sources = [meturl]
        t1 = time.time()
        print(f' - met: {t1 - t0:.0f}s', flush=True)
        if chmvars is None or len(chmvars) > 0:
            t0 = time.time()
            if not os.path.exists(chmdest):
                urlretrieve(chmurl, chmdest)
                removes.append(chmdest)
            cf = xr.open_dataset(chmdest)
            cf = cf.rename({k: k.lower() for k in cf if k != k.lower()})
            if chmvars is None:
                chmvars = list(cf.data_vars)
            tmpcf = cf[chmvars].sel(lat=ylim, lon=xlim).load()
            mergefs.append(tmpcf)
            sources.append(chmurl)
            t1 = time.time()
            print(f' - chm: {t1 - t0:.0f}s', flush=True)

        if xgcvars is None or len(xgcvars) > 0:
            t0 = time.time()
            if not os.path.exists(xgcdest):
                urlretrieve(xgcurl, xgcdest)
                removes.append(xgcdest)
            xf = xr.open_dataset(xgcdest)
            xf = xf.rename({k: k.lower() for k in xf if k != k.lower()})
            if xgcvars is None:
                xgcvars = list(xf.data_vars)
            if len(xgcvars) > 0:
                tmpxf = xf[xgcvars].sel(lat=ylim, lon=xlim).load()
                mergefs.append(tmpxf)
                sources.append(xgcurl)
            t1 = time.time()
            print(f' - xgc: {t1 - t0:.0f}s', flush=True)

        t0 = time.time()
        outf = xr.merge(mergefs)
        outf.attrs['data_source'] = ', '.join(sources)
        outf.to_netcdf(outpath)
        if len(metvars) > 0:
            mf.close()
        if len(chmvars) > 0:
            cf.close()
        if len(xgcvars) > 0:
            xf.close()
        if not keepglobal:
            for path in removes:
                try:
                    os.remove(path)
                except Exception as e:
                    print(f'WARN:: failed to remove {path} -- {str(e)}')
        t1 = time.time()
        print(f' - merge: {t1 - t0:.0f}s', flush=True)
        outpaths.append(outpath)
        if len(dates) > 1:
            time.sleep(sleep)

    return outpaths


def download_window_opendap(
    gdnam, dates, sleep=60,
    metvars=None, chmvars=None, xgcvars=None, gdpath=None
):
    """
    see download_window
    """
    import pandas as pd
    import numpy as np
    import xarray as xr
    import os
    import time
    from ..options import getmetaf

    sleep = 60
    dates = pd.to_datetime(dates)
    metaf = getmetaf(bctype='bcon', gdnam=gdnam, gdpath=gdpath)
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

    outpaths = []
    for t in dates:
        tv = mf.time.sel(time=t, method='nearest').values
        stime = pd.to_datetime(tv).round('1s').to_pydatetime()
        outdir = f'GEOSCF/{gdnam}/{stime:%Y/%m/%d}'
        pathsuf = f'{stime:%Y-%m-%dT%H%M}Z.nc'
        outpath = f'{outdir}/geoscf_mcx_tavg_1hr_g1440x721_v36_{pathsuf}'
        if os.path.exists(outpath):
            print(f'Keeping cached: {outpath}')
            outpaths.append(outpath)
            continue

        print(f'Making: {outpath}')
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
        # to_netcdf compute=True, so okay to delete
        outf.expand_dims(time=[stime]).to_netcdf(outpath)
        outpaths.append(outpath)
        del outf, mergefs, tmpmf
        if len(chmvars) > 0:
            del tmpcf
        if len(xgcvars) > 0:
            del tmpxf
        if t != dates[-1]:
            time.sleep(sleep)

    return outpaths


class geoscf(pnc.PseudoNetCDFFile):
    def __init__(self, path, *args, **kwds):
        """
        Thin wrapper around raqms files to add ll2ij, getTimes, and
        interpSigma functions. Provide multiple paths to open several
        stacked on the time dimension
        """
        import numpy as np
        from PseudoNetCDF.geoschemfiles import _vertcoord
        from ..options import addhyb

        subkwds = {k: v for k, v in kwds.items()}
        subkwds['format'] = 'netcdf'
        if isinstance(path, str):
            f = pnc.pncopen(path, *args, **subkwds)
        else:
            fs = []
            varlist = None
            paths = path
            for path in paths:
                f = pnc.pncopen(path, *args, **subkwds)
                myvarlist = list(f.variables)
                if varlist is None:
                    varlist = myvarlist
                else:
                    dropped = set(varlist).symmetric_difference(myvarlist)
                    if len(dropped):
                        print('dropped:', dropped)
                    varlist = set(varlist).intersection(myvarlist)
                fs.append(f)
            varlist = sorted(varlist)
            fs = [f_.subset(varlist) for f_ in fs]
            f = fs[0].stack(fs[1:], 'time')
        self.dimensions = f.dimensions
        self.variables = f.variables
        for k in f.ncattrs():
            setattr(self, k, f.getncattr(k))
        nz = len(self.dimensions['lev'])
        # convert from hPa to Pa
        Ap = _vertcoord.geos_hyai['GEOS-5-NATIVE'] * 100
        Bp = np.array(_vertcoord.geos_hybi['GEOS-5-NATIVE'], copy=True)
        hyai = Ap[:nz + 1][::-1]
        hybi = Bp[:nz + 1][::-1]
        hyam = (hyai[1:] + hyai[:-1]) / 2
        hybm = (hybi[1:] + hybi[:-1]) / 2
        hyc = dict(hyai=hyai, hybi=hybi, hyam=hyam, hybm=hybm)
        addhyb(self, hyc=hyc, zdim='lev', zedim='ilev')
        psfc = self.variables['ps'][:][:, None, ...]
        delpv = self.variables['delp']
        delp = delpv[:]
        plow = psfc - np.cumsum(delp[:, ::-1], axis=1)[:, ::-1]
        pmid = plow + delp * 0.5
        pvar = self.createVariable(
            'pmid', delp.dtype.char, delpv.dimensions, units='Pa'
        )
        pvar[:] = pmid
        self.setCoords(
            ['time', 'lat', 'lon', 'lev', 'hyai', 'hybi', 'hyam', 'hybm', 'ps']
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
        from .util import zinterp
        from ..options import sig2hyb
        import numpy as np
        if vgtop < 10:
            import warnings
            r = 0.04  # assuming GFS
            wmsg = 'INFO:: VGTOP less than 10; assuming destination is'
            wmsg += f' constant pressure at r={r:.2f}'
            warnings.warn(wmsg)
        else:
            r = 0.2  # assuming typical WRF r value
        midvglvls = (vglvls[:-1] + vglvls[1:]) / 2
        destAB = sig2hyb(midvglvls, r=r, p0=1e5, pt=vgtop)
        dstA = destAB['hya']
        dstB = destAB['hyb']
        myvars = self.variables
        if 'ps' not in myvars or 'pmid' not in myvars:
            raise KeyError('File is missing ps or pmid')

        ps = self.variables['ps']
        pmid = self.variables['pmid']

        sdi = list(range(1, ps.ndim))
        pdims = list(ps.dimensions)
        pdims.insert(1, 'LAY')
        destpmid = (
            ps[:, None] * np.expand_dims(dstB, sdi) + np.expand_dims(dstA, sdi)
        )
        destpmid = pnc.PseudoNetCDFVariable(
            None, 'pmid', 'f', tuple(pdims), values=destpmid
        )
        outf = zinterp(self, pmid, destpmid)
        outf.setncattr('VGLVLS', vglvls)
        outf.setncattr('VGTOP', vgtop)
        outf.setncattr('VGTYP', -9999)

        return outf


def cfdriver(
    gdnam, date, vgnam='EPA_35L', freq='3h', outdir=None, gdpath=None,
    bctype='bcon', protocol='opendap'
):
    """
    Arguments
    ---------
    gdnam : str
        Name of horizontal grid (must be in gdpath or be known grid)
    date : datetime
        Any datetime interpretable by pd.to_datetime
    vgnam : str
        EPA_35L EPA_44L
    freq : str
        24h must be a multiple of frequency (1h, 3h, 6h, 12h)
    outdir : str
        Path for output files
    gdpath : str
        Path to GRIDDESC that defines gdnam
    bctype : str
        bcon or icon
    protocol : str
        opendap or https

    Returns
    -------
    bcpath : str
        Path to CMAQ-ready file
    """
    import os
    import pandas as pd
    from ..bcon import bc
    from ..options import getmetaf, dims
    from .. import exprlib
    from ..cmaq import cmaqready

    if outdir is None:
        outdir = f'./{date:%Y/%m}'
    # Make sure date is a date
    date = pd.to_datetime(date)
    # Define a time range around date
    sdate = date - pd.to_timedelta(freq) + pd.to_timedelta('0.5h')
    edate = date - pd.to_timedelta('24.5')
    if bctype == 'icon':
        sdate = date
        edate = date
    # Find all CF paths necessary to process bcon
    indates = pd.date_range(sdate, edate, freq=freq)
    cfpaths = download_window(
        gdnam, indates, gdpath=gdpath, protocol=protocol
    )
    metaf = getmetaf(bctype=bctype, gdnam=gdnam, vgnam=vgnam, gdpath=gdpath)
    # Definitions necessary to convert CF species to CMAQ
    exprpaths = ['geoscf_met.expr', 'geoscf_cb6.expr', 'geoscf_ae7.expr']
    exprpaths = exprlib.exprpaths(exprpaths, prefix='cf')
    bcpaths = []
    for indate, cfpath in zip(indates, cfpaths):
        pathsuf = f'{indate:%Y-%m-%dT%H%M}Z_{gdnam}_BCON.nc'
        outpath = f'{outdir}/{indate:%Y/%m}'
        outpath = f'{outpath}/geoscf_mcx_tavg_1hr_g1440x721_v36_{pathsuf}'
        os.makedirs(os.path.dirname(outpath), exist_ok=True)
        if os.path.exists(outpath):
            bcpaths.append(outpath)
            print('WARN:: cached', outpath)
            continue
        bc(
            cfpath, outpath, metaf,
            vmethod='linear', exprpaths=exprpaths, dimkeys=dims['gc'],
            format_kw={'format': 'geoscf'},
            history=f"From {cfpath}", clobber=False, verbose=1
        )
        bcpaths.append(outpath)
    if bctype == 'icon':
        return outpath

    pathsuf = f'{date:%Y-%m-%d}_25h_{gdnam}_BCON.nc'
    outpath = f'{outdir}/geoscf_mcx_tavg_1hr_g1440x721_v36_{pathsuf}'
    os.makedirs(os.path.dirname(outpath), exist_ok=True)
    cmaqready(date, bcpaths, outpath=outpath, minvalue=1e-30)
    return outpath
