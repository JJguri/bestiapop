# BestiaPop: A python package to automate the extraction and processing of climate data for crop modelling

[![Documentation Status](https://readthedocs.org/projects/bestiapop/badge/?version=latest)](https://bestiapop.readthedocs.io/en/latest/?badge=latest&style=plastic)

Climate data is an essential input for crop models to predict crop growth and development using site-specific (point) or gridded climate data. However, *Crop Modelling* software expects input data to be encapsulated in custom file formats (`MET`, `WHT`, etc.) which don't conform to a common standard and require various customizations, depending on the prediction engine that generates crop models. Moreover, source data providers like [SILO](https://www.longpaddock.qld.gov.au/silo/gridded-data/) or [NASA POWER](https://power.larc.nasa.gov/) are usually neutral in the type of data output files they provide as part of their API services which leads to a gap between source *raw* data and *processed* data required by crop modelling suites to develop their models. We developed **BestiaPop** (a spanish word that translates to *pop beast*), a Python package which allows model users to automatically download SILO's (Scientific Information for Land Owners) or NASAPOWER gridded climate data and convert this data to files that can be ingested by *Crop Modelling* software like APSIM or DSSAT. 

The package offers the possibility to select a range of grids (5 km × 5 km resolution) and years producing various types of output files: CSV, MET (for APSIM), WHT (for DSSAT) and soon JSON (which will become part of BestiaPop's API in the future).

Curently, the code downloads data from two different climate databases:

1. [SILO](https://www.longpaddock.qld.gov.au/silo/gridded-data/)
2. [NASA POWER](https://power.larc.nasa.gov/)

## Authors

### Core Contributors

* **Data Analytics Specialist & Code Developer**: Diego Perez (@darkquassar / https://linkedin.com/in/diegope)

* **Data Scientist & Agricultural Systems Modeller**: Jonathan Ojeda (@JJguri / https://www.jojeda.com/)

### Acknowledgements

* This work was supported by the JM Roberts Seed Funding for Sustainable Agriculture 2020 and the Tasmanian Institute of Agriculture, University of Tasmania.
* SILO (Scientific Information for Land Owners), see: https://www.longpaddock.qld.gov.au/silo/about/
* NASAPOWER, see: https://power.larc.nasa.gov/

### Other Contributors

* Drew Holzworth ([helping](https://github.com/APSIMInitiative/ApsimX/issues/5423) integrate BestiaPop into APSIM, kudos!)

### More information

* https://www.jojeda.com/project/project-6/

## Crop Modelling Software

There are two major crop modelling suites in use by the scientific community in Australia: APSIM and DSSAT.

**[yoni to expand]**

### [APSIM](https://www.apsim.info): Agricultural Production Systems Simulator

#### What is APSIM?

The Agricultural Production Systems Simulator (APSIM) is internationally recognised as a highly advanced platform for modelling and simulation of agricultural systems. It contains a suite of modules that enable the simulation of systems for a diverse range of crop, animal, soil, climate and management interactions. APSIM is undergoing continual development, with new capability added to regular releases of official versions. Its development and maintenance is underpinned by rigorous science and software engineering standards. The [APSIM Initiative](https://www.apsim.info/about-us/) has been established to promote the development and use of the science modules and infrastructure software of APSIM.

#### What is a MET File

The APSIM Met module provided daily meteorological information to all modules within an APSIM simulation. The APSIM Met Module requires parameters to specify the climate of the site for each APSIM time step. This information is included in a [MET file](https://www.apsim.info/documentation/model-documentation/infrastructure-and-management-documentation/met/).

APSIM MET files consist of a section name, which is always *weather.met.weather*, several constants consisting of *name = value*, followed by a headings line, a units line and then the data. Spacing in the file is not relevant. Comments can be inserted using the ! character.

At a minimum three constants must be included in the file: **latitude**, **tav** and **amp**. The last two of these refer to the annual average ambient temperature and annual amplitude in mean monthly temperature. Full details about tav and amp can be found here: [tav_amp](https://www.apsim.info/wp-content/uploads/2019/10/tav_amp-1.pdf).

The MET file must also have a year and day column (or date formatted as *yyyy/mm/dd*), solar radiation (*MJ/m2*), maximum temperature (*&deg;C*), minimum temperature (*&deg;C*) and rainfall (*mm*). The column headings to use for these are year and day (or date), radn, maxt, mint, rain. Other constants or columns can be added to the file. These then become available to APSIM as variables that can be reported or used in manager script.

While *point* data is usually available in MET format at the [SILO](https://www.longpaddock.qld.gov.au/silo/gridded-data/) webpage, *gridded data* is provided in NetCDF file format which is difficult to store and convert to an input file readable by [APSIM](https://www.apsim.info) or other crop models. **BestiaPop** takes care of generating the required input files for APSIM.

#### Can I use this script to generate climate files for other process-based crop models?

So far, the code is producing CSV or MET files to be directly used by APSIM, however, it also could be applied to produce input climate data for other crop models such as [DSSAT](https://dssat.net/) and [STICS](https://www6.paca.inrae.fr/stics_eng/About-us/Stics-model-overview). Decision Support System for Agrotechnology Transfer (DSSAT) is a software application program that comprises dynamic crop growth simulation models for over 40 crops. DSSAT is supported by a range of utilities and apps for weather, soil, genetic, crop management, and observational experimental data, and includes example data sets for all crop models. The STICS (Simulateur mulTIdisciplinaire pour les Cultures Standard, or multidisciplinary simulator for standard crops) model is a dynamic, generic and robust model aiming to simulate the soil-crop-atmosphere system.

### DSSAT: ???

**[yoni to expand]** --> we need a section similar to what we wrote for APSIM but for DSSAT I guess...

# Installation

1. Clone this repo
2. Install required packages.

## Using pip

1. Change directory to the repo folder
2. `pip install -r requirements.txt`

## Using Anaconda

### In you Base Environment

This option might take a *very* long time due to the multiple dependencies that Anaconda might have to solve on your default **base environment**. Preferably, install using the next method which creates a custom environment.

1. Open your anaconda prompt for the *base* environment (default)
2. `conda install -y -c conda-forge --file requirements.txt`

### Create Custom Environment

1. `conda create -y --name bestiapop python==3.7`
2. `conda install --name bestiapop -y -c conda-forge --file requirements.txt`
3. `conda activate bestiapop`

# Usage

BestiaPop has three primary commands that you can pass in with the `-a` option: 

1. **generate-climate-file**: this command will generate an input file for crop modelling software depending on the output type (`-ot`) being `met` or `wht`. When `csv` is selected, a file containing all years in the sequence, with all requested variables, will be produced for each lat/lon combination.
2. **download-nc4-file**: this command downloads NetCDF4 files from SILO or NASAPOWER
3. **convert-nc4**: *currently not implemented*, this command will allow you to convert NetCDF4 files to other formats like `json` or `csv`.

## Examples

### Generate Climate File

#### Generate MET output files using SILO cloud API, for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016

> **Note**:
    * the resulting MET files will be placed in the output directory specified by "-o"
    * add *-ou csv* at the end of the script if a csv is required as output file. The code generates MET files by default.

```powershell
python bestiapop.py -a generate-climate-file -s silo -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot met
```

#### Generate WHT (for DSSAT) output files using SILO cloud API, for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016

```powershell
python bestiapop.py -a generate-climate-file -s silo -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot wht
```

#### Generate MET output files using NASAPOWER cloud API, for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2003 to 2016

```powershell
python bestiapop.py -a generate-climate-file -s nasapower -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot met
```

#### Generate MET output files from Local Disk for Radiation, Min Temperature, Max Temperature and Daily Rain for years 1990 to 2010

> **Note**: all the required NetCDF files should be placed in a single directory which is then referenced with the *--input* parameter. The directory should have the following structure:

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
python bestiapop.py -a generate-climate-file -y "1990-2010" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -i C:\some\input\folder\with\all\netcdf\files\ -o C:\some\output\folder\ -ot met
```

### Download NetCDF4 File

#### Download SILO climate files for years 2010 to 2018 and the variables daily_rain and max_temp

This command will **only** download the file from the cloud, it won't perform any further processing.

> **NOTE**: a year range must be separated by a dash, whereas multiple climate variables are separated by spaces

```powershell
python bestiapop.py -a download-nc4-file --data-source silo -y "2010-2018" -c "daily_rain max_temp" -o C:\some\output\folder
```

## PARALLEL COMPUTING 

**BestiaPop** as of version 2.5 comes with parallel processing for multicore systems by leveraging python's multiprocessing library. Not all actions have implemented this functionality yet but they will be added progressively. To enable multiprocessing just pass in the `-m` flag to the `bestiapop.py` command. By default it will leverage **all your cores** (whether physical or logical).

Parallelization is done based on the coordinate variable (whether *latitude* or *longitude*) that has the widest spread (highest data points count). This means, you will rip the benefits of multiple cores when your datasets reference wide ranges of *lat* or *lon* variables. 


> **NOTE**: When generating *MET* files *from locally available NetCDF4 files* based on SILO data, you might experience mixed results since SILO provides NetCDF4 files split into `year-variable` and *MET* files require multiple *years* in the same MET file. As of Jun 2020, SILO has refactored all its NetCDF4 files to perform better when extracting spatial data points rather than time-based data points. This effectively means that it is slower to extract data **for all days of the year** from NetCDF4 files, for a single combination of lat/lon, than it is to extract data for all combinations of lat/lon **for a single day**. Since SILO NetCDF4 files are split into `year-variable` units you will always have to extract data from different files when using multiple years. 

### EXAMPLE: Generate MET output files from SILO Cloud API for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016

```powershell
python bestiapop.py -a generate-climate-file -s silo -y "2008-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -m
```

Here, the `-m` at the end will engage multiple cores to process the tasks. If you have 8 available cores it will create 8 separate processes to download the data from the cloud and will then use 8 separate processes to generate the output files.

# Main References (The following papers implemented this code and can be used as references)

1. Ojeda JJ, Eyshi Rezaei E, Remeny TA, Webb MA, Webber HA, Kamali B, Harris RMB, Brown JN, Kidd DB, Mohammed CL, Siebert S, Ewert F, Meinke H (2019) Effects of soil- and climate data aggregation on simulated potato yield and irrigation water demand. Science of the Total Environment. 710, 135589. doi:10.1016/j.scitotenv.2019.135589
2. Ojeda JJ, Perez D, Eyshi Rezaei E (2020) The BestiaPop - A Python package to automatically generate gridded climate data for crop models. APSIM Symposium, Brisbane, Australia.

# Package references

1. https://registry.opendata.aws/silo/ 
2. https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f
3. http://xarray.pydata.org/en/stable/dask.html 
