BCON
----

This folder is designed to make initial and lateral boundary conditions.

Directory Tree
./
 |- README.md
 |- Makefile
 |- make\_curtains.py
 |- make\_rowbycol.py
 |- make\_sigmabyt.py
 |- make\_sigmabyt\_ts.py


Makefile
--------
GNU-style Makefile that makes figures using \*.py files.

make\_curtains.py
-----------------
Plot monthly average "curtain" plots. "Curtain" plots have 4 panel pseudocolor
plots that represent the lateral boundary condition as curtain around an 
observer.


make\_rowbycol.py
-----------------
Plot maps using a single pseudocolor panel for a layer of the atmosphere.


make\_sigmabyt.py
-----------------
Plot pseudocolor panels with sigma on the Y-axis and time on the X-axis.


make\_sigmabyt\_ts.py
---------------------
Plot min,mean,max time-series lines with 4 panels for quarters of the atmos-
phere by mass.

