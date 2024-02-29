__all__ = [
    'geoschem12', 'geoschem12_soas',
    'geoschem14', 'geoschem14_soas',
    'raqms'
]
__doc__ = """
Attributes
----------
geoschem12 : tuple
    options for GEOS-Chem version 12 for CB6r3 with AE7 aerosols
geoschem12_soas : tuple
    same as above, but for the Simple SOA option.
geoschem14 : tuple
    options for GEOS-Chem version 14 with CB6r5 with AE7 aerosols
geoschem14_soas : tuple
    same as above, but for the simple SOA option.
raqms : tuple
    cb6r4 and ae6 definitions for RAQMS
"""
from os.path import join, dirname


# redefining here because reusing from . would be recursive.
defnpath = join(dirname(__file__), 'examples', 'definitions')
geoschem12 = (
    join(defnpath, 'gc', fname) for fname in [
        'gc_airmolden.expr',
        'gc12_to_cb6r3.expr', 'gc12_to_cb6mp.expr',
        'gc12_to_ae7.expr'
    ]
)
geoschem12_soas = (p for p in geoschem12 if 'to_ae' not in p)
geoschem12_soas.append(join(defnpath, 'gc', 'gc12_soas_to_ae7.expr'))
geoschem14 = (
    join(defnpath, 'gc', fname) for fname in [
        'gc_airmolden.expr',
        'gc14_to_cb6r5.expr', 'gc14_to_cb6mp.expr',
        'gc14_to_ae7.expr'
    ]
)
geoschem14_soas = ((p for p in geoschem14 if 'to_ae' not in p)
                   + (join(defnpath, 'gc', 'gc14_soas_to_ae7.expr'),))

raqms = (join(defnpath, 'raqms', 'raqms_to_cb6r4_ae6.expr'),)
