from .._core import icbc


class csvprofile(icbc):
    def load_date(self, date):
        """
        Load a date to process

        Arguments
        ---------
        date : datetime-like
            Date to load using intmpl

        Returns
        -------
        None
        """
        import numpy as np
        import pandas as pd
        reload = True
        if self._rawf is not None:
            if self._timekey in self._rawf.coords:
                t = pd.to_datetime(self._rawf[self._timekey])
                # allowing some numerical noise
                dt = pd.to_timedelta(date - t)
                reload = np.abs(dt.total_seconds()).min() > 10
            else:
                reload = False
        if reload:
            if isinstance(self.intmpl, str):
                path = self._activepath = date.strftime(self.intmpl)
            else:
                path = '<inline>'
                self._activepath = self.intmpl
            self.log(f'Opening {path}', level='STATUS', source='load_date')
            self._rawf = self._opener(self._activepath)
        if self._timekey in self._rawf.coords:
            self._f = self._rawf.sel(**{self._timekey: [date]}, method='nearest')
        else:
            self._f = self._rawf.expand_dims(time=[date])

    def _opener(self, path):
        import xarray as xr
        import pandas as pd
        df = pd.read_csv(path)
        reqs = ['lev(none)', 'ps(Pa)', 'pmid(Pa)']
        foundreqs = {k: k in df.columns for k in reqs}
        for k, found in foundreqs.items():
            if not found:
                self.log(f'{k} not found', level='ERROR', source='_opener')
        units = {} 
        rename = {}
        assert all([(k.endswith(')') and '(' in k) for k in df.columns])
        for col in df.columns:
            key, dum, unit = col[:-1].partition('(')
            rename[col] = key
            units[key] = unit

        df.rename(columns=rename, inplace=True)
        if 'lev' not in df.columns:
            df ['lev'] = df['pmid']
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        if 'lat' not in df.columns:
            df['lat'] = 40.
        if 'lon' not in df.columns:
            df['lon'] = -97
        dims = ['time', 'lev', 'lat', 'lon']
        dims = [d for d in dims if d in df.columns]
        ds = df.set_index(dims).to_xarray()
        ds['ps'] = ds['ps'].max('lev')
        for key, unit in units.items():
            ds[key].attrs.update(
                long_name=key.ljust(16), var_desc=key.ljust(80),
                units=unit.ljust(16)
            )
        # overwrite to add derived variables if necessary
        return ds

