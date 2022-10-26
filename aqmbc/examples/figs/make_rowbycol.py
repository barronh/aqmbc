import numpy as np
from functools import partial
import matplotlib.pyplot as plt
import PseudoNetCDF as pnc


def makerowbycol(plotfile, vark, lslice, norm, outpath):
    plt.close()
    plotfile = plotfile\
        .subsetVariables([vark])\
        .sliceDimensions(TSTEP=0, LAY=lslice)
    var = plotfile.variables[vark]
    val = var.array()
    valmin = val.min()
    valmax = val.max()
    units = var.units.strip()
    lname = var.long_name.strip()
    fig, ax = plt.subplots(1, 1)
    if valmin == 0 and valmax == 0:
        norm = None
    qm = ax.pcolormesh(
        val[:].squeeze(), norm=norm
    )
    clabel = '{} ({}; {:.3g}, {:.3g})'.format(
        lname, units, valmin, valmax
    )
    fig.colorbar(qm, label=clabel, ax=ax)
    ax.set_ylabel('row')
    ax.set_xlabel('col')
    print(outpath)
    plt.savefig(outpath)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('inpath')
    args = parser.parse_args()
    plotfile = pnc.pncopen(args.inpath, format='ioapi')

    lnorm = plt.matplotlib.colors.LogNorm()
    onorm = plt.matplotlib.colors.BoundaryNorm(
        np.array([20, 25, 30, 35, 40, 45, 50, 55]) / 1000, 256
    )
    pmakerc = partial(
        makerowbycol,
        plotfile=plotfile
    )

    tmpl = 'rowbycol/IC_L{0:02d}_{1}.png'.format
    for lay in [0, 20, 26]:
        pmakerc(
            vark='ANO3J', lslice=lay, norm=lnorm, outpath=tmpl(lay, 'ANO3J')
        )
        pmakerc(
            vark='ASO4J', lslice=lay, norm=lnorm, outpath=tmpl(lay, 'ASO4J')
        )
        pmakerc(
            vark='APOCJ', lslice=lay, norm=lnorm, outpath=tmpl(lay, 'APOCJ')
        )
        pmakerc(
            vark='O3', lslice=lay, norm=onorm, outpath=tmpl(lay, 'O3')
        )
