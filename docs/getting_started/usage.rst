How to use BestiaPop
====================

BestiaPop has three primary commands that you can pass in with the ``-a`` option: 

1. ``generate-climate-file``: this command will generate an input file for crop modelling software depending on the output type (``-ot``) being ``met`` or ``wht``. When ``csv`` is selected, a file containing all years in the sequence, with all requested variables, will be produced for each lat/lon combination.
2. ``download-nc4-file``: this command downloads NetCDF4 files from SILO or NASAPOWER
3. ``convert-nc4``: *currently not implemented*, this command will allow you to convert NetCDF4 files to other formats like ``json`` or ``csv``.

Examples
--------

Generate Climate File
~~~~~~~~~~~~~~~~~~~~~

Generate MET output files using SILO cloud API, for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

   **NOTE**:

   -  the resulting MET files will be placed in the output directory specified by "-o"
   -  the "-ot" parameter specifies the output type: met, dssat, csv or json.

.. code-block:: batch

   python bestiapop.py -a generate-climate-file -s silo -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot met

Generate WHT (for DSSAT) output files using SILO cloud API, for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: batch

   python bestiapop.py -a generate-climate-file -s silo -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot wht

Generate MET output files using NASAPOWER cloud API, for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2003 to 2016
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

.. code-block:: batch

   python bestiapop.py -a generate-climate-file -s nasapower -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot met

Generate MET output files from Local Disk for Radiation, Min Temperature, Max Temperature and Daily Rain for years 1990 to 2010
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

   **NOTE**:

   -  all the required NetCDF files should be placed in a single directory which is then referenced with the *--input* parameter. The directory should have the following structure:

.. code:: c

   C:\input\folder:
       \__ 1990.daily_rain.nc
       \__ 1990.max_temp.nc
       \__ 1990.min_temp.nc
       \__ 1990.radiation.nc
       \__ 1991.daily_rain.nc
       \__ 1991.max_temp.nc
       \__ 1991.min_temp.nc
       \__ 1991.radiation.nc
       \__ ...
       \__ 2010.daily_rain.nc
       \__ 2010.max_temp.nc
       \__ 2010.min_temp.nc
       \__ 2010.radiation.nc

.. code:: batch

   python bestiapop.py -a generate-climate-file -y "1990-2010" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -i C:\some\input\folder\with\all\netcdf\files\ -o C:\some\output\folder\ -ot met


Download NetCDF4 File
~~~~~~~~~~~~~~~~~~~~~

Download SILO climate files for years 2010 to 1028 and the variables daily_rain and max_temp
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

This command will **only** download the file from AWS, it won't perform any further processing. 

   **NOTE**: *a year range must be separated by a dash, whereas multiple climate variables are separated by spaces*

.. code:: batch

      python bestiapop.py -a download-nc4-file --data-source silo -y "2010-2018" -c "daily_rain max_temp" -o C:\some\output\folder


PARALLEL COMPUTING
------------------

**BestiaPop** as of version 2.5 comes with parallel processing for multicore systems by leveraging python's multiprocessing library. Not all actions have implemented this functionality yet but they will be added progressively. To enable multiprocessing just pass in the ``-m`` flag to the ``bestiapop.py`` command. By default it will leverage **all your cores** (whether physical or logical).

Parallelization is done based on the coordinate variable (whether *latitude* or *longitude*) that has the widest spread (highest data points count). This means, you will rip the benefits of multiple cores when your datasets reference wide ranges of *lat* or *lon* variables. 


   **NOTE**: When generating *MET* files *from locally available NetCDF4 files* based on SILO data, you might experience mixed results since SILO provides NetCDF4 files split into ``year-variable`` and *MET* files require multiple *years* in the same MET file. SILO has created the NetCDF4 files (as of 2020) to perform better when extracting spatial data points rather than time-based data points. This effectively means that it is slower to extract data **for all days of the year** from NetCDF4 files, for a single combination of lat/lon, than it is to extract data for all combinations of lat/lon **for a single day**. Since SILO NetCDF4 files are split into ``year-variable`` units you will always have to extract data from different files when using multiple years.

EXAMPLE: Generate MET output files from SILO Cloud API for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: batch

   python bestiapop.py -a generate-climate-file -s silo -y "2008-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -m

Here, the ``-m`` at the end will engage multiple cores to process the tasks. If you have 8 available cores it will create 8 separate processes to download the data from the cloud and will then use 8 separate processes to generate the output files.
