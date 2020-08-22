
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

class NASAPowerClimateDataConnector():
    """This class will provide methods that query and parse data from NASA POWER climate database

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
            logger = logging.getLogger('POPBEAST.NASAPOWER_CONNECTOR')
            coloredlogs.install(fmt='%(asctime)s - %(name)s - %(message)s', level="DEBUG", logger=logger)

        except ModuleNotFoundError:
            logger = logging.getLogger('POPBEAST.NASAPOWER_CONNECTOR')
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
        self.climate_data = {}
        self.climate_variables = climate_variables

        # Variable names in NASAPOWER DB
        # nasapower_variables = ["ALLSKY_TOA_SW_DWN", "ALLSKY_SFC_SW_DWN", "T2M", "T2M_MIN", "T2M_MAX", "T2MDEW", "WS2M", "PRECTOT"]

        # Setup Climate Variable Code Translations
        # NASAPOWER Climate variable dict
        self.nasapower_climate_variable_code = {
            "daily_rain":           "PRECTOT", 
            "max_temp":             "T2M_MAX",
            "min_temp":             "T2M_MIN",
            "radiation":            "ALLSKY_SFC_SW_DWN"
        }

        # Generate list with all variables passed as part of the user's request
        # We can then pass this to the API request
        nasapower_climate_variables_list = [self.nasapower_climate_variable_code[x] for x in self.climate_variables]
        self.nasapower_climate_variables_string = ",".join(nasapower_climate_variables_list)

        # Define a lambda for quick translations
        self._Translate_Climate_Var = lambda x: self.nasapower_climate_variable_code[x]

    def get_yearly_data(self, lat, lon, value_array, year, year_range, climate_variable):
        """Extract values from an API endpoint in the cloud or a xarray.Dataset object

        Args:
            lat (float): the latitude that values should be returned for
            lon (float): the longitude that values should be returned for
            value_array (xarray.Dataset): the xarray Dataset object to extract values from
            year (string): the year of the file
            variable_short_name (string): the climate variable name

        Raises:
            ValueError: if there was "NO" data available for all days under a particular combination of lat & lon, then the total values collected should equal "0" (meaning, there was no data for that point in the grid). If this is the case, then the function will simply return with a "no_values" message and signal the calling function that it should ignore this particular year-lat-lon combination.

        Returns:
            pandas.core.frame.DataFrame: a dataframe containing 5 columns: the Julian day, the grid data value for that day, the year, the latitude, the longitude.

        The NASA POWER database is a global database of daily weather data
        specifically designed for agrometeorological applications. The spatial
        resolution of the database is 0.5x0.5 degrees (as of 2018).
        For more information on the NASA POWER database see the documentation
        at: http://power.larc.nasa.gov/common/AgroclimatologyMethodology/Agro_Methodology_Content.html
        The `NASAPowerClimateDataConnector` is used by BestiaPop to retrieve data
        from NASA POWER database and provides functions to parse and extract relevant
        information from it.
        Important NOTE: as per https://power.larc.nasa.gov/docs/services/api/v1/temporal/daily/,
        any latitude-longitude combinations within a 0.5x0.5 degrees grid box
        will yield the same weather data. Thus, there is no difference for data returned between
        lat/lon -41.5/145.3 and lat/lon -41.8/145.7. When BestiaPop requests data from 
        NASA Power, it will automatically create coordinate series wiht 1 degree jumps. So if you
        pass in `-lat "-41.15 -55.05"` the resulting series will be: [-55.05, -54.05, -53.05, -52.05, -51.05,
        -50.05, -49.05, -48.05, -47.05, -46.05, -45.05, -44.05, -43.05, -42.05, -41.05]. Please bear in mind
        that there is no difference between -41.15 and -41.05.
        """

        # Checking if this is a leap-year  
        if (( year%400 == 0) or (( year%4 == 0 ) and ( year%100 != 0))):
            days = np.arange(0,366,1)
        else: 
            days = np.arange(0,365,1)

        # If we are attempting to read from NasaPower, use it's API instead of Xarray
        if self.data_source == "nasapower" and self.input_path is None:
            
            self.logger.info("Extracting data from NASA POWER Climate DataBase")

            try:
                # Attempt to fetch the information from currently available data from a previous API call
                # Check if the coordinates in the available data are different than those being requested
                current_lon, current_lat, current_elev = self.climate_metadata_coordinates
                current_lat = np.round(current_lat, decimals=2)
                current_lon = np.round(current_lon, decimals=2)
                current_elev = np.round(current_elev, decimals=2)

                if (current_lat != lat) or (current_lon != lon):
                    raise ValueError("InvalidCoordinatesInData")

            # If no current_data available, then proceed to call NasaPower API
            except:
                self.logger.debug("Need to get data from the NASA Power Cloud")

                # Obtaining start and end years for API call
                year_start = year_range[0]
                year_end = year_range[len(year_range)-1]

                nasapower_api_url = "https://power.larc.nasa.gov/cgi-bin/v1/DataAccess.py"

                payload = {
                    "request": "execute",
                    "tempAverage": "DAILY",
                    "identifier": "SinglePoint",
                    "parameters": self.nasapower_climate_variables_string,
                    "lat": lat,
                    "lon": lon,
                    "startDate": "{}0101".format(year_start),
                    "endDate": "{}1231".format(year_end),
                    "userCommunity": "AG",
                    "outputList": "JSON",
                    "user": "anonymous"
                }

                r = requests.get(nasapower_api_url, params=payload)
                json_data = r.json()

                # Shape of data returned by NasaPower
                '''
                    {'features': [
                        {'geometry': {'coordinates': [145.50001, -41.14999, 325.05],
                        'type': 'Point'},
                        'properties': {
                            'parameter': {
                                'ALLSKY_SFC_SW_DWN': {
                                    '20100101': 29.31,
                                    '20100102': 23.84,
                                    '20100103': 18.91,
                                    '20100104': 20.08
                                ...
                                'PRECTOT': {
                                    '20100101': 0.19,
                                    '20100102': 1.75,
                                    '20100103': 1.08,
                                ...
                            }
                        },
                        'type': 'Feature'}],
                        'header': {'api_version': '1.1.0',
                        'endDate': '20101231',
                        'fillValue': '-99',
                        'startDate': '20100101',
                        'title': 'NASA/POWER SRB/FLASHFlux/MERRA2/GEOS 5.12.4 (FP-IT) 0.5 x 0.5 Degree Daily Averaged Data'},
                        'messages': [],
                        'outputs': {'json': 'https://power.larc.nasa.gov/downloads/POWER_SinglePoint_Daily_20100101_20101231_41d15S_145d50E_74ee60c3.json'},
                        'parameterInformation': {
                        'ALLSKY_SFC_SW_DWN': {'longname': 'All Sky Insolation Incident on a Horizontal Surface',
                        'units': 'MJ/m^2/day'},
                        'PRECTOT': {'longname': 'Precipitation', 'units': 'mm day-1'},
                        'T2M_MAX': {'longname': 'Maximum Temperature at 2 Meters', 'units': 'C'},
                        'T2M_MIN': {'longname': 'Minimum Temperature at 2 Meters', 'units': 'C'}},
                        'time': [['Main OPeNDAP Requests:', 0.46], ['Total Script:', 1.91]],
                        'type': 'FeatureCollection'}
                '''

                # Capture all the climate variables inside this class object to not have to repeat calls to the cloud API
                self.climate_metadata_coordinates = json_data['features'][0]['geometry']['coordinates']
                self.climate_data = json_data['features'][0]['properties']['parameter']

            # Proceed to extract the values into a list for each day in the year
            translated_climate_variable = self._Translate_Climate_Var(climate_variable)
            data_values = [self.climate_data[translated_climate_variable][x] for x in self.climate_data[translated_climate_variable] if int(x[:4:]) == year]

            #data_values = [np.round(current_data[x], decimals=1) for x in current_data if x[:4:] == year]

        # If we are not extracting data directly from the cloud, then proceed to extract locally from NetCDF4 files
        elif self.input_path is not None:
            # Using a list comprehension to capture all daily values for the given year and lat/lon combinations
            # We round values to a single decimal
            self.logger.debug("Reading array data from NetCDF with xarray")

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

        # We need to get the total amount of values collected
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