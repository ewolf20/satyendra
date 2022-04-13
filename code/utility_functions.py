import datetime
import time 

BREADBOARD_DATETIME_FORMAT_STRING = "%Y-%m-%dT%H:%M:%SZ"

def load_breadboard_client():
    import json 
    import sys
    import importlib.resources as pkg_resources
    from .. import configs as c 
    from .. import secrets as s
    with pkg_resources.path(c, "breadboard_path_config_local.json") as breadboard_config_path, pkg_resources.path(s, "breadboard_api_secret.json") as API_key_path:
        with open(breadboard_config_path) as breadboard_config_file:
            breadboard_config_dict = json.load(breadboard_config_file)
            breadboard_repo_path = breadboard_config_dict.get("breadboard_repo_path") 
            if(breadboard_repo_path is None):
                raise KeyError("The .json config does not contain variable breadboard_repo_path")
            sys.path.insert(0, breadboard_repo_path) 
            from breadboard import BreadboardClient
            bc = BreadboardClient(API_key_path)
    return bc


def _query_breadboard_with_retries(bc, method, endpoint, params = None, data = None, max_attempts = 5, delay_time = 0.2):
    import time 
    from json import JSONDecodeError 
    attempts = 0
    while(attempts < max_attempts):
        attempts += 1 
        try:
            response = bc._send_message(method, endpoint, params = params, data = data)
            if(response.status_code == 200):
                _ = response.json()
                return response
            time.sleep(delay_time)
        except JSONDecodeError:
            time.sleep(delay_time) 
    raise RuntimeError("Could not obtain response within specified number of tries")


def get_newest_run_dict(bc, max_attempts = 5, delay_time = 0.2):
    method = 'get'
    endpoint = '/runs/'
    params = {'lab':'bec1', 'limit':1}
    response = _query_breadboard_with_retries(bc, method, endpoint, params = params)
    run_dict = response.json()['results'][0]
    cleaned_run_dict = {'runtime':run_dict['runtime'], 'run_id':run_dict['id'], **run_dict['parameters']}
    return cleaned_run_dict 


"""
Gets breadboard run id from datetime

Utility function which, given a datetime object representing a target time, queries breadboard 
for the run id corresponding to that time.


Parameters:

bc: The breadboard client
Target datetime: The datetime of the run whose id is to be found.

allowed_seconds_before: The number of seconds before the given datetime during which a timestamp for a run id can be considered a match
allowed_seconds_after: Ditto, but after. 

Remark: Requires ~3s to look up a value, probably because of 
"""
def get_run_id_from_datetime(bc, target_datetime, allowed_seconds_before = 5, allowed_seconds_after = 5):
    datetime_range_start = target_datetime - datetime.timedelta(seconds = allowed_seconds_before) 
    datetime_range_end = target_datetime + datetime.timedelta(seconds = allowed_seconds_after)
    response = get_runs(bc, [datetime_range_start, datetime_range_end])
    runs_list = response.json().get('results')
    if(len(runs_list) == 0):
            raise RuntimeError("Unable to find run_id with specified runtime") 
    elif(len(runs_list) > 1):
        raise RuntimeError("Found multiple run_ids within specified time window.") 
    else:
        run_dict = runs_list[0] 
        return run_dict['id']

def get_run_ids_from_datetime_range(bc, start_datetime, end_datetime, allowed_seconds_deviation = 5):
    datetime_range_start = start_datetime - datetime.timedelta(seconds = allowed_seconds_deviation)
    datetime_range_end = end_datetime + datetime.timedelta(seconds = allowed_seconds_deviation)
    response = get_runs(bc, (datetime_range_start, datetime_range_end))
    response_dict_list = response.json().get('results') 
    runs_list = [d['id'] for d in response_dict_list]
    return runs_list


#TODO: Add support for non-contiguous datetime ranges; just a search in the returned run id dictionary.
"""
Labels a list of datetimes with corresponding run_ids.

Given input [datetime1, datetime2, ...], returns a list of tuples [(datetime1, runID1), (datetime2, runID2), ...].
Note that the datetimes are datetime objects, and the runID is returned as an int.

If contiguous = True, speeds up by sorting datetimes rather than matching brute force. With this flag, 
function will break if either a) run ids are not returned by get_run_ids_from_datetime_range monotonically, or b) the 
given datetime list has ''holes''. 
"""
def label_datetime_list_with_run_ids(bc, datetime_list, allowed_seconds_deviation = 5, contiguous = True):
    min_datetime = min(datetime_list) 
    max_datetime = max(datetime_list)
    if(contiguous):
        run_ids_descending_order = get_run_ids_from_datetime_range(bc, min_datetime, max_datetime, allowed_seconds_deviation= allowed_seconds_deviation)
        if(len(datetime_list) % len(run_ids_descending_order) != 0):
            raise RuntimeError("Did not receive the correct number of run ids for the given datetime range.")
        datetimes_per_run_id = len(datetime_list) // len(run_ids_descending_order) 
        tagged_datetimes_list = list(enumerate(datetimes_per_run_id)) 
        descending_tagged_datetimes_list = sorted(tagged_datetimes_list, key = lambda f: f[1], reverse = True)
        run_id_labeled_tagged_datetimes_list = [] 
        for i, tag_datetime_tuple in enumerate(descending_tagged_datetimes_list):
            tag, current_datetime = tag_datetime_tuple 
            run_id = run_ids_descending_order[i // datetimes_per_run_id]
            run_id_labeled_tagged_datetimes_list.append((tag, (current_datetime, run_id)))
        original_order_datetime_run_id_list = [f[1] for f in sorted(run_id_labeled_tagged_datetimes_list, key = lambda f: f[0])]
        return original_order_datetime_run_id_list
    else:
        lower_limit_datetime = min_datetime - datetime.timedelta(seconds = allowed_seconds_deviation) 
        upper_limit_datetime = max_datetime + datetime.timedelta(seconds = allowed_seconds_deviation)
        resp = get_runs(bc, (lower_limit_datetime, upper_limit_datetime))
        resp_dict_list = resp.json().get('results')
        original_order_datetime_run_id_list = []
        for current_datetime in datetime_list:
            for run_dict in resp_dict_list:
                run_datetime = datetime.datetime.strptime(run_dict['runtime'], BREADBOARD_DATETIME_FORMAT_STRING)
                time_difference = run_datetime - current_datetime
                if (abs(time_difference.total_seconds()) < allowed_seconds_deviation):
                    run_id = run_dict['id']
                    original_order_datetime_run_id_list.append((current_datetime, run_id))
                    break
            else:
                raise RuntimeError("Unable to find a matching run_id for " + current_datetime.strftime(BREADBOARD_DATETIME_FORMAT_STRING))
        return original_order_datetime_run_id_list





"""
Clone for getting runs by datetime range from breadboard client

Clone of the get_runs method in Run_Mixins on breadboard_python_client, but with cleaning 
code removed to avoid throwing errors. 

Parameters:

bc: The breadboard client 
datetime_range: A two-element list [start_datetime, end_datetime] of datetimes; method returns a list 
of run dicts with run times between those two points.

page: Unsure what this does.


Returns: A Response object corresponding to the breadboard server's response to the query.

Remark: The breadboard database has two timestamps for each run: 'runtime' and 'created'. This method 
searches by 'runtime'. 

"""

def get_runs(bc, datetime_range, page = ''):
    payload = {
        'lab':bc.lab_name,
        'start_datetime': datetime_range[0],
        'end_datetime': datetime_range[1]
    }
    response = _query_breadboard_with_retries(bc, 'get', '/runs/' + page, params = payload)
    return response


    


    


        
