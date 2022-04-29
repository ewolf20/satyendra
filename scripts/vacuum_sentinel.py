import json 
import pa
import time
from collections import deque
import importlib.resources as pkg_resources

#Imports utility_functions. Update this once enrico is refactored into modules

import sys 
import os 

path_to_file = os.path.dirname(os.path.abspath(__file__))
path_to_satyendra = path_to_file + "/../../"

sys.path.insert(0, path_to_satyendra)

from satyendra.code.plotting_utilities import initialize_live_plot, update_live_plot
from satyendra.code.vacuum_monitoring.vacuum_monitor import VacuumMonitor



from satyendra import configs as c 
from satyendra import secrets as s 

#Configure sampling rate, etc. 
DELAY_TIME = 5
SAMPLES_PER_LOG = 12
ERROR_PATIENCE = 3
THRESHOLD_PATIENCE = 3
SLACK_ERROR_REUPDATE_TIME_SECS = 1800
SLACK_THRESHOLD_REUPDATE_TIME_SECS = 600

PRINT_VALUES = True

#Configure addresses for vacuum monitors
ION_GAUGE_ADDRESS = "foo"

ION_GAUGE_WARNING_THRESHOLD = 1e-5
ION_GAUGE_TURNOFF_THRESHOLD = 1e-4

#List of sentinel-monitored values to plot. Elements are keys of the dict returned by monitor_once
PLOTTING_KEY_LIST = []

#parameters for live plotting
#Number of values to plot on one live plot. 
PLOTTING_NUMBER = -1
#Interval between plotted points (every Nth point is plotted)
PLOTTING_INTERVAL = 12
#Put the y scale of the plot in log
PLOT_YLOG = False 
#Put the x scale of the plot in log
PLOT_XLOG = False
#Set the unit of time for the live plot
#Accepts "s", "m", "h", "d"
PLOT_TIMEUNIT = "m"




#Configure settings for who to warn in a vacuum emergency

def main():
	my_monitor = VacuumMonitor([("Ion_Gauge", ION_GAUGE_ADDRESS, "gauge_xgs-600", ['pressurecurrentfil'], {'pressurecurrentfil':ION_GAUGE_WARNING_THRESHOLD}, {})])
	protection_thresholds_dict = {"Ion_Gauge pressurecurrentfil": ION_GAUGE_TURNOFF_THRESHOLD}
	start_time = time.time()
	old_time = start_time
	counter = 0
	error_count = 0
	threshold_count = 0
	local_logger_bool = True
	plot_update_bool = True
	threshold_fault = False 
	error_fault = False 
	error_old_time = 0.0 
	threshold_old_time = 0.0
	figure_and_axis_dict, data_deque_dict, time_deque = set_up_plots()
	try:
		while(True):
			current_time = time.time()
			if(current_time - old_time > DELAY_TIME or current_time - old_time < 0):
				old_time = current_time 
				local_logger_bool = (counter % SAMPLES_PER_LOG == 0) 
				plot_update_bool = (counter % PLOTTING_INTERVAL == 0)
				counter += 1
				readings_dict, errors_list, thresholds_list = my_monitor.monitor_once(log_local = local_logger_bool)
				handle_turnoff_limits(my_monitor, readings_dict, protection_thresholds_dict)
				if(PRINT_VALUES):
					print(readings_dict) 
				if(plot_update_bool):
					elapsed_time = current_time - start_time
					update_plots(figure_and_axis_dict, data_deque_dict, time_deque, elapsed_time, readings_dict)
				error_count, error_fault, error_old_time = handle_errors(error_count, error_fault, error_old_time, errors_list, my_monitor)
				threshold_count, threshold_fault, threshold_old_time = handle_thresholds(threshold_count, threshold_fault, threshold_old_time, thresholds_list, my_monitor)
	except Exception as e:
		my_monitor.warn_on_slack(" VACUUM_MONITOR_SHUTDOWN: An exception has crashed the vacuum monitoring.", mention_all = True)
		raise e



def handle_errors(error_count, error_fault, error_old_time, errors_list, my_monitor):
	if(len(errors_list) != 0):
		error_count += 1
		errors_string = ""
		for error_name in errors_list:
			errors_string = errors_string + error_name + ", "
		if(error_count >= ERROR_PATIENCE and not error_fault):
			error_fault = True 
			error_warning_string = "VACUUM_ERROR: The vacuum monitor is unable to read from the following instruments: " + errors_string
			my_monitor.warn_on_slack(error_warning_string, mention_all = True)
			error_old_time = time.time() 
		elif(error_fault):
			error_current_time = time.time() 
			if(error_current_time - error_old_time > SLACK_ERROR_REUPDATE_TIME_SECS):
				error_old_time = error_current_time 
				error_update_string = "VACUUM_ERROR_UPDATE: The reading error persists. Vacuum monitor is unable to read from the following instruments: " + errors_string 
				my_monitor.warn_on_slack(error_update_string, mention_all = True ) 
	elif(error_count > 0):
		error_count -= 1
		if(error_count < ERROR_PATIENCE and error_fault):
			error_fault = False 
			my_monitor.warn_on_slack("VACUUM_ERROR_RESOLVED: The outstanding reading error has been resolved.")
	return (error_count, error_fault, error_old_time) 


def handle_thresholds(threshold_count, threshold_fault, threshold_old_time, thresholds_list, my_monitor):
	if(len(thresholds_list) != 0):
		threshold_count += 1 
		thresholds_string = ""
		for threshold_tuple in thresholds_list:
			reading_key, value, threshold = threshold_tuple 
			thresholds_string = thresholds_string + reading_key + ", value = " + str(value) + ", threshold = " + str(threshold) + "; "
		if(threshold_count >= THRESHOLD_PATIENCE and not threshold_fault):
			threshold_fault = True
			threshold_warning_string = "VACUUM_THRESHOLD_EXCEEDED: The following vacuum readings are above threshold: " + thresholds_string 
			my_monitor.warn_on_slack(threshold_warning_string, mention_all = True)
			threshold_old_time = time.time() 
		elif(threshold_fault):
			threshold_current_time = time.time()
			if(threshold_current_time - threshold_old_time > SLACK_THRESHOLD_REUPDATE_TIME_SECS):
				threshold_old_time = threshold_current_time 
				threshold_update_string = "VACUUM_THRESHOLD_UPDATE: The following values are still above threshold: " + thresholds_string
				my_monitor.warn_on_slack(threshold_update_string, mention_all = True)
	elif(threshold_count > 0):
		threshold_count -= 1
		if(threshold_count < THRESHOLD_PATIENCE and threshold_fault):
			threshold_fault = False
			my_monitor.warn_on_slack("VACUUM_THRESHOLD_RESOLVED: The outstanding threshold warning has been resolved. All vacuum values below threshold.") 
	return (threshold_count, threshold_fault, threshold_old_time) 



#TODO: Make this more general
def handle_turnoff_limits(my_monitor, readings_dict, protection_thresholds_dict):
	turnoff_name_list = [] 
	for key in protection_thresholds_dict:
		if key in readings_dict and readings_dict[key] > protection_thresholds_dict[key]:
			turnoff_name = key.split(" ")[0] 
			turnoff_name_list.append(turnoff_name) 
	if(len(turnoff_name_list) > 0):
		turnoff_success_list = my_monitor.failsafe(turnoff_name_list)
		my_monitor.warn_on_slack("Turning off instruments for safety!", mention_all = True) 


	

			




def set_up_plots():
	figure_and_axis_dict = {} 
	data_deque_dict = {}
	if(PLOTTING_NUMBER == -1):
		time_deque = deque([]) 
	else:
		time_deque = deque([], PLOTTING_NUMBER)
	for key in PLOTTING_KEY_LIST:
		fig, ax = initialize_live_plot()
		if(PLOT_XLOG):
			ax.set_xscale("log")
		if(PLOT_YLOG):
			ax.set_yscale("log")
		ax.set_xlabel("Time (" + PLOT_TIMEUNIT + ") since " + time.strftime("%y-%m-%d %H:%M:%S"))
		ax.set_ylabel(key) 
		figure_and_axis_dict[key] = (fig, ax)
		if(PLOTTING_NUMBER == -1):
			data_deque = deque([]) 
		else:
			data_deque = deque([], PLOTTING_NUMBER)
		data_deque_dict[key] = data_deque
	return (figure_and_axis_dict, data_deque_dict, time_deque)

def update_plots(figure_and_axis_dict, data_deque_dict, time_deque, elapsed_time, readings_dict):
	if(PLOT_TIMEUNIT == "s"):
		seconds_to_time_unit_conversion = 1.0 
	elif(PLOT_TIMEUNIT == "m"):
		seconds_to_time_unit_conversion = 1.0 / (60) 
	elif(PLOT_TIMEUNIT == "h"):
		seconds_to_time_unit_conversion = 1.0 / (60 * 60)
	elif(PLOT_TIMEUNIT == "d"):
		seconds_to_time_unit_conversion = 1.0 / (60 * 60 * 24) 
	time_deque.append(elapsed_time * seconds_to_time_unit_conversion) 
	for key in figure_and_axis_dict:
		fig, ax = figure_and_axis_dict[key]
		data_deque = data_deque_dict[key]
		new_data_point = readings_dict[key] 
		data_deque.append(new_data_point) 
		update_live_plot(time_deque, data_deque, ax = ax) 

if __name__ == "__main__":
	main()

