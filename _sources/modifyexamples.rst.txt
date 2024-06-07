aqmbc Modify Examples
=====================

The process of testing and then updating the examples is described in detail below. I use the GEOS-Chem Benchmark as an example. This describes the entire process for modifying an example. Where a command is executed, it will be shown in shell (bash or csh) and IPython/Jupyter.

#. Install software (requires python3):

   .. code-block:: bash

       pip install --user -qq git+https://github.com/barronh/aqmbc.git

   .. code-block:: ipython

       %pip install --user -qq git+https://github.com/barronh/aqmbc.git

#. Download the gcbc_example.py from the Examples site

   * Use the link in the example.
   * Move the script to a working directory.
   * The rest of the example assumes you are in that working directory.

#. Run gcbc_example.py with no edits.

   .. code-block:: bash

       python gcbc_example.py

   .. code-block:: ipython

       %run gcbc_example.py

#. Edit gcbc_example.py

   *  Change domain definition.

     * Change `gdnam='12US1'` to `gdnam='OTHER'` (*name must exist in ~/GRIDDESC*)

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

     * To see available expressions, run `aqmbc.exprlib.avail()` in a python environment

     * Remove `'gcbench14_o3so4.expr',`

     * Add: `'gcnc_usstd_airmolden.expr',`

     * Add: `'gc14_to_cb6r5.expr',`

     * Add: `'gc14_to_cb6mp.expr',`

     * Add: `'gc14_soas_to_ae7.expr',`

#. Rerun gcbc_example.py

   .. code-block:: bash

       python gcbc_example.py

   .. code-block:: ipython

       %run gcbc_example.py

