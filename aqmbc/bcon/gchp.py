from .geoschem import geoschem

class gchp(geoschem):
    def _opener(self, path):
        return super()._opener(path, drop_variables=['anchor'])
    
    def to_lonlat(self, lon, lat, method='nearest', extrapolate='warn'):
        """
        Thin wrapper around icbc.to_lonlat to convert lon/lat nf, Xdim, Ydim
        """
        import numpy as np
        import xarray as xr
        from sklearn.neighbors import NearestNeighbors
        if method != 'nearest':
            print(f'WARN:: Only supports nearest')
        # overwrite to support projections
        if self.verbose > 0:
            print(f'INFO:: Extracting n={lon.size} lon/lat pairs')

        incoords = np.stack([
            self._f['lons'][:].data.ravel(),
            self._f['lats'][:].data.ravel()
        ], axis=-1)
        outcoords = np.stack([lon.data.ravel() % 360, lat.data.ravel()], axis=-1)
        knn = NearestNeighbors(n_neighbors=1, metric='haversine')
        knn.fit(incoords)
        knn_dist, knn_idx = knn.kneighbors(outcoords)
        knn_idx = knn_idx.ravel()
        sizes = self._f.sizes
        shape = (sizes['nf'], sizes['Ydim'], sizes['Xdim'])
        nf, ydim, xdim = np.unravel_index(knn_idx, shape)
        nf = xr.DataArray(nf.reshape(lon.shape), dims=lon.dims)
        xdim = xr.DataArray(xdim.reshape(lon.shape), dims=lon.dims)
        ydim = xr.DataArray(ydim.reshape(lon.shape), dims=lon.dims)
        test = self._f.isel(nf=nf, Xdim=xdim, Ydim=ydim)
        # print(outcoords[0])
        # print(test.lons[0].data, test.lats[0].data)
        # import pdb; pdb.set_trace()
        self._f = self._f.isel(nf=nf, Xdim=xdim, Ydim=ydim)
