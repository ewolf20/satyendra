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
    assert len(sample_loaded_dict) == 0
    true_loaded_dict = loading_functions.load_experiment_parameters_from_central_folder() 
    assert len(true_loaded_dict) == 2 
    assert "Values" in true_loaded_dict 
    assert "Update_Times" in true_loaded_dict



        
