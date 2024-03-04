aqmbc Examples
==============

Each of the examples below uses a minimum working example. Each example was first tested on the original files from the source model. Afterwards, the input files were subset to make the inputs easy to distribute.

* Only ozone and sulfate aerosol were retained,
* lon/lat was subset to just conver the continental US, and
* the grid was thinned to 3x3 (corners and midpoints).

*Feel free to skip ahead and run the examples. The description below explains how to update examples.*

Make an Example More Real
-------------------------

The minimum working examples can be updated to be full applications easily. Each example is designed so that, if its inputs are not available, it will download the original "full" files. The only other change is to replace the expression files (currently only using ozone and sulfate) with a more comprehensive set.

The process of testing and then updating the examples is described in detail below. I use the GEOS-Chem Benchmark as an example. In this example, I assume a new grid called OTHER that is defined in a GRIDDESC in the users home directory. I also provide syntax for both shell (bash or csh) and IPython/Jupyter.

1.  Install software (requires python3):
  * shell `pip install --user -qq git+https://github.com/barronh/aqmbc.git`
  * notebook `%pip install --user -qq git+https://github.com/barronh/aqmbc.git`
2.  Download the gcbc_example.py from the Examples site
  * Use the link in the example.
  * Move the script to a working directory.
  * The rest of the example assumes you are in that working directory.
3.  Run gcbc_example.py with no edits.
  * shell `python gcbc_example.py`
  * notebook `%run gcbc_example.py`
4.  Edit gcbc_example.py
  *  Change domain definition.
    * Change `gdnam='12US1'` to `gdnam='OTHER'` (name must exist in ~/GRIDDESC)
    * Add keyword `gdpath=os.path.expanduser('~/GRIDDESC')`
  *  Add more months to inpaths (right now just Apr and Jul)
    * Add 'OutputDir/GEOSChem.SpeciesConc.20190101_0000z.nc4',
    * Add 'OutputDir/GEOSChem.SpeciesConc.20190201_0000z.nc4',
    * Add 'OutputDir/GEOSChem.SpeciesConc.20190301_0000z.nc4',
    * Add 'OutputDir/GEOSChem.SpeciesConc.20190501_0000z.nc4',
    * Add 'OutputDir/GEOSChem.SpeciesConc.20190601_0000z.nc4',
    * Add 'OutputDir/GEOSChem.SpeciesConc.20190801_0000z.nc4',
    * Add 'OutputDir/GEOSChem.SpeciesConc.20190901_0000z.nc4',
    * Add 'OutputDir/GEOSChem.SpeciesConc.20191001_0000z.nc4',
    * Add 'OutputDir/GEOSChem.SpeciesConc.20191001_0000z.nc4',
  *  Change exprpaths
    * Remove gcbench14_o3so4.expr
    * Add: gcnc_usstd_airmolden.expr
    * Add: gc14_to_cb6r5.expr
    * Add: gc14_to_cb6mp.expr
    * Add: gc14_soas_to_ae7.expr
5.  Rerun gcbc_example.py
  * shell `python gcbc_example.py`
  * notebook `%run gcbc_example.py`
