__all__ = ['zinterp']


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
    import xarray as xr
    import numpy as np
    from PseudoNetCDF.coordutil import getinterpweights

    nzout = destz.shape[1]
    itershape = srcz[:, 0].shape
    wgtshape = list(srcz.shape)
    wgtshape.insert(2, nzout)
    wgtv = np.zeros(wgtshape, dtype='f')
    if verbose > 0:
        print('INFO:: zinterp building matrix')
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

    zweight = wgtv[:] * srcz.data[:, :, None, ...]
    znorm = zweight.sum(1)
    exprkeys = [
        key for key, var in srcf.variables.items()
        if var.shape == srcz.shape
    ]
    outdims = list(srcf[exprkeys[0]].dims)
    outdims[1] = destz.dims[1]
    outf = xr.Dataset()
    outf.attrs.update(srcf.attrs)
    if verbose > 0:
        print('INFO:: zinterp inteprolating.')

    for key in exprkeys:
        if verbose > 1:
            print(f'INFO:: zinterp inteprolating {key}.')
        invar = srcf[key]
        props = {k: v for k, v in invar.attrs.items()}
        outvar = (
            invar.data[:, :, None, ...] * zweight
        ).sum(1) / znorm
        outf[key] = outdims, outvar
        outf[key].attrs.update(props)
    for k in outf.dims:
        if k in srcf.coords:
            sc = srcf.coords[k]
            if sc.size == outf.sizes[k]:
                outf.coords[k] = srcf.coords[k]
    return outf
