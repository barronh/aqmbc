from .._core import icbc


class cmaq(icbc):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self._pmidkey = 'PRES'
        self._psfckey = 'PRSFC'
        self._timekey = 'TSTEP'

    def _opener(self, path):
        import pyrsig
        import pyproj
        from ..utils import gethybf

        qf = pyrsig.open_ioapi(path)
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

        qf[self._psfckey] = qf[self._pmidkey][:, 0] / hyb.hybi[0]
        qf[self._psfckey].attrs.update(units='Pa')
        self._proj = pyproj.Proj(qf.crs_proj4)
        return qf

    def to_lonlat(self, lon, lat, method='nearest'):
        """
        Thin wrapper around icbc.to_lonlat to convert lon/lat to COL/ROW first
        """
        COL, ROW = self._proj(lon, lat)
        # overwrite to support projections
        if self.verbose > 0:
            print(f'INFO:: Extracting n={lon.size} lon/lat pairs')
        self._f = self._f.sel(ROW=lat, COL=lon, method=method)
