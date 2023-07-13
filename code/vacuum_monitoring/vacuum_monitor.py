import serial
import numpy as np 
import time 

from ..status_monitor import StatusMonitor
from .ionpump import IonPump 
from .iongauge import IonGauge

class VacuumMonitor(StatusMonitor):


    """Initialization method.

    Parameters:

    vacuum_instrument_tuple_list: A list of tuples (inst_name, inst_port, inst_type, [inst_read_key1, inst_read_key2, ...], 
                                                    warning_threshold_dict, keyword_dict) 
    Each tuple contains information on a single instrument that the monitor should read. 
        inst_name: str, The (user-generated) name of the instrument which the vacuum monitor should watch 
        inst_port: str, The port name of the instrument
        inst_type: str, a string identifying the type of instrument
            'pump_spc' - A DIGITEL SPC ion pump controller
            'pump_spce' - A DIGITEL SPCe ion pump controller
            'pump_mpc' - A DIGITEL MPC ion pump controller
            'gauge_xgs-600' - An Agilent XGS-600 ion gauge controller
            'gauge_xgs-600_toggle' - An agilent XGS-600 ion gauge controller which must be turned off and on
        inst_read_key: A key identifying what values, if any, should be read from the instrument and logged.
            'pressure': Supported for 'pump_spc', 'pump_spce'
            'voltage': Supported for 'pump_spc', 'pump_spce'
            'current': Supported for 'pump_spc', 'pump_spce'
            'pressure1': Supported for 'pump_mpc'.
            'pressure2': Supported for 'pump_mpc'
            'pressurecurrentfil': Supported for 'gauge_xgs-600'. Measures the pressure on the currently active filament.
            'pressurefil1toggle': Supported for 'gauge_xgs-600'. Toggles fil1 on, measures pressure, then turns it off
            'pressurefil2toggle': Supported for 'gauge_xgs-600'. Ditto above with fil2.
            'voltage1', 'voltage2': Supported for 'pump_mpc' 
            'current1, current2': Supported for 'pump_mpc'
        warning_threshold_dict: A dictionary {read_key:Max Value} of combinations of keys and maximum allowed values before a warning is sent
        Keys are all of the values in inst_read_key. May be empty or none. 
        keyword_dict: A dictionary of any keywords that should be passed to the instrument constructor. May be empty or none.
        
    """
    def __init__(self, instrument_tuple_list, warning_interval_in_min = 0, local_log_filename = "DEFAULT.csv"):
        super().__init__(warning_interval_in_min = warning_interval_in_min, local_log_filename = local_log_filename)
        self.instrument_list = [] 
        self.instrument_names_list = [] 
        self.instrument_warning_dicts_list = []
        self.instrument_read_keys_list = []
        for instrument_tuple in instrument_tuple_list: 
            inst_name, inst_port, inst_type, inst_read_keys, warning_threshold_dict, keyword_dict = instrument_tuple
            if(keyword_dict is None):
                keyword_dict = {} 
            if(warning_threshold_dict is None):
                warning_threshold_dict = {}
            self.instrument_names_list.append(inst_name)
            self.instrument_warning_dicts_list.append(warning_threshold_dict)
            self.instrument_read_keys_list.append(inst_read_keys)
            if(inst_type == 'pump_spc'):
                instrument = IonPump(inst_port, 'spc', **keyword_dict)
            elif(inst_type == 'pump_spce'):
                instrument = IonPump(inst_port, 'spce', **keyword_dict) 
            elif(inst_type == 'pump_mpc'):
                instrument = IonPump(inst_port, 'mpc', **keyword_dict)
            elif(inst_type == 'gauge_xgs-600' or inst_type == "gauge_xgs-600_toggle"):
                instrument = IonGauge(inst_port, 'xgs-600', **keyword_dict) 
            else:
                raise ValueError("inst_type " + inst_type + " is not supported by vacuum monitor.")
            self.instrument_list.append(instrument) 
        
    def __enter__(self):
        return self 

    def __exit__(self, exc_type, exc_value, traceback):
        for instrument in self.instrument_list:
            instrument.__exit__(exc_type, exc_value, traceback) 

    def monitor_continuously(self, log_local = True, end_time = np.inf, iteration_time = 0.0):
        start_time = time.time() 
        elapsed_time = 0.0
        old_cycle_time = 0.0 
        while(elapsed_time < end_time):
            if(elapsed_time - old_cycle_time > iteration_time):
                foo = self.monitor_once(log_local = log_local) 
                print(foo) 
                old_cycle_time = elapsed_time
            elapsed_time = time.time()
        


    #TODO: Add support for uploading to breadboard
    #TODO: Add support for plotting
    """Core method for monitoring.

    Given the global parameters established in the init, monitors the instruments which have been passed to the vacuum_monitor instance.
    Optionally logs the measured values locally in a pandas-formatted .csv using the method from status_monitor.

    Parameters:

    log_local: Whether to log the measured values of the vacuum readings locally in a .csv. Default true. 
    add_time: Whether to append a timestamp to the dict of measured values. Default true. 

    Returns:

    A tuple (overall_dict, error_list, threshold_list)

    overall_dict: A dict of the values returned from the various vacuum readings. 
    error_list: A list of instrument names which have errors preventing the values from being read
    threshold_list: A list of readings which are above the set threshold values
    """
    def monitor_once(self, log_local = True, add_time = True):
        overall_dict = {}
        error_list = []
        threshold_list = []
        got_error = False
        for instrument, instrument_name, instrument_read_keys, warning_threshold_dict in zip(self.instrument_list, self.instrument_names_list, 
                                                                                            self.instrument_read_keys_list, self.instrument_warning_dicts_list):
            try:
                instrument_dict, instrument_threshold_list = self._monitor_pump_helper(instrument, instrument_name, instrument_read_keys, warning_threshold_dict)
                threshold_list.extend(instrument_threshold_list)
                for key in instrument_dict:
                    overall_dict[key] = instrument_dict[key]
            except (ValueError, serial.serialutil.SerialException) as e:
                for key in instrument_read_keys:
                    overall_dict[key] = "ERROR"
                error_list.append(instrument_name)
                got_error = True
        if(add_time):
            overall_dict["Time"] = time.strftime("%y-%m-%d %H:%M:%S")
        if(log_local and not got_error):
            self.log_values_locally(overall_dict) 
        return (overall_dict, error_list, threshold_list)

    def _monitor_pump_helper(self, instrument, instrument_name, instrument_read_keys, warning_threshold_dict):
        return_dict = {}
        threshold_list = []
        for instrument_read_key in instrument_read_keys:
            overall_reading_key = instrument_name + " " + instrument_read_key
            read_value = self._read_helper(instrument, instrument_read_key)
            if(not warning_threshold_dict is None) and (instrument_read_key in warning_threshold_dict):
                threshold = warning_threshold_dict[instrument_read_key] 
                if(read_value > threshold):
                    threshold_list.append((overall_reading_key, read_value, threshold)) 
            return_dict[overall_reading_key] = read_value
        return (return_dict, threshold_list)

            
    def give_instrument_names(self):
        print("This VacuumMonitor instance has the following instruments: ")
        for instrument_name in self.instrument_names_list:
            print(instrument_name)



    def failsafe(self, instrument_names_to_shutdown = None):
        if(not instrument_names_to_shutdown):
            instrument_names_to_shutdown = self.instrument_names_list
        instruments_shutdown_tuple_list = [f for f in zip(self.instrument_list, self.instrument_names_list) if f[1] in instrument_names_to_shutdown]
        status_list = []
        for instrument, instrument_name in instruments_shutdown_tuple_list:
            success = instrument.failsafe()
            status_list.append(success)
        return status_list

    def close_ports(self, instrument_names_to_close_port = None):
        if instrument_names_to_close_port is None:
            instrument_names_to_close_port = self.instrument_names_list
        instruments_close_port_tuple_list = [f for f in zip(self.instrument_list, self.instrument_names_list) if f[1] in instrument_names_to_close_port]
        for instrument, instrument_name in instruments_close_port_tuple_list: 
            instrument.close_port()


    def refresh_ports(self, instrument_names_to_refresh_port = None):
        if instrument_names_to_refresh_port is None:
            instrument_names_to_refresh_port = self.instrument_names_list
        instruments_refresh_port_tuple_list = [f for f in zip(self.instrument_list, self.instrument_names_list) if f[1] in instrument_names_to_refresh_port]
        for instrument, instrument_name in instruments_refresh_port_tuple_list: 
            instrument.refresh_port()
        
        

    #TODO: Handle exceptions
    @staticmethod
    def _read_helper(instrument, instrument_read_key):
        if(instrument_read_key == "pressure"):
            returned_value = instrument.measure_pressure() 
        elif(instrument_read_key == "pressure1"):
            returned_value = instrument.measure_pressure(1) 
        elif(instrument_read_key == "pressure2"):
            returned_value = instrument.measure_pressure(2) 
        elif(instrument_read_key == "current"):
            returned_value = instrument.measure_current() 
        elif(instrument_read_key == "current1"):
            returned_value = instrument.measure_current(1)
        elif(instrument_read_key == "current2"):
            returned_value = instrument.measure_current(2) 
        elif(instrument_read_key == "voltage"):
            returned_value = instrument.measure_voltage() 
        elif(instrument_read_key == "voltage1"):
            returned_value = instrument.measure_voltage(1) 
        elif(instrument_read_key == "voltage2"):
            returned_value = instrument.measure_voltage(2)
        elif(instrument_read_key == "pressurecurrentfil"):
            returned_value = instrument.measure_pressure() 
        elif(instrument_read_key == "pressurefil1toggle"):
            returned_value = instrument.toggle_and_measure_pressure(1)
        elif(instrument_read_key == "pressurefil2toggle"):
            returned_value = instrument.toggle_and_measure_pressure(2)
        if(returned_value == -1):
            raise ValueError("Unable to read from instrument.")
        return returned_value 


