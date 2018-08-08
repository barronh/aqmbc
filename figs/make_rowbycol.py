from glob import glob
import xarray as xr
import PseudoNetCDF as pnc
import matplotlib.pyplot as plt
import os

inpaths = sorted(glob('../combine/*.ICON.combine.nc'))
inpath = inpaths[0]
#plotfile = xr.open_mfdataset(inpaths, concat_dim='TSTEP', engine='pseudonetcdf', backend_kwargs=dict(format='ioapi', addcf=True, diskless=True))
plotfile = pnc.pncopen(inpath, format='ioapi')

def makerowbycolpnc(plotfile, vark, lslice, norm, outpath):
    plt.close();
    plotfile = plotfile.subsetVariables([vark]).sliceDimensions(TSTEP=0, LAY=lslice)
    var = plotfile.variables[vark]
    units = var.units.strip()
    lname = var.long_name.strip()
    ax = plotfile.plot(vark, plot_kw=dict(norm=norm))
    cax = ax.figure.axes[1]
    val = var.array()
    cax.set_ylabel('{} ({}; {:.3g}, {:.3g})'.format(lname, units, val.min(), val.max()))
    ax.set_ylabel('row')
    ax.set_xlabel('col')
    plt.savefig(outpath)

def makerowbycolxr(plotfile, var, outpath, norm):
    plt.close();
    units = var.attrs['units'].strip()
    lname = var.attrs['long_name'].strip()
    var = var.isel(LAY=0).mean('TSTEP')
    col = var.plot(norm=norm)
    cax = col.axes.figure.axes[1]
    val = var.values
    cax.set_ylabel('{} ({}; {:.3g}, {:.3g})'.format(lname, units, val.min(), val.max()))
    col.axes.set_ylabel('row')
    col.axes.set_xlabel('col')
    plt.savefig(outpath)

makerowbycol = makerowbycolpnc
lnorm=plt.matplotlib.colors.LogNorm()
makerowbycol(plotfile, 'PMIJ', lslice=0, norm=lnorm, outpath='rowbycol/IC_L00_PMIJ.png')
makerowbycol(plotfile, 'PMIJ', lslice=20, norm=lnorm, outpath='rowbycol/IC_L20_PMIJ.png')
makerowbycol(plotfile, 'PMIJ', lslice=26, norm=lnorm, outpath='rowbycol/IC_L26_PMIJ.png')
onorm = plt.matplotlib.colors.BoundaryNorm([20, 25, 35, 40, 45, 50, 55], 256)
makerowbycol(plotfile, 'O3PPB', lslice=0, norm=onorm, outpath='rowbycol/IC_L00_O3.png')
makerowbycol(plotfile, 'O3PPB', lslice=20, norm=onorm, outpath='rowbycol/IC_L20_O3.png')
makerowbycol(plotfile, 'O3PPB', lslice=26, norm=onorm, outpath='rowbycol/IC_L26_O3.png')
os.system('date > rowbycol/updated')
