import PseudoNetCDF as pnc
import numpy as np
import matplotlib.pyplot as plt
from glob import glob
import os
import gc

norms = dict(
    O3PPB = plt.matplotlib.colors.LogNorm(vmin=0.02, vmax=1),
    ANO3IJ = plt.matplotlib.colors.LogNorm(vmin=0.02, vmax=1),
    ASO4IJ = plt.matplotlib.colors.LogNorm(vmin=0.1, vmax=5),
    PMIJ = plt.matplotlib.colors.LogNorm(vmin=0.2, vmax=10),
    default = plt.matplotlib.colors.LogNorm()
)

def curtain(inpaths, vark):
    inf = pnc.sci_var.stack_files(
        [
            pnc.pncopen(path, format='ioapi').subsetVariables([vark])
            for path in inpaths
        ],
        'TSTEP'
    )
    times = inf.getTimes()
    pslices = dict()
    sslice = pslices['S'] = slice(0, inf.NCOLS + 1)
    eslice = pslices['E'] = slice(sslice.stop, sslice.stop + inf.NROWS + 1)
    nslice = pslices['N'] = slice(eslice.stop, eslice.stop + inf.NCOLS + 1)
    wslice = pslices['W'] = slice(nslice.stop, nslice.stop + inf.NROWS + 1)

    axorder = dict()
    axorder['W'] = 0
    axorder['N'] = 1
    axorder['E'] = 2
    axorder['S'] = 3

    norm = norms.get(vark, norms['default'])
    eta = inf.VGLVLS * (101325 - inf.VGTOP) / 100 + inf.VGTOP / 100
    for mo in [1, 4, 7, 10]:
        tidx = np.array([ti for ti, t in enumerate(times) if t.month == mo])
        if tidx.size == 0:
            continue

        tf = inf.sliceDimensions(TSTEP=tidx).applyAlongDimensions(TSTEP='mean')
        reprdate = tf.getTimes()[0]
        yyyy = reprdate.strftime('%Y')
        fig, axarr = plt.subplots(
            1, 4,
            figsize=(16, 4),
            sharey=True,
            gridspec_kw=dict(bottom=0.15)
        )
        for pk, pslice in pslices.items():
            ax = axarr[axorder[pk]]
            plotf = tf.sliceDimensions(PERIM=pslice)
            vals = plotf.variables[vark][0, :, :]
            if vark == 'O3PPB':
                vals = vals / 1000
                units = 'ppm'
            else:
                units = plotf.variables[vark].units.strip()
            x = np.arange(len(plotf.dimensions['PERIM'])) * inf.XCELL / 1000
            p = ax.pcolor(x, eta, vals, norm=norm, cmap='jet')
            ax.set_xlim(x.min(), x.max())

        axarr[0].set_ylim(*axarr[0].get_ylim()[::-1])
        axarr[0].set_ylabel('Pressure')
        ax = axarr[axorder['E']]
        ax.set_xlim(*ax.get_xlim()[::-1])
        ax.set_title('Eastern')
        ax.set_xlabel('N to S km')
        ax = axarr[axorder['W']]
        ax.set_title('Western')
        ax.set_xlabel('S to N km')
        ax = axarr[axorder['N']]
        ax.set_title('Northern')
        ax.set_xlabel('W to E km')
        ax = axarr[axorder['S']]
        ax.set_title('Southern')
        ax.set_xlabel('E to W km')
        ax.set_xlim(*ax.get_xlim()[::-1])
        cax = fig.add_axes([.925, .1, .025, .8])
        fig.colorbar(p, cax=cax, label=units)
        figpath = (
            'curtains/monthly/' +
            'BC_{0}{1:02d}_{2}.png'.format(yyyy, mo, vark)
        )
        print(vark, mo, figpath)
        fig.savefig(figpath)

    del inf
    gc.collect()

if __name__ == '__main__':
    inpaths = sorted(glob('../combine/*BCON*.combine.nc'))
    varkeys = ['O3PPB', 'PMIJ', 'ANO3IJ', 'ASO4IJ']
    for vark in varkeys:
        curtain(inpaths, vark)
    os.system('date > curtains/updated')
