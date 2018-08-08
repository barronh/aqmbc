from glob import glob
import xarray as xr
import PseudoNetCDF as pnc
import matplotlib.pyplot as plt
np = plt.np
from matplotlib.ticker import LogLocator, LogFormatterSciNotation as LogFormatter, StrMethodFormatter
from collections import OrderedDict
import os

inpaths = sorted(glob('../combine/*BCON.combine.4LAY.nc'))
# plotfile = xr.open_mfdataset(inpaths, concat_dim='TSTEP')
# dtime = np.arange(plotfile.dims['TSTEP'], dtype='d').astype(dtype='timedelta64[h]') + (plotfile.SDATE % 1000 - 1) * 24
# rdate = np.array('{:d}-01-01'.format(plotfile.SDATE//1000), dtype='datetime64[h]')
# time = rdate + dtime
# plotfile.coords['TSTEP'] = xr.DataArray(time, dims=('TSTEP',))
# plotfile.coords['LAY'] = xr.DataArray(np.convolve([.5, .5], plotfile.VGLVLS, mode='valid'), dims=('LAY',))
plotfile = pnc.sci_var.stack_files([pnc.pncopen(path, format='ioapi') for path in inpaths], 'TSTEP')
lays = np.arange(-.5, plotfile.NLAYS + 1)
pcolors = dict(S='#2ca02c', N='#d62728', W='#1f77b4', E='#ff7f0e', L='k')

def sigmabyt(plotfile, vark, title, pslices, yscale, outpath):
    #var = plotfile.data_vars[vark]
    pf = plotfile.subsetVariables([vark])
    var = pf.variables[vark]
    plt.close();
    units = var.units.strip()
    lname = var.long_name.strip()
    vglvls = plotfile.VGLVLS
    fig, axarr = plt.subplots(4, 1, sharex=True, gridspec_kw=dict(hspace=0.1, bottom=0.15), figsize=(6, 8))
    # x = np.asarray(pf.coords['TSTEP'])
    x = pf.getTimes()
    llines = []
    first = True
    for pk, pslice in pslices.items():
        print(pk, end='', flush=True)
        #pvar = var.isel(PERIM=pslice)
        ppf = pf.sliceDimensions(PERIM=pslice)
        pvar = ppf.variables[vark]
        print('.', end='', flush=True)
        # pmvar = np.asarray(pvar.mean('PERIM')
        pmvar = np.asarray(ppf.applyAlongDimensions(PERIM='mean').variables[vark])
        print('.', end='', flush=True)
        #pnvar = np.asarray(pvar.min('PERIM'))
        pnvar = np.asarray(ppf.applyAlongDimensions(PERIM='min').variables[vark])
        print('.', end='', flush=True)
        # pxvar = np.asarray(pvar.max('PERIM'))
        pxvar = np.asarray(ppf.applyAlongDimensions(PERIM='max').variables[vark])
        print('.', flush=True)
        for si in range(var.shape[1]):
            ax = axarr[::-1][si]
            smvar = pmvar[:, si]
            snvar = pnvar[:, si]
            sxvar = pxvar[:, si]
            c = pcolors[pk[-1]]
            lmean, = ax.plot(x, smvar, label=pk, color=c)
            lmax, = ax.plot(x, sxvar, ls='--', color=c)
            lmin, = ax.plot(x, snvar, ls='--', color=c)
            ax.set_title('')
            ax.set_ylim(snvar.min(), sxvar.max())
            #ax.set_xlabel('time since {} (hours)'.format(plotfile.SDATE))
            if si == 1:
                llines.append(lmean)
            if first:
                # ax.set_ylim(pvar.values.min(), pvar.values.max())
                ax.set_ylim(pvar.array().min(), pvar.array().max())
                ax.text(1, 0.5, '{}-{}s'.format(vglvls[si], vglvls[si + 1]), transform=ax.transAxes, rotation=90, horizontalalignment='left', verticalalignment='center')
            ax.autoscale(enable=True)
        first = False
    fig.text(0.025, .5, lname + ' (' + units + ')', rotation=90, verticalalignment='center')
    fig.legend(llines, [l.get_label() for l in llines], ncol=8, loc='upper center', bbox_to_anchor=(0.5, 1))
    for ax in axarr:
        plt.setp(ax.get_xticklabels(), rotation=90)
        ax.set_yscale(yscale)
    fig.savefig(outpath)
    print(outpath)
    return fig


pslices=OrderedDict()
start=0
end=plotfile.NCOLS//2
pslices['SW'] = slice(start, end)
start=end
end=start+1+plotfile.NCOLS//2
pslices['SE'] = slice(start, end)
start=end
end=start+plotfile.NROWS//2
pslices['ES'] = slice(start, end)
start=end
end=start+1+plotfile.NROWS//2
pslices['EN'] = slice(start, end)
start=end
end=start+plotfile.NCOLS//2
pslices['NW'] = slice(start, end)
start=end
end=start+1+plotfile.NCOLS//2
pslices['NE'] = slice(start, end)
start=end
end=start+plotfile.NROWS//2
pslices['WS'] = slice(start, end)
start=end
end=start+1+plotfile.NROWS//2
pslices['WN'] = slice(start, end)

bslices = OrderedDict()
aslices = bslices['ALL'] = OrderedDict()
aslices['ALL'] = slice(None)
wslices = bslices['W'] = OrderedDict()
wslices['WN'] = pslices['WN']
wslices['WS'] = pslices['WS']
eslices = bslices['E'] = OrderedDict()
eslices['EN'] = pslices['EN']
eslices['ES'] = pslices['ES']
nslices = bslices['N'] = OrderedDict()
nslices['NW'] = pslices['NW']
nslices['NE'] = pslices['NE']
sslices = bslices['S'] = OrderedDict()
sslices['SW'] = pslices['SW']
sslices['SE'] = pslices['SE']
tslice=slice(None, None, 6)
#pf = plotfile.isel(TSTEP=tslice)
pf = plotfile.sliceDimensions(TSTEP=tslice)
pf.TSTEP *= tslice.step
for k, bpslices in bslices.items():
    print(k)
    vark = 'O3PPB'; fig = sigmabyt(pf, vark, k, bpslices, 'linear', 'ts/BC_{}_{}_ts.png'.format(vark, k))
    vark = 'PMIJ'; fig = sigmabyt(pf, vark, k, bpslices, 'log', 'ts/BC_{}_{}_ts.png'.format(vark, k))
    vark = 'ASO4IJ'; fig = sigmabyt(pf, vark, k, bpslices, 'log', 'ts/BC_{}_{}_ts.png'.format(vark, k))
    vark = 'ANO3IJ'; fig = sigmabyt(pf, vark, k, bpslices, 'log', 'ts/BC_{}_{}_ts.png'.format(vark, k))
    vark = 'ANAIJ'; fig = sigmabyt(pf, vark, k, bpslices, 'log', 'ts/BC_{}_{}_ts.png'.format(vark, k))
    vark = 'NOx'; fig = sigmabyt(pf, vark, k, bpslices, 'log', 'ts/BC_{}_{}_ts.png'.format(vark, k))

os.system('date > ts/updated')
