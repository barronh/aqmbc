BCON
----

This folder is designed to make initial and lateral boundary conditions.

Directory Tree
./
 |- README.md
 |- Makefile
 |- bcon.py
 |- submit.sh
 |- logs


Makefile
--------
GNU-style Makefile that makes a lateral boundary condition file for each
corresponding file in CONC (i.e., ../CONC/CCTM\*) and an initial condition
file from the first file based on sort.

bcon.py
-------
bcon.py is the work horse and perfoms 4 key steps.
  1. Horizontal "interpolation"
  2. Vertical "interpolation"
  3. Species tranlations (including units)
  4. Updating meta-data.



submit.sh
---------
submit.sh is a driver script that can optionally be submitted to a SLURM
scheduling system. All it does is `make`


logs/
-----
logs holds logs from SLURM system
