__all__ = ['gcbench']
import PseudoNetCDF as pnc


class gcbench(pnc.PseudoNetCDFFile):
    def __init__(self, *args, **kwds):
        """
        Thin wrapper around gcnc. Finds associated StateMet file by replacing
        input path SpeciesConc with StateMet. Renames all SpeciesConc_* to
        SpeciesBC_* to allow use with regular expression files.

        If StateMet is not available... set Met_PMID
        """
        import os
        concpath = args[0]
        metpath = concpath.replace('SpeciesConc', 'StateMet')
        f = pnc.pncopen(*args, format='gcnc')
        self._f = f
        for k, d in f.dimensions.items():
            self.createDimension(k, len(d))
        for k, v in f.variables.items():
            self.variables[k.replace('SpeciesConc_', 'SpeciesBC_')] = v
        if os.path.exists(metpath):
            mf = pnc.pncopen(metpath, format='gcnc')
            self.variables['Met_PMIDDRY'] = mf.variables['Met_PMIDDRY']
            self.variables['Met_T'] = mf.variables['Met_T']
            self._mf = mf
        else:
            msg = f'StateMet not found ({metpath})'
            pnc.pncwarn.warn(msg)
            msg = 'Using US STD atmosphere T = f(P) and P=A+B*P0.'
            pnc.pncwarn.warn(msg)
            addstdpt(self)
        for k in f.ncattrs():
            self.setncattr(k, f.getncattr(k))
        self.setCoords(
            ['time', 'lat', 'lon', 'lev', 'hyai', 'hybi', 'hyam', 'hybm', 'P0']
        )

    def getTimes(self):
        return pnc.geoschemfiles.gcnc.getTimes(self)

    def ll2ij(self, *args, **kwds):
        return pnc.geoschemfiles.gcnc.ll2ij(self, *args, **kwds)

    def interpSigma(self, *args, **kwds):
        return pnc.geoschemfiles.gcnc.interpSigma(self, *args, **kwds)


def addstdpt(f):
    import numpy as np
    vard = f.variables
    refkey = 'SpeciesBC_O3'
    refv = vard[refkey]
    stdp = np.array([
        0.01, 0.05, 0.22, 0.8, 2.87, 11.97, 25.49, 55.29, 121.1, 265.0, 308.0,
        356.5, 411.1, 472.2, 540.5, 616.6, 701.2, 795.0, 898.8, 1013.0, 1139.0
    ])
    stdt = np.array([
        198.64, 219.58, 247.02, 270.65, 250.35, 226.51, 221.55, 216.65, 216.65,
        223.25, 229.73, 236.21, 242.7, 249.19, 255.68, 262.17, 268.66, 275.15,
        281.65, 288.15, 294.65
    ])
    PRES = (vard['hybm'][:] * vard['P0'][...] + vard['hyam'][:])
    TEMP = np.interp(PRES, stdp, stdt)
    f.eval(f'Met_PMIDDRY = {refkey}[:] * 0', inplace=True)
    vard['Met_PMIDDRY'].setncattr('long_name', 'Met_PMIDDRY')
    vard['Met_PMIDDRY'].setncattr('units', 'hPa')
    f.eval(f'Met_T = {refkey}[:] * 0', inplace=True)
    vard['Met_T'].setncattr('long_name', 'Met_T')
    vard['Met_T'].setncattr('units', 'K')
    vard['Met_PMIDDRY'][:] = np.expand_dims(
        PRES, axis=[0, 2, 3][:refv.ndim - 1]
    )
    vard['Met_T'][:] = np.expand_dims(
        TEMP, axis=[0, 2, 3][:refv.ndim - 1]
    )
