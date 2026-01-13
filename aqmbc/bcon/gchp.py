from .geoschem import geoschem


class gchp(geoschem):
    def _opener(self, path):
        return super()._opener(path, drop_variables=['anchor'])

    def to_lonlat(self, lon, lat, method='nearest', extrapolate='warn'):
        """
        Thin wrapper around icbc.to_lonlat to convert lon/lat nf, Ydim, Xdim

        GCHP uses a gnomonic-cubed sphere and output contains lons and lats
        variables that have dimensions nf, Ydim, and Xdim.
        - nf : number of faces; cubed spheres have 6
        - Ydim : number of elements in the y-axis
        - Xdim : number of elements in the x-axis (Xdim == Ydim)

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
            self._f['lats'][:].data.ravel(),
            self._f['lons'][:].data.ravel(),
        ], axis=-1)  # incoords are in degrees
        outcoords = np.stack([
            lat.to_numpy().ravel(),
            lon.to_numpy().ravel() % 360
        ], axis=-1)
        knn = NearestNeighbors(n_neighbors=1, metric='haversine')
        knn.fit(np.radians(incoords))  # radians for compat with haversine
        knn_dist, knn_idx = knn.kneighbors(np.radians(outcoords))
        knn_idx = knn_idx.ravel()
        sizes = self._f.sizes
        shape = (sizes['nf'], sizes['Ydim'], sizes['Xdim'])
        nf, ydim, xdim = np.unravel_index(knn_idx, shape)
        nf = xr.DataArray(nf.reshape(lon.shape), dims=lon.dims)
        xdim = xr.DataArray(xdim.reshape(lon.shape), dims=lon.dims)
        ydim = xr.DataArray(ydim.reshape(lon.shape), dims=lon.dims)
        self._f = self._f.isel(nf=nf, Xdim=xdim, Ydim=ydim)
        if self.verbose > 0:
            elon = self._f['lons'].to_numpy()
            elat = self._f['lats'].to_numpy()
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
