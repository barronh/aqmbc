def test_exprpaths():
    from os.path import exists
    from ..exprlib import exprpaths
    paths = exprpaths(['gcnc_airmolden.expr'], prefix='gc')
    assert exists(paths[0])
    try:
        paths = exprpaths(['gcnc_airmolden.notit'], prefix='gc')
        raise IOError('Error was not raised')
    except KeyError:
        pass


def test_avail():
    from ..exprlib import avail
    assert len(avail()) > 0
