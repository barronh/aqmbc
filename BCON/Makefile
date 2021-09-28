# GRID is required in the environment
ifeq ($(GRID),)
$(error GRID is not set)
endif

# FILE Pattern defaults to all files in CONC
ifeq ($(FILEPAT),)
FILEPAT=*
endif

# Definitions defaults to nothing
ifneq ($(DEFN),)
EXPR=$(addprefix --expr=,$(DEFN))
endif

# BCTARGETS are all files
BCTARGETS=$(addsuffix .BCON.nc,$(notdir $(sort $(wildcard ../CONC/$(FILEPAT)))))

# ICTARGETS should be the first file
ICTARGETS=$(subst BCON,ICON,$(firstword $(BCTARGETS)))

all: $(BCTARGETS) $(ICTARGETS)

%.BCON.nc: ../CONC/%
	python ../aqmbc/bcon.py -O $(BCOPTS) $(EXPR) --grid $(GRID) $^ $@

%.ICON.nc: ../CONC/%
	python ../aqmbc/bcon.py -O $(BCOPTS) $(EXPR) --grid $(GRID) --icon $^ $@

clean:
	rm -f *.nc
