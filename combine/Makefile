TARGETS=$(patsubst %.nc,%.combine.nc,$(notdir $(sort $(wildcard ../BCON/CCTM_*))))
LITTLETARGETS=$(patsubst %.nc,%.combine.4LAY.nc,$(notdir $(sort $(wildcard ../BCON/CCTM_*))))


all: $(TARGETS) $(LITTLETARGETS)

CCTM_%.BCON.combine.nc: ../BCON/CCTM_%.BCON.nc
	python combine.py -O --expr=cb6r3_ae6.expr $^ $@

CCTM_%.ICON.combine.nc: ../BCON/CCTM_%.ICON.nc
	python combine.py -O --expr=cb6r3_ae6.expr $^ $@

CCTM_%.combine.4LAY.nc: CCTM_%.combine.nc
	python collapse.py -O $^ $@

clean:
	rm -f *.nc
