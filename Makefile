all: bcon combine fig

bcon:
	$(MAKE) -C BCON all

combine: bcon
	$(MAKE) -C combine all

fig: combine
	$(MAKE) -C figs
