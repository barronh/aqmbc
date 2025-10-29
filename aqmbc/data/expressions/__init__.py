__all__ = ['exprsroot', 'named_exprs']
from os.path import dirname, join
exprsroot = dirname(__file__)

named_exprs = {
    ('geoscf', 'test'): ['geoscf_met.json', 'geoscf_o3so4.json'],
    'geoscf': [
        'geoscf_met.json', 'geoscf_cb6.json', 'geoscf_ae7.json'
    ],
    ('geoscf', 'cb6_ae7'): [
        'geoscf_met.json', 'geoscf_cb6.json', 'geoscf_ae7.json'
    ],
    ('geoscf', 'cracmm2'): [
        'geoscf_met.json', 'geoscf_cracmm2gas.json', 'geoscf_cracmm2aero.json'
    ],
    ('geoschem', 'test'): [
        'gcnc_airmolden.json', 'gc14_o3so4.json',
    ],
    'geoschem': [
        'gcnc_airmolden.json', 'gc14_to_cb6r5.json', 'gc14_to_cb6mp.json',
        'gc14_to_ae7.json'
    ],
    ('geoschem', 'cb6_ae7'): [
        'gcnc_airmolden.json', 'gc14_to_cb6r5.json', 'gc14_to_cb6mp.json',
        'gc14_to_ae7.json'
    ],
    ('geoschem', 'cb6_ae7soas'): [
        'gcnc_airmolden.json', 'gc14_to_cb6r5.json', 'gc14_to_cb6mp.json',
        'gc14_soas_to_ae7.json'
    ],
    ('gcbench', 'cb6_ae7'): [
        'gcnc_airmolden.json', 'gc14_to_cb6r5.json', 'gc14_to_cb6mp.json',
        'gc14_to_ae7.json'
    ],
    ('gcbench', 'cb6_ae7soas'): [
        'gcnc_airmolden.json', 'gc14_to_cb6r5.json', 'gc14_to_cb6mp.json',
        'gc14_soas_to_ae7.json'
    ],
    'raqms': ['raqms_to_cb6r4_ae6.json'],
    ('raqms', 'cb6_ae6'): ['raqms_to_cb6r4_ae6.json'],
    ('raqms', 'test'): ['raqms_o3so4.json'],
    'tcr': ['tcr_cb6.json', 'tcr_ae7.json'],
    ('tcr', 'cb6_ae7'): ['tcr_cb6.json', 'tcr_ae7.json'],
    ('tcr', 'test'): ['tcr_o3so4.json'],
    'waccm': [
        'waccm_met.json', 'waccm_cb6.json', 'waccm_ae7.json'
    ],
    ('waccm', 'cb6_ae7'): [
        'waccm_met.json', 'waccm_cb6.json', 'waccm_ae7.json'
    ],
    ('waccm', 'test'): ['waccm_o3so4.json'],
}

for k, v in list(named_exprs.items()):
    named_exprs[k] = [join(exprsroot, p) for p in v]

named_exprs['cmaq'] = None
named_exprs['csvprofile'] = None
