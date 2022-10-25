from collections import OrderedDict


def perimslices(infile):
    pslices = OrderedDict()
    pslices['ALL'] = slice(None)
    incr = infile.NCOLS + 1
    last = pslices['S'] = slice(0, incr)
    pslices['SW'] = slice(last.start, last.start + incr // 2)
    pslices['SE'] = slice(last.start + incr // 2, last.stop)
    incr = infile.NROWS + 1
    last = pslices['E'] = slice(last.stop, last.stop + incr)
    pslices['ES'] = slice(last.start, last.start + incr // 2)
    pslices['EN'] = slice(last.start + incr // 2, last.stop)
    incr = infile.NCOLS + 1
    last = pslices['N'] = slice(last.stop, last.stop + incr)
    pslices['NW'] = slice(last.start, last.start + incr // 2)
    pslices['NE'] = slice(last.start + incr // 2, last.stop)
    incr = infile.NROWS + 1
    last = pslices['W'] = slice(last.stop, last.stop + incr)
    pslices['WS'] = slice(last.start, last.start + incr // 2)
    pslices['WN'] = slice(last.start + incr // 2, last.stop)
    return pslices
