from sqlite3 import Error
import sqlite3
import numpy as np


class TorqueReactionTestDatabase:

    def __init__(self, database_name):
        self.database_name = database_name
        self.conn = self.create_connection()


    def create_table(self, create_table_sql):
        """ Execute a SQL statement to create a table """
        try:
            c = self.conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)


    def create_connection(self):
        """ create a table from the create_table_sql statement """
        try:
            return sqlite3.connect(self.database_name)
        except Error as e:
            print(e)

    def get_connection(self):
        """
        Return a new connection to the SQLite database.
        This connection is thread-local.
        """
        try:
            return sqlite3.connect(self.database_name, check_same_thread=False)
        except Error as e:
            print(e)

    def create_table(self, create_table_sql):
        """ create table from the create_table_sql statement """
        try:
            c = self.conn.cursor()
            c.execute(create_table_sql)
        except Error as e:
            print(e)

    def add_trial(self):
        """
            Add a new trial to the trials table
        """
        sql = ''' INSERT INTO trials DEFAULT VALUES '''
        cur = self.conn.cursor()
        cur.execute(sql)
        self.conn.commit()
        return cur.lastrowid


    def add_data(self, trial_id, time, pos, vel, torque_setpoint, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured):
        """
        Insert data into data table
        """
        sql = ''' INSERT INTO data(trial_id, time, pos, vel, torque_setpoint, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured)
                  VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?) '''
        cur = self.conn.cursor()
        try:
            cur.execute(sql, (trial_id, time, pos, vel, torque_setpoint, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured))
            self.conn.commit()
        except Exception as e:
            print(f"Error inserting data: {e}")
        return cur.lastrowid

    def all_trials(self):
        """
        Returns all the trials
        """
        sql = ''' SELECT * FROM trials '''
        cur = self.conn.cursor()
        cur.execute(sql)
        return cur.fetchall()

    def all_data(self, trial_id):
        """
        Returns all data for a given trial
        """
        sql = ''' SELECT * FROM data WHERE trial_id=? '''
        cur = self.conn.cursor()
        cur.execute(sql, (trial_id,))
        return cur.fetchall()

    def get_column_data(self, table_name, column_name):
        """
        Get all values from a specific column in a table.
        """
        cur = self.conn.cursor()
        cur.execute(f"SELECT {column_name} FROM {table_name}")
        results = cur.fetchall()
        return [item[0] for item in results]

    def delete_trial(self, trial_id):
        """
        Delete a trial and its associated data
        """
        # Delete associated imu_data first to maintain integrity
        cur = self.conn.cursor()
        cur.execute('''DELETE FROM data WHERE trial_id=?''', (trial_id,))
        cur.execute('''DELETE FROM trials WHERE trial_id=?''', (trial_id,))
        self.conn.commit()

    def get_trial_data(self, trial_id, cleaned=False):
        """
        Fetch all data for a given trial ID from either the original or cleaned data table.
        """
        table_name = "cleaned_data" if cleaned else "data"
        sql = f''' SELECT time, torque_setpoint, torque_estimate, vel FROM {table_name} WHERE trial_id=? '''
        cur = self.conn.cursor()
        cur.execute(sql, (trial_id,))
        return cur.fetchall()

    def get_data_for_plotting(self, trial_id, data_type, cleaned=False):
        """
        Fetch a specific type of data and corresponding time values for a given trial ID
        from either the original or cleaned data table.
        """
        table_name = "cleaned_data" if cleaned else "data"
        sql = f"SELECT time, {data_type} FROM {table_name} WHERE trial_id=?"
        cur = self.conn.cursor()
        cur.execute(sql, (trial_id,))
        return cur.fetchall()

#--------------------------- Cleaning Data Functions --------------------------------------------------------

    def remove_outliers_std(self, data, num_std=1.6):
        """
        Removes outliers from a dataset based on standard deviation.

        Parameters:
        data (list): The dataset to be cleaned.
        num_std (int): Number of standard deviations to use as the threshold. Default is 2.

        Returns:
        list: The cleaned dataset with outliers removed.
        """
        mean = np.mean(data)
        std_dev = np.std(data)
        lower_bound = mean - num_std * std_dev
        upper_bound = mean + num_std * std_dev

        cleaned_data = [x for x in data if lower_bound <= x <= upper_bound]
        return cleaned_data


    def clean_trial_data(self, trial_id):
        # Fetch data for the trial
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM data WHERE trial_id=?", (trial_id,))
        rows = cur.fetchall()

        # Assuming your data columns are: time, pos, vel, torque_setpoint, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured
        # Adjust the indices based on your actual table structure
        columns = {'pos': 3, 'vel': 4, 'torque_setpoint': 5, 'torque_estimate': 6, 'bus_voltage': 7, 'bus_current': 8, 'iq_setpoint': 9, 'iq_measured': 10}
        cleaned_data = []

        # Clean each column separately
        for col_name, col_idx in columns.items():
            col_data = [row[col_idx] for row in rows]
            cleaned_col_data = remove_outliers(col_data)
            for i, row in enumerate(rows):
                if col_data[i] in cleaned_col_data:
                    cleaned_data.append(row)

        # Create a new table for cleaned data
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS cleaned_data (
               id INTEGER PRIMARY KEY AUTOINCREMENT,
               trial_id INTEGER,
               time REAL,
               pos REAL,
               vel REAL,
               torque_setpoint REAL,
               torque_estimate REAL,
               bus_voltage REAL,
               bus_current REAL,
               iq_setpoint REAL,
               iq_measured REAL,
               FOREIGN KEY (trial_id) REFERENCES trials (trial_id)
            );'''
        )

        # Insert cleaned data into the new table
        cur.executemany("INSERT INTO cleaned_data (trial_id, time, pos, vel, torque_setpoint, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", cleaned_data)
        self.conn.commit()

    
    def remove_outliers_and_create_clean_table(self, trial_id):
        # Fetch data for the trial
        cur = self.conn.cursor()
        cur.execute("SELECT * FROM data WHERE trial_id=?", (trial_id,))
        rows = cur.fetchall()

        # Assuming your data columns are: time, pos, vel, torque_setpoint, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured
        columns = {'pos': 3, 'vel': 4, 'torque_setpoint': 5, 'torque_estimate': 6, 'bus_voltage': 7, 'bus_current': 8, 'iq_setpoint': 9, 'iq_measured': 10}

        # Clean each column separately using the standard deviation method
        cleaned_data = []
        for i, row in enumerate(rows):
            is_outlier = False
            for col_name, col_idx in columns.items():
                col_data = [r[col_idx] for r in rows]
                cleaned_col_data = self.remove_outliers_std(col_data)

                if row[col_idx] not in cleaned_col_data:
                    is_outlier = True
                    break

            if not is_outlier:
                cleaned_data.append(row)

        # Create a new table for cleaned data
        cur.execute(
            '''CREATE TABLE IF NOT EXISTS cleaned_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trial_id INTEGER,
            time REAL,
            pos REAL,
            vel REAL,
            torque_setpoint REAL,
            torque_estimate REAL,
            bus_voltage REAL,
            bus_current REAL,
            iq_setpoint REAL,
            iq_measured REAL,
            FOREIGN KEY (trial_id) REFERENCES trials (trial_id)
            );'''
        )

        # Insert cleaned data into the new table
        cur.executemany(
            "INSERT INTO cleaned_data (trial_id, time, pos, vel, torque_setpoint, torque_estimate, bus_voltage, bus_current, iq_setpoint, iq_measured) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", 
            [(row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9], row[10]) for row in cleaned_data]
        )
        self.conn.commit()

    #no longer using, now using STD to remove outliers
    def identify_outliers(self, data):
        """
        Identifies outliers in a dataset using the IQR method.

        Parameters:
        data (list): The dataset to analyze.

        Returns:
        set: A set of indices of the outliers in the data.
        """
        data_array = np.array(data)
        Q1 = np.percentile(data_array, 45)
        Q3 = np.percentile(data_array, 95)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        outliers = {i for i, x in enumerate(data_array) if x < lower_bound or x > upper_bound}
        return outliers

#------------------------ Delete specific table ----------------------------------
    def delete_table(self, table_name):
            """
            Deletes a table from the database.

            Parameters:
            table_name (str): The name of the table to delete.
            """
            try:
                cur = self.conn.cursor()
                cur.execute(f"DROP TABLE IF EXISTS {table_name}")
                self.conn.commit()
                print(f"Table {table_name} deleted successfully.")
            except Error as e:
                print(f"Error deleting table {table_name}: {e}")

# Example usage:
#db = TorqueReactionTestDatabase("torqueReactionTestDatabase.db")
#db.delete_table("cleaned_data")

#db = TorqueReactionTestDatabase("torqueReactionTestDatabase.db")

#Remove outliers and create new clean data table.
#db.remove_outliers_and_create_clean_table(trial_id=29)