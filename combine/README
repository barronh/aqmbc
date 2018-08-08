BCON
----

This folder is designed to make initial and lateral boundary conditions.

Directory Tree
./
 |- README.md
 |- Makefile
 |- combine.py
 |- cb6r3_ae6_nvPOA.expr
 |- collapse.py
 |- submit.sh
 |- logs/


Makefile
--------
GNU-style Makefile that makes a lateral boundary condition file for each
corresponding file in BCON (i.e., ../BCON/CCTM\*).


combine.py
----------
combine.py creates a small file with derived variables where the definitions
for derived variables are in an expr file.


cb6r3_ae6_nvPOA.expr
--------------------
Definition for expressions used by combine.py


collapse.py
-----------
Create a 4 layer version (1-0.75, 0.75-0.5, 0.5-0.25, 0.25-0 sigma) from the
combine file. This is useful for quick understanding of the important parts
of the atmosphere.
plotting and for understanding 


submit.sh
---------
submit.sh is a driver script that can optionally be submitted to a SLURM
scheduling system. All it does is `make`


logs/
-----
logs holds logs from SLURM system
