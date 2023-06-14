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
        pathname = os.path.join(RESOURCE_DIR_PATH, "experiment_parameters_sample.json")
    )
    assert len(sample_loaded_dict) == 2
    assert "Values" in sample_loaded_dict 
    assert "Update_Times" in sample_loaded_dict
    assert sample_loaded_dict["Values"]["foo"] == 0
    true_loaded_dict = loading_functions.load_experiment_parameters_from_central_folder() 
    assert len(true_loaded_dict) == 2 
    assert "Values" in true_loaded_dict 
    assert "Update_Times" in true_loaded_dict


def test_update_central_experiment_parameters():
    sample_parameters_pathname = os.path.join(RESOURCE_DIR_PATH, "experiment_parameters_sample.json")
    sample_parameters_pathname_test_temp = sample_parameters_pathname + "TEST_TEMP" 
    shutil.copy2(sample_parameters_pathname, sample_parameters_pathname_test_temp)
    try:
        loading_functions.update_central_experiment_parameters("bar", 1337, pathname = sample_parameters_pathname)
        assert not sample_parameters_pathname + "TEMP" in os.listdir(RESOURCE_DIR_PATH)
        loaded_dict = loading_functions.load_experiment_parameters_from_central_folder(pathname = sample_parameters_pathname)
        assert loaded_dict["Values"]["bar"] == 1337
    finally:
        os.replace(sample_parameters_pathname_test_temp, sample_parameters_pathname)



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


def test_retroactive_update_existing_experiment_parameters():
    try:
        TEMP_ROOT_FOLDER_NAME = "temp"
        EPOCH_STRING = "1970-01-01--00-00-00"
        root_pathname = os.path.join(RESOURCE_DIR_PATH, TEMP_ROOT_FOLDER_NAME)
        #Plain vanilla invocation of new parameter
        experiment_parameters_pathnames_list = _retroactive_update_spoof_directory_tree_helper(TEMP_ROOT_FOLDER_NAME)
        loading_functions.retroactive_update_existing_experiment_parameters(root_pathname, "bar", 2)
        for experiment_parameters_pathname in experiment_parameters_pathnames_list:
            values_dict, updates_dict = _retroactive_update_load_json_helper(experiment_parameters_pathname)
            assert "bar" in values_dict 
            assert values_dict["bar"] == 2
            assert "foo" in values_dict 
            assert values_dict["foo"] == 1
            assert "bar" in updates_dict 
            assert updates_dict["bar"] != EPOCH_STRING
            assert updates_dict["foo"] == EPOCH_STRING
        shutil.rmtree(root_pathname)
        #Invocation with replacement of parameter with saving previous
        experiment_parameters_pathnames_list = _retroactive_update_spoof_directory_tree_helper(TEMP_ROOT_FOLDER_NAME)
        loading_functions.retroactive_update_existing_experiment_parameters(root_pathname, "foo", 2, save_previous = True)
        for experiment_parameters_pathname in experiment_parameters_pathnames_list:
            values_dict, updates_dict = _retroactive_update_load_json_helper(experiment_parameters_pathname) 
            assert len(values_dict) == 2 
            assert "foo" in values_dict 
            assert values_dict["foo"] == 2 
            previous_key = [key for key in values_dict if "_Previous_Replaced_On" in key][0]
            assert values_dict[previous_key] == 1 
            assert "foo" in updates_dict 
            assert updates_dict["foo"] != EPOCH_STRING
            assert updates_dict[previous_key] == EPOCH_STRING
        shutil.rmtree(root_pathname)
        #Invocation with replacement of parameter without saving previous
        experiment_parameters_pathnames_list = _retroactive_update_spoof_directory_tree_helper(TEMP_ROOT_FOLDER_NAME)
        loading_functions.retroactive_update_existing_experiment_parameters(root_pathname, "foo", 2, save_previous = False)
        for experiment_parameters_pathname in experiment_parameters_pathnames_list: 
            values_dict, updates_dict = _retroactive_update_load_json_helper(experiment_parameters_pathname) 
            assert len(values_dict) == 1
            assert "foo" in values_dict 
            assert values_dict["foo"] == 2 
            assert len(updates_dict) == 1 
            assert "foo" in updates_dict 
            assert updates_dict["foo"] != EPOCH_STRING
        shutil.rmtree(root_pathname)
        #Invocation specifying by date range, without saving previous
        experiment_parameters_pathnames_list = _retroactive_update_spoof_directory_tree_helper(TEMP_ROOT_FOLDER_NAME)
        date_range_list = [datetime.datetime(1970, 1, 2), datetime.datetime(1970, 1, 2)]
        loading_functions.retroactive_update_existing_experiment_parameters(root_pathname, "foo", 2, save_previous = False, 
                                                        date_range = date_range_list)
        for experiment_parameters_pathname in experiment_parameters_pathnames_list:
            values_dict, updates_dict = _retroactive_update_load_json_helper(experiment_parameters_pathname) 
            if "1970-01-01" in experiment_parameters_pathname:
                assert values_dict["foo"] == 1
            else:
                assert values_dict["foo"] == 2
        shutil.rmtree(root_pathname)
        #Invocation specifying by folder name
        experiment_parameters_pathnames_list = _retroactive_update_spoof_directory_tree_helper(TEMP_ROOT_FOLDER_NAME) 
        directory_spec_list = ["hello"] 
        loading_functions.retroactive_update_existing_experiment_parameters(root_pathname, "foo", 2, save_previous = False, 
                                                                    directory_spec_list = directory_spec_list)
        for experiment_parameters_pathname in experiment_parameters_pathnames_list:
            values_dict, updates_dict = _retroactive_update_load_json_helper(experiment_parameters_pathname)
            if "hello" in experiment_parameters_pathname:
                assert values_dict["foo"] == 2
            else:
                assert values_dict["foo"] == 1
    finally:
        if os.path.exists(root_pathname):
            shutil.rmtree(root_pathname)

def test_retroactive_update_experiment_parameters_cleanup():
    TEMP_ROOT_FOLDER_NAME = "temp"
    EPOCH_STRING = "1970-01-01--00-00-00"
    root_pathname = os.path.join(RESOURCE_DIR_PATH, TEMP_ROOT_FOLDER_NAME)
    try:
        #Cleanup specced by directory
        experiment_parameters_pathnames_list = _retroactive_update_spoof_directory_tree_helper(TEMP_ROOT_FOLDER_NAME) 
        directory_spec_list = ["hello"]
        loading_functions.retroactive_update_existing_experiment_parameters(root_pathname, "foo", 2, save_previous = True, 
                                                                directory_spec_list = directory_spec_list)
        for experiment_parameters_pathname in experiment_parameters_pathnames_list:
            values_dict, updates_dict = _retroactive_update_load_json_helper(experiment_parameters_pathname)
            if "hello" in experiment_parameters_pathname:
                assert values_dict["foo"] == 2
                assert len(values_dict) == 2
            else:
                assert values_dict["foo"] == 1
                assert len(values_dict) == 1
        loading_functions.retroactive_update_existing_experiment_parameters_cleanup(root_pathname, directory_spec_list = directory_spec_list)
        for experiment_parameters_pathname in experiment_parameters_pathnames_list:
            values_dict, updates_dict = _retroactive_update_load_json_helper(experiment_parameters_pathname)
            if "hello" in experiment_parameters_pathname:
                assert values_dict["foo"] == 2 
            else:
                assert values_dict["foo"] == 1
            assert len(values_dict) == 1
        shutil.rmtree(root_pathname)
        #Cleanup specced by date 
        experiment_parameters_pathnames_list = _retroactive_update_spoof_directory_tree_helper(TEMP_ROOT_FOLDER_NAME)
        date_range_list = [datetime.datetime(1970, 1, 2), datetime.datetime(1970, 1, 2)]
        loading_functions.retroactive_update_existing_experiment_parameters(root_pathname, "foo", 2, save_previous = True, 
                                                        date_range = date_range_list)
        for experiment_parameters_pathname in experiment_parameters_pathnames_list:
            values_dict, updates_dict = _retroactive_update_load_json_helper(experiment_parameters_pathname) 
            if "1970-01-01" in experiment_parameters_pathname:
                assert values_dict["foo"] == 1
                assert len(values_dict) == 1
            else:
                assert values_dict["foo"] == 2
                assert len(values_dict) == 2
        loading_functions.retroactive_update_existing_experiment_parameters_cleanup(root_pathname, date_range = date_range_list)
        for experiment_parameters_pathname in experiment_parameters_pathnames_list:
            values_dict, updates_dict = _retroactive_update_load_json_helper(experiment_parameters_pathname) 
            if "1970-01-01" in experiment_parameters_pathname:
                assert values_dict["foo"] == 1
            else:
                assert values_dict["foo"] == 2
            assert len(values_dict) == 1
    finally:
        if os.path.exists(root_pathname):
            shutil.rmtree(root_pathname)

def _retroactive_update_spoof_directory_tree_helper(temp_root_folder_name):
    MONTH_FOLDER_NAME = "1970-01"
    YEAR_FOLDER_NAME = "1970"
    DATE_FOLDER_1_NAME = "1970-01-01"
    DATE_FOLDER_2_NAME = "1970-01-02"
    DATA_FOLDER_1_NAME = "hello"
    DATA_FOLDER_2_NAME = "dolly"
    EPOCH_STRING = "1970-01-01--00-00-00"
    DUMMY_EXPERIMENT_PARAMETERS_JSON = {"Values":{"foo":1}, "Update_Times":{"foo":"1970-01-01--00-00-00"}}
    data_folder_list = [DATA_FOLDER_1_NAME, DATA_FOLDER_2_NAME]
    date_folder_list = [DATE_FOLDER_1_NAME, DATE_FOLDER_2_NAME]
    root_pathname = os.path.join(RESOURCE_DIR_PATH, temp_root_folder_name)
    experiment_parameters_pathnames_list = []
    for date_folder_name in date_folder_list:
        for data_folder_name in data_folder_list:
            full_date_folder_tree_name = os.path.join(YEAR_FOLDER_NAME, MONTH_FOLDER_NAME, date_folder_name)
            data_folder_pathname = os.path.join(root_pathname, full_date_folder_tree_name, data_folder_name)
            experiment_parameters_pathname = os.path.join(data_folder_pathname, "experiment_parameters.json")
            os.makedirs(data_folder_pathname)
            with open(experiment_parameters_pathname, 'w') as json_file:
                json.dump(DUMMY_EXPERIMENT_PARAMETERS_JSON, json_file)
            experiment_parameters_pathnames_list.append(experiment_parameters_pathname)
    return experiment_parameters_pathnames_list

def _retroactive_update_load_json_helper(experiment_parameters_pathname):
    with open(experiment_parameters_pathname, 'r') as json_file:
        parameters_dict = json.load(json_file) 
    values_dict = parameters_dict["Values"]
    updates_dict = parameters_dict["Update_Times"]
    return (values_dict, updates_dict)




        
