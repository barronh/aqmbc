__all__ = ['haversinenn']


def haversinenn(srcf, dstf, isdegrees=True):
    """
    Flexible nearest neighbor in haversine space function

    Arguments
    ---------
    srcf : xr.Dataset
        Must have lon and lat in degrees with any dimensions
    dstf : xr.Dataset
        Must have lon and lat in degrees with any dimensions

    Returns
    -------
    idxf : xr.Dataset
        Has variables for each dimension of srcf.lon where each variables
        values are the 0-based index (use isel) for that dimension.

    Examples
    --------

    ```python
    import numpy as np
    import xarray as xr
    from aqmbc.utils import haversinenn
    d = xr.Dataset()
    d['lon'] = ('PERIM',), [-80., -30, -30, -30, -130, -80, -130, -130]
    d['lat'] = ('PERIM',), [20., 20, 40, 60, 60, 60, 20, 40]
    s = xr.Dataset()
    s.coords['lon'] = np.arange(-182.5, 180, 5, dtype='d')
    s.coords['lat'] = np.arange(-87, 90, 4, dtype='d')
    s['testlat'], s['testlon'] = xr.broadcast(s.lat, s.lon)
    s['test'] = np.sin(np.radians(s.lat)) + np.sin(np.radians(s.lon))
    i = haversinenn(s, d)
    satd = s.isel(**i.coords)
    ```
    """
    import numpy as np
    import xarray as xr
    from sklearn.neighbors import NearestNeighbors
    # destination shape and dims
    slat, slon = xr.broadcast(srcf['lat'], srcf['lon'])
    sshape = slon.shape
    sdims = slon.dims
    dlat, dlon = xr.broadcast(dstf['lat'], dstf['lon'])
    dshape = dlon.shape
    ddims = dlon.dims
    # Stack coordinates lat first and then lon for haversine
    incoords = np.stack([
        slat[:].to_numpy().ravel(),
        slon[:].to_numpy().ravel(),
    ], axis=-1)
    outcoords = np.stack([
        dlat.to_numpy().ravel(),
        dlon.to_numpy().ravel()
    ], axis=-1)
    # haversine requires radians
    if isdegrees:
        incoords = np.radians(incoords)
        outcoords = np.radians(outcoords)

    # Create, fit and predict distances to nearest index
    knn = NearestNeighbors(n_neighbors=1, metric='haversine')
    knn.fit(incoords)
    knn_dist, knn_idx = knn.kneighbors(outcoords)
    knn_idxs = np.unravel_index(knn_idx, sshape)
    knn_idxs = dict(zip(sdims, knn_idxs))
    cidxs = {
        kd: xr.DataArray(ki.reshape(dshape), dims=ddims, name=kd)
        for kd, ki in knn_idxs.items()
    }
    cidxs = xr.Dataset(coords=cidxs)
    cidxs['dist'] = ddims, knn_dist.reshape(dshape), {'units': 'rad'}
    return cidxs
