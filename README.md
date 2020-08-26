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

## Process-based (mechanistic) crop models

Process-based crop models are increasingly used in agricultural decision making. In the last two decades, they have intensively contributed to crop management, environmental impact studies, climate risk assessment and climate change adaptation analysis. The number of crop models and model users is increasing and several studies have been intensively focused on model development, i.e. building or improving the science behind the model and multi-model ensembles. [APSIM](https://www.apsim.info/) (Agricultural Production Systems Simulator) and [DSSAT](https://dssat.net/) (Decision Support System for Agrotechnology Transfer) are the two major crop models used by the scientific community worldwide.

### APSIM

#### What is APSIM?

The Agricultural Production Systems Simulator (APSIM) is internationally recognised as a highly advanced platform for modelling and simulation of agricultural systems. It contains a suite of modules that enable the simulation of systems for a diverse range of crop, animal, soil, climate and management interactions. APSIM is undergoing continual development, with new capability added to regular releases of official versions. Its development and maintenance is underpinned by rigorous science and software engineering standards. The [APSIM Initiative](https://www.apsim.info/about-us/) has been established to promote the development and use of the science modules and infrastructure software of APSIM.

APSIM is structured around plant, soil and management modules. These modules include a diverse range of crops, pastures and trees, soil processes including water balance, N and P transformations, soil pH, erosion and a full range of management controls. APSIM resulted from a need for tools that provided accurate predictions of crop production in relation to climate, genotype, soil and management factor while addressing the long-term resource management issues.

The APSIM modelling framework is made up of the following components:

- A set of biophysical modules that simulate biological and physical processes in farming systems.
- A set of management modules that allow the user to specify the intended management rules that characterise the scenario being simulated and that control the simulation.
- Various modules to facilitate data input and output to and from the simulation.
- A simulation engine that drives the simulation process and facilitates communication between the independent modules.

In addition to the science and infrastructure elements of the APSIM simulator, the framework also includes:

- Various user interfaces for model construction, testing and application
- Various interfaces and association database tools for visualisation and further analysis of output.
- Various model development, testing and documentation tools.
- A web based user and developer support facility that provides documentation, distribution and defect/change request tracking.

#### What is a MET File

The APSIM Met module provided daily meteorological information to all modules within an APSIM simulation. The APSIM Met Module requires parameters to specify the climate of the site for each APSIM time step. This information is included in a [MET file](https://www.apsim.info/documentation/model-documentation/infrastructure-and-management-documentation/met/).

APSIM MET files consist of a section name, which is always *weather.met.weather*, several constants consisting of *name = value*, followed by a headings line, a units line and then the data. Spacing in the file is not relevant. Comments can be inserted using the ! character.

At a minimum three constants must be included in the file: **latitude**, **tav** and **amp**. The last two of these refer to the annual average ambient temperature and annual amplitude in mean monthly temperature. Full details about tav and amp can be found here: [tav_amp](https://www.apsim.info/wp-content/uploads/2019/10/tav_amp-1.pdf).

The MET file must also have a year and day column (or date formatted as *yyyy/mm/dd*), solar radiation (*MJ/m2*), maximum temperature (*&deg;C*), minimum temperature (*&deg;C*) and rainfall (*mm*). The column headings to use for these are year and day (or date), radn, maxt, mint, rain. Other constants or columns can be added to the file. These then become available to APSIM as variables that can be reported or used in manager script.

While *point* data is usually available in MET format at the [SILO](https://www.longpaddock.qld.gov.au/silo/gridded-data/) webpage, *gridded data* is provided in NetCDF file format which is difficult to store and convert to an input file readable by [APSIM](https://www.apsim.info) or other crop models. **BestiaPop** takes care of generating the required input files for APSIM.

### DSSAT

#### What is DSSAT?

The Decision Support System for Agrotechnology Transfer (DSSAT) is a software application program that comprises crop simulation models for over 42 crops (as of Version 4.7.5) as well as tools to facilitate effective use of the models. The tools include database management programs for soil, weather, crop management and experimental data, utilities, and application programs. The crop simulation models simulate growth, development and yield as a function of the soil-plant-atmosphere dynamics.

DSSAT and its crop simulation models have been used for a wide range of applications at different spatial and temporal scales. This includes on-farm and precision management, regional assessments of the impact of climate variability and climate change, gene-based modeling and breeding selection, water use, greenhouse gas emissions, and long-term sustainability through the soil organic carbon and nitrogen balances. DSSAT has been in used by more than 16,500 researchers, educators, consultants, extension agents, growers, and policy and decision makers in over 174 countries worldwide.

The crop models require daily weather data, soil surface and profile information, and detailed crop management as input. Crop genetic information is defined in a crop species file that is provided by DSSAT and cultivar or variety information that should be provided by the user. Simulations are initiated either at planting or prior to planting through the simulation of a bare fallow period. These simulations are conducted at a daily step or in some cases, at an hourly time step depending on the process and the crop model. At the end of each day, the plant and soil water, nitrogen, phosphorus, and carbon balances are updated, as well as the crop’s vegetative and reproductive development stage.

#### What is a WHT File

The three key variables in a DSSAT weather file are precipitation, minimum and maximum temperature and solar radiation. [*.WHT](http://www.ukm.my/seaclid-cordex/files/Rice%20Pilot%20Project%20Workshop/PRESENTATION-PDF/20140922-1430-1445-Weather%20data%20format%20of%20%20DSSAT%20model--%20Attachai.pdf) (analogous as *.MET in APSIM) has been defined as the standardized file format for DSSAT. The **latitude**,**longitude**, **tav** and **amp** parameters are also mandatory for these files.

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

#### Generate MET output files (for APSIM) using SILO cloud API, for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2015 to 2016

> **Note**:
    * the resulting MET files will be placed in the output directory specified by "-o"
    * add *-ot csv* at the end of the script if a csv is required as output file. The code generates MET files by default.

```powershell
python bestiapop.py -a generate-climate-file -s silo -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot met
```

#### Generate WHT output files (for DSSAT) output files using SILO cloud API, for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2015 to 2016

```powershell
python bestiapop.py -a generate-climate-file -s silo -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot wht
```

#### Generate MET output files (for APSIM) using NASAPOWER cloud API, for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2003 to 2016

```powershell
python bestiapop.py -a generate-climate-file -s nasapower -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot met
```

#### Generate MET output files (for APSIM) from local disk for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 1990 to 2010

> **Note**: all the required NetCDF files should be placed in a single directory which is then referenced with the *-i* parameter. The directory should have the following structure:

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

### Download NetCDF4 Files

#### Download SILO climate files for years 2010 to 2018 for and maximum air temperature

This command will **only** download the file from the cloud, it won't perform any further processing.

> **NOTE**: a year range must be separated by a dash, whereas multiple climate variables are separated by spaces

```powershell
python bestiapop.py -a download-nc4-file --data-source silo -y "2010-2018" -c "daily_rain max_temp" -o C:\some\output\folder
```

## PARALLEL COMPUTING

**BestiaPop** as of version 2.5 comes with parallel processing for multicore systems by leveraging python's multiprocessing library. Not all actions have implemented this functionality yet but they will be added progressively. To enable multiprocessing just pass in the `-m` flag to the `bestiapop.py` command. By default it will leverage **all your cores** (whether physical or logical).

Parallelization is done based on the coordinate variable (whether *latitude* or *longitude*) that has the widest spread (highest data points count). This means, you will rip the benefits of multiple cores when your datasets reference wide ranges of *lat* or *lon* variables. 


> **NOTE**: When generating *MET* files *from locally available NetCDF4 files* based on SILO data, you might experience mixed results since SILO provides NetCDF4 files split into `year-variable` and *MET* files require multiple *years* in the same MET file. As of Jun 2020, SILO has refactored all its NetCDF4 files to perform better when extracting spatial data points rather than time-based data points. This effectively means that it is slower to extract data **for all days of the year** from NetCDF4 files, for a single combination of lat/lon, than it is to extract data for all combinations of lat/lon **for a single day**. Since SILO NetCDF4 files are split into `year-variable` units you will always have to extract data from different files when using multiple years.

### EXAMPLE: Generate MET output files (for APSIM) from SILO Cloud API global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2015 to 2016

```powershell
python bestiapop.py -a generate-climate-file -s silo -y "2008-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -m
```

Here, the `-m` at the end will engage multiple cores to process the tasks. If you have 8 available cores it will create 8 separate processes to download the data from the cloud and will then use 8 separate processes to generate the output files.

# Main References (The following papers implemented this code and can be used as references)

1. Ojeda JJ, Eyshi Rezaei E, Remeny TA, Webb MA, Webber HA, Kamali B, Harris RMB, Brown JN, Kidd DB, Mohammed CL, Siebert S, Ewert F, Meinke H (2019) Effects of soil- and climate data aggregation on simulated potato yield and irrigation water demand. Science of the Total Environment. 710, 135589. doi:10.1016/j.scitotenv.2019.135589

# Package references

1. https://registry.opendata.aws/silo/ 
2. https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f
3. http://xarray.pydata.org/en/stable/dask.html 
