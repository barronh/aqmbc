import xarray as xr


class icbc:
    def __init__(
        self, metaf, intmpl, exprs=None, outtmpl=None, ofreq='24h', verbose=99
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
        self.ofreq = ofreq
        self._f = None
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
            outtmpl = f'{ctxt}_{gtxt}_{vtxt}_{bctxt}_%Y-%m-%dT%H%M%S.nc'
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
        if self._f is not None:
            f = self._f
            if date >= f.time.min() and date <= f.time.max():
                return
        path = self._activepath = date.strftime(self.intmpl)
        self.log(f'Opening {path}', level='STATUS', source='load_date')
        self._f = self._opener(self._activepath)

    def to_lonlat(self, lon, lat, method='nearest'):
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
        self, dates, fdate=None, pres=None, zkwds=None, overwrite=True
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
        None
        """
        from os.path import exists
        import pandas as pd
        cname = self.__class__.__name__
        dates = pd.to_datetime(dates)
        if fdate is None:
            fdate = dates[0]
        outpath = fdate.strftime(self.outtmpl)
        fs = []
        qf = self._metaf
        if zkwds is None:
            zkwds = {}
        imsg = f'{cname} processing {dates}'
        self.log(imsg, level='INFO', clear=True)
        for date in dates:
            imsg = f'{cname} processing {date}'
            self.log(imsg, level='INFO')
            if self.verbose > 0:
                print(imsg, end='...', flush=True)
            if exists(outpath) and not overwrite:
                continue
            self.load_date(date)
            self.to_lonlat(qf.lon, qf.lat)
            if pres is None:
                self.to_hyb(qf.hyam, qf.hybm, **zkwds)
            else:
                self.to_pres(pres, pmidkey=self._pmidkey, **zkwds)
            outf = self.translate()
            fs.append(outf)
            if self.verbose > 0:
                print()
        tmpf = xr.concat(fs, dim=self._timekey)
        if self._timekey != 'TSTEP':
            renam = {self._timekey: 'TSTEP'}
            tmpf = tmpf.rename(**renam)
        tmpf.attrs.update(qf.attrs)
        tmpf.attrs['HISTORY'] = '; '.join(self._log)
        to_ioapi(tmpf, outpath, verbose=self.verbose)


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
    outf = xr.Dataset()
    outf['TFLAG'] = tf
    for vk in vks:
        vmin = bcf[vk].min()
        if vmin < minvalue:
            if verbose:
                imsg = f'INFO:: Values less than {minvalue} removed from {vk}'
                print(imsg)
            outv = bcf[vk].where(lambda x: x < minvalue).fillna(minvalue)
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
        nh = ds // 3600
        nm = (ds % 3600) // 60
        ns = round(ds % 60, 0)
        tstep = np.int32(nh * 10000 + nm * 100 + ns)

    outf.attrs.update(bcf.attrs)
    outf.attrs['TSTEP'] = tstep
    outf.attrs['SDATE'] = np.int32(tf[0, 0, 0])
    outf.attrs['STIME'] = np.int32(tf[0, 0, 1])
    outf.attrs['VAR-LIST'] = vlist
    outf.attrs['NVARS'] = nv
    outf.attrs['HISTORY'] = outf.attrs['HISTORY'].ljust(60*80)[:60*80]
    outf.attrs['FILEDESC'] = outf.attrs['FILEDESC'].ljust(60*80)[:60*80]
    coords = list(outf.coords)
    outf = outf.drop_indexes(coords).reset_coords(coords, drop=True)
    outf.to_netcdf(outpath, format='NETCDF4_CLASSIC')
