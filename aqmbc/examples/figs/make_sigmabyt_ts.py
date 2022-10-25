from glob import glob
import os
from collections import OrderedDict
from functools import partial

import matplotlib.pyplot as plt

import PseudoNetCDF as pnc
from perim import perimslices

np = plt.np

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
            lmean, = ax.plot(x, smvar, label=pk, color=c, marker='o')
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

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--stem', default='ts/BC_')
    parser.add_argument('-l', '--levels', default=[1, 0.75, 0.5, 0.25, 0])
    parser.add_argument('inpaths', nargs='+')
    args = parser.parse_args()

    infiles = [
        pnc.pncopen(path, format='ioapi').interpSigma(vglvls=args.levels)
        for path in args.inpaths
    ]
    infile = infiles[0].stack(infiles[1:], 'TSTEP')
    lays = np.arange(-.5, infile.NLAYS + 1)
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

    tslice = slice(None, None, 1)

    pf = infile.sliceDimensions(TSTEP=tslice)
    pf.TSTEP *= tslice.step

    for k, bpslices in bslices.items():
        psigmabyt = partial(
            sigmabyt,
            plotfile=pf,
            title=k,
            pslices=bpslices,
        )
        tmpl = (args.stem + '{0}_{1}_ts.png').format
        psigmabyt(vark='O3', yscale='linear', outpath=tmpl('O3', k))
        # psigmabyt(vark='PMJ', yscale='log', outpath=tmpl('PMJ', k))
        psigmabyt(vark='ASO4J', yscale='log', outpath=tmpl('ASO4J', k))
        psigmabyt(vark='ANO3J', yscale='log', outpath=tmpl('ANO3J', k))
        psigmabyt(vark='ANAJ', yscale='log', outpath=tmpl('ANAJ', k))
        psigmabyt(vark='NO2', yscale='log', outpath=tmpl('NO2', k))
