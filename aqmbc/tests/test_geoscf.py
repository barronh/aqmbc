def test_geoscf():
    from .. import driver
    import tempfile
    import os
    curdir = os.path.realpath(os.getcwd())
    dates = ['2023-04-15T12:30', '2023-07-15T12:30']
    config = {
        "source": "geoscf",
        "intmpl": (
            f"{curdir}/examples/inputs/GEOSCF/"
            "%Y/%m/%d/geoscf_mcx_tavg_1hr_g1440x721_v36_%Y-%m-%dT%H30Z.nc"
        ),
        "GDNAM": '108US2', "VGNAM": 'WRFHYBRID_35L',
        "bcon_dates": dates, "icon_dates": dates[:1],
        "exprs": ["geoscf_o3so4.json"],
    }
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        try:
            outpaths = driver(config)
            check = len(outpaths) == 2
            oute = None
        except Exception as e:
            check = False
            oute = e
        os.chdir(curdir)
        if oute is not None:
            raise oute
        assert check
