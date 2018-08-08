from glob import glob
import os
from warnings import warn
from functools import partial

import matplotlib.pyplot as plt
from matplotlib.ticker import StrMethodFormatter

import PseudoNetCDF as pnc

from perim import perimslices

np = plt.np

inpaths = sorted(glob('../combine/*201?????.BCON.combine.nc'))
tslice = slice(None, None, 6)
varks = ['O3PPB', 'ASO4IJ', 'ANO3IJ', 'NOx', 'ANAIJ', 'PMIJ']
infiles = [
        pnc.pncopen(
            inpath,
            format='ioapi'
        ).subsetVariables(varks).sliceDimensions(TSTEP=tslice)
        for inpath in inpaths
]
infile = infiles[0].stack(infiles[1:], 'TSTEP')
del infiles
infile.TSTEP = tslice.step * infile.TSTEP
time = infile.getTimes()
warn('Debug using {}h'.format(tslice.step))
lays = np.arange(0, infile.NLAYS + 1)


def sigmabyt(plotfile, vark, title, norm, ticks, formatter, outpath):
    plt.close()
    ax = plotfile.plot(
        vark, plottype='TSTEP-LAY',
        plot_kw=dict(norm=norm, vmin=norm.vmin, vmax=norm.vmax, cmap='jet'),
        ax_kw=dict(
            position=[.1, .25, .8, .65],
            title=title,
            yticks=lays[::2],
            yticklabels=plotfile.VGLVLS[::2],
            ylabel='sigma',
            xlabel='time since {} (hours; {})'.format(
                plotfile.SDATE,
                tslice.step
            ),
        ),
        cbar_kw=dict(use_gridspec=False, fraction=.1))
    fig = ax.figure
    ax.xaxis.set_major_locator(
        plt.matplotlib.dates.DayLocator(bymonthday=[1])
    )
    ax.xaxis.set_major_formatter(
        plt.matplotlib.dates.DateFormatter('%Y-%m-%d')
    )
    plt.setp(ax.get_xticklabels(), rotation=90)
    fig.savefig(outpath)
    return fig


base = 2
formatter = StrMethodFormatter('{x:.3g}')
pticks = base**np.arange(-2, 4, dtype='f')
sticks = base**np.arange(-5, 1, dtype='f')
nticks = base**np.arange(-6, 0, dtype='f')
noxticks = base**np.arange(-6, 0, dtype='f')
oticks = [25, 27.5, 30, 32.5, 35, 37.5, 40, 45, 50, 55, 60, 70, 80, 160, 320]

lnorm = plt.matplotlib.colors.LogNorm(vmin=pticks.min(), vmax=pticks.max())
snorm = plt.matplotlib.colors.LogNorm(vmin=sticks.min(), vmax=sticks.max())
nnorm = plt.matplotlib.colors.LogNorm(vmin=nticks.min(), vmax=nticks.max())
onorm = plt.matplotlib.colors.BoundaryNorm(oticks, 256)
onorm = plt.matplotlib.colors.LogNorm(vmin=10, vmax=1500)
noxnorm = plt.matplotlib.colors.LogNorm(
    vmin=noxticks.min(), vmax=noxticks.max()
)

pslices = perimslices(infile)

for k, pslice in pslices.items():
    pf = infile\
            .sliceDimensions(PERIM=pslice)\
            .applyAlongDimensions(PERIM='mean')
    psigmabyt = partial(sigmabyt, plotfile=pf, title=k, formatter=formatter)
    tmpl = 'sigmabyt/BC_{0}_{1}.png'.format
    psigmabyt(vark='O3PPB', norm=onorm, ticks=oticks, outpath=tmpl(k, 'O3'))
    psigmabyt(
        vark='ASO4IJ', norm=snorm, ticks=sticks, outpath=tmpl(k, 'ASO4IJ')
    )
    psigmabyt(
        vark='ANO3IJ', norm=nnorm, ticks=nticks, outpath=tmpl(k, 'ANO3IJ')
    )
    psigmabyt(vark='NOx', norm=noxnorm, ticks=noxticks, outpath=tmpl(k, 'NOx'))
    psigmabyt(vark='ANAIJ', norm=nnorm, ticks=nticks, outpath=tmpl(k, 'ANAIJ'))
    psigmabyt(vark='PMIJ', norm=lnorm, ticks=pticks, outpath=tmpl(k, 'PMIJ'))


os.system('date > sigmabyt/updated')
