import PseudoNetCDF as pnc
import numpy as np
import matplotlib.colors as mc


GDNAM_CHILD = '12US5' # os.environ['GRID']
GDNAM_PARENT = 'HEMI_187_187'

child = pnc.pncopen('../GRIDDESC', format='griddesc', GDNAM=GDNAM_CHILD, FTYPE=2)
parent = pnc.pncopen('../GRIDDESC', format='griddesc', GDNAM=GDNAM_PARENT, FTYPE=1)

bmap = parent.getMap(suppress_ticks=False) # resolution='i', states=True)
xp = parent.variables['x'][1:] - parent.XORIG - parent.XCELL / 2
yp = parent.variables['y'][1:] - parent.YORIG - parent.YCELL / 2
Xc, Yc = bmap(
    child.variables['longitude'][:],
    child.variables['latitude'][:]
)
c = bmap.scatter(Xc, Yc, c=Yc * 0 + 1.5, cmap='bwr', norm=mc.BoundaryNorm([0, 1, 2], 256), marker='+')
bmap.drawcoastlines()
bmap.drawcountries()
bmap.drawstates()
ax = c.axes

for x in xp:
    ax.axvline(x, color='k')

for y in yp:
    ax.axhline(y, color='k')

fig = ax.figure

xmin = Xc.min() - parent.XCELL * 2
ymin = Yc.min() - parent.YCELL * 2
xmax = Xc.max() + parent.XCELL * 2
ymax = Yc.max() + parent.YCELL * 2

ax.set_xlim(xmin, xmax)
ax.set_ylim(ymin, ymax)

fig.savefig('netmap/nest.png')
