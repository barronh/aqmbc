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
        "lon": [-142.694, -108.84, -66.768, -38.784, 3.427, 37.0, 94.011,
                51.668, -156.325, 161.749, 127.616],
    },
}


def test_loadexpr_dicts():
    from ..utils import loadexpr
    inp = [{'name': 'O3', 'expression': 'o3vmr[:] * 1e6', 'units': 'ppmV'}]
    out = loadexpr(None)
    assert out is None
    out = loadexpr([])
    assert len(out) == 0
    out = loadexpr(inp)
    assert len(out) == 1
    for k in inp[0]:
        assert inp[0][k] == out[0][k]
    for excludek in ['name', 'expression', 'units']:
        inpi = [{k: v for k, v in el.items() if k != excludek} for el in inp]
        try:
            out = loadexpr(inpi)
            raise IOError(f'should have failed - {excludek} is required')
        except Exception:
            pass

    for intk in ['name', 'expression', 'units']:
        inpi = [{k: v for k, v in el.items()} for el in inp]
        inpi[0][intk] = 1
        try:
            out = loadexpr(inpi)
        except Exception:
            continue
        raise IOError(f'should have failed - {intk} should be str')


def test_loadexpr_paths():
    import os
    from ..data.expressions import named_exprs
    from ..utils import loadexpr
    for name, paths in named_exprs.items():
        if paths is not None:
            out1 = loadexpr(paths)
            assert len(out1) > 0
            paths = [os.path.basename(p) for p in paths]
            out2 = loadexpr(paths)
            assert len(out1) == len(out2)


def test_loadexpr_names():
    from ..utils import loadexpr
    for name in ['geoschem', ('geoschem',), ['geoschem'], [('geoschem',)]]:
        out = loadexpr(name)
        assert len(out) > 0
    for name in ['geos-chem', ('geos-chem',)]:
        try:
            out = loadexpr(name)
        except:
            continue
        raise IOError(f'{name} does not exist; should have failed')


def test_loadconfig():
    import numpy as np
    from ..utils import loadconfig
    dates = ['2025-12-31', '2026-01-01', '2026-01-01']

    config = {
        "source": "gchp",
        "intmpl": '/work/ROMO/users/bhenders/temp/gchp/GEOSChem.BoundaryConditions.%Y%m%d_%H00z.nc4',
        "GDNAM": '108US2', "VGNAM": 'WRFHYBRID_35L',
        "bcon_dates": dates, "icon_dates": dates[:1],
        "verbose": 99
    }
    cfg1 = loadconfig(config)
    dates1 = cfg1['bcon_dates']
    config2 = {k: v for k, v in config.items()}
    config2['bcon_dates'] = {'2026-01-01': dates}
    cfg2 = loadconfig(config2)
    dates2 = cfg2['bcon_dates']['2026-01-01']
    assert len(dates1) == len(dates2)
    for d1, d2 in zip(dates1, dates2):
        assert d1 == d2


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
    # with pressure weighting -- higher pressure than otherwise. Intended to
    # to account for intensive variables (mixing ratios) being more weighted
    # toward higher pressures
    chkpmid = np.array([[
        9e4, 85882.35, 76e3, 66153.85, 56363.64, 46666.67, 37142.86, 3e4, 3e4
    ]])
    # without pressure weighting
    chkmid = np.array([[
        90000., 85000., 75000., 65000., 55000., 45000., 35000., 30000., 30000.
    ]])
    # Define destination coordinate
    dpedges = np.arange(1e5, 0, -1e4)
    dpmid = (dpedges[1:] + dpedges[:-1]) / 2
    dpmid = xr.DataArray(dpmid[None, :], dims=('time', 'LAY'))
    # Define source file with coordinate
    srcf = xr.Dataset()
    spedges = np.arange(1e5, 0, -2e4)
    spmid = (spedges[1:] + spedges[:-1]) / 2
    srcf['pmid'] = ('time', 'LAY',), spmid[None, :], dict(units='Pa')
    for pweight, chk in [(True, chkpmid), (False, chkmid)]:
        testf = zinterp(srcf, srcf['pmid'], dpmid, pweight=pweight)
        assert np.allclose(testf.pmid.round(2), chk)
        isrcf = srcf.isel(LAY=slice(None, None, -1))
        itestf = zinterp(isrcf, isrcf['pmid'], dpmid, pweight=pweight)
        assert np.allclose(itestf.pmid.round(2), chk)
