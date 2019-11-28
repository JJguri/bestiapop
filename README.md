# ClimateDataAutomation
Repository to hold climate data for APSIMX automation

## Usage
1. Clone this repo
2. Install required packages. Using **pip**: `pip install -r requirements.txt`. Using **anaconda**: `conda install --file requirements.txt`
3. Check examples below

## Examples

### Download a SILO file for year 2015 and the daily_rain variable
```powershell
python climatextractor.py -a download-silo-file -y 2015 -c daily_rain -o C:\some\folder
```

### Process file 2015.daily_rain.nc for a range of lat/lon
```powershell
python climatextractor.py -a convert-nc4-to-csv -y 2015 -c daily_rain -lat "-41.15 -41.05" -lon "145.5 145.6" -o C:\some\folder
```