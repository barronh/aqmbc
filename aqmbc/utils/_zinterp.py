__all__ = ['zinterp']


def _getinterpweights(
    xs, nxs, kind='linear', fill_value='extrapolate', extrapolate=False
):
    """
    Get weights for interpolation by matrix multiplication

    Parameters
    ----------
    xs : old input coordinates
    nxs : new output coordinates
    extrapolate : allow extrapolation beyond bounds, default False
    fill_value : set fill value (e.g, nan) to prevent extrapolation or edge
                 continuation

    Returns
    -------
    weights : numpy array shape = (old, new)

    Notes
    -----
    When extrapolate is false, the edge values are used for points beyond
    the inputs. Particularly useful when reusing weights to interpolate
    many variables. Copied from PseudoNetCDF 2025-10-29

    Example
    -------
    xs = np.arange(10, 100, 10)
    ys = xs
    nxs = np.arange(0, 100, 5)
    weights = _getinterpweights(a, b)
    nys = (weights * xs[:, None]).sum(0)

    """
    from scipy.interpolate import interp1d
    import numpy as np
    # identity matrix
    ident = np.identity(xs.size)
    # weight function; use bounds outside
    weight_func = interp1d(xs, ident, axis=-1, kind='linear',
                           bounds_error=False, fill_value='extrapolate')
    # calculate weights, which can be reused
    weights = weight_func(nxs)

    # If not extrapolating, force weights to
    # no more than one at the edges
    if not extrapolate:
        weights = np.maximum(0, weights)
        weights /= weights.sum(0)
    return weights


def zinterp(srcf, srcz, destz, interptype='linear', verbose=0):
    """
    Arguments
    ---------
    srcf : xarray.DataArray
        Must have variables with the same dimensions as srcz
    srcz : xarray.DataArray
        n-dimensional z coordinate with the z-dimension in the second position
        (e.g., time, lev, ...).
    destz : xarray.DataArray
        Must have the same units as srcz, and have the same shape as srcz
        except for the z-dimension, which can vary.
    interptype : str
        Must be accepted by _getinterpweights, which uses scipy.interpolate
        interp1d
    verbose : int
        Level of verbosity

    Returns
    -------
    outf : xarray.Dataset
        File interpolated vertically to destz
    """
    import xarray as xr
    import numpy as np

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
        wgtv[widx] = _getinterpweights(
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
