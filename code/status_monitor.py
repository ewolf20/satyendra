from collections import OrderedDict
import datetime
import os
import sys
import importlib.resources as pkg_resources
import pandas as pd
import numpy as np

from slack_bot import SlackBot

from .. import logs as l

with pkg_resources.path(l, "__init__.py") as temp_path:
    LOG_DIRECTORY_PATH = temp_path.parent

class StatusMonitor:
    def __init__(self, warning_interval_in_min=10, read_run_time_offset=3, local_log_filename = "DEFAULT.csv"):
        self.last_warning = None
        self.warning_interval_in_min = warning_interval_in_min
        self.read_run_time_offset = read_run_time_offset
        self.local_log_filename = local_log_filename
        self.slack_bot = SlackBot()


    """Logs the data contained in a values_dict locally

    Given a dictionary of values, logs them locally to a .csv file in a form which is loadable by 
    pandas.load_csv.

    Parameters:

        values_dict: A dictionary of values, either of scalar or iterable type. If iterable, all values 
        must be of same length.

        overwrite: If True, the local log is overwritten with only the new values in valuesdict. Otherwise, 
        the values are appended to the end of the existing file.

        reload: If True, and overwrite is False, reloads the existing dataframe in the .csv log file 
        and appends the new dataframe to that. Useful when writing values_dicts which do not all have the 
        same keys, or in which the keys are in different orders. 

    Remarks: 
    
        Because the entire .csv must be reloaded if reload is True, this will become prohibitively 
        slow for large .csv log files. Typical code using this logging should be structured so that 
        reload can be False.

        Will crash if reload is True and the dataframe cannot be loaded. This is intentional.

        Indices will not be saved to the log file in any case. The entries will be in order.
    """

    def log_values_locally(self, values_dict, overwrite = False, reload_df = False):
        log_file_path = LOG_DIRECTORY_PATH / self.local_log_filename
        log_exists = os.path.exists(log_file_path)
        #Do a shallow copy so that the exception handling below doesn't mess with other things
        values_dict = values_dict.copy()
        #Cast scalar dict to dict of length 1 lists
        for key in values_dict:
            try:
                foo = len(values_dict[key]) 
            except TypeError:
                values_dict[key] = [values_dict[key]]
        #Write the current dictionary to a df
        new_df = pd.DataFrame(values_dict)
        if(overwrite):
            new_df.to_csv(log_file_path, mode = 'w', index = False)
        else:
            try:
                if(reload_df and log_exists):
                    existing_df = pd.read_csv(log_file_path)
                    concatenated_df = pd.concat([existing_df, new_df], ignore_index = True)
                    concatenated_df.to_csv(log_file_path, mode = 'w', index = False) 
            except pd.errors.EmptyDataError:
                log_exists = False
            if(log_exists):
                if(not reload_df):
                    new_df.to_csv(log_file_path, mode = 'a', index = False, header = False)
            else:
                new_df.to_csv(log_file_path, mode = 'w', header = True, index = False)




    def warn_on_slack(self, warning_message, mention = [], mention_all = False):
        print(warning_message)
        now = datetime.datetime.now()
        if (self.last_warning is None or
                (now - self.last_warning).seconds / 60 > self.warning_interval_in_min):
            self.slack_bot.post_message(warning_message, mention = mention, mention_all = mention_all)
            self.last_warning = now
        else:
            print('Posted to slack {min} min ago, silenced for now.'.format(
                min=str((now - self.last_warning).seconds / 60)))
