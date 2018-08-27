BCTARGETS=$(addsuffix .BCON.nc,$(notdir $(sort $(wildcard ../CONC/CCTM_*))))
ICTARGETS=$(subst BCON,ICON,$(firstword $(BCTARGETS)))
ifeq ($(GRID),)
GRID=36US3
endif

all: $(BCTARGETS) $(ICTARGETS)

CCTM_%.BCON.nc: ../CONC/CCTM_%
	python bcon.py -O --grid $(GRID) $^ $@

CCTM_%.ICON.nc: ../CONC/CCTM_%
	python bcon.py -O --grid $(GRID) --icon $^ $@

clean:
	rm -f *.nc
