from glob import glob
import os
from functools import partial

import matplotlib.pyplot as plt

import PseudoNetCDF as pnc

inpaths = sorted(glob('../combine/*.ICON.combine.nc'))
inpath = inpaths[0]
plotfile = pnc.pncopen(inpath, format='ioapi')


def makerowbycol(plotfile, vark, lslice, norm, outpath):
    plt.close()
    plotfile = plotfile\
        .subsetVariables([vark])\
        .sliceDimensions(TSTEP=0, LAY=lslice)
    var = plotfile.variables[vark]
    units = var.units.strip()
    lname = var.long_name.strip()
    ax = plotfile.plot(vark, plot_kw=dict(norm=norm))
    cax = ax.figure.axes[1]
    val = var.array()
    cax.set_ylabel('{} ({}; {:.3g}, {:.3g})'.format(
        lname, units, val.min(), val.max())
    )
    ax.set_ylabel('row')
    ax.set_xlabel('col')
    print(outpath)
    plt.savefig(outpath)


lnorm = plt.matplotlib.colors.LogNorm()
onorm = plt.matplotlib.colors.BoundaryNorm([20, 25, 30, 35, 40, 45, 50, 55], 256)

pmakerc = partial(
    makerowbycol,
    plotfile=plotfile
)

tmpl = 'rowbycol/IC_L{0:02d}_{1}.png'.format
for lay in [0, 20, 26]:
    pmakerc(vark='PMIJ', lslice=lay, norm=lnorm, outpath=tmpl(lay, 'PMIJ'))
    pmakerc(vark='O3PPB', lslice=lay, norm=onorm, outpath=tmpl(lay, 'O3'))

os.system('date > rowbycol/updated')
