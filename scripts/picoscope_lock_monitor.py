# Huan Q Bui, BEC1@MIT
# Last updated: 08:01 pm, Mar 30, 2023


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
from satyendra.code.ps2000_wrapper_blockmode_utils import Picoscope



#####BEGIN CONFIGS#########
#Slack config params
SLACK_SECS_BETWEEN_WARNINGS = 300

#Lock data acquisition config params
LOCK_BLOCK_SIZE = 1000 
LOCK_BLOCK_DURATION = 0.005
LOCK_PRE_TRIGGER_PERCENT = 0


#Na lock config params
NA_LOCK_OUTPUT_THRESHOLD_MV = 9000
NA_LOCK_ERROR_THRESHOLD_MV = 69


#Li lock config params
LI_LOCK_PEAK_THRESHOLD = 1000


#Li scope config params
LI_SCOPE_DEFAULT_TRIGGER_LEVEL_MV = 2000

LI_SCOPE_ID = 0
LI_SCOPE_SERIAL = "J0247/1191" 
LI_SCOPE_CHANNEL_A_RANGE_MV = 10000
LI_SCOPE_CHANNEL_B_RANGE_MV = 5000
LI_SCOPE_TRIGGER_DIRECTION = 0
LI_SCOPE_TRIGGER_CHANNEL = "A"

LI_SCOPE_FIXED_PARAMS = [LI_SCOPE_ID, LI_SCOPE_SERIAL, LI_SCOPE_CHANNEL_A_RANGE_MV, 
                   LI_SCOPE_CHANNEL_B_RANGE_MV, 
                   LOCK_PRE_TRIGGER_PERCENT, LOCK_BLOCK_SIZE, LOCK_BLOCK_DURATION]

LI_SCOPE_TRIGGER_FIXED_PARAMS = [LI_SCOPE_TRIGGER_DIRECTION, LI_SCOPE_TRIGGER_CHANNEL]

#Na scope config params 
NA_SCOPE_ID = 1
NA_SCOPE_SERIAL = "J0247/0361"
NA_SCOPE_CHANNEL_A_RANGE_MV = 500 
NA_SCOPE_CHANNEL_B_RANGE_MV = 10000

NA_SCOPE_FIXED_PARAMS = [NA_SCOPE_ID, NA_SCOPE_SERIAL, NA_SCOPE_CHANNEL_A_RANGE_MV, 
                         NA_SCOPE_CHANNEL_B_RANGE_MV, LOCK_PRE_TRIGGER_PERCENT, LOCK_BLOCK_SIZE, 
                         LOCK_BLOCK_DURATION]

#########END CONFIGS#######


def main(initial_trigger_level):
    zira, david = initialize_ttsengines()

    last_slack_warned_time = -np.inf
    slack_unlock_status = False
    slack_bot = slack_bot.SlackBot()

    li_scope_trigger_level = parse_clas()
    li_scope_trigger_params = [li_scope_trigger_level, *LI_SCOPE_TRIGGER_FIXED_PARAMS]

    initialization_counter = 0
    initialization_counter_MAX = 20

    # average peak heights
    boosterPeak_avg = 0
    slowerPeak_avg = 0
    repumpPeak_avg = 0
    MOTPeak_avg = 0
    # AVERAGE SPACINGS to booster:
    booster_to_slower = 0  # 130
    booster_to_repump = 0  # 280
    booster_to_MOT    = 0  # 400
    # lock status
    slowerLocked = 0
    repumpLocked = 0
    MOTLocked = 0
    # old peaks to compare in code
    slowerPeakOld = 0
    repumpPeakOld = 0
    MOTPeakOld = 0 
    # quality factor:
    quality = 0.9
    # print lock status:
    printLockStatus_COUNTER = 0
    printLockStatus_after = 2
    # lock max strikes
    lock_max_strikes = 5
    # update avg counter params 
    updatePeak_avg_counter = 0
    updatePeak_avg_after = 10
    # peak threshold:
    # good window for booster peak:
    boosterLocMin = int(blockSize*(0.002/0.006))
    boosterLocMax = int(blockSize*(0.0023/0.006))

    boosterPeak_avg_new = 0
    slowerPeak_avg_new = 0
    repumpPeak_avg_new = 0
    MOTPeak_avg_new = 0

    # triggering issue:
    triggering_issue_counter = 0
    triggering_issue_max_strikes = 5 


    # peak find window:
    peak_find_window = 35

    li_figure, li_ax, li_lines = initialize_li_plot()
    na_figure, na_ax1, na_ax2, na_lines = initialize_na_plot()

    li_picoscope = initialize_scope(*LI_SCOPE_FIXED_PARAMS, trigger_params = li_scope_trigger_params)
    li_time_data = np.linspace(0, LOCK_BLOCK_DURATION, num = LOCK_BLOCK_SIZE)

    na_picoscope = initialize_scope(*NA_SCOPE_FIXED_PARAMS)
    na_time_data = np.linspace(0, LOCK_BLOCK_DURATION, num = LOCK_BLOCK_SIZE)

    with li_picoscope, na_picoscope:
        try:
            while True:

                #########################################################
                ########## Na scope #####################################
                #########################################################

                na_ydata_traces = get_scope_traces(na_picoscope)
                update_na_plot(na_figure, na_ax1, na_ax2, na_lines, na_time_data, na_ydata_traces)
                na_has_error = detect_na_error(na_ydata_traces)
                if na_has_error:
                    NA_ERROR_MESSAGE_SPOKEN = "Guys, sodium unlocked!"
                    NA_ERROR_MESSAGE_SLACK = "Guys, the Na laser unlocked"
                    tts_engine_say(david, NA_ERROR_MESSAGE_SPOKEN)
                    slack_unlock_status = True
                    last_slack_warned_time = slack_warn(NA_ERROR_MESSAGE_SLACK, slack_bot,
                                                        last_slack_warned_time, SLACK_SECS_BETWEEN_WARNINGS, mention_all = True, 
                                                        override_interval = False)
                #########################################################
                ########## Li scope #####################################
                #########################################################

                li_ydata_traces = get_scope_traces(li_picoscope)
                li_fp_trace = li_ydata_traces[1]
                fp_peak_indices, fp_peak_properties = find_peaks(li_fp_trace, height = LI_LOCK_PEAK_THRESHOLD)
                update_li_plot(li_figure, li_ax, li_lines, li_time_data, li_ydata_traces, fp_peak_indices)
                li_fp_errors_array = detect_li_error()

                ###############################
                # first, there should be exactly four peaks
                if initialization_counter < initialization_counter_MAX:
                    if len(FP_peak_indices) == 4:
                        # store peak values
                        boosterPeak = int(FP_array[FP_peak_indices[0]])
                        slowerPeak  = int(FP_array[FP_peak_indices[1]])
                        repumpPeak  = int(FP_array[FP_peak_indices[2]])
                        MOTPeak     = int(FP_array[FP_peak_indices[3]])

                        # store peak locations
                        boosterLoc  = FP_peak_indices[0]
                        slowerLoc   = FP_peak_indices[1]
                        repumpLoc   = FP_peak_indices[2]
                        MOTLoc      = FP_peak_indices[3]

                        ########## INITIALIZE #############:
                        if boosterLoc <= boosterLocMax and boosterLoc >= boosterLocMin:
                            # if booster in good location:
                            print('Initializing: ' + str(initialization_counter+1) + '/' + str(initialization_counter_MAX))
                            # AVERAGE HEIGHTS
                            boosterPeak_avg += boosterPeak/initialization_counter_MAX
                            slowerPeak_avg += slowerPeak/initialization_counter_MAX
                            repumpPeak_avg += repumpPeak/initialization_counter_MAX
                            MOTPeak_avg += MOTPeak/initialization_counter_MAX
                            # AVERAGE SPACINGS to booster:
                            booster_to_slower += abs(slowerLoc - boosterLoc)/initialization_counter_MAX
                            booster_to_repump += abs(repumpLoc - boosterLoc)/initialization_counter_MAX
                            booster_to_MOT    += abs(MOTLoc    - boosterLoc)/initialization_counter_MAX
                            initialization_counter += 1
                        else:
                            if boosterLoc >= boosterLocMax:
                                msg = 'Triggering too soon. Adjusting'
                                zira.setProperty('voice', voice_zira[1].id) # index = 0 for male and 1 for female
                                zira.say(msg)
                                zira.runAndWait()
                                # do sth
                                triggerLevel += 100
                                Li_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)
                                print('Trigger level: ' + str(triggerLevel))

                            elif boosterLoc <= boosterLocMin:
                                msg = 'Triggering too late. Adjusting'
                                zira.setProperty('voice', voice_zira[1].id) # index = 0 for male and 1 for female
                                zira.say(msg)
                                zira.runAndWait()
                                # do sth
                                triggerLevel -= 100
                                Li_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)
                                print('Trigger level: ' + str(triggerLevel))
                    else:
                        # if dont see exactly four peaks...
                        if len(FP_peak_indices) >= 5:
                            msg = 'Bad trigger'
                            zira.setProperty('voice', voice_zira[1].id) # index = 0 for male and 1 for female
                            zira.say(msg)
                            zira.runAndWait()
                        else:
                            msg = 'Not locked'
                            zira.setProperty('voice', voice_zira[1].id) # index = 0 for male and 1 for female
                            zira.say(msg)
                            zira.runAndWait()
                
                else:
                    if len(FP_peak_indices) >= 1: 
                        # find peaks based on location relative to booster now:
                        boosterLoc = FP_peak_indices[0]
                        slowerPeak = int(max(FP_array[ boosterLoc - peak_find_window + int(booster_to_slower) : boosterLoc + peak_find_window + int(booster_to_slower)]))
                        repumpPeak = int(max(FP_array[ boosterLoc - peak_find_window + int(booster_to_repump) : boosterLoc + peak_find_window + int(booster_to_repump)]))
                        MOTPeak = int(max(FP_array[ boosterLoc - peak_find_window + int(booster_to_MOT) : boosterLoc + peak_find_window + int(booster_to_MOT)]))

                        # turn average quantities into integers:
                        boosterPeak_avg = int(boosterPeak_avg)
                        slowerPeak_avg = int(slowerPeak_avg)
                        repumpPeak_avg = int(repumpPeak_avg)
                        MOTPeak_avg = int(MOTPeak_avg)

                        # now monitor logic
                        if boosterLoc >= boosterLocMax:
                            msg = 'Triggering too soon. Adjusting'
                            zira.setProperty('voice', voice_zira[1].id) # index = 0 for male and 1 for female
                            zira.say(msg)
                            zira.runAndWait()
                            # do sth
                            triggerLevel += 25
                            Li_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)

                        elif boosterLoc <= boosterLocMin:
                            msg = 'Triggering too late. Adjusting'
                            zira.setProperty('voice', voice_zira[1].id) # index = 0 for male and 1 for female
                            zira.say(msg)
                            zira.runAndWait()
                            # do sth
                            triggerLevel -= 25
                            Li_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)

                        # SLOWER
                        if (slowerPeak < quality*slowerPeak_avg):
                            if (slowerLocked < lock_max_strikes):
                                if (slowerPeakOld < quality*slowerPeak_avg):
                                    slowerLocked+=1 # only add if previous shot also bad
                                else:
                                    slowerLocked=0 # if last shot was good then reset, probably noise                 
                        else: # if Peak is good, then reset strikes
                            slowerLocked = 0
                            
                        # repump
                        if (repumpPeak < quality*repumpPeak_avg):
                            if (repumpLocked < lock_max_strikes):
                                if (repumpPeakOld < quality*repumpPeak_avg):
                                    repumpLocked+=1 # only add if previous shot also bad
                                else:
                                    repumpLocked = 0 # if last shot was good then reset, probably noise                 
                        else: # if Peak is good, then reset strikes
                            repumpLocked = 0

                        # MOT
                        if (MOTPeak < quality*MOTPeak_avg):
                            if (MOTLocked < lock_max_strikes):
                                if (MOTPeakOld < quality*MOTPeak_avg):
                                    MOTLocked+=1 # only add if previous shot also bad
                                else:
                                    MOTLocked = 0 # if last shot was good then reset, probably noise                 
                        else: # if Peak is good, then reset strikes
                            MOTLocked = 0

                        # the end
                        boosterPeakOld = boosterPeak
                        slowerPeakOld = slowerPeak
                        repumpPeakOld = repumpPeak
                        MOTPeakOld = MOTPeak

                        # print status
                        if (printLockStatus_COUNTER > printLockStatus_after):                                                    
                            printLockStatus_COUNTER = 0 # reset
                            slower_unlocked = (slowerLocked == lock_max_strikes)
                            MOT_unlocked = (MOTLocked == lock_max_strikes) 
                            repump_unlocked = (repumpLocked == lock_max_strikes)
                            msg_list = []
                            if slower_unlocked:
                                msg_list.append("slower") 
                            if repump_unlocked:
                                msg_list.append("repump")
                            if MOT_unlocked:
                                msg_list.append("mott")
                            if slower_unlocked or MOT_unlocked or repump_unlocked:
                                msg = ' '.join(msg_list)
                                zira.setProperty('voice', voice_zira[1].id) # index = 0 for male and 1 for female
                                zira.say(msg)
                                zira.runAndWait()
                                current_time = time.time()
                                slack_unlock_status = True
                                if current_time - last_slack_warned_time > SLACK_SECS_BETWEEN_WARNINGS:
                                    msg_string = "The following injection locked diodes appear to be unlocked: "
                                    for name in msg_list:
                                        msg_string += name + ", "
                                    my_bot.post_message(msg_string, mention_all = True)
                                    last_slack_warned_time = current_time
                            elif slack_unlock_status:
                                my_bot.post_message("Everything's fine now.") 
                                slack_unlock_status = False
                                last_slack_warned_time = -np.inf
                        else:
                            printLockStatus_COUNTER += 1

                        # auto update MAX values, only if everything is locked
                        # act only for every "updatePeak_avg_after" iterations, to stay conservative
                        if not any([slowerLocked, repumpLocked, MOTLocked]): 
                            if updatePeak_avg_counter >= updatePeak_avg_after:

                                boosterPeak_avg = int(boosterPeak_avg_new)
                                slowerPeak_avg = int(slowerPeak_avg_new)
                                repumpPeak_avg = int(repumpPeak_avg_new)
                                MOTPeak_avg = int(MOTPeak_avg_new)
                                
                                # reset everything
                                updatePeak_avg_counter = 0 
                                boosterPeak_avg_new = 0
                                slowerPeak_avg_new = 0
                                repumpPeak_avg_new = 0
                                MOTPeak_avg_new = 0
                            else:
                                boosterPeak_avg_new += boosterPeak/updatePeak_avg_after
                                slowerPeak_avg_new += slowerPeak/updatePeak_avg_after
                                repumpPeak_avg_new += repumpPeak/updatePeak_avg_after
                                MOTPeak_avg_new += MOTPeak/updatePeak_avg_after
                                updatePeak_avg_counter += 1

                    else:
                        # this means everything's unlocked most likely
                        msg = "Something is wrong. Please check Lithium table."
                        zira.setProperty('voice', voice_zira[1].id) # index = 0 for male and 1 for female
                        zira.say(msg)
                        zira.runAndWait()

                        current_time = time.time()
                        slack_unlock_status = True
                        if current_time - last_slack_warned_time > SLACK_SECS_BETWEEN_WARNINGS:
                            msg_string = "Something is wrong. Please check Lithium table."
                            my_bot.post_message(msg_string, mention_all = True)
                            last_slack_warned_time = current_time

        except KeyboardInterrupt:
            print('Picoscope logging terminated by keyboard interrupt')



def initialize_ttsengines():
    # enable text to speech: Female voice (Zira)
    zira = pyttsx3.init()
    voice_zira = zira.getProperty('voices')
    zira.setProperty('voice', voice_zira[1].id) # index = 0 for male and 1 for female
    # enable text to speech: Male voice (David)
    david = pyttsx3.init()
    voice_david = david.getProperty('voices')
    david.setProperty('voice', voice_david[0].id) 
    return (zira, david)

def tts_engine_say(engine, msg):
    engine.say(msg)
    engine.runAndWait()

def initialize_li_plot():
    plt.ion()
    li_figure, li_ax = plt.subplots(figsize = (5, 5)) 
    li_line1, = li_ax.plot(0, 0) 
    li_line2, = li_ax.plot(0, 0) 
    li_line3, = li_ax.plot(0, 0, 'x') 
    li_lines = (li_line1, li_line2, li_line3)
    plt.xlabel("Time (s)") 
    plt.ylabel("Voltage (mV)")
    return (li_figure, li_ax, li_lines)


def initialize_na_plot():
    plt.ion()
    na_figure, na_ax1 = plt.subplots(figsize = (5,5)) 
    na_ax1.set_xlabel("Time (s)")
    na_ax1.set_ylabel("Error signal (mV)", color = "blue")
    na_line_1, = na_ax1.plot(0, 0, color = "blue") 
    na_ax1.set_ylim([-1000, 1000])
    na_ax1.tick_params(axis = 'y', labelcolor = 'blue')
    na_ax2 = na_ax1.twinx()
    na_line_2, = na_ax2.plot(0, 0, color = "red")
    na_ax2.set_label("Time (s)") 
    na_ax2.set_ylabel("Output signal (mV)\n", color = "red")
    na_ax2.tick_params(axis = 'y', labelcolor = "red")
    na_figure.tight_layout()
    na_lines = (na_line_1, na_line_2)
    return (na_figure, na_ax1, na_ax2, na_lines)


def update_na_plot(na_fig, na_ax1, na_ax2, na_lines, na_time_data, na_ydata_traces):
    for line, ydata in zip(na_lines, na_ydata_traces):
        line.set_xdata(na_time_data) 
        line.set_ydata(ydata)
    trace_max = np.max(na_ydata_traces)
    ax2_ymax = min(NA_SCOPE_CHANNEL_B_RANGE_MV, 1.2 * trace_max)
    na_ax1.set_ylim([-NA_SCOPE_CHANNEL_A_RANGE_MV, NA_SCOPE_CHANNEL_A_RANGE_MV])
    na_ax2.set_ylim([-int(ax2_ymax), int(ax2_ymax)])
    #update plot 
    na_fig.canvas.draw() 
    na_fig.canvas.flush_events() 
    time.sleep(0.1)

                # Li_picoscope.run_block()
                # buffers = Li_picoscope.get_block_traces()

                # traces_value = [val for val in buffers.values()]
                # time_data = np.linspace(0, blockDuration, num=blockSize)
                # line1.set_xdata(time_data)
                # line1.set_ydata(traces_value[0])
                # line2.set_xdata(time_data)
                # line2.set_ydata(traces_value[1])

                # ###############################
                # # find peaks
                # FP_array = np.array(traces_value[1])
                # FP_peak_indices, FP_peak_properties = find_peaks(FP_array, height = peakThreshold)
                # line3.set_xdata(time_data[FP_peak_indices])
                # line3.set_ydata(FP_array[FP_peak_indices])

                # ###############################
                # # update plot
                # figure_Li.canvas.draw()
                # figure_Li.canvas.flush_events()
                # time.sleep(0.1)

def update_li_plot(li_fig, li_ax, li_lines, li_time_data, li_ydata_traces, li_fp_peak_indices):
    sweep_line, fp_line, peaks_line = li_lines
    sweep_ydata, fp_ydata = li_ydata_traces
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
    


def initialize_scope(id, serial, channel_range_A, channel_range_B,
                     pre_trigger_percent, block_size, block_duration, trigger_params = None):
    picoscope = Picoscope(id, serial = serial, verbose = True) 
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


def slack_warn(msg, slack_bot, last_slack_warned_time, warning_interval, 
               mention_all = False, override_interval = False):
    current_time = time.time() 
    if override_interval or current_time - last_slack_warned_time > warning_interval:
        last_slack_warned_time = current_time 
        slack_bot.post_message(msg, mention_all = mention_all)
    return last_slack_warned_time


HELP_ALIASES = ["help", "h", "HELP", "H", "Help"]
def parse_clas():
    clas = sys.argv[1:] 
    if len(clas) > 0 and clas[1] in HELP_ALIASES:
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


    