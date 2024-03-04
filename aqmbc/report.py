import PseudoNetCDF as pnc
import pandas as pd


def get_vertprof(inpaths, varkeys=None):
    import xarray as xr
    import numpy as np
    vfs = []
    ts = []
    for inpath in inpaths:
        f = xr.open_dataset(inpath, decode_cf=False)
        ts.append(f.SDATE * 1000000 + f.STIME)
        if 'PERIM' in f.sizes:
            dims = ('TSTEP', 'PERIM')
        else:
            dims = ('TSTEP', 'ROW', 'COL')
        if varkeys is None:
            varkeys = [k for k, v in f.data_vars.items() if 'LAY' in v.dims]
        vfs.append(f[varkeys].mean(dims))
    vf = xr.concat(vfs, dim='TSTEP')
    for vkey in varkeys:
        vf[vkey].attrs.update(f[vkey].attrs)
    vf.attrs.update(f.attrs)
    vf.coords['LAY'] = (f.VGLVLS[1:] + f.VGLVLS[:-1]) / 2
    try:
        vf.coords['TSTEP'] = pd.to_datetime(ts, format='%Y%j%H%M%S')
    except Exception:
        # time-independet files cannot know their time. Use sequence
        # starting at 1
        vf.coords['TSTEP'] = np.arange(vf.sizes['TSTEP']) + 1
        pass
    return vf


def getstats(inpaths, varkeys=None, verbose=0):
    import numpy as np
    stats = {}
    for inpath in inpaths:
        if verbose > 0:
            print(inpath, flush=True)
        infile = pnc.pncopen(inpath, format='ioapi')
        if varkeys is None:
            varkeys = sorted([k for k in infile.variables if k != 'TFLAG'])
        for vark in varkeys:
            # print(vark)
            var = infile.variables[vark]
            vl = var[:]
            stats[inpath, vark] = {
                'unit': var.units.strip(), 'mean': vl.mean(), 'std': vl.std(),
                'median': np.median(vl), 'min': vl.min(), 'max': vl.max()
            }

    statdf = pd.DataFrame.from_dict(stats, orient='index')
    statdf.index.names = ['path', 'variable']

    return statdf


def summarize(statdf, outpath=None, append=True):
    summarydf = statdf.groupby(['variable']).agg(
        unit=('unit', 'min'), mean=('mean', 'mean'),
        median=('median', 'median'),
        std=('std', 'mean'), max=('max', 'max'), min=('min', 'min')
    )
    summarydf['path'] = 'Overall'
    summarydf = summarydf.reset_index().set_index(['path', 'variable'])
    if append:
        outdf = pd.concat([summarydf, statdf])
    else:
        outdf = summarydf
    if outpath is not None:
        outdf.to_csv(outpath)
    return outdf


def barplot(ds, norm=True, bar_kw=None):
    import numpy as np
    import pandas as pd
    if bar_kw is None:
        bar_kw = {}

    power = np.log10(ds).round(0)
    scale = 1 / 10**power
    index = scale.index + power.apply(lambda x: f' x1e{-x:.0f}')
    pds = pd.Series((ds * scale).values, index=index)
    pds.plot.bar(**bar_kw)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description="""
Create a report of basic stats from a set of BCON files.
""")
    parser.add_argument(
        '-v', '--variable', default=[], action='append',
        help='If not provided, all non TFLAG variables will be used'
    )
    parser.add_argument('csvpath', help='Path for report as a csv')
    parser.add_argument('inpaths', nargs='+', help='BCON files')
    args = parser.parse_args()
    statdf = getstats(args.inpaths, args.variable)
    summarize(statdf, args.csvpath)
