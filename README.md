# ClimateDataAutomation

Repository to hold climate data for APSIMX automation

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

## Usage

### Examples

#### Download a SILO file for year 2015 and the daily_rain variable

This command will **only** download the file from AWS, it won't do any further processing.

```powershell
python bestiapop.py -a download-silo-file -y 2015 -c daily_rain -o C:\some\output\folder
```

#### Process file 2015.daily_rain.nc for a range of lat/lon

```powershell
python bestiapop.py -a convert-nc4-to-csv -y 2015 -c daily_rain -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\folder
```

#### Generate MET output files for Radiation, Min Temperature, Max Temperature and Daily Rain for years 2015 to 2016

Note: the resulting MET files will be placed in the output directory specified by "-o"
Note: add -ou csv at the end of the script if a csv is required as output file. The code generates MET files by default.

```powershell
python bestiapop.py -a generate-met-file -y "2015-2016" -c "radiation max_temp min_temp daily_rain" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder
```

## Main References (The following papers implemented this code and can be used as references)

1. Ojeda JJ, Eyshi Rezaei E, Remeny TA, Webb MA, Webber HA, Kamali B, Harris RMB, Brown JN, Kidd DB, Mohammed CL, Siebert S, Ewert F, Meinke H (2019) Effects of soil- and climate data aggregation on simulated potato yield and irrigation water demand. Science of the Total Environment. 710, 135589. doi:10.1016/j.scitotenv.2019.135589
2. Ojeda JJ, Perez D, Eyshi Rezaei E (2020) The BestiaPop - A Python package to automatically generate gridded climate data for crop models. APSIM Symposium, Brisbane, Australia.

## Package references

1. https://registry.opendata.aws/silo/ 
2. https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f
3. http://xarray.pydata.org/en/stable/dask.html 