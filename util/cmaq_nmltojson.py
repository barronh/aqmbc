import argparse
import pandas as pd
import io
from collections import OrderedDict
import json


parser = argparse.ArgumentParser()
parser.add_argument('--version', default=5.3, help='5.3 or greater uses ! column header', type=float)
parser.add_argument('outpath', help='Output path for CMAQ species JSON')
parser.add_argument('nmls', nargs='+', help='Path for NML files from CMAQ')

test = """
nmlroot = (
    '/work/MOD3DEV/hwo/cmaq_testbed/NATA_model_2017_Feb-18-2020_parallel/' +
    'CCTM/scripts/BLD_CCTM_v531_intel18.0/'
)
aenml = nmlroot + 'AE_cb6mp_ae7_aq.nml'
gcnml = nmlroot + 'GC_cb6mp_ae7_aq.nml'
nrnml = nmlroot + 'NR_cb6mp_ae7_aq.nml'

args = parser.parse_args(['CMAQ.json', gcnml, aenml, nrnml])
"""

args = parser.parse_args()

datas = []
for nml in args.nmls:
    nmltxt = open(nml, mode='r').read()
    for i in range(100):
        nmltxt = nmltxt.replace(' ', '')

    nmllines = nmltxt.split('\n')
    if args.version >= 5.3:
        lines = [l[1:] for l in nmllines if l.startswith('!')]
    else:
        lines = []
    lines += [l.strip()[:-1].replace("'", "") for l in nmllines if l.startswith("'")]
    if ':' in lines[0]:
        delim = ':'
    else:
        delim = ','
    tmpdata = pd.read_csv(io.StringIO('\n'.join(lines)), delimiter=delim)
    if any([l.startswith('&AE_nml') for l in nmllines]):
        tmpdata['TYPE'] = 'AE'
    elif any([l.startswith('&GC_nml') for l in nmllines]):
        tmpdata['TYPE'] = 'GC'
    elif any([l.startswith('&NR_nml') for l in nmllines]):
        tmpdata['TYPE'] = 'NR'
    else:
        tmpdata['TYPE'] = 'UNK'

    tmpdata.columns = [k.strip().replace('SPECIES', 'SPC') for k in tmpdata.columns]
    #tmpdata.set_index(['TYPE', 'SPC'], inplace=True)
    datas.append(tmpdata)
    # .filter(
    #     ['TYPE', 'SPC', 'MOLWT', 'IC', 'BC', 'TRNS', 'WDEP', 'DDEP', 'CONC']
    # ))

data = pd.concat(datas)

props = OrderedDict()

def check(row, key):
    return (
        row[key] == 'Yes' or
        row[key] == 'Y' or
        row[key] == 'T' or
        row[key] == 'True' or
        row[key] == 'true'
    )

for i, row in data.iterrows():
    spc = row['SPC']
    isaero = row['TYPE'] == 'AE'
    if isaero:
        suffixes = []
        if check(row, 'Aitken'):
            suffixes.append('I')
        if check(row, 'Accum'):
            suffixes.append('J')
        if check(row, 'Coarse'):
            suffixes.append('K')
    else:
        suffixes = ['']
    for suffix in suffixes:
        props[f'{spc}{suffix}'] = OrderedDict(
            Fullname=f'{spc}{suffix}',
            Formula=spc,
            Is_Advected=check(row, 'TRNS'),
            Is_Aero=row['TYPE'] == 'AE',
            Is_DryDep=check(row, 'DDEP'),
            Is_Gas=row['TYPE'] == 'GC',
            Is_HygroGrowth=None,
            Is_Photolysis=None,
            Is_WetDep=check(row, 'WDEP'),
            MW_g=row['MOLWT'],
            EmMW_g=row['MOLWT'],
            MolecRatio=1.0000
        )

json.dump(props, open(args.outpath, 'w'), indent=4)
