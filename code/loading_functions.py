import datetime
import hashlib
import importlib.resources as pkg_resources
import json
import os
import random
import shutil
import subprocess
import sys
import time

from .. import configs as c
from . import image_watchdog


CENTRAL_PARAMETERS_DATETIME_FORMAT_STRING = "%Y-%m-%d--%H-%M-%S"


def _get_central_experiment_parameters_pathname():
    IMAGE_SAVER_CONFIG_FILENAME = "image_saver_config_local.json"
    with pkg_resources.path(c, IMAGE_SAVER_CONFIG_FILENAME) as config_path:
        with open(config_path, 'r') as config_file:
            config_dict = json.load(config_file) 
            pathname = config_dict["experiment_parameters_pathname"]
            return pathname

def load_experiment_parameters_from_central_folder(pathname = None):
    if pathname is None:
        pathname = _get_central_experiment_parameters_pathname()
    with open(pathname, 'r') as experiment_parameters_file:
        return json.load(experiment_parameters_file)

def load_guppy_camera_parameters_json():
    GUPPY_CAMERA_CONFIG_FILENAME = "guppy_camera_config_local.json"
    with pkg_resources.path(c, GUPPY_CAMERA_CONFIG_FILENAME) as config_path:
        with open(config_path, 'r') as config_file:
            return json.load(config_file)

def update_central_experiment_parameters(key, value, pathname = None):
    if pathname is None:
        pathname = _get_central_experiment_parameters_pathname()
    with open(pathname, 'r') as experiment_parameters_file:
        parameters_dict = json.load(experiment_parameters_file)
    parameters_dict_values = parameters_dict["Values"] 
    parameters_dict_update_times = parameters_dict["Update_Times"]
    parameters_dict_values[key] = value 
    current_datetime = datetime.datetime.now() 
    current_datetime_string = current_datetime.strftime(CENTRAL_PARAMETERS_DATETIME_FORMAT_STRING)
    parameters_dict_update_times[key] = current_datetime_string 
    #Create a temporary copy just in case something breaks in the load/write 
    temp_pathname = pathname + "TEMP"
    shutil.copy2(pathname, temp_pathname)
    with open(pathname, 'w') as experiment_parameters_file:
        json.dump(parameters_dict, experiment_parameters_file)
    #Get rid of the temp
    os.remove(temp_pathname)



"""
Convenience function for retroactively changing the experiment parameters in old datasets.

Given a root folder, recursively search for subdirectories containing an experiment_parameters.json file. 
When found, update this file to contain the specified key-value pair.

WARNING: This function is capable of IRREVERSIBLY DESTROYING CRUCIAL INFORMATION. It is recommended to follow 
all possible precautions, including:
    *   Running with save_previous equal to True, then calling the below cleanup function after inspecting results.
    *   Passing the lowest-possible root folder pathname that contains the runs of interest.
    *   Wherever practical, explicitly specifying the directories to be updated rather than relying on date_range.
    
Parameters:

root_folder_pathname: The root folder to be recursively searched for matching folders.

key, value: The key-value pair to be added to the dict.

save_previous: If True, then if key already exists in the dict, the previously-existing value will be saved under a 
    modified key name, allowing reversion of changes if necessary.
    
date_range: A list [min_datetime, max_datetime]. If passed, then only directories which have a parent folder
whose name is parsable as a date lying between the specified datetimes, inclusive, will have their experiment parameters modified.

directory_spec_list: A list of strings. If passed, then only directories whose names appear in directory_spec_list (note: these 
are base names) will be modified. 

If both date_range and directory_spec_list are passed, then the intersection of their domains is used.
    """

RETROACTIVE_UPDATE_PREVIOUS_REPLACED_STRING = "Previous_Replaced_On"
def retroactive_update_existing_experiment_parameters(root_folder_pathname, key, value, save_previous = True, 
                                                date_range = None, directory_spec_list = None):
    pathname_to_modify_list = _retroactive_update_directory_finder_helper(root_folder_pathname, date_range = date_range, 
                                        directory_spec_list = directory_spec_list)
    for pathname_to_modify in pathname_to_modify_list:
        experiment_parameters_path = os.path.join(pathname_to_modify, "experiment_parameters.json")
        with open(experiment_parameters_path, 'r') as json_file:
            existing_dict = json.load(json_file)
        existing_dict_values = existing_dict["Values"]
        existing_dict_update_times = existing_dict["Update_Times"]
        current_datetime = datetime.datetime.now()
        if key in existing_dict_values and save_previous:
            previous_key = "{0}_{1}_{2}".format(key, RETROACTIVE_UPDATE_PREVIOUS_REPLACED_STRING,
                                 current_datetime.strftime(CENTRAL_PARAMETERS_DATETIME_FORMAT_STRING))
            existing_dict_values[previous_key] = existing_dict_values[key] 
            existing_dict_update_times[previous_key] = existing_dict_update_times[key]
        existing_dict_values[key] = value 
        existing_dict_update_times[key] = current_datetime.strftime(CENTRAL_PARAMETERS_DATETIME_FORMAT_STRING)
        #Temporarily copy the file in case something goes wrong
        temp_experiment_parameters_path = experiment_parameters_path + "TEMP"
        shutil.copy2(experiment_parameters_path, temp_experiment_parameters_path)
        with open(experiment_parameters_path, 'w') as json_file:
            json.dump(existing_dict, json_file)
        os.remove(temp_experiment_parameters_path)


"""
Convenience function which removes the previous entries stored by the above when save_previous is true.

WARNING: Any deletions done by this function are COMPLETELY IRREVOCABLE at the level of this code. Be cautious. """
def retroactive_update_existing_experiment_parameters_cleanup(root_folder_pathname, date_range = None, directory_spec_list = None):
    pathname_to_modify_list = _retroactive_update_directory_finder_helper(root_folder_pathname, date_range = date_range, 
                                                                directory_spec_list = directory_spec_list)
    for pathname_to_modify in pathname_to_modify_list:
        experiment_parameters_path = os.path.join(pathname_to_modify, "experiment_parameters.json")
        with open(experiment_parameters_path, 'r') as json_file:
            existing_dict = json.load(json_file) 
        existing_dict_values = existing_dict["Values"] 
        existing_dict_update_times = existing_dict["Update_Times"]
        keys_to_pop = [key for key in existing_dict_values if RETROACTIVE_UPDATE_PREVIOUS_REPLACED_STRING in key]
        for key in keys_to_pop:
            existing_dict_values.pop(key) 
            existing_dict_update_times.pop(key)
        temp_experiment_parameters_path = experiment_parameters_path + "TEMP" 
        shutil.copy2(experiment_parameters_path, temp_experiment_parameters_path)
        with open(experiment_parameters_path, 'w') as json_file:
            json.dump(existing_dict, json_file)
        os.remove(temp_experiment_parameters_path)

def _retroactive_update_directory_finder_helper(root_folder_pathname, date_range = None, directory_spec_list = None):
    pathname_to_modify_list = []
    for dirpath, dirnames, filenames in os.walk(root_folder_pathname):
        if "experiment_parameters.json" in filenames:
            if not directory_spec_list is None and not os.path.basename(dirpath) in directory_spec_list:
                continue
            if not date_range is None:
                range_min, range_max = date_range
                dir_parent_datetime = _get_folder_parent_date_helper(root_folder_pathname, dirpath)
                if dir_parent_datetime is None or (dir_parent_datetime < range_min or dir_parent_datetime > range_max):
                    continue 
            pathname_to_modify_list.append(dirpath)
    return pathname_to_modify_list

def _get_folder_parent_date_helper(root_folder_pathname, dirpath):
    RUN_FOLDER_NAME_DATETIME_FORMAT_STRING = "%Y-%m-%d"
    current_dir_path = dirpath
    parent_date = None
    while parent_date is None and not current_dir_path == root_folder_pathname:
        current_dir_name = os.path.basename(current_dir_path)
        try:
            parent_datetime = datetime.datetime.strptime(current_dir_name, RUN_FOLDER_NAME_DATETIME_FORMAT_STRING)
        except ValueError:
            current_dir_path = os.path.abspath(os.path.join(current_dir_path, os.path.pardir)) 
        else:
            return parent_datetime
    return None



def force_refresh_file(file_pathname, patience = 3, sleep_time = 0.1):
    ERRORS_TO_CATCH = (FileNotFoundError, OSError)
    counter = 0
    while True:
        try:
            _twiddle_file(file_pathname) 
            break
        except ERRORS_TO_CATCH as e:
            counter += 1
            if counter < patience:
                time.sleep(sleep_time) 
            else:
                raise e



def _twiddle_file(file_pathname):
    #Black magic to open a file with a "legitimate" program that forces a refresh of its contents from the remote
    if sys.platform.startswith("win32"):
        WINDOWS_OPEN_TIMEOUT = 0.1
        try:
            subprocess.run(["notepad", file_pathname], timeout = WINDOWS_OPEN_TIMEOUT)
        except subprocess.TimeoutExpired:
            pass
    elif sys.platform.startswith("darwin"):
        subprocess.run(["open", "-a", "TextEdit", file_pathname])
        subprocess.run(["killall", "TextEdit"])
    else:
        raise NotImplementedError("File refreshing not yet implemented for non-windows or Mac platforms.")


def update_json_file(file_pathname, update_dict, patience = 3, wait_time = 0.1):
    ERRORS_TO_CATCH = (FileNotFoundError, OSError)
    counter = 0
    while True:
        try:
            with open(file_pathname, 'r+') as f:
                initial_dict = json.load(f) 
                f.seek(0) 
                appended_dict = initial_dict 
                for key in update_dict:
                    appended_dict[key] = update_dict[key] 
                json.dump(appended_dict, f)
                f.truncate()
            break 
        except ERRORS_TO_CATCH as e:
            counter += 1 
            if counter < patience:
                time.sleep(wait_time)
            else:
                raise e

class CheckedOutFile(object):
    def __init__(self, file_path, method, checkout_patience = 3, wait_time = 0.1, 
                checkout_appendix = None, checkin_fail_policy = "raise"):
        self.file_path = file_path 
        self.method = method
        self.checkout_patience = checkout_patience 
        self.wait_time = wait_time
        file_obj, checkout_pathname = self.checkout_file(checkout_appendix)
        self.file_obj = file_obj 
        self.checkout_pathname = checkout_pathname
        self.checkin_fail_policy = checkin_fail_policy

    def __enter__(self):
        return self.file_obj 

    def __exit__(self, type, value, traceback):
        self.checkin_file()
        
    def checkout_file(self, checkout_appendix = None):
        if checkout_appendix is None:
            checkout_appendix = CheckedOutFile.generate_unique_checkout_appendix() 
        checked_out_file_path = self.file_path + checkout_appendix
        counter = 0
        while True:
            try:
                os.rename(self.file_path, checked_out_file_path)
            except OSError as e:
                if counter < self.checkout_patience:
                    counter += 1 
                    time.sleep(self.wait_time)
                else:
                    raise e 
            else:
                file_obj = open(checked_out_file_path, self.method) 
                return (file_obj, checked_out_file_path)

    def checkin_file(self):
        self.file_obj.close()
        try:
            os.rename(self.checkout_pathname, self.file_path)
        except FileExistsError as e:
            if self.checkin_fail_policy == "raise":
                raise e 
            elif self.checkin_fail_policy == "discard":
                os.remove(self.checkout_pathname)
            elif self.checkin_fail_policy == "replace":
                os.replace(self.checkout_pathname, self.file_path)
            else:
                raise e


    #Best-effort approach to ensure no collisions in checkout appendix;
    #relies on platform randomness
    @staticmethod 
    def generate_unique_checkout_appendix():
        h = hashlib.sha1()
        random_bytes = random.randbytes(256)
        h.update(random_bytes)
        return h.hexdigest()