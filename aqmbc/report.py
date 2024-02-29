import PseudoNetCDF as pnc
import pandas as pd


def get_vertprof(inpaths, varkeys=None):
    import xarray as xr
    vfs = []
    for inpath in inpaths:
        f = xr.open_dataset(inpath, decode_cf=False)
        if 'PERIM' in f.sizes:
            dims = ('TSTEP', 'PERIM')
        else:
            dims = ('TSTEP', 'ROW', 'COL')
        if varkeys is None:
            varkeys = [k for k, v in f.data_vars.items() if 'LAY' in v.dims]
        vf = f[[varkeys]].mean(dims)
    vf = xr.concat(vfs, dim='TSTEP')
    return vf


def getstats(inpaths, varkeys, verbose=0):
    stats = {}
    for inpath in inpaths:
        if verbose > 0:
            print(inpath, flush=True)
        infile = pnc.pncopen(inpath, format='ioapi')
        if len(varkeys) == 0:
            varkeys = sorted([k for k in infile.variables if k != 'TFLAG'])
        for vark in varkeys:
            # print(vark)
            var = infile.variables[vark]
            vals = var[:]
            stats[inpath, vark] = {
                'unit': var.units.strip(), 'mean': vals.mean(),
                'std': vals.std(), 'min': vals.min(), 'max': vals.max()
            }

    statdf = pd.DataFrame.from_dict(stats, orient='index')
    statdf.index.names = ['path', 'variable']

    return statdf


def summarize(statdf, outpath=None):
    summarydf = statdf.groupby(['variable']).agg(
        unit=('unit', 'min'), mean=('mean', 'mean'), std=('std', 'mean'),
        max=('max', 'max'), min=('min', 'min')
    )
    summarydf['path'] = 'Overall'
    summarydf = summarydf.reset_index().set_index(['path', 'variable'])
    outdf = pd.concat([summarydf, statdf])
    if outpath is not None:
        outdf.to_csv(outpath)


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
