#!/usr/bin/env python3

'''
 NAME: POPBEAST SILO CLIMATE EXCTRACTOR
 VERSION: 2.0
 AUTHOR: Diego Perez (@darkquasar) - Jonathan Ojeda () - 
 DESCRIPTION: Main module that automates the download of data from APSIM and subsequent transformations into MET files
 
 HISTORY: 
    v0.1 - Created python file
    v0.2 - Added progress bar to download routine
    
 TODO:
    1. Use AutoComplete package to help in commandline params: https://github.com/kislyuk/argcomplete.

'''

import argparse
import calendar
import h5netcdf
import logging
import numpy as np
import pandas as pd
import requests
import os
import s3fs
import sys
import time
import xarray as xr
from datetime import datetime as datetime
from jinja2 import Template
from numpy import array
from pathlib import Path
from tqdm import tqdm

class Arguments():

    def __init__(self, args):
        self.parser = argparse.ArgumentParser(
            description="SILO Climate Data Extractor"
            )

        self.parser.add_argument(
            "-a", "--action",
            help="The type of operation to want to perform: download-silo-file (it will only download a particular SILO file from S3 to your local disk), convert-nc4-to-met (it will only convert a local or S3 file from NC4 format to MET), convert-nc4-to-csv(it will only convert a local or S3 file from NC4 format to CSV), download-and-convert-to-met (combines the first two actions)",
            type=str,
            choices=["download-silo-file", "convert-nc4-to-met", "convert-nc4-to-csv", "generate-met-file"],
            default="convert-nc4-to-csv",
            required=True
            )

        self.parser.add_argument(
            "-y", "--year-range",
            help="This option determines what is the range of years that you want to download data for. It can be a single year (-y 2015) or a range, using a dash in between (-y 2000-2015)",
            type=str,
            default="",
            required=True
            )

        self.parser.add_argument(
            "-c", "--climate-variable",
            help="The climate variable you want to download data for. To see all variables: https://www.longpaddock.qld.gov.au/silo/about/climate-variables/. You can also specify multiple variables separating them with spaces, example: ""daily_rain radiation min_temp max_temp""",
            type=self.string_variable_list,
            default="daily_rain",
            required=True
            )

        self.parser.add_argument(
            "-lat", "--latitude-range",
            help="The latitude range to download data from the grid to a decimal degree, separated by a ""space"", in increments of 0.05. It also accepts single values. Examples: -lat ""-40.85 -40.90"" \n -lat ""30.10 33"" \n -lat -41",
            type=self.int_variable_list,
            default=None,
            required=False
            )

        self.parser.add_argument(
            "-lon", "--longitude-range",
            help="The longitude range to download data from the grid to a decimal degree, separated by a ""space"", in increments of 0.05. It also accepts single values. Examples: -lon ""145.45 145.5"" \n -lon ""145.10 146"" \n -lon 145",
            type=self.int_variable_list,
            required=False
            )

        self.parser.add_argument(
            "-i", "--input-path",
            help="For ""convert-nc4-to-met"" and ""convert-nc4-to-csv"", the file or folder that will be ingested as input in order to extract the specified data. Example: -i ""C:\\some\\folder\\2015.daily_rain.nc"". When NOT specified, the tool assumes it needs to get the data from the cloud.",
            type=str,
            default=os.getcwd(),
            required=False
            )

        self.parser.add_argument(
            "-o", "--output-directory",
            help="This argument is required and represents the directory that we will use to: (a) stage the netCDF4 files as well as save any output (MET, CSV, etc.) or (b) collect any .nc files when you have already downloaded them for conversion to CSV or MET. If no folder is passed in, the current directory is assumed to the right directory. Examples: (1) download files to a local disk: -o ""C:\\some\\folder\\path""",
            type=str,
            default=os.getcwd(),
            required=True
            )

        self.pargs = self.parser.parse_args()

    def int_variable_list(self, string):
        # Adding our own parser for comma separated values
        # since Argparse interprets them as multiple values and complains
        if " " in string:
            return [float(x) for x in string.split()]
        else:
            return [float(string)]

    def string_variable_list(self, string):
        # Adding our own parser for comma separated values
        # since Argparse interprets them as multiple values and complains
        if " " in string:
            return [str(x) for x in string.split()]
        else:
            return [str(string)]

    def get_args(self):
        return self.pargs

class SILO():

    def __init__(self, logger, action, outputpath, inputpath, variable_short_name, year_range, lat_range, lon_range):

        # Initializing variables
        self.action = action
        self.logger = logger
        self.logger.info('Initializing {}'.format(__name__))
        self.outputdir = Path(outputpath)
        self.variable_short_name = variable_short_name
        
        # Check whether a year range with "-" was provided for the year.
        # If this is the case, generate a list out of it
        # TODO: handle lists of discontinuous year ranges like [1999-2001,2005-2019]
        if "-" in year_range:
            first_year = int(year_range.split("-")[0])
            last_year = int(year_range.split("-")[1]) + 1
            year_range = np.arange(first_year,last_year,1)
        else:
            year_range = [int(year_range)]

        self.year_range = year_range

        # Check whether a lat and lon range separated by a space was provided.
        # If this is the case, generate a list out of it
        # NOTE: for some reason I get a list within a list from the argparse...
        if lat_range:
            if len(lat_range) > 1:
                if lat_range[0] < 0 and lat_range[1] < 0:
                    if lat_range[0] > lat_range[1]:
                        # We are clearly dealing with negative numbers
                        # User has mistakenly swapped the order of numbers
                        # we need to silently swap them back
                        first_lat = lat_range[1]
                        last_lat = lat_range[0]
                    else:
                        first_lat = lat_range[0]
                        last_lat = lat_range[1]
                lat_range = np.arange(first_lat,last_lat,0.05).round(decimals=2)
            self.lat_range = lat_range

        if lon_range:
            if len(lon_range) > 1:
                if lon_range[0] > lon_range[1]:
                    # User has mistakenly swapped the order of numbers
                    # we need to silently swap them back
                    first_lon = lon_range[1]
                    last_lon = lon_range[0]
                else:
                    first_lon = lon_range[0]
                    last_lon = lon_range[1]
                lon_range = np.arange(first_lon,last_lon,0.05).round(decimals=2)
            self.lon_range = lon_range

        # Validate input directory
        # TODO

        # Validate output directory
        if self.outputdir.is_dir() == True:
            if self.outputdir.exists() == False:
                self.logger.info('{} does not exist, creating it...'.format(self.outputdir))
                self.outputdir.mkdir(parents=True, exist_ok=True)
        elif (self.outputdir.is_file() == True) and (self.outputdir.exists() == False):
            self.logger.error('File {} does not exist'.format(self.outputdir))
        else:
            self.logger.error('{} is not a folder, please provide a folder path'.format(self.outputdir))
            sys.exit(1)
  
    def process_records(self, action):
        # Let's check what's inside the "action" variable and invoke the corresponding function
        if action == "download-silo-file":
            self.logger.info('Action {} invoked'.format(action))
            for year in self.year_range:
                self.logger.info('Downloading SILO file for year {}'.format(year))
                self.download_file_from_silo_s3(year, self.variable_short_name, self.outputdir)

        elif action == "convert-nc4-to-met":
            self.logger.info('Action {} not implemented yet'.format(action))

        elif action == "convert-nc4-to-csv":
            self.logger.info('Converting files to CSV format')
            # 1. Let's invoke generate_silo_dataframe with the appropriate options
            self.generate_silo_dataframe(year_range=self.year_range,
                                        variable_short_name=self.variable_short_name, 
                                        lat_range=self.lat_range,
                                        lon_range=self.lon_range,
                                        outputdir=self.outputdir,
                                        download_files=False,
                                        output_to_file=True,
                                        output_format="CSV")

        elif action == "generate-met-file":
            self.logger.info('Downloading data and converting to MET format')
            # 1. Let's invoke generate_silo_dataframe with the appropriate options
            self.generate_silo_dataframe(year_range=self.year_range,
                                        variable_short_name=self.variable_short_name, 
                                        lat_range=self.lat_range,
                                        lon_range=self.lon_range,
                                        outputdir=self.outputdir,
                                        download_files=False,
                                        output_to_file=True,
                                        output_format="MET")

    def load_cdf_file(self, sourcepath, data_category, load_from_s3=True, year=None):

        # This function loads the ".nc" file using the xarray library and
        # stores a pointer to it in "data_dict"

        # Let's first check whether a source file was passed in, otherwise
        # assume we need to fetch from the cloud
        if load_from_s3 == True:
            silo_file = "silo-open-data/annual/{}/{}.{}.nc".format(data_category, year, data_category)
            fs_s3 = s3fs.S3FileSystem(anon=True)
            remote_file_obj = fs_s3.open(silo_file, mode='rb')
            DS_data_handle = xr.open_dataset(remote_file_obj, engine='h5netcdf')
        
        else:
            # This function expects that we will pass the value series
            # we are looking for in the "data_category" parameter
            # So if we want the function to return all values for 
            # rain we shall call the function as:
            # load_file(sourcepath, sourcefile, 'daily_rain')
            self.logger.info('Loading netCDF4 file {}'.format(sourcepath))
            DS_data_handle = xr.open_dataset(sourcepath)
        
        # Extracting the "year" from within the file itself.
        # For this we get a sample of the values and then 
        # convert the first value to a year. Assuming we are dealing
        # with single year files as per SILO S3 files, this shouldn't
        # represent a problem
        DS_sample = DS_data_handle.time.head().values[1]
        data_year = DS_sample.astype('datetime64[Y]').astype(int) + 1970
        
        # Storing the pointer to the data and the year in a dict
        data_dict = {
            "value_array": DS_data_handle, 
            "data_year": data_year,            
        }
        
        # returning our dictionary with relevant values
        return data_dict

    def download_file_from_silo_s3(self, year, variable_short_name, output_path = Path().cwd()):
        # This function connects to the public S3 site for SILO and downloads the specified file
        # For a list of variables to use in "variable_short_name" see
        # https://silo.longpaddock.qld.gov.au/climate-variables
        # Most common are: daily_rain, max_temp, min_temp
        # Example, call the function like: download_file_from_silo_s3(2011, "daily_rain")
        # The above will save to the current directory, however, you can also pass
        # your own like: download_file_from_silo_s3(2011,'daily_rain','C:\\Downloads\\SILO\2011')

        # We use TQDM to show a progress bar of the download status
      
        filename = str(year) + "." + variable_short_name + ".nc"
        url = 'https://s3-ap-southeast-2.amazonaws.com/silo-open-data/annual/{}/{}'.format(variable_short_name, filename)

        # Get pointer to URL
        req = requests.get(url, stream=True)

        # Set initial file size and total file size
        first_byte = 0
        total_file_size = int(req.headers.get("Content-Length", 0))
        
        if first_byte >= total_file_size:
            return total_file_size

        progressbar = tqdm(
                            total=total_file_size,
                            initial=first_byte,
                            unit='B',
                            unit_scale=True,
                            desc=url.split('/')[-1])
        
        # Write file in chunks
        # Let's first check whether the file has already been downloaded
        # if it has, let's return without downloading it again
        output_file = output_path/filename
        if output_file.is_file() == True:
            if output_file.exists() == True:
                self.logger.info('File {} already exists. Skipping download...'.format(output_file))
                return

        chunk_size = 1024
        with open(output_file, 'ab') as f:
            self.logger.info('Downloading file {}...'.format(output_file))
            for chunk in req.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    progressbar.update(1024)
                    
        progressbar.close()

    def get_values_from_array(self, lat, lon, value_array, file_year, variable_short_name):
        # This function will use xarray to extract a slice of time data for a combination
        # of lat and lon values

        # Checking if this is a leap-year  
        if (( file_year%400 == 0) or (( file_year%4 == 0 ) and ( file_year%100 != 0))):
            days = np.arange(0,366,1)
        else: 
            days = np.arange(0,365,1)

        # Using a list comprehension to capture all daily values for the given year and lat/lon combinations
        # We round values to a single decimal
        data_values = [np.round(x, decimals=1) for x in value_array[variable_short_name].sel(lat=lat, lon=lon).values]

        # We have captured all 365 or 366 values, however, they could all be NaN (non existent)
        # If this is the case, skip it
        # NOTE: we could have filtered this in the list comprehension above, however
        # we chose to do it here for code readability
        data_values = [x for x in data_values if np.isnan(x) != True]

        # we need to get the total amount of values collected
        # if there was "NO" data available for all days under a particular combination
        # of lat & lon, then the total values collected should equal "0"
        # (meaning, there was no data for that point in the grid)
        # If this is the case, then the function will simply return with
        # a "no_values"
        if len(data_values) == 0:
            raise ValueError('No data for the lat & lon combination provided')
      
        # now we need to fill a PANDAS DataFrame with the lists we've been 
        # compiling.
        # Uncomment below if you want to also get lat and lon values in output df
        '''
        lat_values = np.full(total_values, lat)
        lon_values = np.full(total_values, lon)
        pandas_dict_of_items = {'lat': lat_values,
                                'lon': lon_values,
                                'day': year,
                                'rain': data_values}
        '''

        pandas_dict_of_items = {'days': days,
                                variable_short_name: data_values}
      
        df = pd.DataFrame.from_dict(pandas_dict_of_items)
        
        # making the julian day match the expected
        df['days'] += 1
        
        # adding a column with the "year" to the df
        # so as to prepare it for export to other formats (CSV, MET, etc.)
        df.insert(0, 'year', file_year)
      
        return df

    def generate_silo_dataframe(self, year_range, variable_short_name, lat_range, lon_range, outputdir, download_files=False, load_from_s3=True, output_to_file=True, output_format="CSV"):

        '''
        Creation of the DataFrame and Files
        ===================================

        We will iterate through each "latitude" value and, 
        within this loop, we will iterate through all the different 
        "longitude" values for a given year. Results for each year
        are collected inside the "yearly_met_df" with "yearly_met_df.append"
        At the end, it will output a file with all the contents if
        "output_to_file=True" (by default it is "True")
        '''
        self.logger.debug('Generating DataFrames')

        # let's first create an empty df to store 
        # all data for a given year
        yearly_met_df = pd.DataFrame()
        all_years_met_df = pd.DataFrame()

        # setting up Jinja2 Template for final MET file if required
        met_file_j2_template = '''
            [weather.met.weather]
            !station number={{ lat }}-{{ lon }}
            Latitude={{ lat }}
            Longitude={{ lon }}
            tav={{ tav }}
            amp={{ amp }}

            year day radn maxt mint rain
            () () (MJ^m2) (oC) (oC) (mm)
            {{ data }}
        '''

        # Loading and/or Downloading the files
        for lat in tqdm(lat_range, desc="Latitude"):    

            for lon in tqdm(lon_range, desc="Longitude"):

                for year in tqdm(year_range, desc="Year"):
                
                    for climate_variable in tqdm(variable_short_name, desc="Climate Variable"):

                        self.logger.info('Processing data for variable {} - year {} - lat {} - lon {}'.format(climate_variable, year, lat, lon))

                        # should we download the file first?
                        if download_files == True:
                            self.logger.debug('Attempting to download files')
                            self.download_file_from_silo_s3(year, climate_variable, outputdir)

                        # Opening the target CDF database
                        # We need to check:
                        # (1) should we fetch the data directly from AWS S3 buckets
                        # (2) if files should be fetched locally, whether the user passed a directory with multiple files or just a single file to process.
                        if load_from_s3 == True:
                            self.logger.info('Fetching remote NetCDF file for {}'.format(climate_variable))
                            data = self.load_cdf_file(None, climate_variable, load_from_s3=True, year=year)
                        else:
                            if outputdir.is_dir() == True:
                                sourcefile = str(year) + "." + climate_variable + ".nc"
                                sourcepath = outputdir/sourcefile
                            elif outputdir.is_file() == True:
                                sourcepath = outputdir

                            if sourcepath.exists() == False:
                                self.logger.error('Could not find file {}. Please make sure you have downloaded the required netCDF4 files in the format "year.variable.nc" to the input directory. Skipping...'.format(sourcepath))
                                continue
                            
                            self.logger.info('Fetching data from local NetCDF file {}'.format(sourcepath))
                            data = self.load_cdf_file(sourcepath, climate_variable)

                        file_year = data['data_year']

                        self.logger.debug('Processing {} --> Lat {} - Lon {} for year {}'.format(climate_variable, lat, lon, file_year))

                        # here we are checking whether the get_values_from_cdf function
                        # returns with a ValueError (meaning there were no values for
                        # that particular lat & long combination). If it does return
                        # with an error, we skip this loop and don't produce any output files
                    
                        try:
                            year_lat_lon_df = self.get_values_from_array(lat, lon, data['value_array'], file_year, climate_variable)
                        except ValueError:
                            continue
                        
                        # Should we generate any file output?
                        if output_to_file == True:

                            if output_format == "MET":

                                # check if the selected action was to generate a final met file
                                # we need to combine the values of all the climate variables first
                                # before generating the final MET
                                if self.action == "generate-met-file":

                                    # test if yearly_met_df is empty, if so, we need to initialize it with first climate
                                    # variable data
                                    if yearly_met_df.empty == True:
                                        yearly_met_df = year_lat_lon_df
                                    else:
                                        # grab columns present in year_lat_lon_df that are not in yearly_met_df yet
                                        differential_cols = year_lat_lon_df.columns.difference(yearly_met_df.columns)
                                        yearly_met_df = pd.merge(yearly_met_df, year_lat_lon_df[differential_cols], left_index=True, right_index=True, how='outer')
                              
                            # Should we output using CSV file format?
                            elif output_format == "CSV":
                                # let's build the name of the file based on the value of the 
                                # first row for latitude, the first row for longitude and then 
                                # the year (obtained from the name of the file with file_year = int(sourcefile[:4]))
                                # Note: there is a better method for obtaining this by looking at the
                                # "time" variable, see here below:

                                if outputdir.is_dir() == True:
                                    csv_file_name = '{}-{}.{}-{}.csv'.format(climate_variable, file_year, lat, lon)
                                    self.logger.debug('Writting CSV file {} to {}'.format(csv_file_name, outputdir))
                                    full_output_path = outputdir/csv_file_name
                                    year_lat_lon_df.to_csv(full_output_path, sep=',', index=False, mode='a', float_format='%.1f')
                        
                        # "reset" the year_lat_lon_df back to zero.
                        year_lat_lon_df = pd.DataFrame()
                    
                    ## DEBUG - ERASE
                    print(yearly_met_df)
                    ## End of climate_variable loop
                    self.logger.info('Finished CLIMATE VARIABLE Loop for Year {}'.format(year))
                    # (1) append the yearly_met_df that contains all variable values
                    # for a particular year to the all_years_met_df
                    # (2) "reset" the yearly_met_df back to zero.
                    all_years_met_df = all_years_met_df.append(yearly_met_df, ignore_index=True)
                    yearly_met_df = pd.DataFrame()

                self.logger.info('Finished YEAR Loop for Year {}'.format(year))
                ## End of year loop

                # Should we output to a file using MET file format?
                if output_format == "MET":
                    met_file_name = met_file_name = '{}-{}.met'.format(lat, lon)
                    self.logger.info('Writting MET file {} to {}'.format(met_file_name, outputdir))
                    full_output_path = outputdir/met_file_name
                    all_years_met_df.to_csv(full_output_path, sep=',', index=False, mode='a', float_format='%.1f')
                    # reset all_years_met_df back to zero.
                    all_years_met_df = pd.DataFrame()
                
            ## End of lon loop

         ## End of lat loop

def main():
  # Instantiating the arguments class
  args = Arguments(sys.argv)
  pargs = args.get_args()
  print(pargs.latitude_range)

  # Setup logging
  # We need to pass the "logger" to any Classes or Modules that may use it 
  # in our script
  try:
    import coloredlogs
    logger = logging.getLogger('POPBEAST')
    coloredlogs.install(fmt='%(asctime)s - %(name)s - %(message)s', level="INFO", logger=logger)
    
  except ModuleNotFoundError:
    logger = logging.getLogger('POPBEAST')
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)
    logger.setLevel(logging.INFO)
  
  # Capturing start time for debugging purposes
  st = datetime.now()
  starttime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
  logger.info("Starting POPBEAST Climate Automation Framework")
  
  # Grab an instance of the SILO class
  silo_instance = SILO(logger, pargs.action, pargs.output_directory, pargs.input_path, pargs.climate_variable, pargs.year_range, pargs.latitude_range, pargs.longitude_range)
  # Start to process the records
  silo_instance.process_records(pargs.action)
    
  # Capturing end time for debugging purposes
  et = datetime.now()
  endtime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
  
  hours, remainder = divmod((et-st).seconds, 3600)
  minutes, seconds = divmod(remainder, 60)

  logger.info("Finished this unit of work")
  logger.info('Workload took: \x1b[47m \x1b[32m{} hours / {} minutes / {} seconds \x1b[0m \x1b[39m'.format(hours,minutes,seconds))

if __name__ == '__main__':
    try:
        main()
        sys.exit()
    
    except KeyboardInterrupt:
        print("\n" + "I've been interrupted by a mortal" + "\n\n")
        sys.exit()