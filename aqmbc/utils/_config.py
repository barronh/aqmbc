__all__ = ['loadconfig']

_dflts = {
    'vgpath': None,
    'gdpath': None,
    'outtmpl': None,
}


def _dateparser(dates):
    import pandas as pd
    if isinstance(dates, dict):
        dates = pd.date_range(**dates)
    else:
        dates = pd.to_datetime(dates)
    return dates


def loadconfig(cfg):
    import json
    from os.path import exists, join
    from ..data import exprsroot
    if isinstance(cfg, str):
        opts = json.load(open(cfg, 'r'))
    else:
        opts = cfg
    bdates = opts['bcon_dates']
    opts['bcon_dates'] = _dateparser(opts['bcon_dates'])
    opts['icon_dates'] = _dateparser(opts['icon_dates'])
    for k, v in _dflts.items():
        opts.setdefault(k, v)
    oexprs = []
    for ev in opts['exprs']:
        if isinstance(ev, str):
            fev = join(exprsroot, ev)
            if exists(ev):
                pass
            elif exists(fev):
                ev = fev
            else:
                raise IOError('expressions does not exist')
            oexprs.extend(json.load(open(ev, 'r')))
        else:
            oexprs.append(ev)
    opts['exprs'] = oexprs

    return opts


def driver(cfg):
    from .. import bcon
    from . import getmetaf
    opts = loadconfig(cfg)
    gkwds = ['GDNAM', 'gdpath', 'VGNAM', 'vgpath']
    gkwds = {k: v for k, v in opts.items() if k in gkwds}
    bdates = opts['bcon_dates']
    idates = opts['icon_dates']
    source = getattr(getattr(bcon, opts['source']), opts['source'])
    ckwds = ['intmpl', 'outtmpl', 'exprs']
    ckwds = {k: v for k, v in opts.items() if k in ckwds}
    bgf = getmetaf(**gkwds, FTYPE=2)
    cf = source(bgf, **ckwds)
    cf.process(bdates)
    igf = getmetaf(**gkwds, FTYPE=1)
    cf = source(bgf, **ckwds)
    cf.process(idates)
