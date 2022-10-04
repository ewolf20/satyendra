import datetime
import json
import hashlib
import os
import sys

path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"
sys.path.insert(0, path_to_satyendra)

from satyendra.code import breadboard_functions


def check_sha_hash(my_bytes, checksum_string):
    m = hashlib.sha256() 
    m.update(my_bytes) 
    return m.hexdigest() == checksum_string

def get_sha_hash_string(my_bytes):
    m = hashlib.sha256() 
    m.update(my_bytes) 
    return m.hexdigest()

def test_load_breadboard_client():
    bc = breadboard_functions.load_breadboard_client() 
    assert True

def test_get_newest_run_dict():
    bc = breadboard_functions.load_breadboard_client() 
    run_dict = breadboard_functions.get_newest_run_dict(bc)
    assert 'run_id' in run_dict

def test_get_run_id_from_datetime():
    bc = breadboard_functions.load_breadboard_client() 
    TARGET_DATETIME = datetime.datetime(2022, 4, 6, 9, 56, 19)
    TARGET_RUN_ID = 805383
    assert TARGET_RUN_ID == breadboard_functions.get_run_id_from_datetime(bc, TARGET_DATETIME)

def test_get_results_dict_list_from_datetime_range():
    bc = breadboard_functions.load_breadboard_client() 
    CHECKSUM_STRING = 'c9242662be6ca06257a74b2ec024b7cad8fba2efaaea7e3c4b868c99ff066401'
    MIN_DATETIME = datetime.datetime(2022, 4, 6, 9, 56, 19)
    MAX_DATETIME = datetime.datetime(2022, 4, 6, 15, 48, 46)
    results_dict_list = breadboard_functions._get_results_dict_list_from_datetime_range(bc, (MIN_DATETIME, MAX_DATETIME))
    assert len(results_dict_list) == 208
    json_bytes = json.dumps(results_dict_list).encode("ASCII")
    assert check_sha_hash(json_bytes, CHECKSUM_STRING)


def get_run_parameter_dicts_from_datetimes():
    bc = breadboard_functions.load_breadboard_client()
    DATETIME_1 = datetime.datetime(2022, 4, 6, 9, 56, 19)
    DATETIME_2 = datetime.datetime(2022, 4, 6, 9, 56, 58)
    #Non-contiguous with above two
    DATETIME_3 = datetime.datetime(2022, 4, 6, 15, 48, 46)
    RUN_ID_1 = 805383
    RUN_ID_2 = 805384
    RUN_ID_3 = 805734
    DATETIME_LIST = [DATETIME_1, DATETIME_3, DATETIME_2]
    TARGET_ID_RESULT = [RUN_ID_1, RUN_ID_3, RUN_ID_2]
    datetime_and_parameters_list = breadboard_functions.get_run_parameter_dicts_from_datetimes(bc, DATETIME_LIST)
    run_id_list = [x[1]['id'] for x in datetime_and_parameters_list]
    assert run_id_list == TARGET_ID_RESULT
    DUPLICATED_DATETIME_LIST = [DATETIME_1, DATETIME_3, DATETIME_2, DATETIME_3, DATETIME_1]
    TARGET_DUPLICATED_ID_RESULT = [RUN_ID_1, RUN_ID_3, RUN_ID_2, RUN_ID_3, RUN_ID_1]
    duplicated_datetime_and_parameters_list = breadboard_functions.get_run_parameter_dicts_from_datetimes(bc, DUPLICATED_DATETIME_LIST)
    duplicated_run_id_list = [x[1]['id'] for x in duplicated_datetime_and_parameters_list]
    assert duplicated_run_id_list == TARGET_DUPLICATED_ID_RESULT


def test_get_datetime_from_run_id():
    bc = breadboard_functions.load_breadboard_client() 
    TEST_RUN_ID = 805306
    TEST_DATETIME = datetime.datetime(2022, 4, 6, 8, 57, 35) 
    assert TEST_DATETIME == breadboard_functions.get_datetime_from_run_id(bc, TEST_RUN_ID) 


def test_get_run_parameter_dicts_from_ids():
    bc = breadboard_functions.load_breadboard_client() 
    RUN_IDS_LIST = [805383, 805384, 805734]
    START_DATETIME = datetime.datetime(2022, 4, 6, 9, 56, 19) 
    END_DATETIME = datetime.datetime(2022, 4, 6, 15, 48, 46)
    VERBOSE_SHA_CHECKSUM = 'b26a4a14c5e43c48856bda7f89fb973fa7ac126a37dd674eef5d7d5e2e210d3d'
    SHA_CHECKSUM = '270f085a08e6713c06a5eaad679cf8fa7f28f8ec61431c8d637b5be58c871457'
    verbose_dicts_list = breadboard_functions.get_run_parameter_dicts_from_ids(bc, RUN_IDS_LIST, verbose = True) 
    dicts_list = breadboard_functions.get_run_parameter_dicts_from_ids(bc, RUN_IDS_LIST, verbose = False) 
    dicts_list_specify_times = breadboard_functions.get_run_parameter_dicts_from_ids(bc, RUN_IDS_LIST, start_datetime = START_DATETIME,
                                                                            end_datetime = END_DATETIME)
    verbose_dicts_bytes = json.dumps(verbose_dicts_list).encode("ASCII")
    dicts_bytes = json.dumps(dicts_list).encode("ASCII")
    dicts_specify_times_bytes = json.dumps(dicts_list_specify_times).encode("ASCII")
    assert check_sha_hash(verbose_dicts_bytes, VERBOSE_SHA_CHECKSUM)
    assert check_sha_hash(dicts_bytes, SHA_CHECKSUM)
    assert check_sha_hash(dicts_specify_times_bytes, SHA_CHECKSUM)


def test_get_run_parameter_dict_from_id():
    bc = breadboard_functions.load_breadboard_client()
    RUN_ID = 805383
    VERBOSE_SHA_CHECKSUM = 'c31f9362e4bf931f780e22682738e05ea93b25150e457267b0f353b3a492100b'
    TACIT_SHA_CHECKSUM = '24daa69f8dd0bfc121061500c9beac25a13c1697ea57c79228e7b28cf6182683'
    verbose_dict = breadboard_functions.get_run_parameter_dict_from_id(bc, RUN_ID, verbose = True)
    tacit_dict = breadboard_functions.get_run_parameter_dict_from_id(bc, RUN_ID, verbose = False)
    verbose_bytes = json.dumps(verbose_dict).encode("ASCII") 
    tacit_dict_bytes = json.dumps(tacit_dict).encode("ASCII")
    assert check_sha_hash(verbose_bytes, VERBOSE_SHA_CHECKSUM)
    assert check_sha_hash(tacit_dict_bytes, TACIT_SHA_CHECKSUM)






