from .._core import icbc


class raqms(icbc):
    def _opener(self, path):
        import xarray as xr
        tmpf = xr.open_dataset(path)
        tmpf['ps'] = tmpf['psfc'] * 100
        tmpf['ps'].attrs['units'] = 'Pa'
        tmpf['pmid'] = tmpf['pdash'] * 100
        tmpf['pmid'].attrs['units'] = 'Pa'
        # overwrite to add derived variables if necessary
        return tmpf[['pmid', 'ps']].load()

    def to_lonlat(self, lon, lat, method='nearest'):
        """
        Thin wrapper around icbc.to_lonlat to convert lon to [0, 360] first
        """
        super().to_lonlat(lon % 360, lat, method='nearest')
