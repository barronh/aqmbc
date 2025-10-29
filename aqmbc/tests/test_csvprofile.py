def test_csvprofile():
    from .. import driver
    import tempfile
    import os
    curdir = os.path.realpath(os.getcwd())
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        csvpath = 'csvprofile.csv'
        with open(csvpath, 'w') as csvf:
            csvf.write('''ps(Pa),pmid(Pa),O3(ppmV),ASO4J(micrograms/m**3)
1e5,8e4,0.04,0.8
,6e4,0.05,0.2
,4e4,0.06,0.1
,2e4,0.08,0.04
,1e4,.4,0.02
,0.5e4,2,0.02
''')
        dates = ['2019-04-01T00']
        config = {
            "source": "csvprofile",
            "intmpl": csvpath,
            "GDNAM": '108US2', "VGNAM": 'WRFHYBRID_35L',
            "bcon_dates": dates, "icon_dates": dates[:1],
        }
        try:
            outpaths = driver(config)
            check = len(outpaths) == 2
        except Exception:
            check = False
        os.chdir(curdir)
        assert check


def test_report():
    from .. import driver
    from .. import report
    import tempfile
    import os
    curdir = os.path.realpath(os.getcwd())
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        csvpath = 'csvprofile.csv'
        with open(csvpath, 'w') as csvf:
            csvf.write('''ps(Pa),pmid(Pa),O3(ppmV),ASO4J(micrograms/m**3)
1e5,8e4,0.04,0.8
,6e4,0.05,0.2
,4e4,0.06,0.1
,2e4,0.08,0.04
,1e4,.4,0.02
,0.5e4,2,0.02
''')
        dates = ['2019-04-01T00']
        config = {
            "source": "csvprofile",
            "intmpl": csvpath,
            "GDNAM": '108US2', "VGNAM": 'WRFHYBRID_35L',
            "bcon_dates": dates, "icon_dates": dates[:1],
        }
        try:
            outpaths = driver(config)
            vprof = report.profile_report(outpaths['bcon'])
            statdf = report.range_report(vprof)
            check = (statdf.shape[0] > 1) & (statdf.shape[1] > 1)
        except Exception:
            check = False
        os.chdir(curdir)
        assert check


def test_exprs():
    from .. import driver
    import tempfile
    import os
    curdir = os.path.realpath(os.getcwd())
    with tempfile.TemporaryDirectory() as td:
        os.chdir(td)
        csvpath = 'csvprofile.csv'
        with open(csvpath, 'w') as csvf:
            csvf.write('''ps(Pa),pmid(Pa),O3(ppbV),ASO4J(g/m**3)
1e5,8e4,40,0.8e-6
,6e4,50,0.2e-6
,4e4,60,0.1e-6
,2e4,80,0.04e-6
,1e4,400,0.02e-6
,0.5e4,2000,0.02e-6
''')
        dates = ['2019-04-01T00']
        exprs = [
            {'name': 'O3', 'expression': 'O3 * 1e-3', 'units': 'ppmV'},
            {
                'name': 'ASO4J', 'expression': 'ASO4J * 1e6',
                'units': 'micrograms/m**3'
            },
        ]
        config = {
            "source": "csvprofile",
            "intmpl": csvpath,
            "GDNAM": '108US2', "VGNAM": 'WRFHYBRID_35L',
            "bcon_dates": dates, "icon_dates": dates[:1],
            "exprs": exprs
        }
        try:
            outpaths = driver(config)
            check = len(outpaths) == 2
        except Exception:
            check = False
        os.chdir(curdir)
        assert check
