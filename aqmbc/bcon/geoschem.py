from .._core import icbc


class geoschem(icbc):
    def __init__(self, *args, bcprefix='SpeciesBC_', **kwds):
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
        bcprefix : str
            Prefix of collection with concentration data (e.g., SpeciesBC_,
            SpeciesConc_, or something custom). Default SpeciesBC_.

        Returns
        -------
        None
        """
        super().__init__(*args, **kwds)
        self._pmidkey = 'pmid'
        self._psfckey = 'ps'
        self._bcprefix = bcprefix

    def _opener(self, path, **kwds):
        import xarray as xr
        from ..utils import getstdatm
        from os.path import exists
        tmpf = xr.open_dataset(path, **kwds)
        bcprefix = self._bcprefix
        metpath = path.replace(bcprefix[:-1], 'StateMet')
        missp = 'Met_PMIDDRY' not in tmpf
        misst = 'Met_T' not in tmpf
        renamers = {
            k: k.replace(bcprefix, '')
            for k in tmpf.data_vars
            if k.startswith(bcprefix)
        }
        tmpf = tmpf.rename(**renamers)
        if missp or misst:
            if exists(metpath):
                metf = xr.open_dataset(metpath)
                tmpf['Met_PMIDDRY'] = metf['Met_PMIDDRY']
                tmpf['Met_T'] = metf['Met_T']
            else:
                refv = tmpf['O3']
                # GEOS-Chem stores hyam in hPa
                stdf = getstdatm(tmpf.hyam * 100, tmpf.hybm, refv=refv, p0=1e5)
                tmpf['Met_PMIDDRY'] = stdf['pmid'] / 100.
                tmpf['Met_PMIDDRY'].attrs.update(units='hPa')
                tmpf['Met_T'] = stdf['tmid']

        tmpf['pmid'] = tmpf['Met_PMIDDRY'] * 100
        tmpf['pmid'].attrs.update(units='Pa')
        if 'hybm' in tmpf:
            sfc_hybm = tmpf.hybm[0]
        else:
            sfc_hybm = 0.992476
        tmpf['ps'] = tmpf['pmid'][:, 0] / sfc_hybm
        # overwrite to add derived variables if necessary
        return tmpf.load()
