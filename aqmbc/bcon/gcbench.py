from .geoschem import geoschem

class gcbench(geoschem):
    def __init__(self, *args, bcprefix='SpeciesConc_', **kwds):
        super().__init__(*args, bcprefix=bcprefix, **kwds)
