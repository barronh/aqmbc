__all__ = ['gethybf', 'getllf', 'getmetaf']


def getllf(GDNAM, gdpath=None, FTYPE=2):
    import xarray as xr
    import PseudoNetCDF as pnc
    if isinstance(FTYPE, str):
        FTYPE = {'bcon': 2, 'icon': 1}
    if gdpath is None:
        from os.path import join
        from ..data import dataroot
        gdpath = join(dataroot, 'GRIDDESC')
    gf = pnc.pncopen(gdpath, format='griddesc', GDNAM=GDNAM, FTYPE=FTYPE)
    if FTYPE == 2:
        dims = ('PERIM',)
    else:
        dims = ('ROW', 'COL',)
    lat = xr.DataArray(gf.variables['latitude'].array(), dims=dims)
    lon = xr.DataArray(gf.variables['longitude'].array(), dims=dims)
    outf = xr.Dataset()
    outf['lat'] = lat
    outf['lon'] = lon
    outf.attrs.update({k: gf.getncattr(k) for k in gf.ncattrs()})
    return outf


def gethybf(VGNAM, vgpath=None, vgdf=None):
    import xarray as xr
    import pandas as pd
    if vgdf is None:
        if vgpath is None:
            from os.path import join
            from ..data import vertgridroot
            vgpath = join(vertgridroot, f'{VGNAM}.csv')
        vgdf = pd.read_csv(vgpath)
        if 'edge_mid' in vgdf:
            vgdf = vgdf.query('edge_mid == "edge"')

    hyai = xr.DataArray(vgdf['A'], dims=('ILAY',))
    hybi = xr.DataArray(vgdf['B'], dims=('ILAY',))
    hyam = (hyai.data[1:] + hyai.data[:-1]) / 2
    hyam = xr.DataArray(hyam, dims=('LAY',))
    hybm = (hybi.data[1:] + hybi.data[:-1]) / 2
    hybm = xr.DataArray(hybm, dims=('LAY',))
    outf = xr.Dataset()
    outf['hybi'] = hybi
    outf['hyai'] = hyai
    outf['hybm'] = hybm
    outf['hyam'] = hyam
    return outf


def getmetaf(GDNAM, VGNAM, gdpath=None, vgpath=None, FTYPE=2, p0=1e5):
    import numpy as np
    gdf = getllf(GDNAM, gdpath=gdpath, FTYPE=FTYPE)
    vgf = gethybf(VGNAM, vgpath)
    gdf['hybm'] = vgf['hybm']
    gdf['hyam'] = vgf['hyam']
    p = vgf['hyai'] + vgf['hybi'] * p0
    pt = p.min()
    gdf.attrs['VGLVLS'] = np.asarray((p - pt) / (p0 - pt), dtype='f')
    gdf.attrs['VGTOP'] = np.asarray(pt, dtype='f')
    gdf.attrs['GDNAM'] = GDNAM.ljust(16)
    gdf.attrs['VGNAM'] = VGNAM.ljust(16)
    return gdf
