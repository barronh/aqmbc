from .._core import icbc


class geoscf(icbc):
    def _opener(self, path):
        import xarray as xr
        from ..utils import gethybf
        hybf = gethybf('GEOS5')
        if path.endswith('.txt'):
            with open(path) as plist:
                paths = plist.read().split()
            tmpfs = [xr.open_dataset(p) for p in paths]
            tmpf = xr.merge(tmpfs, join="override")
            tmpf = tmpf.rename({key: key.lower() for key in tmpf.data_vars})
        else:
            tmpf = xr.open_dataset(path)
        nz = tmpf.sizes['lev']
        hyai = hybf.hyai.data[:nz + 1][::-1]
        hybi = hybf.hybi.data[:nz + 1][::-1]
        hyam = (hyai[1:] + hyai[:-1]) / 2
        hybm = (hybi[1:] + hybi[:-1]) / 2
        tmpf['hybm'] = ('lev',), hybm
        tmpf['hyam'] = ('lev',), hyam
        ps = tmpf['ps']
        tmpf['pmid'] = (ps * tmpf['hybm'] + tmpf['hyam']).transpose(
            'time', 'lev', 'lat', 'lon'
        )
        # overwrite to add derived variables if necessary
        return tmpf.load()
