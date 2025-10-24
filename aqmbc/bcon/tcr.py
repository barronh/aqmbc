from .._core import icbc


class tcr(icbc):
    def _opener(self, path):
        raise IOError('Need to implement multipath merge reader')

    def to_lonlat(self, lon, lat, method='nearest'):
        """
        Thin wrapper around icbc.to_lonlat to convert lon to [0, 360] first
        """
        super().to_lonlat(lon % 360, lat, method='nearest')
