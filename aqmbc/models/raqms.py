__all__ = ['download']


def download(dates, root=None):
    """
    Convenience function for downloading. If root url change

    Arguments
    ---------
    dates : list
        Dates to download
    root : str
        Root path where RAQMS files are available for downloading.
        If None, defaults to https://bin.ssec.wisc.edu/pub/raqms/ESRL/RAQMS/
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
        root = 'https://bin.ssec.wisc.edu/pub/raqms/ESRL/RAQMS/'

    destpaths = []
    for date in pd.to_datetime(dates):
        url = date.strftime(f'{root}/uwhyb_%m_%d_%Y_%HZ.chem.assim.nc')
        dest = join('RAQMS', basename(url))
        if not exists(dest):
            makedirs('RAQMS', exist_ok=True)
            with requests.get(url, stream=True) as r:
                total_size = int(r.headers.get("content-length", 0))
                if total_size == 0:
                    total_size = 1024**3
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
