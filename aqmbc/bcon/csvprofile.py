from .._core import icbc


class csvprofile(icbc):
    def __init__(self, *args, **kwds):
        """
        Arguments
        ---------
        metaf : xarray.Dataset
        intmpl : str
            Input file template using strftime format that points to a csv file
            where columns have units in parentheses:
            - ps(Pa) is surface pressure (e.g., 1e5) - required for first level
            - pmid(Pa) is mid-level pressure - required for all levels
            - time(utc) if time varying - optional
            - lon(degrees_east) and/or lat(degrees_north) - required if
              spatially varying
            - lev(none) defaults to pmid - required if ps and pmid vary by
              time/lat/lon
            - other columns will be interpolated for use as boundary conditions
        exprs : list
            List of dictionaries. If provided, columns will be used as inputs
            to derive outputs.
        outtmpl : str
            Output file template using strftime format
        verbose : int
            Verbosity level

        Returns
        -------
        None

        Example
        -------
        import aqmbc

        csvpath = 'inputs/csvprofile.csv'
        with open(csvpath, 'w') as csvf:
            csvf.write('''
        ps(Pa),pmid(Pa),O3(ppmV),ASO4J(micrograms/m**3)
        1e5,8e4,0.04,0.8
        ,6e4,0.05,0.2
        ,4e4,0.06,0.1
        ,2e4,0.08,0.04
        ,1e4,.4,0.02
        ,0.5e4,2,0.02
        ''')

        dates = ['2019-04-01T00']
        config = {
            "source": "csvprofile",
            "intmpl": csvpath,
            "GDNAM": '108US2', "VGNAM": 'WRFHYBRID_35L',
            "bcon_dates": dates, "icon_dates": dates[:1],
        }
        outpaths = aqmbc.driver(config)
        """
        super().__init__(*args, **kwds)

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

        _rf = self._rawf
        if self._timekey in _rf.coords:
            self._f = _rf.sel(**{self._timekey: [date]}, method='nearest')
        else:
            self._f = _rf.expand_dims(time=[date])

    def _opener(self, path):
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
            df['lev'] = df['pmid']
        if 'time' in df.columns:
            df['time'] = pd.to_datetime(df['time'])
        # lat/lon default to center of US
        # nearest interpolation will always choose this cell no matter where
        # the target is.
        if 'lat' not in df.columns:
            df['lat'] = 40.
        if 'lon' not in df.columns:
            df['lon'] = -97.
        dims = ['time', 'lev', 'lat', 'lon']
        dims = [d for d in dims if d in df.columns]
        ds = df.set_index(dims).to_xarray()
        ds['ps'] = ds['ps'].max('lev')
        for key, unit in units.items():
            ds[key].attrs.update(
                long_name=key.ljust(16), var_desc=key.ljust(80),
                units=unit.ljust(16)
            )
        return ds
