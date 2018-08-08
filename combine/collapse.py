import os
from glob import glob

import numpy as np
import PseudoNetCDF as pnc

outvglvls = np.array(
    [1, .75, .5, .25, 0],
    'f'
)


def collapse(inpath, outpath, clobber=False):
    """
    Arguments
    ---------
    inpath : path to netcdf input file
    outpath : path to output file
    
    Returns
    -------
    None
    """
    if os.path.exists(outpath) and not clobber:
        print('Using cached:', outpath)
        return 
    infile = pnc.pncopen(inpath, format='ioapi')
    outfile = infile.interpSigma(vglvls=outvglvls, vgtop=infile.VGTOP, interptype='conserve')
    outfile.save(outpath, format='NETCDF4_CLASSIC')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-O', '--clobber', default=False, action='store_true')
    parser.add_argument('inpath')
    parser.add_argument('outpath')
    args = parser.parse_args()
    collapse(args.inpath, args.outpath, clobber=args.clobber)
