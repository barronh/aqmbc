__all__ = ['dataroot', 'vgroot', 'exprsroot']

from os.path import dirname, join
dataroot = dirname(__file__)
vertgridroot = join(dataroot, 'vertgrid')
exprsroot = join(dataroot, 'expressions')
