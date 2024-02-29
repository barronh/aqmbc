def test_bconfromcmaq():
    import tempfile
    from os.path import join
    import glob
    import PseudoNetCDF as pnc
    import numpy as np
    from .. import runcfg

    tdir = tempfile.TemporaryDirectory()
    gdpath = join(tdir.name, 'GRIDDESC')
    cfgpath = join(tdir.name, 'test.cfg')
    exprpath = join(tdir.name, 'test.expr')
    with open(gdpath, mode='w') as gdf:
        gdf.write("""' '
'CONUS_LCC'
2 33.0 45.0 -97.0 -97.0 40.0
'POLSTE_HEMI'
 6 1.0 45.0 -98.0 -98.0 90.0
' '
'108US1'
'CONUS_LCC'  -2952000.0 -2772000.0 108000.0 108000.0 60 50 1
'1188NHEMI2'
'POLSTE_HEMI' -10098000.0 -10098000.0 1188000. 1188000. 17 17 1
' '
""")
        gdf.flush()
    with open(exprpath, mode='w') as exprf:
        exprf.write("""O3 = O3 * 1000
O3.units = 'hi'
""")
    with open(cfgpath, mode='w') as cfgf:
        cfgf.write("""
[common]
gdnam=108US1
griddesc=${rcpath}/GRIDDESC
vgtop=5000
vglvls=[1.0, 0.75, 0.5, 0.25, 0.0]
vinterp=linear
expressions=["${rcpath}/test.expr"]

[source]
input=${rcpath}/test_input_%Y%m%d.nc
format={"format": "ioapi"}
dims={"TSTEP": "TSTEP", "LAY": "LAY", "ROW": "ROW", "COL": "COL"}

[ICON]
dates=["2022-01-01"]
output=${rcpath}/test.icon.%Y%m%d.nc

[BCON]
start_date=2022-01-01
end_date=2022-01-01
freq=d
output=${rcpath}/test.bcon.%Y%m%d.nc
""")
        cfgf.flush()

    concpath = join(tdir.name, 'test_input_20220101.nc')
    cf = pnc.pncopen(
        gdpath, format='griddesc', GDNAM='1188NHEMI2', FTYPE=1,
        SDATE=2022001, STIME=0, TSTEP=10000, nsteps=24,
        VGLVLS=np.asarray([1., .8, .6, .4, .2, 0]),
        var_kwds={'O3': 'ppb'}, withcf=False
    )
    cf.variables['O3'][:, :, :, :] = np.arange(5)[None, :, None, None] + 1
    cf.save(concpath, verbose=0)
    runcfg([cfgpath])
    iconpath = glob.glob(join(tdir.name, 'test.icon.*.nc'))[0]
    bconpath = glob.glob(join(tdir.name, 'test.bcon.*.nc'))[0]
    icf = pnc.pncopen(iconpath, format='ioapi')
    bcf = pnc.pncopen(bconpath, format='ioapi')
    assert icf.NROWS == 50
    assert icf.NCOLS == 60
    assert bcf.NROWS == 50
    assert bcf.NCOLS == 60
    print(bcf.variables['O3'][0, :, 0])
    assert len(bcf.dimensions['PERIM']) == (50 * 2 + 60 * 2 + 4)
