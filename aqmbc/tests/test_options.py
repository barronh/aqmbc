def test_metaf():
    from ..options import getmetaf
    bcf = getmetaf()
    bcf = getmetaf(bctype='bcon', gdnam='12US1', vgnam='EPA_35L')
    assert bcf.VGLVLS.size == 36
    assert len(bcf.dimensions['PERIM']) == 1520
    icf = getmetaf(bctype='icon', gdnam='12US1', vgnam='EPA_35L')
    assert bcf.VGLVLS.size == 36
    assert icf.NROWS == 299
    assert icf.NCOLS == 459
    bcf = getmetaf(bctype='bcon', gdnam='TEST', vgnam='EPA_44L')
    assert bcf.VGLVLS.size == 45
    assert len(bcf.dimensions['PERIM']) == 164
    assert bcf.NROWS == 37
    assert bcf.NCOLS == 43
