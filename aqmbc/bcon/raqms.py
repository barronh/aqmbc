from .._core import icbc


class raqms(icbc):
    def _opener(self, path):
        import xarray as xr
        import pandas as pd
        latmin = float(self._metaf.lat.min() - 2)
        latmax = float(self._metaf.lat.max() + 2)
        lonmin = float(self._metaf.lon.min() - 2)
        lonmax = float(min(self._metaf.lon.max() + 2, 360))
        xlim = slice(lonmin % 360, lonmax % 360)
        ylim = slice(latmin, latmax)
        tmpf = xr.open_dataset(path)
        tmpf.coords['time'] = pd.to_datetime(tmpf['IDATE'], format='%Y%m%d%H')
        tmpf = tmpf.sel(lon=xlim, lat=ylim)
        tmpf['ps'] = tmpf['psfc'] * 100
        tmpf['ps'].attrs['units'] = 'Pa'
        tmpf['pmid'] = tmpf['pdash'] * 100
        tmpf['pmid'].attrs['units'] = 'Pa'
        # overwrite to add derived variables if necessary
        return tmpf.load()

    def to_lonlat(self, lon, lat, method='nearest'):
        """
        Thin wrapper around icbc.to_lonlat to convert lon to [0, 360] first
        """
        super().to_lonlat(lon % 360, lat, method='nearest')
