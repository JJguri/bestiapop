How to use BestiaPop
====================

Examples
--------

Download SILO climate files for years 2010 to 1028 and the variables daily_rain and max_temp
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This command will **only** download the file from AWS, it won't perform
any further processing. **NOTE**: *a year range must be separated by a
dash, whereas multiple climate variables are separated by spaces*

.. code:: powershell

   python bestiapop.py -a download-silo-file -y "2010-2018" -c "daily_rain max_temp" -o C:\some\output\folder

Generate MET output files from AWS S3 for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Note**:

-  the resulting MET files will be placed in the output directory
   specified by "-o"
-  add *-ou csv* at the end of the script if a csv is required as output
   file. The code generates MET files by default.

.. code:: powershell

   python bestiapop.py -a generate-met-file -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\

Generate MET output files from Local Disk for Radiation, Min Temperature, Max Temperature and Daily Rain for years 1990 to 2010
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Note**:

-  all the required NetCDF files should be placed in a single directory
   which is then referenced with the *--input* parameter. The directory
   should have the following structure:

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

.. code:: powershell

   python bestiapop.py -a generate-met-file -y "1990-2010" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -i C:\some\input\folder\with\all\netcdf\files\ -o C:\some\output\folder\

Generate a CSV containing daily_rain data for year 2015 for a range of lat/lon
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: powershell

   python bestiapop.py -a convert-nc4-to-csv -y 2015 -c daily_rain -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\folder

PARALLEL COMPUTING
------------------

**BestiaPop** as of version 2.5 comes with parallel processing for
multicore systems by leveraging python's multiprocessing library. Not
all actions have implemented this functionality yet but they will be
added progressively. To enable multiprocessing just pass in the ``-m``
flag to the ``bestiapop.py`` command. By default it will leverage **all
your cores** (whether physical or logical).

Parallelization is done based on the *year* variable. This means, you
will rip the benefits of multiple cores when your datasets reference a
long time slice (i.e. at least 4+ years). When generating *MET* files it
is unlikely that you will require more than 4 to 6 climate variables,
whereas it is more likely that you would like to generate files that go
quite far back in time, needing to process data from 10 to 30 years.
Since SILO NetCDF4 files are split into ``year-variable`` units you will
always have to extract data from different files when using multiple
years.

You might not perceive the benefits of multiprocessing when using the
option to process NetCDF4 files in the cloud, since the bottleneck in
this case is determined by your internet bandwidth and python's
``xarray`` and ``fsspec`` libraries' speed to read from the remote
files. However, even in this scenario you will be able to process
multiple years at a time without having to wait for sequential
processing tasks.

Real performance improvements from using multiprocessing can be achieved
when processing local NetCDF4 files, i.e. when passing the
``-i / --input-dir`` parameter to ``bestiapop.py``.

MULTIPROCESSING CASE 1 - Generate MET output files from AWS S3 for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code:: powershell

   python bestiapop.py -a generate-met-file -y "2008-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -m

Here, the ``-m`` at the end will engage multiple cores to process the
tasks. If you have 8 available cores

Main References (The following papers implemented this code and can be used as references)
------------------------------------------------------------------------------------------

1. Ojeda JJ, Eyshi Rezaei E, Remeny TA, Webb MA, Webber HA, Kamali B,
   Harris RMB, Brown JN, Kidd DB, Mohammed CL, Siebert S, Ewert F,
   Meinke H (2019) Effects of soil- and climate data aggregation on
   simulated potato yield and irrigation water demand. Science of the
   Total Environment. 710, 135589. doi:10.1016/j.scitotenv.2019.135589
2. Ojeda JJ, Perez D, Eyshi Rezaei E (2020) The BestiaPop - A Python
   package to automatically generate gridded climate data for crop
   models. APSIM Symposium, Brisbane, Australia.

Package references
------------------

1. `https://registry.opendata.aws/silo/`_
2. `https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f`_
3. `http://xarray.pydata.org/en/stable/dask.html`_

.. _`https://registry.opendata.aws/silo/`: https://registry.opendata.aws/silo/
.. _`https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f`: https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f
.. _`http://xarray.pydata.org/en/stable/dask.html`: http://xarray.pydata.org/en/stable/dask.html