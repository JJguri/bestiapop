#!/usr/bin/env python3

'''
 NAME: POPBEAST
 VERSION: 2.1
 DATA ANALYTICS SPECIALIST - CORE CODE DEVELOPER: Diego Perez (@darkquassar / https://linkedin.com/in/diegope) 
 DATA SCIENTIST - MODEL DEVELOPER: Jonathan Ojeda (https://researchgate.net/profile/Jonathan_Ojeda)
 DESCRIPTION: A python package to automatically generate gridded climate data for APSIM (to be extended for any crop models)
 PAPERS OR PROJECTS USING THIS CODE: 
    1. Ojeda JJ, Eyshi Rezaei E, Remeny TA, Webb MA, Webber HA, Kamali B, Harris RMB, Brown JN, Kidd DB, Mohammed CL, Siebert S, Ewert F, Meinke H (2019) Effects of soil- and climate data aggregation on simulated potato yield and irrigation water demand. Science of the Total Environment. 710, 135589. doi:10.1016/j.scitotenv.2019.135589
    2. Ojeda JJ, Perez D, Eyshi Rezaei E (2020) The BestiaPop - A Python package to automatically generate gridded climate data for crop models. APSIM Symposium, Brisbane, Australia.

 HISTORY: 
    v0.1 - Created python file
    v0.2 - Added numpy series extraction
    v0.3 - Using pathlib for cross-platform path compatibility
    v1.0 - Added progress bar to download routine
    v1.5 - Discarded netCDF4 python package in favor of h5netcdf and xarray for faster slice reads
    v1.6 - Implemented data read directly from the Cloud (AWS S3) for faster data loads, improved speed x15
    v2.0 - Collection of all variable combinations in final dataframe. Obtaining pseudo-MET df from final df.
    v2.1 - Generating final MET file
    v2.2 - Adding commandline parameter to allow for the selection of output type: either MET or CSV
    
 TODO:
    1. Implement a new functionality in APSIM that automatically executes this code by only providing lat and lon values (and generating a MET)
    2. Use AutoComplete package to help in commandline params: https://github.com/kislyuk/argcomplete.
    3. Allow for the extraction of climate data from any other gridded climate data source as long as it is encoded in NETCDF4. Example: allowing the user to pass a parameter for the cloud (S3 or other) location of their data
    4. Extend output formats to generate input climate data for other crop models (DSSAT, STICS)
    5. Implement MultiProcessing to allow for the parallelization of workloads

'''

import argparse
import calendar
import h5netcdf
import io
import logging
#import netCDF4
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
            description="Bestiapop Climate Data Extractor"
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
            type=self.space_separated_list,
            default="daily_rain",
            required=True
            )

        self.parser.add_argument(
            "-lat", "--latitude-range",
            help="The latitude range to download data from the grid to a decimal degree, separated by a ""space"", in increments of 0.05. It also accepts single values. Examples: -lat ""-40.85 -40.90"" \n -lat ""30.10 33"" \n -lat -41",
            type=self.space_separated_list_float,
            default=None,
            required=False
            )

        self.parser.add_argument(
            "-lon", "--longitude-range",
            help="The longitude range to download data from the grid to a decimal degree, separated by a ""space"", in increments of 0.05. It also accepts single values. Examples: -lon ""145.45 145.5"" \n -lon ""145.10 146"" \n -lon 145",
            type=self.space_separated_list_float,
            required=False
            )

        self.parser.add_argument(
            "-i", "--input-path",
            help="For ""convert-nc4-to-met"" and ""convert-nc4-to-csv"", the file or folder that will be ingested as input in order to extract the specified data. Example: -i ""C:\\some\\folder\\2015.daily_rain.nc"". When NOT specified, the tool assumes it needs to get the data from the cloud.",
            type=str,
            default=None,
            required=False
            )

        self.parser.add_argument(
            "-o", "--output-directory",
            help="This argument is required and represents the directory that we will use to: (a) stage the netCDF4 files as well as save any output (MET, CSV, etc.) or (b) collect any .nc files when you have already downloaded them for conversion to CSV or MET. If no folder is passed in, the current directory is assumed to the right directory. Examples: (1) download files to a local disk: -o ""C:\\some\\folder\\path""",
            type=str,
            default=os.getcwd(),
            required=True
            )

        self.parser.add_argument(
            "-ot", "--output-type",
            help="This argument will tell the script whether you want the output file to be in CSV or MET format",
            type=str,
            choices=["met", "csv"],
            default="met",
            required=False
            )

        self.pargs = self.parser.parse_args()

    def space_separated_list_float(self, string):
        # Adding our own parser for space separated values
        # since Argparse interprets them as multiple values and complains
        if " " in string:
            return [float(x) for x in string.split()]
        else:
            return [float(string)]

    def space_separated_list(self, string):
        # Adding our own parser for space separated values
        # since Argparse interprets them as multiple values and complains
        if " " in string:
            return [str(x) for x in string.split()]
        else:
            return [string]

    def get_args(self):
        return self.pargs

class SILO():

    def __init__(self, logger, action, outputpath, output_type, inputpath, variable_short_name, year_range, lat_range, lon_range):

        # Initializing variables
        self.action = action
        self.logger = logger
        self.logger.info('Initializing {}'.format(__name__))
        if inputpath:
            self.inputdir = Path(inputpath)
        else:
            self.inputdir = None
        self.outputdir = Path(outputpath)
        self.output_type = output_type
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
                for variable in self.variable_short_name:
                    self.logger.info('Downloading SILO file for year {}'.format(year))
                    self.download_file_from_silo_s3(year, variable, self.outputdir)

        elif action == "convert-nc4-to-met":
            self.logger.info('Action {} not implemented yet'.format(action))

        elif action == "convert-nc4-to-csv":
            self.logger.info('Converting files to CSV format')
            # 1. Let's invoke generate_climate_dataframe with the appropriate options
            self.generate_climate_dataframe(year_range=self.year_range,
                                        variable_short_name=self.variable_short_name, 
                                        lat_range=self.lat_range,
                                        lon_range=self.lon_range,
                                        outputdir=self.outputdir,
                                        download_files=False,
                                        output_to_file=True,
                                        output_format="CSV")

        elif action == "generate-met-file":
            self.logger.info('Downloading data and converting to {} format'.format(self.output_type))
            # 1. Let's invoke generate_climate_dataframe with the appropriate options
            self.generate_climate_dataframe(year_range=self.year_range,
                                        variable_short_name=self.variable_short_name, 
                                        lat_range=self.lat_range,
                                        lon_range=self.lon_range,
                                        inputdir=self.inputdir,
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
            self.silo_file = "silo-open-data/annual/{}/{}.{}.nc".format(data_category, year, data_category)
            fs_s3 = s3fs.S3FileSystem(anon=True)
            self.remote_file_obj = fs_s3.open(self.silo_file, mode='rb')
            da_data_handle = xr.open_dataset(self.remote_file_obj, engine='h5netcdf')
            self.logger.debug('Loaded netCDF4 file {} from Amazon S3'.format(self.silo_file))
        
        else:
            # This function expects that we will pass the value series
            # we are looking for in the "data_category" parameter
            # So if we want the function to return all values for 
            # rain we shall call the function as:
            # load_file(sourcepath, sourcefile, 'daily_rain')
            self.logger.info('Loading netCDF4 file {} from Disk'.format(sourcepath))
            da_data_handle = xr.open_dataset(sourcepath, engine='h5netcdf')
        
        # Extracting the "year" from within the file itself.
        # For this we get a sample of the values and then 
        # convert the first value to a year. Assuming we are dealing
        # with single year files as per SILO S3 files, this shouldn't
        # represent a problem
        da_sample = da_data_handle.time.head().values[1]
        data_year = da_sample.astype('datetime64[Y]').astype(int) + 1970
        
        # Storing the pointer to the data and the year in a dict
        data_dict = {
            "value_array": da_data_handle, 
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
                            ascii=True,
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
        # This function will use xarray to extract a slice of time data for a combination of lat and lon values

        # Checking if this is a leap-year  
        if (( file_year%400 == 0) or (( file_year%4 == 0 ) and ( file_year%100 != 0))):
            days = np.arange(0,366,1)
        else: 
            days = np.arange(0,365,1)

        # Using a list comprehension to capture all daily values for the given year and lat/lon combinations
        # We round values to a single decimal
        self.logger.debug("Reading array data with xarray")

        # Alternatively: data_values = [np.round(x, decimals=1) for x in (value_array[variable_short_name].loc[dict(lat=lat, lon=lon)]).values]
        data_values = [np.round(x, decimals=1) for x in value_array[variable_short_name].sel(lat=lat, lon=lon).values]

        # We have captured all 365 or 366 values, however, they could all be NaN (non existent)
        # If this is the case, skip it
        # NOTE: we could have filtered this in the list comprehension above, however
        # we chose to do it here for code readability.
        # We assume that, if the first value is "NaN" then the rest of the 364 values will also be null
        # data_values = [x for x in data_values if np.isnan(x) != True]

        if np.isnan(data_values[1]) == True:
            data_values = []

        # we need to get the total amount of values collected
        # if there was "NO" data available for all days under a particular combination
        # of lat & lon, then the total values collected should equal "0"
        # (meaning, there was no data for that point in the grid)
        # If this is the case, then the function will simply return with
        # a "no_values"
        if len(data_values) == 0:
            # DEBUG - ERASE
            self.logger.warning("THERE ARE NO VALUES FOR LAT {} LON {} VARIABLE {}".format(lat, lon, variable_short_name))
            raise ValueError('no_data_for_lat_lon')

        # now we need to fill a PANDAS DataFrame with the lists we've been collecting
        pandas_dict_of_items = {'days': days,
                                variable_short_name: data_values}
      
        df = pd.DataFrame.from_dict(pandas_dict_of_items)
        
        # making the julian day match the expected
        df['days'] += 1
        
        # adding a column with the "year" to the df
        # so as to prepare it for export to other formats (CSV, MET, etc.)
        df.insert(0, 'year', file_year)
        df.insert(0, 'lat', lat)
        df.insert(0, 'lon', lon)

        # closing handle to xarray DataSet
        value_array.close()
   
        return df

    def generate_climate_dataframe(self, year_range, variable_short_name, lat_range, lon_range, inputdir, outputdir, download_files=False, load_from_s3=True, output_to_file=True, output_format="CSV"):

        '''
        Creation of the DataFrame and Files
        ===================================

        We will iterate through each "latitude" value and, 
        within this loop, we will iterate through all the different 
        "longitude" values for a given year. Results for each year
        are collected inside the "met_df" with "met_df.append"
        At the end, it will output a file with all the contents if
        "output_to_file=True" (by default it is "True")
        '''
        self.logger.debug('Generating DataFrames')

        # let's first create an empty df to store 
        # all data for a given variable-year-lat-lon combination
        met_df = pd.DataFrame()

        # empty df to append all the met_df to
        total_met_df = pd.DataFrame()

        # create an empty list to keep track of lon coordinates
        # where there are no values
        empty_lon_coordinates = []

        # Loading and/or Downloading the files
        for climate_variable in tqdm(variable_short_name, ascii=True, desc="Climate Variable"):

            self.logger.debug('Processing data for variable {}'.format(climate_variable))

            for year in tqdm(year_range, ascii=True, desc="Year"):

                self.logger.debug('Processing data for year {}'.format(year))

                # should we download the file first?
                if download_files == True:
                    self.logger.debug('Attempting to download files')
                    self.download_file_from_silo_s3(year, climate_variable, outputdir)

                # Opening the target CDF database
                # We need to check:
                # (1) should we fetch the data directly from AWS S3 buckets
                # (2) if files should be fetched locally, whether the user passed a directory with multiple files or just a single file to process.
                if inputdir:
                    if inputdir.is_dir() == True:
                        sourcefile = str(year) + "." + climate_variable + ".nc"
                        sourcepath = inputdir/sourcefile
                    elif inputdir.is_file() == True:
                        sourcepath = inputdir

                    if sourcepath.exists() == False:
                        self.logger.error('Could not find file {}. Please make sure you have downloaded the required netCDF4 files in the format "year.variable.nc" to the input directory. Skipping...'.format(sourcepath))
                        continue
                    
                    data = self.load_cdf_file(sourcepath, climate_variable, load_from_s3=False)

                elif load_from_s3 == True:
                    data = self.load_cdf_file(None, climate_variable, load_from_s3=True, year=year)
                    
            
                # Now iterating over lat and lon combinations
                # Each year-lat-lon matrix generates a different file
                
                for lat in tqdm(lat_range, ascii=True, desc="Latitude"):

                    for lon in lon_range:

                        file_year = data['data_year']

                        self.logger.debug('Processing Variable {} - Lat {} - Lon {} for Year {}'.format(climate_variable, lat, lon, file_year))

                        # here we are checking whether the get_values_from_cdf function
                        # returns with a ValueError (meaning there were no values for
                        # that particular lat & long combination). If it does return
                        # with an error, we skip this loop and don't produce any output files
                    
                        try:
                            var_year_lat_lon_df = self.get_values_from_array(lat, lon, data['value_array'], file_year, climate_variable)
                        except ValueError:
                            self.logger.warning("Skipping this Loop since no values were obtained")
                            self.logger.warning("Deleting lon {} in array position {}".format(lon, np.where(lon_range == lon)[0][0]))
                            # Append empty lon value to list
                            empty_lon_coordinates.append(lon)                         
                            continue
                        
                        # Should we generate any file output for this var-year-lat-lon iteration?
                        if output_to_file == True:
                                    
                            # Should we output using CSV file format?
                            if output_format == "CSV":
                                # let's build the name of the file based on the value of the 
                                # first row for latitude, the first row for longitude and then 
                                # the year (obtained from the name of the file with file_year = int(sourcefile[:4]))
                                # Note: there is a better method for obtaining this by looking at the
                                # "time" variable, see here below:

                                if outputdir.is_dir() == True:
                                    csv_file_name = '{}-{}.{}-{}.csv'.format(climate_variable, file_year, lat, lon)
                                    self.logger.debug('Writting CSV file {} to {}'.format(csv_file_name, outputdir))
                                    full_output_path = outputdir/csv_file_name
                                    var_year_lat_lon_df.to_csv(full_output_path, sep=',', index=False, mode='a', float_format='%.2f')
                        
                        # delete the var_year_lat_lon_df back to zero.
                        total_met_df = total_met_df.append(var_year_lat_lon_df)
                        del var_year_lat_lon_df

                # We reached the end of the year loop
                # we need must close the open handle to the s3fs file to free up resources
                self.logger.debug("Closed handle to cloud s3fs file {}".format(self.silo_file))
                self.remote_file_obj.close()

        # Remove any empty lon values from longitude array so as to avoid empty MET generation
        empty_lon_array = np.array(empty_lon_coordinates)
        final_lon_range = np.setdiff1d(lon_range, empty_lon_array)

        # Should we generate any file output for this var-year-lat-lon iteration?
        if output_to_file == True:
            
            # Rename variables
            # Check if final df is empty, if so, then return and do not proceed with the rest of the file
            if total_met_df.empty == True:
                self.logger.error("No data in final dataframe. No file can be generated. Exiting...")
                return

            total_met_df = total_met_df.rename(columns={"days": "day","daily_rain": "rain",'min_temp':'mint','max_temp':'maxt','radiation':'radn'})
            total_met_df = total_met_df.groupby(['lon', 'lat', 'year', 'day'])['radn', 'maxt', 'mint', 'rain'].sum().reset_index()
            
            self.logger.info("Proceeding to the generation of MET files")

            for lat in tqdm(lat_range, ascii=True, desc="Latitude"):
                
                for lon in tqdm(final_lon_range, ascii=True, desc="Longitude"):

                    met_slice_df = total_met_df[(total_met_df.lon == lon) & (total_met_df.lat == lat)]
                    del met_slice_df['lat']
                    del met_slice_df['lon']

                    if self.output_type == "met":
                        self.generate_met(outputdir, met_slice_df, lat, lon)
                    
                    elif self.output_type == "csv":
                        full_output_path = outputdir/'{}-{}.csv'.format(lat, lon)
                        met_slice_df.to_csv(full_output_path, sep=",", index=False, mode='w', float_format='%.2f')

                    else:
                        self.logger.info("Output not yet implemented")

                    # Delete unused df
                    del met_slice_df

            generate_final_csv = False
            if generate_final_csv == True:
                # Creating final CSV file
                csv_file_name = 'mega_final_data_frame.csv'
                self.logger.info('Writting CSV file {} to {}'.format(csv_file_name, outputdir))
                full_output_path = outputdir/csv_file_name
                total_met_df.to_csv(full_output_path, sep=',', na_rep=np.nan, index=False, mode='w', float_format='%.2f')

    def generate_met(self, outputdir, met_dataframe, lat, lon):

        # Creating final MET file

        # Setting up Jinja2 Template for final MET file if required
        # Text alignment looks weird here but it must be left this way for proper output
        met_file_j2_template = '''[weather.met.weather]
!station number={{ lat }}-{{ lon }}
Latitude={{ lat }}
Longitude={{ lon }}
tav={{ tav }}
amp={{ amp }}

year day radn maxt mint rain
() () (MJ^m2) (oC) (oC) (mm)
{{ vardata }}
        '''

        j2_template = Template(met_file_j2_template)

        # Initialize a string buffer to receive the output of df.to_csv in-memory
        df_output_buffer = io.StringIO()

        # Save data to a buffer (same as with a regular file but in-memory):
        met_dataframe.to_csv(df_output_buffer, sep=" ", header=False, na_rep="NaN", index=False, mode='w', float_format='%.1f')

        # Get values from buffer
        # Go back to position 0 to read from buffer
        # Replace get rid of carriage return or it will add an extra new line between lines
        df_output_buffer.seek(0)
        met_df_text_output = df_output_buffer.getvalue()
        met_df_text_output = met_df_text_output.replace("\r\n", "\n")
        
        # Calculate here the tav, amp values
        # TODO
        # Calculate amp

        # Get the months as a column
        met_dataframe['cte'] = 1997364
        met_dataframe['day2'] = met_dataframe['day']+met_dataframe['cte']
        met_dataframe['date'] = (pd.to_datetime((met_dataframe.day2 // 1000)) + pd.to_timedelta(met_dataframe.day2 % 1000, unit='D'))
        met_dataframe['month'] = met_dataframe.date.dt.month
        month=met_dataframe.loc[:,'month']

        met_dataframe['tmean'] = met_dataframe[['maxt', 'mint']].mean(axis=1)
        tmeanbymonth = met_dataframe.groupby(month)[["tmean"]].mean()
        maxmaxtbymonth=tmeanbymonth['tmean'].max()
        minmaxtbymonth=tmeanbymonth['tmean'].min()
        amp=np.round((maxmaxtbymonth-minmaxtbymonth), decimals=5)

        # Calculate tav
        tav = tmeanbymonth.mean().tmean.round(decimals=5)
        
        in_memory_met = j2_template.render(lat=lat, lon=lon, tav=tav, amp=amp, vardata=met_df_text_output)
        df_output_buffer.close()

        full_output_path = outputdir/'{}-{}.met'.format(lat, lon)
        with open(full_output_path, 'w+') as f:
            self.logger.info('Writting MET file {}'.format(full_output_path))
            f.write(in_memory_met)

def main():
  # Instantiating the arguments class
  args = Arguments(sys.argv)
  pargs = args.get_args()

  # Setup logging
  # We need to pass the "logger" to any Classes or Modules that may use it 
  # in our script
  try:
    import coloredlogs
    logger = logging.getLogger('POPBEAST')
    coloredlogs.install(fmt='%(asctime)s - %(name)s - %(message)s', level="DEBUG", logger=logger)
    
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
  silo_instance = SILO(logger, pargs.action, pargs.output_directory, pargs.output_type, pargs.input_path, pargs.climate_variable, pargs.year_range, pargs.latitude_range, pargs.longitude_range)
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