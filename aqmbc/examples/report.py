import PseudoNetCDF as pnc
import argparse
import pandas as pd


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


stats = {}
for inpath in args.inpaths:
    print(inpath, end='\n', flush=True)
    infile = pnc.pncopen(inpath, format='ioapi')
    if len(args.variable) == 0:
        args.variable = sorted([k for k in infile.variables if k != 'TFLAG'])
    for vark in args.variable:
        # print(vark)
        var = infile.variables[vark]
        vals = var[:]
        stats[inpath, vark] = {
            'unit': var.units.strip(), 'mean': vals.mean(), 'std': vals.std(),
            'min': vals.min(), 'max': vals.max()
        }
print()

statdf = pd.DataFrame.from_dict(stats, orient='index')
statdf.index.names = ['path', 'variable']
summarydf = statdf.groupby(['variable']).agg(
    unit=('unit', 'min'), mean=('mean', 'mean'), std=('std', 'mean'),
    max=('max', 'max'), min=('min', 'min')
)
summarydf['path'] = 'Overall'
summarydf = summarydf.reset_index().set_index(['path', 'variable'])
outdf = pd.concat([summarydf, statdf])
outdf.to_csv(args.csvpath)
