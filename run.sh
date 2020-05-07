#!/bin/bash


# GRID for output files
# see GRIDDESC for options
export GRID=TEST

# Whitespace Delimited list of definition files
# to use in translating input mechanism to output mechanism
# not necessary when mapping from same mechanism
export DEFN="${PWD}/definitions/gc/gc_airmolden.expr ${PWD}/definitions/gc/gc11_to_cb6r3.expr ${PWD}/definitions/gc/gc11_to_ae6_nvPOA.expr"

# Link files
DATAROOT=/work/ROMO/global/GCv11-01/GC/rundirs/geosfp_2x25_soa/ND49/
# DATAROOT=/work/ROMO/global/CMAQv5.2.1/2016fe_hemi_cb6_16jh/108km/basecase/output/CONC/
export FILEPAT='ts.*'
# export FILEPAT='CCTM_*'
ln -fs ${DATAROOT}/${FILEPAT} CONC/
ln -fs ${DATAROOT}/*info.dat BCON/
# Run all or bcon or combine or fig
make all

