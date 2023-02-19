import datetime 
import hashlib
import json
import os
import shutil
import sys

import matplotlib.pyplot as plt


path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"
sys.path.insert(0, path_to_satyendra)

from satyendra.code import loading_functions


def test_load_experiment_parameters_from_central_folder():
    sample_loaded_dict = loading_functions.load_experiment_parameters_from_central_folder(
        os.path.join("resources", "experiment_parameters_sample.json")
    )
    assert len(sample_loaded_dict) == 2
    assert "Values" in sample_loaded_dict 
    assert "Update_Times" in sample_loaded_dict
    true_loaded_dict = loading_functions.load_experiment_parameters_from_central_folder() 
    assert len(true_loaded_dict) == 2 
    assert "Values" in true_loaded_dict 
    assert "Update_Times" in true_loaded_dict


def test_update_central_experiment_parameters():
    sample_pathname = os.path.join("resources", "experiment_parameters_sample.json")
    sample_temp_pathname = os.path.join("resources", "experiment_parameters_sample_temp.json")
    try:
        shutil.copyfile(sample_pathname, sample_temp_pathname)
        sample_loaded_dict = loading_functions.load_experiment_parameters_from_central_folder(
            pathname = sample_temp_pathname
        )
        assert len(sample_loaded_dict) == 2
        assert len(sample_loaded_dict["Values"]) == 0
        loading_functions.update_central_experiment_parameters("foo", 1, add_var = True, pathname = sample_temp_pathname)
        sample_reloaded_dict = loading_functions.load_experiment_parameters_from_central_folder(
            pathname = sample_temp_pathname
        )
        assert sample_reloaded_dict["Values"]["foo"] == 1 
        try:
            loading_functions.update_central_experiment_parameters("bar", 2, add_var = False, pathname = sample_temp_pathname)
        except ValueError as e:
            pass 
        else:
            assert False
        loading_functions.update_central_experiment_parameters("foo", 2, pathname = sample_temp_pathname) 
        sample_reloaded_dict = loading_functions.load_experiment_parameters_from_central_folder(
            pathname = sample_temp_pathname
        )
        assert sample_reloaded_dict["Values"]["foo"] == 2
    finally:
        os.remove(sample_temp_pathname)



        
