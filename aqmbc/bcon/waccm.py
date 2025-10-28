from .._core import icbc


class waccm(icbc):
    def __init__(self, *args, **kwds):
        super().__init__(*args, **kwds)
        self._pmidkey = 'pmid'
        self._psfckey = 'PS'

    def _opener(self, path):
        import xarray as xr
        import pandas as pd
        import pdb; pdb.set_trace()
        latmin = float(self._metaf.lat.min() - 2)
        latmax = float(self._metaf.lat.max() + 2)
        lonmin = float(self._metaf.lon.min() - 2)
        lonmax = float(min(self._metaf.lon.max() + 2, 360))
        xlim = slice(lonmin % 360, lonmax % 360)
        ylim = slice(latmin, latmax)
        tmpf = xr.open_dataset(path)
        tmpf = tmpf.sel(lon=xlim, lat=ylim)
        dims = ('time', 'lev', 'lat', 'lon')
        tmpf['pmid'] = (
            tmpf['hyam'] * tmpf['P0'][...] + tmpf['hybm'] * tmpf['PS']
        ).transpose(*dims)
        tmpf['pmid'].attrs['units'] = 'Pa'
        # overwrite to add derived variables if necessary
        return tmpf.load()

    def to_lonlat(self, lon, lat, method='nearest'):
        """
        Thin wrapper around icbc.to_lonlat to convert lon to [0, 360] first
        """
        super().to_lonlat(lon % 360, lat, method='nearest')
