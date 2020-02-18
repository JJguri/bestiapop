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

#### Generate CSV output files for Min Temperature, Radiation and Daily Rain

Note: the resulting csv files will be placed in the output directory specified by "-o"

```powershell
python bestiapop.py -a convert-nc4-to-csv -y 2015 -c "daily_rain min_temp radiation" -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\output\folder
```

## References

1. https://registry.opendata.aws/silo/ 
2. https://towardsdatascience.com/handling-netcdf-files-using-xarray-for-absolute-beginners-111a8ab4463f
3. http://xarray.pydata.org/en/stable/dask.html 