#!/usr/bin/env python3

'''
 NAME: BESTIAPOP (POPBEAST)
 VERSION: 2.5
 DATA ANALYTICS SPECIALIST - CORE DEVELOPER: Diego Perez (@darkquassar / https://linkedin.com/in/diegope) 
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
    v2.5 - Implemented MultiProcessing for MET file generation, fixed Pandas warnings, decoupled output generation from data carving, added "days" counter for proper output when tasks run longer than 24hs.
    
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
import multiprocessing as mp
import pandas as pd
import requests
import os
import s3fs
import sys
import time
import warnings
import xarray as xr
from datetime import datetime as datetime
from jinja2 import Template
from numpy import array
from pathlib import Path
from tqdm import tqdm

warnings.filterwarnings("ignore")

class Arguments():
    """This class defines the arguments used in the commandline and is invoked by the Main() method to obtain a parsed Argparse logger
    """

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
            #choices=["daily_rain", "monthly_rain", "max_temp", "min_temp", "vp", "vp_deficit", "evap_pan", "evap_syn", "evap_comb", "radiation", "rh_tmax", "rh_tmin", "et_short_crop", "et_tall_crop", "et_morton_actual", "et_morton_potential", "et_morton_wet", "mslp"],
            default="daily_rain",
            required=True
        )

        self.parser.add_argument(
            "-latf", "--latitude-file",
            help="A file containing a single column with a list of latitudes that you would like BestiaPop to extract data from.",
            type=self.extract_coord_from_file,
            default=None,
            required=False
        )

        self.parser.add_argument(
            "-lonf", "--longitude-file",
            help="A file containing a single column with a list of longitudes that you would like BestiaPop to extract data from.",
            type=self.extract_coord_from_file,
            default=None,
            required=False
        )

        self.parser.add_argument(
            "-lat", "--latitude-range",
            help="The latitude range to download data from the grid, separated by a ""space"", in increments of 0.05. It also accepts single values. Examples: -lat ""-40.85 -40.90"" \n -lat ""30.10 33"" \n -lat -41",
            type=self.space_separated_list_float,
            default=None,
            required=False
        )

        self.parser.add_argument(
            "-lon", "--longitude-range",
            help="The longitude range to download data from the grid, separated by a ""space"", in increments of 0.05. It also accepts single values. Examples: -lon ""145.45 145.5"" \n -lon ""145.10 146"" \n -lon 145",
            type=self.space_separated_list_float,
            required=False
        )

        self.parser.add_argument(
            "-i", "--input-directory",
            help="For ""convert-nc4-to-met"" and ""convert-nc4-to-csv"", the file or folder that will be ingested as input in order to extract the specified data. Example: -i ""C:\\some\\folder\\2015.daily_rain.nc"". When NOT specified, the tool assumes it needs to get the data from the cloud. For ""generate-met-file"", the local folder where BestiaPop will find the required NetCDF files to generate the required MET file, example: -i ""C:\\some\\folder\\"". When ""-i"" is used with ""generate-met-file"" then MET creation won't use S3 cloud files as the source.",
            type=str,
            default=None,
            required=False
        )

        self.parser.add_argument(
            "-m", "--multiprocessing",
            help="This switch will enable multiprocessing for enhanced performance and reduce processing times when utilizing multiple cores",
            action="store_true",
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

    def extract_coord_from_file(self, file):
        self.logger.info("A file has been provided with coordinate values, processing it...")
        coordinate_list_table = pd.read_csv(file, names=["coord"])
        coordinate_list_array = np.array(coordinate_list_table.coord.to_list(), dtype=float)
        return coordinate_list_array

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
    """The main class that performs the majority of NetCDF file download and data extraction

        Args:
            logger (str): A pointer to an initialized Argparse logger
            action (str): the type of action to be performed by BestiaPop. Available choices are: download-silo-file (it will only download a particular SILO file from S3 to your local disk), convert-nc4-to-met (it will only convert a local or S3 file from NC4 format to MET), convert-nc4-to-csv(it will only convert a local or S3 file from NC4 format to CSV), download-and-convert-to-met (combines the first two actions)
            inputpath (str): if the NetCDF files to be processed are stored locally, this path will be used to look for all the files required to extract data from the different year, latitude and longitude ranges
            outputpath (str): the path where generated output files will be stored
            output_type (str): the type of output
            variable_short_name (str): 
            year_range (str): a starting and ending year separated by a dash, example: "2012-2016". This string gets broken down into numpy.ndarray array afterwards.
            lat_range (str): a start and end latitude separated by a "space", example: "-41.15 -41.05". This string gets broken down into numpy.ndarray array afterwards. 
            lon_range (str): a start and end latitude separated by a "space", example: "145.5 145.6". This string gets broken down into numpy.ndarray array afterwards.
            multiprocessing (bool): a switch that tells BestiaPop to process records using parallel computing with python's multiprocessing module.

        Returns:
            SILO: A class object with access to SILO methods
    """

    def __init__(self, logger, action, outputpath, output_type, inputpath, variable_short_name, year_range, lat_range, lon_range, multiprocessing):

        # Checking that valid input has been provided
        self.logger = logger
        if not lat_range:
            self.logger.error('You have not provided a valid value for latitude range. Cannot proceed.')
        if not lon_range:
            self.logger.error('You have not provided a valid value for longitude range. Cannot proceed.')
        if not lat_range or not lon_range:
            sys.exit()

        # Initializing variables
        # For parallel multiprocessing
        self.multiprocessing = multiprocessing
        self.total_parallel_met_df = pd.DataFrame()
        self.final_parallel_lon_range = np.empty(0)
        self.datasource = None

        self.action = action
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
        if isinstance(lat_range, np.ndarray):
            # The user passed in a file with an array of latitudes
            # this file was processed during the argument parsing phase
            # and a numpy.ndarray was returned. Nothing else to do.
            self.lat_range = lat_range
        else:
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

                # Find absolute distance to account for missing values
                # numpy.arange erratic behaviour with floats: https://numpy.org/doc/stable/reference/generated/numpy.arange.html
                lat_value_count = np.round((abs(first_lat-last_lat) / 0.05), decimals=0)
                lat_range = np.arange(first_lat,last_lat,0.05).round(decimals=2)
                
                # Check the number spread
                if int(lat_value_count+1) != len(lat_range):
                    lat_range = np.arange(first_lat,np.round((last_lat+0.05), decimals=2),0.05).round(decimals=2).tolist()
                    if int(lat_value_count+1) != len(lat_range):
                        # Must get rid of last float
                        lat_range = np.delete(lat_range,(len(lat_range)-1),0)
            
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

                # Find absolute distance to account for missing values
                # numpy.arange erratic behaviour with floats: https://numpy.org/doc/stable/reference/generated/numpy.arange.html
                lon_value_count = np.round((abs(first_lon-last_lon) / 0.05), decimals=0)
                lon_range = np.arange(first_lon,last_lon,0.05).round(decimals=2)

                # Check the number spread
                if int(lon_value_count+1) != len(lon_range):
                    lon_range = np.arange(first_lon,np.round((last_lon+0.05), decimals=2),0.05).round(decimals=2).tolist()
                    if int(lat_value_count+1) != len(lat_range):
                        # Must get rid of last float
                        lon_range = np.delete(lon_range,(len(lon_range)-1),0)

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

    def process_records_parallel(self, action):
        """Perform selected actions on NetCDF4 file in parallel mode 

        Args:
            action {'download-silo-file', 'convert-nc4-to-met', 'convert-nc4-to-csv'} (string): the type of action to be performed in parallel. Example: download-silo-file, convert-nc4-to-met, convert-nc4-to-csv, generate-met-file
        """

        # Let's check what's inside the "action" variable and invoke the corresponding function
        if action == "download-silo-file":
            # TODO
            self.logger.info("Parallel Computing for {} not implemented yet".format(action))

        elif action == "convert-nc4-to-met":
            # TODO
            self.logger.info("Parallel Computing for {} not implemented yet".format(action))

        elif action == "convert-nc4-to-csv":
            # TODO
            self.logger.info("Parallel Computing for {} not implemented yet".format(action))

        elif action == "generate-met-file":
            # setup value of datasource property to allow for desicions on downstream functions
            self.datasource = "SILO"

            # Let's generate a worker pool equal to the amount of cores available
            self.logger.info("\x1b[47m \x1b[32mGenerating PARALLEL WORKER POOL consisting of {} WORKERS \x1b[0m \x1b[39m".format(mp.cpu_count()))
            worker_pool = mp.Pool(mp.cpu_count())
            worker_jobs = worker_pool.map_async(self.process_parallel_met, self.year_range)
            worker_pool.close()
            #worker_pool.join() # block until all processes have finished

            while True:
                if not worker_jobs.ready():
                    self.logger.info("Parallel Jobs left: {}".format(worker_jobs._number_left))
                    worker_jobs.wait(20)
                else:
                    break

            # Pipe all results from the queue to a variable
            final_df_latlon_tuple_list = worker_jobs.get()

            # Generating MET Files
            # Extract final pre-MET dataframe and final list of coordinates for output processing
            for element in final_df_latlon_tuple_list:
                # element is a tuple comprised of (pandas_df_with_data, numpy_array_for_coordinates)
                self.total_parallel_met_df = self.total_parallel_met_df.append(element[0])
                self.final_parallel_lon_range = np.concatenate((self.final_parallel_lon_range, element[1]))

            # Generate Output
            self.logger.info("Processing Output in Parallel")
            self.logger.info("\x1b[47m \x1b[32mGenerating PARALLEL WORKER POOL consisting of {} WORKERS \x1b[0m \x1b[39m".format(mp.cpu_count()))
            worker_pool = mp.Pool(mp.cpu_count())
            worker_jobs = worker_pool.map_async(self.process_parallel_output, self.lat_range)
            worker_pool.close()
            while True:
                if not worker_jobs.ready():
                    self.logger.info("Output Generator - Parallel Jobs left: {}".format(worker_jobs._number_left))
                    worker_jobs.wait(5)
                else:
                    break

    def process_parallel_output(self, lat_range):
        """Generate output files using multiple cores

        Args:
            lat_range (numpy.ndarray): A numpy array with all the desired latitudes whose data needs to be extracted and converted to an output format. This function is called by process_records_parallel.
        """

        try:
            self.generate_output(
                final_met_df=self.total_parallel_met_df,
                lat_range=[lat_range],
                lon_range=self.final_parallel_lon_range,
                outputdir=self.outputdir,
                output_type="met"
            )
    
        except KeyboardInterrupt:
            print("\n" + "Parallel process interrupted" + "\n\n")
            sys.exit()

    def process_parallel_met(self, year):
        """Process records using multiple cores

        Args:
            year (int): the year to extract information for. This function gets called iteratively by a multiprocessing Pool created by process_records_parallel.

        Returns:
            pandas.core.frame.DataFrame: the slice dataframe
        """

        try:
            final_df_latlon_tuple_list = self.generate_climate_dataframe(
                year_range=[year],
                variable_short_name=self.variable_short_name, 
                lat_range=self.lat_range,
                lon_range=self.lon_range,
                inputdir=self.inputdir,
                download_files=False
            )

        except KeyboardInterrupt:
            print("\n" + "Parallel process interrupted" + "\n\n")
            sys.exit()

        return final_df_latlon_tuple_list

    def process_records(self, action):
        """Processing records for non-parallel computing

        Args:
            action (str): the type of action to be performed
        """

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
            self.generate_climate_dataframe(
                year_range=self.year_range,
                variable_short_name=self.variable_short_name, 
                lat_range=self.lat_range,
                lon_range=self.lon_range,
                inputdir=self.inputdir,
                download_files=False
            )

        elif action == "generate-met-file":
            # setup value of datasource property to allow for desicions on downstream functions
            self.datasource = "SILO"
            
            self.logger.info('Downloading data and converting to {} format'.format(self.output_type))
            # 1. Let's invoke generate_climate_dataframe with the appropriate options
            final_df_latlon_tuple_list = self.generate_climate_dataframe(
                year_range=self.year_range,
                variable_short_name=self.variable_short_name, 
                lat_range=self.lat_range,
                lon_range=self.lon_range,
                inputdir=self.inputdir,
                download_files=False
            )

            # 2. Generate Output
            self.total_parallel_met_df = final_df_latlon_tuple_list[0]
            self.final_parallel_lon_range = final_df_latlon_tuple_list[1]
            self.generate_output(
                final_met_df=self.total_parallel_met_df,
                lat_range=self.lat_range,
                lon_range=self.final_parallel_lon_range,
                outputdir=self.outputdir,
                output_type="met"
            )

    def load_cdf_file(self, sourcepath, data_category, load_from_s3=True, year=None):
        """This function loads a NetCDF4 file either from the cloud or locally

        Args:
            sourcepath (str): when loading a NetCDF4 file locally, this specifies the source folder. Only the "folder" must be specified, the actual file name will be further qualified by BestiaPop grabbing data from the year and climate variable paramaters passed to the SILO class.
            data_category (str): the short name variable, examples: daily_rain, max_temp, etc.
            load_from_s3 (bool, optional): This parameter tells BestiaPop whether data should be fetched directly from the cloud. Defaults to True.
            year (int, optional): the year we want to extract data from, it is used to compose the final AWS S3 URL or to qualify the full path to the local NetCDF4 file we would like to load. Defaults to None.

        Returns:
            dict: a dictionary containing two items, "value_array" which is a xarray DataSet object and "data_year" which is the year that the NetCDF4 file contains data for, extracted by looking at the contents of the NetCDF4 file itself.
        """

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

    def download_file_from_silo_s3(self, year, variable_short_name, output_path = Path().cwd(), skip_certificate_checks=False):
        """Downloads a file from AWS S3 bucket

        Args:
            year (int): the year we require data for. SILO stores climate data as separate years like so: daily_rain.2018.nc
            variable_short_name (str): the climate variable short name as per SILO nomenclature, see https://www.longpaddock.qld.gov.au/silo/about/climate-variables/
            output_path (str, optional): The target folder where files should be downloaded. Defaults to Path().cwd().
            skip_certificate_checks (bool, optional): ask the requests library to skip certificate checks, useful when attempting to download files behind a proxy. Defaults to False.

        """

        # This function connects to the public S3 site for SILO and downloads the specified file
        # For a list of variables to use in "variable_short_name" see
        # https://www.longpaddock.qld.gov.au/silo/about/climate-variables/
        # Most common are: daily_rain, max_temp, min_temp
        # Example, call the function like: download_file_from_silo_s3(2011, "daily_rain")
        # The above will save to the current directory, however, you can also pass
        # your own like: download_file_from_silo_s3(2011,'daily_rain','C:\\Downloads\\SILO\2011')

        # We use TQDM to show a progress bar of the download status

        filename = str(year) + "." + variable_short_name + ".nc"
        url = 'https://s3-ap-southeast-2.amazonaws.com/silo-open-data/annual/{}/{}'.format(variable_short_name, filename)

        # Get pointer to URL
        try:
            req = requests.get(url, stream=True)
        except requests.exceptions.SSLError:
            self.logger.warning("Could not download file due to Certificate issues, potentially caused by your proxy. Relaxing Certificate Checking and attempting again...")
            self.logger.warning('Skipping SSL certificate checks for {}/{}'.format(variable_short_name, filename))
            req = requests.get(url, stream=True, verify=False)

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
        try:
            with open(output_file, 'ab') as f:
                self.logger.info('Downloading file {}...'.format(output_file))
                for chunk in req.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)
                        progressbar.update(1024)

        except:
            self.logger.error("Could not download SILO file")

        progressbar.close()

    def get_values_from_array(self, lat, lon, value_array, file_year, variable_short_name):
        """Extract values from a xarray.Dataset object

        Args:
            lat (float): the latitude that values should be returned for
            lon (float): the longitude that values should be returned for
            value_array (xarray.Dataset): the xarray Dataset object to extract values from
            file_year (string): the year of the file
            variable_short_name (string): the climate variable short name as per SILO nomenclature, see https://www.longpaddock.qld.gov.au/silo/about/climate-variables/

        Raises:
            ValueError: if there was "NO" data available for all days under a particular combination of lat & lon, then the total values collected should equal "0" (meaning, there was no data for that point in the grid). If this is the case, then the function will simply return with a "no_values" message and signal the calling function that it should ignore this particular year-lat-lon combination.

        Returns:
            pandas.core.frame.DataFrame: a dataframe containing 5 columns: the Julian day, the grid data value for that day, the year, the latitude, the longitude.
        """

        # This function will use xarray to extract a slice of time data for a combination of lat and lon values

        # Checking if this is a leap-year  
        if (( file_year%400 == 0) or (( file_year%4 == 0 ) and ( file_year%100 != 0))):
            days = np.arange(0,366,1)
        else: 
            days = np.arange(0,365,1)

        # If we are attempting to read from the cloud, use SILO's API instead of Xarray
        if self.datasource == "SILO":
            self.logger.debug("Reading array data using SILO API")

            # SILO Climate variable dict
            silo_climate_variable_code = {
                "daily_rain":           "R", 
                "monthly_rain":         "R",
                "max_temp":             "X",
                "min_temp":             "N",
                "vp":                   "V",
                "vp_deficit":           "D",
                "evap_pan":             "E",
                "evap_syn":             "S",
                "evap_comb":            "C",
                "radiation":            "J",
                "rh_tmax":              "H",
                "rh_tmin":              "G",
                "et_short_crop":        "F",
                "et_tall_crop":         "T",
                "et_morton_actual":     "A",
                "et_morton_potential":  "P",
                "et_morton_wet":        "W",
                "mslp":                 "M"
            }

            silo_api_url = "https://www.longpaddock.qld.gov.au/cgi-bin/silo/DataDrillDataset.php?lat={}&lon={}&format=json&start={}0101&finish={}1231&username=bestiapop@bestiapop.com&password=gui&comment={}".format(lat, lon, file_year, file_year, silo_climate_variable_code[variable_short_name])
            r = requests.get(silo_api_url)
            json_data = r.json()
            # The shape of returned data from SILO is: 
            '''
            'location': {'latitude': -41.1,
            'longitude': 145.5,
            'elevation': 298.1,
            'reference': 'R'},
            'extracted': 20200808,
            'data': [
                {'date': '2003-01-03',
                'variables': [{'source': 25, 'value': 1.4, 'variable_code': 'daily_rain'}]},
                {'date': '2003-01-04',
                'variables': [{'source': 25, 'value': 1.8, 'variable_code': 'daily_rain'}]}, ...
            ]
            '''
            
            data_values = [np.round(x['variables'][0]['value'], decimals=1) for x in json_data['data']]

        else:
            # Using a list comprehension to capture all daily values for the given year and lat/lon combinations
            # We round values to a single decimal
            self.logger.debug("Reading array data from NetCDF with xarray")

            # Alternatively: data_values = [np.round(x, decimals=1) for x in (value_array[variable_short_name].loc[dict(lat=lat, lon=lon)]).values]
            data_values = [np.round(x, decimals=1) for x in value_array[variable_short_name].sel(lat=lat, lon=lon).values]

            # closing handle to xarray DataSet
            value_array.close()

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

        return df

    def generate_climate_dataframe(self, year_range, variable_short_name, lat_range, lon_range, inputdir, download_files=False, load_from_s3=True):
        """Creation of the different Climate DataFrames

        Args:
            year_range (numpy.ndarray): a numpy array with all the years for which we are seeking data, each year equates to a different file in the SILO database.
            variable_short_name (str): the climate variable short name as per SILO nomenclature, see https://www.longpaddock.qld.gov.au/silo/about/climate-variables/
            lat_range (numpy.ndarray): a numpy array of latitude values to extract data from
            lon_range (numpy.ndarray): a numpy array of longitude values to extract data from
            inputdir (str): when selecting the option to generate MET files from local directories, this parameter must be specified, otherwise data will be fetched directly from cloud S3 buckets.
            download_files (bool, optional): a switch that tells BestiaPop to first download the file from the cloud before processing them. It may speed up certain data processing times. Defaults to False.
            load_from_s3 (bool, optional): whether data should be fetched directly from the cloud, whithout having to download a file locally. Defaults to True.

        Returns:
            tuple: a tuple consisting of (a) the final dataframe containing values for all years, latitudes and longitudes for a particular climate variable, (b) the curated list of longitude ranges (which excludes all those lon values where there were no actual data points). The tuple is ordered as follows: (final_dataframe, final_lon_range)
        """

        #We will iterate through each "latitude" value and, 
        #within this loop, we will iterate through all the different 
        #"longitude" values for a given year. Results for each year
        #are collected inside the "met_df" with "met_df.append"
        #At the end, it will output a file with all the contents if
        #"output_to_file=True" (by default it is "True")

        self.logger.debug('Generating DataFrames')

        # let's first create an empty df to store 
        # all data for a given variable-year-lat-lon combination
        met_df = pd.DataFrame()

        # empty df to append all the met_df to
        total_met_df = pd.DataFrame()

        # create an empty list to keep track of lon coordinates
        # where there are no values
        empty_lon_coordinates = []

        # Determine whether we are running multithreaded or not for nested loop efficiency
        # This method will allow us to swap the first two iterator levels in the 4-level nested loop
        if self.multiprocessing == True:
            main_loop_var = year_range
            main_loop_var_desc = "Year"
            secondary_loop_var = variable_short_name
            secondary_loop_var_desc = "Climate Variable"
        else:
            main_loop_var = variable_short_name
            main_loop_var_desc = "Climate Variable"
            secondary_loop_var = year_range
            secondary_loop_var_desc = "Year"

        # Loading and/or Downloading the files
        for main_element in tqdm(main_loop_var, ascii=True, desc=main_loop_var_desc):
            if self.multiprocessing == True:
                year = main_element
                self.logger.debug('Processing data for year {}'.format(year))
            else:
                climate_variable = main_element
                self.logger.debug('Processing data for climate variable {}'.format(climate_variable))

            for second_element in tqdm(secondary_loop_var, ascii=True, desc=secondary_loop_var_desc):
                if self.multiprocessing == True:
                    climate_variable = second_element
                    self.logger.debug('Processing data for climate variable {}'.format(climate_variable))
                else:
                    year = second_element
                    self.logger.debug('Processing data for year {}'.format(year))
                    

                # should we download the file first?
                if download_files == True:
                    self.logger.debug('Attempting to download files')
                    self.download_file_from_silo_s3(year, climate_variable, self.outputdir)

                # Opening the target CDF database
                # We need to check:
                # (1) should we fetch the data directly from AWS S3 buckets
                # (2) if files should be fetched locally, whether the user passed a directory with multiple files or just a single file to process.
                if inputdir:
                    # Setting this variable to false to know how to react at the end of each year loop
                    load_from_s3 = False

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
                    if self.datasource == "SILO":
                        self.logger.info("Datasource is: SILO. Reading data using SILO's API")
                        file_year = year
                    else:
                        data = self.load_cdf_file(None, climate_variable, load_from_s3=True, year=year)
                        file_year = data['data_year']
                    
            
                # Now iterating over lat and lon combinations
                # Each year-lat-lon matrix generates a different file
                
                for lat in tqdm(lat_range, ascii=True, desc="Latitude"):

                    for lon in lon_range:

                        # Skipping any longitude points that have already been proven to not contain any data
                        # This adds a slight performance improvement too

                        if lon in empty_lon_coordinates:
                            continue

                        self.logger.debug('Processing Variable {} - Lat {} - Lon {} for Year {}'.format(climate_variable, lat, lon, file_year))

                        # here we are checking whether the get_values_from_cdf function
                        # returns with a ValueError (meaning there were no values for
                        # that particular lat & long combination). If it does return
                        # with an error, we skip this loop and don't produce any output files
                    
                        try:
                            if self.datasource == "SILO":
                                var_year_lat_lon_df = self.get_values_from_array(lat, lon, None, file_year, climate_variable)
                            else:
                                var_year_lat_lon_df = self.get_values_from_array(lat, lon, data['value_array'], file_year, climate_variable)
                        except ValueError:
                            self.logger.warning("This longitude value will be skipped for the rest of the climate variables and years")
                            self.logger.warning("Deleting lon {} in array position {}".format(lon, np.where(lon_range == lon)[0][0]))
                            # Append empty lon value to list
                            empty_lon_coordinates.append(lon)                         
                            continue
                        
                        # delete the var_year_lat_lon_df back to zero.
                        total_met_df = total_met_df.append(var_year_lat_lon_df)
                        del var_year_lat_lon_df

                # We reached the end of the year loop
                # we need must close the open handle to the s3fs file to free up resources
                if load_from_s3 == True:
                    if self.datasource == "SILO":
                        None
                    else:
                        self.remote_file_obj.close()
                        self.logger.debug("Closed handle to cloud s3fs file {}".format(self.silo_file))

        # Remove any empty lon values from longitude array so as to avoid empty MET generation
        empty_lon_array = np.array(empty_lon_coordinates)
        final_lon_range = np.setdiff1d(lon_range, empty_lon_array)

        # Return results
        return (total_met_df, final_lon_range)

    def generate_output(self, final_met_df, lat_range, lon_range, outputdir, output_type="met"):
        """Generate required Output based on Output Type selected

        Args:
            final_met_df (pandas.core.frame.DataFrame): the pandas daframe containing all the values that are going to be parsed into a specific output
            lat_range (numpy.ndarray): an array of latitude values to select from the final_met_df
            lon_range (numpy.ndarray): an array of longitude values to select from the final_met_df
            outputdir (str): the folder that will be used to store the output files
            output_type (str, optional): the output type: csv (not implemented yet), json(not implemented yet), met. Defaults to "met".

        """

        if output_type == "met":
            # Rename variables
            # Check if final df is empty, if so, then return and do not proceed with the rest of the file
            if final_met_df.empty == True:
                self.logger.error("No data in final dataframe. No file can be generated. Exiting...")
                return

            try: 
                final_met_df = final_met_df.rename(columns={"days": "day","daily_rain": "rain",'min_temp':'mint','max_temp':'maxt','radiation':'radn'})
                final_met_df = final_met_df.groupby(['lon', 'lat', 'year', 'day'])[['radn', 'maxt', 'mint', 'rain']].sum().reset_index()
                
                self.logger.info("Proceeding to the generation of MET files")

                for lat in tqdm(lat_range, ascii=True, desc="Latitude"):
                    
                    for lon in tqdm(lon_range, ascii=True, desc="Longitude"):

                        met_slice_df = final_met_df[(final_met_df.lon == lon) & (final_met_df.lat == lat)]
                        del met_slice_df['lat']
                        del met_slice_df['lon']

                        self.generate_met(outputdir, met_slice_df, lat, lon)

                        # Delete unused df
                        del met_slice_df

            except KeyError as e:
                self.logger.error("Could not find all required climate variables to generate MET: {}".format(str(e)))

        if output_type == "csv":
            # TODO: Clean this up...

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

            generate_final_csv = False
            if generate_final_csv == True:
                # Creating final CSV file
                csv_file_name = 'mega_final_data_frame.csv'
                self.logger.info('Writting CSV file {} to {}'.format(csv_file_name, outputdir))
                full_output_path = outputdir/csv_file_name
                final_met_df.to_csv(full_output_path, sep=',', na_rep=np.nan, index=False, mode='w', float_format='%.2f')

    def generate_met(self, outputdir, met_dataframe, lat, lon):
        """Generate APSIM MET File

        Args:
            outputdir (str): the folder where the generated MET files will be stored
            met_dataframe (pandas.core.frame.DataFrame): the pandas dataframe slice to convert to MET file
            lat (float): the latitude for which this MET file is being generated
            lon (float): the longitude for which this MET file is being generated
        """

        # Creating final MET file

        # Setting up Jinja2 Template for final MET file if required
        # Text alignment looks weird here but it must be left this way for proper output
        met_file_j2_template = '''[weather.met.weather]
!station number={{ lat }}-{{ lon }}
!This climate file is created by BestiaPop on {{ current_date }}
!Source: {{ data_source }}
!Date period from: {{ year_from }} to {{ year_to }}
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
        met_dataframe.loc[:, 'cte'] = 1997364
        met_dataframe.loc[:, 'day2'] = met_dataframe['day'] + met_dataframe['cte']
        met_dataframe.loc[:, 'date'] = (pd.to_datetime((met_dataframe.day2 // 1000)) + pd.to_timedelta(met_dataframe.day2 % 1000, unit='D'))
        met_dataframe.loc[:, 'month'] = met_dataframe.date.dt.month
        month=met_dataframe.loc[:, 'month']

        met_dataframe.loc[:, 'tmean'] = met_dataframe[['maxt', 'mint']].mean(axis=1)
        tmeanbymonth = met_dataframe.groupby(month)[["tmean"]].mean()
        maxmaxtbymonth = tmeanbymonth['tmean'].max()
        minmaxtbymonth = tmeanbymonth['tmean'].min()
        amp = np.round((maxmaxtbymonth-minmaxtbymonth), decimals=5)

        # Calculate tav
        tav = tmeanbymonth.mean().tmean.round(decimals=5)
        
        # Configure some header variables
        current_date = datetime.now().strftime("%d/%m/%Y")
        data_source = "SILO"
        # TODO: data_source must be variable based on what the actual source is, whether SILO or NASAPOWER

        in_memory_met = j2_template.render(lat=lat, lon=lon, tav=tav, amp=amp, vardata=met_df_text_output)
        df_output_buffer.close()

        full_output_path = outputdir/'{}-{}.met'.format(lat, lon)
        with open(full_output_path, 'w+') as f:
            self.logger.info('Writting MET file {}'.format(full_output_path))
            f.write(in_memory_met)

def main():
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

  # Instantiating the arguments class
  args = Arguments(sys.argv)
  pargs = args.get_args()

  # Pre-process the Latitude and Longitude argument
  if pargs.__contains__("latitude_file"):
      if pargs.latitude_file != None:
        pargs.latitude_range = pargs.latitude_file
  if pargs.__contains__("longitude_file"):
      if pargs.longitude_file != None:
        pargs.longitude_range = pargs.longitude_file
  
  # Capturing start time for debugging purposes
  st = datetime.now()
  logger.info("Starting BESTIAPOP Climate Data Mining Automation Framework")
  
  # Grab an instance of the SILO class
  silo_instance = SILO(logger, pargs.action, pargs.output_directory, pargs.output_type, pargs.input_directory, pargs.climate_variable, pargs.year_range, pargs.latitude_range, pargs.longitude_range, multiprocessing=pargs.multiprocessing)
  # Start to process the records
  if pargs.multiprocessing == True:
    logger.info("\x1b[47m \x1b[32mMultiProcessing selected \x1b[0m \x1b[39m")
    silo_instance.process_records_parallel(pargs.action)
  else:
    silo_instance.process_records(pargs.action)
    
  # Capturing end time for debugging purposes
  et = datetime.now()
  
  days = (et-st).days
  hours, remainder = divmod((et-st).seconds, 3600)
  minutes, seconds = divmod(remainder, 60)

  logger.info("Finished this unit of work")
  logger.info('Workload took: \x1b[47m \x1b[32m{} days / {} hours / {} minutes / {} seconds \x1b[0m \x1b[39m'.format(days,hours,minutes,seconds))

if __name__ == '__main__':
    try:
        main()
        sys.exit()
    
    except KeyboardInterrupt:
        print("\n" + "I've been interrupted by a mortal" + "\n\n")
        sys.exit()