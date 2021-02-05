

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
            if 'bestiapop' in __name__:
                coloredlogs.install(fmt='%(asctime)s - %(name)s - %(message)s', level="WARNING", logger=logger)
            else:
                coloredlogs.install(fmt='%(asctime)s - %(name)s - %(message)s', level="DEBUG", logger=logger)

        except ModuleNotFoundError:
            logger = logging.getLogger('POPBEAST.DATAOUTPUT')
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(message)s')
            console_handler = logging.StreamHandler()
            console_handler.setFormatter(formatter)
            console_handler.setLevel(logging.DEBUG)
            logger.addHandler(console_handler)
            if 'bestiapop' in __name__:
                logger.setLevel(logging.WARNING)
            else:
                logger.setLevel(logging.INFO)

        # Setting up class variables
        self.logger = logger
        self.data_source = data_source
        if 'bestiapop' in __name__:
            self.tqdm_enabled = True
        else:
            self.tqdm_enabled = False
        
    def generate_output(self, final_daily_df, lat_range, lon_range, outputdir=None, output_type="met"):
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

            for primary_data_point in tqdm(primary_var, ascii=True, desc=primary_var_desc, disable=self.tqdm_enabled):
                
                for secondary_data_point in tqdm(secondary_var, ascii=True, desc=secondary_var_desc, disable=self.tqdm_enabled):

                    if primary_var_desc == "lat":
                        lat = primary_data_point
                        lon = secondary_data_point
                    elif primary_var_desc == "lon":
                        lon = primary_data_point
                        lat = secondary_data_point

                    coordinate_slice_df = final_daily_df[(final_daily_df.lon == lon) & (final_daily_df.lat == lat)]

                    # We shall output the plain final DataFrame to stdout using tabulate
                    print("\n")
                    print(tabulate(
                                    coordinate_slice_df,
                                    headers=coordinate_slice_df.keys(),
                                    tablefmt='psql',
                                    numalign='right',
                                    stralign='right',
                                    showindex=False))
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

                for primary_data_point in tqdm(primary_var, ascii=True, desc=primary_var_desc, disable=self.tqdm_enabled):
                    
                    for secondary_data_point in tqdm(secondary_var, ascii=True, desc=secondary_var_desc, disable=self.tqdm_enabled):

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

        if output_type == "wth":
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
                
                self.logger.info("Proceeding to the generation of WTH files")

                for primary_data_point in tqdm(primary_var, ascii=True, desc=primary_var_desc, disable=self.tqdm_enabled):
                    
                    for secondary_data_point in tqdm(secondary_var, ascii=True, desc=secondary_var_desc, disable=self.tqdm_enabled):

                        if primary_var_desc == "lat":
                            lat = primary_data_point
                            lon = secondary_data_point
                        elif primary_var_desc == "lon":
                            lon = primary_data_point
                            lat = secondary_data_point

                        coordinate_slice_df = final_daily_df[(final_daily_df.lon == lon) & (final_daily_df.lat == lat)]
                        del coordinate_slice_df['lat']
                        del coordinate_slice_df['lon']

                        self.generate_wth(outputdir, coordinate_slice_df, lat, lon)

                        # Delete unused df
                        del coordinate_slice_df

            except KeyError as e:
                self.logger.error("Could not find all required climate variables to generate WTH file: {}".format(str(e)))

        if output_type == "dataframe":
            try:

                # Rename df columns and sort them
                final_daily_df = final_daily_df.rename(columns={"days": "day","daily_rain": "rain",'min_temp':'mint','max_temp':'maxt','radiation':'radn'})

                final_daily_df = final_daily_df.groupby(['lon', 'lat', 'year', 'day'])[['radn', 'maxt', 'mint', 'rain']].sum().reset_index()
                
                return final_daily_df

            except Exception as e:
                    self.logger.error(e)
            
        if output_type == "csv":
            # TODO: Clean this up...

            # let's build the name of the file based on the value of lat/lon combinations
            # followed by the climate data source used (SILO or NASA POWER)

            if outputdir.is_dir() == True:

                try:

                    # Rename df columns and sort them
                    final_daily_df = final_daily_df.rename(columns={"days": "day","daily_rain": "rain",'min_temp':'mint','max_temp':'maxt','radiation':'radn'})

                    final_daily_df = final_daily_df.groupby(['lon', 'lat', 'year', 'day'])[['radn', 'maxt', 'mint', 'rain']].sum().reset_index()

                    for primary_data_point in tqdm(primary_var, ascii=True, desc=primary_var_desc, disable=self.tqdm_enabled):
                        
                        for secondary_data_point in tqdm(secondary_var, ascii=True, desc=secondary_var_desc, disable=self.tqdm_enabled):

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

    def generate_wth(self, outputdir, wth_dataframe, lat, lon):
        """Generate WTH File

        Args:
            outputdir (str): the folder where the generated WTH files will be stored
            wth_dataframe (pandas.core.frame.DataFrame): the pandas dataframe slice to convert to WTH file
            lat (float): the latitude for which this WTH file is being generated
            lon (float): the longitude for which this WTH file is being generated
        """

        # Creating final WTH file

        # Setting up Jinja2 Template for final WTH file if required
        # Text alignment looks weird here but it must be left this way for proper output
        wth_file_j2_template = '''*WEATHER DATA : {{ lat }}-{{ lon }}

{{ wth_header }}
{{ vardata }}
        '''

        j2_template = Template(wth_file_j2_template)

        # Initialize a string buffer to receive the output of df.to_csv in-memory
        df_output_buffer = io.StringIO()

        # Save data to a buffer (same as with a regular file but in-memory):
        # Make a copy of the original dataframe so as to remove unnecessary values for the WTH file
        # but to leave the values required to calculate TAV and AMP
        wth_df_2 = wth_dataframe.copy()
        # remove year but first capture it for output file name
        del wth_df_2['year']
        # remove day
        del wth_df_2['day']
        # rename columns to match expected values in preparation for "tabulate" and right alignment
        wth_df_2 = wth_df_2.rename(columns={'dssatday':'@DATE', 'rain':'RAIN', 'mint':'TMIN', 'maxt':'TMAX', 'radn':'SRAD'})
        wth_var_data_ascii = tabulate(
                                    wth_df_2.set_index('@DATE'),
                                    tablefmt='plain',
                                    numalign='right',
                                    stralign='right',
                                    headers=wth_df_2.columns.values) # Add this for float equalization if required --> floatfmt=['.2f' for x in wth_df_2.columns]

        df_output_buffer.write(wth_var_data_ascii)
        # delete df copy
        del wth_df_2

        # Get values from buffer
        # Go back to position 0 to read from buffer
        # Replace get rid of carriage return or it will add an extra new line between lines
        df_output_buffer.seek(0)
        wth_df_text_output = df_output_buffer.getvalue()
        # Get rid of Tabulate's annoying double-space padding
        wth_df_text_output = re.sub(r'^\s\s', '', wth_df_text_output)
        wth_df_text_output = re.sub(r'\n\s\s', '\n', wth_df_text_output)        
        
        # Calculate here the tav, amp values

        # Calculate amp
        # Get the months as a column
        wth_dataframe.loc[:, 'cte'] = 1997364
        wth_dataframe.loc[:, 'day2'] = wth_dataframe['day'] + wth_dataframe['cte']
        wth_dataframe.loc[:, 'date'] = (pd.to_datetime((wth_dataframe.day2 // 1000)) + pd.to_timedelta(wth_dataframe.day2 % 1000, unit='D'))
        wth_dataframe.loc[:, 'month'] = wth_dataframe.date.dt.month
        month=wth_dataframe.loc[:, 'month']

        wth_dataframe.loc[:, 'tmean'] = wth_dataframe[['maxt', 'mint']].mean(axis=1)
        tmeanbymonth = wth_dataframe.groupby(month)[["tmean"]].mean()
        maxmaxtbymonth = tmeanbymonth['tmean'].max()
        minmaxtbymonth = tmeanbymonth['tmean'].min()
        amp = np.round((maxmaxtbymonth-minmaxtbymonth), decimals=1)

        # Calculate tav
        tav = tmeanbymonth.mean().tmean.round(decimals=1)

        # Create WTH Header values
        # We don't have elevation?
        elev = -99

        wth_header_dict = {
            '@ INSI':  'BPOP',
            'LAT':     [lat],
            'LONG':     [lon],
            'ELEV':     [elev],
            'TAV':     [tav],
            'AMP':     [amp],
            'REFHT':     [-99],
            'WNDHT':     [-99],
        }
        wth_dssat_header = pd.DataFrame(wth_header_dict)
        wth_header = tabulate(
            wth_dssat_header.set_index('@ INSI'),
            tablefmt='plain',
            numalign='right',
            stralign='right',
            headers=wth_dssat_header.columns.values,
            floatfmt=('', '.2f', '.2f', '.1f', '.1f', '.1f', '.1f', '.1f')
        )
        # Get rid of Tabulate's annoying double-space padding
        wth_header = re.sub(r"^\s\s", "", wth_header)
        wth_header = re.sub(r"\n\s\s", "\n", wth_header) 

        # Get required values to configure WTH file name as per DSSAT convention
        flat = str(lat).replace(".", "")
        flon = str(lon).replace(".", "")
        fyear_array = wth_dataframe['dssatday'].apply(lambda x: int(str(x)[:2:])).unique()
        fyear = fyear_array[0]
        fyear_len = len(fyear_array)

        # Delete df
        del wth_dataframe

        in_memory_dssat = j2_template.render(
                                            lat=lat,
                                            lon=lon,
                                            wth_header=wth_header,
                                            vardata=wth_df_text_output)
        df_output_buffer.close()



        full_output_path = outputdir/'{}{}{}{}.WTH'.format(flat, flon, fyear, fyear_len)
        with open(full_output_path, 'w+') as f:
            self.logger.info('Writting WTH file {}'.format(full_output_path))
            f.write(in_memory_dssat)