import PseudoNetCDF as pnc


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

    def ll2ij(self, lon, lat):
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

        psfc = self.variables['psfc'][:][:, None, :, :] * 100
        delp = self.variables['delp'][:] * 100
        pmid = self.variables['pdash'][:] * 100
        ptop = psfc - delp.sum(1)
        pedges = np.concatenate([ptop, ptop + np.cumsum(delp, axis=1)], axis=1)
        newshape = list(delp.shape)
        newshape.insert(2, len(vglvls) - 1)
        itershape = [newshape[0]] + newshape[3:]
        sigma = (pedges - vgtop) / (psfc - vgtop)
        tmpv = np.zeros(newshape, dtype='f')
        for ti, ri, ci in np.ndindex(*itershape):
            fromvglvls = sigma[ti, :, ri, ci]
            # sigma2coeff expects vglvls to decrease (i.e., surface to top),
            # but RAQMS is ordered top-to-surface. So, the vglvls are reversed
            # and the results are reversed as well.
            tmpv[ti, :, :, ri, ci] = sigma2coeff(
                fromvglvls[::-1], vglvls
            )[::-1]

        pweight = tmpv[:] * pmid[:, :, None, :, :]
        pnorm = pweight.sum(1)
        outdims = ('time', 'lev', 'lat', 'lon')
        exprkeys = [
            key
            for key, var in self.variables.items()
            if var.dimensions == outdims
        ]
        outvars = {}
        for key in exprkeys:
            outvars[key] = (
                self.variables[key][:][:, :, None, :, :] * pweight
            ).sum(1) / pnorm

        return pnc.PseudoNetCDFFile.from_ncvs(**outvars)
