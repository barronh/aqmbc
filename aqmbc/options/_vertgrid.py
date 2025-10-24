__all__ = ['sig2hyb', 'vgopts']

import numpy as np


def sig2hyb(s, r=0.2, p0=1000e2, pt=50e2):
    """
    Convert sigma coordinate to terrain-following (B) and pressure (A)
    components of a hybrid WRF coordinate. From CMAQ, s=VGLVLS and pt=VGTOP.
    The standard r=0.2 and p0=1000e2.

    This is just a rearrangement of Eq 1 in doi: 10.1175/MWR-D-18-0334.1

    Arguments
    ---------
    s : array-like
        Sigma coordinates defined as (p - pt) / (ps - pt)
    r : float
        Sigma coordinate at which B component is 0
    p0 : float
        Reference coordinate to use a ps in blend
    pt : float
        Pressure at the top of sigma coordinate

    Returns
    -------
    coords : dict
        contains the hybrid pressure (A=hya) and hybrid terrain-following
        (hyb=B) coordinates. This allows for a transformation from one
        coordinate to another. P = hya + hyb * ps
    """
    c1 = 2. * r**2 / (1 - r)**3
    c2 = -r * (4. + r + r**2) / (1 - r)**3
    c3 = 2 * (1. + r + r**2) / (1 - r)**3
    c4 = -(1 + r) / (1 - r)**3
    B = c1 + c2 * s + c3 * s**2 + c4 * s**3
    B = np.where(s >= 1, 1, B)
    B = np.where(s <= r, 0, B)
    A = (s - B) * (p0 - pt) + pt - B * pt
    return dict(hya=A, hyb=B)


_vglv35 = np.asarray([
    1., 0.9975, 0.995, 0.99, 0.985, 0.98, 0.97, 0.96, 0.95, 0.94,
    0.93, 0.92, 0.91, 0.9, 0.88, 0.86, 0.84, 0.82, 0.8, 0.77,
    0.74, 0.7, 0.65, 0.6, 0.55, 0.5, 0.45, 0.4, 0.35, 0.3,
    0.25, 0.2, 0.15, 0.1, 0.05, 0.
], dtype='f')
_vglv44 = np.asarray([
    1., 0.9975, 0.9946, 0.9913, 0.9875, 0.9831, 0.9781, 0.9723, 0.9657,
    0.958, 0.9492, 0.9391, 0.9275, 0.9141, 0.8987, 0.881, 0.8607,
    0.8373, 0.8104, 0.7795, 0.7439, 0.7066, 0.6693, 0.632, 0.5946,
    0.5573, 0.52, 0.4827, 0.4454, 0.4081, 0.3708, 0.3352, 0.3013,
    0.269, 0.2383, 0.2089, 0.181, 0.1543, 0.1289, 0.1047, 0.0816,
    0.0596, 0.0386, 0.0186, 0.
], dtype='f')


vgopts = {
    'WRF_TERRAIN_35L': dict(VGTOP=5e3, VGTYP=7, VGLVLS=_vglv35.copy()),
    'WRF_TERRAIN_44L': dict(VGTOP=5e3, VGTYP=7, VGLVLS=_vglv44.copy()),
    'WRF_HYBRID_35L': dict(VGTOP=5e3, VGTYP=-9999, VGLVLS=_vglv35.copy()),
    'WRF_HYBRID_44L': dict(VGTOP=5e3, VGTYP=-9999, VGLVLS=_vglv44.copy()),
    'EMBER_35L': dict(VGTOP=0.999, VGTYP=-9999, VGLVLS=_vglv35.copy()),
}

# Add hyb and hya
for vkey, vopt in vgopts.items():
    pt = vopt['VGTOP']
    edge = vopt['VGLVLS']
    mid = (edge[1:] + edge[:-1]) / 2
    if vopt['VGTYP'] == -9999:
        hyi = sig2hyb(edge, r=0.2, p0=1e5, pt=pt)
        hym = sig2hyb(mid, r=0.2, p0=1e5, pt=pt)
        vopt['hybi'] = hyi['hyb']
        vopt['hyai'] = hyi['hya']
        vopt['hybm'] = hym['hyb']
        vopt['hyam'] = hym['hya']
    elif vopt['VGTYP'] == 7:
        vopt['hybi'] = edge
        vopt['hyai'] = pt - edge * pt
        vopt['hybm'] = mid
        vopt['hyam'] = pt - mid * pt

embopt = vgopts['EMBER_35L']
embopt.update(dict(
    hyai=np.array([
        0., 0., 0., 0.17594, 1.1941, 3.7361, 19.757, 57.571, 121.1, 211.07,
        325.9, 464.69, 625.75, 807.51, 1223.6, 1704.5, 2236.9, 2812.4, 3424,
        4396, 5415.5, 6823.3, 8617.7, 10401, 12123, 13730, 15164, 16352,
        17204, 17576, 17294, 16066, 13672, 9885.6, 5000.9, 0.999
    ], dtype='f'),
    hybi=np.array([
        1, 0.9975, 0.995, 0.99, 0.98499, 0.97996, 0.9698, 0.95942, 0.94879,
        0.93789, 0.92674, 0.91535, 0.90374, 0.89193, 0.86777, 0.84296, 0.81763,
        0.79188, 0.76576, 0.72604, 0.68585, 0.63177, 0.56383, 0.49599, 0.42878,
        0.36271, 0.29837, 0.23648, 0.17797, 0.12425, 0.077071, 0.039351,
        0.013293, 0.0011529, 0., 0.
    ], dtype='f'),
))
_vedg = embopt['VGLVLS']
_vmid = (_vedg[1:] + _vedg[:-1]) / 2
embopt['hyam'] = np.interp(_vmid, _vedg[::-1], embopt['hyai'][::-1])
embopt['hybm'] = np.interp(_vmid, _vedg[::-1], embopt['hybi'][::-1])

vgopts['EPA_35L'] = vgopts['WRF_HYBRID_35L']
vgopts['EPA_44L'] = vgopts['WRF_HYBRID_44L']
