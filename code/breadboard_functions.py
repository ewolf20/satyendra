import datetime
import time 
import warnings

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


#TODO: Add support for non-contiguous datetime ranges; just a search in the returned run id dictionary.
"""
Associates a list of datetimes with run parameters. 

Given input [datetime1, datetime2, ...], returns a list of tuples [(datetime1, runparameters1), (datetime2, runparameters2), ...].
Note that the datetimes are datetime objects, and runparameters is the dict returned by get_run_parameters_dict_from_ids.

If allow_fails = False, the program will throw an error if there are any datetimes which cannot be matched with a run id. If true, it will issue a warning 
and then return None in place of the missing id.
"""
def get_run_parameter_dicts_from_datetimes(bc, datetime_list, allowed_seconds_deviation = 5, allow_fails = False, 
                                    verbose = False):
    if(len(datetime_list) == 0):
        return [] 
    min_datetime = min(datetime_list) 
    max_datetime = max(datetime_list)
    lower_limit_datetime = min_datetime - datetime.timedelta(seconds = allowed_seconds_deviation) 
    upper_limit_datetime = max_datetime + datetime.timedelta(seconds = allowed_seconds_deviation)
    results_dict_list = _get_results_dict_list_from_datetime_range(bc, (lower_limit_datetime, upper_limit_datetime))
    original_order_datetime_run_id_list = []
    for current_datetime in datetime_list:
        for results_dict in results_dict_list:
            run_datetime = datetime.datetime.strptime(results_dict['runtime'], BREADBOARD_DATETIME_FORMAT_STRING)
            time_difference = run_datetime - current_datetime
            if (abs(time_difference.total_seconds()) < allowed_seconds_deviation):
                parameters_dict = _get_filtered_parameters_dict(results_dict, verbose = verbose)
                original_order_datetime_run_id_list.append((current_datetime, parameters_dict))
                break
        else:
            if allow_fails:
                warnings.warn("Unable to find a matching run for " + current_datetime.strftime(BREADBOARD_DATETIME_FORMAT_STRING), RuntimeWarning)
                original_order_datetime_run_id_list.append((current_datetime, None))
            else:
                raise RuntimeError("Unable to find a matching run for " + current_datetime.strftime(BREADBOARD_DATETIME_FORMAT_STRING))
    return original_order_datetime_run_id_list


#TODO: Should really implement this at the level of breadboard python client, probably in the mixins, though then I'll have to get push access.
#TODO: Need to remove the hard-coded limit and read it from the http response somehow...
def _get_results_dict_list_from_datetime_range(bc, datetime_range, page = '', **kwargs):
    #The page size of breadboard's http responses, hard-coded in
    LIMIT = 200
    initial_response = get_runs(bc, datetime_range, page = page, **kwargs)
    initial_response_json = initial_response.json() 
    results_dict_list = []
    results_dict_list.extend(initial_response_json.get('results')) 
    next = initial_response_json.get('next') 
    offset = 0 
    offset += LIMIT
    while next:
        response = get_runs(bc, datetime_range, page = page, offset = offset, limit = LIMIT)
        response_json = response.json() 
        results_dict_list.extend(response_json.get('results')) 
        next = response_json.get('next') 
        offset += LIMIT
    return results_dict_list


def get_datetime_from_run_id(bc, run_id):
    resp = _query_breadboard_with_retries(bc, 'get', '/runs/' + str(run_id))
    resp_json = resp.json()
    run_time_string = resp_json.get('runtime') 
    return datetime.datetime.strptime(run_time_string, BREADBOARD_DATETIME_FORMAT_STRING)



"""Method for getting run parameter dicts from a list of run_ids.

Params:

start_datetime, end_datetime: Optional; if not specified, gets these by querying breadboard, but this will slow things down.

Returns: 

A list [run1params, run2params, ...] of the 'params' from the 'results' dict returned for each run by breadboard."""
def get_run_parameter_dicts_from_ids(bc, run_id_list, start_datetime = None, end_datetime = None, verbose = False, allowed_seconds_deviation = 5):
    if(len(run_id_list) == 0):
        return []
    tagged_run_id_list = list(enumerate(run_id_list)) 
    sorted_tagged_run_id_list = sorted(tagged_run_id_list, key = lambda f: f[1], reverse = True) 
    if(not start_datetime):
        first_run_id = sorted_tagged_run_id_list[-1][1] 
        start_datetime = get_datetime_from_run_id(bc, first_run_id)
    offset_start_datetime = start_datetime - datetime.timedelta(allowed_seconds_deviation)
    if(not end_datetime):
        last_run_id = sorted_tagged_run_id_list[0][1] 
        end_datetime = get_datetime_from_run_id(bc, last_run_id)
    offset_end_datetime = end_datetime + datetime.timedelta(allowed_seconds_deviation)
    results_dict_list = _get_results_dict_list_from_datetime_range(bc, (offset_start_datetime, offset_end_datetime))
    tagged_results_dict_list = []
    #Naive bubble search...
    for tagged_run_id in sorted_tagged_run_id_list:
        tag, run_id = tagged_run_id
        for results_dict in results_dict_list:
            if results_dict['id'] == run_id:
                tagged_results_dict_list.append((tag, results_dict))
                break 
        else:
            raise RuntimeError('Unable to find specified run id.')
    original_order_results_dict_list = [f[1] for f in sorted(tagged_results_dict_list, key = lambda el: el[0])] 
    original_order_params_dict_list = [_get_filtered_parameters_dict(f, verbose = verbose) for f in original_order_results_dict_list]
    return original_order_params_dict_list


def get_run_parameter_dict_from_id(bc, run_id, verbose = False, allowed_seconds_diff = 5):
    resp = _query_breadboard_with_retries(bc, 'get', '/runs/' + str(run_id))
    results = resp.json()
    return _get_filtered_parameters_dict(results, verbose = verbose) 




def _get_filtered_parameters_dict(results_dict, verbose = False):
    cleaned_dict = {}
    cleaned_dict['id'] = results_dict['id']
    cleaned_dict['runtime'] = results_dict['runtime'] 
    if 'badshot' in results_dict:
        cleaned_dict['badshot'] = results_dict['badshot'] 
    params_dict = results_dict['parameters']
    if(verbose):
        cleaned_dict.update(params_dict)
    else:
        list_bound_var_names = params_dict['ListBoundVariables']
        for list_bound_var_name in list_bound_var_names:
            cleaned_dict[list_bound_var_name] = params_dict[list_bound_var_name]
    return cleaned_dict

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

def get_runs(bc, datetime_range, page = '', **kwargs):
    payload = {
        'lab':bc.lab_name,
        'start_datetime': datetime_range[0],
        'end_datetime': datetime_range[1],
        **kwargs
    }
    response = _query_breadboard_with_retries(bc, 'get', '/runs/' + page, params = payload)
    return response


    


    


        
