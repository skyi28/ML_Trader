"""
This python module contains a function to manipulate a PostgreSQL database.
"""
import pandas as pd
import psycopg2
from sqlalchemy import create_engine, Engine
from config import load_config
from logger import create_logger

class Database:
    def __init__(self) -> None:
        """
        Initialize a Database object.

        This function initializes a Database object by loading the configuration settings, creating a logger,
        establishing a connection to the PostgreSQL database, creating an engine and a cursor.

        Parameters:
        None

        Returns:
        None
        """
        self.config = load_config('config.yaml')
        self.logger = create_logger('database.log')
        self.engine = self.create_engine()
        self.connection = self.create_connection()
        self.cursor = self.create_cursor()
        # self.create_needed_tables()
        
    def create_connection(self) -> psycopg2.extensions.connection:
        """
        This function creates a connection to a PostgreSQL database using the provided configuration settings.

        Parameters:
        self (Database): The instance of the Database class.

        Returns:
        psycopg2.extensions.connection: A connection object to the PostgreSQL database. If the connection fails,
        it returns None.
        """
        try:
            connection = psycopg2.connect(database=self.config.postgres.database,
                                        user=self.config.postgres.username,
                                        password=self.config.postgres.password,
                                        host=self.config.postgres.host,
                                        port=self.config.postgres.port)
            self.logger.debug('create_connection: Created connection!')
            return connection
        except Exception as e:
            self.logger.error(f'create_connection: Could not create a connection: {str(e)}')
            return None
        
    def create_cursor(self) -> psycopg2.extensions.cursor:
        """
        This function creates a cursor for executing SQL commands in the PostgreSQL database.

        Parameters:
        self (Database): The instance of the Database class.

        Returns:
        psycopg2.extensions.cursor: A cursor object for executing SQL commands. If the cursor creation fails,
        it returns None. The cursor object is used to interact with the database and execute SQL queries.
        """
        try:
            cursor = self.connection.cursor()
            self.logger.debug('create_cursor: Created cursor!')
            return cursor
        except Exception as e:
            self.logger.error(f'create_cursor: Could not create a cursor: {str(e)}')
            return None
        
    def create_engine(self) -> Engine:
        """
        This function creates a SQLAlchemy engine for connecting to a PostgreSQL database.

        Parameters:
        self (Database): The instance of the Database class.

        Returns:
        Engine: A SQLAlchemy engine object for interacting with the PostgreSQL database. If the engine creation fails,
        it returns None. The engine object is used to create a connection pool and manage connections to the database.
        """
        try:
            engine = create_engine(f'postgresql://'
                                    f'{self.config.postgres.username}:'
                                    f'{self.config.postgres.password}@'
                                    f'{self.config.postgres.host}:'
                                    f'{self.config.postgres.port}/'
                                    f'{self.config.postgres.database}')
            self.logger.debug('create_engine: Created engine!')
            return engine
        except Exception as e:
            self.logger.error(f'create_engine: Could not create an engine: {str(e)}')
            return None
        
    def commit(self) -> None:
        """
        Commits the current transaction to the PostgreSQL database.

        This function is used to permanently save the changes made to the database during the current transaction.
        It is essential to call this function after executing write queries to ensure that the changes are saved.

        Parameters:
        self (Database): The instance of the Database class.

        Returns:
        None: This function does not return any value.
        """
        try:
            self.connection.commit()
        except Exception as e:
            self.logger.error(f'commit: Error committing changes: {str(e)}')
        
    def execute_write_query(self, query: str, params: tuple = ()) -> int | None:
        """
        Executes a write query (INSERT, UPDATE, DELETE) on the PostgreSQL database.

        Parameters:
        - query (str): The SQL query to be executed.
        - params (tuple, optional): A tuple of parameters to be used in the SQL query. Defaults to an empty tuple.

        Returns:
        - int | None: Returns the number of rows affected by the query if successful. If an error occurs, returns None.
        """
        try:
            self.cursor.execute(query, params)
            return self.cursor.rowcount
        except psycopg2.OperationalError as e:
            try:
                self.connection.rollback()
            except Exception as e:
                self.logger.error(f'execute_write_query: Error rolling back changes: {str(e)}')
            self.logger.error(f'execute_write_query: Error executing the query: {str(e)}')
            self.logger.error(f'execute_write_query: Query: {query}')    
        except Exception as e:
            self.logger.error(f'execute_write_query: Error executing the query: {str(e)}')
            self.logger.error(f'execute_write_query: Query: {query}')
            
    def execute_read_query(self, query: str, first_only: bool = False, return_column_names: bool = False, return_type: str = 'list') -> list | tuple | pd.DataFrame | None:
        """
        Executes a read query on the PostgreSQL database and returns the result based on the specified parameters.

        Parameters:
        - query (str): The SQL query to be executed.
        - first_only (bool, optional): If True, only the first row of the result is returned. Defaults to False.
        - return_column_names (bool, optional): If True, the column names of the result are returned along with the data. Defaults to False.
        - return_type (str, optional): The type of the result. Can be either 'list' or 'pd.DataFrame'. Defaults to 'list'.

        Returns:
        - list | tuple | pd.DataFrame | None: The result of the query. Depending on the 'return_type' parameter, it can be a list of tuples, a tuple of list and column names, a pandas DataFrame, or None in case of an error.
        """
        if return_type not in ['pd.DataFrame', 'list']:
            self.logger.error(f'execute_read_query: Return type {return_type} is not implemented!')
            return None
        
        if return_type == 'list':
            try:
                self.cursor.execute(query)
                if first_only:
                    result = self.cursor.fetchone()
                    self.logger.debug('execute_read_query: Returns a single item!')
                else:
                    result = self.cursor.fetchall()
                    self.logger.debug('execute_read_query: Returns a list of items!')
                
                if return_column_names:
                    column_names = [d[0] for d in self.cursor.description()]
                    
                if return_column_names:
                    return result, column_names
                return result
            except psycopg2.OperationalError as e:
                self.logger.error(f'execute_read_query: Error executing query: {query} \n{str(e)}')
            except Exception as e:
                self.logger.error(f'execute_read_query: Error executing query: {query} \n{str(e)}')
        elif return_type == 'pd.DataFrame':
            try:
                result = pd.read_sql_query(query, self.engine)
                self.logger.debug('execute_read_query: Returns a DataFrame!')
            except Exception as e:
                self.logger.error(f'execute_read_query: Error reading the query: {query} \n{str(e)}')
        
        
    def create_table(self, table_name: str, column_names_and_types: list[str], unique_constraints: list[str] = None) -> bool:
        """
        Creates a new table in the PostgreSQL database with the specified column names and types.

        Parameters:
        - table_name (str): The name of the table to be created.
        - column_names_and_types (list): A string containing the column names and their corresponding data types.
        The string should be formatted as 'column1 type1, column2 type2, ...'.

        Returns:
        - bool: Returns True if the table is created successfully, False otherwise.
        """
        try:
            column_names = []
            column_types = []
            for column in column_names_and_types:
                column_names.append(column.split(' ')[0])
                column_types.append(column.split(' ')[1])
            assert len(column_names) == len(column_types), self.logger.error('create_table: Column names and types must have the same length!')
            
            query: str = f'CREATE TABLE IF NOT EXISTS {table_name} ('
            for idx, column_name in enumerate(column_names):
                query += f'{column_name} {column_types[idx]},'
            query = query[:-1] # remove last comma
            
            if unique_constraints:
                for column in unique_constraints:
                    query += f',UNIQUE ({column}),'
                query = query[:-1]
            query += ');'
            
            self.execute_write_query(query)
            self.commit()
            return True
        except Exception as e:
            self.logger.error(f'create_table: Error creating the table: {str(e)}')
            return False
        
    def delete_table(self, table_name: str) -> bool:
        """
        Deletes a table from the PostgreSQL database.

        Parameters:
        - table_name (str): The name of the table to be deleted.

        Returns:
        - bool: Returns True if the table is deleted successfully, False otherwise.
        If an error occurs during the deletion process, the function logs the error and returns False.
        """
        try:
            query = f'DROP TABLE IF EXISTS {table_name};'
            self.execute_write_query(query)
            return True
        except Exception as e:
            self.logger.error(f'delete_table: Error deleting the table: {str(e)}')
            return False
        
    def truncate_table(self, table_name: str) -> bool:
        """
        Truncates a table from the PostgreSQL database.

        Parameters:
        - table_name (str): The name of the table to be deleted.

        Returns:
        - bool: Returns True if the table is truncated successfully, False otherwise.
        If an error occurs during the deletion process, the function logs the error and returns False.
        """
        try:
            query = f'TRUNCATE TABLE {table_name};'
            self.execute_write_query(query)
            return True
        except Exception as e:
            self.logger.error(f'truncate_table: Error truncating the table: {str(e)}')
            return False
        
    def add_column(self, table_name: str, column_name: str, column_type: str) -> None:
        """
        Adds a new column to an existing table in the PostgreSQL database.

        Parameters:
        - table_name (str): The name of the table to which the new column will be added.
        - column_name (str): The name of the new column to be added.
        - column_type (str): The data type of the new column to be added.

        Returns:
        - None
        """
        query: str = f'ALTER TABLE {table_name} ADD COLUMN IF NOT EXISTS {column_name} {column_type}'
        self.execute_write_query(query)
        self.commit()
        
    def count_columns_of_table(self, table_name: str) -> int | None:
        """
        Counts the number of columns in a specified table in the PostgreSQL database.

        Parameters:
        - table_name (str): The name of the table in the PostgreSQL database.

        Returns:
        - int | None: The number of columns in the specified table. If an error occurs during the count,
        it returns None. If the table does not exist, it returns 0.
        """
        try:
            query = f"SELECT COUNT(*) FROM information_schema.columns WHERE table_name = '{table_name}';"
            result = self.execute_read_query(query, first_only=True)
            if result is not None:
                return result[0]
            return 0
        except Exception as e:
            self.logger.error(f'count_columns_of_table: Error counting the columns: {str(e)}')
            return None
        
    def count_rows_of_table(self, table_name: str) -> int | None:
        """
        Counts the number of rows in a specified table in the PostgreSQL database.

        Parameters:
        - table_name (str): The name of the table in the PostgreSQL database.

        Returns:
        - int | None: The number of rows in the specified table. If an error occurs during the count,
        it returns None. If the table does not exist, it returns 0.
        """
        try:
            query = f"SELECT COUNT(*) FROM {table_name};"
            result = self.execute_read_query(query, first_only=True)
            if result is not None:
                return result[0]
            return 0
        except Exception as e:
            self.logger.error(f'count_rows_of_table: Error counting the rows: {str(e)}')
            return None
            