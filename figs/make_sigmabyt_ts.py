from glob import glob
import os
from collections import OrderedDict
from functools import partial

import matplotlib.pyplot as plt

import PseudoNetCDF as pnc
from perim import perimslices

np = plt.np

inpaths = sorted(glob('../combine/*BCON.combine.4LAY.nc'))
infile = pnc.sci_var.stack_files(
    [pnc.pncopen(path, format='ioapi') for path in inpaths],
    'TSTEP'
)
lays = np.arange(-.5, infile.NLAYS + 1)
pcolors = dict(S='#2ca02c', N='#d62728', W='#1f77b4', E='#ff7f0e', L='k')


def sigmabyt(plotfile, vark, title, pslices, yscale, outpath):
    pf = plotfile.subsetVariables([vark])
    var = pf.variables[vark]
    plt.close()
    units = var.units.strip()
    lname = var.long_name.strip()
    vglvls = plotfile.VGLVLS
    fig, axarr = plt.subplots(
        4, 1,
        sharex=True,
        gridspec_kw=dict(hspace=0.1, bottom=0.15), figsize=(6, 8)
    )
    x = pf.getTimes()
    llines = []
    first = True
    for pk, pslice in pslices.items():
        print(pk, end='', flush=True)
        ppf = pf.sliceDimensions(PERIM=pslice)
        pvar = ppf.variables[vark]
        print('.', end='', flush=True)
        pmvar = np.asarray(
            ppf.applyAlongDimensions(PERIM='mean').variables[vark]
        )
        print('.', end='', flush=True)
        pnvar = np.asarray(
            ppf.applyAlongDimensions(PERIM='min').variables[vark]
        )
        print('.', end='', flush=True)
        pxvar = np.asarray(
            ppf.applyAlongDimensions(PERIM='max').variables[vark]
        )
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
            if si == 1:
                llines.append(lmean)
            if first:
                ax.set_ylim(pvar.array().min(), pvar.array().max())
                ax.text(
                    1, 0.5, '{}-{}s'.format(vglvls[si], vglvls[si + 1]),
                    transform=ax.transAxes, rotation=90,
                    horizontalalignment='left', verticalalignment='center'
                )
            ax.autoscale(enable=True)

        first = False

    fig.text(
        0.025, .5, lname + ' (' + units + ')',
        rotation=90, verticalalignment='center'
    )
    fig.legend(
        llines,
        [l.get_label() for l in llines],
        ncol=8, loc='upper center', bbox_to_anchor=(0.5, 1)
    )
    for ax in axarr:
        plt.setp(ax.get_xticklabels(), rotation=90)
        ax.set_yscale(yscale)
    fig.savefig(outpath)
    print(outpath)
    return fig


pslices = perimslices(infile)

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

tslice = slice(None, None, 6)

pf = infile.sliceDimensions(TSTEP=tslice)
pf.TSTEP *= tslice.step

for k, bpslices in bslices.items():
    psigmabyt = partial(
        sigmabyt,
        plotfile=pf,
        title=k,
        pslices=bpslices,
    )
    tmpl = 'ts/BC_{0}_{1}_ts.png'.format
    psigmabyt(vark='O3PPB', yscale='linear', outpath=tmpl('O3', k))
    psigmabyt(vark='PMIJ', yscale='log', outpath=tmpl('PMIJ', k))
    psigmabyt(vark='ASO4IJ', yscale='log', outpath=tmpl('ASO4IJ', k))
    psigmabyt(vark='ANO3IJ', yscale='log', outpath=tmpl('ANO3IJ', k))
    psigmabyt(vark='ANAIJ', yscale='log', outpath=tmpl('ANAIJ', k))
    psigmabyt(vark='NOx', yscale='log', outpath=tmpl('NOx', k))

os.system('date > ts/updated')
