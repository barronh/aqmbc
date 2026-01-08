import xarray as xr


class icbc:
    def __init__(
        self, metaf, intmpl, exprs=None, outtmpl=None, verbose=99
    ):
        """
        Arguments
        ---------
        metaf : xarray.Dataset
        intmpl : str
            Input file template using strftime format
        exprs : list
            List of dictionaries
        outtmpl : str
            Output file template using strftime format
        verbose : int
            Verbosity level

        Returns
        -------
        None
        """
        self.intmpl = intmpl
        self._rawf = None
        self.verbose = verbose
        self._metaf = metaf
        self._exprs = exprs
        self._timekey = 'time'
        self._pmidkey = 'pmid'
        self._psfckey = 'ps'
        if outtmpl is None:
            ctxt = self.__class__.__name__
            gtxt = metaf.attrs.get('GDNAM', 'CMAQ').strip()
            vtxt = metaf.attrs.get('VGNAM', 'WRF').strip()
            if self._metaf.FTYPE == 1:
                bctxt = 'ICON'
            else:
                bctxt = 'BCON'
            outtmpl = (
                'outputs/'
                + f'{bctxt}/{ctxt}_{gtxt}_{vtxt}_{bctxt}_%Y-%m-%d'
                + ('' if bctxt == 'BCON' else 'T%H%M%S')
                + '.nc'
            )
        self.outtmpl = outtmpl
        self._log = []

    def log(self, msg, level='INFO', source='', clear=False):
        vb = self.verbose
        if clear:
            self._log = []
        ilevel = {'INFO': 1, 'DEBUG': 2}.get(level, 0)
        keep = {'STATUS': False, 'DEBUG': False}.get(level, True)
        lmsg = f'{level}:{source}: {msg}'
        if vb > ilevel:
            print(lmsg)
        if keep:
            self._log.append(lmsg)

    def _opener(self, path):
        """
        Arguments
        ---------
        intmpl : str
            Input file template using strftime format

        Returns
        -------
        outf : xarray.Dataset
            Output files
        """
        import xarray as xr
        tmpf = xr.open_dataset(path)
        # overwrite to add derived variables if necessary
        return tmpf

    def load_date(self, date):
        """
        Load a date to process

        Arguments
        ---------
        date : datetime-like
            Date to load using intmpl

        Returns
        -------
        None
        """
        import numpy as np
        import pandas as pd
        reload = True
        if self._rawf is not None:
            t = pd.to_datetime(self._rawf[self._timekey])
            # allowing some numerical noise
            dt = pd.to_timedelta(date - t)
            reload = np.abs(dt.total_seconds()).min() > 10
        if reload:
            path = self._activepath = date.strftime(self.intmpl)
            self.log(f'Opening {path}', level='STATUS', source='load_date')
            self._rawf = self._opener(self._activepath)
        self._f = self._rawf.sel(**{self._timekey: [date]}, method='nearest')

    def to_lonlat(self, lon, lat, method='nearest', extrapolate='warn'):
        """
        Extract locations from loaded input file.

        Arguments
        ---------
        lon, lat : xarray.DataArrays
            Longitude [-180, 180] and latitude [-90, 90] with dimensions
            ROW, COL or PERIM

        Returns
        -------
        None
        """
        # overwrite to support projections
        imsg = f'Extracting n={lon.size} lon/lat pairs'
        self.log(imsg, level='INFO', source='to_lonlat')
        if extrapolate in ('warn', 'error'):
            west = float(self._f.lon.min())
            east = float(self._f.lon.max())
            south = float(self._f.lat.min())
            north = float(self._f.lat.max())
            outside = dict(
                west=int(((lon - west) < 0).sum()),
                east=int(((lon - east) > 0).sum()),
                south=int(((lat - south) < 0).sum()),
                north=int(((lat - north) > 0).sum()),
            )
            outside = {k: v for k, v in outside.items() if v > 0}
            if len(outside) > 0:
                latmin = float(lat.min())
                latmax = float(lat.max())
                lonmin = float(lon.min())
                lonmax = float(lon.max())
                wmsg = 'Some points out of bbox'
                wmsg += f' ({west}, {south}, {east}, {north}); {outside};'
                wmsg += ' Requested ranges'
                wmsg += f'lat=({latmin}, {latmax}); lon=({lonmin}, {lonmax})'
                if extrapolate == 'warn':
                    self.log(wmsg, level='WARN', source='to_lonlat')
                else:
                    raise ValueError(wmsg)

        self._f = self._f.sel(lon=lon, lat=lat, method=method)

    def to_pres(self, pres, pmidkey=None, **kwds):
        """
        Interpolate working file to pressure coordinate uzing zinterp
        from utils.

        Arguments
        ---------
        pres : xarray.DataArray
            Pressure variable that must have the same units as the pmidkey
        pmidkey : str
            Pressure layer-mid variable name.
        kwds : dict
            Keywords to pass to zinterp

        Returns
        -------
        None
        """
        from .utils import zinterp
        if pmidkey is None:
            pmidkey = self._pmidkey
        srcz = self._f[pmidkey]
        nzin = srcz.shape[1]
        nzout = pres.shape[1]
        imsg = f'Interp pres from nzin={nzin} to nzout={nzout}'
        self.log(imsg, level='INFO', source='to_pres')
        self._f = zinterp(self._f, srcz, pres, **kwds)

    def to_hyb(self, hyam, hybm, pmidkey=None, psfckey=None, **kwds):
        """
        Interpolate working file to pressure coordinate uzing zinterp
        from utils. First construct pressure coordinate from hyam, hybm, and
        the working file surface pressure.

        Arguments
        ---------
        hyam : xarray.DataArrays
            Hybrid coordinate constant pressure [Pa] component
        hybm : xarray.DataArrays
            Hybrid terrain following [1] component
        pmidkey : str
            Pressure layer-mid variable name.
        psfckey : str
            Surface pressure used with hyam and hybm to calculate destination
            pressure.
        kwds : dict
            Keywords to pass to zinterp

        Returns
        -------
        None
        """
        if psfckey is None:
            psfckey = self._psfckey
        ps = self._f[psfckey]
        dims = list(ps.dims)
        dims.insert(1, hybm.dims[0])
        pres = (hybm * ps + hyam).transpose(*dims)
        imsg = 'Calculated pres from HYBRID hyam and hybm.'
        self.log(imsg, level='INFO', source='to_hyb')
        self.to_pres(pres, pmidkey=pmidkey, **kwds)

    def translate(self, exprs=None):
        """
        Arguments
        ---------
        exprs : list
            List of expression dictionaries. Each item must have keys name,
            expression, and units. Defaults to exprs provided to __init__
            or no translation.

        Returns
        -------
        outf : xarray.Dataset
            Output file with the same structure as the working file, but
            with variables according to exprs.
        """
        import numpy as np
        outf = self._f[list(self._f.coords)]
        if exprs is not None:
            pass
        if self._exprs is None:
            exprs = []
            for k, v in self._f.data_vars.items():
                if 'LAY' in v.dims:
                    attrs = {pk: pv for pk, pv in v.attrs.items()}
                    attrs['name'] = k
                    attrs['expression'] = k
                    exprs.append(attrs)
        else:
            exprs = self._exprs
        glbs = dict(np=np)
        glbs.update({k: v for k, v in self._f.data_vars.items()})
        lcls = {}
        imsg = f'Evaluating n={len(exprs)} expressions'
        self.log(imsg, level='INFO', source='translate')
        for expropt in exprs:
            key = expropt['name'].strip()
            estr = expropt['expression']
            dmsg = f'Evaluating {key}={estr}'
            self.log(dmsg, level='STATUS', source='translate')
            attrs = {k: v for k, v in expropt.items()}
            attrs.setdefault('long_name', key)
            attrs.setdefault('var_desc', estr)
            attrs.setdefault('units', 'unknown')
            lcls[key] = eval(estr, glbs, lcls).astype('f')
            lcls[key].attrs.update(attrs)
            outf[key] = lcls[key]

        return outf

    def process(
        self, dates, fdate=None, pres=None, zkwds=None, overwrite=False
    ):
        """
        Process all dates to create a single boundary condition file.

        Arguments
        ---------
        dates : iterable
            Iterable of date-like objects to create an icbc file.
        fdate : datetime-like
            Used as the date for the file name. Defaults to the first element
            of dates.
        pres : xarray.DataArray
            Pressure used as the target for vertical interpolation.
        zkwds : dict
            Dictionary of vertical interpolation kwds.
        overwrite : bool
            If True, overwrite existing files.

        Returns
        -------
        outpath : str
            Output file path
        """
        from os.path import exists, dirname, realpath
        from os import makedirs
        import pandas as pd
        from . import __version__ as version
        cname = self.__class__.__name__
        dates = pd.to_datetime(dates)
        if fdate is None:
            fdate = dates[0]
        fdate = pd.to_datetime(fdate)
        if self.outtmpl is not False:
            outpath = fdate.strftime(self.outtmpl)
            if exists(outpath) and not overwrite:
                return outpath
        fs = []
        qf = self._metaf
        if zkwds is None:
            zkwds = {}
        datestr = ', '.join([d.strftime('%Y-%m-%dT%H%M%S') for d in dates])
        fdatestr = fdate.strftime('%Y-%m-%dT%H%M%S')
        imsg = f'aqmbc (v{version}) {cname} processing {fdatestr}'
        filedesc = [imsg]
        self.log(imsg, level='INFO', clear=True)
        for date in dates:
            imsg = f'{cname} processing {date}'
            self.log(imsg, level='INFO')
            self.load_date(date)
            self.to_lonlat(qf.lon, qf.lat)
            if pres is None:
                self.to_hyb(qf.hyam, qf.hybm, **zkwds)
            else:
                self.to_pres(pres, pmidkey=self._pmidkey, **zkwds)
            outf = self.translate()
            fs.append(outf)
        tmpf = xr.concat(fs, dim=self._timekey)
        if self._timekey != 'TSTEP':
            renam = {self._timekey: 'TSTEP'}
            tmpf = tmpf.rename(**renam)
        tmpf.attrs.update(qf.attrs)
        tmpf.attrs['FILEDESC'] = '; '.join(filedesc)
        tmpf.attrs['HISTORY'] = '; '.join(self._log)
        tmpf.attrs['description'] = '; '.join(self._log)
        tmpf.attrs['NLAYS'] = outf.sizes['LAY']
        tmpf.attrs['VGTYP'] = qf.attrs['VGTYP']
        if self.outtmpl is False:
            return tmpf
        else:
            makedirs(realpath(dirname(outpath)), exist_ok=True)
            to_ioapi(tmpf, outpath, verbose=self.verbose)
            return outpath


def to_ioapi(
    bcf, outpath, format='NETCDF4_CLASSIC', vencoding=None, minvalue=1e-30,
    verbose=0
):
    """
    Save an xarray.Dataset as an IOAPI-formatted file.

    Arguments
    ---------
    bcf : xarray.Dataset
        Input file to be converted to IOAPI meta-data format
    outpath : str
        Path to save file
    format : str
        Output format NETCDF4_CLASSIC or NETCDF3_CLASSIC
    vencoding : dict
        Variable-level encoding

    Returns
    -------
    None
    """
    import pandas as pd
    import numpy as np
    if vencoding is None:
        vencoding = dict(zlib=True, complevel=1)
    vks = [k for k, v in bcf.data_vars.items() if 'LAY' in v.dims]
    nv = len(vks)
    vlist = ''.join([vk.ljust(16) for vk in vks])
    outdates = pd.to_datetime(bcf.TSTEP)
    jdate = np.asarray(outdates.strftime('%Y%j').astype('i'))
    jtime = np.asarray(outdates.strftime('%H%M%S').astype('i'))
    tf = np.zeros((bcf.sizes['TSTEP'], nv, 2), dtype='i')
    tf[:, :, 0] = jdate[:, None]
    tf[:, :, 1] = jtime[:, None]
    tf = xr.DataArray(
        tf, dims=('TSTEP', 'VAR', 'DATE-TIME'),
        attrs=dict(
            long_name='TFLAG'.ljust(16), units='<YYYYJJJ,HHMMSS>',
            var_desc='TFLAG'.ljust(80)
        )
    )
    history = bcf.attrs['HISTORY'].strip()
    descr = bcf.attrs.get('description', history).strip()
    outf = xr.Dataset()
    outf['TFLAG'] = tf
    for vk in vks:
        vmin = bcf[vk].min()
        if vmin < minvalue:
            wvals = bcf[vk].where(lambda x: x > minvalue)
            nna = int(wvals.isnull().sum())
            imsg = f'INFO:: {nna} values < {minvalue} removed from {vk}'
            history += '; ' + imsg
            descr += '; ' + imsg
            if verbose > 0:
                print(imsg)
            outv = wvals.fillna(minvalue)
        else:
            outv = bcf[vk]
        outf[vk] = outv
        outf[vk].encoding.update(vencoding)
        vattrs = outf[vk].attrs
        vattrs['long_name'] = vattrs['long_name'].ljust(16)
        vattrs['var_desc'] = vattrs['var_desc'].ljust(80)[:80]
        vattrs['units'] = vattrs['units'].ljust(16)

    if len(outdates) == 1:
        tf[:] = 0
        tstep = np.int32(0)
    else:
        dt = outdates.diff().mean()
        ds = int(dt.total_seconds())
        durationh = (outdates[1] - outdates[0]).total_seconds() / 3600
        if durationh > 670 and (ds / 3600) > 670:
            # if the duration of the file is more than a month
            # assume the file is approximately monthly. IOAPI cannot
            # store monthly files, so use the nearest 1d time step to
            # approximate it
            ds = 30 * 24 * 3600.

        nh = ds // 3600
        nm = (ds % 3600) // 60
        ns = round(ds % 60, 0)
        tstep = np.int32(nh * 10000 + nm * 100 + ns)
        nd = len(outdates)
        outdates = pd.date_range(outdates[0], periods=nd, freq=f'{ds}s')
        jdate = np.asarray(outdates.strftime('%Y%j').astype('i'))
        jtime = np.asarray(outdates.strftime('%H%M%S').astype('i'))
        tf[:, :, 0] = jdate[:, None]
        tf[:, :, 1] = jtime[:, None]

    outf.attrs.update(bcf.attrs)
    outf.attrs['TSTEP'] = tstep
    outf.attrs['SDATE'] = np.int32(tf[0, 0, 0])
    outf.attrs['STIME'] = np.int32(tf[0, 0, 1])
    now = pd.to_datetime('now', utc=True)
    njd = np.int32(now.strftime('%Y%j'))
    njt = np.int32(now.strftime('%H%M%S'))
    outf.attrs.update(WDATE=njd, WTIME=njt, CDATE=njd, CTIME=njt)
    outf.attrs['IOAPI_VERSION'] = 'N/A'.ljust(80)
    outf.attrs['UPNAM'] = 'aqmbc {__version__}'.ljust(16)[:16]
    outf.attrs['EXEC_ID'] = 'aqmbc {__version__}'.ljust(80)[:80]
    outf.attrs['VAR-LIST'] = vlist
    outf.attrs['NVARS'] = nv
    outf.attrs['HISTORY'] = history.ljust(60*80)[:60*80]
    outf.attrs['FILEDESC'] = outf.attrs['FILEDESC'].ljust(60*80)[:60*80]
    outf.attrs['description'] = descr
    idxs = list(outf.indexes)
    coords = list(outf.coords)
    outf = outf.drop_indexes(idxs).reset_coords(coords, drop=True)
    outf.to_netcdf(outpath, format='NETCDF4_CLASSIC')


def driver(cfg=None, **cfgkwds):
    """
    GDNAM : str
        Name of horizontal grid (12US1, 36US3, 108NHEMI2)
    gdpath : str
        Path to GRIDDESC file to find GDNAM definition.
    VGNAM : str
        Name of vertical grid (WRFHYBRID_35L, WRFHYBRID_44L, EMBER_35L)
    vgpath : str
        Path to find A/B components of vertical grid definition
    source : str
        Name of source (geoscf, geoschem, gcbench, cmaq, raqms, waccm, tcr)
    intmpl : str
        Template for date-specific inputs, which uses strftime
    outtmpl : str
        Template for date-specific outputs, which uses strftime
    exprs : list or None
        If None, defaults to typical values for source.
        If list of strings, loads expressions from files.
        If list of dictionaries, each dictionary should have units, expression,
        and name.
    bcon_dates : iterable
        Iterable of dates to process for lateral boundary conditions.
    icon_dates : iterable
        Iterable of dates to process for intial boundary conditions.
    """
    from copy import deepcopy
    if cfg is None:
        cfg = {}
    cfg = deepcopy(cfg)
    cfg.update(cfgkwds)
    from . import bcon
    from .utils import getmetaf, loadconfig
    opts = loadconfig(cfg)
    gkwds = ['GDNAM', 'gdpath', 'VGNAM', 'vgpath']
    gkwds = {k: v for k, v in opts.items() if k in gkwds}
    bdates = opts['bcon_dates']
    idates = opts['icon_dates']
    source = getattr(getattr(bcon, opts['source']), opts['source'])
    ckwds = ['intmpl', 'outtmpl', 'exprs', 'bcprefix']
    ckwds = {k: v for k, v in opts.items() if k in ckwds}
    out = {}
    if idates is not None:
        igf = getmetaf(**gkwds, FTYPE=1)
        ico = source(igf, **ckwds)
        ipaths = []
        for idate in idates:
            ipath = ico.process([idate])
            ipaths.append(ipath)
        out['icon'] = ipaths
    if bdates is not None:
        bgf = getmetaf(**gkwds, FTYPE=2)
        bco = source(bgf, **ckwds)
        bpaths = []
        if isinstance(bdates, dict):
            for fdate, bdates in sorted(bdates.items()):
                bpath = bco.process(bdates, fdate=fdate)
                bpaths.append(bpath)
        else:
            bpath = bco.process(bdates)
            bpaths.append(bpath)
        out['bcon'] = bpaths
    return out
