# every tenth element of the raveled lat lon from an LCC (36US3) and a polar
# stereographic domain latitude and longitude. Verified by comparison with
# PseudoNetCDF griddesc
_check10th = {
   ('36US3', 1): {
        "lat": [12.376, 18.295, 24.428, 29.325, 32.611, 33.35, 41.562, 48.321,
                53.074, 55.379, 55.216],
        "lon": [-121.87, -78.988, -89.886, -102.343, -116.156, -62.218,
                -73.929, -88.535, -106.196, -126.267, -48.593],
    },
   ('36US3', 2): {
        "lat": [12.092, 15.259, 14.312, 17.021, 35.967, 54.239, 62.086, 60.588,
                16.887, 36.062, 54.717],
        "lon": [-121.788, -102.452, -82.617, -67.744, -59.599, -45.822,
                -109.999, -70.047, -123.547, -130.968, -143.651],
    },
   ('108NHEMI2', 1): {
        "lat": [-15.128, 10.575, 28.869, 9.374, 31.574, 85.45, 25.206, 14.263,
                30.737, 8.04, -12.739],
        "lon": [-143.0, -71.741, -117.654, -162.335, -27.722, 172.0, 154.699,
                20.202, 69.905, 112.964, 39.573],
    },
   ('108NHEMI2', 2): {
        "lat": [-15.425, 2.905, -5.026, -4.758, 2.79, -15.718, 2.669, -4.492,
                -5.296, 3.014, -15.131],
        "lon": [-142.694, -108.84, -66.768, -38.784, 3.427, 37.0, 94.011, 51.668,
                -156.325, 161.749, 127.616],
    },
}


def test_getllf():
    import numpy as np
    from ..utils import getllf
    for (GDNAM, FTYPE), chk in _check10th.items():
        llf = getllf(GDNAM=GDNAM, FTYPE=FTYPE)
        latv = llf.lat.values.ravel()
        latv = latv[::latv.size // 10].round(3)
        lonv = llf.lon.values.ravel()
        lonv = lonv[::lonv.size // 10].round(3)
        assert np.allclose(latv, chk['lat'])
        assert np.allclose(lonv, chk['lon'])


def test_zinterp():
    import numpy as np
    import xarray as xr
    from ..utils import zinterp
    srcf = xr.Dataset()
    dpedges = np.arange(1e5, 0, -1e4)
    dpmid = (dpedges[1:] + dpedges[:-1]) / 2
    dpmid = xr.DataArray(dpmid[None, :], dims=('time', 'LAY'))
    # with pressure weighting
    chkpmid = np.array([[
        90000., 85882.35, 76000., 66153.85, 56363.64, 46666.67, 37142.86,
        30000., 30000.
    ]])
    # without pressure weighting
    chkmid = np.array([[
        90000., 85000., 75000., 65000., 55000., 45000., 35000., 30000.,
        30000.
    ]])
    spedges = np.arange(1e5, 0, -2e4)
    spmid = (spedges[1:] + spedges[:-1]) / 2
    srcf['pmid'] = ('LAY',), spmid, dict(units='Pa')
    srcf = srcf.expand_dims('time').transpose('time', 'LAY')
    for pweight, chk in [(True, chkpmid), (False, chkmid)]:
        testf = zinterp(srcf, srcf['pmid'], dpmid, pweight=pweight)
        assert np.allclose(testf.pmid.round(2), chk)
        isrcf = srcf.isel(LAY=slice(None, None, -1))
        itestf = zinterp(isrcf, isrcf['pmid'], dpmid, pweight=pweight)
        assert np.allclose(itestf.pmid.round(2), chk)
