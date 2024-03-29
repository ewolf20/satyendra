# Huan Q Bui, BEC1@MIT
# Last updated: 08:01 pm, Mar 30, 2023
# Eric A Wolf
# Refactor: 2:09 PM, Sep 20, 2023


import numpy as np
import sys 
import matplotlib.pyplot as plt
import time
from scipy.signal import find_peaks
import ctypes
import pyttsx3 


PATH_TO_REPOSITORIES_FOLDER = "C:/Users/BEC1 Top/Repositories"
sys.path.insert(0, PATH_TO_REPOSITORIES_FOLDER)

from satyendra.code import slack_bot
from satyendra.code.instruments.ps2000_wrapper_blockmode_utils import Picoscope



#####BEGIN CONFIGS#########
#Slack config params
SLACK_SECS_BETWEEN_WARNINGS = 300

#Lock data acquisition config params
LOCK_BLOCK_SIZE = 1000 
LOCK_BLOCK_DURATION = 0.005
LOCK_PRE_TRIGGER_PERCENT = 0


#Na lock config params
NA_LOCK_OUTPUT_THRESHOLD_MV = 7000
NA_LOCK_ERROR_THRESHOLD_MV = 25


#Li lock config params
LI_LOCK_PEAK_THRESHOLD = 1250
LI_LOCK_PEAK_DISTANCE = 20
LI_LOCK_BOOSTER_MIN_LOCATION = int(LOCK_BLOCK_SIZE * (0.002 / 0.006))
LI_LOCK_BOOSTER_MAX_LOCATION = int(LOCK_BLOCK_SIZE * (0.0023 / 0.006))
LI_LOCK_TRIGGER_LEVEL_ADJUST_INCREMENT = 100

LI_LOCK_PEAK_INDEX_TOLERANCE = 35
LI_LOCK_PEAK_HEIGHT_MIN_RATIO = 0.9

LI_LOCK_PEAK_UPDATING_CONSTANT = 0.01

LI_LOCK_ERROR_TOLERANCE = 3


#Li scope config params
LI_SCOPE_DEFAULT_TRIGGER_LEVEL_MV = 2000

LI_SCOPE_SERIAL = b'JO247/1191' 
LI_SCOPE_CHANNEL_A_RANGE_MV = 10000
LI_SCOPE_CHANNEL_B_RANGE_MV = 5000
LI_SCOPE_TRIGGER_DIRECTION = 0
LI_SCOPE_TRIGGER_CHANNEL = "A"

LI_SCOPE_FIXED_PARAMS = [LI_SCOPE_SERIAL, LI_SCOPE_CHANNEL_A_RANGE_MV, 
                   LI_SCOPE_CHANNEL_B_RANGE_MV, 
                   LOCK_PRE_TRIGGER_PERCENT, LOCK_BLOCK_SIZE, LOCK_BLOCK_DURATION]

LI_SCOPE_TRIGGER_FIXED_PARAMS = [LI_SCOPE_TRIGGER_DIRECTION, LI_SCOPE_TRIGGER_CHANNEL]

#Na scope config params 
NA_SCOPE_SERIAL = b'JY214/4314'
NA_SCOPE_CHANNEL_A_RANGE_MV = 500 
NA_SCOPE_CHANNEL_B_RANGE_MV = 10000

NA_SCOPE_FIXED_PARAMS = [NA_SCOPE_SERIAL, NA_SCOPE_CHANNEL_A_RANGE_MV, 
                         NA_SCOPE_CHANNEL_B_RANGE_MV, LOCK_PRE_TRIGGER_PERCENT, LOCK_BLOCK_SIZE, 
                         LOCK_BLOCK_DURATION]



#INITIALIZATION PARAMS
LI_FP_PEAK_INITIALIZATION_SAMPLES = 20


#FABRY PEROT PARAMS 
FP_PEAK_NAMES = ["Booster", "Slower", "Repump", "Mott"] 

#########END CONFIGS#######


def main(initial_trigger_level):
    tts_engine = pyttsx3.init()

    last_slack_warned_time = -np.inf
    slack_unlock_status = False
    my_bot = slack_bot.SlackBot()

    li_scope_trigger_level = parse_clas()
    li_scope_trigger_params = [li_scope_trigger_level, *LI_SCOPE_TRIGGER_FIXED_PARAMS]
    li_time_data = np.linspace(0, LOCK_BLOCK_DURATION, num = LOCK_BLOCK_SIZE)
    na_time_data = np.linspace(0, LOCK_BLOCK_DURATION, num = LOCK_BLOCK_SIZE)


    li_figure, li_ax, li_lines = initialize_li_plot(li_time_data)
    na_figure, na_ax1, na_ax2, na_lines = initialize_na_plot(na_time_data)

    li_picoscope = initialize_scope(*LI_SCOPE_FIXED_PARAMS, trigger_params = li_scope_trigger_params)
    li_figure_tuple = (li_figure, li_ax, li_lines, li_time_data)


    na_picoscope = initialize_scope(*NA_SCOPE_FIXED_PARAMS)
    na_figure_tuple = (na_figure, na_ax1, na_ax2, na_lines, na_time_data)

    sim_li_trace = np.stack((np.zeros(len(li_time_data)), np.ones(len(li_time_data)) * 1000))
    sim_li_fp_peak_indices = np.arange(4) * 30

    with li_picoscope, na_picoscope:
        try:
            na_scope_offset = initialize_na_scope_offset(na_picoscope)
            li_scope_trigger_level, reference_peak_indices, reference_peak_values = initialize_li_fp_peaks(LI_FP_PEAK_INITIALIZATION_SAMPLES, 
                                                                                    li_picoscope, li_scope_trigger_level, li_figure_tuple, tts_engine)
            tts_engine_say(tts_engine, "Initialization complete", voice = "Zira")
            li_fp_peak_error_count = np.zeros(len(reference_peak_indices))
            bad_trigger_counter = 0
            while True:

                #Na scope

                na_ydata_traces = get_scope_traces(na_picoscope) - na_scope_offset
                update_na_plot(na_figure_tuple, na_ydata_traces)
                na_has_error = detect_na_error(na_ydata_traces)

                #Na error handling

                if na_has_error:
                    NA_ERROR_MESSAGE_SPOKEN = "Guys, sodium unlocked!"
                    NA_ERROR_MESSAGE_SLACK = "Guys, the Na laser unlocked"
                    tts_engine_say(tts_engine, NA_ERROR_MESSAGE_SPOKEN, voice = "David")
                    slack_unlock_status = True
                    last_slack_warned_time = slack_warn(NA_ERROR_MESSAGE_SLACK, my_bot,
                                                        last_slack_warned_time, SLACK_SECS_BETWEEN_WARNINGS, mention_all = True, 
                                                        override_interval = False)
                    

                #Li scope

                li_ydata_traces = get_scope_traces(li_picoscope)
                li_fp_trace = li_ydata_traces[1]
                fp_peak_indices, fp_peak_properties = find_peaks(li_fp_trace, height = LI_LOCK_PEAK_THRESHOLD, distance = LI_LOCK_PEAK_DISTANCE)
                update_li_plot(li_figure_tuple, li_ydata_traces, fp_peak_indices)

                #Li error handling

                li_errors = detect_li_errors(li_fp_trace, fp_peak_indices, reference_peak_indices, reference_peak_values) 
                bad_trigger_counter = np.clip(bad_trigger_counter, 0, 2*LI_LOCK_ERROR_TOLERANCE)
                if len(fp_peak_indices) > len(FP_PEAK_NAMES):
                    bad_trigger_counter += 1
                    if bad_trigger_counter > LI_LOCK_ERROR_TOLERANCE:
                        slack_unlock_status = True 
                        BAD_TRIGGER_ERROR_MESSAGE_SPOKEN = "Bad Trigger" 
                        BAD_TRIGGER_ERROR_MESSAGE_SLACK = "The lithium scope has a bad trigger"
                        tts_engine_say(tts_engine, BAD_TRIGGER_ERROR_MESSAGE_SPOKEN, voice = "Zira")
                        last_slack_warned_time = slack_warn(BAD_TRIGGER_ERROR_MESSAGE_SLACK, my_bot, last_slack_warned_time, SLACK_SECS_BETWEEN_WARNINGS, 
                                                            mention_all = False, override_interval = False)
                else:
                    bad_trigger_counter -= 1
                    if not np.any(li_errors):
                        fp_peak_values = li_fp_trace[fp_peak_indices]
                        reference_peak_indices, reference_peak_values = update_reference_peaks(fp_peak_indices, reference_peak_indices, 
                                                                                            fp_peak_values, reference_peak_values)
                        booster_peak_index = fp_peak_indices[0]
                        trigger_adjusted, adjusted_li_scope_trigger_level = adjust_li_trigger_location(li_picoscope, li_scope_trigger_level, booster_peak_index, 
                                                                        LI_LOCK_TRIGGER_LEVEL_ADJUST_INCREMENT, tts_engine)
                        if trigger_adjusted:
                            trigger_adjust_increment_mV = adjusted_li_scope_trigger_level - li_scope_trigger_level
                            li_fp_sweep_trace_mV = li_ydata_traces[0]
                            trigger_adjust_index_correction = calculate_li_fp_trigger_adjust_index_correction(li_fp_sweep_trace_mV, trigger_adjust_increment_mV)
                            reference_peak_indices = reference_peak_indices + trigger_adjust_index_correction
                        li_scope_trigger_level = adjusted_li_scope_trigger_level
                    li_fp_peak_error_count += np.where(li_errors, 1, -1)
                    li_fp_peak_error_count = np.clip(li_fp_peak_error_count, 0, 2 * LI_LOCK_ERROR_TOLERANCE)
                    fp_peak_has_error_indices = np.nonzero(li_fp_peak_error_count > LI_LOCK_ERROR_TOLERANCE)[0]
                    if len(fp_peak_has_error_indices) > 0:
                        error_peak_names_list = []
                        for fp_peak_has_error_index in fp_peak_has_error_indices:
                            error_peak_names_list.append(FP_PEAK_NAMES[fp_peak_has_error_index])
                        spoken_message_string = " ".join(error_peak_names_list)
                        tts_engine_say(tts_engine, spoken_message_string, voice = "Zira")
                        slack_message_string = "The following diodes appear to be unlocked: {0}".format(", ".join(error_peak_names_list))
                        last_slack_warned_time = slack_warn(slack_message_string, my_bot, last_slack_warned_time, SLACK_SECS_BETWEEN_WARNINGS, 
                                                            mention_all = True, override_interval = False)
                        slack_unlock_status = True

                #Broadcast an all-clear if all errors are cleared
                #Reset warning time so new error can be broadcast right away once old one is resolved

                if slack_unlock_status and not na_has_error and not len(fp_peak_indices) > len(FP_PEAK_NAMES) and len(fp_peak_has_error_indices) == 0:
                    slack_unlock_status = False
                    all_clear_string = "Everything's fine now."
                    last_slack_warned_time = slack_warn(all_clear_string, my_bot, last_slack_warned_time, SLACK_SECS_BETWEEN_WARNINGS, 
                                                        mention_all = False, override_interval = True) 
                    last_slack_warned_time = -np.inf
        except KeyboardInterrupt:
            print('Picoscope logging terminated by keyboard interrupt')


def tts_engine_say(engine, msg, voice = None):
    if voice == "Zira":
        voice_zira = engine.getProperty("voices")[1]
        engine.setProperty('voice', voice_zira.id)
    elif voice == "David":
        voice_david = engine.getProperty("voices")[0] 
        engine.setProperty('voice', voice_david.id)
    engine.say(msg)
    engine.runAndWait()


def initialize_li_plot(li_time_data):
    plt.ion()
    li_figure, li_ax = plt.subplots(figsize = (5, 5)) 
    li_line1, = li_ax.plot(li_time_data, np.zeros(len(li_time_data))) 
    li_line2, = li_ax.plot(li_time_data, np.zeros(len(li_time_data))) 
    li_line3, = li_ax.plot(np.linspace(0, 1, 4) * max(li_time_data), np.zeros(4), 'x') 
    li_lines = (li_line1, li_line2, li_line3)
    plt.xlabel("Time (s)") 
    plt.ylabel("Voltage (mV)")
    return (li_figure, li_ax, li_lines)


def initialize_na_plot(na_time_data):
    plt.ion()
    na_figure, na_ax1 = plt.subplots(figsize = (5,5)) 
    na_ax1.set_xlabel("Time (s)")
    na_ax1.set_ylabel("Error signal (mV)", color = "blue")
    na_line_1, = na_ax1.plot(na_time_data, np.zeros(len(na_time_data)), color = "blue") 
    na_ax1.set_ylim([-1000, 1000])
    na_ax1.tick_params(axis = 'y', labelcolor = 'blue')
    na_ax2 = na_ax1.twinx()
    na_line_2, = na_ax2.plot(na_time_data, np.zeros(len(na_time_data)), color = "red")
    na_ax2.set_label("Time (s)") 
    na_ax2.set_ylabel("Output signal (mV)\n", color = "red")
    na_ax2.tick_params(axis = 'y', labelcolor = "red")
    na_figure.tight_layout()
    na_lines = (na_line_1, na_line_2)
    return (na_figure, na_ax1, na_ax2, na_lines)


def update_na_plot(na_figure_tuple, na_ydata_traces):
    na_fig, na_ax1, na_ax2, na_lines, na_time_data = na_figure_tuple
    for line, ydata in zip(na_lines, na_ydata_traces):
        line.set_xdata(na_time_data) 
        line.set_ydata(ydata)
    trace_max = np.max(na_ydata_traces)
    ax2_ymax = min(NA_SCOPE_CHANNEL_B_RANGE_MV, 1.2 * trace_max)
    na_ax1.set_ylim([-NA_SCOPE_CHANNEL_A_RANGE_MV, NA_SCOPE_CHANNEL_A_RANGE_MV])
    na_ax2.set_ylim([-int(ax2_ymax), int(ax2_ymax)])
    na_fig.canvas.draw() 
    na_fig.canvas.flush_events() 
    time.sleep(0.1)

def update_li_plot(li_figure_tuple, li_ydata_traces, li_fp_peak_indices):
    li_fig, li_ax, li_lines, li_time_data = li_figure_tuple
    sweep_line, fp_line, peaks_line = li_lines
    sweep_ydata, fp_ydata = li_ydata_traces
    trace_min = np.min(li_ydata_traces) 
    trace_max = np.max(li_ydata_traces) 
    trace_diff = trace_max - trace_min 
    trace_padding = trace_diff / 10

    li_ax.set_ylim([trace_min - trace_padding, trace_max + trace_padding])
    peaks_ydata = fp_ydata[li_fp_peak_indices]
    peaks_time_data = li_time_data[li_fp_peak_indices] 
    sweep_line.set_xdata(li_time_data) 
    sweep_line.set_ydata(sweep_ydata) 
    fp_line.set_xdata(li_time_data) 
    fp_line.set_ydata(fp_ydata) 
    peaks_line.set_xdata(peaks_time_data) 
    peaks_line.set_ydata(peaks_ydata) 
    li_fig.canvas.draw() 
    li_fig.canvas.flush_events() 
    time.sleep(0.1)
    


def initialize_scope(serial, channel_range_A, channel_range_B,
                     pre_trigger_percent, block_size, block_duration, trigger_params = None):
    picoscope = Picoscope(serial = serial, verbose = True) 
    picoscope.setup_channel('A', channel_range_mv = channel_range_A) 
    picoscope.setup_channel('B', channel_range_mv = channel_range_B)
    if not trigger_params is None:
        trigger_level, trigger_direction, trigger_channel = trigger_params
        picoscope.setup_trigger(trigger_channel, trigger_threshold_mv = trigger_level, trigger_direction = trigger_direction)
    picoscope.setup_block(block_size = block_size, block_duration = block_duration, pre_trigger_percent = pre_trigger_percent)
    return picoscope


def get_scope_traces(picoscope):
    picoscope.run_block()
    buffers = picoscope.get_block_traces()
    return np.array([val for val in buffers.values()])


def detect_na_error(na_ydata_traces):
    error_signal_values, output_signal_values = na_ydata_traces 
    mean_error_signal = np.mean(error_signal_values) 
    mean_output_signal = np.mean(output_signal_values) 
    return np.abs(mean_error_signal) > NA_LOCK_ERROR_THRESHOLD_MV or np.abs(mean_output_signal) > NA_LOCK_OUTPUT_THRESHOLD_MV


def detect_li_errors(li_fp_trace, fp_peak_indices, reference_peak_indices, reference_peak_values):
    reference_peak_numbering_array = np.arange(len(reference_peak_indices))
    li_fp_peak_values = li_fp_trace[fp_peak_indices] 
    if len(fp_peak_indices) == 0:
        return np.full(4, True)
    fp_peak_reference_differences = np.abs(np.expand_dims(fp_peak_indices, axis = 1) - reference_peak_indices)
    #Identify peaks in the FP spectrum by assigning peaks to the closest reference peak
    fp_peak_identities = np.argmin(fp_peak_reference_differences, axis = 1)
    fp_peak_differences = np.min(fp_peak_reference_differences, axis = 1)
    peak_detected_array = np.isin(reference_peak_numbering_array, li_fp_peak_values)
    fp_peak_within_tolerance_array = np.logical_and(
        fp_peak_differences < LI_LOCK_PEAK_INDEX_TOLERANCE, 
        li_fp_peak_values > reference_peak_values[fp_peak_identities] * LI_LOCK_PEAK_HEIGHT_MIN_RATIO
    )
    reference_peak_is_there_array = peak_detected_array
    reference_peak_is_there_array[fp_peak_identities] = fp_peak_within_tolerance_array
    return np.logical_not(reference_peak_is_there_array)



#NOTE: This function implicitly relies on the linearity of the Fabry-Perot sweep
def calculate_li_fp_trigger_adjust_index_correction(li_fp_sweep_trace_mV, trigger_adjust_increment_mV):
    reference_sweep_value = np.average(li_fp_sweep_trace_mV) 
    reference_sweep_value_index = np.argmin(np.abs(li_fp_sweep_trace_mV) - reference_sweep_value)
    trigger_adjust_offset_sweep_trace = li_fp_sweep_trace_mV + trigger_adjust_increment_mV 
    adjusted_reference_sweep_value_index = np.argmin(np.abs(trigger_adjust_offset_sweep_trace) - reference_sweep_value)
    reference_sweep_value_index_change = adjusted_reference_sweep_value_index - reference_sweep_value_index 
    return reference_sweep_value_index_change

def update_reference_peaks(fp_peak_indices, reference_peak_indices, fp_peak_values, reference_peak_values):
    reference_peak_indices += LI_LOCK_PEAK_UPDATING_CONSTANT * (fp_peak_indices - reference_peak_indices) 
    reference_peak_values += LI_LOCK_PEAK_UPDATING_CONSTANT * (fp_peak_values - reference_peak_values)
    return reference_peak_indices, reference_peak_values

def slack_warn(msg, my_bot, last_slack_warned_time, warning_interval, 
               mention_all = False, override_interval = False):
    current_time = time.time() 
    if override_interval or current_time - last_slack_warned_time > warning_interval:
        last_slack_warned_time = current_time 
        my_bot.post_message(msg, mention_all = mention_all)
    return last_slack_warned_time


def adjust_li_trigger_location(li_scope, li_scope_trigger_level, booster_peak_index, increment, tts_engine):
    if booster_peak_index < LI_LOCK_BOOSTER_MIN_LOCATION:
        trigger_adjusted = True
        spoken_msg = "Triggering too late. Adjusting." 
        li_scope_trigger_level -= increment
    elif booster_peak_index > LI_LOCK_BOOSTER_MAX_LOCATION: 
        trigger_adjusted = True
        spoken_msg = "Triggering too soon. Adjusting."
        tts_engine_say(tts_engine, spoken_msg, voice = "Zira")
        li_scope_trigger_level += increment
    else:
        trigger_adjusted = False
    if trigger_adjusted:
        tts_engine_say(tts_engine, spoken_msg, voice = "Zira")
        li_scope.setup_trigger(LI_SCOPE_TRIGGER_CHANNEL, trigger_threshold_mv = li_scope_trigger_level, 
                                trigger_direction = LI_SCOPE_TRIGGER_DIRECTION)
        print("Trigger level: {0:.1f} mV".format(li_scope_trigger_level))
    return (trigger_adjusted, li_scope_trigger_level)


def initialize_na_scope_offset(na_scope):
    na_scope_ydata = get_scope_traces(na_scope) 
    return np.average(na_scope_ydata, axis = 1, keepdims = True)


def initialize_li_fp_peaks(initialization_samples, li_scope, li_scope_trigger_level, li_figure_tuple, tts_engine):
    initialization_counter = 0
    average_peak_indices = np.zeros(4) 
    average_peak_values = np.zeros(4)
    while initialization_counter < initialization_samples:
        li_traces = get_scope_traces(li_scope)
        li_fp_trace = li_traces[1]
        li_fp_peak_indices, li_fp_peak_properties = find_peaks(li_fp_trace, height = LI_LOCK_PEAK_THRESHOLD, distance = LI_LOCK_PEAK_DISTANCE)
        update_li_plot(li_figure_tuple, li_traces, li_fp_peak_indices)
        if len(li_fp_peak_indices) == 4:
            booster_peak_index, *_ = li_fp_peak_indices 
            li_fp_peak_values = li_fp_trace[li_fp_peak_indices]
            trigger_adjusted, li_scope_trigger_level = adjust_li_trigger_location(li_scope, li_scope_trigger_level, 
                                                                                  booster_peak_index, LI_LOCK_TRIGGER_LEVEL_ADJUST_INCREMENT, 
                                                                                  tts_engine)
            if not trigger_adjusted:
                initialization_counter += 1
                print("Initializing: {0:d}/{1:d}".format(initialization_counter, initialization_samples)) 
                average_peak_indices += li_fp_peak_indices / initialization_samples 
                average_peak_values += li_fp_peak_values / initialization_samples
        else:
            if len(li_fp_peak_indices) > 4:
                spoken_message = "Bad trigger"
            else:
                spoken_message = "Not locked" 
            tts_engine_say(tts_engine, spoken_message, voice = "Zira")
    return (li_scope_trigger_level, average_peak_indices, average_peak_values)


HELP_ALIASES = ["help", "h", "HELP", "H", "Help"]
def parse_clas():
    clas = sys.argv[1:] 
    if len(clas) > 0 and clas[0] in HELP_ALIASES:
        help_function()
        exit(0)
    if len(clas) > 0:
        trigger_level = int(clas[0]) 
    else:
        trigger_level = LI_SCOPE_DEFAULT_TRIGGER_LEVEL_MV
    return trigger_level

def help_function():
    print("Program name: Picoscope Lock Monitor") 
    print("Utility program for monitoring the sodium and lithium injection diode laser locks.") 
    print("CLAS:")
    print("""1 (int, optional): Trigger level. The trigger level for the injection lock monitoring scope on the Fabry-Perot piezo sweep. 
        Default is 2000 mV.""")


if __name__ == "__main__":
	main(sys.argv)


    