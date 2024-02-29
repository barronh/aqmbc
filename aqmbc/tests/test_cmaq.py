def test_cmaqready():
    import tempfile
    from os.path import join
    import PseudoNetCDF as pnc
    import numpy as np
    from ..cmaq import cmaqready

    tdir = tempfile.TemporaryDirectory()
    gdpath = join(tdir.name, 'GRIDDESC')
    with open(gdpath, mode='w') as gdf:
        gdf.write("""' '
'CONUS_LCC'
2 33.0 45.0 -97.0 -97.0 40.0
' '
'108US1'
'CONUS_LCC'  -2952000.0 -2772000.0 108000.0 108000.0 60 50 1
' '
""")
        gdf.flush()

    bcpaths = [join(tdir.name, f'test_202201{d:02d}.nc') for d in [1, 2, 3]]
    for d, path in enumerate(bcpaths):
        bcf = pnc.pncopen(
            gdpath, format='griddesc', GDNAM='108US1', FTYPE=2,
            SDATE=2022001 + d, STIME=0, TSTEP=10000, nsteps=24,
            var_kwds={'O3': 'ppb'}
        )
        bcf.variables['O3'][:] = d + 1
        bcf.save(path, verbose=0)
    bcf = cmaqready('2022-01-02', bcpaths)
    assert bcf.sizes['TSTEP'] == 25
    assert bcf.TFLAG[0, 0, 0] == 2022002
    assert bcf.TFLAG[0, 0, 1] == 0
    assert bcf.TFLAG[-1, 0, 0] == 2022003
    assert bcf.TFLAG[-1, 0, 1] == 0
    assert np.allclose(bcf.O3[:-1, :, :], 2)
    assert np.allclose(bcf.O3[-1, :, :], 3)
