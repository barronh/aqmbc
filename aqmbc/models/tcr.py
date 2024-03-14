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
    raise ImplementationError('Not implemented')

class tcr(pnc.PseudoNetCDFFile):
    def __init__(self, *args, **kwds):
        """
        This is a special reader for TCR files. TCR files are distributed per
        species, but aqmbc expects to find the files together. The first
        argument to this reader must be a path to a text file or a list of
        paths. If it is a single path, it should be a text file with absolute
        paths of all the files you want to read.

        The files will be read in and combined for your convenience. The
        standard ll2ij, getTimes, and interpSigma function have been defined
        to be TCR meta-data aware.
        
        Example
        -------

        import glob
        import io
        from aqmbc.models.tcr import tcr

        # Assuming files were downloaded with wget -r from
        # https://tropess.gesdisc.eosdis.nasa.gov/data/
        paths = sorted(glob('tropess.gesdisc.eosdis.nasa.gov/data/*/*/*.nc'))

        # Open from a list
        f = tcr(paths)
        print(sorted(f.variables))

        # Open from an open file
        path = io.StringIO('\n'.join(paths))
        f = tcr(path)
        print(sorted(f.variables))

        # Open from a file on disk
        with open('test.txt', 'w') as outf:
            outf.write('\n'.join(paths))

        f = tcr('test.txt')
        print(sorted(f.variables))

        # ['aerosol_nh3', 'aerosol_no3', 'aerosol_so4', 'co', 'hno3', 'lat', 'lat_bnds', 'lev', 'lon', 'lon_bnds', 'no', 'no2', 'o3', 'q', 't', 'time', 'time_bnds']
        """
        import os
        inpath = args[0]
        if isinstance(inpath, str):
            inpath = open(inpath, 'r')
        if hasattr(inpath, 'read'):
            paths = inpath.read().strip().split()
        elif isinstance(inpath, (list, tuple)):
            paths = inpath
        else:
            paths = args[0].read().strip().split()
        self.dimensions = {}
        self.variables = {}
        self._fs = {}
        for path in paths:
            if not os.path.exists(path):
                print(f'Warning: not found {path}')
                continue
            f = self._fs[path] = pnc.pncopen(path)
            self.dimensions.update(f.dimensions)
            vardict = {k: v for k, v in f.variables.items() if not k.endswith('_bnds')}
            if 'aerosol' in vardict:
                var = vardict.pop('aerosol')
                aerokey = var.long_name.split(' ')[1].lower()
                vardict['aerosol_' + aerokey] = var
                if kwds.get('verbose', 0):
                    print(f'Renamed aerosol to aerosol_{aerokey}')
                
            self.variables.update(vardict)

        for k in f.ncattrs():
            setattr(self, k, f.getncattr(k))
        self.setCoords(
            ['time', 'lat', 'lon', 'lev']
        )
        

    def ll2ij(self, lon, lat, bounds='warn', clean='clip'):
        import numpy as np
        # tcr longitude is on 0-360, while inputs are on -180, 180
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
        import cftime
        time = self.variables['time']
        if bounds:
            raise NotImplementedError('bounds is not available')
        out = cftime.num2pydate(time[:], units=time.units.lower().strip())
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

        vglvls = np.asarray(vglvls)
        lev = self.variables['lev']
        levvals = lev[:] * 100
        nz = levvals.size
        pedges = np.interp(
            np.arange(nz + 1), np.arange(nz) + 0.5, levvals
        )
        psfc = 100250
        ptop = 5500
        pedges[0] = psfc
        pedges[-1] = ptop
        exvar = None
        for exkey, exvar in self.variables.items():
            if exvar.dimensions[:2] == ('time', 'lev'):
                break
        else:
            raise ValueError('Unable to find example variable')
        newshape = list(exvar.shape)
        newshape.insert(2, len(vglvls) - 1)
        wgtslice = [None] * len(newshape)
        wgtslice[1] = slice(None)
        wgtslice[2] = slice(None)
        wgtslice = tuple(wgtslice)
        sigma = (pedges - vgtop) / (psfc - vgtop)
        tmpv = np.zeros((exvar.shape[1], vglvls.size - 1), dtype='f')
        tmpv[:] = sigma2coeff(sigma, vglvls)

        pweight = (tmpv[:] * levvals[:, None])[wgtslice]
        pnorm = pweight.sum(1)
        exprkeys = [
            key for key, var in self.variables.items()
            if var.dimensions[:2] == ('time', 'lev')
        ]
        outvars = {}
        for key in exprkeys:
            var = self.variables[key]
            vals = var[:][:, :, None, ...]
            vals = np.ma.masked_values(vals, var.fill_value)
            mask = np.ma.getmaskarray(vals)
            pnorm = (pweight * (~mask).astype('i')).sum(1, keepdims=True)
            wgt = pweight / pnorm
            newvals = (
                vals * wgt
            ).sum(1)
            for l in np.arange(nz)[::-1][1:]:
                lbelo = newvals[:, l]
                labov = newvals[:, l + 1]
                newvals[:, l] = np.where(np.isnan(lbelo), labov, lbelo)

            outvars[key] = newvals

        vattrs = {pk: exvar.getncattr(pk) for pk in exvar.ncattrs()}
        fattrs = {pk: self.getncattr(pk) for pk in self.ncattrs()}

        outf = pnc.PseudoNetCDFFile.from_arrays(
            dims=exvar.dimensions, attrs=vattrs, fileattrs=fattrs,
            nameattr='long_name', **outvars
        )

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
