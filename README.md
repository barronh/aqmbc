aqmbc
-----

Air Quality Model Boundary Condition Tools

Air Quality Model Boundary Conditions is a tool to create time and space
boundary conditions for an Air Quality Model from one or many data sources.

Directory Listing
./
 |- README
 |- GRIDDESC
 |- CONC/
 |- BCON/
 |- combine/
 |- figs/

Each folder has its own README, Makefile, and submit.sh. The README describes
in detail the process for that folder. The Makefile has rules for making
necessary files. The submit.sh has a SLURM submittal script to call make.

This README describes the overall flow.

Steps:
1. Populate CONC with concentration files (symbolic links for files; in run.sh).
2. Populate BCON with boundary files using contained scripts (make bcon).
3. Populate combine with derived variables (make combine).
4. Populate figs to illustrate results (make fig).

All steps can be run with `./run.sh` and 2-4 can be run with `GRID=12US1 make`
Each step can be called iteratively while the others are in process.

Prerequisites:
 1. All steps require PseudoNetCDF (github.com/barronh/PseudoNetCDF).
