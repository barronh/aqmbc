if __name__ == '__main__':
    import argparse
    from . import runcfg

    parser = argparse.ArgumentParser(
        prog='python -m aqmbc',
        description=(
            'Make boundary conditions and initial conditions in IOAPI-like'
            + ' format for CMAQ.'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        'config', nargs='*', default=['run.cfg'],
        help=(
            'Configuraton file or files. Parsed in order according to the'
            + ' configparser approach using extended interpolation'
        )
    )
    parser.epilog = """
Example
    $ python -m aqmbc run.cfg
"""

    args = parser.parse_args()
    runcfg(args.config)
