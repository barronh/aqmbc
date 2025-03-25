import pandas as pd
import glob
import os


def get_vertprof(inbcon, varkeys=None, func='mean', verbose=0, outpath=None):
    """
    Arguments
    ---------
    inbcon : list or str
        If str, inbcon = sorted(glob.glob(inbcon))
        If list, items should be str or xarray.Dataset object.
        * If str, infiles = [xr.open_dataset(inpath) for inpath in inbcon]
        * If Datasets, infiles = inbcon
    varkeys : list or None
        variable keys (if None, use all)
    func : str
        Name of function to apply to each variable (min, mean, max, median)
    verbose : int
        Level of verbosity
    outpath : str or None
        Path to save (or retrieve) the vertical profile from

    Returns
    -------
    vf : xarray.Dataset
        Variables have func applied to all dimensions except for LAY.
    """
    import xarray as xr
    if isinstance(inbcon, str):
        inbcon = sorted(glob.glob(inbcon))
    if outpath is not None:
        if os.path.exists(outpath):
            intimes = [os.stat(p).st_mtime for p in inbcon]
            outtime = os.stat(outpath).st_mtime
            if len(intimes) == 0 or outtime > max(intimes):
                vprof = xr.open_dataset(outpath)
                return vprof
    vprof = make_vertprof(
        inbcon=inbcon, varkeys=varkeys, func=func, verbose=verbose
    )
    if outpath is not None:
        vprof.to_netcdf(outpath)
    return vprof


def make_vertprof(inbcon, varkeys=None, func='mean', verbose=0):
    """
    Arguments
    ---------
    inbcon : list or str
        If str, inbcon = sorted(glob.glob(inbcon))
        If list, items should be str or xarray.Dataset object.
        * If str, infiles = [xr.open_dataset(inpath) for inpath in inbcon]
        * If Datasets, infiles = inbcon
    varkeys : list or None
        variable keys (if None, use all)
    func : str
        Name of function to apply to each variable (min, mean, max, median)
    verbose : int
        Level of verbosity

    Returns
    -------
    vf : xarray.Dataset
        Variables have func applied to all dimensions except for LAY.
    """
    import xarray as xr
    import numpy as np

    if isinstance(func, str):
        funcs = [func]
    else:
        funcs = func
    vfs = []
    ts = []
    if isinstance(inbcon, str):
        inbcon = sorted(glob.glob(inbcon))
    n = len(inbcon)
    for i, inpath in enumerate(inbcon):
        if isinstance(inpath, str):
            if verbose > 0:
                print(inpath, flush=True)
            f = xr.open_dataset(inpath, decode_cf=False)
        else:
            if verbose > 0:
                print(f'\r{i / n:.2%}', end='', flush=True)
            f = inpath
        ts.append(f.SDATE * 1000000 + f.STIME)
        if 'PERIM' in f.sizes:
            dims = ('TSTEP', 'PERIM')
        else:
            dims = ('TSTEP', 'ROW', 'COL')
        if varkeys is None:
            varkeys = [k for k, v in f.data_vars.items() if 'LAY' in v.dims]
        vfs.append(xr.concat([
            getattr(f[varkeys], funcstr)(dims)
            for funcstr in funcs
        ], dim='func'))
    vf = xr.concat(vfs, dim='TSTEP')
    for vkey in varkeys:
        vf[vkey].attrs.update(f[vkey].attrs)
    vf.attrs.update(f.attrs)
    vf.coords['LAY'] = (f.VGLVLS[1:] + f.VGLVLS[:-1]) / 2
    vf.coords['func'] = funcs
    try:
        vf.coords['TSTEP'] = pd.to_datetime(ts, format='%Y%j%H%M%S')
    except Exception:
        # time-independent files cannot know their time. Use sequence
        # starting at 1
        vf.coords['TSTEP'] = np.arange(vf.sizes['TSTEP']) + 1
        pass
    if isinstance(func, str):
        vf = vf.isel(func=0)
    return vf


def plot_vprof(vmean, vmin=None, vmax=None, ax=None, **kwds):
    """
    Arguments
    ---------
    vmean : xarray.DataArray
        Average of vertical profile at time steps; must have the TSTEP and LAY
        dimensions
    vmin, vmax : xarray.DataArray
        Optional lower and upper bounds
    ax : matplotlit.axes.Axes
        Optional axes to add lines to.
    kwds : mappable
        Properties for lines

    Returns
    -------
    ax : matplotlit.axes.Axes
        If ax was provided, the same ax is returned.
        Otherwise, a new ax is created using subplots.
    """
    import matplotlib.pyplot as plt
    if vmin is None:
        vmin = vmean
    if vmax is None:
        vmax = vmean

    x = vmean.mean('TSTEP')
    xmin = vmin.min('TSTEP')
    xmax = vmax.max('TSTEP')
    y = x.LAY.values
    if ax is None:
        fig, ax = plt.subplots()
    ax.fill_betweenx(y=y, x1=xmin, x2=xmax, alpha=0.5, ax=ax, **kwds)
    ax.plot(x, y, ax=ax, **kwds)
    ax.set(ylim=(1, 0))
    return ax


def getstats(
    inbcon, varkeys=None, verbose=0, add_summary=True, outpath=None,
    draft=False
):
    """
    Arguments
    ---------
    inbcon : list or str
        If str, inbcon = sorted(glob.glob(inbcon))
        If list, items should be str or xarray.Dataset object.
        * If str, infiles = [xr.open_dataset(inpath) for inpath in inbcon]
        * If Datasets, infiles = inbcon
        If outpath is not None, inbcon must be a str or list of paths
    varkeys : list
        List of variable keys to process
    verbose : int
        Level of verbosity
    add_summary : bool
        Add summary level data
    outpath : str or None
        Path to save (or retrieve) results from. Cached results will only be
        used if the outpath file is newer than all the inputs.
    draft : bool
        If True, use actual_range and actual_median properties instead of file
        data.

    Returns
    -------
    statdf : pandas.DataFrame
        Dataframe with rows for each file and variable combination. Each row
        has min, mean, median, max, std
    """
    import pandas as pd

    if isinstance(inbcon, str):
        inbcon = sorted(glob.glob(inbcon))
    if outpath is not None:
        if os.path.exists(outpath):
            intimes = [os.stat(p).st_mtime for p in inbcon]
            outtime = os.stat(outpath).st_mtime
            if len(intimes) == 0 or outtime > max(intimes):
                statdf = pd.read_csv(outpath, index_col=[0, 1])
                return statdf

    statdf = makestats(inbcon, varkeys=varkeys, verbose=verbose, draft=draft)

    if add_summary:
        statdf = summarize(statdf)

    if outpath is not None:
        statdf.to_csv(outpath)

    return statdf


def makestats(inbcon, varkeys=None, verbose=0, draft=False):
    """
    Arguments
    ---------
    inbcon : list or str
        If str, inbcon = sorted(glob.glob(inbcon))
        If list, items should be str or xarray.Dataset object.
        * If str, infiles = [xr.open_dataset(inpath) for inpath in inbcon]
        * If Datasets, infiles = inbcon
    varkeys : list
        List of variable keys to process
    verbose : int
        Level of verbosity
    draft : bool
        If True, use actual_range and actual_median properties instead of file
        data.


    Returns
    -------
    statdf : pandas.DataFrame
        Dataframe with rows for each file and variable combination. Each row
        has min, mean, median, max, std
    """
    import numpy as np
    import xarray as xr

    stats = {}
    if isinstance(inbcon, str):
        inbcon = sorted(glob.glob(inbcon))
    n = len(inbcon)
    for bi, inpath in enumerate(inbcon):
        if verbose > 0:
            if isinstance(inpath, str):
                print(inpath, flush=True)
            else:
                print(f'\r{bi / n:.2%}', end='', flush=True)

        infile = xr.open_dataset(inpath, decode_cf=False)
        if varkeys is None or len(varkeys) == 0:
            varkeys = sorted([k for k in infile.data_vars if k != 'TFLAG'])
        for vark in varkeys:
            if verbose > 1:
                print(vark, end='.', flush=True)
            var = infile[vark]
            if draft:
                vstd = var.attrs.get('actual_std', np.nan)
                vmean = var.attrs.get('actual_mean', np.nan)
                vmedian = var.attrs.get('actual_median', np.nan)
                vmin, vmax = var.attrs.get('actual_range', np.nan)
            else:
                vl = var[:]
                vmedian = float(np.median(vl))
                vmean = float(vl.mean())
                vstd = float(vl.std())
                vmin = float(vl.min())
                vmax = float(vl.max())
            stats[inpath, vark] = {
                'unit': var.units.strip(), 'mean': vmean, 'std': vstd,
                'median': vmedian, 'min': vmin, 'max': vmax
            }
        if verbose > 1:
            print()

    statdf = pd.DataFrame.from_dict(stats, orient='index')
    statdf.index.names = ['path', 'variable']
    return statdf


def summarize(statdf, append=True):
    """
    Arguments
    ---------
    statdf : pandas.DataFrame
        DataFrame from makestats or getstats
    append : bool
        If True, add record to statdf and return full dataframe.

    Returns
    -------
    statdf : pandas.DataFrame
        Add Overall record for each variable where mean and std are averages,
        unit and min are their minimums, max is its maximum, and median is its
        median.
    """
    summarydf = statdf.groupby(['variable']).agg(
        unit=('unit', 'min'), mean=('mean', 'mean'),
        median=('median', 'median'),
        std=('std', 'mean'), max=('max', 'max'), min=('min', 'min')
    )
    summarydf['path'] = 'Overall'
    summarydf = summarydf.reset_index().set_index(['path', 'variable'])
    if append:
        outdf = pd.concat([summarydf, statdf])
    else:
        outdf = summarydf

    return outdf


def _scaletxt(p):
    if p == -0 or p == 0:
        return ' [0]'
    return f' [{-p:.0f}]'


def barplot(ds, bar_kw=None):
    """
    Arguments
    ---------
    ds : pandas.Series
        Series get from makestats or getstats
    bar_kw : mappable
        Options for the barplot function (including ax)

    Returns
    -------
    ax : matplotlib.axes.Axes
        Axes object with barplot
    """
    import numpy as np
    import pandas as pd
    import warnings
    if bar_kw is None:
        bar_kw = {}

    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        power = np.ceil(-np.log10(ds.where(ds > 0))).fillna(0)
    scale = 10**power
    index = scale.index + power.apply(_scaletxt)
    pds = pd.Series((ds * scale).values, index=index)
    # print(pd.DataFrame(dict(
    #     orig=ds, scale=scale, scaled=ds * scale
    # )).to_csv())
    ax = pds.plot.bar(**bar_kw)
    ax.set(ylabel='m x 10$^{p}$ (p by species)')
    ax.text(
        -0.02, -0.05, 'species [p]', transform=ax.transAxes, rotation=90,
        horizontalalignment='right', verticalalignment='top'
    )
    return ax


def reportfromcfg(cfgobjs, cfgtype='path'):
    """
    Runs getstats, and get_vertprof and save to disk
    If summaryfigs='y', run plot_gaspm_bars and plot_2spc_vprof and save
    results to disk.

    Arguments
    ---------
    cfgobjs : list
        List of paths, files, or dictionaries
    cfgtype : str
        'path', 'file', or 'dict'

    Returns
    -------
    None
    """
    from . import loadcfg
    import json
    import pandas as pd

    cfg = loadcfg(cfgobjs, cfgtype=cfgtype)
    dofigs = cfg.get('REPORT', 'standardfigs').lower()[:1] in ('y', 't', '1')
    dates = pd.date_range(
        cfg.get('BCON', 'start_date'), cfg.get('BCON', 'end_date')
    )
    verbose = int(cfg.get('common', 'verbose'))
    outtmpl = cfg.get('BCON', 'output')
    inpaths = [d.strftime(outtmpl) for d in dates]
    sumpath = cfg.get('REPORT', 'summary')
    varkeys = json.loads(cfg.get('REPORT', 'summaryspcs'))
    print(sumpath)
    os.makedirs(os.path.dirname(sumpath), exist_ok=True)
    statdf = getstats(
        inpaths, varkeys=varkeys, verbose=verbose, outpath=sumpath
    )
    datadesc = f'({dates[0]:%F} to {dates[-1]:%F}, n={len(dates)})'
    if dofigs:
        for metric in ['median', 'mean', 'min', 'max']:
            fig = plot_gaspm_bars(statdf, metric=metric, sortmetric='median')
            fig.text(
                0.99, 0.98, datadesc,
                horizontalalignment='right', verticalalignment='top'
            )
            fig.savefig(sumpath + f'.{metric}.png')
    varkeys = json.loads(cfg.get('REPORT', 'profilespcs'))
    for funcstr in ['mean', 'min', 'max']:
        vpath = cfg.get('REPORT', f'profile{funcstr}')
        os.makedirs(os.path.dirname(vpath), exist_ok=True)
        print(vpath)
        bf = get_vertprof(
            inpaths, varkeys=varkeys, func=funcstr, verbose=verbose,
            outpath=vpath
        )
        if dofigs:
            fig = plot_2spc_vprof(bf)
            fig.axes[0].set_title(f'{funcstr.title()} around perimiter')
            fig.axes[1].set_title(f'{funcstr.title()} around perimiter')
            fig.savefig(vpath + '.png')


def plot_gaspm_bars(
    statdf, filekey='Overall', metric='median', sortmetric='median'
):
    import matplotlib.pyplot as plt
    filedf = statdf.xs(filekey)
    sortdf = filedf.sort_values(sortmetric, ascending=False)
    gasds = sortdf.query('unit in ("ppmV", "ppmv")')[metric]
    pmds = sortdf.query('unit == "micrograms/m**3" or unit == "ug m-3"')[metric]

    gskw = dict(left=0.04, hspace=.8, bottom=0.15, right=0.98)
    gasat12 = gasds.shape[0] * 0.2
    pmat12 = pmds.shape[0] * 0.2
    gasfontsize = min(1, 16 * (gskw['right'] - gskw['left']) / gasat12) * 12
    pmfontsize = min(1, 16 * (gskw['right'] - gskw['left']) / pmat12) * 12
    fig, axx = plt.subplots(2, 1, figsize=(16, 8), gridspec_kw=gskw)
    axx[0].tick_params(labelsize=gasfontsize)
    axx[1].tick_params(labelsize=pmfontsize)
    barplot(gasds, bar_kw=dict(ax=axx[0]))
    axx[0].set_title(f'{filekey} gases {metric} sorted by {sortmetric}')
    barplot(pmds, bar_kw=dict(ax=axx[1]))
    axx[1].set_title(f'{filekey} particles {metric} sorted by {sortmetric}')
    return fig


def plot_2spc_vprof(vprof, vminprof=None, vmaxprof=None, v1k='O3', v2k=None):
    import matplotlib.pyplot as plt
    if vprof[v1k].shape[0] > 11:
        mvprof = vprof.groupby('TSTEP.month').mean().rename(month='TSTEP')
        mvprof.coords['TSTEP'] = (
            vprof['TSTEP'].groupby('TSTEP.month').mean().dt.floor('1d')
        ).values
        vprof = mvprof
        datefmt = '%Y-%m'
    else:
        datefmt = '%FT%H:%MZ'
    v1 = vprof[v1k]
    v1attrs = {}
    for k, v in v1.attrs.items():
        if isinstance(v, str):
            v = v.strip()
        v1attrs[k] = v

    dvars = vprof.data_vars
    std2ks = [k for k, v in dvars.items() if 'micrograms' in v.units.strip()]
    if v2k is None:
        if 'ASO4I' in dvars and 'ASO4J' in dvars:
            v2 = vprof['ASO4J'] + vprof['ASO4I']
            v2.attrs.update(vprof['ASO4J'].attrs)
            v2.attrs['long_name'] = 'ASO4IJ'
            v2k = 'ASO4IJ'
            if vminprof is not None and vmaxprof is not None:
                vminprof['ASO4IJ'] = vminprof['ASO4I'] + vminprof['ASO4J']
                vmaxprof['ASO4IJ'] = vmaxprof['ASO4I'] + vmaxprof['ASO4J']
        elif 'ASO4J' in dvars:
            v2k = 'ASO4J'
            v2 = vprof[v2k]
        else:
            for v2k in std2ks:
                if v2k in dvars:
                    v2 = vprof[v2k]
                    break
            else:
                raise KeyError('Could not find expected keys; specify v2k')
    v2attrs = {}
    for k, v in v2.attrs.items():
        if isinstance(v, str):
            v = v.strip()
        v2attrs[k] = v

    gskw = dict(left=0.04, right=0.98)
    fig, axx = plt.subplots(
        1, 2, figsize=(16, 6), sharey=True, gridspec_kw=gskw
    )
    cmap = plt.cm.nipy_spectral
    nt = v1.shape[0]
    for ti, v1t in enumerate(v1):
        t = v1.coords[v1.dims[0]][ti]
        try:
            label = t.dt.strftime(datefmt).values
        except Exception:
            label = f'{t.values}'

        axx[0].plot(v1t, v1.LAY, label=label, color=cmap(ti / nt))
        if vminprof is not None and vmaxprof is not None:
            vmin = vminprof[v1k][ti]
            vmax = vmaxprof[v1k][ti]
            axx[0].fill_betweenx(
                y=v1.LAY, x1=vmin, x2=vmax, color=cmap(ti / nt), alpha=0.5
            )

    axx[0].legend()
    cmap = plt.cm.nipy_spectral
    for ti, v2t in enumerate(v2):
        t = v2.coords[v2.dims[0]][ti]
        try:
            label = t.dt.strftime(datefmt).values
        except Exception:
            label = f'{t.values}'

        axx[1].plot(v2t, v2.LAY, label=label, color=cmap(ti / nt))
        if vminprof is not None and vmaxprof is not None:
            vmin = vminprof[v2k][ti]
            vmax = vmaxprof[v2k][ti]
            axx[1].fill_betweenx(
                y=v2.LAY, x1=vmin, x2=vmax, color=cmap(ti / nt), alpha=0.5
            )

    axx[1].legend()
    axx[0].set(
        xlabel='{long_name} [{units}]'.format(**v1attrs),
        ylabel='VGLVLS [$(p - p_t) / (p_s - p_t)$]', ylim=(1, 0)
    )
    axx[1].set(xlabel='{long_name} [{units}]'.format(**v2attrs))
    if v1k == 'O3':
        axx[0].set(xlim=(0.01, 0.2))
    if v2k in ('ASO4IJ', 'ASO4J') or v2k in std2ks:
        axx[1].set(xscale='log')
    return fig


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(
        prog='python -m aqmbc',
        description=(
            'Make report files (summary and profiles) for BCON files from a'
            + ' configuration file used to make them.'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'config', nargs='*', default=['run.cfg'],
        help=(
            'Configuraton file or files. Parsed in order according to the'
            + ' configparser approach using extended interpolation'
        )
    )
    parser.epilog = """
Example
    $ python -m aqmbc.report run.cfg
"""
    args = parser.parse_args()
    reportfromcfg(args.config)
