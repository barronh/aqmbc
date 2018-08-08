BCTARGETS=$(addsuffix .BCON.nc,$(subst ../CONC/,,$(sort $(wildcard ../CONC/CCTM_*))))
ICTARGETS=$(subst BCON,ICON,$(firstword $(BCTARGETS)))


all: $(BCTARGETS) $(ICTARGETS)

CCTM_%.BCON.nc: ../CONC/CCTM_%
	python bcon.py -O $^ $@

CCTM_%.ICON.nc: ../CONC/CCTM_%
	python bcon.py -O --icon $^ $@

clean:
	rm -f *.nc
