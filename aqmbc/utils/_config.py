__all__ = ['loadconfig', 'loadexpr']

_dflts = {
    'vgpath': None,
    'gdpath': None,
    'outtmpl': None,
    'exprs': None,
}


def _dateparser(dates):
    import pandas as pd
    if isinstance(dates, dict):
        dates = {
            dk: pd.to_datetime(dv)
            for dk, dv in dates.items()
        }
    else:
        dates = pd.to_datetime(dates)
    return dates


def loadexpr(exprs):
    from os.path import exists, join
    from ..data import exprsroot
    import json
    if exprs is None:
        return exprs
    oexprs = []
    for ev in exprs:
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

    return oexprs


def loadconfig(cfg):
    import json
    if isinstance(cfg, str):
        opts = json.load(open(cfg, 'r'))
    else:
        opts = cfg
    if opts.get('exprs', None) is None:
        from ..data.expressions import named_exprs
        opts['exprs'] = named_exprs[opts['source']]
    opts['bcon_dates'] = _dateparser(opts['bcon_dates'])
    opts['icon_dates'] = _dateparser(opts['icon_dates'])
    for k, v in _dflts.items():
        opts.setdefault(k, v)

    opts['exprs'] = loadexpr(opts['exprs'])

    return opts
