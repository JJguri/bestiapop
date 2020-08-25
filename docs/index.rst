:Authors: 
  * Diego Perez (@darkquassar)

**********
BestiaPop 
**********

**Date**: |today| **Version**: |version|

.. module:: bestiapop

.. toctree::
    :maxdepth: 3
    :titlesonly:

    getting_started/usage
    api_reference/api
    paper/paper

BestiaPop: A python script for climate data extraction and processing
=====================================================================

Climate data is an essential input for crop models to predict crop growth and development using site-specific (point) or gridded climate
data. While *point* data is currently available in MET format, *gridded data* is provided in NetCDF file format which is difficult to store and
convert to an input file readable by `APSIM`_ or other crop models. We developed **bestiapop** (a spanish word that translates to *pop beast*),
a Python script (*soon to become a package*) which allows model users to automatically download SILO's (Scientific Information for Land Owners)
gridded climate data in MET file format that can then be inputted by APSIM for **crop modelling predictions**. The package offers the
possibility to select a range of grids (5 km × 5 km resolution) and years producing various types of output files: csv, MET and soon TSV and
SQLite.

Although the code downloads data from the `SILO`_ database, it could be applied to other climate data sources e.g. `NASA POWER`_ as was impplemented in R using `APSIM CRAN`_.

Authors
~~~~~~~

* **Data Analytics Specialist & Code Developer**: Diego Perez (@darkquassar / `https://linkedin.com/in/diegope`_)

* **Data Scientist & Agricultural Systems Modeller**: Jonathan Ojeda (@JJguri / `https://www.jojeda.com/`_)

Acknowledgements
~~~~~~~~~~~~~~~~

* Aasdf
* fasdf
* fdfsdfsd


Description
===========

What is \ `APSIM`_\?
~~~~~~~~~~~~~~~~~~~~

The Agricultural Production Systems sIMulator (APSIM) is internationally recognised as a highly advanced platform for modelling and simulation of agricultural systems. It contains a suite of modules that enable the simulation of systems for a diverse range of crop, animal, soil, climate and management interactions. APSIM is undergoing continual development, with new capability added to regular releases of official versions. Its development and maintenance is underpinned by rigorous science and software engineering standards. The `APSIM Initiative`_ has been established to promote the development and use of the science modules and infrastructure software of APSIM.

.. _APSIM: https://www.apsim.info
.. _SILO: https://www.longpaddock.qld.gov.au/silo/gridded-data/
.. _NASA POWER: https://power.larc.nasa.gov/
.. _APSIM CRAN: https://cran.r-project.org/web/packages/APSIM/APSIM.pdf
.. _`https://linkedin.com/in/diegope`: https://linkedin.com/in/diegope
.. _`https://www.jojeda.com/`: https://www.jojeda.com/
.. _APSIM Initiative: https://www.apsim.info/about-us/

What is a MET file?
~~~~~~~~~~~~~~~~~~~

The APSIM Met module provided daily meteorological information to all modules within an APSIM simulation. The APSIM Met Module requires parameters to specify the climate of the site for each APSIM time step. This information is included in a `MET file`_.

APSIM MET files consist of a section name, which is always *weather.met.weather*, several constants consisting of *name = value*, followed by a headings line, a units line and then the data. Spacing in the file is not relevant. Comments can be inserted using the !character.

At a minimum three constants must be included in the file: **latitude**, **tav** and **amp**. The last two of these refer to the annual average ambient temperature and annual amplitude in mean monthly temperature. Full details about tav and amp can be found here: `tav_amp`_.

The MET file must also have a year and day column (or date formatted as
*yyyy/mm/dd*), solar radiation (*MJ/m2*), maximum temperature (*°C*),
minimum temperature (*°C*) and rainfall (*mm*). The column headings to
use for these are year and day (or date), radn, maxt, mint, rain. Other
constants or columns can be added to the file. These then become
available to APSIM as variables that can be reported or used in manager
script.

Can I use this script to generate climate files for other process-based crop models?
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

So far, the code is producing CSV or MET files to be directly used by
APSIM, however, it also could be applied to produce input climate data
for other crop models such as `DSSAT`_ and `STICS`_. **Decision Support
System for Agrotechnology Transfer** (DSSAT) is a software application
program that comprises dynamic crop growth simulation models for over 40
crops. DSSAT is supported by a range of utilities and apps for weather,
soil, genetic, crop management, and observational experimental data, and
includes example data sets for all crop models. The STICS (**Simulateur
mulTIdisciplinaire pour les Cultures Standard**, or *multidisciplinary
simulator for standard crops*) model is a dynamic, generic and robust
model aiming to simulate the soil-crop-atmosphere system.

About SILO
==========

SILO is a database of Australian climate data from 1889 to the present. It provides daily meteorological datasets for a range of climate variables in ready-to-use formats suitable for biophysical modelling, research and climate applications.

NetCDF and API data variations from SILO
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are particular years where some data may be different when you read the data from a `NetCDF SILO file`, as opposed to reading the same data from the `SILO API`. Below is a detailed description of the SILO team as to why this might happen.

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

> Differences between the API and NetCDF values only occur when a datum fails one of the aforementioned range checks, for example, when the interpolated maximum temperature is lower than the interpolated minimum temperature. Such situations typically arise due to errors in the observed data (leading to errors in the gridded surface), or in regions where there are very few recording stations. We expect there to be more errors in the gridded surfaces for the early years, as there were relatively few stations recording data (other than rainfall) before 1957. Plots showing the number of stations recording each variable as a function of time are provided in our 2001 paper (see the [Publications section on SILO](https://www.longpaddock.qld.gov.au/silo/about/publications-references/)).

More information
~~~~~~~~~~~~~~~~

`https://www.jojeda.com/project/project-6/`_

Installation
============

1. Clone this repo
2. Install required packages.

Using Anaconda (preferred)
~~~~~~~~~~~~~~~~~~~~~~~~~~

Create Custom Environment
^^^^^^^^^^^^^^^^^^^^^^^^^

1. ``conda create -y --name bestiapop python==3.7``
2. ``conda install --name bestiapop -y -c conda-forge --file requirements.txt``
3. ``conda activate bestiapop``

In you Base Environment
^^^^^^^^^^^^^^^^^^^^^^^

This option might take a *very* long time due to the multiple
dependencies that Anaconda might have to solve on your default **base
environment**. Preferably, install using the next method which creates a
custom environment.

1. Open your anaconda prompt for the *base* environment (default)
2. ``conda install -y -c conda-forge --file require``

Using pip
~~~~~~~~~

1. Change directory to the repo folder
2. ``pip install -r requirements.txt``

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
