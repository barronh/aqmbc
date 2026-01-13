from .cmaq import cmaq
from .._core import icbc


class mpascmaq(cmaq):
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
        self._timekey = 'Time'
        self._pmidkey = 'PRES'
        self._psfckey = 'PRSFC'

    def _opener(self, path):
        """
        mpascmaq uses the standard icbc opener, but adds the Time coordinate
        variable and heuristically selects CMAQ-related variables:

        A variable is a CMAQ variable when its dimensions match and name is
        all uppercase.

        dims == ('Time', 'nCells', 'nVertLevels') and key == key.upper()

        Also keeping pressure, surface_pressure, latCell, and lonCell.
        """
        import pandas as pd
        tmpf = icbc._opener(self, path)
        qdims = ('Time', 'nCells', 'nVertLevels')
        keep = [
            'pressure', 'surface_pressure', 'latCell', 'lonCell'
        ] + [
            k for k, v in tmpf.data_vars.items()
            if (
                v.dims == qdims
                and k == k.upper()
                and len(k) < 16
            )
        ]
        time = pd.to_datetime(tmpf['xtime'].str.replace(b'_', b'T').astype('U'))
        tmpf = tmpf[keep]
        tmpf.coords['Time'] = time
        return tmpf.rename(pressure='PRES', surface_pressure='PRSFC')

    def to_lonlat(self, lon, lat, method='nearest', extrapolate='warn'):
        """
        Thin wrapper around icbc.to_lonlat to convert lon/lat to dimension
        nCells

        MPAS-CMAQ uses an unstructured grid and output contains lons and lats
        as variables latCell and lonCell with dimension nCell. The coordinates
        are stored in spherical radians.

        Notes:
        For ease, all coordinates are loaded into an 2d array (cells, yx) and
        NearestNeighbors from sklearn.neighbors is used with the haversine
        metric to identify the nearest neighbor. The haversine metric requries
        y/x order and degrees are translated to radians.
        """
        import numpy as np
        import xarray as xr
        from sklearn.neighbors import NearestNeighbors
        if method != 'nearest':
            print(
                'WARN:: gchp only supports method="nearest"'
                + f'({method} ignored)'
            )
        # overwrite to support projections
        if self.verbose > 0:
            print(f'INFO:: Extracting n={lon.size} lon/lat pairs')

        incoords = np.stack([
            self._f['latCell'][:].data.ravel(),
            self._f['lonCell'][:].data.ravel(),
        ], axis=-1)  # incoords are in radians; compat w/ haversine
        outcoords = np.stack([
            lat.to_numpy().ravel(),
            lon.to_numpy().ravel()
        ], axis=-1)  # out coords in degrees
        knn = NearestNeighbors(n_neighbors=1, metric='haversine')
        knn.fit(incoords)
        knn_dist, knn_idx = knn.kneighbors(np.radians(outcoords))
        cidx = xr.DataArray(knn_idx.reshape(lon.shape), dims=lon.dims)
        # Moving z dimension to second position (i=1)
        tdims = ('Time', 'nVertLevels') + lon.dims
        self._f = self._f.isel(nCells=cidx).transpose(*tdims)
        if self.verbose > 0:
            elon = np.degrees(self._f['lonCell'].to_numpy())
            elat = np.degrees(self._f['latCell'].to_numpy())
            elon = np.where(elon > 180, elon - 360, elon)
            ecoords = np.stack([elat.ravel(), elon.ravel()], axis=-1)
            dist = ((ecoords - outcoords)**2).sum(-1)**.5
            print('INFO:to_lonlat:dist:source/dest distances (deg)')
            print(f'INFO:to_lonlat:dist:median: {np.median(dist):.8e} deg')
            print(f'INFO:to_lonlat:dist:mean: {np.mean(dist):.8e} deg')
            print(f'INFO:to_lonlat:dist:std: {np.std(dist):.8e} deg')
            print(f'INFO:to_lonlat:dist:max: {np.max(dist):.8e} deg')
        if self.verbose > 1:
            imid = ecoords.shape[0]
            for tag, cidx in [('first', 0), ('mid', imid), ('last', -1)]:
                msg = f'INFO:to_lonlat:dest:{tag}:lat,lon'
                print('{}:{:.8e},{:.8e} deg'.format(msg, *outcoords[0]))
                msg = f'INFO:to_lonlat:srce:{tag}:lat,lon'
                print('{}:{:.8e},{:.8e} deg'.format(msg, *ecoords[0]))
                msg = f'INFO:to_lonlat:dist:{tag}'
                print('{}:{:.8e} deg'.format(msg, dist[0]))
