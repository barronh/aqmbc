__all__ = ['dims', 'getmetaf']

import numpy as np

_vglv35 = (1., 0.9975, 0.995, 0.99, 0.985, 0.98, 0.97, 0.96, 0.95, 0.94,
           0.93, 0.92, 0.91, 0.9, 0.88, 0.86, 0.84, 0.82, 0.8, 0.77,
           0.74, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3,
           0.25, 0.2, 0.15, 0.1, 0.05, 0.)
_vglv44 = (1., 0.9975, 0.9946, 0.9913, 0.9875, 0.9831, 0.9781, 0.9723, 0.9657,
           0.958, 0.9492, 0.9391, 0.9275, 0.9141, 0.8987, 0.881, 0.8607,
           0.8373, 0.8104, 0.7795, 0.7439, 0.7066, 0.6693, 0.632, 0.5946,
           0.5573, 0.52, 0.4827, 0.4454, 0.4081, 0.3708, 0.3352, 0.3013,
           0.269, 0.2383, 0.2089, 0.181, 0.1543, 0.1289, 0.1047, 0.0816,
           0.0596, 0.0386, 0.0186, 0.)
vglvls = {
    'EPA_35L': np.asarray(_vglv35, dtype='f'),
    'EPA_44L': np.asarray(_vglv44, dtype='f'),
}

dims = {
    'gc': {'TSTEP': 'time', 'LAY': 'lev', 'ROW': 'lat', 'COL': 'lon'},
    'raqms': {'TSTEP': 'time', 'LAY': 'lev', 'ROW': 'lat', 'COL': 'lon'},
    'waccm': {'TSTEP': 'time', 'LAY': 'lev', 'ROW': 'lat', 'COL': 'lon'},
    'tcr': {'TSTEP': 'time', 'LAY': 'lev', 'ROW': 'lat', 'COL': 'lon'},
}


def getmetaf(bctype='bcon', gdnam='12US1', vgnam='EPA_35L', gdpath=None):
    """
    bctype : str
        bcon (boundary) or icon (initial) boundary conditions.
    gdnam : str
        Name of grid in gdpath
    vgnam : str
        Name of vertical grid (must exist in vglvls)
    gdpath : str or None
        If none, looks for GRIDDESC environment, then looks for a local file,
        then uses the default.
    """
    from os import environ
    from os.path import dirname, join, exists
    import PseudoNetCDF as pnc

    if gdpath is None:
        gdpath = environ.get('GRIDDESC', None)
    if gdpath is None:
        if exists('GRIDDESC'):
            gdpath = 'GRIDDESC'
    if gdpath is None:
        # redefining here because reusing from . would be recursive.
        gdpath = join(dirname(__file__), 'examples', 'GRIDDESC')

    if bctype == 'bcon':
        FTYPE = 2
    elif bctype == 'icon':
        FTYPE = 1
    else:
        raise KeyError(f'bctype must be either bcon or icon; got {bctype}')

    VGLVLS = vglvls[vgnam]
    metaf = pnc.pncopen(
        gdpath, format='griddesc', FTYPE=FTYPE, GDNAM=gdnam, VGLVLS=VGLVLS,
        SDATE=1970001
    )
    return metaf
