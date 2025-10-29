__all__ = ['open_ioapi', 'attrs2proj']
_lcctmpl = (
    '+proj=lcc +lat_1={P_ALP} +lat_2={P_BET} +lat_0={YCENT} +lon_0={P_GAM}'
    + ' +R={earth_radius} +x_0={x_0} +y_0={y_0} +to_meter={XCELL}'
    + ' +no_defs'
)
_poltmpl = (
    '+proj=stere +lat_0={lat_0} +lat_ts={P_BET} +lon_0={P_GAM} +x_0={x_0}'
    + ' +y_0={x_0} +R={earth_radius} +to_meter={XCELL} +no_defs'
)


def attrs2proj(attrs, earth_radius=6370000.0):
    pattrs = {'earth_radius': earth_radius}
    pattrs.update({
        k: (v.item() if hasattr(v, 'item') else v)
        for k, v in attrs.items() if k != 'VGLVLS'
    })
    pattrs['x_0'] = -pattrs['XORIG']
    pattrs['y_0'] = -pattrs['YORIG']
    if attrs['GDTYP'] == 2:
        tmpl = _lcctmpl
    elif attrs['GDTYP'] == 6:
        tmpl = _poltmpl
        pattrs['lat_0'] = pattrs['P_ALP'] * 90.
    else:
        raise KeyError('Unknown grid type')
    projstr = tmpl.format(**pattrs)
    return projstr


def open_ioapi(path):
    import xarray as xr
    qf = xr.open_dataset(path, decode_cf=False)
    _addcoords(qf)
    return qf


def open_griddesc(attrs):
    import xarray as xr
    qf = xr.Dataset()
    qf.attrs.update(attrs)
    _addcoords(qf)
    return qf


def _addcoords(qf):
    import xarray as xr
    import pandas as pd
    import numpy as np
    attrs = qf.attrs
    hastattrs = all([k in attrs for k in 'SDATE STIME TSTEP'.split()])
    if 'TFLAG' in qf.data_vars:
        js = xr.DataArray(np.array([1000000, 1]), dims=('DATE-TIME',))
        jdates = (qf['TFLAG'][:, 0, :] * js).sum('DATE-TIME')
        qf.coords['TSTEP'] = pd.to_datetime(jdates, format='%Y%j%H%M%S')
    elif hastattrs and 'TSTEP' in qf.sizes:
        nt = qf.sizes['TSTEP']
        dhhmmss = attrs['TSTEP']
        hh = dhhmmss // 10000
        mm = (dhhmmss % 10000) // 100
        ss = dhhmmss % 100
        ds = pd.to_timedelta(hh * 3600. + mm * 60. + ss, unit='s')
        t0 = pd.to_datetime(qf.SDATE * 1000000 + qf.STIME, format='%Y%j%H%M%S')
        time = pd.date_range(t0, periods=nt, freq=ds)
        qf.coords['TSTEP'] = time
    if 'VGLVLS' in attrs:
        qf.coords['LEV'] = (qf.VGLVLS[1:] + qf.VGLVLS[:-1]) / 2
    nr = qf.sizes.get('ROW', attrs['NROWS'])
    nc = qf.sizes.get('COL', attrs['NCOLS'])
    if attrs['FTYPE'] == 1:
        qf.coords['ROW'] = np.arange(nr) + 0.5
        qf.coords['COL'] = np.arange(nc) + 0.5
    if attrs['FTYPE'] == 2:
        nperim = qf.sizes.get('PERIM', (nr + 1 + nc + 1) * 2)
        qf.coords['PERIM'] = np.arange(nperim) + 0.5
    projstr = attrs2proj(attrs)
    qf.attrs['crs_proj4'] = projstr
