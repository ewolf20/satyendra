# Huan Q Bui, BEC1@MIT
# Last updated: 9:58 am, Feb 01, 2023
import numpy as np
import sys 
import matplotlib.pyplot as plt
import time
from scipy.signal import find_peaks
import ctypes
import pyttsx3 

# TODO: update trigger level automatically based on where boosterLoc is...

PATH_TO_REPOSITORIES_FOLDER = "C:/Users/BEC1Top/Repositories"
sys.path.insert(0, PATH_TO_REPOSITORIES_FOLDER)

from satyendra.code import slack_bot
from satyendra.code.ps2000_wrapper_blockmode_utils import Picoscope


def main(initial_trigger_level):
    # enable text to speech engine:
    engine = pyttsx3.init()
    voice = engine.getProperty('voices')
    engine.setProperty('voice', voice[1].id) # index = 0 for male and 1 for female
    #Slack notification params:
    SLACK_SECS_BETWEEN_WARNINGS = 600 

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
    peakThreshold = 400
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

    #instantiate a device with its specific serial number:
    my_picoscope = Picoscope(0, serial='JO247/1191', verbose=True)
    my_picoscope.setup_channel('A',channel_range_mv=10000)
    my_picoscope.setup_channel('B',channel_range_mv=5000)
    my_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)
    my_picoscope.setup_block(block_size = blockSize, block_duration=blockDuration, pre_trigger_percent=0)

    with my_picoscope:
        my_picoscope.run_block()
        buffers = my_picoscope.get_block_traces()
        traces_value = [val for val in buffers.values()]

        time_data = np.linspace(0, blockDuration, num=blockSize)
        # time_data = np.linspace(0, 1, len(traces_value[0]))
        # initial shot
        plt.ion()
        figure, ax = plt.subplots(figsize=(5,5))
        line1, = ax.plot(time_data, traces_value[0])
        line2, = ax.plot(time_data, traces_value[1]) 
        plt.xlabel('Time (s)')
        plt.ylabel('Voltage (mV)')

        # for getting peaks
        FP_array = np.array(traces_value[1])
        FP_peak_indices, FP_peak_properties = find_peaks(FP_array, height = 100)
        line3, = ax.plot(time_data[FP_peak_indices], FP_array[FP_peak_indices], 'x')

        try:
            while True:

                my_picoscope.run_block()
                buffers = my_picoscope.get_block_traces()

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
                figure.canvas.draw()
                figure.canvas.flush_events()
                time.sleep(0.1)

                ###############################
                # injection lock now:                   

                # first, there should be exactly four peaks
                if initialization_counter < initialization_counter_MAX:
                    if len(FP_peak_indices) == 4:
                        # get info of the four peaks:
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
                        # compute, from the first few shots:
                        # the average height of each peak
                        # the average spacings between the peaks:

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
                                # triggering too soon, gotta trigger later
                                msg = 'Triggering too soon. Adjusting'
                                engine.say(msg)
                                engine.runAndWait()
                                # do sth
                                triggerLevel += 100
                                my_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)
                                print('Trigger level: ' + str(triggerLevel))

                            elif boosterLoc <= boosterLocMin:
                                # triggering too late, gotta trigger earlier
                                msg = 'Triggering too late. Adjusting'
                                engine.say(msg)
                                engine.runAndWait()
                                # do sth
                                triggerLevel -= 100
                                my_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)
                                print('Trigger level: ' + str(triggerLevel))
                    
                    else:
                        # if dont see exactly four peaks...
                        if len(FP_peak_indices) >= 5:
                            msg = 'Bad trigger'
                            engine.say(msg)
                            engine.runAndWait()
                        else:
                            msg = 'Not locked'
                            engine.say(msg)
                            engine.runAndWait()


                
                else:
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
                    # assuming that the first peak is the booster...
                    # this might sound bad, but it is in fact a safe assumption because 
                    # if the first peak is not the booster then the code will say that at least one of the lasers unlocked, then we can step in and see what's wrong 
                    # and then happens only due to extreme changes in the lock status
                    # anyway, assuming booster is the first peak, adjust the trigger level:
                    if boosterLoc >= boosterLocMax:
                        # triggering too soon, gotta trigger later
                        msg = 'Triggering too soon. Adjusting'
                        engine.say(msg)
                        engine.runAndWait()
                        # do sth
                        triggerLevel += 25
                        my_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)

                    elif boosterLoc <= boosterLocMin:
                        # triggering too late, gotta trigger earlier
                        msg = 'Triggering too late. Adjusting'
                        engine.say(msg)
                        engine.runAndWait()
                        # do sth
                        triggerLevel -= 25
                        my_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)

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
                        # print lock status
                        print("Booster location: " + str(boosterLoc) + "/" + str(len(FP_array)))
                        print('Trigger level:    ' + str(triggerLevel))
                        print(" - - - - - - - - - - - - - -")
                        print("Booster peak: " + str(boosterPeak))
                        # slower
                        print("Slower peak:  " + str(slowerPeak))
                        # repump
                        print("Repump peak:  " + str(repumpPeak))
                        # MOT
                        print("MOT peak:     " + str(MOTPeak))
                        if (slowerLocked == lock_max_strikes):
                            print("Slower unlocked!")
                        if (repumpLocked == lock_max_strikes):
                            print("Repump unlocked!")
                        if (MOTLocked == lock_max_strikes):
                            print("MOT unlocked!")
                        print("----------------------------")
                        print("boosterPeak_avg: " + str(boosterPeak_avg))
                        print("slowerPeak_avg:  " + str(slowerPeak_avg))
                        print("repumpPeak_avg:  " + str(repumpPeak_avg))
                        print("MOTPeak_avg:     " + str(MOTPeak_avg))
                        print("============================")
                        # end of print lock status
                        
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
                            engine.say(msg)
                            engine.runAndWait()
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

        except KeyboardInterrupt:
            print('Picoscope logging terminated by keyboard interrupt')

if __name__ == "__main__":
	main(sys.argv)


    