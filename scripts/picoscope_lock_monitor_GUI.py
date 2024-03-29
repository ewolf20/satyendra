# Huan Q. Bui, BEC1@MIT
# Created: 10:00 am, April 13, 2023
# Last updated: April 13, 2023

# Lock monitor for BEC1 with GUI

import tkinter as tk
from tkinter import *
from tkinter import ttk

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
import picoscope_lock_monitor


class Lock_Monitor():
    def __init__(self, master):
        self.master = master
        self.lock_monitor = Frame(master)
        self.lock_monitor.pack() 
        tabControl = ttk.Notebook(master)
        self.tab1 = ttk.Frame(tabControl)
        tabControl.pack(expand = 1, fill ="both")
        tabControl.add(self.tab1, text ='Lock Monitor')
        # engage button
        self.engage_bttn = Button(self.tab1, text="Engage", relief="raised",  width=8, command= self.engage)
        self.engage_bttn.place(x=20,y=20)
        # disengage button
        self.disengage_bttn = Button(self.tab1, text="Stop", relief="raised",  width=8, command= self.disengage)
        self.disengage_bttn.place(x=150,y=20)
        # add trigger level
        self.trig_label = Label(self.tab1, text="Trigger level for Li: ")
        self.trig_label.place(x=20, y=70)
        self.trig_entry = Entry(self.tab1, text="new param", width=15)
        self.trig_entry.place(x=150, y=70)  
        self.trig_entry.delete(0,'end')   
        self.trig_entry.insert(0, "2000") 
        self.trig = self.trig_entry.get()

        # engage:
        self.engage = True

    def engage(self):
        print(int(self.trig))
        self.engage = True
        self.lock(self.trig)
    
    def disengage(self):
        self.engage = False
        print('Stopped')

    def lock(self, initial_trigger_level):
        # enable text to speech: Zira
        zira = pyttsx3.init()
        voice_zira = zira.getProperty('voices')
        zira.setProperty('voice', voice_zira[1].id) # index = 0 for male and 1 for female
        # enable text to speech: David
        david = pyttsx3.init()
        voice_david = david.getProperty('voices')
        david.setProperty('voice', voice_david[0].id) # index = 0 for male and 1 for female
        #Slack notification params:
        SLACK_SECS_BETWEEN_WARNINGS = 300 
        # lock constants
        blockSize = 1000
        blockDuration = 0.005

        if len(initial_trigger_level) == 1: # if no argv found:
            triggerLevel = 2000 # default value 
        else:
            triggerLevel = int(initial_trigger_level[1])
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
        peakThreshold = 1000
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

        # setup slack bot:
        last_slack_warned_time = -np.inf
        slack_unlock_status = False
        my_bot = slack_bot.SlackBot()

        # peak find window:
        peak_find_window = 35

        # instantiate a device with its specific serial number: Li picoscope
        Li_picoscope = Picoscope(0, serial='JO247/1191', verbose=True)
        Li_picoscope.setup_channel('A',channel_range_mv=10000)
        Li_picoscope.setup_channel('B',channel_range_mv=5000)
        Li_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)
        Li_picoscope.setup_block(block_size = blockSize, block_duration=blockDuration, pre_trigger_percent=0)

        # instantiate a device with its specific serial number: Na picoscope
        Na_picoscope = Picoscope(1, serial='JO247/0361', verbose=True)
        Na_picoscope.setup_channel('A',channel_range_mv=500)
        Na_picoscope.setup_channel('B',channel_range_mv=10000)
        Na_picoscope.setup_block(block_size = blockSize, block_duration=blockDuration, pre_trigger_percent=0)

        with Li_picoscope and Na_picoscope:
            #### LI SCOPE ####
            Li_picoscope.run_block()
            buffers = Li_picoscope.get_block_traces()
            traces_value = [val for val in buffers.values()]

            time_data = np.linspace(0, blockDuration, num=blockSize)
            # time_data = np.linspace(0, 1, len(traces_value[0]))
            # initial shot
            plt.ion()
            figure_Li, ax = plt.subplots(figsize=(5,5))
            line1, = ax.plot(time_data, traces_value[0])
            line2, = ax.plot(time_data, traces_value[1]) 
            plt.xlabel('Time (s)')
            plt.ylabel('Voltage (mV)')

            # for getting peaks
            FP_array = np.array(traces_value[1])
            FP_peak_indices, FP_peak_properties = find_peaks(FP_array, height = peakThreshold)
            line3, = ax.plot(time_data[FP_peak_indices], FP_array[FP_peak_indices], 'x')

            #### NA SCOPE ####
            Na_picoscope.run_block()
            buffers_Na = Na_picoscope.get_block_traces()
            traces_value_Na = [val for val in buffers_Na.values()]

            time_data_Na = np.linspace(0, blockDuration, num=blockSize)

            plt.ion()
            figure_Na, ax1 = plt.subplots(figsize=(5,5))
            ax1.set_xlabel('Time (s)')
            ax1.set_ylabel('Error signal (mV)', color = 'blue')
            line1_Na, = ax1.plot(time_data_Na, traces_value_Na[0], color = 'blue')
            ax1.set_ylim([-1000, 1000])
            ax1.tick_params(axis='y', labelcolor='blue')
            ax2 = ax1.twinx()
            line2_Na, = ax2.plot(time_data_Na, traces_value_Na[1], color = 'red') 
            ax2.set_xlabel('Time (s)')
            ax2.set_ylabel('Output signal (mV) \n', color = 'red')
            ax2.tick_params(axis='y', labelcolor='red')

            figure_Na.tight_layout()

            try:
                while self.engage:
                    
                    #########################################################
                    ########## Na scope #####################################
                    #########################################################

                    Na_picoscope.run_block()
                    buffers_Na = Na_picoscope.get_block_traces()

                    traces_value_Na = [val for val in buffers_Na.values()]
                    time_data_Na = np.linspace(0, blockDuration, num=blockSize)
                    line1_Na.set_xdata(time_data_Na)
                    line1_Na.set_ydata(traces_value_Na[0])
                    line2_Na.set_xdata(time_data_Na)
                    line2_Na.set_ydata(traces_value_Na[1])

                    max_trace_0 = max(traces_value_Na[0])
                    max_trace_1 = max(traces_value_Na[1])
                    ylim = min(10000, max(2000,   1.2*max(max_trace_0, max_trace_1)))
                    ax1.set_ylim([-500, 500])
                    ax2.set_ylim([-int(ylim), int(ylim)])
                    
                    # update plot
                    figure_Na.canvas.draw()
                    figure_Na.canvas.flush_events()
                    time.sleep(0.1)

                    # now calculate averages:
                    mean_error_signal_avg = np.mean(traces_value_Na[0]) # this is the error signal
                    mean_output_signal_avg = np.mean(traces_value_Na[1]) # this is the output signal (aux)

                    # the lock LED turns RED if the error signal is above 0.33 V in magnitude, but ok can set to 69
                    # OR the output signal voltage is within 10% of max outputs, which is 10 V
                    if (np.abs(mean_error_signal_avg) > 69) or (np.abs(mean_output_signal_avg) > 9000 ):
                        # triggering too soon, gotta trigger later
                            msg = 'Guys, Sodium unlocked!'
                            david.setProperty('voice', voice_david[0].id) # index = 0 for male and 1 for female
                            david.say(msg)
                            david.runAndWait()

                            current_time = time.time()
                            slack_unlock_status = True
                            if current_time - last_slack_warned_time > SLACK_SECS_BETWEEN_WARNINGS:
                                msg_string = "Guys, the Na laser unlocked!"
                                my_bot.post_message(msg_string, mention_all = True)
                                last_slack_warned_time = current_time
                    else:
                        slack_unlock_status = False

                    #########################################################
                    ########## Li scope #####################################
                    #########################################################

                    Li_picoscope.run_block()
                    buffers = Li_picoscope.get_block_traces()

                    traces_value = [val for val in buffers.values()]
                    time_data = np.linspace(0, blockDuration, num=blockSize)
                    line1.set_xdata(time_data)
                    line1.set_ydata(traces_value[0])
                    line2.set_xdata(time_data)
                    line2.set_ydata(traces_value[1])

                    ###############################
                    # find peaks
                    FP_array = np.array(traces_value[1])
                    FP_peak_indices, FP_peak_properties = find_peaks(FP_array, height = peakThreshold)
                    line3.set_xdata(time_data[FP_peak_indices])
                    line3.set_ydata(FP_array[FP_peak_indices])

                    ###############################
                    # update plot
                    figure_Li.canvas.draw()
                    figure_Li.canvas.flush_events()
                    time.sleep(0.1)

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


def main():
    root = Tk()
    root.title('BEC1 Lock Monitor')
    root.geometry("500x500")
    lock_monitor = Lock_Monitor(root)
    root.mainloop()

    return 

if __name__ == "__main__":
	main()