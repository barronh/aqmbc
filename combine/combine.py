import os

import PseudoNetCDF as pnc


def combine(inpath, outpath, exprpath, clobber=False):
    """
    Arguments
    ---------
    inpath : path to netcdf input file
    outpath : path to output file
    exprpath : path to text file with expressions

    Returns
    -------
    None
    """
    if os.path.exists(outpath) and not clobber:
        print('Using cached:', outpath)
        return
    spcexpr = open(exprpath, 'r').read()
    infile = pnc.pncopen(inpath, format='ioapi')
    if len(infile.dimensions['TSTEP']) > 1:
        infile = infile.sliceDimensions(TSTEP=slice(None, -1))
    spcfile = infile.copy().eval(spcexpr, inplace=False)
    spcfile.save(outpath, format='NETCDF4_CLASSIC')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-O', '--clobber', default=False, action='store_true')
    parser.add_argument('--expr', default='spc.expr')
    parser.add_argument('inpath')
    parser.add_argument('outpath')
    args = parser.parse_args()
    combine(args.inpath, args.outpath, args.expr, clobber=args.clobber)
