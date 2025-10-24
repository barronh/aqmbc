__all__ = ['dims', 'getmetaf', 'vgopts', 'sig2hyb', 'addhyb']

import numpy as np
from ._vertgrid import vgopts, sig2hyb
dims = {
    'gc': {'TSTEP': 'time', 'LAY': 'lev', 'ROW': 'lat', 'COL': 'lon'},
    'cf': {'TSTEP': 'time', 'LAY': 'lev', 'ROW': 'lat', 'COL': 'lon'},
    'raqms': {'TSTEP': 'time', 'LAY': 'lev', 'ROW': 'lat', 'COL': 'lon'},
    'waccm': {'TSTEP': 'time', 'LAY': 'lev', 'ROW': 'lat', 'COL': 'lon'},
    'tcr': {'TSTEP': 'time', 'LAY': 'lev', 'ROW': 'lat', 'COL': 'lon'},
}
pmid = {
    'gc': 'Met_PMID',
    'cf': 'pmid',
    'raqms': 'pdash',
    'wacmm': '?',
    'tcr': '?'
}


def getmetaf(
    bctype='bcon', gdnam='12US1', vgnam='EPA_35L', gdpath=None,
    vglvls=None, vgtop=None, vgtyp=None
):
    """
    Arguments
    ---------
    bctype : str
        bcon (boundary) or icon (initial) boundary conditions.
    gdnam : str
        Name of grid in gdpath
    vgnam : str
        Name of vertical grid (must exist in vglvls). If unknown coordinate,
        provide an array of sigma levels (e.g, 1, ..., 0)
    gdpath : str or None
        If none, looks for GRIDDESC environment, then looks for a local file,
        then uses the default.
    vgtop : float
        Vertical grid top in Pascals
    vgtyp : float
        This should normally be one of the known vertical grid types
        7: WRF terrain following,
        -9999: WRF hybrid terrain following and constant pressure,
        -9999: GFS hybrid terrain following and constant pressure

    Returns
    -------
    metaf : PseudoNetCDF.PseudoNetCDFFile
        File with metadata associated with grid
    """
    from os import environ
    from os.path import dirname, join, exists
    import PseudoNetCDF as pnc
    import warnings
    import copy

    if gdpath is None:
        gdpath = environ.get('GRIDDESC', None)
    if gdpath is None:
        if exists('GRIDDESC'):
            gdpath = 'GRIDDESC'
    if gdpath is None:
        # redefining here because reusing from . would be recursive.
        gdpath = join(dirname(dirname(__file__)), 'examples', 'GRIDDESC')

    if bctype == 'bcon':
        FTYPE = 2
    elif bctype == 'icon':
        FTYPE = 1
    else:
        raise KeyError(f'bctype must be either bcon or icon; got {bctype}')

    if isinstance(vgnam, str):
        vgopt = vgopts[vgnam]
        vgnam = vgopt
        if not (vglvls is None and vgtyp is None and vgtop is None):
            warnings.warn('vgnam supersedes vglvls, vgtop, and vgtyp')

    if isinstance(vgnam, dict):
        vgopt = copy.deepcopy(vgnam)
    else:
        if vglvls is None or vgtyp is None or vgtop is None:
            emsg = 'If no vgnam provided, requires vglvls, vgtop and vgtyp.'
            emsg = f'Got vglvls={vglvls}, vgtop={vgtop} and vgtyp={vgtyp}'
            raise ValueError(emsg)

        vgopt = {
            'VGLVLS': np.asarray(vglvls, dtype='f'),
            'VGTOP': np.asarray(vgtop, dtype='f'),
            'VGTYP': np.asarray(vgtyp, dtype='i'),
        }
    openopts = {k: vgopt[k] for k in 'VGLVLS VGTOP VGTYP'.split()}
    hyopts = {k: vgopt[k] for k in vgopt if k.startswith('hy')}
    metaf = pnc.pncopen(
        gdpath, format='griddesc', FTYPE=FTYPE, GDNAM=gdnam,
        SDATE=1970001, **openopts
    )
    addhyb(metaf, hyc=hyopts)

    return metaf


def addhyb(f, hyc=None, r=0.2, p0=1e5, zdim='LAY', zedim='ILAY'):
    """
    Add mid-level and interface-level hybrid coordiantes as attributes.
    If VGTYP == -9999, hya/hyb are calculated from sig2hyb using
    s=f.VGLVLS and pt=f.PTOP. If VGTYP==7, a=vglvls and
    b=ptop - vglvls * ptop. r and p0 can be provided as keywords
    and will be passed to sig2hyb.
    """
    import warnings
    if hyc is None:
        VGLVLS = f.VGLVLS
        MIDVGLVLS = VGLVLS[1:] + VGLVLS[:-1]
        if f.VGTYP == -9999:
            hyi = sig2hyb(VGLVLS, pt=f.VGTOP, r=r, p0=p0)
            hym = sig2hyb(MIDVGLVLS, pt=f.VGTOP, r=r, p0=p0)
            hyc = {
                'hyai': hyi['hya'], 'hybi': hyi['hyb'],
                'hyam': hym['hya'], 'hybm': hym['hyb'],
            }
        elif f.VGTYP == 7:
            warnings.warn('Using old VGTYP')
            hyai = f.VGTOP * (1 - VGLVLS)
            hyam = f.VGTOP * (1 - MIDVGLVLS)
            hyc = dict(
                hyai=hyai, hybi=VGLVLS,
                hyam=hyam, hybm=MIDVGLVLS
            )
        else:
            emsg = f'Unknown VGTYP={f.VGTYP}; expected -9999 or 7'
            raise ValueError(emsg)

    varopts = {
        'hyai': dict(units='Pa', var_desc='constant pressure edge component'),
        'hybi': dict(units='1', var_desc='terrain following edge component'),
        'hyam': dict(units='Pa', var_desc='constant pressure mid component'),
        'hybm': dict(units='1', var_desc='terrain following mid component'),
    }
    for hk, hv in hyc.items():
        if hk.endswith('i'):
            if zedim not in f.dimensions:
                f.createDimension(zedim, hv.size)
            dims = (zedim,)
        else:
            dims = (zdim,)
        varo = f.createVariable(hk, 'f', dims)
        var_desc = varopts[hk]['var_desc'] + ' (p=a+b*ps)'
        units = varopts[hk]['units']
        varo.setncatts(dict(
            long_name=hk.ljust(16), var_desc=var_desc.ljust(80),
            units=units.ljust(16)
        ))
        varo[:] = hv
