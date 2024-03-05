__all__ = ['download', 'raqms']
import PseudoNetCDF as pnc


def download(dates, root=None):
    """
    Convenience function for downloading. If root url change

    dates : list
        Dates to download
    root : str
        Root path where RAQMS files are available for downloading.
        If None, defaults to https://bin.ssec.wisc.edu/pub/raqms/ESRL/RAQMS/
        If the root path has changed, provide a new value here and raise an
        issue at  https://github.com/barronh/aqmbc/issues

    Returns
    -------
    paths : list
        List of paths that were downloaded
    """
    import pandas as pd
    import requests
    from os.path import basename, join, exists

    if root is None:
        root = 'https://bin.ssec.wisc.edu/pub/raqms/ESRL/RAQMS/'

    destpaths = []
    for date in pd.to_datetime(dates):
        url = date.strftime(f'{root}/uwhyb_%m_%d_%Y_%HZ.chem.assim.nc')
        dest = join('RAQMS', basename(url))
        if not exists(dest):
            with requests.get(url, stream=True) as r:
                total_size = int(r.headers.get("content-length", 0))
                if total_size == 0:
                    total_size = 1024**3
                print('total_size (MB):', total_size / 1024**2)
                print('Each . represents 1/80th')
                block_size = 1024 * 1024
                r_size = 0
                r.raise_for_status()
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=block_size):
                        f.write(chunk)
                        r_size += len(chunk)
                        print(f'\r{int(r_size / total_size * 80)*"."}', end='')
                    print()
        else:
            print(f'Using cached {dest}')

        destpaths.append(dest)

    return destpaths


class raqms(pnc.PseudoNetCDFFile):
    def __init__(self, *args, **kwds):
        """
        Thin wrapper around raqms files to add ll2ij, getTimes, and
        interpSigma functions.
        """
        f = pnc.pncopen(*args, **kwds)
        self.dimensions = f.dimensions
        self.variables = f.variables
        for k in f.ncattrs():
            setattr(self, k, f.getncattr(k))
        self.setCoords(
            ['lat', 'lon', 'lev', 'Times', 'IDATE', 'wlong', 'slat']
        )

    def ll2ij(self, lon, lat, bounds='warn', clean='clip'):
        import numpy as np
        # raqms longitude is on 0-360, while inputs are on -180, 180
        i = self.val2idx('lon', lon % 360)
        j = self.val2idx('lat', lat)
        ni = self.variables['lon'].size
        nj = self.variables['lat'].size
        ic = np.minimum(np.maximum(i, 0), ni - 1)
        jc = np.minimum(np.maximum(j, 0), nj - 1)
        if ((ic != i).any() | (ic != i).any()):
            import warnings
            warnings.warn('Some cells are outside the source domain')

        return ic, jc

    def getTimes(self, datetype='datetime', bounds=False):
        from datetime import datetime
        import numpy as np
        if bounds:
            raise NotImplementedError('bounds is not available')
        out = np.array([
            datetime.strptime(str(ti) + '+0000', '%Y%m%d%H%z')
            for ti in self.variables['IDATE'][:]
        ])
        return out

    def interpSigma(self, vglvls, vgtop=None, interptype='linear',
                    extrapolate=False, fill_value='extrapolate',
                    verbose=0):
        """
        Parameters
        ----------
        vglvls : iterable
            the new vglvls (edges)
        vgtop : scalar
            Converting to new vgtop
        interptype : string
             'linear' uses a linear interpolation
             'conserve' uses a mass conserving interpolation
        extrapolate : boolean
            allow extrapolation beyond bounds with linear, default False
        fill_value : boolean
            set fill value (e.g, nan) to prevent extrapolation or edge
            continuation

        Returns
        -------
        outf : ioapi_base
            PseudoNetCDFFile with all variables interpolated

        Notes
        -----
        When extrapolate is false, the edge values are used for points beyond
        the inputs.
        """
        from PseudoNetCDF.coordutil import sigma2coeff
        import numpy as np

        psfc = self.variables['psfc'][:][:, None, ...] * 100
        delp = self.variables['delp'][:] * 100
        pmid = self.variables['pdash'][:] * 100
        ptop = psfc - delp.sum(1)
        pedges = np.concatenate([ptop, ptop + np.cumsum(delp, axis=1)], axis=1)
        newshape = list(delp.shape)
        newshape.insert(2, len(vglvls) - 1)
        itershape = [newshape[0]] + newshape[3:]
        sigma = (pedges - vgtop) / (psfc - vgtop)
        tmpv = np.zeros(newshape, dtype='f')
        for idx in np.ndindex(*itershape):
            srcidx = (idx[0], slice(None)) + tuple(idx[1:])
            destidx = (idx[0], slice(None), slice(None)) + tuple(idx[1:])
            fromvglvls = sigma[srcidx]
            # sigma2coeff expects vglvls to decrease (i.e., surface to top),
            # but RAQMS is ordered top-to-surface. So, the vglvls are reversed
            # and the results are reversed as well.
            tmpv[destidx] = sigma2coeff(
                fromvglvls[::-1], vglvls
            )[::-1]

        pweight = tmpv[:] * pmid[:, :, None, ...]
        pnorm = pweight.sum(1)
        exprkeys = [
            key
            for key, var in self.variables.items()
            if var.dimensions[:2] == ('time', 'lev')
        ]
        outvars = {}
        for key in exprkeys:
            outvars[key] = (
                self.variables[key][:][:, :, None, ...] * pweight
            ).sum(1) / pnorm

        outf = pnc.PseudoNetCDFFile.from_ncvs(**outvars)

        for pk in self.ncattrs():
            outf.setncattr(pk, self.getncattr(pk))

        for key, dim in self.dimensions.items():
            if key not in outf.dimensions:
                outf.copyDimension(dim, key=key)

        for key, var in self.variables.items():
            if key not in exprkeys and key not in self.dimensions:
                outf.copyVariable(var, key=key)

        for vk, ov in self.variables.items():
            if vk in outf.variables:
                outf.variables[vk].setncatts({
                    k: ov.getncattr(k) for k in ov.ncattrs()
                })
        outf.VGLVLS = vglvls
        outf.VGTOP = vgtop
        return outf
