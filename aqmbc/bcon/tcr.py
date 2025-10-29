from .._core import icbc


class tcr(icbc):
    def _opener(self, path):
        """
        Arguments
        ---------
        path : str
            Path to a file, which is a list of file paths.
        Returns
        -------
        outf : xarray.Dataset
            File with sufficient variables to create boundary conditions

        Notes
        -----
        import glob
        yyyy = '2021'
        paths = sorted(glob.glob(
            f'inputs/TCR2/tropess.gesdisc.eosdis.nasa.gov/data/*/*/*{yyyy}.nc'
        ))
        tpath = f'inputs/TCR2/TCR2_MON_{yyyy}.txt'
        with open(tpath, 'w') as tcrf:
            tcrf.write('\n'.join(paths))

        """
        import xarray as xr
        import numpy as np
        import pandas as pd
        paths = open(path, 'r').read().split('\n')
        for i, path in enumerate(paths):
            tmpf = xr.open_dataset(path)
            if 'aerosol' in tmpf:
                aspc = tmpf['aerosol'].long_name.split(' ')[1].lower()
                tmpf = tmpf.rename(aerosol='aerosol_' + aspc)
            if i == 0:
                outf = tmpf
            else:
                for k in tmpf.data_vars:
                    outf[k] = tmpf[k]
        pedges = np.append(outf.lev.values * 100, 5500)
        pmid = (pedges[1:] + pedges[:-1]) / 2.
        outf.coords['lev'] = pmid
        PMID = outf.coords['lev'].expand_dims(
            time=outf.time, lat=outf.lat, lon=outf.lon
        )
        PMID = PMID.transpose('time', 'lev', 'lat', 'lon')
        PS = PMID.max('lev') * pedges[0] / pmid[0]
        outf['pmid'] = PMID
        outf['ps'] = PS
        # files are nominally monthly. Put the times at the mid-point of
        # the month so that IOAPI processing has the right month after
        # approximating the time window.
        outf.coords['time'] = outf.coords['time'] + pd.to_timedelta('14d')

        return outf

    def to_lonlat(self, lon, lat, method='nearest'):
        """
        Thin wrapper around icbc.to_lonlat to convert lon to [0, 360] first
        """
        super().to_lonlat(lon % 360, lat, method='nearest')
