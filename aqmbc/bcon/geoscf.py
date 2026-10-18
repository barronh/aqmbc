from .._core import icbc


class geoscf(icbc):
    def _destslices(self):
        """
        Dateline Wrapping Challenge

        bc-met/chm1/chm2 files (-208.5E, 7N, -44E, 82E)
        meta file (-180, -90, 180, 90)

        Sometimes when meta file western edge lon
        is greater than the eastern edge lon

        requires separate treatment of PERIM and ROW,COL
        structured files.
        PERIM=SW-SE,SE-NE,NW-NE,SW-NW
          SW-SE=0,NCOLS  # inclusive
          SE-NE=NCOLS+1,NCOLS+NROWS+1 # inclusive
          NW-NE=NCOLS+NROWS+2,NCOLS*2+NROWS+2 # inclusive
          SW-NW=NCOLS*2+NROWS+3,NCOLS*2+NROWS*3+4 # inclusive

        dateline crossed if:
          lon[0] > lon[NCOLS]
          lon[NCOLS+NROWS+2] > lon[NCOLS*2+NROWS+2]

        if crossed, lonslice=(None, elon)

        matters for 27AK1, 9AK1 where domain crosses dateline
        """
        destf = self._metaf
        # using bbox to limit memory use during concatenation
        slat = destf.lat.min() - 1
        nlat = destf.lat.max() + 1
        if 'PERIM' in destf.dims:
            nc = destf.NCOLS
            nr = destf.NROWS
            # SE-NE=NCOLS+1,NCOLS+NROWS+1
            sp = nc + 1
            ep = sp + nr
            elon = destf.lon[sp:ep + 1].max() + 1
            # SW-NW=NCOLS*2+NROWS+3,NCOLS*2+NROWS*3+4
            sp = nc * 2 + nr + 3
            ep = sp + nr
            wlon = destf.lon[sp:ep + 1].min() - 1
            sp = nc + nr + 2
            ep = sp + nc
            ewlon = float(max(destf.lon[0], destf.lon[sp]))
            welon = float(min(destf.lon[nc], destf.lon[ep]))
            dlcrossed = (
                (destf.lon[0] > destf.lon[nc])
                | (destf.lon[sp] > destf.lon[ep])
            )
        else:
            # any western edge lon is greater than any eastern edge lon
            wlon = destf.lon[:, 0].min() - 1
            ewlon = destf.lon[:, 0].max()
            elon = destf.lon[:, -1].max() + 1
            welon = destf.lon[:, -1].min()
            dlcrossed = bool(destf.lon[:, 0].max() > destf.lon[:, -1].min())
        wlon = float(wlon)
        slat = float(slat)
        elon = float(elon)
        nlat = float(nlat)
        if wlon > 0 or dlcrossed:
            msg = f'Dateline crossed ({wlon}E,{slat}N,{elon}E,{nlat}N)'
            msg += f'; west edge max = {ewlon}'
            msg += f'; east edge min = {welon}'
            self.log(msg, level='WARN')
            lonslice = slice(None, elon)
            latslice = slice(None, nlat)
        else:
            lonslice = slice(wlon, elon)
            latslice = slice(slat, nlat)
        return {'lon': lonslice, 'lat': latslice}

    def _opener(self, path):
        import xarray as xr
        from ..utils import gethybf
        hybf = gethybf('GEOS5')
        if path.endswith('.txt'):
            with open(path) as plist:
                paths = plist.read().split()
            tmpfs = [
                xr.open_dataset(p)
                for p in paths
            ]
            destslices = self._destslices()
            tmpf = xr.merge([
                tmp.sel(**destslices)
                for tmp in tmpfs
            ], join="override")
            tmpf = tmpf.rename({key: key.lower() for key in tmpf.data_vars})
        else:
            tmpf = xr.open_dataset(path)
        nz = tmpf.sizes['lev']
        hyai = hybf.hyai.data[:nz + 1][::-1]
        hybi = hybf.hybi.data[:nz + 1][::-1]
        hyam = (hyai[1:] + hyai[:-1]) / 2
        hybm = (hybi[1:] + hybi[:-1]) / 2
        tmpf['hybm'] = ('lev',), hybm
        tmpf['hyam'] = ('lev',), hyam
        ps = tmpf['ps']
        tmpf['pmid'] = (ps * tmpf['hybm'] + tmpf['hyam']).transpose(
            'time', 'lev', 'lat', 'lon'
        )
        # overwrite to add derived variables if necessary
        return tmpf.load()
