# BestiaPop: A python script for climate data extraction and processing

[![Docs](https://bestiapop.readthedocs.io/en/latest/?badge=latest)](https://bestiapop.readthedocs.io/en/latest/?badge=latest)

Climate data is an essential input for crop models to predict crop growth and development using site-specific (point) or gridded climate data. While *point* data is currently available in MET format, *gridded data* is provided in NetCDF file format which is difficult to store and convert to an input file readable by [APSIM](https://www.apsim.info) or other crop models. We developed **bestiapop** (a spanish word that translates to *pop beast*), a Python script (*soon to become a package*) which allows model users to automatically download SILO's (Scientific Information for Land Owners) gridded climate data in MET file format that can then be inputted by APSIM for **crop modelling predictions**. The package offers the possibility to select a range of grids (5 km × 5 km resolution) and years producing various types of output files: csv, MET and soon TSV and SQLite.

Although the code downloads data from the [SILO](https://www.longpaddock.qld.gov.au/silo/gridded-data/) database, it could be applied to other climate data sources e.g. [NASA POWER](https://power.larc.nasa.gov/) as was implemented in R using [APSIM CRAN](https://cran.r-project.org/web/packages/APSIM/APSIM.pdf).

### Authors

**Data Analytics Specialist & Code Developer**: Diego Perez (@darkquassar / https://linkedin.com/in/diegope)

**Data Scientist & Agricultural Systems Modeller**: Jonathan Ojeda (@JJguri / https://www.jojeda.com/)

### Description

**What is [APSIM](https://www.apsim.info)?**

The Agricultural Production Systems sIMulator (APSIM) is internationally recognised as a highly advanced platform for modelling and simulation of agricultural systems. It contains a suite of modules that enable the simulation of systems for a diverse range of crop, animal, soil, climate and management interactions. APSIM is undergoing continual development, with new capability added to regular releases of official versions. Its development and maintenance is underpinned by rigorous science and software engineering standards. The [APSIM Initiative](https://www.apsim.info/about-us/) has been established to promote the development and use of the science modules and infrastructure software of APSIM.

**What is a MET file?**

The APSIM Met module provided daily meteorological information to all modules within an APSIM simulation. The APSIM Met Module requires parameters to specify the climate of the site for each APSIM time step. This information is included in a [MET file](https://www.apsim.info/documentation/model-documentation/infrastructure-and-management-documentation/met/).

APSIM MET files consist of a section name, which is always *weather.met.weather*, several constants consisting of *name = value*, followed by a headings line, a units line and then the data. Spacing in the file is not relevant. Comments can be inserted using the ! character.

At a minimum three constants must be included in the file: **latitude**, **tav** and **amp**. The last two of these refer to the annual average ambient temperature and annual amplitude in mean monthly temperature. Full details about tav and amp can be found here: [tav_amp](https://www.apsim.info/wp-content/uploads/2019/10/tav_amp-1.pdf).

The MET file must also have a year and day column (or date formatted as *yyyy/mm/dd*), solar radiation (*MJ/m2*), maximum temperature (*&deg;C*), minimum temperature (*&deg;C*) and rainfall (*mm*). The column headings to use for these are year and day (or date), radn, maxt, mint, rain. Other constants or columns can be added to the file. These then become available to APSIM as variables that can be reported or used in manager script.

**Can I use this script to generate climate files for other process-based crop models?**

So far, the code is producing CSV or MET files to be directly used by APSIM, however, it also could be applied to produce input climate data for other crop models such as [DSSAT](https://dssat.net/) and [STICS](https://www6.paca.inrae.fr/stics_eng/About-us/Stics-model-overview). Decision Support System for Agrotechnology Transfer (DSSAT) is a software application program that comprises dynamic crop growth simulation models for over 40 crops. DSSAT is supported by a range of utilities and apps for weather, soil, genetic, crop management, and observational experimental data, and includes example data sets for all crop models. The STICS (Simulateur mulTIdisciplinaire pour les Cultures Standard, or multidisciplinary simulator for standard crops) model is a dynamic, generic and robust model aiming to simulate the soil-crop-atmosphere system.

### More information

https://www.jojeda.com/project/project-6/

## Installation

1. Clone this repo
2. Install required packages.

### Using pip

1. Change directory to the repo folder
2. `pip install -r requirements.txt`

### Using Anaconda

#### In you Base Environment

This option might take a *very* long time due to the multiple dependencies that Anaconda might have to solve on your default **base environment**. Preferably, install using the next method which creates a custom environment.

1. Open your anaconda prompt for the *base* environment (default)
2. `conda install -y -c conda-forge --file requirements.txt`

#### Create Custom Environment

1. `conda create -y --name bestiapop python==3.7`
2. `conda install --name bestiapop -y -c conda-forge --file requirements.txt`
3. `conda activate bestiapop`

# Usage

## Examples

### Download SILO climate files for years 2010 to 1028 and the variables daily_rain and max_temp

This command will **only** download the file from AWS, it won't perform any further processing.
**NOTE**: *a year range must be separated by a dash, whereas multiple climate variables are separated by spaces*

```powershell
python bestiapop.py -a download-silo-file -y "2010-2018" -c "daily_rain max_temp" -o C:\some\output\folder
```

### Generate MET output files from AWS S3 for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016

**Note**:

* the resulting MET files will be placed in the output directory specified by "-o"
* add *-ou csv* at the end of the script if a csv is required as output file. The code generates MET files by default.

```powershell
python bestiapop.py -a generate-met-file -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\
```

### Generate MET output files from Local Disk for Radiation, Min Temperature, Max Temperature and Daily Rain for years 1990 to 2010

**Note**:

* all the required NetCDF files should be placed in a single directory which is then referenced with the *--input* parameter. The directory should have the following structure:

```c
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
```

```powershell
python bestiapop.py -a generate-met-file -y "1990-2010" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -i C:\some\input\folder\with\all\netcdf\files\ -o C:\some\output\folder\
```

### Generate a CSV containing daily_rain data for year 2015 for a range of lat/lon

```powershell
python bestiapop.py -a convert-nc4-to-csv -y 2015 -c daily_rain -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\folder
```

## PARALLEL COMPUTING 

**BestiaPop** as of version 2.5 comes with parallel processing for multicore systems by leveraging python's multiprocessing library. Not all actions have implemented this functionality yet but they will be added progressively. To enable multiprocessing just pass in the `-m` flag to the `bestiapop.py` command. By default it will leverage **all your cores** (whether physical or logical).

Parallelization is done based on the *year* variable. This means, you will rip the benefits of multiple cores when your datasets reference a long time slice (i.e. at least 4+ years). When generating *MET* files it is unlikely that you will require more than 4 to 6 climate variables, whereas it is more likely that you would like to generate files that go quite far back in time, needing to process data from 10 to 30 years. Since SILO NetCDF4 files are split into `year-variable` units you will always have to extract data from different files when using multiple years. 

You might not perceive the benefits of multiprocessing when using the option to process NetCDF4 files in the cloud, since the bottleneck in this case is determined by your internet bandwidth and python's `xarray` and `fsspec` libraries' speed to read from the remote files. However, even in this scenario you will be able to process multiple years at a time without having to wait for sequential processing tasks. 

Real performance improvements from using multiprocessing can be achieved when processing local NetCDF4 files, i.e. when passing the `-i / --input-dir` parameter to `bestiapop.py`.

### MULTIPROCESSING CASE 1 - Generate MET output files from AWS S3 for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016

```powershell
python bestiapop.py -a generate-met-file -y "2008-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -m
```

Here, the `-m` at the end will engage multiple cores to process the tasks. If you have 8 available cores 

## Main References (The following papers implemented this code and can be used as references)

1. Ojeda JJ, Eyshi Rezaei E, Remeny TA, Webb MA, Webber HA, Kamali B, Harris RMB, Brown JN, Kidd DB, Mohammed CL, Siebert S, Ewert F, Meinke H (2019) Effects of soil- and climate data aggregation on simulated potato yield and irrigation water demand. Science of the Total Environment. 710, 135589. doi:10.1016/j.scitotenv.2019.135589
2. Ojeda JJ, Perez D, Eyshi Rezaei E (2020) The BestiaPop - A Python package to automatically generate gridded climate data for crop models. APSIM Symposium, Brisbane, Australia.

## Package references

1. https://registry.opendata.aws/silo/ 
2. https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f
3. http://xarray.pydata.org/en/stable/dask.html 
