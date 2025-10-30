from .._core import icbc


class cmaq(icbc):
    def __init__(self, *args, **kwds):
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

        Notes
        -----
        Uses TSTEP as time dimension, PRES as layer-mid pressure, and PRSFC as
        surface pressrue. If PRES is not provided, it will be derived assuming
        WRFTERRAIN_{NLAYS}L or WRFHYBRID_{NLAYS}L hyam and hybm structure.
        """
        super().__init__(*args, **kwds)
        self._timekey = 'TSTEP'
        self._pmidkey = 'PRES'
        self._psfckey = 'PRSFC'

    def _opener(self, path):
        import pyproj
        from ..utils import gethybf, open_ioapi

        qf = open_ioapi(path)
        if self._pmidkey not in qf.data_vars:
            nz = qf.sizes['LAY']
            if qf.attrs['VGTYP'] == 7:
                pfx = 'WRFTERRAIN_'
            else:
                pfx = 'WRFHYBRID_'
            hyb = gethybf(VGNAM=f'{pfx}{nz}L')
            p = 1e5 * hyb.hybm + hyb.hyam
            pdims = ('TSTEP', 'LAY', 'ROW', 'COL')
            edims = {pk: qf.coords[pk] for pk in pdims if pk != 'LAY'}
            qf[self._pmidkey] = p.expand_dims(**edims).transpose(*pdims)
            qf[self._pmidkey].attrs.update(units='Pa')
            l1hybm = hyb.hybi[0]
        elif qf.VGTYP in (7, -9999):
            # Assuming near-surface sigma coordinate is approximately
            # terrain following.
            l1hybm = qf.VGLVLS[:2].mean()
        else:
            wmsg = 'Unknown VGTYP ({qf.VGTYP}); assuming max pressure is'
            wmsg += ' 99% of surface pressure.'
            self.log(wmsg, level='WARN', source='_opener')
            l1hybm = .99

        if self._psfckey not in qf.data_vars:
            qf[self._psfckey] = qf[self._pmidkey][:, 0] / l1hybm
            qf[self._psfckey].attrs.update(units='Pa')
        self._proj = pyproj.Proj(qf.crs_proj4)
        return qf

    def to_lonlat(self, lon, lat, method='nearest', extrapolate='warn'):
        """
        Thin wrapper around icbc.to_lonlat to convert lon/lat to COL/ROW first
        """
        # overwrite to support projections
        if self.verbose > 0:
            print(f'INFO:: Extracting n={lon.size} lon/lat pairs')

        COL, ROW = self._proj(lon, lat)
        if extrapolate in ('warn', 'error'):
            west = 0.
            east = float(self._metaf.NCOLS)
            south = 0.
            north = float(self._metaf.NROWS)
            outside = dict(
                west=int(((COL - west) < 0).sum()),
                east=int(((COL - east) > 0).sum()),
                south=int(((ROW - south) < 0).sum()),
                north=int(((ROW - north) > 0).sum()),
            )
            outside = {k: v for k, v in outside.items() if v > 0}
            if len(outside) > 0:
                rmin = float(ROW.min())
                rmax = float(ROW.max())
                cmin = float(COL.min())
                cmax = float(COL.max())
                wmsg = 'Some points out of bbox'
                wmsg += f' ({west}, {south}, {east}, {north}); {outside};'
                wmsg += ' Requested ranges '
                wmsg += f'ROW=({rmin}, {rmax}); COL=({cmin}, {cmax})'
                if extrapolate == 'warn':
                    self.log(wmsg, level='WARN', source='to_lonlat')
                else:
                    raise ValueError(wmsg)

        self._f = self._f.sel(ROW=lat, COL=lon, method=method)
