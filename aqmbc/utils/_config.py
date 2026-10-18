__all__ = ['loadconfig', 'loadexpr']

_dflts = {
    'vgpath': None,
    'gdpath': None,
    'outtmpl': None,
    'exprs': None,
}


def _dateparser(dates):
    """
    dates : dict or list
        dict - key is the output file date and value should be input file times
        list - items are both output file date and input file date
    Returns
    -------
    dateopts : dict or lsit
        Output type depends on input. The input file times are all converted

    Notes
    -----
    """
    import pandas as pd
    if isinstance(dates, dict):
        dates = {
            dk: pd.to_datetime(dv)
            for dk, dv in dates.items()
        }
    else:
        dates = pd.to_datetime(dates)
    return dates


def _validexpr(edict):
    errors = []
    if isinstance(edict, list):
        for ev in edict:
            errors.extend(_validexpr(ev))
        return errors
    for k in ['name', 'expression', 'units']:
        if k not in edict:
            errors.append(f'ERROR:loadexpr:{k} not in {ev}')
        else:
            kv = edict[k]
            if not isinstance(kv, str):
                errors.append(f'ERROR:loadexpr:{k} not a string')
    return errors


def loadexpr(exprs):
    """
    Provide elements to build an expression list. Each element will be expanded
    and concatenated to create a new exprs list. The final exprs list will be
    a list of dictionaries with at least keys name, expression, and units.

    If an exprs element is alrady a dictionary, it will be checked for keys and
    data types.

    Arguments
    ---------
    exprs : str, tuple, list
        str or tuple - must name an option in data.expressions.named_exprs
        list of
            tuples - each tuple used as a key to named_exprs
                     to a json describing a list of dictionaries.
            str    - each str used as a key to named_exprs
                     to a json describing a list of dictionaries.
            dict - each element must have name, expression, and units keys
                   the expression must be defined by variables in the data
                   source or by a previous expression.

    Returns
    -------
    exprs : list of dict
         each element must have name, expression, and units keys
         the expression must be defined by variables in the data
         source or by a previous expression.
    """
    from os.path import exists, join
    from ..data import exprsroot
    from ..data.expressions import named_exprs
    import json

    if exprs is None:
        return exprs
    if isinstance(exprs, (str, tuple)):
        return loadexpr([exprs])

    oexprs = []
    errors = []
    for ev in exprs:
        tmpexprs = []
        if isinstance(ev, str):
            # If an expression value is a path on disk, use that file.
            # Try looking in the exprs data root as a failsafe
            fev = join(exprsroot, ev)
            for epath in [ev, fev]:
                if exists(epath):
                    try:
                        with open(epath, 'r') as ef:
                            tmpexprs = json.load(ef)
                        break
                    except Exception as e:
                        errors.append(str(e))
            else:
                # if ev is a string, but not a path, try looking it up as a
                # 1-element tuple
                msg = f'{ev} does not exist locally (./) or in {exprsroot}'
                if (ev,) in named_exprs:
                    tmpexprs = loadexpr(named_exprs[(ev,)])
                else:
                    errors.append(msg)
            # use loadexpr with list of dicts to validate individual expr items
        elif isinstance(ev, tuple):
            if ev in named_exprs:
                # load
                tmpexprs = loadexpr(named_exprs[ev])
            else:
                msg = f'{ev} not in named expressions ({list(named_exprs)})'
                errors.append(msg)
        elif isinstance(ev, dict):
            tmpexprs = [ev]
        else:
            errors.append(f'{ev} option must be a str, tuple, or dict')

        errors.extend(_validexpr(tmpexprs))
        oexprs.extend(tmpexprs)
    if len(errors) > 0:
        raise Exception(f'{len(errors)} errors:\n  ' + '\n  '.join(errors))
    return oexprs


def loadconfig(cfg):
    """
    Arguments
    ---------
    cfg : str or dict
        If cfg is a str, it will be treated as a path to a json file to load
        a dict.

    Returns
    -------
    cfg : dict
        Updated dictionary of options with parsed dates (bcon_dates, icon_date),
        loaded expressions, and defaults for all other options
    """
    import json
    if isinstance(cfg, str):
        opts = json.load(open(cfg, 'r'))
    else:
        opts = cfg
    if 'exprs' not in opts:
        from ..data.expressions import named_exprs
        opts['exprs'] = named_exprs[(opts['source'],)]
    opts['bcon_dates'] = _dateparser(opts['bcon_dates'])
    opts['icon_dates'] = _dateparser(opts['icon_dates'])
    for k, v in _dflts.items():
        opts.setdefault(k, v)

    opts['exprs'] = loadexpr(opts['exprs'])

    return opts
