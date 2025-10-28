__all__ = ['download']


def download(dates, root=None, fires='finn', destdir='inputs/WACCM'):
    """
    Convenience function for downloading. If root url change

    dates : list
        Dates to download
    fires : str
        finn or qfed
    root : str
        Root path where WACCM files are available for downloading.
        If None, defaults to https://www.acom.ucar.edu/waccm/DATA/
        If the root path has changed, provide a new value here and raise an
        issue at  https://github.com/barronh/aqmbc/issues

    Returns
    -------
    paths : list
        List of paths that were downloaded
    """
    import pandas as pd
    import requests
    from os.path import basename, join, exists
    from os import makedirs

    if root is None:
        root = 'https://www.acom.ucar.edu/waccm/DATA/'

    destpaths = []
    for date in pd.to_datetime(dates):
        fname = (
            'f.e22.beta02.FWSD.f09_f09_mg17.cesm2_2_beta02.forecast.'
            + {'finn': '001', 'qfed': '002'}[fires]
            + '.cam.h3.%Y-%m-%d-00000.nc')
        url = date.strftime(f'{root}/{fname}')
        dest = join(destdir, basename(url))
        if not exists(dest):
            makedirs(destdir, exist_ok=True)
            with requests.get(url, stream=True) as r:
                total_size = int(r.headers.get("content-length", 0))
                if total_size == 0:
                    total_size = 8 * 1024**3
                print('total_size (MB):', total_size / 1024**2)
                print('Each . represents 1/80th')
                block_size = 1024 * 1024
                r_size = 0
                r.raise_for_status()
                with open(dest, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=block_size):
                        f.write(chunk)
                        r_size += len(chunk)
                        print(f'\r{int(r_size / total_size * 80)*"."}', end='')
                    print()
        else:
            print(f'Using cached {dest}')

        destpaths.append(dest)

    return destpaths
