import ctypes
from math import floor, log2
import sys
import numpy as np
from picosdk.ps2000 import ps2000 as ps
from picosdk.functions import adc2mV, assert_pico2000_ok, mV2adc, assert_pico_ok
import time
import matplotlib.pyplot as plt
from multiprocessing import Process


class Picoscope:
    def __init__(self, handle, serial=None, verbose=False):
        """
        Args:
            - handle: unique int to identify each picoscope connected to the PC
            - serial: 10-digit string typically found on the back of the device between two asterisks
        """
        self.verbose = verbose
        # Create c_handle and status ready for use
        self.c_handle = ctypes.c_int16(handle)
        self.status = {}

        self.status["openUnit"] = ps.ps2000_open_unit()
        
        self.buffers = {}
        self.chARange = 7
        self.chBRange = 7
        self.active_channels = []
        #channel voltage range index as defined in ps4000a.py
        self.channel_ranges = {} 
        #lookup list to convert range index to mV. Max of 50000 mV comes from datasheet.
        self.allowed_ranges = [10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000] 
        self._get_max_ADC()

    def __enter__(self):
        pass

    def __exit__(self, exc_type, exc_value, exc_traceback):
        try:

            self.status["stop"] = ps.ps2000_stop(self.c_handle)
            assert_pico2000_ok(self.status["stop"])
            self.status["close"] = ps.ps2000_close_unit(self.c_handle)
            assert_pico2000_ok(self.status["close"])
            if self.verbose:
                print('scope closed.')
        except Exception as e:
            if self.verbose:
                print('Picoscope was not closed successfully.')
            raise e

    def _get_max_ADC(self):
        """
        Query the maximum ADC count supported by the device which will be used in unit conversions later.
        """
        # handle = chandle
        # pointer to value = ctypes.byref(maxADC)
        self.max_ADC = ctypes.c_int16(32767)

    def setup_channel(self, channel_name, analog_offset=0, channel_range_mv=2000,
                      coupling_DC=1):
        """
        Args:
            - channel_name: str (single capital letter, A-H, e.g. 'D')
            - analog_offset: offsets the input, in Volts. Check datasheet for allowed values. TODO: coerce these things too!
            - channel_range_mv: in mV  
            - coupling_DC: bool, set to False for AC coupling
        """
        if self.verbose:
            print('Opening channel ' + channel_name + '...\n')  
        def coerce_channel_range(channel_range_mv):
            """
            Coerce channel voltage range set by user into device allowed values or raise an error

            Args: 
                - channel_range_mv: user set channel range in mV
            
            Return:
                - coerced channel range converted to a range index as defined in ps4000a.py
            """
            try:
                coerced_range = next(x for x in self.allowed_ranges if x >= abs(channel_range_mv))
                if channel_range_mv != coerced_range:
                    print(f'[PS2000 configuration error]: channel {channel_name} range setting coerced to {coerced_range} mV !\n')
            except StopIteration:
                coerced_range = self.allowed_ranges[-1]
                print((f'[PS2000 configuration error]: channel {channel_name} range setting is out of bound and therefore'
                        f' coerced to 50000 mV !\n'))
            return self.allowed_ranges.index(coerced_range) 

        channel_range = coerce_channel_range(channel_range_mv)

        # Set up a channel
        # handle = chandle
        # channel = PS4000a_CHANNEL_A = 0
        # enabled = 1
        # coupling type = PS4000a_DC = 1
        # range = PS4000a_2V = 7
        # analogOffset = 0 V

        if channel_name == 'A':
            channel = 0
            self.chARange = channel_range
        elif channel_name == 'B':
            channel = 1
            self.chBRange = channel_range
        else:
            print('Invalid Channel Name!')

        self.c_handle = ctypes.c_int16(self.status["openUnit"])

        self.status["setCh"+channel_name] = ps.ps2000_set_channel(self.c_handle, channel, 1, coupling_DC, channel_range)
        assert_pico2000_ok(self.status["setCh"+channel_name])

        self.active_channels.append(channel_name)
        self.channel_ranges[channel_name] = channel_range

    def setup_trigger(self, source_channel_name, trigger_threshold_mv=100, 
                        trigger_direction=2, trigger_delay=0, auto_trigger=0):
        """
        Setup a single trigger on a selected source channel. Must setup the channel first!
        Args:
            - source_channel_name: str (single capital letter, A-H, e.g. 'D'). 
            - trigger_threshold_mv: in mV. 
            - trigger_direction: trigger mode (e.g. = 2 for triggering on rising edge)
            - trigger_delay: in sample periods
            - auto_trigger: waittime in ms after which the trigger will automatically
                            fire. Set to 0 to disable. 
        """
        def convert_trigger_units(trigger_threshold_mv):
            """
            Convert user input trigger threshold in mv to ADC counts
            """
            try:
                source_channel_range = self.channel_ranges[source_channel_name]
            except KeyError:
                print((f'[PS2000 configuration error]: channel {source_channel_name} not found. '
                        'Setup all channels before setting a trigger.\n \nProgram aborted.'))
                sys.exit()
            if self.allowed_ranges[source_channel_range] <= trigger_threshold_mv:
                print('[PS2000 configuration error]: trigger threshold is higher than the channel range.\n',
                        'Program aborted.')
                sys.exit()
            return mV2adc(trigger_threshold_mv, source_channel_range, self.max_ADC)
        
        trigger_threshold = convert_trigger_units(trigger_threshold_mv)
        # Set up single trigger
        # handle = chandle
        # enabled = 1
        # source = PS4000a_CHANNEL_A = 0
        # threshold = 1024 ADC counts
        # direction = PS4000a_RISING = 2
        # delay = 0 s
        # auto Trigger = 1000 ms           

        if source_channel_name == 'A':
            channel = 0
        elif source_channel_name == 'B':
            channel = 1

        self.status["trigger"] = ps.ps2000_set_trigger(self.c_handle,
                                        channel,
                                        trigger_threshold,
                                        trigger_direction,
                                        trigger_delay,
                                        auto_trigger)
        assert_pico2000_ok(self.status["trigger"])

        if self.verbose:
            print(f'Trigger is armed on channel {source_channel_name}. Waiting for the first data trace...\n')

    def setup_block(self, block_size=1000, block_duration=1, pre_trigger_percent=0):
        """
        Setup the the size and duration of the data block one wishes to capture.
        Args: 
            - block_size: number of samples to take in each block
            - block_duration: in seconds
            - pre_trigger_percent: percentage of the sample took before trigger event (from 0 to 1)
        """
        def convert_timebase(block_size, block_duration):
            """
            Convert sampling rate defined by user (by specifying block duration and size) to a timebase integer 
            that the device uses to configure the clock (see device documentation). Additionally coerces the rate to 1000kS/s
            if setting is out of bound.
            """
            sampling_rate = (block_size-1) / block_duration # in Samples /s
            timebase = floor(  np.log2(1/(1e-8 * sampling_rate)) + 2 ) # see documentation for definition, secs per division
            if 0 <= timebase <= 2e32 - 1:
                print((f'Configured PS2000 to take blocks of {block_size} samples at {sampling_rate*1e-3:.3f} kS/s,'
                f'each lasting {(block_size-1)/sampling_rate:.3f} s\n'))
            else:
                print((f'[PS2000 configuration error]: sampling rate of {sampling_rate*1e-3:.3f} kS/s is out of bound.\n'
                        f'Coerced to taking blocks of {block_size} samples at 100 kS/s, each lasting'
                        f'{(block_size-1)/100e3:.3f} s\n'))
                timebase = 10
            return timebase
        
        self.timebase = convert_timebase(block_size,block_duration)
        self.block_size = block_size
        self.pre_trigger_samples = floor(block_size * pre_trigger_percent)
        self.post_trigger_samples = block_size - self.pre_trigger_samples
        # i don't know what the following arguments do
        timeInterval = ctypes.c_int32()
        returned_block_size = ctypes.c_int32() 
        timeUnits = ctypes.c_int32()
        oversample = ctypes.c_int16(1)


        # Get timebase information
        # WARNING: When using this example it may not be possible to access all Timebases as all channels are enabled by default when opening the scope.  
        # To access these Timebases, set any unused analogue channels to off.
        # handle = chandle
        # timebase = 8 = timebase
        # noSamples = maxSamples
        # pointer to timeIntervalNanoseconds = ctypes.byref(timeIntervalns)
        # pointer to maxSamples = ctypes.byref(returnedMaxSamples)
        # segment index = 0

        self.status["getTimebase"] = ps.ps2000_get_timebase(self.c_handle, self.timebase, self.block_size, ctypes.byref(timeInterval), ctypes.byref(timeUnits), oversample, ctypes.byref(returned_block_size))
        assert_pico2000_ok(self.status["getTimebase"])

    def run_block(self):
        """
        Call this function after the device is configured to prepare fresh buffers for capturing a new data block, and to start this capture
        """

        timeIndisposedms = ctypes.c_int32()
        oversample = ctypes.c_int16(1)
        self.status["runBlock"] = ps.ps2000_run_block(self.c_handle, self.block_size, self.timebase, oversample, ctypes.byref(timeIndisposedms))
        assert_pico2000_ok(self.status["runBlock"])



    def get_block_traces(self):
        """
        Check and transfer data block when captured.

        Return: dict{key: list} where key is the channel name and list is the captured data trace on this channel.
        """

        # Check for data collection to finish using ps2000aIsReady
        ready = ctypes.c_int16(0)
        check = ctypes.c_int16(0)
        while ready.value == check.value:
            self.status["isReady"] = ps.ps2000_ready(self.c_handle)
            ready = ctypes.c_int16(self.status["isReady"])


        # Create buffers ready for data
        bufferA = (ctypes.c_int16 * self.block_size)()
        bufferB = (ctypes.c_int16 * self.block_size)()

        # Get data from scope
        # handle = chandle
        # pointer to buffer_a = ctypes.byref(bufferA)
        # pointer to buffer_b = ctypes.byref(bufferB)
        # poiner to overflow = ctypes.byref(oversample)
        # no_of_values = cmaxSamples


        cmaxSamples = ctypes.c_int32(self.block_size)
        oversample = ctypes.c_int16(1)
        self.status["getValues"] = ps.ps2000_get_values(self.c_handle, ctypes.byref(bufferA), ctypes.byref(bufferB), None, None, ctypes.byref(oversample), cmaxSamples)
        assert_pico2000_ok(self.status["getValues"])


        # convert ADC counts data to mV
        adc2mVChA =  adc2mV(bufferA, self.chARange, self.max_ADC)
        adc2mVChB =  adc2mV(bufferB, self.chBRange, self.max_ADC)

        # #TODO temporary figure stuff do this properly later
        # if show_traces: 
        #     fig, ax = plt.subplots()
        #     sample_id = np.linspace(1, self.block_size, self.block_size) #change this to timestamps later
        #     sample_values = [chl for chl in self.buffers.values()]
        #     for chl in sample_values:
        #         ax.plot(sample_id, chl)
        #     fig.show()

        self.buffers = {'A': adc2mVChA, 'B': adc2mVChB}

        return self.buffers

