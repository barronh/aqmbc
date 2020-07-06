TARGETS=$(patsubst %.nc,%.combine.nc,$(notdir $(sort $(wildcard ../BCON/*.?CON.nc))))
LITTLETARGETS=$(patsubst %.nc,%.combine.4LAY.nc,$(notdir $(sort $(wildcard ../BCON/*.?CON.nc))))


all: $(TARGETS) $(LITTLETARGETS)

%.BCON.combine.nc: ../BCON/%.BCON.nc
	python combine.py -O --expr=cb6r3_ae6.expr $^ $@

%.ICON.combine.nc: ../BCON/%.ICON.nc
	python combine.py -O --expr=cb6r3_ae6.expr $^ $@

%.combine.4LAY.nc: %.combine.nc
	python collapse.py -O $^ $@

clean:
	rm -f *.nc
