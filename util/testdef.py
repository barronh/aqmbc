import PseudoNetCDF as pnc
from symtable import symtable
import json
import yaml
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--spcprefix', default='SpeciesBC_', help='Prefix in file (e.g., SpeciesConc_')
parser.add_argument('inpath')
parser.add_argument('fromjson')
parser.add_argument('tojson')
parser.add_argument('exprpaths', nargs='+')

test = """
gcpath = 'CONC/GEOSChem.SpeciesConc.20160701_0000z.nc4'
#gcpath = '/work/ROMO/global/GCv12.0.1/GC/rundirs/geosfp_2x25_standard/Output/GEOSChem.SpeciesConc.20160101_0000z.nc4'
gcexprpath = 'definitions/gc/gc12_to_cb6r3.expr'
aeexprpath = 'definitions/gc/gc12_to_ae6_nvPOA.expr'

args = parser.parse_args([
    '--spcprefix', 'SpeciesConc_', gcpath,
    'GEOS-Chem_Species_Database.json', 'CMAQ.json',
    gcexprpath, aeexprpath
])
"""
args = parser.parse_args()

f = pnc.pncopen(args.inpath)

#fromspcs = json.load(open(args.fromjson, 'r'))
fromspcs = yaml.load(open(args.fromjson, 'r'))
tospcs = json.load(open(args.tojson, 'r'))
exprstr = '\n'.join([open(exprpath, 'r').read() for exprpath in args.exprpaths])

noadvspc = [k for k, v in fromspcs.items() if not v.get('Is_Advected', False)]
gcspc = [k for k, v in fromspcs.items() if not v.get('Is_Aerosol', False) and v.get('Is_Advected', False)]
aespc = [k for k, v in fromspcs.items() if v.get('Is_Aerosol', False) and v.get('Is_Advected', False)]

spc = gcspc
prefix = args.spcprefix
symtbl = symtable(exprstr, '<pncexpr>', 'exec')
assigned_sym = [sym.get_name() for sym in symtbl.get_symbols() if sym.is_assigned()]
used_sym = [sym.get_name() for sym in symtbl.get_symbols() if not sym.is_assigned()]
used = [k.replace(prefix, '') for k in used_sym]

usable = sorted([k for k in spc if k not in used and (prefix + k) in f.variables])
fromneeded = sorted([k for k in used_sym if k not in f.variables])
extra = sorted([k for k in assigned_sym if k not in tospcs])
toneeded = sorted([k for k in tospcs if k not in assigned_sym and tospcs[k]['Is_Advected']])

print('\nNeeded Output, but not Assigned')
print('\n'.join(toneeded))

print('\nAssigned, but not Needed Output')
print('\n'.join(extra))

print('\nUsed in Definition, but not avail')
print('\n'.join(fromneeded))

print('\nUsed in Definition and Available, but not an Advected species')
print('\n'.join([k for k in used if k in noadvspc]))

print('\nAvail Not Used')
print('\n'.join([k + ': ' + fromspcs[k].get('FullName', k) + ' (' + fromspcs[k].get('Formula', '') + ')' for k in usable]))
