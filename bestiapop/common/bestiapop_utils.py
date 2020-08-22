
import logging
import numpy as np
import os
import requests
import s3fs
import xarray as xr
from pathlib import Path
from tqdm import tqdm

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
            float_step = 1  
        
        if coordinate_type == "latitude":
            if isinstance(coordinate_range, np.ndarray):
                # The user passed in a file with an array of latitudes
                # this file was processed during the argument parsing phase
                # and a numpy.ndarray was returned. Nothing else to do.
                return coordinate_range
            else:
                if len(coordinate_range) > 1:
                    if coordinate_range[0] < 0 and coordinate_range[1] < 0:
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
                        if int(lat_value_count+1) != len(lat_range):
                            # Must get rid of last float
                            lon_range = np.delete(lon_range,(len(lon_range)-1),0)

                return lon_range