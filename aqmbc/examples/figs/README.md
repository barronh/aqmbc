# BCON

This folder is designed to make initial and lateral boundary conditions.

## Directory Tree

```
.
|-- README.md
|-- make_curtains.py
|-- make_rowbycol.py
|-- make_sigmabyt.py
`-- make_sigmabyt_ts.py
```

## make\_curtains.py

Plot monthly average "curtain" plots. "Curtain" plots have 4 panel pseudocolor
plots that represent the lateral boundary condition as curtain around an 
observer.

```bash
python make_curtains.py BCON/*
```


## make\_rowbycol.py

Plot maps using a single pseudocolor panel for a layer of the atmosphere.

```bash
python make_rowbycol.py ICON/*
```


## make\_sigmabyt.py

Plot pseudocolor panels with sigma on the Y-axis and time on the X-axis.

```bash
python make_sigmabyt.py BCON/*
```


## make_sigmabyt_ts.py

Plot min,mean,max time-series lines with 4 panels for quarters of the atmos-
phere by mass.

```bash
python make_sigmabyt_ts.py BCON/*
```

