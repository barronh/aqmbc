def test_cmaq():
    from .. import driver
    import tempfile
    import os
    import pandas as pd
    curdir = os.path.realpath(os.getcwd())
    dates = pd.date_range('2019-04-01T00', periods=25, freq='1h')
    config = {
        "source": "cmaq",
        "intmpl": (
            f"{curdir}/examples/inputs/CMAQ/"
            "cmaq.equates.hemi_example.conc.%Y-%m-%d.nc"
        ),
        "GDNAM": '108US2', "VGNAM": 'WRFHYBRID_35L',
        "bcon_dates": dates, "icon_dates": dates[:1],
    }
    hybtxt = """vglvl,A,B
1.0,0.0,1.0
0.9391,1062.8639333447954,0.9315163863966851
0.6693,17100.095881179142,0.514834059942214
0.2690,28995.40023128937,0.015595991798167425
0.0,5000.0,0.0
"""
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        with open('WRFHYBRID_4L.csv', 'w') as hybf:
            hybf.write(hybtxt)
        try:
            outpaths = driver(config)
            check = len(outpaths) == 2
            oute = None
        except Exception as e:
            check = False
            oute = e
        os.chdir(curdir)
        if oute is None:
            assert check
        else:
            raise oute
