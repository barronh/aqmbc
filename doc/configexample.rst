aqmbc Config File
======================

aqmbc can also be run from a command line using a configuration file. This section shows how to use aqmbc with GEOS-Chem and a config file. There are several prerequisites for this example:

* aqmbc must be installed
* GEOS-Chem version 14.0.1 simulation with simple organic aerosols (SOAS).
* BoundaryConditions extension enabled in HISTORY.rc with:

  * 'SpeciesBC_?ADV?             ',
  * 'Met_PMIDDRY'
  * 'Met_T'


Step 1: Create Run Directory
----------------------------

Create a run directory. `aqmbc` has a template option, which will export all its examples to a template run directory. You can then pick and choose which files to use. Below shows a template being created.

.. code-block:: bash

    python -m aqmbc -t run

After the folder was created, below is the directory structure where only the files used are highlighted.

.. code-block:: bash

    tree --charset=ASCII run
    run/
    |-- definitions
    |   |-- cf      # GEOS-CF definitions not used here
    |   |-- gc
    |   |   |   ...
    |   |   |-- gcnc_usstd_airmolden.expr
    |   |   |-- gc14_to_cb6r5.expr
    |   |   |-- gc14_to_cb6mp.expr
    |   |   `-- gc14_soas_to_ae7.expr
    |   `-- raqms   # RAQMS definitions not used here
    |-- gcncv14.cfg # GEOS-Chem v14 configuration
    |-- hcmaq.cfg   # Hemispheric-CMAQ Configuration file
    |-- raqms.cfg   # RAQMS model configuration file.
    `-- GRIDDESC    # IOAPI grid description file

Step 2: Edit
------------

Edit the configuration files to suite your application. Common examples:

1. Edit gcncv14.cfg to update the paths to your GEOS-Chem BoundaryConditions.
2. Edit gcncv14.cfg to use the domain of interest (12US1, 36US3, etc)
3. Edit gcncv14.cfg to output more days
4. Add a new domain to GRIDDESC for your CMAQ grid definition.
5. Edit `definitions/gc` to match your application.

If you used a different version of GEOS-Chem, there are two paths forward.

1. See if definitions for that version already exists.
2. Make definitions for your version. (if you do, please open an issue http://github.com/barronh/aqmbc/issues; and submit them).

Step 3: Run
-----------

.. code-block:: bash

    python -m aqmbc gcncv14.cfg


Alternative Configurations
--------------------------

Similar example configurations are provided for Hemispheric-CMAQ (`hcmaq.cfg`) and RAQMS (`raqms.cfg`).

* `hcmaq.cfg` is designed to work with 3D "CONC" files with all the species included from a larger domain.
* `raqms.cfg` is designed to work with the files provided by Brad Pierce at the University of Wisconsin.
