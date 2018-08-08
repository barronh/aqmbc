from glob import glob
import xarray as xr
from warnings import warn
import matplotlib.pyplot as plt
np = plt.np
from matplotlib.ticker import LogLocator, LogFormatterSciNotation as LogFormatter, StrMethodFormatter
from collections import OrderedDict
import PseudoNetCDF as pnc
import os

inpaths = sorted(glob('../combine/*201?????.BCON.combine.nc'))
tslice=slice(None, None, 6)
varks = ['O3PPB', 'ASO4IJ', 'ANO3IJ', 'NOx', 'ANAIJ', 'PMIJ']
infiles = [
        pnc.pncopen(inpath, format='ioapi').subsetVariables(varks).sliceDimensions(TSTEP=tslice)
        for inpath in inpaths
]
infile = infiles[0].stack(infiles[1:], 'TSTEP')
del infiles
infile.TSTEP = tslice.step * infile.TSTEP
time = infile.getTimes()
warn('Debug using {}h'.format(tslice.step))
lays = np.arange(0, infile.NLAYS + 1)


def sigmabyt(plotfile, vark, title, norm, ticks, formatter, outpath):
    plt.close();
    #fig, ax = plt.subplots(1, 1, gridspec_kw=dict(bottom=0.175, top=0.9, right=0.85))
    #cax = fig.add_axes([.875, .175, .025, .725])
    ax = plotfile.plot(vark, plottype='TSTEP-LAY',
        plot_kw=dict(norm=norm, vmin=norm.vmin, vmax=norm.vmax, cmap='jet'),
        ax_kw=dict(
            position=[.1, .25, .8, .65],
            title=title,
            yticks=lays[::2],
            yticklabels=plotfile.VGLVLS[::2],
            ylabel='sigma',
            xlabel='time since {} (hours; {})'.format(plotfile.SDATE, tslice.step),
        ),
        cbar_kw=dict(use_gridspec=False, fraction=.1))
    fig = ax.figure
    cax = fig.axes[1]
    ax.xaxis.set_major_locator(plt.matplotlib.dates.DayLocator(bymonthday=[1]))
    ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%Y-%m-%d'))
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

lnorm = plt.matplotlib.colors.LogNorm(vmin=pticks.min(), vmax=pticks.max(), clip=True)
snorm = plt.matplotlib.colors.LogNorm(vmin=sticks.min(), vmax=sticks.max(), clip=True)
nnorm = plt.matplotlib.colors.LogNorm(vmin=nticks.min(), vmax=nticks.max(), clip=True)
onorm = plt.matplotlib.colors.BoundaryNorm(oticks, 256)
onorm = plt.matplotlib.colors.LogNorm(vmin=10, vmax=1500)
noxnorm = plt.matplotlib.colors.LogNorm(vmin=noxticks.min(), vmax=noxticks.max(), clip=True)

pslices=OrderedDict()
pslices['ALL'] = slice(None)
start=0
end=infile.NCOLS//2
pslices['SW'] = slice(start, end)
start=end
end=start+1+infile.NCOLS//2
pslices['S'] = slice(pslices['SW'].start, end)
pslices['SE'] = slice(start, end)
start=end
end=start+infile.NROWS//2
pslices['ES'] = slice(start, end)
start=end
end=start+1+infile.NROWS//2
pslices['E'] = slice(pslices['ES'].start, end)
pslices['EN'] = slice(start, end)
start=end
end=start+infile.NCOLS//2
pslices['NW'] = slice(start, end)
start=end
end=start+1+infile.NCOLS//2
pslices['N'] = slice(pslices['NW'].start, end)
pslices['NE'] = slice(start, end)
start=end
end=start+infile.NROWS//2
pslices['WS'] = slice(start, end)
start=end
end=start+1+infile.NROWS//2
pslices['W'] = slice(pslices['WS'].start, end)
pslices['WN'] = slice(start, end)

for k, pslice in pslices.items():
    pf = infile.sliceDimensions(PERIM=pslice).applyAlongDimensions(PERIM='mean')
    vark = 'O3PPB'; fig = sigmabyt(pf, vark, k, onorm, oticks, formatter, 'sigmabyt/BC_{0}_O3.png'.format(k, vark))
    vark = 'ASO4IJ'; fig = sigmabyt(pf, vark, k, snorm, sticks, formatter, 'sigmabyt/BC_{0}_{1}.png'.format(k, vark))
    vark = 'ANO3IJ'; fig = sigmabyt(pf, vark, k, nnorm, nticks, formatter, 'sigmabyt/BC_{0}_{1}.png'.format(k, vark))
    vark = 'NOx'; fig = sigmabyt(pf, vark, k, noxnorm, noxticks, formatter, 'sigmabyt/BC_{0}_{1}.png'.format(k, vark))
    vark = 'ANAIJ'; fig = sigmabyt(pf, vark, k, nnorm, nticks, formatter, 'sigmabyt/BC_{0}_{1}.png'.format(k, vark))
    vark = 'PMIJ'; fig = sigmabyt(pf, vark, k, lnorm, pticks, formatter, 'sigmabyt/BC_{0}_{1}.png'.format(k, vark))
os.system('date > sigmabyt/updated')
