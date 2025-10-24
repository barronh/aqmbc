def vglvls2wrfab(s, r=0.2, p0=1000e2, pt=50e2):
    """
    Convert sigma coordinate to terrain-following (B) and pressure (A)
    components of a hybrid WRF coordinate. From CMAQ, s=VGLVLS and pt=VGTOP.
    The standard r=0.2 and p0=1000e2.

    This is just a rearrangement of Eq 1 in doi: 10.1175/MWR-D-18-0334.1

    If r is None, use the non-hybrid option instead.

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
    import numpy as np
    if r is None:
        return dict(hyb=s, hya=pt - s * pt)

    c1 = 2. * r**2 / (1 - r)**3
    c2 = -r * (4. + r + r**2) / (1 - r)**3
    c3 = 2 * (1. + r + r**2) / (1 - r)**3
    c4 = -(1 + r) / (1 - r)**3
    B = c1 + c2 * s + c3 * s**2 + c4 * s**3
    B = np.where(s >= 1, 1, B)
    B = np.where(s <= r, 0, B)
    A = (s - B) * (p0 - pt) + pt - B * pt
    return dict(hya=A, hyb=B)
