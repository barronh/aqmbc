__all__ = ['download', 'waccm']
import PseudoNetCDF as pnc


def download(dates, root=None, fires='finn'):
    """
    Convenience function for downloading. If root url change

    dates : list
        Dates to download
    fires : str
        finn or qfed
    root : str
        Root path where WACCM files are available for downloading.
        If None, defaults to https://www.acom.ucar.edu/waccm/DATA/
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
    from os import makedirs

    if root is None:
        root = 'https://www.acom.ucar.edu/waccm/DATA/'

    destpaths = []
    for date in pd.to_datetime(dates):
        fname = (
            'f.e22.beta02.FWSD.f09_f09_mg17.cesm2_2_beta02.forecast.'
            + {'finn': '001', 'qfed': '002'}[fires]
            + '.cam.h3.%Y-%m-%d-00000.nc')
        url = date.strftime(f'{root}/{fname}')
        dest = join('WACCM', basename(url))
        if not exists(dest):
            makedirs('WACCM', exist_ok=True)
            with requests.get(url, stream=True) as r:
                total_size = int(r.headers.get("content-length", 0))
                if total_size == 0:
                    total_size = 8 * 1024**3
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


class waccm(pnc.PseudoNetCDFFile):
    def __init__(self, *args, **kwds):
        """
        Thin wrapper around waccm files to add ll2ij, getTimes, and
        interpSigma functions.
        """
        f = pnc.pncopen(*args, **kwds)
        self.dimensions = f.dimensions
        self.variables = f.variables
        for k in f.ncattrs():
            setattr(self, k, f.getncattr(k))
        self.setCoords(
            [
                'lat', 'lon', 'lev', 'time', 'date', 'datesec', 'date',
                'hyam', 'hybm', 'P0', 'ilev', 'hyai', 'hybi', 'PS'
            ]
        )

    def ll2ij(self, lon, lat, bounds='warn', clean='clip'):
        import numpy as np
        # waccm longitude is on 0-360, while inputs are on -180, 180
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

        # time, lev, lat, lon or time, lev, PERIM
        psfc = self.variables['PS'][:][:, None, ...]
        slicer = psfc.ndim * [None]
        slicer[1] = slice(None)
        slicer = tuple(slicer)
        p0 = self.variables['P0'][...]
        hybm = self.variables['hybm'][:][slicer]
        hyam = self.variables['hyam'][:][slicer]
        hybi = self.variables['hybi'][:][slicer]
        hyai = self.variables['hyai'][:][slicer]
        pmid = (psfc * hybm + p0 * hyam)
        pedges = (psfc * hybi + p0 * hyai)
        # ptop = pedges[:, 1:]
        # pbot = pedges[:, :-1]
        # delp = pbot - ptop
        newshape = list(pmid.shape)
        newshape.insert(2, len(vglvls) - 1)
        itershape = [newshape[0]] + newshape[3:]
        sigma = (pedges - vgtop) / (psfc - vgtop)
        tmpv = np.zeros(newshape, dtype='f')
        for idx in np.ndindex(*itershape):
            srcidx = (idx[0], slice(None)) + tuple(idx[1:])
            destidx = (idx[0], slice(None), slice(None)) + tuple(idx[1:])
            fromvglvls = sigma[srcidx]
            # sigma2coeff expects vglvls to decrease (i.e., surface to top),
            # but WACCM is ordered top-to-surface. So, the vglvls are reversed
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
            if (
                key not in exprkeys
                and key not in self.dimensions
                and key not in ('hyam', 'hybm', 'hyai', 'hybi')
            ):
                outf.copyVariable(var, key=key)

        for vk, ov in self.variables.items():
            if vk in outf.variables:
                outf.variables[vk].setncatts({
                    k: ov.getncattr(k) for k in ov.ncattrs()
                })
        outf.VGLVLS = vglvls
        outf.VGTOP = vgtop
        return outf
