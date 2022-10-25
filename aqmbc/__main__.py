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
        '-t', '--template', default=None, type=str,
        help='Copy example directory to template'
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
    if args.template is not None:
        import shutil
        import os
        srcdir = os.path.join(os.path.dirname(__file__), 'examples')
        shutil.copytree(srcdir, args.template)
    else:
        runcfg(args.config)
