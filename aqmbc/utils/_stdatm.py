def getstdatm(hyam, hybm, p0=1e5, refv=None):
    import xarray as xr
    from scipy.interpolate import interp1d
    import numpy as np
    stdp = np.array([
        0.01, 0.05, 0.22, 0.8, 2.87, 11.97, 25.49, 55.29, 121.1, 265.0, 308.0,
        356.5, 411.1, 472.2, 540.5, 616.6, 701.2, 795.0, 898.8, 1013.0, 1139.0
    ]) * 100.  # [Pa]
    stdt = np.array([
        198.64, 219.58, 247.02, 270.65, 250.35, 226.51, 221.55, 216.65, 216.65,
        223.25, 229.73, 236.21, 242.7, 249.19, 255.68, 262.17, 268.66, 275.15,
        281.65, 288.15, 294.65
    ])  # [K]
    pmid = hyam + hybm * p0
    temp = interp1d(stdp, stdt)(pmid)
    if refv is not None:
        pmid = (refv * 0).fillna(0) + pmid
        temp = (refv * 0).fillna(0) + temp
    outf = xr.Dataset()
    outf['pmid'] = pmid
    outf['pmid'].attrs.update(units='Pa', long_name='pressure layer-mid')
    outf['tmid'] = temp
    outf['tmid'].attrs.update(units='K', long_name='air temperature layer-mid')
    return outf
