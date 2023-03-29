# Huan Q Bui, BEC1@MIT
# Last updated: Mar 29, 2023
import numpy as np
import sys 
import matplotlib.pyplot as plt
import time
from scipy.signal import find_peaks
import ctypes
import pyttsx3 

PATH_TO_REPOSITORIES_FOLDER = "C:/Users/BEC1Top/Repositories"
sys.path.insert(0, PATH_TO_REPOSITORIES_FOLDER)

from satyendra.code import slack_bot
from satyendra.code.ps2000_wrapper_blockmode_utils import Picoscope


def main():
    blockSize = 1000
    blockDuration = 0.005
    # setup slack bot:
    last_slack_warned_time = -np.inf
    slack_unlock_status = False
    my_bot = slack_bot.SlackBot()
    #Slack notification params:
    SLACK_SECS_BETWEEN_WARNINGS = 600 

     # enable text to speech engine:
    engine = pyttsx3.init()
    voice = engine.getProperty('voices')
    engine.setProperty('voice', voice[0].id) # index = 0 for male and 1 for female
    #Slack notification params:
    SLACK_SECS_BETWEEN_WARNINGS = 600 

    #instantiate a device with its specific serial number:
    Na_picoscope = Picoscope(0, serial='JO247/0361', verbose=True)
    Na_picoscope.setup_channel('A',channel_range_mv=500)
    Na_picoscope.setup_channel('B',channel_range_mv=10000)
    #Na_picoscope.setup_trigger('A',trigger_threshold_mv=triggerLevel, trigger_direction=0)
    Na_picoscope.setup_block(block_size = blockSize, block_duration=blockDuration, pre_trigger_percent=0)

    with Na_picoscope:
        Na_picoscope.run_block()
        buffers = Na_picoscope.get_block_traces()
        traces_value = [val for val in buffers.values()]

        time_data = np.linspace(0, blockDuration, num=blockSize)

        plt.ion()
        figure, ax1 = plt.subplots(figsize=(5,5))
        ax1.set_xlabel('Time (s)')
        ax1.set_ylabel('Error signal (mV)', color = 'blue')
        line1, = ax1.plot(time_data, traces_value[0], color = 'blue')
        ax1.set_ylim([-1000, 1000])
        ax1.tick_params(axis='y', labelcolor='blue')
        ax2 = ax1.twinx()
        line2, = ax2.plot(time_data, traces_value[1], color = 'red') 
        ax2.set_xlabel('Time (s)')
        ax2.set_ylabel('Output signal (mV) \n', color = 'red')
        ax2.tick_params(axis='y', labelcolor='red')

        figure.tight_layout()
        
        try:
            while True:
                Na_picoscope.run_block()
                buffers = Na_picoscope.get_block_traces()

                traces_value = [val for val in buffers.values()]
                time_data = np.linspace(0, blockDuration, num=blockSize)
                line1.set_xdata(time_data)
                line1.set_ydata(traces_value[0])
                line2.set_xdata(time_data)
                line2.set_ydata(traces_value[1])

                max_trace_0 = max(traces_value[0])
                max_trace_1 = max(traces_value[1])
                ylim = min(10000, max(2000,   1.2*max(max_trace_0, max_trace_1)))
                ax1.set_ylim([-500, 500])
                ax2.set_ylim([-int(ylim), int(ylim)])
                
                # update plot
                figure.canvas.draw()
                figure.canvas.flush_events()
                time.sleep(0.1)

                # now calculate averages:
                mean_error_signal_avg = np.mean(traces_value[0]) # this is the error signal
                mean_output_signal_avg = np.mean(traces_value[1]) # this is the output signal (aux)

                # the lock LED turns RED if the error signal is above 0.33 V in magnitude, but ok can set to 69
                # OR the output signal voltage is within 10% of max outputs, which is 10 V
                if (np.abs(mean_error_signal_avg) > 69) or (np.abs(mean_output_signal_avg) > 9000 ):
                    # triggering too soon, gotta trigger later
                        msg = 'Guys, Sodium unlocked!'
                        engine.say(msg)
                        engine.runAndWait()

                        current_time = time.time()
                        slack_unlock_status = True
                        if current_time - last_slack_warned_time > SLACK_SECS_BETWEEN_WARNINGS:
                            msg_string = "Guys, the Na laser unlocked!"
                            my_bot.post_message(msg_string, mention_all = True)
                            last_slack_warned_time = current_time
                else:
                    slack_unlock_status = False

        except KeyboardInterrupt:
            print('Picoscope logging terminated by keyboard interrupt')

if __name__ == "__main__":
	main()

