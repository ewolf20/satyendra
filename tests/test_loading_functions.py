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

RESOURCE_DIR_PATH = "resources"


def test_load_experiment_parameters_from_central_folder():
    sample_loaded_dict = loading_functions.load_experiment_parameters_from_central_folder(
        os.path.join(RESOURCE_DIR_PATH, "experiment_parameters_sample.json")
    )
    assert len(sample_loaded_dict) == 0
    true_loaded_dict = loading_functions.load_experiment_parameters_from_central_folder() 
    assert len(true_loaded_dict) == 2 
    assert "Values" in true_loaded_dict 
    assert "Update_Times" in true_loaded_dict



def test_force_refresh_file():
    TEST_FILENAME = "Refresh_Test_File.json"
    test_filepath = os.path.join(RESOURCE_DIR_PATH, TEST_FILENAME)
    EXPECTED_DICT = {"foo":"bar"}
    assert _get_json_contents(test_filepath) == EXPECTED_DICT
    loading_functions.force_refresh_file(test_filepath)
    assert _get_json_contents(test_filepath) == EXPECTED_DICT 
    assert TEST_FILENAME in os.listdir(RESOURCE_DIR_PATH)
    assert len([f for f in os.listdir(RESOURCE_DIR_PATH) if TEST_FILENAME in f]) == 1



def test_file_checkout():
    TEMP_FILE_NAME = "Temp_Checkout_Test.txt"
    temp_file_path = os.path.join(RESOURCE_DIR_PATH, TEMP_FILE_NAME)
    try:
        with open(temp_file_path, 'w') as f:
            f.write("Hello")
        assert TEMP_FILE_NAME in os.listdir(RESOURCE_DIR_PATH)
        with loading_functions.CheckedOutFile(temp_file_path, 'r') as f:
            for line in f:
                assert line == "Hello"
            assert not TEMP_FILE_NAME in os.listdir(RESOURCE_DIR_PATH)
            assert len([f for f in os.listdir(RESOURCE_DIR_PATH) if TEMP_FILE_NAME in f]) == 1
        assert TEMP_FILE_NAME in os.listdir(RESOURCE_DIR_PATH)
    finally:
        os.remove(temp_file_path)

def _get_json_contents(file_path):
    with open(file_path, 'r') as f:
        return json.load(f)



        
