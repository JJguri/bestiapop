# BestiaPop: A python package to automate the extraction and processing of climate data for crop modelling

[![Documentation Status](https://readthedocs.org/projects/bestiapop/badge/?version=latest)](https://bestiapop.readthedocs.io/en/latest/?badge=latest&flat-square)
![GitHub last commit](https://img.shields.io/github/last-commit/jjguri/bestiapop?style=flat-square)
![GitHub code size in bytes](https://img.shields.io/github/languages/code-size/jjguri/bestiapop?style=flat-square)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/bestiapop?style=flat-square)
![PyPI - Downloads](https://img.shields.io/pypi/dm/bestiapop?style=flat-square)
[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/JJguri/bestiapop/HEAD?filepath=sample-data%2FExampleMapsTasmania.ipynb)

Climate data is an essential input for crop models to predict crop growth and development using site-specific (point) or gridded climate data. However, *Crop Models* expects input data to be encapsulated in custom file formats (`MET`, `WTH`, etc.) which don't conform to a common standard and require various customizations, depending on the prediction engine that generates crop models. Moreover, source data providers like [SILO](https://www.longpaddock.qld.gov.au/silo/gridded-data/) or [NASA POWER](https://power.larc.nasa.gov/) are usually neutral in the type of data output files they provide as part of their API services which leads to a gap between source *raw* data and *processed* data required by crop modelling suites to develop their models. We developed **BestiaPop** (a spanish word that translates to *pop beast*), a Python package which allows model users to automatically download SILO's (Scientific Information for Land Owners) or NASAPOWER gridded climate data and convert this data to files that can be ingested by *Crop Models* like APSIM or DSSAT.

The package offers the possibility to select a range of grids (5 km × 5 km resolution) and years producing various types of output files: CSV, MET (for APSIM), WTH (for DSSAT) and soon JSON (which will become part of BestiaPop's API in the future).

Currently, the code downloads data from two different climate databases:

1. [SILO](https://www.longpaddock.qld.gov.au/silo/gridded-data/)
2. [NASA POWER](https://power.larc.nasa.gov/)

## Documentation

Check our docs! --> https://bestiapop.readthedocs.io/en/latest/

## Authors

### Core Contributors

* **Data Analytics Specialist & Code Developer**: Diego Perez (@darkquassar / https://linkedin.com/in/diegope)

* **Crop Physiologist & Crop Modeller**: Jonathan Ojeda (@JJguri / https://www.jojeda.com/ / j.ojeda@uq.edu.au)

### Acknowledgements

* This work was supported by the JM Roberts Seed Funding for Sustainable Agriculture 2020 and the Tasmanian Institute of Agriculture, University of Tasmania.
* SILO (Scientific Information for Land Owners), see: https://www.longpaddock.qld.gov.au/silo/about/
* NASAPOWER, see: https://power.larc.nasa.gov/

### Other Contributors

* Drew Holzworth ([helping](https://github.com/APSIMInitiative/ApsimX/issues/5423) integrate BestiaPop into APSIM, kudos!)

## How do I cite BestiaPop?

1. Give us a star in this repo and specify in your work (paper, report, etc) you have used 
_**Bestiapop**_
2. Ojeda JJ, Eyshi Rezaei E, Remeny TA, Webb MA, Webber HA, Kamali B, Harris RMB, Brown JN, Kidd DB, Mohammed CL, Siebert S, Ewert F, Meinke H (2020) Effects of soil- and climate data aggregation on simulated potato yield and irrigation water demand. Science of the Total Environment. 710, 135589. [link paper](https://www.sciencedirect.com/science/article/pii/S0048969719355846?casa_token=OGL6vAdGeLEAAAAA:dULqxjuvxgte1Fbi-TKw8lVkl-l5bjX5y0Zy0nuejczXqfSzv-O4O3mj17SuA4R5uelV-Akuqj0)
3. Ojeda JJ, Eyshi Rezaei E, Remenyi TA, Webber HA, Siebert S, Meinke H, Webb MA, Kamali B, Harris RMB, Kidd DB, Mohammed CL, 
McPhee J, Capuano J, Ewert F (2021) Implications of data aggregation method on crop model outputs – The case of irrigated potato systems in Tasmania, Australia. European Journal of Agronomy.126, 126276. [link paper](https://www.sciencedirect.com/science/article/pii/S1161030121000484?casa_token=b-63Jy5I_lMAAAAA:OOd81fokigyPEfmW7OmfyNC__I3oCyo1G3zgUHtfI1gL-LVPGdNR5tk53G1M_Y0w-Q934oKw74g)

# BestiaPop in action!

Here you can visualise BestiaPop in action

![image](/docs/_static/bpop_in_action.gif)

## Use it in Jupyter Notebook :)

If you would like to use BESTIAPOP in you Jupyter Notebook, you can! Please see the example [notebook](/sample-data/BestiaPop.ipynb)

**You can also try it live in Binder Project, just hit the badge mate! -->** [![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/JJguri/bestiapop/HEAD?filepath=sample-data%2FExampleMapsTasmania.ipynb)

> If you download files, you can retrieve them via the Jupyter interface :)

# Process-based (mechanistic) crop models

Process-based crop models are increasingly used in agricultural decision making. In the last two decades, they have intensively contributed to crop management, environmental impact studies, climate risk assessment and climate change adaptation analysis. The number of crop models and model users is increasing and several studies have been intensively focused on model development, i.e. building or improving the science behind the model and multi-model ensembles. [APSIM](https://www.apsim.info/) (Agricultural Production Systems Simulator) and [DSSAT](https://dssat.net/) (Decision Support System for Agrotechnology Transfer) are the two major crop models used by the scientific community worldwide.

## APSIM

### What is APSIM?

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

### What is a MET File

The APSIM Met module provided daily meteorological information to all modules within an APSIM simulation. The APSIM Met Module requires parameters to specify the climate of the site for each APSIM time step. This information is included in a [MET file](https://www.apsim.info/documentation/model-documentation/infrastructure-and-management-documentation/met/).

APSIM MET files consist of a section name, which is always *weather.met.weather*, several constants consisting of *name = value*, followed by a headings line, a units line and then the data. Spacing in the file is not relevant. Comments can be inserted using the ! character.

At a minimum three constants must be included in the file: **latitude**, **tav** and **amp**. The last two of these refer to the annual average ambient temperature and annual amplitude in mean monthly temperature. Full details about tav and amp can be found here: [tav_amp](https://www.apsim.info/wp-content/uploads/2019/10/tav_amp-1.pdf).

The MET file must also have a year and day column (or date formatted as *yyyy/mm/dd*), solar radiation (*MJ/m2*), maximum temperature (*&deg;C*), minimum temperature (*&deg;C*) and rainfall (*mm*). The column headings to use for these are year and day (or date), radn, maxt, mint, rain. Other constants or columns can be added to the file. These then become available to APSIM as variables that can be reported or used in manager script.

While *point* data is usually available in MET format at the [SILO](https://www.longpaddock.qld.gov.au/silo/gridded-data/) webpage, *gridded data* is provided in NetCDF file format which is difficult to store and convert to an input file readable by [APSIM](https://www.apsim.info) or other crop models. **BestiaPop** takes care of generating the required input files for APSIM.

## DSSAT

### What is DSSAT?

The Decision Support System for Agrotechnology Transfer (DSSAT) is a software application program that comprises crop simulation models for over 42 crops (as of Version 4.7.5) as well as tools to facilitate effective use of the models. The tools include database management programs for soil, weather, crop management and experimental data, utilities, and application programs. The crop simulation models simulate growth, development and yield as a function of the soil-plant-atmosphere dynamics.

DSSAT and its crop simulation models have been used for a wide range of applications at different spatial and temporal scales. This includes on-farm and precision management, regional assessments of the impact of climate variability and climate change, gene-based modeling and breeding selection, water use, greenhouse gas emissions, and long-term sustainability through the soil organic carbon and nitrogen balances. DSSAT has been in used by more than 16,500 researchers, educators, consultants, extension agents, growers, and policy and decision makers in over 174 countries worldwide.

The crop models require daily weather data, soil surface and profile information, and detailed crop management as input. Crop genetic information is defined in a crop species file that is provided by DSSAT and cultivar or variety information that should be provided by the user. Simulations are initiated either at planting or prior to planting through the simulation of a bare fallow period. These simulations are conducted at a daily step or in some cases, at an hourly time step depending on the process and the crop model. At the end of each day, the plant and soil water, nitrogen, phosphorus, and carbon balances are updated, as well as the crop’s vegetative and reproductive development stage.

### What is a WTH File

The three key variables in a DSSAT weather file are precipitation, minimum and maximum temperature and solar radiation. [*.WTH](http://www.ukm.my/seaclid-cordex/files/Rice%20Pilot%20Project%20Workshop/PRESENTATION-PDF/20140922-1430-1445-Weather%20data%20format%20of%20%20DSSAT%20model--%20Attachai.pdf) (analogous as *.MET in APSIM) has been defined as the standardized file format for DSSAT. The **latitude**,**longitude**, **tav** and **amp** parameters are also mandatory for these files.

# Climate Data Sources

## About SILO

SILO (Scientific Information for Land Owners) is a database of Australian climate data from 1889 to the present. It provides daily meteorological datasets for a range of climate variables in ready-to-use formats suitable for biophysical crop modelling, research and climate applications.

SILO is an enabling technology which allows users to focus on their research, without the burden of data preparation. SILO products support research through providing:

- national coverage, with infilled values for missing data, and
- datasets being model ready, in a variety of formats.

SILO is hosted by the Queensland Department of Environment and Science (DES). The data system began in 1996 as a collaborative project between the Queensland Government and the Australian Bureau of Meteorology (BoM) sponsored by the Land and Water Resources Research and Development Corporation. The datasets are constructed from observational data obtained from BoM.

### NetCDF and API data variations from SILO

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

Differences between the API and NetCDF values only occur when a datum fails one of the aforementioned range checks, for example, when the interpolated maximum temperature is lower than the interpolated minimum temperature. Such situations typically arise due to errors in the observed data (leading to errors in the gridded surface), or in regions where there are very few recording stations. We expect there to be more errors in the gridded surfaces for the early years, as there were relatively few stations recording data (other than rainfall) before 1957. Plots showing the number of stations recording each variable as a function of time are provided in Jeffrey et al. 2001 (see the [Publications section on SILO](https://www.longpaddock.qld.gov.au/silo/about/publications-references/)).

### Data request

Data request is limited to years after 1889.

## About NASA POWER

NASA's goal in Earth science is to observe, understand, and model the Earth system to discover how it is changing, to better predict change, and to understand the consequences for life on Earth. The Applied Sciences Program, within the Science Mission Directorate (which replaced both the Office of Earth Science and the Office of Space Science), serves NASA and Society by expanding and accelerating the realization of societal and economic benefits from Earth science, information, and technology research and development.

The Prediction Of Worldwide Energy Resources (POWER) project was initiated to improve upon the current renewable energy data set and to create new data sets from new satellite systems. The POWER project targets three user communities: (1) Renewable Energy, (2) Sustainable Buildings, and (3) Agroclimatology. The Agroclimatology Archive is designed to provide web-based access to industry-friendly parameters formatted for input to crop models contained within agricultural DSS.

### What is the spatial resolution of the POWER data?

Bestiapop produces data from NASAPOWER at a 0.5&deg; x 0.5&deg; resolution however the original datasets have different spatial resolution accordingly with the variable.

- **Solar**: The data was initially produced on a 1&deg; x 1&deg; global grid and then re-gridded via data replication to a 0.5&deg; x 0.5&deg; latitude and longitude global grid.

- **Meteorology**: The data was initially produced on a 1/2&deg; x 2/3&deg; global grid and then re-gridded via bi-linearly interpolation to a 0.5&deg; x 0.5&deg; latitude and longitude global grid.

### What is the temporal resolution of the POWER data?

Bestiapop produces data at a daily step however the original datasets have different temporal resolution accordingly with the variable.

- **Solar**: The data was initially produced on 3-hourly time increments which are averaged to provide daily values. The daily averaged values are used to calculate climatologically averaged monthly values.

- **Meteorology**: The data was initially produced on 1-hourly time increments which are averaged to provided daily values. The daily averaged values are used to calculate climatologically averaged monthly values.
 
### Climate Variables

One consideration is the name and number of variables in each data source (SILO vs NASAPOWER). They have different number of climate variables and names. Therefore, for a friendly use of BestiaPop with different data sources, we have defined generic variable names for global solar radiation, precipitation, maximum temperature and minimum temperature which are mandatory to create MET and WTH files for crop modelling purposes. Abbreviations of NASAPOWER variables and their corresponding variable names are provided below:

|Original Name|BestiaPop Name|Description|Unit|
|:--------------:|:---------------:|:------------:|:------------:|
|ALLSKY_SFC_SW_DWN|radiation|All Sky Insolation Incident on a Horizontal Surface|MJ m<sup>-2<sup>|
|PRECTOT|daily_rain|Precipitation|mm|
|T2M_MIN|min_temp|Minimum Temperature at 2 Meters |&deg;C |
|T2M_MAX|max_temp|Maximum Temperature at 2 Meters |&deg;C |

### Missing values

Solar daily data are typically missing because the satellite observational data are missing and irretrievable. Therefore, in the NASAPOWER data there are missing values for this variable which are represented by `-99`. It is a problem for crop models that works at daily step due to they have defined boundaries for climate variables, so they crashes if read `Nan` values. To solve this problem, BestiaPop automatically calculates the mean value between the previous and the following `NaN`value of the variable and replace the `NaN` with the calculated mean.

### Data request

Data request is limited to years after 1981.


# Installation

There are two ways to install BestiaPop

1. With pip
2. Cloning repo

## 1. Install using PIP

1. `pip install bestiapop` --> This will install all required packages that BestiaPop needs to run as well
2. **Done!**, to use, sipmply type `python -m bestiapop [args]` :)

> **NOTE**: We recomend you install BestiaPop in an isolated environment created with *Anaconda* or *VirtualEnv*. If using *Anaconda* simply do `conda create -y --name my_data_env python=3.7`

## 2. Install Cloning BestiaPop Repo

1. Clone this repo
2. Install required packages.

### Using pip

1. Change directory to the repo folder
2. `pip install -r pip_requirements.txt`

### Using Anaconda

#### In you Base Environment

This option might take a *very* long time due to the multiple dependencies that Anaconda might have to solve on your default **base environment**. Preferably, install using the next method which creates a custom environment.

1. Open your anaconda prompt for the *base* environment (default)
2. `conda install -y -c conda-forge --file pip_requirements.txt`

#### Create Custom Environment

1. `conda create -y --name bestiapop python==3.7`
2. `conda install --name bestiapop -y -c conda-forge --file pip_requirements.txt`
3. `conda activate bestiapop`

# Usage

BestiaPop has three primary commands that you can pass in with the `-a` option: 

1. **generate-climate-file**: this command will generate an input file for crop modelling software depending on the output type (`-ot`) being `met` or `wth`. When `csv` or `stdout` is selected, a file containing all years in the sequence, with all requested variables, will be produced for each lat/lon combination.
2. **download-nc4-file**: this command downloads NetCDF4 files from SILO or NASAPOWER
3. **convert-nc4**: *currently not implemented*, this command will allow you to convert NetCDF4 files to other formats like `json` or `csv`.

## Examples

> **NOTE**: if you installed BestiaPop using `pip`, then instead of `python bestiapop.py` you will have to use `python -m bestiapop`.

### Download NetCDF4 Files

#### Download SILO climate files for years 2010 to 2018 for and maximum air temperature

This command will **only** download the file from the cloud, it won't perform any further processing.

> **NOTE**: a year range must be separated by a dash, whereas multiple climate variables are separated by spaces

```powershell
python bestiapop.py -a download-nc4-file --data-source silo -y "2010-2018" -c "daily_rain max_temp" -o C:\some\output\folder
```

### Generate Climate Files

#### Generate MET output files (for APSIM) using SILO cloud API, for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2015 to 2016

> **Note**:
    * the resulting MET files will be placed in the output directory specified by "-o"
    * add *-ot csv* at the end of the script if a csv is required as output file. The code generates MET files by default.

```powershell
python bestiapop.py -a generate-climate-file -s silo -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot met
```

#### Generate MET output files FROM A LIST OF LAT/LON combinations

This option is handy if you already know the combinations of lat/lon that you want to process.

> **Note**:
    The CSV file with lat/lon combinations does not need to have a header and should only list a single combination per line like so:

    
    -41.15,145.5
    -43.45,146.7
    -41.25,145.25
    -42.70,147.45
    -41.50,145.6
    

```bash
python bestiapop.py -a generate-climate-file -s silo -y "2015-2016" -c "radiation max_temp min_temp daily_rain" --coordinates-file .\path\to\coordinates.csv -o C:\some\output\folder\ -ot met
```

#### Generate WTH output files (for DSSAT) output files using SILO cloud API, for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2015 to 2016

```powershell
python bestiapop.py -a generate-climate-file -s silo -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot wth
```

#### Generate CSV output files (for APSIM) using SILO cloud API, for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2015 to 2016

> **Note**:
    * BestiaPop will generate as many CSV files as there are combinations of lat/lon in the coordinate ranges passed in to the application.
    * BestiaPop will *also* generate a single extra file at the end called `bestiapop-beastly-dataframe.csv` which basically contains **all** the lat/lon combinations for **all years** and **all variables**. The purpose of this file is to make it easier to ingest this data into engines like Pandas, Excel or Elasticsearch, without having to piece together the *individual csv files* generated for each lat/lon combination.

```powershell
python bestiapop.py -a generate-climate-file -s silo -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot csv
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

#### Generate MET output files (for APSIM) using NASAPOWER cloud API, for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2003 to 2016

```powershell
python bestiapop.py -a generate-climate-file -s nasapower -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot met
```

#### Generate WTH output files (for DSSAT) output files NASAPOWER cloud API, for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2015 to 2016

```powershell
python bestiapop.py -a generate-climate-file -s nasapower -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot wth
```

#### Generate CSV output files using NASAPOWER cloud API, for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2015 to 2016

> **Note**:
    * BestiaPop will generate as many CSV files as there are combinations of lat/lon in the coordinate ranges passed in to the application.
    * BestiaPop will *also* generate a single extra file at the end called `bestiapop-beastly-dataframe.csv` which basically contains **all** the lat/lon combinations for **all years** and **all variables**. The purpose of this file is to make it easier to ingest this data into engines like Pandas, Excel or Elasticsearch, without having to piece together the *individual csv files* generated for each lat/lon combination.

```powershell
python bestiapop.py -a generate-climate-file -s nasapower -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -ot csv
```

#### Print data directly to screen (stdout) using NASAPOWER cloud API, for global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for year 2019

```powershell
python bestiapop.py -a generate-climate-file -s nasapower -y "2019" -c "radiation max_temp min_temp daily_rain" -lat "-55" -lon "-20" -ot stdout
```

Result:

```
+-------+-------+--------+-------+--------+--------+--------+--------+
|   lon |   lat |   year |   day |   radn |   maxt |   mint |   rain |
|-------+-------+--------+-------+--------+--------+--------+--------|
|   -20 |   -55 |   2019 |     1 |  16.88 |   3.27 |      2 |   1.99 |
|   -20 |   -55 |   2019 |     2 |   8.88 |   3.61 |   2.11 |   1.02 |
|   -20 |   -55 |   2019 |     3 |     23 |   2.91 |   2.22 |   0.85 |
|   -20 |   -55 |   2019 |     4 |   7.64 |   2.22 |    0.7 |  10.42 |
|   -20 |   -55 |   2019 |     5 |  10.38 |   2.33 |   1.17 |   5.89 |
...
|   -20 |   -55 |   2019 |   362 |     14 |    3.4 |   2.68 |   0.66 |
|   -20 |   -55 |   2019 |   363 |  14.51 |   3.75 |   2.29 |   0.51 |
|   -20 |   -55 |   2019 |   364 |   8.37 |   3.41 |   2.47 |   1.61 |
|   -20 |   -55 |   2019 |   365 |  13.57 |    2.3 |   1.67 |   2.35 |
+-------+-------+--------+-------+--------+--------+--------+--------+
```

## Parallel Computing

**BestiaPop** as of version 2.5 comes with parallel processing for multicore systems by leveraging python's multiprocessing library. Not all actions have implemented this functionality yet but they will be added progressively. To enable multiprocessing just pass in the `-m` flag to the `bestiapop.py` command. By default it will leverage **all your cores** (whether physical or logical).

Parallelization is done based on the coordinate variable (whether *latitude* or *longitude*) that has the widest spread (highest data points count). This means, you will rip the benefits of multiple cores when your datasets reference wide ranges of *lat* or *lon* variables. 


> **NOTE**: When generating *MET* files *from locally available NetCDF4 files* based on SILO data, you might experience mixed results since SILO provides NetCDF4 files split into `year-variable` and *MET* files require multiple *years* in the same MET file. As of Jun 2020, SILO has refactored all its NetCDF4 files to perform better when extracting spatial data points rather than time-based data points. This effectively means that it is slower to extract data **for all days of the year** from NetCDF4 files, for a single combination of lat/lon, than it is to extract data for all combinations of lat/lon **for a single day**. Since SILO NetCDF4 files are split into `year-variable` units you will always have to extract data from different files when using multiple years.

### EXAMPLE: Generate MET output files (for APSIM) from SILO Cloud API global solar radiation, minimum air temperature, maximum air temperature and daily rainfall for years 2015 to 2016

```powershell
python bestiapop.py -a generate-climate-file -s silo -y "2008-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder\ -m
```

Here, the `-m` at the end will engage multiple cores to process the tasks. If you have 8 available cores it will create 8 separate processes to download the data from the cloud and will then use 8 separate processes to generate the output files.

# BestiaPop performance

Below you can find a descriptive table with some performance indicators for BestiaPop. We used an AMD Ryzen Threadripper 2990WX 32-Core Processor (128 GB of physical memory) to run 20 lat * 20 lon combinations for SILO, i.e. 400 files at 0.05&deg;. The same lat-lon combinations were applied for NASAPOWER, however it generated only 9 files at 0.5&deg; due to the nature of its data resolution. Runs were performed for a 5 year period to generate MET, WTH and CSV files with the parallel computing (PC) function (-m) activated and deactivated. We calculated the the total workload time to generate all files (_Total Time (seconds)_), a single file (_Time/File (s)_) and the time to generate a single year of daily data (_Time/Year (seconds)_). We also estimated the efficiency of the parallel computing function, i.e. how many times faster was BestiaPop using PC activated (_PC Efficiency (times)_).

> **NOTE**: When the amount of lat-lon combinations is reduced (e.g. 9 files), the benefits of multiprocessing are not visualised. However, when the amount of lat-lon combinations are increased (e.g. 400 files), the use of the `-m` function is recommended due to its increase considerably the time efficiency.

| Data Source | Parallel Computing (PC) | File Type | Number of Files | Years | Total Time (s) | Time/File (s) | Time/Year (s) | PC Efficiency (times) |
|:------------|:------------------------|:----------|:--------------:|:--------------:|:--------------:|:--------------:|:--------------:|:--------------:|
| SILO      | deactivated      | MET |400|5| 1571    | 3.93  | 0.79 |      |
|           |                  | WTH |400|5| 1450    | 3.63  | 0.73 |      |
|           |                  | CSV |400|5| 1503    | 3.76  | 0.75 |      |
|           | activated        | MET |400|5| 149     | 0.37  | 0.07 | 10.5 |
|           |                  | WTH |400|5| 152     | 0.38  | 0.08 | 9.5  |
|           |                  | CSV |400|5| 161     | 0.40  | 0.08 | 9.3  |
| NASAPOWER | deactivated      | MET |9  |5| 41      | 4.56  | 0.91 |      |
|           |                  | WTH |9  |5| 38      | 4.22  | 0.84 |      |
|           |                  | CSV |9  |5| 41      | 4.56  | 0.91 |      |
|           | activated        | MET |9  |5| 71      | 7.89  | 1.58 | 0.6  |
|           |                  | WTH |9  |5| 84      | 9.33  | 1.87 | 0.5  |
|           |                  | CSV |9  |5| 94      | 10.44 | 2.09 | 0.4  |

# BestiaPop products

## MET file example (APSIM)

![image](/sample-data/products/met.jpg)
Complete MET file [here](/sample-data/products/-41.0-145.0.met) 

## WTH file example (DSSAT)

![image](/sample-data/products/wth.jpg)
Complete WTH file [here](/sample-data/products/-4101450161.WTH)

## CSV file example

![image](/sample-data/products/csv.jpg)
Complete CSV file [here](/sample-data/products/-41.0-145.0.silo.csv)

# Package references

1. https://registry.opendata.aws/silo/
2. https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f
3. http://xarray.pydata.org/en/stable/dask.html
