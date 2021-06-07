:Authors:
  * Diego Perez (@darkquassar)
  * Jonathan Ojeda

**********
BestiaPop 
**********

**Date**: |today| **Version**: |version|

.. module:: bestiapop

.. toctree::
    :maxdepth: 3
    :titlesonly:

    index
    getting_started/usage
    api_reference/api
    paper/paper

BestiaPop: A python package to automate the extraction and processing of climate data for crop modelling
========================================================================================================

Climate data is an essential input for crop models to predict crop growth and development using site-specific (point) or gridded climate data. However, *Crop Modelling* software expects input data to be encapsulated in custom file formats (``MET``, ``WTH``, etc.) which don't conform to a common standard and require various customizations, depending on the prediction engine that generates crop models. Moreover, source data providers like `SILO`_ or `NASA POWER`_ are usually neutral in the type of data output files they provide as part of their API services which leads to a gap between source *raw* data and *processed* data required by crop modelling suites to develop their models. We developed **BestiaPop** (a spanish word that translates to *pop beast*), a Python package which allows model users to automatically download SILO's (Scientific Information for Land Owners) or NASAPOWER gridded climate data and convert this data to files that can be ingested by *Crop Modelling* software like APSIM or DSSAT. 

The package offers the possibility to select a range of grids (5 km × 5 km resolution) and years producing various types of output files: CSV, MET (for APSIM), WTH (for DSSAT) and soon JSON (which will become part of BestiaPop's API in the future).

Curently, the code downloads data from two different climate databases:

1. `SILO`_
2. `NASA POWER`_

Authors
~~~~~~~

Core Contributors
+++++++++++++++++

* **Data Analytics Specialist & Code Developer**: Diego Perez (@darkquassar / `https://linkedin.com/in/diegope`_)

* **Data Scientist & Agricultural Systems Modeller**: Jonathan Ojeda (@JJguri / `https://www.jojeda.com/`_)

Acknowledgements
++++++++++++++++

* This work was supported by the JM Roberts Seed Funding for Sustainable Agriculture 2020 and the Tasmanian Institute of Agriculture, University of Tasmania.
* SILO (Scientific Information for Land Owners), see: https://www.longpaddock.qld.gov.au/silo/about/
* NASAPOWER, see: https://power.larc.nasa.gov

Other Contributors
++++++++++++++++++

* Drew Holzworth ([helping](https://github.com/APSIMInitiative/ApsimX/issues/5423) integrate BestiaPop into APSIM, kudos!)

More information
++++++++++++++++

* https://www.jojeda.com/project/project-6/

Crop Modelling Software
=======================

There are two major crop modelling suites in use by the scientific community in Australia: APSIM and DSSAT.

**[yoni to expand]**

`APSIM`_: Agricultural Production Systems Simulator 
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

What is APSIM?
++++++++++++++

The Agricultural Production Systems sIMulator (APSIM) is internationally recognised as a highly advanced platform for modelling and simulation of agricultural systems. It contains a suite of modules that enable the simulation of systems for a diverse range of crop, animal, soil, climate and management interactions. APSIM is undergoing continual development, with new capability added to regular releases of official versions. Its development and maintenance is underpinned by rigorous science and software engineering standards. The `APSIM Initiative`_ has been established to promote the development and use of the science modules and infrastructure software of APSIM.

.. _APSIM: https://www.apsim.info
.. _SILO: https://www.longpaddock.qld.gov.au/silo/gridded-data/
.. _NASA POWER: https://power.larc.nasa.gov/
.. _APSIM CRAN: https://cran.r-project.org/web/packages/APSIM/APSIM.pdf
.. _`https://linkedin.com/in/diegope`: https://linkedin.com/in/diegope
.. _`https://www.jojeda.com/`: https://www.jojeda.com/
.. _APSIM Initiative: https://www.apsim.info/about-us/

What is a MET file?
+++++++++++++++++++

The APSIM MET module provided daily meteorological information to all modules within an APSIM simulation. The APSIM Met Module requires parameters to specify the climate of the site for each APSIM time step. This information is included in a `MET file`_.

APSIM MET files consist of a section name, which is always *weather.met.weather*, several constants consisting of *name = value*, followed by a headings line, a units line and then the data. Spacing in the file is not relevant. Comments can be inserted using the ! character.

At a minimum three constants must be included in the file: **latitude**, **tav** and **amp**. The last two of these refer to the annual average ambient temperature and annual amplitude in mean monthly temperature. Full details about tav and amp can be found here: `tav_amp`_.

The MET file must also have a year and day column (or date formatted as *yyyy/mm/dd*), solar radiation (*MJ/m2*), maximum temperature (*&deg;C*), minimum temperature (*&deg;C*) and rainfall (*mm*). The column headings to use for these are year and day (or date), radn, maxt, mint, rain. Other constants or columns can be added to the file. These then become available to APSIM as variables that can be reported or used in manager script.

While *point* data is usually available in MET format at the `SILO`_ webpage, *gridded data* is provided in NetCDF file format which is difficult to store and convert to an input file readable by `APSIM`_ or other crop models. **BestiaPop** takes care of generating the required input files for APSIM.


Can I use this script to generate climate files for other process-based crop models?
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

**[yoni to expand/fix]**

So far, the code is producing CSV or MET files to be directly used by APSIM, however, it also could be applied to produce input climate data for other crop models such as `DSSAT`_ and `STICS`_. Decision Support System for Agrotechnology Transfer (DSSAT) is a software application program that comprises dynamic crop growth simulation models for over 40 crops. DSSAT is supported by a range of utilities and apps for weather, soil, genetic, crop management, and observational experimental data, and includes example data sets for all crop models. The STICS (Simulateur mulTIdisciplinaire pour les Cultures Standard, or multidisciplinary simulator for standard crops) model is a dynamic, generic and robust model aiming to simulate the soil-crop-atmosphere system.

DSSAT: ???
~~~~~~~~~~

**[yoni to expand]** --> we need a section similar to what we wrote for APSIM but for DSSAT I guess...

About SILO
==========

SILO is a database of Australian climate data from 1889 to the present. It provides daily meteorological datasets for a range of climate variables in ready-to-use formats suitable for biophysical modelling, research and climate applications.

NetCDF and API data variations from SILO
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are particular years where some data may be different when you read the data from a ``NetCDF SILO file``, as opposed to reading the same data from the ``SILO API``. Below is a detailed description of the SILO team as to why this might happen.

When you request point data at grid cell locations, the data is extracted from the relevant grid cell in the NetCDF files. This data is then passed through a simple filter that checks if each datum is within an acceptable range:

  * daily rainfall: 0 – 1300 mm
  * maximum temperature: -9 - 54 ᵒC
  * minimum temperature: -20 - 40 ᵒC
  * class A pan evaporation: 0 - 35 mm
  * solar radiation: 0 - 35 MJ/m2
  * vapour pressure: 0 - 43.2 hPa
  * maximum temperature > minimum temperature

If a given datum (or pair of data values for the Tmax > Tmin check) fails the check, it/they may be erroneous so SILO provides the long term daily mean(s) instead. This is represented by a number *75* in the value for a particular datum.

If you request data at station locations the same checks are done; the main difference is observed data are provided where possible, and gridded data are provided if observed data are not available on a given day(s).

  Differences between the API and NetCDF values only occur when a datum fails one of the aforementioned range checks, for example, when the interpolated maximum temperature is lower than the interpolated minimum temperature. Such situations typically arise due to errors in the observed data (leading to errors in the gridded surface), or in regions where there are very few recording stations. We expect there to be more errors in the gridded surfaces for the early years, as there were relatively few stations recording data (other than rainfall) before 1957. Plots showing the number of stations recording each variable as a function of time are provided in our 2001 paper (see the `Publications section on SILO <https://www.longpaddock.qld.gov.au/silo/about/publications-references/>`_).

More information
~~~~~~~~~~~~~~~~

`https://www.jojeda.com/project/project-6/`_

Installation
============

There are two ways to install BestiaPop

1. With **pip**
2. Cloning repo

1. Install using PIP
~~~~~~~~~~~~~~~~~~~~

1. ``pip install bestiapop`` --> This will install all required packages that BestiaPop needs to run as well
2. **Done!**, to use, sipmply type ``python -m bestiapop [args]`` :)

> **NOTE**: We recomend you install BestiaPop in an isolated environment created with *Anaconda* or *VirtualEnv*. If using *Anaconda* simply do ``conda create -y --name my_data_env python=3.7``

1. Install Cloning BestiaPop Repo
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. Clone this repo
2. Install required packages.

Using Anaconda (preferred)
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Create Custom Environment**

1. ``conda env create --name bestiapop --file environment.yml``
2. ``conda activate bestiapop``

Using pip
^^^^^^^^^

1. Change directory to the repo folder
2. ``pip install -r pip_requirements.txt``

Main References
===============

*The following papers implemented this code and can be used as references*

1. Ojeda JJ, Eyshi Rezaei E, Remeny TA, Webb MA, Webber HA, Kamali B,
   Harris RMB, Brown JN, Kidd DB, Mohammed CL, Siebert S, Ewert F,
   Meinke H (2019) Effects of soil- and climate data aggregation on
   simulated potato yield and irrigation water demand. Science of the
   Total Environment. 710, 135589. doi:10.1016/j.scitotenv.2019.135589
2. Ojeda JJ, Perez D, Eyshi Rezaei E (2020) The BestiaPop - A Python
   package to automatically generate gridded climate data for crop
   models. APSIM Symposium, Brisbane, Australia.

Package references
~~~~~~~~~~~~~~~~~~

1. `https://registry.opendata.aws/silo/`_
2. `https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f`_
3. `http://xarray.pydata.org/en/stable/dask.html`_


.. _`https://registry.opendata.aws/silo/`: https://registry.opendata.aws/silo/
.. _`https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f`: https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f
.. _`http://xarray.pydata.org/en/stable/dask.html`: http://xarray.pydata.org/en/stable/dask.html

.. _MET file: https://www.apsim.info/documentation/model-documentation/infrastructure-and-management-documentation/met/
.. _tav_amp: https://www.apsim.info/wp-content/uploads/2019/10/tav_amp-1.pdf
.. _DSSAT: https://dssat.net/
.. _STICS: https://www6.paca.inrae.fr/stics_eng/About-us/Stics-model-overview
.. _`https://www.jojeda.com/project/project-6/`: https://www.jojeda.com/project/project-6/
