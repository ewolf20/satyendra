# -*- coding: utf-8 -*-
"""
Created on Thu Apr  3 16:38:22 2025

@author: BEC1
"""

import numpy as np 
import serial
import time
import warnings

MINIECL_LI_CONSTANTS = {
"max_current_mA": 140, 
"current_limit_max_power_mA": 95, #measured for a give temperature for max power 40 mW
"max_power_mW":40,  #currently not used, value from docs, another protection can be added with photodiode implemented (keyword 'iphd')
"max_temp_C": 30, #at chip
"min_temp_C": 0, #at chip
"Steinhart_Hart_coeff": {'A' : 1.1293 *10**(-3) , 'B': 2.3410 *10**(-4), 'C': 8.7755 *10**(-8)}, 
}

KELVIN_CELSIUS_OFFSET = 273.15


class CTL200() :
    
    CTL200_SEND_EOL= '\r\n'
    CTL200_REPLY_EOL = '\r\n'
    CTL200_SERIAL_SETTINGS = {'baudrate': 115200, 'bytesize': serial.EIGHTBITS, 'parity': serial.PARITY_NONE, 'stopbits': serial.STOPBITS_ONE, 'timeout': 5.0}
    CTL200_DELAY = 0.05 #in s

    
    """
    Init method. 

    Most args self-explanatory. laser_profile may either be dict or str; if str, specifies one of the default laser profiles specified in CTL200_control.py. 
    If dict, contains a dict with keys as given in the default laser profiles.
    """

    def __init__(self, com_port, laser_profile, echo = False, disable_protection = False, 
                custom_current_limit_mA = None, custom_max_temp_C = None, custom_min_temp_C = None):
        
        port_settings = CTL200.CTL200_SERIAL_SETTINGS
        self.serial_port = serial.Serial(com_port , **port_settings)
        print("The port is open ==", self.serial_port.isOpen())
        self.send_eol = CTL200.CTL200_SEND_EOL
        self.reply_eol = CTL200.CTL200_REPLY_EOL
        self.echo = echo
        self.message_encoding = 'utf-8'

        self.disable_protection = disable_protection

        if isinstance(laser_profile, dict):
            laser_profile_dict = laser_profile
        elif isinstance(laser_profile, str):
            if laser_profile == "miniecl_li": 
                laser_profile_dict = MINIECL_LI_CONSTANTS
            else:
                raise ValueError("Unsupported laser profile")
        else:
            raise ValueError("Unsupported laser profile")
        
        self.max_current_mA = laser_profile_dict["max_current_mA"]
        self.current_limit_max_power_mA = laser_profile_dict["current_limit_max_power_mA"]
        
        self.current_limit = np.min(np.array( [ self.max_current_mA , self.current_limit_max_power_mA ] ) )
        if not custom_current_limit_mA is None:
            self.current_limit = custom_current_limit_mA

        self.max_temp_C = laser_profile_dict["max_temp_C"]
        if not custom_max_temp_C is None:
            self.max_temp_C = custom_max_temp_C

        self.min_temp_C = laser_profile_dict["min_temp_C"]
        if not custom_min_temp_C is None:
            self.min_temp_C = custom_min_temp_C
        
        self.Steinhart_Hart_coeff = laser_profile_dict["Steinhart_Hart_coeff"]
        
        
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_value, traceback):
        self.serial_port.close()
        
    def communicate(self, msg_str, get_reply = False):
        terminated_msg_str = msg_str + self.send_eol
        self.serial_port.write(terminated_msg_str.encode(self.message_encoding))
        self.serial_port.flush()
        time.sleep(CTL200.CTL200_DELAY)
        received_bytes = self.serial_port.read(size = self.serial_port.in_waiting)
        self.serial_port.flush()
        
        if self.echo:
            print( "Sent msg : {}".format(msg_str) )
                        
        if get_reply:
            received_string = received_bytes.decode(self.message_encoding).split(self.reply_eol)[-2]
            
            if self.echo:
                print( "Received msg : {}".format(received_string))

            return received_string
        

    #As in e.g. https://en.wikipedia.org/wiki/Steinhart%E2%80%93Hart_equation
    def _Steinhart_Hart_equation(self, R):
        A = self.Steinhart_Hart_coeff['A']
        B = self.Steinhart_Hart_coeff['B']
        C = self.Steinhart_Hart_coeff['C']
        
        log_val = np.log(R)
        temp = 1/ ( A + B*log_val + C*(log_val)**3 )
        
        return temp
    
    def _inverse_of_Steinhart_equation(self, T):
        A = self.Steinhart_Hart_coeff['A']
        B = self.Steinhart_Hart_coeff['B']
        C = self.Steinhart_Hart_coeff['C']
        
        x = (1/C) * (A - (1/T))
        y = np.sqrt( (B / (3*C))**3 + (x**2)/4 )
        
        R = np.exp( ( y- (x/2) )**(1/3) - ( y + (x/2) )**(1/3) )
        
        return R
        
    def set_current_mA(self, current_mA): 
        if not self.disable_protection and current_mA >= self.current_limit:
            raise Exception("above the current limit")
        self.communicate('ilaser ' +str(current_mA))
    
    def get_current_mA(self): 
        response = self.communicate('ilaser', get_reply= True)
        return float(response)

    def set_thermistor_setpoint(self, resistance_set_point):
        max_temp_K = self.max_temp_C + KELVIN_CELSIUS_OFFSET
        if not self.disable_protection and resistance_set_point >= self._inverse_of_Steinhart_equation(max_temp_K):
            raise Exception("above the temperature limit")
        self.communicate('rtset ' +str(resistance_set_point))
        
    def get_thermistor_setpoint(self):
        response = self.communicate('rtset' , get_reply= True)
        return response

    def get_thermistor_resistance_actual(self):
        response = self.communicate('rtact' , get_reply= True)
        return response
        
    def get_temperature_C(self):
        resistance = self.get_thermistor_resistance_actual()
        temp_K = self._Steinhart_Hart_equation(float(resistance))
        temp_C = (temp_K - KELVIN_CELSIUS_OFFSET)
        return temp_C


    def set_temperature_C(self, temperature_C):
        if not self.disable_protection and temperature_C >= self.max_temp_C:
            raise Exception("above the temperature limit, T = {} C".format(temperature_C))
        
        if not self.disable_protection and temperature_C <= self.min_temp_C:
            raise Exception("below the temperature limit, T = {} C".format(temperature_C))
                
        temperature_K = temperature_C + KELVIN_CELSIUS_OFFSET
        thermistor_setpoint = self._inverse_of_Steinhart_equation(temperature_K)
        self.communicate('rtset ' + str(thermistor_setpoint))
    
    
    def turn_on(self, debug = False):
        if not debug :
            self.communicate("lason 1")
        else :
            self.communicate("lason 1", get_reply = True)
        
    def turn_off(self, debug = False):
        if not debug :
            self.communicate("lason 0")
        else :
            self.communicate("lason 0", get_reply = True)
            
    def status(self):
        status = self.communicate("status", get_reply = True)
        return status 
    
    def check_port(self):
        print("The port is open ==", self.serial_port.isOpen())
    
        
        
        
        
        
        
        
        