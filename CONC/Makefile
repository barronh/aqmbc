ifeq ($(SPINPAT),)
SPINPAT=/work/ROMO/global/CMAQv5.2.1/2016fe_spinup_cb6_15jh/108km/basecase/output/CONC/CCTM_CONC_v521_intel17.0_HEMIS_cb6_201512??
endif
ifeq ($(PRODPAT),)
PRODPAT=/work/ROMO/global/CMAQv5.2.1/2016fe_hemi_cb6_16jh/108km/basecase/output/CONC/CCTM_CONC_v521_intel17.0_HEMIS_cb6_2016????
endif

all: link

link:
	ln -fs $(SPINPAT) CONC/
	ln -fs $(PRODPAT) CONC/

clean:
	rm CCTM_*
