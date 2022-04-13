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

def test_get_runs_dict_from_datetime_range():
    bc = breadboard_functions.load_breadboard_client() 
    CHECKSUM_STRING = 'c9242662be6ca06257a74b2ec024b7cad8fba2efaaea7e3c4b868c99ff066401'
    MIN_DATETIME = datetime.datetime(2022, 4, 6, 9, 56, 19)
    MAX_DATETIME = datetime.datetime(2022, 4, 6, 15, 48, 46)
    results_dict_list = breadboard_functions._get_runs_dict_from_datetime_range(bc, (MIN_DATETIME, MAX_DATETIME))
    assert len(results_dict_list) == 208
    json_bytes = json.dumps(results_dict_list).encode("ASCII")
    assert check_sha_hash(json_bytes, CHECKSUM_STRING)

def test_get_run_ids_from_datetime_range():
    bc = breadboard_functions.load_breadboard_client() 
    START_DATETIME = datetime.datetime(2022, 4, 6, 9, 56, 0)
    END_DATETIME = datetime.datetime(2022, 4, 6, 9, 57, 0)
    TARGET_RUN_IDS_LIST = [805384, 805383]
    run_ids_list = breadboard_functions.get_run_ids_from_datetime_range(bc, START_DATETIME, END_DATETIME) 
    assert TARGET_RUN_IDS_LIST == run_ids_list

def test_label_datetime_list_with_run_ids():
    bc = breadboard_functions.load_breadboard_client()
    DATETIME_1 = datetime.datetime(2022, 4, 6, 9, 56, 19)
    DATETIME_2 = datetime.datetime(2022, 4, 6, 9, 56, 58)
    #Non-contiguous with above two
    DATETIME_3 = datetime.datetime(2022, 4, 6, 15, 48, 46)
    RUN_ID_1 = 805383
    RUN_ID_2 = 805384
    RUN_ID_3 = 805734
    WELL_FORMED_DATETIME_LIST = [DATETIME_1, DATETIME_2]
    TARGET_WELL_FORMED_RESULT = [(DATETIME_1, RUN_ID_1), (DATETIME_2, RUN_ID_2)]
    assert (breadboard_functions.label_datetime_list_with_run_ids(bc, WELL_FORMED_DATETIME_LIST, well_formed = True)
     == TARGET_WELL_FORMED_RESULT)
    WELL_FORMED_DUPLICATED_DATETIME_LIST = [DATETIME_1, DATETIME_2, DATETIME_2, DATETIME_1]
    TARGET_WELL_FORMED_DUPLICATED_RESULT = [(DATETIME_1, RUN_ID_1), (DATETIME_2, RUN_ID_2), (DATETIME_2, RUN_ID_2), (DATETIME_1, RUN_ID_1)]
    assert (breadboard_functions.label_datetime_list_with_run_ids(bc, WELL_FORMED_DUPLICATED_DATETIME_LIST, well_formed = True) ==
     TARGET_WELL_FORMED_DUPLICATED_RESULT)
    NORMAL_DATETIME_LIST = [DATETIME_1, DATETIME_3, DATETIME_2]
    TARGET_NORMAL_RESULT = [(DATETIME_1, RUN_ID_1), (DATETIME_3, RUN_ID_3), (DATETIME_2, RUN_ID_2)]
    assert (breadboard_functions.label_datetime_list_with_run_ids(bc, NORMAL_DATETIME_LIST, well_formed = False) ==
     TARGET_NORMAL_RESULT)
    NORMAL_DUPLICATED_DATETIME_LIST = [DATETIME_1, DATETIME_3, DATETIME_2, DATETIME_3, DATETIME_1]
    TARGET_NORMAL_DUPLICATED_RESULT = [(DATETIME_1, RUN_ID_1), (DATETIME_3, RUN_ID_3), (DATETIME_2, RUN_ID_2), 
                                        (DATETIME_3, RUN_ID_3), (DATETIME_1, RUN_ID_1)]
    assert (breadboard_functions.label_datetime_list_with_run_ids(bc, NORMAL_DUPLICATED_DATETIME_LIST, well_formed = False) ==
     TARGET_NORMAL_DUPLICATED_RESULT)





