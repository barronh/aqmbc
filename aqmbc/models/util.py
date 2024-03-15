__all__ = ['sigma2coeff_lin']


def sigma2coeff_lin(sigma, vglvls):
    """
    Calculate weighting coefficients for each source (S) layer to each
    destination (D) layer using a simple piecewise linear interpolation.

    Arguments
    ---------
    sigma : array-like
        Source model edges defined as sigma = (p - ptop) / (psrf / ptop)
    vglvls : array-like
        CMAQ model edges defined as sigma = (p - ptop) / (psrf / ptop)

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
