#!/usr/bin/env python3

'''
    NAME: BESTIAPOP (POPBEAST) ("My heroe es, la gran bestia pop!", thanks Redonditos de Ricota)
    DESCRIPTION: A python package to automate the extraction and processing of climate data for crop modelling.
    VERSION: 3.0

    DATA ANALYTICS SPECIALIST - CORE DEVELOPER: Diego Perez (@darkquassar / https://linkedin.com/in/diegope) 
    DATA SCIENTIST - MODEL DEVELOPER: Jonathan Ojeda (https://researchgate.net/profile/Jonathan_Ojeda)
 
    ACKNOWLEDGEMENTS:
        * This work was supported by the JM Roberts Seed Funding for Sustainable Agriculture 2020 and the Tasmanian Institute of Agriculture, University of Tasmania.
        * SILO (Scientific Information for Land Owners), see: https://www.longpaddock.qld.gov.au/silo/about/
        * NASAPOWER, see: https://power.larc.nasa.gov/

    LICENSE:
        * Please refer to the LICENSE file at the root of the repository for a modified BSD clause that includes the acknowledgements required by the open source climate data providers that BestiaPop utilizes (SILO and NASAPOWER).

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
        v3.0 - Major version jump due to complete restructuring of BestiaPop. Broke down the single script into multiple ones according to functionalities to make it more extensible and prepare for future enhancements. New features: ****
        
    TODO:
        1. Implement a new functionality in APSIM that automatically executes this code by only providing lat and lon values (and generating a MET)
        2. Use AutoComplete package to help in commandline params: https://github.com/kislyuk/argcomplete.

'''

import argparse
import calendar
import h5netcdf
import logging
#import netCDF4
import numpy as np
import multiprocessing as mp
import os
import pandas as pd
import re
import requests
import s3fs
import sys
import time
import warnings
import xarray as xr

from connectors import (silo_connector, nasapower_connector)
from common import bestiapop_utils
from producers import output

from datetime import datetime as datetime
from numpy import array
from pathlib import Path

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
            help="The type of operation to want to perform: download-nc4-file (it will only download a particular NetCDF4 file from the cloud to your local disk, the source can be specified with the --data-source parameter), convert-nc4 (it will only convert a local or cloud file from NC4/HDF5 format to the output format specified with --output-type), generate-climate-file (the default action, it will generate a particular climate file like MET (for APSIM) or WHT (for DSSAT) using the parameters passed in as years, climate variable, etc.)",
            type=str,
            choices=["download-nc4-file", "convert-nc4", "generate-climate-file"],
            default="generate-climate-file",
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
            "-s", "--data-source",
            help="The source of the climate data, which to date can either be SILO (default, Australia only) or NASAPOWER (world wide, not yet implemented)",
            type=str,
            choices=["silo", "nasapower"],
            default="silo",
            required=False
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
            help="For ""convert-nc4"", the file or folder that will be ingested as input in order to extract the specified data. Example: -i ""C:\\some\\folder\\2015.daily_rain.nc"". When NOT specified, the tool assumes it needs to get the data from the cloud. For ""generate-climate-file"", the local folder where BestiaPop will find the required NetCDF files to generate the required Climate File, example: -i ""C:\\some\\folder\\"". When ""-i"" is used with ""generate-climate-file"" then Climate File creation won't use cloud sources like S3 or API to extract the required data.",
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
            help="This argument is required and represents the directory that we will use to (a) save any output (MET, CSV, etc.) when you are generating a climate file or (b) save files converted from NetCDF4 format to CSV or MET. If no folder is passed in, the current directory is assumed to the right directory. Examples: (1) download files to a local disk: -o ""C:\\some\\folder\\path""",
            type=str,
            default=os.getcwd(),
            required=False
        )

        self.parser.add_argument(
            "-ot", "--output-type",
            help="This argument will tell the script whether you want the output file to be in MET (default, for APSIM), WHT (for DSSAT), CSV (not yet implemented) or JSON (not yet implemented) format",
            type=str,
            choices=["met", "wht", "csv", "json", "stdout"],
            default="met",
            required=False
        )

        self.pargs = self.parser.parse_args()

    def extract_coord_from_file(self, file):
        #self.logger.info("A file has been provided with coordinate values, processing it...")
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

class CLIMATEBEAST():
    """The main class that performs the majority of NetCDF file download and data extraction

        Args:
            logger (str): A pointer to an initialized Argparse logger
            action (str): the type of action to be performed by BestiaPop. Available choices are: download-nc4-file (it will only download a particular NetCDF4 file from the cloud to your local disk, the source can be specified with the --data-source parameter), convert-nc4 (it will only convert a local or cloud file from NC4/HDF5 format to the output format specified with --output-type), generate-climate-file (the default action, it will generate a particular climate file like MET (for APSIM) or WHT (for DSSAT) using the parameters passed in as years, climate variable, etc.)
            data_source (str): the source database for the climate data: SILO (Australia only) or NASAPOWER (world wide)
            input_path (str): if the NetCDF files to be processed are stored locally, this path will be used to look for all the files required to extract data from the different year, latitude and longitude ranges
            output_path (str): the path where generated output files will be stored
            output_type (str): the type of output
            climate_variables (str): 
            year_range (str): a starting and ending year separated by a dash, example: "2012-2016". This string gets broken down into numpy.ndarray array afterwards.
            lat_range (str): a start and end latitude separated by a "space", example: "-41.15 -41.05". This string gets broken down into numpy.ndarray array afterwards. 
            lon_range (str): a start and end latitude separated by a "space", example: "145.5 145.6". This string gets broken down into numpy.ndarray array afterwards.
            multiprocessing (bool): a switch that tells BestiaPop to process records using parallel computing with python's multiprocessing module.

        Returns:
            CLIMATEBEAST: A class object with access to CLIMATEBEAST methods
    """

    def __init__(self, logger, action, data_source, output_path, output_type, input_path, climate_variables, year_range, lat_range, lon_range, multiprocessing):

        # Checking that valid input has been provided
        self.logger = logger
        if action != "download-nc4-file":
            if not lat_range:
                self.logger.error('You have not provided a valid value for latitude range. Cannot proceed.')
            if not lon_range:
                self.logger.error('You have not provided a valid value for longitude range. Cannot proceed.')
            if not lat_range or not lon_range:
                sys.exit()

        # Initializing variables
        # For parallel multiprocessing
        self.multiprocessing = multiprocessing
        self.total_parallel_climate_df = pd.DataFrame()
        self.final_parallel_lon_range = np.empty(0)

        # General
        self.action = action
        self.data_source = data_source
        self.logger.info('Initializing {}'.format(__name__))
        if input_path is not None:
            self.input_path = Path(input_path)
        else:
            self.input_path = None
        self.outputdir = Path(output_path)
        self.output_type = output_type
        self.climate_variables = climate_variables
        
        # Get a handle to an instance of BestiaPop Utilities
        my_beast_utils = bestiapop_utils.MyUtilityBeast(input_path=self.input_path)

        # Obtain year range list
        self.year_range = my_beast_utils.get_years_list(year_range)

        # Obtain coordinates range
        # The granularity of the returned range will depend whether the source data is SILO or NASA POWER
        self.lat_range = my_beast_utils.get_coordinate_numpy_list(lat_range, "latitude", self.data_source)
        self.lon_range = my_beast_utils.get_coordinate_numpy_list(lon_range, "longitude", self.data_source)

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

    def process_parallel_records(self, action):
        """Perform selected actions on NetCDF4 file in parallel mode 

        Args:
            action {'download-nc4-file', 'convert-nc4', 'generate-climate-file'} (string): the type of action to be performed in parallel. Example: download-nc4-file, convert-nc4, generate-climate-file
        """

        # Let's check what's inside the "action" variable and invoke the corresponding function
        if action == "download-nc4-file":
            # TODO
            self.logger.info("Parallel Computing for {} not implemented yet".format(action))

        elif action == "convert-nc4":
            # TODO
            # Allow for the conversion of inputs to multiple outputs at the same time, that would be cool, and in parallel imagine!

            if self.output_type == "met":
                self.logger.info('Action {} not implemented yet'.format(action))
            if self.output_type == "wht":
                self.logger.info('Action {} not implemented yet'.format(action))
            if self.output_type == "csv":
                self.logger.info('Action {} not implemented yet'.format(action))
            if self.output_type == "json":
                self.logger.info('Action {} not implemented yet'.format(action))

        elif action == "generate-climate-file":

            try:
                # Let's generate a worker pool equal to the amount of cores available
                self.logger.info("\x1b[47m \x1b[32mGenerating PARALLEL WORKER POOL consisting of {} WORKERS \x1b[0m \x1b[39m".format(mp.cpu_count()))

                # Setting a MultiProcessing Manager to be able to terminate the pool of workers
                # if a SIGKILL is received from the keyboard whilst running inside a worker process
                # Thanks!: https://stackoverflow.com/questions/26068819/how-to-kill-all-pool-workers-in-multiprocess
                
                # Capture the coordinate that has the highest range so we can 
                # parallelize based on that
                if len(self.lat_range) > len(self.lon_range):
                    self.parallel_var = "lat"
                    parallel_var_range = self.lat_range
                elif len(self.lat_range) < len(self.lon_range):
                    self.parallel_var = "lon"
                    parallel_var_range = self.lon_range
                else:
                    self.parallel_var = "lat"
                    parallel_var_range = self.lat_range

                multiproc_manager = mp.Manager()
                self.multiproc_event = multiproc_manager.Event()
                worker_pool = mp.Pool(mp.cpu_count())
                worker_jobs = worker_pool.map_async(self.process_parallel_met, parallel_var_range)
                worker_pool.close()
                #worker_pool.join() # block until all processes have finished

                while True:
                    if not worker_jobs.ready():
                        self.logger.info("Parallel Jobs left: {}".format(worker_jobs._number_left))
                        worker_jobs.wait(20)
                    else:
                        break
                
                # multiproc_event.wait()
                # worker_pool.terminate()

                # Pipe all results from the queue to a variable
                final_df_latlon_tuple_list = worker_jobs.get()

                # Generating Climate Files
                # Extract final pre-final-output dataframe and final list of coordinates for output processing
                for element in final_df_latlon_tuple_list:
                    # element is a tuple comprised of (pandas_df_with_data, numpy_array_for_coordinates)
                    # we need to create a final_parallel_lon_range that contains only unique values
                    self.total_parallel_climate_df = self.total_parallel_climate_df.append(element[0])
                    self.final_parallel_lon_range = np.unique(np.concatenate((self.final_parallel_lon_range, element[1])))

                # Generate Output
                # Obtain an instance of the DATAOUTPUT class
                self.data_output = output.DATAOUTPUT(self.data_source)
                self.logger.info("Processing Output in Parallel")
                self.logger.info("\x1b[47m \x1b[32mGenerating PARALLEL WORKER POOL consisting of {} WORKERS \x1b[0m \x1b[39m".format(mp.cpu_count()))
                worker_pool = mp.Pool(mp.cpu_count())
                worker_jobs = worker_pool.map_async(self.process_parallel_output, parallel_var_range)
                worker_pool.close()
                while True:
                    if not worker_jobs.ready():
                        self.logger.info("Output Generator - Parallel Jobs left: {}".format(worker_jobs._number_left))
                        worker_jobs.wait(5)
                    else:
                        break

            except KeyboardInterrupt:
                #print("The ClimateBeast parallel processing has been interrupted. Need to drink some volcanic lava to help with stress." + "\n\n")
                worker_pool.terminate()
                worker_pool.close()
                raise Exception('BestiaPopParallelProcessInterrupted')

    def process_parallel_met(self, parallel_var_single_value):
        """Process records using multiple cores

        Args:
            year (int): the year to extract information for. This function gets called iteratively by a multiprocessing Pool created by process_parallel_records.

        Returns:
            pandas.core.frame.DataFrame: the slice dataframe
        """

        try:
            if self.input_path is None:
                if self.data_source == "silo":
                    # Initialize BestiaPop required class instances
                    silo = silo_connector.SILOClimateDataConnector(
                        climate_variables=self.climate_variables,
                        data_source=self.data_source,
                        input_path=self.input_path
                    )

                    if self.parallel_var == "lat":
                        final_df_latlon_tuple_list = silo.generate_climate_dataframe_from_silo_cloud_api(
                            year_range=self.year_range,
                            climate_variables=self.climate_variables, 
                            lat_range=[parallel_var_single_value],
                            lon_range=self.lon_range,
                            input_dir=self.input_path
                        )

                    elif self.parallel_var == "lon":
                        final_df_latlon_tuple_list = silo.generate_climate_dataframe_from_silo_cloud_api(
                            year_range=self.year_range,
                            climate_variables=self.climate_variables, 
                            lat_range=self.lat_range,
                            lon_range=[parallel_var_single_value],
                            input_dir=self.input_path
                        )

                elif self.data_source == "nasapower":
                    # Initialize BestiaPop required class instances
                    nasapower = nasapower_connector.NASAPowerClimateDataConnector(
                        climate_variables=self.climate_variables,
                        data_source=self.data_source,
                        input_path=self.input_path
                    )

                    if self.parallel_var == "lat":
                        final_df_latlon_tuple_list = nasapower.generate_climate_dataframe_from_nasapower_cloud_api(
                            year_range=self.year_range,
                            climate_variables=self.climate_variables, 
                            lat_range=[parallel_var_single_value],
                            lon_range=self.lon_range,
                            input_dir=self.input_path
                        )

                    elif self.parallel_var == "lon":
                        final_df_latlon_tuple_list = nasapower.generate_climate_dataframe_from_nasapower_cloud_api(
                            year_range=self.year_range,
                            climate_variables=self.climate_variables, 
                            lat_range=self.lat_range,
                            lon_range=[parallel_var_single_value],
                            input_dir=self.input_path
                        )

            else:
                final_df_latlon_tuple_list = self.generate_climate_dataframe_from_disk(
                    year_range=[year],
                    climate_variables=self.climate_variables, 
                    lat_range=self.lat_range,
                    lon_range=self.lon_range,
                    input_dir=self.input_path
                )

        except KeyboardInterrupt:
            print("\n" + "\x1b[47m \x1b[32mYou scared away the PopBeast. Parallel processing interrupted\x1b[0m \x1b[39m" + "\n\n")
            self.multiproc_event.set()

        return final_df_latlon_tuple_list

    def process_parallel_output(self, parallel_var_single_value):
        """Generate output files using multiple cores

        Args:
            lat (numpy.ndarray): A numpy array with all the desired latitudes whose data needs to be extracted and converted to an output format. This function is called by process_parallel_records.
        """

        try:
            if self.parallel_var == "lat":
                self.data_output.generate_output(
                    final_daily_df=self.total_parallel_climate_df,
                    lat_range=[parallel_var_single_value],
                    lon_range=self.final_parallel_lon_range,
                    outputdir=self.outputdir,
                    output_type=self.output_type
                )

            elif self.parallel_var == "lon":
                self.data_output.generate_output(
                    final_daily_df=self.total_parallel_climate_df,
                    lat_range=self.final_parallel_lon_range,
                    lon_range=[parallel_var_single_value],
                    outputdir=self.outputdir,
                    output_type=self.output_type
                )
    
        except KeyboardInterrupt:
            print("\x1b[47m \x1b[32mYou scared away the PopBeast. Parallel processing interrupted\x1b[0m \x1b[39m" + "\n")
            self.multiproc_event.set()

    def process_records(self, action):
        """Processing records for non-parallel computing

        Args:
            action (str): the type of action to be performed as per `bestiapop -a` parameter
        """

        # Let's check what's inside the "action" variable and invoke the corresponding function
        if action == "download-nc4-file":
            self.logger.info('Action {} invoked'.format(action))

            # Creating instances of required BestiaPop classes
            beastutils = bestiapop_utils.MyUtilityBeast(input_path=self.input_path)

            if self.data_source == "silo":
                for year in self.year_range:
                    for variable in self.climate_variables:
                        self.logger.info('Downloading SILO NetCDF4 file for year {}'.format(year))
                        beastutils.download_nc4_file_from_cloud(year, variable, self.outputdir)

            if self.data_source == "nasapower":
                for year in self.year_range:
                    for variable in self.climate_variables:
                        self.logger.info('Downloading NASAPOWER NetCDF4 file not implemented yet')
                        #self.logger.info('Downloading NASAPOWER NetCDF4 file for year {}'.format(year))
                        #self.download_nc4_file_from_cloud(year, variable, self.outputdir)

        elif action == "convert-nc4":
            if self.output_type == "met":
                self.logger.info('Action {} not implemented yet'.format(action))
            if self.output_type == "wht":
                self.logger.info('Action {} not implemented yet'.format(action))
            if self.output_type == "csv":
                self.logger.info('Action {} not implemented yet'.format(action))
            if self.output_type == "json":
                self.logger.info('Action {} not implemented yet'.format(action))

        elif action == "generate-climate-file":      
            self.logger.info('Extracting data and converting to {} format'.format(self.output_type))

            # 1. Let's invoke generate_climate_dataframe with the appropriate options
            if self.input_path is None:
                if self.data_source == "silo":
                    # Initialize BestiaPop required class instances
                    silo = silo_connector.SILOClimateDataConnector(
                        climate_variables=self.climate_variables,
                        data_source=self.data_source,
                        input_path=self.input_path
                    )

                    final_df_latlon_tuple_list = silo.generate_climate_dataframe_from_silo_cloud_api(
                        year_range=self.year_range,
                        climate_variables=self.climate_variables, 
                        lat_range=self.lat_range,
                        lon_range=self.lon_range,
                        input_dir=self.input_path
                    )

                elif self.data_source == "nasapower":
                    # Initialize BestiaPop required class instances
                    nasapower = nasapower_connector.NASAPowerClimateDataConnector(
                        climate_variables=self.climate_variables,
                        data_source=self.data_source,
                        input_path=self.input_path,
                    )

                    final_df_latlon_tuple_list = nasapower.generate_climate_dataframe_from_nasapower_cloud_api(
                        year_range=self.year_range,
                        climate_variables=self.climate_variables, 
                        lat_range=self.lat_range,
                        lon_range=self.lon_range,
                        input_dir=self.input_path
                    )
            else:
                final_df_latlon_tuple_list = self.generate_climate_dataframe_from_disk(
                    year_range=self.year_range,
                    climate_variables=self.climate_variables, 
                    lat_range=self.lat_range,
                    lon_range=self.lon_range,
                    input_dir=self.input_path
                )


            # 2. Generate Output
            # Obtain an instance of the DATAOUTPUT class
            self.data_output = output.DATAOUTPUT(self.data_source)
            self.total_climate_met_df = final_df_latlon_tuple_list[0]
            self.final_lon_range = final_df_latlon_tuple_list[1]
            self.data_output.generate_output(
                final_daily_df=self.total_climate_met_df,
                lat_range=self.lat_range,
                lon_range=self.final_lon_range,
                outputdir=self.outputdir,
                output_type=self.output_type
            )

    def generate_climate_dataframe_from_disk(self, year_range, climate_variables, lat_range, lon_range, input_dir):
        """This function generates a dataframe containing (a) climate values (b) for every variable requested (c) for every day of the year (d) for every year passed in as argument. The values will be sourced from Disk.
        Args:
            year_range (numpy.ndarray): a numpy array with all the years for which we are seeking data.
            climate_variables (str): the climate variable short name as per SILO or NASAPOWER nomenclature. For SILO check https://www.longpaddock.qld.gov.au/silo/about/climate-variables/. For NASAPOWER check: XXXXX.
            lat_range (numpy.ndarray): a numpy array of latitude values to extract data from
            lon_range (numpy.ndarray): a numpy array of longitude values to extract data from
            input_dir (str): when selecting the option to generate Climate Data Files from local directories, this parameter must be specified, otherwise data will be fetched directly from the cloud either via an available API or S3 bucket.
        Returns:
            tuple: a tuple consisting of (a) the final dataframe containing values for all years, latitudes and longitudes for a particular climate variable, (b) the curated list of longitude ranges (which excludes all those lon values where there were no actual data points). The tuple is ordered as follows: (final_dataframe, final_lon_range)
        """

        # We will iterate through each "latitude" value and, 
        # within this loop, we will iterate through all the different 
        # "longitude" values for a given year. Results for each year
        # are collected inside the "met_df" with "met_df.append"
        # At the end, it will output a file with all the contents if
        # "output_to_file=True" (by default it is "True")

        self.logger.debug('Generating DataFrames')

        # empty df to append all the met_df to
        total_climate_df = pd.DataFrame()

        # create an empty list to keep track of lon coordinates
        # where there are no values
        empty_lon_coordinates = []

        # Initialize BestiaPop required class instances
        silo = silo_connector.SILOClimateDataConnector(data_source=self.data_source, input_path=self.input_path, climate_variables=climate_variables)
        nasapower = nasapower_connector.NASAPowerClimateDataConnector(data_source=self.data_source, input_path=self.input_path, climate_variables=climate_variables)
        beastutils = bestiapop_utils.MyUtilityBeast(input_path=self.input_path)

        # Loading and/or Downloading the files
        for year in tqdm(year_range, ascii=True, desc="Year"):
            self.logger.debug('Processing data for year {}'.format(year))

            for climate_variable in tqdm(climate_variables, ascii=True, desc="Climate Variable"):
                self.logger.debug('Processing data for climate variable {}'.format(climate_variable))

                # Opening the target CDF database
                # We need to check:
                # (1) should we fetch the data directly from the cloud via an API or S3 bucket
                # (2) if files should be fetched locally, whether the user passed a directory with multiple files or just a single file to process.

                # if an input directory was provided
                if self.input_path is not None:

                    if input_dir.is_dir() == True:
                        sourcefile = str(year) + "." + climate_variable + ".nc"
                        sourcepath = input_dir/sourcefile
                    elif input_dir.is_file() == True:
                        sourcepath = input_dir

                    if sourcepath.exists() == False:
                        self.logger.error('Could not find file {}. Please make sure you have downloaded the required netCDF4 files in the format "year.variable.nc" to the input directory. Skipping...'.format(sourcepath))
                        continue
                    
                    data = beastutils.load_cdf_file(sourcepath, climate_variable)

                # Now iterating over lat and lon combinations
                # Each year-lat-lon matrix generates a different file

                for lat in tqdm(lat_range, ascii=True, desc="Latitude"):

                    for lon in lon_range:

                        # Skipping any longitude points that have already been proven to not contain any data
                        # This adds a slight performance improvement too
                        if lon in empty_lon_coordinates:
                            continue

                        self.logger.debug('Processing Variable {} - Lat {} - Lon {} for Year {}'.format(climate_variable, lat, lon, year))

                        # here we are checking whether the get_values_from_cdf function
                        # returns with a ValueError (meaning there were no values for
                        # that particular lat & long combination). If it does return
                        # with an error, we skip this loop and don't produce any output files
                    
                        try:
                            # Local file, read from input directory
                            if self.data_source == "silo":
                                var_year_lat_lon_df = silo.get_yearly_data(lat, lon, data['value_array'], year, climate_variable)
                            elif self.data_source == "nasapower":
                                var_year_lat_lon_df = nasapower.get_yearly_data(lat, lon, data['value_array'], year, climate_variable)

                        except ValueError:
                            self.logger.warning("This longitude value will be skipped for the rest of the climate variables and years")
                            self.logger.warning("Deleting lon {} in array position {}".format(lon, np.where(lon_range == lon)[0][0]))
                            # Append empty lon value to list
                            empty_lon_coordinates.append(lon)
                            continue
                        
                        # delete the var_year_lat_lon_df back to zero.
                        total_climate_df = total_climate_df.append(var_year_lat_lon_df)
                        del var_year_lat_lon_df

                # We reached the end of the year loop
                # we need must close the open handle to the s3fs file to free up resources
                if self.input_path is None:
                    try:
                        self.remote_file_obj.close()
                        self.logger.debug("Closed handle to cloud s3fs file {}".format(self.silo_file))
                    except AttributeError:
                        self.logger.debug("Closing handle to remote s3fs file not required. Using an API endpoint instead of a cloud NetCDF4 file")

        # Remove any empty lon values from longitude array so as to avoid empty MET generation
        empty_lon_array = np.array(empty_lon_coordinates)
        final_lon_range = np.setdiff1d(lon_range, empty_lon_array)

        # Return results
        return (total_climate_df, final_lon_range)

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
  
  # Grab an instance of the CLIMATEBEAST class
  myclimatebeast = CLIMATEBEAST(logger, pargs.action, pargs.data_source, pargs.output_directory, pargs.output_type, pargs.input_directory, pargs.climate_variable, pargs.year_range, pargs.latitude_range, pargs.longitude_range, multiprocessing=pargs.multiprocessing)
  # Start to process the records
  if pargs.multiprocessing == True:
    logger.info("\x1b[47m \x1b[32mMultiProcessing selected \x1b[0m \x1b[39m")
    myclimatebeast.process_parallel_records(pargs.action)
  else:
    myclimatebeast.process_records(pargs.action)
    
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
        print("\n" + "BestiaPop amazing work has been interrupted by a mortal. Returning to the depths of the earth." + "\n\n")
        sys.exit()