
import logging
import numpy as np
import os
import requests
import pandas as pd
import s3fs
import sys
import xarray as xr

from pathlib import Path
from tqdm import tqdm

# Ugly but workable importing solution so that the package can be both 
# imported as a package, run from commandline with `python -m bestiapop`
# or from the source directory as `python bestiapop.py`
if "bestiapop" in sys.modules:
    from bestiapop.connectors import (silo_connector, nasapower_connector)
    from bestiapop.producers import output
else:
    from connectors import (silo_connector, nasapower_connector)
    from producers import output

class MyUtilityBeast():
    """This class will provide methods to perform generic or shared operations on data

        Args:
            logger (str): A pointer to an initialized Argparse logger

    """

    def __init__(self, input_path=None):

        # Setup logging
        # We need to pass the "logger" to any Classes or Modules that may use it 
        # in our script
        try:
            import coloredlogs
            logger = logging.getLogger('POPBEAST.BESTIAPOP_UTILS')
            coloredlogs.install(fmt='%(asctime)s - %(name)s - %(message)s', level="DEBUG", logger=logger)

        except ModuleNotFoundError:
            logger = logging.getLogger('POPBEAST.BESTIAPOP_UTILS')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)

        # Setting up class variables
        self.logger = logger
        self.input_path = input_path

    def download_nc4_file_from_cloud(self, year, climate_variable, output_path = Path().cwd(), data_source="silo", skip_certificate_checks=False):
        """Downloads a file from AWS S3 bucket or other cloud API

        Args:
            year (int): the year we require data for. SILO stores climate data as separate years like so: daily_rain.2018.nc
            climate_variable (str): the climate variable short name as per SILO nomenclature, see https://www.longpaddock.qld.gov.au/silo/about/climate-variables/
            output_path (str, optional): The target folder where files should be downloaded. Defaults to Path().cwd().
            skip_certificate_checks (bool, optional): ask the requests library to skip certificate checks, useful when attempting to download files behind a proxy. Defaults to False.

        """

        # This function connects to the public S3 site for SILO and downloads the specified file
        # For a list of variables to use in "climate_variable" see
        # https://www.longpaddock.qld.gov.au/silo/about/climate-variables/
        # Most common are: daily_rain, max_temp, min_temp
        # Example, call the function like: download_nc4_file_from_cloud(2011, "daily_rain")
        # The above will save to the current directory, however, you can also pass
        # your own like: download_nc4_file_from_cloud(2011,'daily_rain','C:\\Downloads\\SILO\2011')

        # We use TQDM to show a progress bar of the download status

        if data_source == "silo":
            filename = str(year) + "." + climate_variable + ".nc"
            url = 'https://s3-ap-southeast-2.amazonaws.com/silo-open-data/annual/{}/{}'.format(climate_variable, filename)

            # Get pointer to URL
            try:
                req = requests.get(url, stream=True)
            except requests.exceptions.SSLError:
                self.logger.warning("Could not download file due to Certificate issues, potentially caused by your proxy. Relaxing Certificate Checking and attempting again...")
                self.logger.warning('Skipping SSL certificate checks for {}/{}'.format(climate_variable, filename))
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

        elif data_source == "nasapower":
            None

    def load_cdf_file(self, sourcepath, data_category, year=None):
        """This function loads a NetCDF4 file either from the cloud or locally

        Args:
            sourcepath (str): when loading a NetCDF4 file locally, this specifies the source folder. Only the "folder" must be specified, the actual file name will be further qualified by BestiaPop grabbing data from the year and climate variable paramaters passed to the SILO class.
            data_category (str): the short name variable, examples: daily_rain, max_temp, etc.
            year (int, optional): the year we want to extract data from, it is used to compose the final AWS S3 URL or to qualify the full path to the local NetCDF4 file we would like to load. Defaults to None.

        Returns:
            dict: a dictionary containing two items, "value_array" which is a xarray DataSet object and "data_year" which is the year that the NetCDF4 file contains data for, extracted by looking at the contents of the NetCDF4 file itself.
        """

        # This function loads the ".nc" file using the xarray library and
        # stores a pointer to it in "data_dict"

        # Let's first check whether a source directory was passed in, otherwise
        # assume we need to fetch from the cloud
        if self.input_path is None:
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

    def get_years_list(self, year_range):

        # Check whether a year range with "-" was provided for the year.
        # If this is the case, generate a list out of it

        # TODO: handle lists of discontinuous year ranges like [1999-2001,2005-2019]
        if "-" in year_range:
            first_year = int(year_range.split("-")[0])
            last_year = int(year_range.split("-")[1]) + 1
            year_range = np.arange(first_year,last_year,1)
        else:
            year_range = [int(year_range)]

        return year_range

    def get_coordinate_numpy_list(self, coordinate_range, coordinate_type, climate_data_source):

        # Check whether a lat and lon range separated by a space was provided.
        # If this is the case, generate a list out of it
        # NOTE: for some reason I get a list within a list from the argparse...

        # Let's define whether the float range will be defined on steps of 
        # 0.05 (SILO) or 0.5 (NASAPOWER)
        if climate_data_source == "silo":
            float_step = 0.05
        elif climate_data_source == "nasapower":
            float_step = 0.5
        
        if coordinate_type == "latitude":
            if isinstance(coordinate_range, np.ndarray):
                # The user passed in a file with an array of latitudes
                # this file was processed during the argument parsing phase
                # and a numpy.ndarray was returned. Nothing else to do.
                return coordinate_range
            else:
                if len(coordinate_range) > 1:
                    if coordinate_range[0] > coordinate_range[1]:
                        # We are clearly dealing with negative numbers
                        # User has mistakenly swapped the order of numbers
                        # we need to silently swap them back
                        first_lat = coordinate_range[1]
                        last_lat = coordinate_range[0]
                    else:
                        first_lat = coordinate_range[0]
                        last_lat = coordinate_range[1]

                    # Find absolute distance to account for missing values
                    # numpy.arange erratic behaviour with floats: https://numpy.org/doc/stable/reference/generated/numpy.arange.html
                    lat_value_count = np.round((abs(first_lat-last_lat) / float_step), decimals=0)
                    lat_range = np.arange(first_lat,last_lat,float_step).round(decimals=2)
                    
                    # Check the number spread
                    if int(lat_value_count+1) != len(lat_range):
                        lat_range = np.arange(first_lat,np.round((last_lat+float_step), decimals=2),float_step).round(decimals=2).tolist()
                        if int(lat_value_count+1) != len(lat_range):
                            # Must get rid of last float
                            lat_range = np.delete(lat_range,(len(lat_range)-1),0)
                else:
                    # when only a single lat is passed in
                    lat_range = coordinate_range

                return lat_range

        elif coordinate_type == "longitude":
            if coordinate_range:
                if len(coordinate_range) > 1:
                    if coordinate_range[0] > coordinate_range[1]:
                        # User has mistakenly swapped the order of numbers
                        # we need to silently swap them back
                        first_lon = coordinate_range[1]
                        last_lon = coordinate_range[0]
                    else:
                        first_lon = coordinate_range[0]
                        last_lon = coordinate_range[1]

                    # Find absolute distance to account for missing values
                    # numpy.arange erratic behaviour with floats: https://numpy.org/doc/stable/reference/generated/numpy.arange.html
                    lon_value_count = np.round((abs(first_lon-last_lon) / float_step), decimals=0)
                    lon_range = np.arange(first_lon,last_lon,float_step).round(decimals=2)

                    # Check the number spread
                    if int(lon_value_count+1) != len(lon_range):
                        lon_range = np.arange(first_lon,np.round((last_lon+float_step), decimals=2),float_step).round(decimals=2).tolist()
                        if int(lon_value_count+1) != len(lon_range):
                            # Must get rid of last float
                            lon_range = np.delete(lon_range,(len(lon_range)-1),0)

                else:
                    # when only a single lon is passed in
                    lon_range = coordinate_range

                return lon_range

    def generate_climate_dataframe_from_disk(self, year_range, climate_variables, lat_range, lon_range, input_dir, data_source="silo"):
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
        silo = silo_connector.SILOClimateDataConnector(data_source=data_source, input_path=self.input_path, climate_variables=climate_variables)
        nasapower = nasapower_connector.NASAPowerClimateDataConnector(data_source=data_source, input_path=self.input_path, climate_variables=climate_variables)

        # Loading and/or Downloading the files
        for year in tqdm(year_range, file=sys.stdout, ascii=True, desc="Total Progress"):
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
                    
                    data = self.load_cdf_file(sourcepath, climate_variable)

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
                            if data_source == "silo":
                                var_year_lat_lon_df = silo.get_yearly_data(
                                                                            lat=lat, 
                                                                            lon=lon, 
                                                                            value_array=data['value_array'], 
                                                                            year=year,
                                                                            year_range=year_range,
                                                                            climate_variable=climate_variable
                                                                        )
                            elif data_source == "nasapower":
                                var_year_lat_lon_df = nasapower.get_yearly_data(
                                                                            lat=lat, 
                                                                            lon=lon, 
                                                                            value_array=data['value_array'], 
                                                                            year=year,
                                                                            year_range=year_range,
                                                                            climate_variable=climate_variable
                                                                        )

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