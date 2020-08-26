

import io
import logging
import numpy as np
import os
import pandas as pd
import re

from datetime import datetime as datetime
from jinja2 import Template
from numpy import array
from pathlib import Path
from tabulate import tabulate
from tqdm import tqdm

class DATAOUTPUT():
    """This class will provide different methods for data output from climate dataframes

        Args:
            logger (str): A pointer to an initialized Argparse logger
            data_source (str): The climate database where the values are being extracted from: SILO or NASAPOWER

        Returns:
            DATAOUTPUT: A class object with access to DATAOUTPUT methods
    """

    def __init__(self, data_source):

        # Setup logging
        # We need to pass the "logger" to any Classes or Modules that may use it 
        # in our script
        try:
            import coloredlogs
            logger = logging.getLogger('POPBEAST.DATAOUTPUT')
            coloredlogs.install(fmt='%(asctime)s - %(name)s - %(message)s', level="DEBUG", logger=logger)

        except ModuleNotFoundError:
            logger = logging.getLogger('POPBEAST.DATAOUTPUT')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)
            logger.addHandler(console_handler)
            logger.setLevel(logging.INFO)

        # Setting up class variables
        self.logger = logger
        self.data_source = data_source
        
    def generate_output(self, final_daily_df, lat_range, lon_range, outputdir, output_type="met"):
        """Generate required Output based on Output Type selected

        Args:
            final_daily_df (pandas.core.frame.DataFrame): the pandas daframe containing all the values that are going to be parsed into a specific output
            lat_range (numpy.ndarray): an array of latitude values to select from the final_daily_df
            lon_range (numpy.ndarray): an array of longitude values to select from the final_daily_df
            outputdir (str): the folder that will be used to store the output files
            output_type (str, optional): the output type: csv (not implemented yet), json(not implemented yet), met. Defaults to "met".

        """

        # Determine the variable that has the highest range so we can 
        # benefit from parallel processing when active, based on the
        # variable that can be allocated the highest ammount of cores
        if len(lat_range) > len(lon_range):
            primary_var_desc = "lat"
            secondary_var_desc = "lon"
            primary_var = lat_range
            secondary_var = lon_range
        elif len(lat_range) < len(lon_range):
            primary_var_desc = "lon"
            secondary_var_desc = "lat"
            primary_var = lon_range
            secondary_var = lat_range
        else:
            # by default, let's leave "lat" as the primary var
            primary_var_desc = "lat"
            secondary_var_desc = "lon"
            primary_var = lat_range
            secondary_var = lon_range

        if output_type == "stdout":

            # Rename df columns and sort them
            final_daily_df = final_daily_df.rename(columns={"days": "day","daily_rain": "rain",'min_temp':'mint','max_temp':'maxt','radiation':'radn'})

            final_daily_df = final_daily_df.groupby(['lon', 'lat', 'year', 'day'])[['radn', 'maxt', 'mint', 'rain']].sum().reset_index()

            for primary_data_point in tqdm(primary_var, ascii=True, desc=primary_var_desc):
                
                for secondary_data_point in tqdm(secondary_var, ascii=True, desc=secondary_var_desc):

                    if primary_var_desc == "lat":
                        lat = primary_data_point
                        lon = secondary_data_point
                    elif primary_var_desc == "lon":
                        lon = primary_data_point
                        lat = secondary_data_point

                    coordinate_slice_df = final_daily_df[(final_daily_df.lon == lon) & (final_daily_df.lat == lat)]

                    # We shall output the plain final DataFrame to stdout using tabulate
                    print("\n")
                    print(tabulate(coordinate_slice_df, headers=coordinate_slice_df.keys(), tablefmt='psql', showindex=False))
                    print("\n")

        if output_type == "met":
            # Rename variables
            # Check if final df is empty, if so, then return and do not proceed with the rest of the file
            if final_daily_df.empty == True:
                self.logger.error("No data in final dataframe. No file can be generated. Exiting...")
                return

            try:
                # Rename df columns and sort them to match order expected by MET
                final_daily_df = final_daily_df.rename(columns={"days": "day","daily_rain": "rain",'min_temp':'mint','max_temp':'maxt','radiation':'radn'})
                final_daily_df = final_daily_df.groupby(['lon', 'lat', 'year', 'day'])[['radn', 'maxt', 'mint', 'rain']].sum().reset_index()

                self.logger.info("Proceeding to the generation of MET files")

                for primary_data_point in tqdm(primary_var, ascii=True, desc=primary_var_desc):
                    
                    for secondary_data_point in tqdm(secondary_var, ascii=True, desc=secondary_var_desc):

                        if primary_var_desc == "lat":
                            lat = primary_data_point
                            lon = secondary_data_point
                        elif primary_var_desc == "lon":
                            lon = primary_data_point
                            lat = secondary_data_point

                        coordinate_slice_df = final_daily_df[(final_daily_df.lon == lon) & (final_daily_df.lat == lat)]
                        del coordinate_slice_df['lat']
                        del coordinate_slice_df['lon']

                        self.generate_met(outputdir, coordinate_slice_df, lat, lon)

                        # Delete unused df
                        del coordinate_slice_df

            except KeyError as e:
                self.logger.error("Could not find all required climate variables to generate MET: {}".format(str(e)))

        if output_type == "wht":
            # Rename variables
            # Check if final df is empty, if so, then return and do not proceed with the rest of the file
            if final_daily_df.empty == True:
                self.logger.error("No data in final dataframe. No file can be generated. Exiting...")
                return

            try:
                # Rename df columns and sort them to match order expected by DSSAT
                final_daily_df = final_daily_df.rename(columns={"days": "day","daily_rain": "rain",'min_temp':'mint','max_temp':'maxt','radiation':'radn'})
                final_daily_df = final_daily_df.groupby(['lon', 'lat', 'year', 'day'])[['radn', 'maxt', 'mint', 'rain']].sum().reset_index()

                # Let's generate DSSAT Year+JulianDay time format
                # Creating pandas series with last two digits of the year
                dssat_year_series = final_daily_df.year.apply(lambda x: str(x)[2:])
                # Creating pandas series with julian days with leading zeroes up to two spaces
                dssat_julian_day_series = np.char.zfill(final_daily_df.day.apply(str).to_list(), 3)
                # Add DSSAT julian day values as first column
                final_daily_df.insert(0, 'dssatday', dssat_year_series + dssat_julian_day_series)
                
                self.logger.info("Proceeding to the generation of WHT files")

                for primary_data_point in tqdm(primary_var, ascii=True, desc=primary_var_desc):
                    
                    for secondary_data_point in tqdm(secondary_var, ascii=True, desc=secondary_var_desc):

                        if primary_var_desc == "lat":
                            lat = primary_data_point
                            lon = secondary_data_point
                        elif primary_var_desc == "lon":
                            lon = primary_data_point
                            lat = secondary_data_point

                        coordinate_slice_df = final_daily_df[(final_daily_df.lon == lon) & (final_daily_df.lat == lat)]
                        del coordinate_slice_df['lat']
                        del coordinate_slice_df['lon']

                        self.generate_wht(outputdir, coordinate_slice_df, lat, lon)

                        # Delete unused df
                        del coordinate_slice_df

            except KeyError as e:
                self.logger.error("Could not find all required climate variables to generate WHT file: {}".format(str(e)))

        if output_type == "csv":
            # TODO: Clean this up...

            # let's build the name of the file based on the value of lat/lon combinations
            # followed by the climate data source used (SILO or NASA POWER)

            if outputdir.is_dir() == True:

                try:

                    # Rename df columns and sort them
                    final_daily_df = final_daily_df.rename(columns={"days": "day","daily_rain": "rain",'min_temp':'mint','max_temp':'maxt','radiation':'radn'})

                    final_daily_df = final_daily_df.groupby(['lon', 'lat', 'year', 'day'])[['radn', 'maxt', 'mint', 'rain']].sum().reset_index()

                    for primary_data_point in tqdm(primary_var, ascii=True, desc=primary_var_desc):
                        
                        for secondary_data_point in tqdm(secondary_var, ascii=True, desc=secondary_var_desc):

                            if primary_var_desc == "lat":
                                lat = primary_data_point
                                lon = secondary_data_point
                            elif primary_var_desc == "lon":
                                lon = primary_data_point
                                lat = secondary_data_point

                            coordinate_slice_df = final_daily_df[(final_daily_df.lon == lon) & (final_daily_df.lat == lat)]

                            # Let's create a CSV for each lat/lon combination
                            csv_file_name = '{}-{}.{}.csv'.format(lat, lon, self.data_source)
                            full_output_path = outputdir/csv_file_name
                            self.logger.debug('Writting CSV file {} to {}'.format(csv_file_name, full_output_path))
                            coordinate_slice_df.to_csv(full_output_path, sep=',', index=False, mode='a', float_format='%.2f')

                    # Let's also create a CSV containing all the datapoints
                    csv_file_name = 'bestiapop-beastly-dataframe.csv'
                    full_output_path = outputdir/csv_file_name
                    self.logger.debug('Writting BEAST DATAFRAME :) CSV file {} to {}'.format(csv_file_name, full_output_path))
                    final_daily_df.to_csv(full_output_path, sep=',', na_rep=np.nan, index=False, mode='w', float_format='%.2f')

                except Exception as e:
                    self.logger.error(e)

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
!This climate file was created by BestiaPop on {{ current_date }} - Taming the Climate Beast
!Check our docs in https://bestiapop.readthedocs.io/en/latest/
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
        current_date = datetime.now().strftime("%d%m%Y")
        year_from = met_dataframe.year.min()
        year_to = met_dataframe.year.max()
        if self.data_source == "silo":
            data_source="SILO (Scientific Information for Land Owners) (https://www.longpaddock.qld.gov.au/silo/)"
        elif self.data_source == "nasapower":
            data_source="NASA POWER (https://power.larc.nasa.gov/)"


        # Delete df
        del met_dataframe

        in_memory_met = j2_template.render(
                                            lat=lat,
                                            lon=lon,
                                            tav=tav,
                                            amp=amp,
                                            data_source=data_source,
                                            current_date=current_date,
                                            year_from=year_from,
                                            year_to=year_to,
                                            vardata=met_df_text_output
                                        )
        df_output_buffer.close()

        full_output_path = outputdir/'{}-{}.met'.format(lat, lon)
        with open(full_output_path, 'w+') as f:
            self.logger.info('Writting MET file {}'.format(full_output_path))
            f.write(in_memory_met)

    def generate_wht(self, outputdir, wht_dataframe, lat, lon):
        """Generate WHT File

        Args:
            outputdir (str): the folder where the generated WHT files will be stored
            wht_dataframe (pandas.core.frame.DataFrame): the pandas dataframe slice to convert to WHT file
            lat (float): the latitude for which this WHT file is being generated
            lon (float): the longitude for which this WHT file is being generated
        """

        # Creating final WHT file

        # Setting up Jinja2 Template for final WHT file if required
        # Text alignment looks weird here but it must be left this way for proper output
        wht_file_j2_template = '''*WEATHER DATA : {{ lat }}-{{ lon }}

{{ wht_header }}
{{ vardata }}
        '''

        j2_template = Template(wht_file_j2_template)

        # Initialize a string buffer to receive the output of df.to_csv in-memory
        df_output_buffer = io.StringIO()

        # Save data to a buffer (same as with a regular file but in-memory):
        # Make a copy of the original dataframe so as to remove unnecessary values for the WHT file
        # but to leave the values required to calculate TAV and AMP
        wht_df_2 = wht_dataframe.copy()
        # remove year but first capture it for output file name
        del wht_df_2['year']
        # remove day
        del wht_df_2['day']
        # rename columns to match expected values in preparation for "tabulate" and right alignment
        wht_df_2 = wht_df_2.rename(columns={'dssatday':'@DATE', 'rain':'RAIN', 'mint':'TMIN', 'maxt':'TMAX', 'radn':'SRAD'})
        wht_var_data_ascii = tabulate(wht_df_2.set_index('@DATE'), tablefmt='plain', numalign='right', stralign='right', headers=wht_df_2.columns.values)
        df_output_buffer.write(wht_var_data_ascii)
        # delete df copy
        del wht_df_2

        # Get values from buffer
        # Go back to position 0 to read from buffer
        # Replace get rid of carriage return or it will add an extra new line between lines
        df_output_buffer.seek(0)
        wht_df_text_output = df_output_buffer.getvalue()
        # Get rid of Tabulate's annoying double-space padding
        wht_df_text_output = re.sub(r'^\s\s', '', wht_df_text_output)
        wht_df_text_output = re.sub(r'\n\s\s', '\n', wht_df_text_output)        
        
        # Calculate here the tav, amp values

        # Calculate amp
        # Get the months as a column
        wht_dataframe.loc[:, 'cte'] = 1997364
        wht_dataframe.loc[:, 'day2'] = wht_dataframe['day'] + wht_dataframe['cte']
        wht_dataframe.loc[:, 'date'] = (pd.to_datetime((wht_dataframe.day2 // 1000)) + pd.to_timedelta(wht_dataframe.day2 % 1000, unit='D'))
        wht_dataframe.loc[:, 'month'] = wht_dataframe.date.dt.month
        month=wht_dataframe.loc[:, 'month']

        wht_dataframe.loc[:, 'tmean'] = wht_dataframe[['maxt', 'mint']].mean(axis=1)
        tmeanbymonth = wht_dataframe.groupby(month)[["tmean"]].mean()
        maxmaxtbymonth = tmeanbymonth['tmean'].max()
        minmaxtbymonth = tmeanbymonth['tmean'].min()
        amp = np.round((maxmaxtbymonth-minmaxtbymonth), decimals=1)

        # Calculate tav
        tav = tmeanbymonth.mean().tmean.round(decimals=1)

        # Create WHT Header values
        # We don't have elevation?
        elev = -99.0
        station_hex_name = hex(14590)[2:]
        wht_header_dict = {
            '@ INSI':  [station_hex_name],
            'LAT':     [lat],
            'LONG':     [lon],
            'ELEV':     [elev],
            'TAV':     [tav],
            'AMP':     [amp],
            'REFHT':     [-99.0],
            'WNDHT':     [-99.0],
        }
        wht_dssat_header = pd.DataFrame(wht_header_dict)
        wht_header = tabulate(
            wht_dssat_header.set_index('@ INSI'),
            tablefmt='plain',
            numalign='right',
            stralign='right',
            headers=wht_dssat_header.columns.values,
            floatfmt=('', '.3f', '.3f', '.1f', '.1f', '.1f', '.1f', '.1f')
        )
        # Get rid of Tabulate's annoying double-space padding
        wht_header = re.sub(r"^\s\s", "", wht_header)
        wht_header = re.sub(r"\n\s\s", "\n", wht_header) 

        # Get vales to configure WHT file name as per DSSAT convention
        flat = str(lat).replace(".", "")
        flon = str(lon).replace(".", "")
        fyear_array = wht_dataframe['dssatday'].apply(lambda x: int(str(x)[:2:])).unique()
        fyear = fyear_array[0]
        fyear_len = len(fyear_array)

        # Delete df
        del wht_dataframe

        in_memory_dssat = j2_template.render(
                                            lat=lat,
                                            lon=lon,
                                            wht_header=wht_header,
                                            vardata=wht_df_text_output
                                        )
        df_output_buffer.close()



        full_output_path = outputdir/'{}{}{}{}.WHT'.format(flat, flon, fyear, fyear_len)
        with open(full_output_path, 'w+') as f:
            self.logger.info('Writting WHT file {}'.format(full_output_path))
            f.write(in_memory_dssat)