import datetime
import importlib.resources as pkg_resources
import json
import os

from .. import configs as c


CENTRAL_EXPERIMENT_PARAMETERS_DATETIME_FORMAT_STRING = "%Y-%m-%d--%H-%M-%S"

def _get_central_experiment_parameters_pathname_from_config():
    IMAGE_SAVER_CONFIG_FILENAME = "image_saver_config_local.json"
    with pkg_resources.path(c, IMAGE_SAVER_CONFIG_FILENAME) as config_path:
        with open(config_path, 'r') as config_file:
            config_dict = json.load(config_file) 
            pathname = config_dict["experiment_parameters_pathname"]
    return pathname

def load_experiment_parameters_from_central_folder(pathname = None):
    if pathname is None:
        pathname = _get_central_experiment_parameters_pathname_from_config()
    with open(pathname, 'r') as experiment_parameters_file:
        return json.load(experiment_parameters_file)



def update_central_experiment_parameters(varname, val, add_var = False, pathname = None):
    if pathname is None:
        pathname = _get_central_experiment_parameters_pathname_from_config()
    experiment_parameters_dict = load_experiment_parameters_from_central_folder(pathname = pathname)
    experiment_parameters_values = experiment_parameters_dict["Values"]
    experiment_parameters_update_times = experiment_parameters_dict["Update_Times"]
    if add_var or varname in experiment_parameters_values:
        experiment_parameters_values[varname] = val
        current_datetime = datetime.datetime.now()
        datetime_string = current_datetime.strftime(CENTRAL_EXPERIMENT_PARAMETERS_DATETIME_FORMAT_STRING)
        experiment_parameters_update_times[varname] = datetime_string
        with open(pathname, 'w') as experiment_parameters_file:
            json.dump(experiment_parameters_dict, experiment_parameters_file)
    else:
        raise ValueError("The stipulated varname is not in the experiment parameters. Pass add_var=True to add new variables.")