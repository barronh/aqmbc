.. aqmbc documentation master file, created by
   sphinx-quickstart on Fri Mar 17 21:46:43 2023.

aqmbc User's Guide
===================

`aqmbc` is a python tool to make boundary conditions for CMAQ.

The key value of `aqmbc` is to provide a single interface to multiple models.
This makes maintaining a system easy to acheive and hopefully easy to use.

Currently, aqmbc supports:

* GEOS-Chem v12 and v14
* CMAQ (Hemispheric or Regional)
* NASA GMAO's GEOS-CF
* RAQMS

To do:

* aqmbc would like to support WACCM, AM4, and CAMS
* A future version will allow for explicit output of CAMx readable boundary
  conditions. For now, use the cmaq2camx tools to convert these files.


Getting Started
---------------

The best way to get started is to install (see below) and then explore the
:doc:`auto_examples/index`. The examples include data download, processing,
and create summaries of the data (figures and tables).


Installation
------------

Right now, you can get the latest version of `aqmbc` with this command.

.. code-block::

    pip install git+https://github.com/barronh/aqmbc.git


Issues
------

If you're having any problems, open an issue on github.

https://github.com/barronh/aqmbc/issues


Quick Links
-----------

* :doc:`auto_examples/index`
* :doc:`api/aqmbc`


.. toctree::
   :maxdepth: 2
   :hidden:
   :caption: Table of Contents

   self
   auto_examples/index
   modifyexamples
   configexample
   api/aqmbc
   api/modules
