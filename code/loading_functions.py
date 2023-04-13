import datetime
import hashlib
import importlib.resources as pkg_resources
import json
import os
import random
import shutil
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




def force_refresh_file(file_pathname):
    #Checking the file out is actually enough to force refresh
    with CheckedOutFile(file_pathname, 'r', checkin_fail_policy = "discard") as f:
        pass


def update_json_file(file_pathname, update_dict, checkin_fail_policy = "raise"):
    with CheckedOutFile(file_pathname, 'r+', checkin_fail_policy = checkin_fail_policy) as f:
        initial_dict = json.load(f) 
        f.seek(0) 
        appended_dict = initial_dict 
        for key in update_dict:
            appended_dict[key] = update_dict[key] 
        json.dump(appended_dict, f)
        f.truncate()

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
        while counter < self.checkout_patience:
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



