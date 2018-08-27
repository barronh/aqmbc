SPINPAT=/work/ROMO/global/CMAQv5.2.1/2016fe_spinup_cb6_15jh/108km/basecase/output/CONC/CCTM_CONC_v521_intel17.0_HEMIS_cb6_201512??
PRODPAT=/work/ROMO/global/CMAQv5.2.1/2016fe_hemi_cb6_16jh/108km/basecase/output/CONC/CCTM_CONC_v521_intel17.0_HEMIS_cb6_2016????

GRID=12US1

export GRID
export SPINPAT
export CONCPAT

all: link bcon combine fig

bcon: link
	$(MAKE) -C BCON all

combine: bcon
	$(MAKE)-C combine all

fig: combine
	$(MAKE) -C figs

link:
	$(MAKE) -C CONC

