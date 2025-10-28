__all__ = ['download']


def download(dates, freq='mon', root=None, destroot='inputs/TCR2'):
    """
    Convenience function for downloading. If root url change

    dates : list
        Dates to download
    freq : str
        mon or 6hr
    root : str
        Root path where TROPESS Composition Reanalysis (TCR) files are
        available for downloading.
        If None, defaults to https://tropess.gesdisc.eosdis.nasa.gov/data/
        If the root path has changed, provide a new value here and raise an
        issue at  https://github.com/barronh/aqmbc/issues

    Returns
    -------
    paths : list
        List of paths that were downloaded
    """
    import pandas as pd
    import requests
    from os.path import basename, join, exists, dirname
    from os import makedirs

    if root is None:
        root = 'https://tropess.gesdisc.eosdis.nasa.gov/data/'
    years = sorted(set([d.year for d in pd.to_datetime(dates)]))
    frequ = freq.upper()
    freql = freq.lower()
    freqs = {'6HR': '6H', 'MON': 'M'}[frequ]
    ft = '_VERTCONCS/TRPSCR'
    st = '3D.1/TROPESS_reanalysis_'

    destpaths = []
    for year in years:
        varpaths = [
            f"TCR2_{frequ}_METFIELDS/TRPSCRT{freqs}{st}{freql}_t_{year}.nc",
            f"TCR2_{frequ}_METFIELDS/TRPSCRQ{freqs}{st}{freql}_q_{year}.nc",
            f"TCR2_{frequ}{ft}CO{freqs}{st}{freql}_co_{year}.nc",
            f"TCR2_{frequ}{ft}O3{freqs}{st}{freql}_o3_{year}.nc",
            f"TCR2_{frequ}{ft}NO{freqs}{st}{freql}_no_{year}.nc",
            f"TCR2_{frequ}{ft}NO2{freqs}{st}{freql}_no2_{year}.nc",
            f"TCR2_{frequ}{ft}HNO3{freqs}{st}{freql}_hno3_{year}.nc",
            f"TCR2_{frequ}{ft}SO2{freqs}{st}{freql}_so2_{year}.nc",
            f"TCR2_{frequ}{ft}CH2O{freqs}{st}{freql}_ch2o_{year}.nc",
            f"TCR2_{frequ}{ft}PAN{freqs}{st}{freql}_pan_{year}.nc",
            f"TCR2_{frequ}{ft}AERNO3{freqs}{st}{freql}_aero_no3_{year}.nc",
            f"TCR2_{frequ}{ft}AERNH4{freqs}{st}{freql}_aero_nh4_{year}.nc",
            f"TCR2_{frequ}{ft}AERSO4{freqs}{st}{freql}_aero_so4_{year}.nc",
        ]
        for varpath in varpaths:
            url = f'{root}/{varpath}'
            dest = join(destroot, basename(url))
            if not exists(dest):
                makedirs(dirname(dest), exist_ok=True)
                with requests.get(url, stream=True) as r:
                    ts = int(r.headers.get("content-length", 0))
                    if ts == 0:
                        ts = 1024**3
                    print('total_size (MB):', ts / 1024**2)
                    print('Each . represents 1/80th')
                    block_size = 1024 * 1024
                    rs = 0
                    r.raise_for_status()
                    with open(dest, 'wb') as f:
                        for chunk in r.iter_content(chunk_size=block_size):
                            f.write(chunk)
                            rs += len(chunk)
                            print(f'\r{int(rs / ts * 80)*"."}', end='')
                        print()
            else:
                print(f'Using cached {dest}')

        destpaths.append(dest)

    return destpaths
