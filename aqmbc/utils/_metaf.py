__all__ = ['gethybf', 'getllf', 'getmetaf']


def getllf(GDNAM, gdpath=None, FTYPE=2):
    import numpy as np
    import pandas as pd
    import xarray as xr
    import pyproj
    from ._cmaq import open_griddesc
    if isinstance(FTYPE, str):
        FTYPE = {'bcon': 2, 'icon': 1}
    if gdpath is None:
        from os.path import join, exists
        from ..data import dataroot
        gdpath1 = 'GRIDDESC.csv'
        gdpath2 = join(dataroot, 'GRIDDESC.csv')
        if exists(gdpath1):
            gdpath = gdpath1
        elif exists(gdpath2):
            gdpath = gdpath2
        else:
            raise IOError(f'{gdpath1} or {gdpath2} must exist.')
    dtypes = dict(
        GDNAM=str, GDTYP=int, P_ALP=float, P_BET=float, P_GAM=float,
        XCENT=float, YCENT=float, XORIG=float, YORIG=float,
        XCELL=float, YCELL=float, NCOLS=int, NROWS=int, NTHIK=int,
    )
    gdf = pd.read_csv(gdpath, dtype=dtypes)
    for attrs in gdf.to_dict('records'):
        if attrs['GDNAM'] == GDNAM:
            break
    else:
        raise KeyError(f'GDNAM {GDNAM} not found; {gdf["GDNAM"]}')
    attrs['FTYPE'] = FTYPE
    outf = open_griddesc(attrs)
    proj = pyproj.Proj(outf.crs_proj4)
    nr = outf.NROWS
    nc = outf.NCOLS
    try:
        if FTYPE == 1:
            outf.coords['ROW'] = np.arange(nr) + 0.5
            outf.coords['COL'] = np.arange(nc) + 0.5
            row, col = xr.broadcast(outf.ROW, outf.COL)
            lon, lat = proj(col, row)
            outf['lat'] = ('ROW', 'COL'), lat, dict(units='degrees_north')
            outf['lon'] = ('ROW', 'COL'), lon, dict(units='degrees_east')
        elif FTYPE == 2:
            row = np.concatenate([
                np.zeros(nc + 1, dtype='d') - 0.5,
                np.arange(nr + 1, dtype='d') + 0.5,
                np.zeros(nc + 1, dtype='d') + nr + 0.5,
                np.arange(-1, nr, dtype='d') + 0.5,
            ])
            col = np.concatenate([
                np.arange(nc + 1, dtype='d') + 0.5,
                np.zeros(nr + 1, dtype='d') + nc + 0.5,
                np.arange(-1, nc, dtype='d') + 0.5,
                np.zeros(nr + 1) - 0.5
            ])
            nperim = col.size
            assert nperim == ((nr + 1 + nc + 1) * 2)
            outf.coords['PERIM'] = np.arange(nperim)
            lon, lat = proj(col, row)
            outf['lat'] = ('PERIM',), lat, dict(units='degrees_north')
            outf['lon'] = ('PERIM',), lon, dict(units='degrees_east')
        else:
            raise KeyError(f'FTYPE must be 1 or 2; got {FTYPE}')
    except IOError as e:
        raise IOError(f'Unable to read {GDNAM} from {gdpath}; {str(e)}')

    return outf


def gethybf(VGNAM, vgpath=None, vgdf=None):
    import xarray as xr
    import pandas as pd
    if vgdf is None:
        if vgpath is None:
            from os.path import join, exists
            from ..data import vertgridroot
            vgpath1 = f'{VGNAM}.csv'
            vgpath2 = join(vertgridroot, f'{VGNAM}.csv')
            if exists(vgpath1):
                vgpath = vgpath1
            elif exists(vgpath2):
                vgpath = vgpath2
            else:
                raise IOError(f'{vgpath1} or {vgpath2} must exist')
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
