import importlib.resources as pkg_resources
import json
import os

from .. import configs as c


def load_experiment_parameters_from_central_folder(pathname = None):
    if pathname is None:
        IMAGE_SAVER_CONFIG_FILENAME = "image_saver_config_local.json"
        with pkg_resources.path(c, IMAGE_SAVER_CONFIG_FILENAME) as config_path:
            with open(config_path, 'r') as config_file:
                config_dict = json.load(config_file) 
                pathname = config_dict["experiment_parameters_pathname"]
    with open(pathname, 'r') as experiment_parameters_file:
        return json.load(experiment_parameters_file)