__all__ = ['gc12', 'gc12_soas', 'gc14', 'gc14_soas', 'raqms']
__doc__ = """
Attributes
----------
gc12 : tuple
    options for GEOS-Chem version 12 for CB6r3 with AE7 aerosols
gc12_soas : tuple
    same as above, but for the Simple SOA option.
gc14 : tuple
    options for GEOS-Chem version 14 with CB6r5 with AE7 aerosols
gc14_soas : tuple
    same as above, but for the simple SOA option.
raqms : tuple
    cb6r4 and ae6 definitions for RAQMS
"""
from os.path import join, dirname

# redefining here because reusing from . would be recursive.
defnpath = join(dirname(__file__), 'examples', 'definitions')


def exprpaths(filenames, prefix=''):
    """
    Use short file name to get full path in expression database.

    Arguments
    ---------
    filenames : list
        File names (without directory)
    prefix : str
        Subfolder name (e.g., gc)

    Returns
    -------
    paths : tuple
        Full path (usually in site-packages) of definition files.

    Example
    -------
    The code below will return the fullpath to the gcnc_airmolden.expr file
    installed on your machine.

    > exprpaths(['gcnc_airmolden.expr'], prefix='gc')

    Note
    ----
    Use avail to find all available expression full paths.
    """
    from warnings import warn
    from os.path import exists

    paths = tuple([join(defnpath, prefix, fname) for fname in filenames])
    missing = []
    for k, p in zip(filenames, paths):
        if not exists(p):
            missing.append(k)

    if len(missing) > 0:
        missing = ', '.join(missing)
        raise KeyError(f'{p} not found with prefix="{prefix}"')

    return paths


def avail(prefix=None):
    """
    Use avail to find all available expression full paths.
    """
    from glob import glob
    if prefix is None:
        gcpaths = sorted(glob(join(defnpath, 'gc', '*')))
        cfpaths = sorted(glob(join(defnpath, 'cf', '*')))
        raqmspaths = sorted(glob(join(defnpath, 'raqms', '*')))
        return gcpaths + cfpaths + raqmspaths
    else:
        return sorted(glob(join(defnpath, prefix, '*')))


gc12 = exprpaths(['gcnc_airmolden.expr', 'gc12_to_cb6r3.expr',
                  'gc12_to_cb6mp.expr', 'gc12_to_ae7.expr'], prefix='gc')
gc12_soas = gc12[:-1] + exprpaths(['gc12_soas_to_ae7.expr'], 'gc')
gc14 = exprpaths(['gcnc_airmolden.expr', 'gc14_to_cb6r5.expr',
                  'gc14_to_cb6mp.expr', 'gc14_to_ae7.expr'], prefix='gc')
gc14_soas = gc14[:-1] + exprpaths(['gc14_soas_to_ae7.expr'], prefix='gc')
raqms = exprpaths(['raqms_to_cb6r4_ae6.expr'], prefix='raqms')
