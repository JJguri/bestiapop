

import h5netcdf
import io
import logging
import numpy as np
import multiprocessing as mp
import os
import pandas as pd
import re
import requests
import s3fs
import sys
import xarray as xr

class SILOClimateDataConnector():
    """This class will provide methods that query and parse data from SILO climate database

        Args:
            logger (str): A pointer to an initialized Argparse logger
            data_source (str): The climate database where the values are being extracted from: SILO or NASAPOWER

    """


    def __init__(self, data_source, input_path, climate_variables):

        # Setup logging
        # We need to pass the "logger" to any Classes or Modules that may use it 
        # in our script
        try:
            import coloredlogs
            logger = logging.getLogger('POPBEAST.SILO_CONNECTOR')
            coloredlogs.install(fmt='%(asctime)s - %(name)s - %(message)s', level="DEBUG", logger=logger)

        except ModuleNotFoundError:
            logger = logging.getLogger('POPBEAST.SILO_CONNECTOR')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)

        # Setting up class variables
        self.logger = logger
        self.data_source = data_source
        self.input_path = input_path
        self.climate_variables = climate_variables

        # Setup Climate Variable Code Translations
        # SILO Climate variable dict
        self.silo_climate_variable_code = {
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

        # Generate list with all variables passed as part of the user's request
        # We can then pass this to the API request
        silo_climate_variables_list = [self.silo_climate_variable_code[x] for x in self.climate_variables]
        self.silo_climate_variables_string = "".join(silo_climate_variables_list)

        # Define a lambda for quick identification of the right index for a particular dict in a list
        self._Obtain_Index_Of_Dict_In_List = lambda dict_list, climate_var: [i for i, dict_data in enumerate(dict_list) if dict_data['variable_code'] == climate_var][0]

    def get_yearly_data(self, lat, lon, value_array, year, climate_variable):
        """Extract values from an API endpoint in the cloud or a xarray.Dataset object

        Args:
            lat (float): the latitude that values should be returned for
            lon (float): the longitude that values should be returned for
            value_array (xarray.Dataset): the xarray Dataset object to extract values from
            year (string): the year of the file
            variable_short_name (string): the climate variable short name as per SILO nomenclature, see https://www.longpaddock.qld.gov.au/silo/about/climate-variables/

        Raises:
            ValueError: if there was "NO" data available for all days under a particular combination of lat & lon, then the total values collected should equal "0" (meaning, there was no data for that point in the grid). If this is the case, then the function will simply return with a "no_values" message and signal the calling function that it should ignore this particular year-lat-lon combination.

        Returns:
            pandas.core.frame.DataFrame: a dataframe containing 5 columns: the Julian day, the grid data value for that day, the year, the latitude, the longitude.
        """

        # This function will use xarray to extract a slice of time data for a combination of lat and lon values

        # Checking if this is a leap-year  
        if (( year%400 == 0) or (( year%4 == 0 ) and ( year%100 != 0))):
            days = np.arange(0,366,1)
        else: 
            days = np.arange(0,365,1)

        # If we are attempting to read from the cloud, use SILO's API instead of Xarray
        if self.data_source == "silo" and self.input_path is None:

            self.logger.debug("Extracting data from SILO API")

            try:
                # Attempt to fetch the information from currently available data from a previous API call
                current_data_year = self.climate_data[0].get('date', None)
                
                if current_data_year != None:

                    # Check if the year in available data is different than the year being requested
                    current_data_year = int(current_data_year.split('-')[0])
                    if current_data_year != year:
                        raise ValueError("InvalidYearInData")
                    
                    # Check if the coordinates in the available data are different than those being requested
                    current_lat = float(self.climate_metadata['latitude'])
                    current_lon = float(self.climate_metadata['longitude'])
                    if (current_lat != float(lat)) or (current_lon != float(lon)):
                        raise ValueError("InvalidCoordinatesInData")

            except:
                # If we get here, then either the self.climate_data variable does not exist
                # or the data stored in the object is not relevant for the year being queried right now. 
                # We need to fetch data from the cloud using SILO's API again.

                self.logger.debug("Need to get data from SILO Cloud")

                silo_api_url = "https://www.longpaddock.qld.gov.au/cgi-bin/silo/DataDrillDataset.php?lat={}&lon={}&format=json&start={}0101&finish={}1231&username=bestiapop@bestiapop.com&password=gui&comment={}".format(lat, lon, year, year, self.silo_climate_variables_string)
                r = requests.get(silo_api_url)
                json_data = r.json()

                # The shape of returned data from SILO is: 
                '''
                    {
                    'location': {
                        'latitude': -41.1,
                        'longitude': 145.1,
                        'elevation': 153.9,
                        'reference': 'XNR'
                    },
                    'extracted': 20200821,
                    'data': [
                        {   'date': '2011-01-01',
                            'variables': [
                                {'source': 25, 'value': 0.0, 'variable_code': 'daily_rain'},
                                {'source': 25, 'value': 19.7, 'variable_code': 'max_temp'},
                                {'source': 25, 'value': 11.0, 'variable_code': 'min_temp'}
                            ]
                        },
                        {   'date': '2011-01-02',
                            'variables': [
                                {'source': 25, 'value': 0.0, 'variable_code': 'daily_rain'},
                                {'source': 25, 'value': 17.8, 'variable_code': 'max_temp'},
                                {'source': 25, 'value': 8.8, 'variable_code': 'min_temp'}
                            ]
                        },
                        {   'date': '2011-01-03',
                            'variables': [
                                {'source': 25, 'value': 0.0, 'variable_code': 'daily_rain'},
                                {'source': 25, 'value': 19.8, 'variable_code': 'max_temp'},
                                {'source': 25, 'value': 5.7, 'variable_code': 'min_temp'}
                            ]
                        }...
                '''

                self.climate_metadata = json_data['location']
                self.climate_data = json_data['data']

            # The index of the variable data inside the 'variables' element of the returned json is always
            # the same for the same variable across all dates. Obtain once from first element and re-use.
            i = self._Obtain_Index_Of_Dict_In_List(self.climate_data[0]['variables'], climate_variable)
            data_values = [np.round(x['variables'][i]['value'], decimals=1) for x in self.climate_data]

        # If we are not extracting data directly from the cloud, then proceed to extract locally from NetCDF4 files
        elif self.input_path is not None:
            # Using a list comprehension to capture all daily values for the given year and lat/lon combinations
            # We round values to a single decimal
            self.logger.debug("Reading array data from NetCDF with xarray")

            # Alternatively: data_values = [np.round(x, decimals=1) for x in (value_array[variable_short_name].loc[dict(lat=lat, lon=lon)]).values]
            data_values = [np.round(x, decimals=1) for x in value_array[climate_variable].sel(lat=lat, lon=lon).values]

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
            self.logger.warning("THERE ARE NO VALUES FOR LAT {} LON {} VARIABLE {}".format(lat, lon, climate_variable))
            raise ValueError('no_data_for_lat_lon')

        # now we need to fill a PANDAS DataFrame with the lists we've been collecting
        pandas_dict_of_items = {'days': days,
                                climate_variable: data_values}

        df = pd.DataFrame.from_dict(pandas_dict_of_items)

        # making the julian day match the expected
        df['days'] += 1

        # adding a column with the "year" to the df
        # so as to prepare it for export to other formats (CSV, MET, etc.)
        df.insert(0, 'year', year)
        df.insert(0, 'lat', lat)
        df.insert(0, 'lon', lon)

        return df