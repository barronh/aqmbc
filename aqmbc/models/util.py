__all__ = ['sigma2coeff_lin']


def sigma2coeff_lin(sigma, vglvls):
    """
    Calculate weighting coefficients for each source (S) layer to each
    destination (D) layer using a simple piecewise linear interpolation.

    Arguments
    ---------
    sigma : array-like
        Source model edges defined as sigma = (p - ptop) / (psrf - ptop)
    vglvls : array-like
        CMAQ model edges defined as sigma = (p - ptop) / (psrf - ptop)

    Returns
    -------
    coeff : array
        Weights shaped (S,D) of each source (S) layer to each destination (D)
        layer. The sum of coeff over the S (0) axes should be an array of shape
        D with all values set to 1.

    Notes
    -----
    * Both sigma and vglvls are expected in descending order (1 to 0)
    * Both sigma and vglvls must be use the same ptop and psrf
    """
    import numpy as np
    sigma = np.asarray(sigma)
    vglvls = np.asarray(vglvls)
    cvglvls = (vglvls[1:] + vglvls[:-1]) / 2
    csigma = (sigma[1:] + sigma[:-1]) / 2
    nzs = csigma.size
    nzd = cvglvls.size
    lwgt = np.zeros((nzs, nzd), dtype='f')
    lfs = np.interp(cvglvls, csigma[::-1], np.arange(nzs)[::-1])
    for li in range(cvglvls.size):
        lf = lfs[li]
        lli = int(lf)
        lui = lli + 1
        luw = lf - lli
        llw = 1 - luw
        lwgt[lli, li] = llw
        if luw > 0:
            lwgt[lui, li] = luw

    return lwgt


def pres2vglvl(p, pt=None, ps=None):
    """
    Convert pressures to terrain-following coordinates.

    Arguments
    ---------
    p : array-like
        Pressure typically in Pa, but must match units of pt and ps
    pt : float
        Vertical grid top typically in Pa, but must match units of p
        If None, defaults to the minimum pressure in p which assumes p are
        edge pressures and complete.
    ps : float
        Surface pressure typically in Pa, but must match units of p.
        If None, defaults to the maximum pressure in p which assumes p are
        edge pressures and complete.

    Returns
    -------
    vglvls :
        vglvl = (p - pt) / (ps - pt)
    """
    import numpy as np
    if pt is None:
        pt = np.min(p)
    if ps is None:
        ps = np.max(p)

    vglvls = (p - pt) / (ps - pt)
    return vglvls


def vglvls2ab(VGLVLS, VGTOP=5e3, p0=1e5, r=0.2, ltype='edge', add_mid=False):
    """
    This utility will read an MCIP 3D file (or CMAQ 3D) and output the hybrid
    coordinate edges and mids in p = B x ps + A where ps is the surface
    pressure in Pa, A is the constant pressure component in Pa, and B is the
    terrain-following component as a fraction.

    This is a rearrangement of Park et al.[1] equation 1.

    P = B(h) * (ps - pt)      + [h - B(h)](p0 - pt) + pt
      = B(h) * ps - B(h) * pt + [h - B(h)](p0 - pt) + pt
      = B(h) * ps + A

    [1] https://doi.org/10.1175/MWR-D-18-0334.1

    Arguments
    ---------
    VGLVLS : array-like
        Vertical grid levels (typically edges, but can be mids)
    VGTOP : float
        Top of the model in pressure (default 5000 Pa)
    p0 : float
        Reference pressure used in WRF grid definition (default: 100000 Pa)
    r : float
        Eta level at which B = 0
    ltype : str
        Edge type ("edge" or "mid")
    add_mid : bool
        If add_mid and etype == "edge", the add the mid layers based on
        interpolation.

    Returns
    -------
    out : dict
        Dictionary with VGLVLS, VGTOP, p0, r, A, B, and edge_mid:
        - VGLVLS : sigma coordinates used to calculate A/B
        - A : Constant pressure component of vertical coordinate [Pa]
        - B : Terrain following component of vertical coordinate [1]
        - edge_mid : "edge" or "mid"
    """
    import numpy as np
    # r = eta_c in https://doi.org/10.1175/MWR-D-18-0334.1
    hi = np.asarray(VGLVLS, dtype='d')  # at interfaces
    if add_mid and ltype == 'edge':
        hm = (hi[1:] + hi[:-1]) / 2  # mid-levels
        h = np.zeros(hi.size + hm.size, dtype='d')
        h[::2] = hi
        h[1::2] = hm
        etype = (['edge', 'mid'] * hi.size)[:-1]
    else:
        h = hi
        etype = [ltype] * hi.size

    c1 = 2. * r**2 / (1 - r)**3
    c2 = -r * (4. + r + r**2) / (1 - r)**3
    c3 = 2 * (1. + r + r**2) / (1 - r)**3
    c4 = -(1 + r) / (1 - r)**3
    B = c1 + c2 * h + c3 * h**2 + c4 * h**3
    B = np.where(h >= 1, 1, B)
    B = np.where(h <= r, 0, B)
    A = (h - B) * (p0 - VGTOP) + VGTOP - B * VGTOP
    out = dict(
        VGLVLS=h, A=A, B=B, edge_mid=etype,
        VGTOP=VGTOP, p0=p0, r=r,
    )
    return out


def zinterp(srcf, srcz, destz, interptype='linear', verbose=0):
    """
    Arguments
    ---------
    srcf : PseudoNetCDFFile
        Must have variables with the same dimensions as srcz
    srcz : PseudoNetCDFVariable
        n-dimensional z coordinate with the z-dimension in the second position
        (e.g., time, lev, ...).
    destz : PseudoNetCDFVariable
        Must have the same units as srcz, and have the same shape as srcz
        except for the z-dimension, which can vary.
    interptype : str
        Must be accepted by getinterpweights, which uses scipy.interpolate
        interp1d
    verbose : int
        Level of verbosity

    Returns
    -------
    outf : PseudoNetCDFFile
        File interpolated vertically to destz
    """
    import numpy as np
    import PseudoNetCDF as pnc
    from PseudoNetCDF.coordutil import getinterpweights

    nzout = destz.shape[1]
    itershape = srcz[:, 0].shape
    wgtshape = list(srcz.shape)
    wgtshape.insert(2, nzout)
    wgtv = np.zeros(wgtshape, dtype='f')
    for idx in np.ndindex(*itershape):
        widx = (idx[0], slice(None), slice(None)) + tuple(idx[1:])
        zidx = (idx[0], slice(None)) + tuple(idx[1:])
        # Tested many alternative approaches... converting to pressure using
        # A/B coordinates
        tox = np.ma.filled(destz[zidx])
        fromx = np.ma.filled(srcz[zidx])
        wgtv[widx] = getinterpweights(
            fromx, tox, kind=interptype, fill_value='extrapolate',
            extrapolate=False
        )

    zweight = wgtv[:] * srcz[:, :, None, ...]
    znorm = zweight.sum(1)
    exprkeys = [
        key for key, var in srcf.variables.items()
        if var.shape == srcz.shape
    ]
    outdims = srcf.variables[exprkeys[0]].dimensions
    outf = pnc.PseudoNetCDFFile()
    levkey = srcz.dimensions[1]
    for k, d in srcf.dimensions.items():
        if k == levkey:
            outf.createDimension(k, nzout)
        else:
            outf.createDimension(k, len(d))
    for k in srcf.ncattrs():
        outf.setncattr(k, srcf.getncattr(k))
    for key in exprkeys:
        invar = srcf.variables[key]
        typecode = invar.dtype.char
        props = {
            k: invar.getncattr(k)
            for k in invar.ncattrs()
        }
        outvar = outf.createVariable(key, typecode, outdims, **props)
        outvar[:] = (
            invar[:][:, :, None, ...] * zweight
        ).sum(1) / znorm
    excludekeys = exprkeys + list(srcf.dimensions)
    excludekeys += ['hybi', 'hyai', 'hybm', 'hyam']
    for key, var in srcf.variables.items():
        if key not in excludekeys:
            outf.copyVariable(var, key=key)

    return outf


def hybinterp(
    srcf, destf, ps=None, interptype='linear', verbose=0
):
    """
    Generalized Vertical Interpolation

    Arguments
    ---------
    srcf : netcdf-like
        Must have hyam [hPa or Pa] and hybm [1] and variables with dims
        ('time', 'lev', ...) where ... is often lat/lon, ROW/COl, or PERIM
    destf : netcdf-like
        Must have hyam [hPa or Pa] and hybm [1]
    ps : array
        Must have dims ('time', ...) where ... is often lat/lon, ROW/COl, or
        PERIM and units must be Pa

    Returns
    -------
    outf : PseudoNetCDFFile
        Interpolated file to new LAY structure.
    """
    import PseudoNetCDF as pnc
    import numpy as np
    import warnings
    from ..options import addhyb
    srcAB = all([vk in srcf.variables for vk in 'hybm hyam'.split()])
    destAB = all([vk in destf.variables for vk in 'hybm hyam'.split()])
    if not destAB:
        destf = destf.copy()
        addhyb(destf)
        destAB = True

    if ps is None or not srcAB or not destAB:
        wmsg = ''
        if not srcAB:
            wmsg += 'Source does not have hyam or hybm. '
        if not destAB:
            wmsg += 'Destination does not have hyam or hybm. '
        if ps is None:
            wmsg += 'Surface pressure (ps) is None.'
        warnings.warn(wmsg)
        return srcf.interpSigma(
            vglvls=destf.VGLVLS, vgtop=destf.VGTOP, interptype=interptype
        )
    srcA = srcf.variables['hyam'][:]
    srcB = srcf.variables['hybm'][:]
    srcAunit = srcf.variables['hyam'].units.strip().lower()
    if srcAunit == 'hpa':
        srcA = srcA * 100
    elif not srcAunit == 'pa':
        raise ValueError(f'Expected pa or hpa; got {srcAunit}')

    destA = destf.variables['hyam'][:]
    destB = destf.variables['hybm'][:]
    destAunit = destf.variables['hyam'].units.strip().lower()
    if destAunit == 'hpa':
        destA = destA * 100
    elif not destAunit == 'pa':
        raise ValueError(f'Expected pa or hpa; got {destAunit}')

    sdi = list(range(1, ps.ndim))
    pdims = list(ps.dimensions)
    pdims.insert(1, srcA.dimensions[0])
    srcpmid = (
        ps[:, None] * np.expand_dims(srcB, sdi) + np.expand_dims(srcA, sdi)
    )
    srcpmid = pnc.PseudoNetCDFVariable(
        None, 'pmid', 'f', tuple(pdims), values=srcpmid
    )
    pdims = list(ps.dimensions)
    pdims.insert(1, destA.dimensions[0])
    destpmid = (
        ps[:, None] * np.expand_dims(destB, sdi) + np.expand_dims(destA, sdi)
    )
    destpmid = pnc.PseudoNetCDFVariable(
        None, 'pmid', 'f', tuple(pdims), values=destpmid
    )
    outf = zinterp(srcf, srcpmid, destpmid)
    outf.setncattr('VGLVLS', destf.VGLVLS)
    outf.setncattr('VGTOP', destf.VGTOP)
    outf.setncattr('VGTYP', destf.VGTYP)
    return outf
