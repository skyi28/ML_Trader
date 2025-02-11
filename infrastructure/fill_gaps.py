"""
This file contains the implementation of the GapFiller class, which is responsible for filling gaps in historical data for a given symbol.
The class uses a logger, database, and BybitData object to perform the necessary operations.

The GapFiller class provides the following functionalities:
1. Fetching and identifying gaps in the historical data for a given symbol.
2. Fetching data from the database after a specified gap start timestamp and deleting it.
3. Downloading missing historical data for a given gap.
4. Inserting newly downloaded data into the database.
5. Reinserting temporarily stored data into the database.
6. Checking if the timestamps in the database for a given symbol are consecutive and in order.
7. Verifying the historical data by plotting the closing prices over time using matplotlib.

The class has the following attributes:
- logger: An instance of the Logger class for logging messages.
- db: An instance of the Database class for interacting with the database.
- bd: An instance of the BybitData class for fetching historical data from Bybit.

The class has the following methods:
- __init__: Initializes the GapFiller class.
- fetch_gaps: Fetches and identifies gaps in the historical data for a given symbol.
- fetch_and_delete_after_gap: Fetches data from the database after a specified gap start timestamp and deletes it.
- fill_gaps: Fills gaps in the historical data for a given symbol by fetching missing data, deleting existing data after the gap, and reinserting the data.
- check_consecutive_timestamps: Checks if the timestamps in the database for a given symbol are consecutive and in order.
- verify_by_plotting: Verifies the historical data by plotting the closing prices over time using matplotlib.
"""
import os
import sys
basedir = os.path.abspath(os.path.dirname(__file__)) + os.sep
basedir_split = basedir.split(os.sep)
path_to_config = ''
for part in basedir_split:
    path_to_config += part + os.sep
    if part == "ML_Trader":
        path_to_config += f'{os.sep}config'
        break
sys.path.append(path_to_config)

import matplotlib.pyplot as plt
import datetime
import time
import pandas as pd

from infrastructure.logger import create_logger
from infrastructure.bybit_data import BybitData
from infrastructure.database import Database


class GapFiller:
    def __init__(self):
        """
        Initializes the GapFiller class.

        This class is responsible for filling gaps in historical data for a given symbol.
        It uses a logger, database, and BybitData object to perform the necessary operations.

        Attributes:
        logger (Logger): An instance of the Logger class for logging messages.
        db (Database): An instance of the Database class for interacting with the database.
        bd (BybitData): An instance of the BybitData class for fetching historical data from Bybit.
        """
        self.logger = create_logger('gap_filler.log')
        self.logger.info('-'*100)
        self.db = Database()
        self.bd = BybitData()

    def fetch_gaps(self, symbol: str) -> list[tuple[pd.Timestamp, pd.Timestamp]]:
        """
        Fetches and identifies gaps in the historical data for a given symbol.

        Parameters:
        symbol (str): The symbol for which to fetch and identify gaps.

        Returns:
        list[tuple[pd.Timestamp, pd.Timestamp]]: A list of tuples, where each tuple represents a gap in the historical data.
        Each tuple contains the start and end timestamps of the gap.
        """
        query = f"""SELECT timestamp FROM {symbol} ORDER BY timestamp ASC;"""
        df = self.db.execute_read_query(query, return_type='pd.DataFrame')

        df["time_diff"] = df["timestamp"].diff()
        gaps: pd.DataFrame = df[df["time_diff"] > pd.Timedelta(minutes=1)]
        
        gap_list: list[tuple] = []
        for idx, row in gaps.iterrows():
            gap_start: pd.Timestamp = df.loc[idx - 1, "timestamp"] + pd.Timedelta(minutes=1)
            gap_end: pd.Timestamp = row["timestamp"] - pd.Timedelta(minutes=0)
            gap_list.append((gap_start, gap_end))
        
        return gap_list

    def fetch_and_delete_after_gap(self, gap_start, symbol: str) -> pd.DataFrame:
        """
        Fetches data from the database after a specified gap start timestamp and deletes it.

        Parameters:
        gap_start (datetime.datetime): The timestamp marking the start of the gap.
        symbol (str): The symbol for which to fetch and delete data.

        Returns:
        pd.DataFrame: A DataFrame containing the fetched data after the gap.
        """
        query: str = f"""SELECT * FROM {symbol} WHERE "timestamp" >= '{gap_start}' ORDER BY timestamp ASC;"""
        df: pd.DataFrame = self.db.execute_read_query(query, return_type='pd.DataFrame')

        self.logger.info(f'DELETING EVERYTHING AFTER {gap_start}')
        
        delete_query: str = f"""DELETE FROM {symbol} WHERE "timestamp" >= '{gap_start}';"""
        self.db.execute_write_query(delete_query, (gap_start,))
        self.db.commit()

        newest_date_in_database: datetime.datetime = self.db.execute_read_query(f"""SELECT timestamp FROM {symbol} ORDER BY "timestamp" DESC LIMIT(1)""")
        self.logger.info(f'NEWEST DATE IN DATABASE AFTER DELETING: {newest_date_in_database}')
        
        return df

    def fill_gaps(self, symbol: str) -> None:
        """
        Fills gaps in the historical data for a given symbol by fetching missing data,
        deleting existing data after the gap, and reinserting the data.

        Parameters:
        symbol (str): The symbol for which to fill gaps.

        Returns:
        None
        """
        start_time_overall: float = time.time()
        gaps: list[tuple[pd.Timestamp, pd.Timestamp]] = self.fetch_gaps(symbol=symbol)
        
        for gap_start, gap_end in gaps:
            start_time_gap: float = time.time()
            self.logger.info('-'*50 + f'{symbol.upper()}' + '-'*50)
            self.logger.info(f"Filling gap from {gap_start} to {gap_end}")

            # Step 1: Fetch and delete data after the gap
            start_time: float = time.time()
            self.logger.info('Temporary storing existing data and deleting existing data after the gap...')
            temp_data: pd.DataFrame = self.fetch_and_delete_after_gap(gap_start, symbol)
            self.logger.info(f"Temporary storage and deletion took {time.time() - start_time:.2f} seconds.")

            # Step 2: Download missing historical data
            start_time: float = time.time()
            self.logger.info('Downloading gap data...')
            new_data: pd.DataFrame = self.bd.get_historic_data(start=gap_start, end=gap_end)
            self.logger.info(f'OLDEST DOWNLOADED data: {new_data["Timestamp"].min()}')
            self.logger.info(f'NEWEST DOWNLOADED data: {new_data["Timestamp"].max()}')
            self.logger.info(f"Download took {time.time() - start_time:.2f} seconds.")
            
            # Step 3: Insert newly downloaded data
            start_time: float = time.time()
            self.logger.info(f'Inserting {len(new_data)} rows...')
            self.bd.insert_historical_data(symbol.upper(), new_data)
            self.logger.info(f"Insertion took {time.time() - start_time:.2f} seconds.")

            # Step 4: Reinsert temporarily stored data
            start_time: float = time.time()
            self.logger.info(f'Reinserting {len(temp_data)} temporary stored rows...')
            self.logger.info(f'OLDEST DATA IN STORED IN TEMPORARY: {temp_data["timestamp"].min()}')
            self.bd.insert_historical_data(symbol.upper(), temp_data)
            self.logger.info(f"Reinsertion took {time.time() - start_time:.2f} seconds.")

            self.logger.info(f"Process for whole gap took {time.time() - start_time_gap:.2f} seconds.")

        self.logger.info(f"Filling all gaps took {round(time.time() - start_time_overall, 2)} seconds.")

    def check_consecutive_timestamps(self, symbol: str) -> tuple[bool, bool] | tuple[bool, pd.DataFrame]:
        """
        This function checks if the timestamps in the database for a given symbol are consecutive and in order.

        Parameters:
        symbol (str): The symbol for which to check the timestamps.

        Returns:
        tuple[bool, bool] | tuple[bool, pd.DataFrame]: A tuple containing two elements. The first element is a boolean indicating
        whether all timestamps are consecutive and in order (True) or not (False). The second element is either None or a DataFrame
        showing the rows where the timestamps are not consecutive. If the timestamps are consecutive, the second element is False.
        """
        query: str = f"""SELECT "timestamp" FROM {symbol}"""
        df: pd.DataFrame = self.db.execute_read_query(query, return_type='pd.DataFrame')

        # Ensure 'timestamp' column is in datetime format
        df['timestamp'] = pd.to_datetime(df['timestamp'])

        # Calculate the time difference between consecutive timestamps
        time_diff: pd.Series = df['timestamp'].diff()

        # Check if the time difference is exactly 1 minute (or adjust as needed)
        is_consecutive: pd.Series = time_diff.fillna(pd.Timedelta(seconds=0)) == pd.Timedelta(minutes=1)

        # Identify where the data is not in order
        non_consecutive_rows: pd.DataFrame = df[~is_consecutive]  # rows where is_consecutive is False

        # Create a dataframe showing the time differences where not in order
        if not non_consecutive_rows.empty:
            non_consecutive_rows['time_diff'] = time_diff[~is_consecutive]

        # Return True if all differences are 1 minute, otherwise False
        # Return results
        if non_consecutive_rows.empty:
            return True, None  # All timestamps are in order
        else:
            return False, non_consecutive_rows  # There are issues with the order

    def verify_by_plotting(self, symbol: str) -> None:
        """
        This function retrieves historical data for a given symbol from the database,
        plots the closing prices over time, and displays the plot using matplotlib.

        Parameters:
        symbol (str): The symbol for which to retrieve and plot historical data.

        Returns:
        None: The function does not return any value. It displays a plot using matplotlib.
        """
        query: str = f"""SELECT "timestamp", close FROM {symbol}"""
        data: pd.DataFrame = self.db.execute_read_query(query, return_type='pd.DataFrame')

        # Create a figure and axis for plotting
        fig = plt.figure(figsize=(16,9))
        ax = fig.add_subplot()

        # Plot the closing prices over time
        ax.plot(data['timestamp'], data['close'])

        # Display the plot
        plt.show()

    def download_missing_data_since_last_application_start(self, symbol: str) -> None:
        """
        This function downloads missing historical data for a given symbol from the database,
        starting from the newest date in the database until the current date.

        Parameters:
        symbol (str): The symbol for which to download missing historical data.

        Returns:
        None: The function does not return any value. It downloads and inserts data into the database.
        """
        try:
            newest_date_in_database: datetime.datetime = self.db.execute_read_query(f"""SELECT timestamp FROM {symbol} ORDER BY "timestamp" DESC LIMIT(1)""")[0][0]
        except Exception as e:
            self.logger.error(f"Error fetching the newest date in the database - The table {symbol} might be empty or does not exist. {e}")
            newest_date_in_database: datetime.datetime = datetime.datetime.now() - datetime.timedelta(days=30)
        self.logger.info(f"Downloading missing data from {newest_date_in_database} until {datetime.datetime.now()}.")
        new_data: pd.DataFrame = self.bd.get_historic_data(
                                    start=newest_date_in_database,
                                    end=datetime.datetime.now(),
                                    symbol=symbol.upper()
                                )
        self.bd.insert_historical_data(symbol.upper(), new_data)
        self.logger.info(f"Downloaded {len(new_data)} new rows of data for {symbol}.")
