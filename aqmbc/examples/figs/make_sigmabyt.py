from glob import glob
import os
from warnings import warn
from functools import partial

import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

import PseudoNetCDF as pnc

from perim import perimslices

np = plt.np

def sigmabyt(plotfile, vark, title, norm, ticks, formatter, outpath):
    plt.close()
    fig = plt.figure()
    ax = fig.add_axes([.1, .25, .8, .65])
    val = plotfile.variables[vark][:].mean(2)
    qm = ax.pcolormesh(
        val.T, norm=norm, cmap='jet'
    )
    ax.set(
        title=title,
        yticks=lays[::2],
        yticklabels=plotfile.VGLVLS[::2],
        ylabel='sigma',
        xlabel='time since {} (hours; {})'.format(
            plotfile.SDATE,
            tslice.step
        )
    )
    fig.colorbar(
        qm, ax=ax, use_gridspec=False, fraction=.1
    )
    ax.xaxis.set_major_locator(
        plt.matplotlib.dates.DayLocator(bymonthday=[1])
    )
    ax.xaxis.set_major_formatter(
        plt.matplotlib.dates.DateFormatter('%Y-%m-%d')
    )
    plt.setp(ax.get_xticklabels(), rotation=90)
    fig.savefig(outpath)
    return fig


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--stem', default='sigmabyt/BC_')
    parser.add_argument('-v', '--variables', action='append', default=[])
    parser.add_argument('inpaths', nargs='+')
    args = parser.parse_args()
    if len(args.variables) == 0:
        args.variables = ['O3', 'ASO4J', 'ANO3J', 'NO2', 'ANAJ']
    tslice = slice(None, None, 6) 
    infiles = [
            pnc.pncopen(
                inpath, format='ioapi'
            ).subsetVariables(
                args.variables
            ).sliceDimensions(TSTEP=tslice)
            for inpath in args.inpaths
    ]
    infile = infiles[0].stack(infiles[1:], 'TSTEP')
    del infiles
    infile.TSTEP = tslice.step * infile.TSTEP
    time = infile.getTimes()
    warn('Debug using {}h'.format(tslice.step))
    lays = np.arange(0, infile.NLAYS + 1)

    base = 2
    formatter = StrMethodFormatter('{x:.3g}')
    pticks = base**np.arange(-2, 4, dtype='f')
    sticks = base**np.arange(-5, 1, dtype='f')
    nticks = base**np.arange(-6, 0, dtype='f')
    noxticks = base**np.arange(-6, 0, dtype='f')
    oticks = np.array([25, 27.5, 30, 32.5, 35, 37.5, 40, 45, 50, 55, 60, 70, 80, 160, 320]) / 1000

    lnorm = plt.matplotlib.colors.LogNorm(vmin=pticks.min(), vmax=pticks.max())
    snorm = plt.matplotlib.colors.LogNorm(vmin=sticks.min(), vmax=sticks.max())
    nnorm = plt.matplotlib.colors.LogNorm(vmin=nticks.min(), vmax=nticks.max())
    onorm = plt.matplotlib.colors.BoundaryNorm(oticks, 256)
    onorm = plt.matplotlib.colors.LogNorm(vmin=0.010, vmax=1.500)
    noxnorm = plt.matplotlib.colors.LogNorm(
        vmin=noxticks.min(), vmax=noxticks.max()
    )

    pslices = perimslices(infile)

    for k, pslice in pslices.items():
        pf = infile\
                .sliceDimensions(PERIM=pslice)\
                .applyAlongDimensions(PERIM='mean')
        psigmabyt = partial(sigmabyt, plotfile=pf, title=k, formatter=formatter)
        tmpl = args.stem + '{0}_{1}.png'.format
        psigmabyt(vark='O3', norm=onorm, ticks=oticks, outpath=tmpl(k, 'O3'))
        psigmabyt(
            vark='ASO4J', norm=snorm, ticks=sticks, outpath=tmpl(k, 'ASO4J')
        )
        psigmabyt(
            vark='ANO3J', norm=nnorm, ticks=nticks, outpath=tmpl(k, 'ANO3J')
        )
        psigmabyt(vark='NO2', norm=noxnorm, ticks=noxticks, outpath=tmpl(k, 'NO2'))
        psigmabyt(vark='ANAJ', norm=nnorm, ticks=nticks, outpath=tmpl(k, 'ANAJ'))
        # psigmabyt(vark='PMJ', norm=lnorm, ticks=pticks, outpath=tmpl(k, 'PMIJ'))
