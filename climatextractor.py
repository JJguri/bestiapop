#!/usr/bin/env python3

'''
 NAME: POPBEAST SILO CLIMATE EXCTRACTOR
 VERSION: 0.1
 AUTHOR: Diego Perez (@darkquasar) - Jonathan Ojeda () - 
 DESCRIPTION: Main module that automates the download of data from APSIM and subsequent transformations into MET files
 
 HISTORY: 
    v0.1 - Created python file
    
 TODO:
    1. ----.

'''

import argparse
import calendar
import logging
import netCDF4
import numpy as np
import pandas as pd
import requests
import os
import shutil
import sys
import time
from datetime import datetime as datetime
from numpy import array
from pathlib import Path

class Arguments():

  def __init__(self, args):
    self.parser = argparse.ArgumentParser(
        description="SILO Climate Data Extractor"
        )

    self.parser.add_argument(
      "-a", "--action",
      help="The type of operation to want to perform: download-silo-file (it will only download a particular SILO file from S3), convert-nc4-to-met (it will only convert a file from NC4 format to MET), download-and-convert-to-met (combines the first two actions)",
      type=str,
      choices=["download-silo-file", "convert-nc4-to-met", "convert-nc4-to-csv", "download-and-convert-to-met"],
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
      help="The climate variable you want to download data for. To see all variables: https://www.longpaddock.qld.gov.au/silo/about/climate-variables/",
      type=str,
      choices=["max_temp", "min_temp", "radiation", "daily_rain", "monthly_rain", "vp", "vp_deficit", "evap_pan", "evap_syn", "evap_comb", "evap_morton_lake", "rh_tmax", "rh_tmin", "et_short_crop", "et_tall_crop", "et_morton_actual", "et_morton_potential", "et_morton_wet", "mslp"],
      default="daily_rain",
      required=True
      )

    self.parser.add_argument(
      "-lat", "--latitude-range",
      help="The latitude range to download data from the grid to a decimal degree, separated by a comma, in increments of 0.05. It also accepts single values. Examples: -lat -40.85,-40.90 \n -lat 30.10,33 \n -lat -41",
      type=str,
      default=None,
      required=False
      )

    self.parser.add_argument(
      "-lon", "--longitude-range",
      help="The longitude range to download data from the grid to a decimal degree, separated by a comma, in increments of 0.05. It also accepts single values. Examples: -lon 145.45,145.5 \n -lon 145.10,146 \n -lon 145",
      type=str,
      required=False
      )

    self.parser.add_argument(
      "-o", "--output-directory",
      help="This argument is required and represents the directory that we will use to: \n (a) stage the netCDF4 files as well as save any output (MET, CSV, etc.) or \n (b) collect any .nc files when you have already downloaded them for conversion to CSV or MET. If no folder is passed in, the current directory is assumed to the right directory. Examples: \n (1) Process all files within the folder: -o ""C:\\some\\folder\\path"" \n (2) Process a single file: -o ""C:\\some\\folder\\2015.daily_rain.nc""",
      type=string,
      default=os.getcwd(),
      required=True
      )

    self.pargs = self.parser.parse_args()

  def get_args(self):
    return self.pargs

class SILO():

  def __init__(self, logger, outputpath, variable_short_name, year_range, lat_range, lon_range):

    # Initializing variables
    self.logger = logger
    self.logger.info('Initializing {}'.format(__name__))
    self.outputdir = Path(outputpath)
    self.variable_short_name = variable_short_name
    self.year_range = year_range
    self.lat_range = lat_range
    self.lon_range = lon_range

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
      self.logger.info('Action {} not implemented yet'.format(action))

    elif action == "convert-nc4-to-met":
      self.logger.info('Action {} not implemented yet'.format(action))

    elif action == "convert-nc4-to-csv":
      self.logger.info('Converting files to CSV format')
      # 1. Let's invoke generate_silo_dataframe with the appropriate options
      generate_silo_dataframe(year_range=list(self.year_range),
                              variable_short_name=self.variable_short_name, 
                              lat_range=[self.lat_range],
                              lon_range=[self.lon_range],
                              outputdir=self.outputdir,
                              download_files=False,
                              output_to_file=True,
                              output_format="CSV")

    elif action == "download-and-convert-to-met":
      self.logger.info('Downloading files and converting to MET format')
      # 1. Let's invoke generate_silo_dataframe with the appropriate options
      generate_silo_dataframe(year_range=list(self.year_range),
                              variable_short_name=self.variable_short_name, 
                              lat_range=[self.lat_range],
                              lon_range=[self.lon_range],
                              outputdir=self.outputdir,
                              download_files=True,
                              output_to_file=True,
                              output_format="MET")

  def load_cdf_file(self, sourcepath, data_category):

      # This function loads the ".nc" file using the netCDF4 library and
      # stores a pointer to it in the "data" variable
      
      # This function expects that we will pass the value series
      # we are looking for in the "data_category" parameter
      # So if we want the function to return all values for 
      # rain we shall call the function as:
      # load_file(sourcepath, sourcefile, 'daily_rain')
      self.logger.info('Loading netCDF4 file {}'.format(sourcepath))
      data_handle = netCDF4.Dataset(sourcepath, 'r')
      
      # Extracting the "year" from within the file itself, 
      # regardless of the file name
      data_year = int(data_handle.variables['time'].units[11:15])
      
      # Storing an array of values in a variable
      value_array = data_handle.variables[data_category][:]

      # Getting total grid size into variables
      # For Australia, the Latitude is a negative value, as it's counted as degrees North
      lat_total_value_count = len(data_handle.variables['lat'])
      first_lat = data_handle.variables['lat'][0].item()
      last_lat = data_handle.variables['lat'][lat_total_value_count-1].item()
      
      # Longitude is positive, as it's counted as degrees East
      lon_total_value_count = len(data_handle.variables['lon'])
      first_lon = data_handle.variables['lon'][0].item()
      last_lon = data_handle.variables['lon'][lon_total_value_count-1].item()
      
      # Defining the total range of Lat and Lon so that we can then 
      # find the position of a particular value within those arrays
      # using numpy.argwhere()
      lat_range = np.arange(first_lat,last_lat+0.05,0.05).round(decimals=2)
      lon_range = np.arange(first_lon,last_lon+0.05,0.05).round(decimals=2)
      
      data_dict = {
          
          "value_array": value_array, 
          "data_year": data_year,
          "lat_range": lat_range,
          "lon_range": lon_range
          
      }    
      
      # Closing the file now that we have extracted the data we wanted
      # so as to save RAM
      data_handle.close()
      
      # returning our dictionary with relevant values
      return data_dict

  def download_file_from_silo_s3(self, year, variable_short_name, output_file_dir = os.getcwd()):
      # This function connects to the public S3 site for SILO and downloads the specified file
      # For a list of variables to use in "variable_short_name" see
      # https://silo.longpaddock.qld.gov.au/climate-variables
      # Most common are: daily_rain, max_temp, min_temp
      # Example, call the function like: download_file_from_silo_s3(2011,'evap_pan')
      # The above will save to the current directory, however, you can also pass
      # your own like: download_file_from_silo_s3(2011,'daily_rain','C:\\Downloads\\SILO\2011')
      
      filename = str(year) + "." + variable_short_name + ".nc"
      url = 'https://s3-ap-southeast-2.amazonaws.com/silo-open-data/annual/{}/{}'.format(variable_short_name, filename)

      # Let's first check whether the file has already been downloaded
      # if it has, let's return without downloading it again
      output_file = output_file_dir + "\\" + filename
      
      if pathlib.Path(output_file).is_file():
          print("File {} already exists. Skipping download...".format(output_file))
          return
      
      r = requests.get(url, stream=True)
      
      with open(output_file, 'wb') as f:
          print("Downloading file {}...".format(output_file))
          shutil.copyfileobj(r.raw, f)

  def get_values_from_array(self, lon, lat, lat_range, lon_range, value_array, file_year, variable_short_name):
       
      # Checking if this is a leap-year  
      if (( file_year%400 == 0) or (( file_year%4 == 0 ) and ( file_year%100 != 0))):
          year = np.arange(0,366,1)
      else: 
          year = np.arange(0,365,1)
          
      data_values = []
      lon_values = []
          
      lat_position_in_array = np.argwhere(lat_range == lat).item()
      lon_position_in_array = np.argwhere(lon_range == lon).item()
      
      
      for day in year:
          # let's retrieve the specific data value first
          val = value_array[day][lat_position_in_array][lon_position_in_array]

          if type(val) is not np.ma.core.MaskedConstant:
              val = round(val,1)
              # if the value is NOT "masked" then we have an actual value
              # (as opposed to a "null") and we will append it to the data_values list
              data_values.append(val)
              
          else:
              # if the value is "masked" then it's non-existent. 
              # If you want to append a NaN ("None") value to the final df
              # please uncomment the below. Otherwise it is ignored.
              
              # data_values.append(None)
              
              # Ignoring anything without a value
              pass


      # we need to get the total amount of values collected
      # if there was "NO" data available for a particular combination
      # of lat & lon, then the total_values collected should equal "0"
      # meaning: there was no data for that point in the grid.
      # If this is the case, then the function will simply return with
      # a "no_values"
      total_values = len(data_values)
      if total_values == 0:
          raise ValueError('No data for the lat & lon combination provided')
      
      # let's now create a numpy array containing the "latitude" value
      # that we are pivoting off of in this loop iteration. The same value
      # should be repeated as many times as "lon" values there are (841)
      lat_values = np.full(total_values, lat)

      # let's do the same as above but for the "longitude" dimension
      lon_values = np.full(total_values, lon)

      # now we need to fill a PANDAS DataFrame with the lists we've been 
      # compiling.
      # Uncomment below if you want to also get lat and lon values in output df
      '''
      pandas_dict_of_items = {'lat': lat_values,
                              'lon': lon_values,
                              'day': year,
                              'rain': data_values}
      '''

      pandas_dict_of_items = {'day': year,
                              variable_short_name: data_values}
      
      df = pd.DataFrame.from_dict(pandas_dict_of_items)
      
      # making the julian day match the expected
      df['day'] += 1
      
      # adding a column with the "year" to the df
      df.insert(0, 'year', file_year)
      
      return df

  def generate_silo_dataframe(self, year_range, variable_short_name, lat_range, lon_range, outputdir, download_files=False, output_to_file=True, output_format="CSV"):

        '''
        Creation of the DataFrame and Files
        ===================================

        We will iterate through each "latitude" value and, 
        within this loop, we will iterate through all the different 
        "longitude" values for a given year. Results for each year
        are collected inside the "yearly_df" with "yearly_df.append"
        At the end, it will output a file with all the contents if
        "output_to_file=True" (by default it is "True")
        '''
        self.logger.info('Generating DataFrames')

        # let's first create an empty df to store 
        # all data for a given year
        yearly_df = pd.DataFrame()

        # checking whether a year range with "-" was provided
        # if this is the case, generate a list out of it
        # TODO: handle lists of year ranges like [1999-2001,2005-2019]
        if "-" in year_range[0]:
            first_year = int(year_range[0].split("-")[0])
            last_year = int(year_range[0].split("-")[1]) + 1
            year_range = np.arange(first_year,last_year,1)

        # Loading and/or Downloading the files
        for year in year_range:

            self.logger.info('Processing data for year {}'.format(year))

            # should we download the file first?
            if download_files == True:
                self.logger.debug('Attempting to download files')
                download_file_from_silo_s3(year, variable_short_name, outputdir)

            # Opening the target CDF database
            # We need to check whether we were passed a directory with multiple files inside
            # or a single file to process.
            if outputdir.is_dir() == True:
                sourcefile = str(year) + "." + variable_short_name + ".nc"
                sourcepath = outputdir/sourcefile
            elif outputdir.is_file() == True:
                sourcepath = outputdir

            if sourcepath.exists() == False:
                self.logger.error('Could not find file {}. Please make sure you have downloaded the required netCDF4 files in the format "year.variable.nc" to the output directory. Skipping...'.format(sourcepath))
                continue

            data = load_cdf_file(sourcepath, variable_short_name)
        
            # Now iterating over lat and lon combinations
            # Each year-lat-lon matrix generates a different file
            self.logger.info('Iterating over Lat and Lon value combinations')
            
            for lat in lat_range:

                for lon in lon_range:

                    file_year = data['data_year']

                    self.logger.info('Processing Lat {} - Lon {} for year {}'.format(lat, lon, file_year))

                    # here we are checking whether the get_values_from_cdf function
                    # returns with a ValueError (meaning there were no values for
                    # that particular lat & long combination). If it does return
                    # with an error, we skip this loop and don't produce any output files
                
                    try: 
                        temp_df = get_values_from_array(lon, lat, data['lat_range'], data['lon_range'], data['value_array'], file_year, variable_short_name)
                    except ValueError:
                        pass

                    yearly_df = yearly_df.append(temp_df, ignore_index=True)
                    
                    # Should we generate any file output?
                    if output_to_file == True:
                        # Should we output using MET file format?
                        if output_format == "MET":

                            if outputdir.is_dir() == True:
                                metfile_name = '{}-{}-{}.met'.format(variable_short_name,lat,lon)
                                self.logger.info('Writting .met file {} to {}'.format(metfile_name, output_dir))
                        
                        # Should we output using MET file format?
                        elif output_format == "CSV":
                            # let's build the name of the file based on the value of the 
                            # first row for latitude, the first row for longitude and then 
                            # the year (obtained from the name of the file with file_year = int(sourcefile[:4]))
                            # Note: there is a better method for obtaining this by looking at the
                            # "time" variable, see here below:

                            if outputdir.is_dir() == True:
                                csv_file_name = '{}-{}-{}-{}.csv'.format(variable_short_name, file_year, lat, lon)
                                self.logger.info('Writting CSV file {} to {}'.format( csv_file_name, outputdir))
                                yearly_df.to_csv(csv_file_name, sep=',', index=False, mode="a")

                    # when we get out of this Longitude leaf node, we would have
                    # completed the iteration for the first year-lat-lon combination, 
                    # we will have a df containing either 365 or 366 rows, we need to
                    # "reset" the yearly_df back to zero so we can process the next matrix
                    yearly_df = pd.DataFrame()

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
  starttime = strftime("%Y-%m-%d %H:%M:%S", time.localtime())
  logger.info("Starting POPBEAST Climate Automation Framework")
  
  # Grab an instance of the SILO class
  silo_instance = SILO(logger, pargs.output_directory, pargs.climate_variable, pargs.year_range, pargs.latitude_range, pargs.longitude_range)
  # Start to process the records
  silo_instance.process_records(pargs.action)
    
  # Capturing end time for debugging purposes
  et = datetime.now()
  endtime = strftime("%Y-%m-%d %H:%M:%S", time.localtime())
  
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